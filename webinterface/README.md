# Proteobench web interface

Start the streamlit GUI from your terminal with the following commands.

```bash
streamlit run Home.py
```

## Session state

In VSCode you can search under this folder, `webinterface`, for `session_state` to see
how it is used in the code. This page tries to summarize some of the usage.

### Naming Convention

Each module (page) has its own namespace in the session state. This allows switching between
module pages without the session state of one module interfering with another.

Every session state key is defined as a string field inside the module's `dataclass` in
[`pages_variables`](pages/pages_variables/). All string values **must** include a
module-specific suffix (e.g. `_dda_quant_QExactive`, `_dia_quant_Astral`) so that keys
from different modules never collide.

Example — reading a value:
```python
# key resolved via the dataclass, e.g. "all_datapoints_dda_quant_QExactive"
st.session_state[self.variables.all_datapoints]
```

Example — toggling the submit flag:
```python
st.session_state[self.variables.submit] = False   # e.g. "submit_dda_quant_QExactive"
```

### Module suffix reference

| Module | Suffix |
|--------|--------|
| DDA QExactive | `_dda_quant_QExactive` |
| DDA Astral | `_dda_quant_Astral` |
| DDA peptidoform | `_dda_quant_peptidoform` |
| DIA AIF | `_dia_quant` |
| DIA Astral | `_dia_quant_Astral` |
| DIA diaPASEF | `_dia_quant_diaPASEF` |
| DIA singlecell | `_dia_quant_singlecell` |
| DIA ZenoTOF | `_dia_quant_ZenoTOF` |
| DIA Plasma | `_dia_quant_Plasma` |
| De Novo HCD | `_dda_hcd_denovo` |

### Debug panel

A collapsible **🔧 Debug: Session State** expander is available at the bottom of the
sidebar on every page. It lists all current session state keys grouped into:

- **Data keys** – module data such as `DataFrame`s, booleans, strings
- **Widget/UUID keys** – internal Streamlit widget identifiers (UUID values)

A standalone `render_session_state_debug(variables)` helper is also available in
`webinterface/streamlit_utils.py` for rendering a module-scoped view inline on a page.

## Session state keys reference

All keys are accessed exclusively through the variables dataclass; never use raw string
literals for session state. The keys used across modules are:

```python
# Submission flow
st.session_state[self.variables.submit]
st.session_state[self.variables.check_submission]
st.session_state[self.variables.check_submission_uuid]

# Parameter files
st.session_state[self.variables.params_file_dict]
st.session_state[self.variables.params_json_dict]

# UI element widget identifiers (hold UUID values)
st.session_state[self.variables.slider_id_uuid]
st.session_state[self.variables.slider_id_submitted_uuid]
st.session_state[self.variables.selectbox_id_uuid]
st.session_state[self.variables.selectbox_id_submitted_uuid]
st.session_state[self.variables.table_id_uuid]
st.session_state[self.variables.download_selector_id_uuid]
st.session_state[self.variables.dataset_selector_id_uuid]
st.session_state[self.variables.meta_file_uploader_uuid]
st.session_state[self.variables.comments_submission_uuid]
st.session_state[self.variables.button_submission_uuid]

# Placeholders (Streamlit empty/container objects)
st.session_state[self.variables.placeholder_table]
st.session_state[self.variables.placeholder_slider]
st.session_state[self.variables.placeholder_downloads_container]
st.session_state[self.variables.placeholder_dataset_selection_container]
st.session_state[self.variables.placeholder_fig_compare]

# Highlight lists
st.session_state[self.variables.highlight_list]
st.session_state[self.variables.highlight_list_submitted]

# Data
st.session_state[self.variables.all_datapoints]
st.session_state[self.variables.all_datapoints_submitted]
st.session_state[self.variables.all_datapoints_submission]
st.session_state[self.variables.input_df]
st.session_state[self.variables.input_df_submission]
st.session_state[self.variables.result_perf]
st.session_state[self.variables.result_performance_submission]

# Metadata / submission text
st.session_state[self.variables.meta_data]
st.session_state[self.variables.meta_data_text]
st.session_state[self.variables.df_head]

# Cached figures
st.session_state[self.variables.fig_logfc]
st.session_state[self.variables.fig_metric]
st.session_state[self.variables.fig_cv]
st.session_state[self.variables.fig_ma_plot]
```

