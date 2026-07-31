# Submitter identity (OAuth sign-in and attribution)

ProteoBench can optionally attribute a submitted benchmark run to the person who
submitted it. This is entirely optional: the platform works fully without it, and a
submission made while signed out is stored anonymously, exactly as before this feature
existed.

## Overview

A user may sign in with **GitHub** or **ORCID** before submitting a benchmark run. If
they do, their provider id and display name are attached to the resulting datapoint and
shown publicly:

- in the PR description created for the submission,
- as `submitter_id` / `submitter_name` / `submitter_provider` fields on the stored
  datapoint JSON,
- on the Home page "Top Submitters" leaderboard.

Sign-in is available from every page (Home page hero row, or next to the module
documentation link on each module page tab header) and never interrupts in-progress
work: it opens the identity provider in a **new browser tab**, so the tab the user is
working in keeps its Streamlit session (uploaded files, computed results) intact. Once
sign-in completes, the identity is written to a signed cookie shared across tabs, and
the working tab picks it up automatically on its next interaction.

## Code layout

| File | Responsibility |
|------|----------------|
| `webinterface/pages/base_pages/utils/auth.py` | OAuth flows for GitHub and ORCID, cookie-based session persistence, sign-in/sign-out UI widgets |
| `webinterface/pages/base_pages/tabs/tab6_submit_results.py` | `generate_submitter_identity()` reads the current user and injects `submitter_id`/`submitter_name`/`submitter_provider` into `user_input`; `create_pull_request()` appends the identity to the PR body and stamps it onto the submission row |
| `proteobench/datapoint/quant_datapoint.py` | `QuantDatapointHYE` dataclass fields `submitter_id`, `submitter_name`, `submitter_provider` (defaults `""`), populated in `generate_datapoint()` from `user_input`. `QuantDatapointPYE` inherits them unchanged — its `generate_datapoint()` delegates to `QuantDatapointHYE.generate_datapoint()` for all non-plasma-specific fields |
| `proteobench/datapoint/denovo_datapoint.py` | Same three fields on `DenovoDatapoint`, populated the same way |
| `webinterface/pages/base_pages/utils/leaderboard.py` | `get_leaderboard_data()` clones every module's results repo and aggregates submitter statistics from the stored JSON files |
| `webinterface/Home.py` | Renders the "Top Submitters" leaderboard from `get_leaderboard_data()` |

## Configuration

OAuth is configured via `webinterface/.streamlit/secrets.toml` (gitignored, never
committed). Both providers are optional and independently toggled by whether their
section is present:

```toml
[auth]
cookie_secret = "..."      # random secret used to sign the identity cookie
use_cookies = true         # required for cross-tab sign-in propagation

[auth.github]
client_id = "..."
client_secret = "..."

[auth.orcid]
client_id = "..."
client_secret = "..."
```

`is_auth_configured()` (and the provider-specific `_is_github_configured()` /
`_is_orcid_configured()`) checks for the presence of these keys; if neither provider is
configured, all sign-in UI is hidden and the feature is fully inert. Treat the values in
`secrets.toml` as live credentials: never paste them into documentation, commit
messages, or code comments.

The OAuth redirect URI is derived from the current request URL
(`_get_redirect_uri()` in `auth.py`) and must match the callback URL registered with
each provider.

## Data flow

1. **Sign-in** (any page): `auth.py` completes the OAuth code exchange and stores
   `{"provider", "id", "name", "avatar_url"}` in `st.session_state`, then persists it to
   a signed cookie (`_save_user_cookie`) so other tabs pick it up.
2. **Datapoint creation (Tab 2, upload)**: `ionmodule.benchmarking()` builds the
   datapoint from the uploaded file. At this point the submitter identity has **not**
   been read yet — `generate_submitter_identity()` only runs later, in Tab 6 — so the
   datapoint's `submitter_id`/`submitter_name`/`submitter_provider` fields are empty at
   creation time.
3. **Submission (Tab 6)**: `generate_submitter_identity()` reads the signed-in user (if
   any) and injects the three fields into `user_input`. `create_pull_request()` then:
   - appends `Submitter: {name} ({provider}: {id})` to the PR body's user comments,
   - stamps the same three fields directly onto the last "new" row of the submission
     DataFrame (`submission_df.loc[last_new_idx, "submitter_id"] = ...`), since that row
     was created back in Tab 2 before the identity was known.
4. **Storage**: the datapoint is serialized to the result JSON in the
   `Proteobot/Results_*` repo (via the usual PR flow), including the submitter fields.
5. **Leaderboard**: `get_leaderboard_data()` clones each module's public
   `Proteobench/Results_*` repo, reads `submitter_id` out of every JSON file, and
   aggregates submission counts per submitter. Anonymous submissions (empty
   `submitter_id`) are skipped. The result is cached for one hour
   (`@st.cache_data(ttl=3600)`).

## For PR reviewers

When reviewing a submission PR (see {doc}`reviewing-new-point-pr`), check the PR
description for a `Submitter: <name> (<provider>: <id>)` line. Its absence means the
point was submitted anonymously (the submitter was not signed in), not that anything is
wrong with the submission.

## Adding a new module

No extra work is required to support submitter identity in a new quant module: if it calls `QuantDatapointHYE.generate_datapoint()` (directly, or transitively like
`QuantDatapointPYE` does), the three fields are populated automatically from
`user_input`. A brand-new datapoint class that does not subclass `QuantDatapointHYE` would need to declare and populate the three fields
itself, following the pattern in `QuantDatapointHYE`/`DenovoDatapoint`.
