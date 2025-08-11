# Proteobench web inteface 

Start the streamlit GUI from your terminal with the following commands. 

```bash
streamlit run Home.py
```

## Session state


In VSCode you can search under this folder, `webinterface`, for `session_state` to see 
how it is used in the code. This page tries to summarize some of the usage.

### Submission State

Each module (page) has it's own state for submission. This allows switching between module
pages without losing the information for the Streamlit session for each module.

```python
st.session_state[self.variables_dda_quant.submit] = False
st.session_state[self.variables_quant.submit] = True
```

The key to be used in the session state is defined by the `dataclass` for the module 
in [`pages_variables`](pages/pages_variables/) to ensure separated namespaces. Each 
class should have the same attributes with different values assigned. 

Some other attributes can be set on the fly, e.g. `input_df`.

So separating the keys set in the `dataclass`es from the actual data could be a
good first step to more easily understand the session state.

## Information

> [!NOTE]
> This overview is not yet completly checked. An analysis of set variables between the
> modules is still pending.

```python
# parsed parameter file for module, e.g. "params_file_dict_lfq_ion_dda_quant_astral"
st.session_state[self.variables_quant.params_file_dict] = {}
st.session_state[self.variables_quant.params_file_dict] = params.__dict__
# UI element string identifiers, e.g. slider ID 
st.session_state[self.variables_quant.slider_id_submitted_uuid] = 'uuid'
st.session_state[self.variables_quant.slider_id_uuid] = 'uuid'
st.session_state[self.variables_quant.selectbox_id_submitted_uuid] = 'uuid'
st.session_state[self.variables_quant.table_id_uuid] = 'uuid'
# data
st.session_state[self.variables_quant.all_datapoints]
st.session_state[self.variables_quant.all_datapoints_submitted]

st.session_state[self.variables_quant.input_df] # string key
st.session_state[self.variables_quant.input_df_submission] # string key
st.session_state[self.variables_quant.all_datapoints_submission].columns # DataFrame

st.session_state[self.variables_quant.result_perf]
```

So in general everthing scoped with a variable `variables_quant`, which is a `dataclass` 
is a list of dictionary keys (unique to the model). For now the session state is a flat
dictionary with many keys, which are kept separated by unique keys for each entry. One 
could also imagine to use a nested dictionary structure, e.g. with the module name as the first key
and the variable name as the second key. This would allow to have a more scoped session state
by namespaces defined by dictionary keys: `st.session_state.module_name.variable_name`



Other keys:
```python
st.session_state[self.variables_quant.submit]
st.session_state[self.variables_quant.params_file_dict]
st.session_state[self.variables_quant.params_json_dict]
st.session_state[self.variables_quant.slider_id_uuid]
st.session_state[self.variables_quant.slider_id_submitted_uuid]
st.session_state[self.variables_quant.selectbox_id_uuid]
st.session_state[self.variables_quant.selectbox_id_submitted_uuid]
st.session_state[self.variables_quant.table_id_uuid]
st.session_state[self.variables_quant.placeholder_table]
st.session_state[self.variables_quant.placeholder_slider]
st.session_state[self.variables_quant.placeholder_downloads_container]
st.session_state[self.variables_quant.download_selector_id_uuid]
st.session_state[self.variables_quant.highlight_list]
st.session_state[self.variables_quant.highlight_list_submitted]
st.session_state[self.variables_quant.all_datapoints]
st.session_state[self.variables_quant.all_datapoints_submitted]
st.session_state[self.variables_quant.all_datapoints_submission]
st.session_state[self.variables_quant.input_df]
st.session_state[self.variables_quant.input_df_submission]
st.session_state[self.variables_quant.result_perf]
st.session_state[self.variables_quant.result_performance_submission]
st.session_state[self.variables_quant.meta_data]
st.session_state[self.variables_quant.meta_data_text]
st.session_state[self.variables_quant.meta_file_uploader_uuid]
st.session_state[self.variables_quant.comments_submission_uuid]
st.session_state[self.variables_quant.check_submission]
st.session_state[self.variables_quant.check_submission_uuid]
st.session_state[self.variables_quant.button_submission_uuid]
st.session_state[self.variables_quant.df_head]
st.session_state[self.variables_quant.fig_logfc]
st.session_state[self.variables_quant.fig_metric]
st.session_state[self.variables_quant.fig_cv]
st.session_state[self.variables_quant.fig_ma_plot]
st.session_state[self.variables_quant.placeholder_fig_compare]
```
