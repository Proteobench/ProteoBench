import pandas as pd
import streamlit as st

st.title("Session State Debug")

MAX_LIST_REPR = 5  # max items shown inline for lists


def summarize_value(val):
    """Return a short, human-readable summary of a session state value."""
    if isinstance(val, pd.DataFrame):
        return f"<DataFrame shape={val.shape} columns={list(val.columns)}>"
    if isinstance(val, list):
        if len(val) <= MAX_LIST_REPR:
            return repr(val)
        preview = repr(val[:MAX_LIST_REPR])[:-1] + f", ... +{len(val) - MAX_LIST_REPR} more]"
        return preview
    return val


# ── Overview table ─────────────────────────────────────────────────────────────
st.subheader("Overview")

st.write(st.session_state)

rows = []
for key, val in st.session_state.items():
    rows.append(
        {
            "key": str(key),
            "type": type(val).__name__,
            "summary": summarize_value(val),
        }
    )

if rows:
    st.dataframe(
        pd.DataFrame(rows).set_index("key"),
        use_container_width=True,
        height=min(40 + 35 * len(rows), 500),
    )
else:
    st.info("Session state is empty.")

# ── Per-key inspector ──────────────────────────────────────────────────────────
st.subheader("Inspect key")

keys = list(st.session_state.keys())
if keys:
    selected = st.selectbox("Select a key", options=keys, format_func=str)

    val = st.session_state[selected]

    if isinstance(val, pd.DataFrame):
        st.write(f"**DataFrame** — shape `{val.shape}`, columns: `{list(val.columns)}`")
        st.dataframe(val, use_container_width=True)
    elif isinstance(val, list):
        st.write(f"**list** — {len(val)} items")
        for i, item in enumerate(val):
            with st.expander(f"[{i}]  {repr(item)[:120]}", expanded=False):
                if isinstance(item, pd.DataFrame):
                    st.dataframe(item, use_container_width=True)
                else:
                    st.write(item)
    elif isinstance(val, dict):
        st.write(f"**dict** — {len(val)} keys")
        st.json({k: summarize_value(v) if isinstance(v, (pd.DataFrame, list)) else v for k, v in val.items()})
    else:
        st.write(val)
else:
    st.info("No keys to inspect.")
