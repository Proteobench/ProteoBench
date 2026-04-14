"""
Optional OAuth authentication for ProteoBench submitter identification.

Supports GitHub and ORCID as identity providers. Authentication is entirely
optional -- the application works fully without it. When configured (via
secrets.toml) and the user chooses to sign in, their identity is stored in
a cookie and automatically attached to public submissions.

Sign-in is only available on the Home page. Other pages show the signed-in
user but do not offer sign-in buttons, to avoid redirecting away from work
in progress.
"""

import logging
from urllib.parse import urlencode

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# Session state key for the authenticated user
_AUTH_USER_KEY = "auth_user"
_COOKIE_RESTORED_KEY = "auth_cookie_restored"

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
        manager = CookieManager(key="pb_cookie_manager")
        manager.set(_COOKIE_NAME, token, max_age=_COOKIE_MAX_AGE_DAYS * 86400)
    except Exception as e:
        logger.debug(f"Could not save auth cookie: {e}")


def _restore_user_from_cookie() -> None:
    """Restore user session from cookie if available."""
    if not _is_cookie_enabled():
        return
    if get_current_user() is not None:
        return
    if st.session_state.get(_COOKIE_RESTORED_KEY):
        return

    st.session_state[_COOKIE_RESTORED_KEY] = True
    try:
        import jwt
        from extra_streamlit_components import CookieManager

        manager = CookieManager(key="pb_cookie_manager")
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

        manager = CookieManager(key="pb_cookie_manager")
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
    """Clear authentication state and cookie."""
    if _AUTH_USER_KEY in st.session_state:
        del st.session_state[_AUTH_USER_KEY]
    if _COOKIE_RESTORED_KEY in st.session_state:
        del st.session_state[_COOKIE_RESTORED_KEY]
    _delete_user_cookie()


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
            logger.warning("GitHub OAuth: no access_token in response")
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
            logger.warning("ORCID OAuth: no orcid in response")
            return None

        return {
            "provider": "orcid",
            "id": orcid_id,
            "name": name or orcid_id,
            "avatar_url": None,
        }
    except Exception as e:
        logger.error(f"ORCID OAuth error: {e}")
        return None


# ---------------------------------------------------------------------------
# OAuth callback handling (runs on Home page after redirect)
# ---------------------------------------------------------------------------


def handle_oauth_callback() -> None:
    """Check for OAuth callback parameters and complete sign-in if present."""
    if get_current_user() is not None:
        return

    params = st.query_params
    code = params.get("code")
    state = params.get("state")

    if not code or not state:
        return

    user = None
    if state == "github" and _is_github_configured():
        user = _exchange_github_code(code)
    elif state == "orcid" and _is_orcid_configured():
        user = _exchange_orcid_code(code)

    if user:
        st.session_state[_AUTH_USER_KEY] = user
        _save_user_cookie(user)
        st.query_params.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# UI rendering
# ---------------------------------------------------------------------------


def render_auth_status() -> None:
    """Render the signed-in user indicator in the top-right corner.

    Shows the user's initials/avatar if signed in, or nothing if not.
    This is displayed on all pages **except** the Home page. It does NOT
    offer sign-in buttons — sign-in only happens on the Home page.
    """
    if not is_auth_configured():
        return

    _restore_user_from_cookie()

    user = get_current_user()
    if not user:
        return

    _, right_col = st.columns([6, 1])
    with right_col:
        initials = "".join(w[0].upper() for w in user["name"].split() if w)[:2] or "?"
        popover_label = f":material/person: {initials}"

        with st.popover(popover_label):
            if user["avatar_url"]:
                st.image(user["avatar_url"], width=48)
            else:
                initials = "".join(w[0].upper() for w in user["name"].split() if w)[:2] or "?"
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
            if st.button("Sign out", key="auth_sign_out"):
                sign_out()
                st.rerun()


def render_auth_home() -> None:
    """Render the sign-in section on the Home page.

    This is the only place where sign-in buttons are shown. After OAuth
    redirect, the user lands back on the Home page and the callback is
    handled here.
    """
    if not is_auth_configured():
        return

    _restore_user_from_cookie()
    handle_oauth_callback()

    user = get_current_user()

    if user:
        _, right_col = st.columns([6, 1])
        with right_col:
            initials = "".join(w[0].upper() for w in user["name"].split() if w)[:2] or "?"
            popover_label = f":material/person: {initials}"

            with st.popover(popover_label):
                if user["avatar_url"]:
                    st.image(user["avatar_url"], width=48)
                else:
                    initials = "".join(w[0].upper() for w in user["name"].split() if w)[:2] or "?"
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
                if st.button("Sign out", key="auth_sign_out_home"):
                    sign_out()
                    st.rerun()
    else:
        # Sign-in button in the top-right corner
        _, right_col = st.columns([6, 1])
        with right_col:
            with st.popover("Sign in"):
                if _is_github_configured():
                    st.link_button("Sign in with GitHub", _github_auth_url())
                if _is_orcid_configured():
                    st.link_button("Sign in with ORCID", _orcid_auth_url())
        # Flag to render encouragement banner after the welcome message
        st.session_state["_auth_show_signin_banner"] = True


def render_signin_banner() -> None:
    """Render the sign-in encouragement banner below the welcome message.

    Call this after the welcome/preface section on the Home page.
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
        "leaderboard (see below) when you submit benchmark runs. It's optional, but helps "
        "the community identify contributors and allows maintainers to direct questions. "
        "Use the <b>Sign in</b> button in the top-right corner to get started."
        "</span></div>",
        unsafe_allow_html=True,
    )
