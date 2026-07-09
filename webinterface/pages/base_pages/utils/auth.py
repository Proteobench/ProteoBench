"""
Optional OAuth authentication for ProteoBench submitter identification.

Supports GitHub and ORCID as identity providers. Authentication is entirely
optional -- the application works fully without it. When configured (via
secrets.toml) and the user chooses to sign in, their identity is stored in
a cookie and automatically attached to public submissions.

Sign-in is available from every page (top-right corner). Because an OAuth
sign-in requires a full-page redirect to the identity provider, the sign-in
links open in a **new browser tab**: the tab the user is working in keeps its
Streamlit session (uploaded files, computed results) fully intact. The signed-in
identity is persisted to a browser cookie, so once sign-in completes in the new
tab the working tab picks it up on its next interaction. This requires
``use_cookies = true`` (and a ``cookie_secret``) in ``secrets.toml``; without
cookies enabled the sign-in cannot propagate back to the working tab.
"""

import logging
from urllib.parse import urlencode

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# Session state key for the authenticated user
_AUTH_USER_KEY = "auth_user"
_COOKIE_RESTORED_KEY = "auth_cookie_restored"
# Set by sign_out() so the cookie deletion happens on the next run (see sign_out).
_PENDING_SIGNOUT_KEY = "auth_pending_signout"
# Set by handle_oauth_callback() on a successful sign-in. Marks this browser tab as
# having been opened solely to complete the OAuth redirect, so Home can show a
# "you can close this tab" banner (see render_oauth_success_banner).
_OAUTH_JUST_COMPLETED_KEY = "auth_oauth_completed_this_tab"

# OAuth authorization codes already exchanged, process-wide (single-use guard).
# See handle_oauth_callback: prevents a code being exchanged twice across reruns
# or a reconnected session, which the provider would reject as invalid/expired.
_HANDLED_CODES: set = set()

# Cookie settings
_COOKIE_NAME = "pb_auth"
_COOKIE_MAX_AGE_DAYS = 30

# GitHub OAuth endpoints
_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"

# ORCID OAuth endpoints (public API)
_ORCID_AUTHORIZE_URL = "https://orcid.org/oauth/authorize"
_ORCID_TOKEN_URL = "https://orcid.org/oauth/token"


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


def is_auth_configured() -> bool:
    """Check whether any OAuth provider is configured in secrets."""
    return _is_github_configured() or _is_orcid_configured()


def _is_github_configured() -> bool:
    return "auth" in st.secrets and "github" in st.secrets["auth"] and "client_id" in st.secrets["auth"]["github"]


def _is_orcid_configured() -> bool:
    return "auth" in st.secrets and "orcid" in st.secrets["auth"] and "client_id" in st.secrets["auth"]["orcid"]


def _is_cookie_enabled() -> bool:
    """Check if cookie-based session persistence is enabled."""
    try:
        return bool(st.secrets["auth"].get("use_cookies", False)) and bool(st.secrets["auth"].get("cookie_secret", ""))
    except (KeyError, FileNotFoundError):
        return False


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------


def _get_cookie_secret() -> str:
    return st.secrets["auth"]["cookie_secret"]


def _save_user_cookie(user: dict) -> None:
    """Save user info to a signed JWT cookie."""
    if not _is_cookie_enabled():
        return
    try:
        import jwt
        from extra_streamlit_components import CookieManager

        token = jwt.encode(user, _get_cookie_secret(), algorithm="HS256")
        # Distinct component key per operation: save, restore and delete may all
        # run within a single script rerun (e.g. restore + save on the OAuth
        # callback), and reusing one key would raise a Streamlit duplicate-key error.
        manager = CookieManager(key="pb_cookie_save")
        manager.set(_COOKIE_NAME, token, max_age=_COOKIE_MAX_AGE_DAYS * 86400)
    except Exception as e:
        logger.debug(f"Could not save auth cookie: {e}")


def _restore_user_from_cookie() -> None:
    """Restore user session from cookie if available.

    Runs on every rerun while the user is not signed in (not just once per
    session). This is what lets a tab the user is working in pick up a sign-in
    that completed in a separate browser tab: the other tab writes the shared
    browser cookie, and this tab reads it back on its next interaction without
    ever having navigated away (so its session state is preserved).
    """
    if not _is_cookie_enabled():
        return
    if get_current_user() is not None:
        return

    try:
        import jwt
        from extra_streamlit_components import CookieManager

        manager = CookieManager(key="pb_cookie_restore")
        token = manager.get(_COOKIE_NAME)
        if token:
            user = jwt.decode(token, _get_cookie_secret(), algorithms=["HS256"])
            st.session_state[_AUTH_USER_KEY] = user
    except Exception as e:
        logger.debug(f"Could not restore auth cookie: {e}")


def _delete_user_cookie() -> None:
    """Delete the auth cookie."""
    if not _is_cookie_enabled():
        return
    try:
        from extra_streamlit_components import CookieManager

        manager = CookieManager(key="pb_cookie_delete")
        manager.delete(_COOKIE_NAME)
    except Exception as e:
        logger.debug(f"Could not delete auth cookie: {e}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_current_user() -> dict | None:
    """Return the current authenticated user info, or None if not signed in.

    Returns
    -------
    dict or None
        Dict with keys: ``provider``, ``id``, ``name``, ``avatar_url``.
    """
    return st.session_state.get(_AUTH_USER_KEY)


def sign_out() -> None:
    """Clear the in-session identity and request cookie deletion on the next run.

    The cookie is not deleted inline. Deleting it renders a ``CookieManager``
    component that must reach the browser, but the sign-out button triggers an
    immediate ``st.rerun()`` that would discard that render (so the cookie would
    survive and the user would be silently restored from it). Instead we flag the
    deletion and carry it out at the very start of the next run, before the cookie
    is read back (see ``_process_pending_signout``).
    """
    st.session_state.pop(_AUTH_USER_KEY, None)
    st.session_state.pop(_COOKIE_RESTORED_KEY, None)
    if _is_cookie_enabled():
        st.session_state[_PENDING_SIGNOUT_KEY] = True
    else:
        _delete_user_cookie()


def _process_pending_signout() -> bool:
    """Delete the auth cookie if a sign-out was requested on the previous run.

    Returns
    -------
    bool
        True if a pending sign-out was handled (in which case the caller must
        skip restoring from the cookie this run, since the deletion has not yet
        reached the browser and a stale read would sign the user back in).
    """
    if not st.session_state.pop(_PENDING_SIGNOUT_KEY, False):
        return False
    _delete_user_cookie()
    return True


def _get_redirect_uri() -> str:
    """Return the OAuth redirect URI.

    Derived from the current app URL (base URL only). Must match the
    callback URL registered with the OAuth provider.
    """
    from urllib.parse import urlparse

    parsed = urlparse(st.context.url)
    return f"{parsed.scheme}://{parsed.netloc}"


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------


def _github_auth_url() -> str:
    """Build the GitHub OAuth authorization URL."""
    params = {
        "client_id": st.secrets["auth"]["github"]["client_id"],
        "redirect_uri": _get_redirect_uri(),
        "scope": "read:user",
        "state": "github",
    }
    return f"{_GITHUB_AUTHORIZE_URL}?{urlencode(params)}"


def _exchange_github_code(code: str) -> dict | None:
    """Exchange GitHub authorization code for user profile."""
    try:
        resp = requests.post(
            _GITHUB_TOKEN_URL,
            data={
                "client_id": st.secrets["auth"]["github"]["client_id"],
                "client_secret": st.secrets["auth"]["github"]["client_secret"],
                "code": code,
                "redirect_uri": _get_redirect_uri(),
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        token_data = resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            logger.warning(
                "GitHub OAuth: no access_token in token response (keys=%s, error=%s)",
                list(token_data.keys()),
                token_data.get("error_description") or token_data.get("error"),
            )
            return None

        user_resp = requests.get(
            _GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            timeout=10,
        )
        user_resp.raise_for_status()
        user_data = user_resp.json()

        return {
            "provider": "github",
            "id": user_data["login"],
            "name": user_data.get("name") or user_data["login"],
            "avatar_url": user_data.get("avatar_url"),
        }
    except requests.HTTPError as e:
        body = e.response.text[:500] if e.response is not None else ""
        logger.error("GitHub OAuth HTTP error: %s | body=%s", e, body)
        return None
    except Exception as e:
        logger.error(f"GitHub OAuth error: {e}")
        return None


# ---------------------------------------------------------------------------
# ORCID OAuth
# ---------------------------------------------------------------------------


def _orcid_auth_url() -> str:
    """Build the ORCID OAuth authorization URL."""
    params = {
        "client_id": st.secrets["auth"]["orcid"]["client_id"],
        "response_type": "code",
        "scope": "/authenticate",
        "redirect_uri": _get_redirect_uri(),
        "state": "orcid",
    }
    return f"{_ORCID_AUTHORIZE_URL}?{urlencode(params)}"


def _exchange_orcid_code(code: str) -> dict | None:
    """Exchange ORCID authorization code for user profile."""
    try:
        resp = requests.post(
            _ORCID_TOKEN_URL,
            data={
                "client_id": st.secrets["auth"]["orcid"]["client_id"],
                "client_secret": st.secrets["auth"]["orcid"]["client_secret"],
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _get_redirect_uri(),
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        token_data = resp.json()

        orcid_id = token_data.get("orcid")
        name = token_data.get("name")
        if not orcid_id:
            logger.warning(
                "ORCID OAuth: no orcid in token response (keys=%s, error=%s)",
                list(token_data.keys()),
                token_data.get("error_description") or token_data.get("error"),
            )
            return None

        return {
            "provider": "orcid",
            "id": orcid_id,
            "name": name or orcid_id,
            "avatar_url": None,
        }
    except requests.HTTPError as e:
        body = e.response.text[:500] if e.response is not None else ""
        logger.error("ORCID OAuth HTTP error: %s | body=%s", e, body)
        return None
    except Exception as e:
        logger.error(f"ORCID OAuth error: {e}")
        return None


# ---------------------------------------------------------------------------
# OAuth callback handling (runs on Home page after redirect)
# ---------------------------------------------------------------------------


def handle_oauth_callback() -> None:
    """Check for OAuth callback parameters and complete sign-in if present.

    An OAuth authorization code is single-use: exchanging it twice makes the
    provider reject the second attempt (GitHub: ``bad_verification_code``).
    ``_HANDLED_CODES`` guarantees each code is exchanged at most once in this
    process; any repeat just clears the URL and returns.

    IMPORTANT: this must run before any ``CookieManager`` component renders on the
    callback page (see ``render_auth_home``). Rendering a cookie component while
    the unexchanged ``?code=`` is still in the URL triggers a rerun that
    re-renders the sign-in (authorize) link, the browser re-hits the authorize
    endpoint, and GitHub invalidates the pending code before we can exchange it.
    """
    code = st.query_params.get("code")
    state = st.query_params.get("state")

    if get_current_user() is not None:
        # Already signed in: strip the leftover ``?code=...&state=...`` from the URL.
        if code or state:
            st.query_params.clear()
        return

    if not code or not state:
        return

    if code in _HANDLED_CODES:
        logger.info("OAuth callback: authorization code already handled; not re-exchanging")
        st.query_params.clear()
        return
    _HANDLED_CODES.add(code)
    # Bound the set: authorization codes are short-lived, so a hard cap is enough.
    if len(_HANDLED_CODES) > 256:
        _HANDLED_CODES.clear()
        _HANDLED_CODES.add(code)

    user = None
    if state == "github" and _is_github_configured():
        user = _exchange_github_code(code)
    elif state == "orcid" and _is_orcid_configured():
        user = _exchange_orcid_code(code)
    else:
        logger.warning("OAuth callback: unhandled or unconfigured state=%r", state)

    if user:
        logger.info("OAuth sign-in succeeded: provider=%s id=%s", user.get("provider"), user.get("id"))
        st.session_state[_AUTH_USER_KEY] = user
        st.session_state[_OAUTH_JUST_COMPLETED_KEY] = True
        _save_user_cookie(user)
        # Deliberately no st.rerun() here. Rerunning in the same run would discard
        # the CookieManager "set" delta before it reaches the browser, so the cookie
        # would never be written and cross-tab sign-in would silently fail. The
        # caller renders the signed-in badge on this same run (user is now set), the
        # cookie flushes to the browser at the end of the run, and the leftover URL
        # query params are cleared on the next run by the early-return branch above.
    else:
        logger.warning("OAuth sign-in failed: token/profile exchange returned no user (state=%r)", state)


# ---------------------------------------------------------------------------
# UI rendering
# ---------------------------------------------------------------------------


def _render_user_topright(user: dict, key_suffix: str = "") -> None:
    """Render the signed-in user popover in the top-right corner."""
    initials = "".join(w[0].upper() for w in user["name"].split() if w)[:2] or "?"
    popover_label = f":material/person: {initials}"

    _, right_col = st.columns([6, 1])
    with right_col:
        with st.popover(popover_label):
            if user["avatar_url"]:
                st.image(user["avatar_url"], width=48)
            else:
                st.markdown(
                    f'<div style="width:48px;height:48px;border-radius:50%;background:#4169E1;color:white;'
                    f'display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:700;">'
                    f"{initials}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(f"**{user['name']}**")
            provider_label = "GitHub" if user["provider"] == "github" else "ORCID"
            st.caption(f"Signed in via {provider_label}")
            st.caption(f"ID: `{user['id']}`")
            if st.button("Sign out", key=f"auth_sign_out{key_suffix}"):
                sign_out()
                st.rerun()


def _signin_link(label: str, url: str) -> str:
    """Return HTML for a sign-in link styled as a button that opens in a new tab.

    ``st.link_button`` navigates the current tab, which would tear down the
    Streamlit session (and any in-progress work) of the page the user is on.
    A plain anchor with ``target="_blank"`` runs the OAuth redirect in a new
    tab instead, leaving the working tab untouched.
    """
    return (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
        'style="display:block;box-sizing:border-box;width:100%;text-align:center;'
        "padding:0.5rem 1rem;margin-bottom:0.4rem;border-radius:0.5rem;"
        "border:1px solid rgba(49,51,63,0.2);text-decoration:none;color:inherit;"
        f'font-weight:600;">{label}</a>'
    )


def _render_signin_topright() -> None:
    """Render a sign-in popover in the top-right corner.

    Available on every page. The sign-in links open in a new browser tab so the
    current tab's session state is preserved; the signed-in identity flows back
    via the shared auth cookie on the working tab's next interaction.
    """
    _, right_col = st.columns([6, 1])
    with right_col:
        with st.popover("Sign in"):
            links = []
            if _is_github_configured():
                links.append(_signin_link("Sign in with GitHub", _github_auth_url()))
            if _is_orcid_configured():
                links.append(_signin_link("Sign in with ORCID", _orcid_auth_url()))
            st.markdown("".join(links), unsafe_allow_html=True)
            st.caption(
                "Opens in a new tab. After signing in, return to this tab and continue "
                "where you left off; your session and any in-progress work are preserved."
            )


def render_auth_status() -> None:
    """Render the auth control in the top-right corner of a module page.

    Shows the signed-in user badge when signed in, or the sign-in popover when
    not. Sign-in is available here (not only on the Home page); the links open
    in a new tab so this page's session state is preserved, and the identity is
    restored from the shared cookie once sign-in completes.

    The actual rendering happens in ``_render_auth_status_fragment``, an
    auto-refreshing ``st.fragment``: it periodically re-checks the cookie and
    swaps the sign-in popover for the signed-in badge in place, so a sign-in
    completed in another tab appears here without the user having to click or
    navigate. Being a fragment, its periodic reruns are scoped to just this
    small widget and never touch the rest of the page (uploaded files,
    computed results, ...).
    """
    if not is_auth_configured():
        return

    _render_auth_status_fragment()


@st.fragment(run_every="5s")
def _render_auth_status_fragment() -> None:
    if not _process_pending_signout():
        _restore_user_from_cookie()

    user = get_current_user()
    if user:
        _render_user_topright(user, key_suffix="_module")
    else:
        _render_signin_topright()


def render_auth_home() -> None:
    """Render sign-in handling on the Home page.

    Handles OAuth callbacks and shows the user badge if signed in.
    Sets a flag for ``render_signin_banner`` if not signed in.
    Sign-in buttons are shown in the banner above the leaderboard.

    The exchange for an OAuth callback (``?code=`` present) runs here, in the
    main (non-fragment) script body, on every real page load -- never inside
    the auto-refreshing fragment below. It must complete BEFORE any
    ``CookieManager`` component renders: rendering a cookie component first
    triggers a rerun that re-renders the authorize link while the single-use
    code is still in the URL, causing the browser to re-hit authorize and the
    provider to invalidate the code before we can exchange it.

    The rest of the widget (cookie restore + badge/popover) lives in
    ``_render_auth_home_fragment``, an auto-refreshing ``st.fragment``: it
    periodically re-checks the cookie so a sign-in completed in another tab
    appears here without the user having to click or navigate.
    """
    if not is_auth_configured():
        return

    if "code" in st.query_params:
        handle_oauth_callback()

    _render_auth_home_fragment()


@st.fragment(run_every="5s")
def _render_auth_home_fragment() -> None:
    if "code" not in st.query_params:
        if not _process_pending_signout():
            _restore_user_from_cookie()

    user = get_current_user()

    if user:
        _render_user_topright(user, key_suffix="_home")
    else:
        _render_signin_topright()
        st.session_state["_auth_show_signin_banner"] = True


def render_oauth_success_banner() -> None:
    """Render a "you can close this tab" banner at the top of the Home page.

    A sign-in click opens the identity provider in a new browser tab (so the tab
    the user was working in keeps its session), and that new tab lands back on
    the Home page once the provider redirects here. This tab exists only to
    complete the redirect, so show a banner telling the user they can close it
    once their other tab reflects the sign-in.

    Rendered as a banner on top of the normal Home page -- NOT as a page that
    replaces it. Replacing the full Home render with a minimal page broke the
    cookie write from reaching the browser (so the user's other tab never picked
    up the sign-in). Keeping the full render is what makes cross-tab reliable, so
    this only adds a message and changes nothing else about what renders.
    """
    if not st.session_state.get(_OAUTH_JUST_COMPLETED_KEY, False):
        return

    user = get_current_user()
    provider_label = "GitHub" if user and user.get("provider") == "github" else "ORCID"
    name = user.get("name") if user else None

    headline = f"You're signed in{f' as {name}' if name else ''} via {provider_label}." if user else "Sign-in complete."
    st.success(
        f"**{headline}** You can return to the tab you were working in -- it will show you "
        "signed in within a few seconds. You can then safely close this tab.",
        icon=":material/check_circle:",
    )


def render_signin_banner() -> None:
    """Render the sign-in encouragement banner above the leaderboard.

    Call this right before the leaderboard section on the Home page.
    Only renders if the user is not signed in.
    """
    if not st.session_state.pop("_auth_show_signin_banner", False):
        return

    st.markdown(
        '<div style="background:linear-gradient(135deg, #e3f2fd, #f3e5f5);border-radius:10px;'
        'padding:14px 20px;margin-bottom:16px;">'
        '<span style="font-size:1.05rem;font-weight:600;">'
        "\U0001f3c6 Get recognized for your benchmark contributions!</span><br>"
        '<span style="font-size:0.85rem;color:#444;">'
        "Sign in with your GitHub or ORCID account to have your name appear on the "
        "leaderboard when you submit benchmark runs. It's optional, but helps "
        "the community identify contributors and allows maintainers to direct questions. "
        "Use the <b>Sign in</b> button in the top-right corner to get started."
        "</span></div>",
        unsafe_allow_html=True,
    )


def render_upload_tab_signin_reminder() -> None:
    """Show a reminder on the upload/submit tab for non-signed-in users.

    Call this at the top of the upload tab (tab 2) in each module.

    Note: this does not read the cookie itself. ``render_auth_status`` (or
    ``render_auth_home`` on Home) runs earlier in the same script run -- via the
    sidebar during page setup -- and performs the single per-run cookie read.
    Reading the cookie again here would render a second ``CookieManager`` with
    the same component key in the same run and raise a duplicate-key error.
    """
    if not is_auth_configured():
        return

    if get_current_user() is not None:
        return

    st.info(
        "You are not signed in. Optionally sign in with GitHub or ORCID using the "
        "**Sign in** button in the top-right corner to get on the leaderboard! "
        "It opens in a new tab, so your work on this page is preserved.",
        icon=":material/person_add:",
    )
