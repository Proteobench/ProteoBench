"""Streamlit-based web interface for ProteoBench."""

import copy
import glob
import json
import logging
import os
import tempfile
import uuid
import zipfile
from datetime import datetime
from pprint import pformat
from typing import Any, Dict, Optional

import pages.texts.proteobench_builder as pbb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_utils
from pages.pages_variables.DeNovo.lfq_DDA_HCD_variables import (
    VariablesDDADeNovo,
)
from streamlit_extras.let_it_rain import rain

from proteobench.io.params import ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.io.parsing.utils import add_maxquant_fixed_modifications
from proteobench.modules.denovo.denovo_lfq_DDA_HCD import (
    DDAHCDDeNovoModule as IonModule,
)
from proteobench.plotting.plot_denovo import PlotDataPoint

logger: logging.Logger = logging.getLogger(__name__)


class DeNovoUIObjects():
    """
    Main class for the Streamlit interface of ProteoBench de novo identification.
    This class handles the creation of the Streamlit UI elements, including the main page layout,
    input forms, results display, and data submission elements.

    Parameters
    ----------
    variables_denovo : VariablesDDAQuant
        The variables for the quantification module.
    ionmodule : IonModule
        The quantification module.
    parsesettingsbuilder : ParseSettingsBuilder
        The parse settings builder.
    """
    def __init__(
            self,
            variables_denovo: VariablesDDADeNovo,
            ionmodule: IonModule,
            parsesettingsbuilder: ParseSettingsBuilder
    ) -> None:
        """
        Initialize the Streamlit UI objects for the de novo modules.

        Parameters
        ----------
        variables_denovo : VariablesDDADeNovo
            The variables for the de novo module.
        ionmodule : IonModule
            The de novo module.
        parsesettingsbuilder : ParseSettingsBuilder
            The parse settings builder.
        """
        self.variables_denovo: VariablesDDADeNovo = variables_denovo
        self.ionmodule: IonModule = ionmodule
        self.parsesettingsbuilder: ParseSettingsBuilder = parsesettingsbuilder
        self.user_input: Dict[str, Any] = dict()

        # Create page config and sidebar
        pbb.proteobench_page_config()

        self.first_point_plotted = False
        st.session_state[self.variables_denovo.submit] = False
        self.stop_duplicating = False

        if self.variables_denovo.params_file_dict not in st.session_state.keys():
            st.session_state[self.variables_denovo.params_file_dict] = dict()
        # if self.variables_denovo.radio_level_id_submitted_uuid not in st.session_state.keys():
        #     st.session_state[self.variables_denovo.radio_level_id_submitted_uuid] = str()
        # if self.variables_denovo.radio_evaluation_id_submitted_uuid not in st.session_state.keys():
        #     st.session_state[self.variables_denovo.radio_evaluation_id_submitted_uuid] = str()

        self.level_mapping = {"Peptide": "peptide", "Amino Acid": "aa"}
        self.level_mapping_submitted = {"Peptide": "peptide", "Amino Acid": "aa"}
        self.evaluation_type_mapping = {"Exact": "exact", "Mass-based": "mass"}

    ####################
    ### MAIN METHODS ###
    ####################
    def display_all_data_results_main(self):
        """Display the results for all data in Tab 1."""
        st.title("Results (All Data)")
        self._initialize_main_radios()
        self._generate_main_radios()
        self._generate_main_selectbox()
        self._display_existing_results()


    def display_submission_form(self) -> None:
        """
        Create the main submission form for the Streamlit UI in Tab 2.
        """
        with st.form(key="main_form"):
            self._generate_input_fields()
            self._generate_additional_parameters_fields()

            st.markdown(self.variables_denovo.texts.ShortMessages.run_instructions)
            submit_button = st.form_submit_button("Parse and bench", help=self.variables_denovo.texts.Help.parse_button)

        if submit_button:
            self._process_submission_form()

    def display_indepth_plots(self) -> None:
        """
        Display the dataset selection dropdown and plot the selected dataset (Tab 3).
        """
        if self.variables_denovo.all_datapoints_submitted not in st.session_state:
            self._initialize_main_data_points()
            st.session_state[self.variables_denovo.all_datapoints_submitted] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_denovo.all_datapoints]
            )

        if self.variables_denovo.all_datapoints_submitted not in st.session_state.keys():
            st.error("No data available for plotting.", icon="🚨")
            return
        if st.session_state[self.variables_denovo.all_datapoints_submitted].empty:
            st.error("No data available for plotting.", icon="🚨")
            return
        downloads_df = st.session_state[self.variables_denovo.all_datapoints_submitted][["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        if self.variables_denovo.placeholder_dataset_selection_container not in st.session_state.keys():
            st.session_state[self.variables_denovo.placeholder_dataset_selection_container] = st.empty()
            st.session_state[self.variables_denovo.dataset_selector_id_uuid] = uuid.uuid4()

        st.subheader("Select dataset to plot")

        dataset_options = [("Uploaded dataset", None)] + list(
            zip(downloads_df["id"], downloads_df["intermediate_hash"])
        )

        dataset_selection = st.multiselect(
            label="Select datasets",
            options=dataset_options,
            key=st.session_state[self.variables_denovo.dataset_selector_id_uuid],
            format_func=lambda x: x[0],
            default=[dataset_options[0]]
        )

        modifications = ['M-Oxidation', 'Q-Deamidation', 'N-Deamidation', 'N-term Acetylation', 'N-term Carbamylation', 'N-term Ammonia-loss']
        feature_names = [
            'Missing Fragmentation Sites',
            'Peptide Length',
            '% Explained Intensity'
        ]

        selected_dtps = st.session_state[self.variables_denovo.all_datapoints_submitted][
            st.session_state[self.variables_denovo.all_datapoints_submitted]['id'].isin(
                [dtp_id for dtp_id, _ in dataset_selection]
            )
        ]

        self._generate_ptm_plots(
            df=selected_dtps,
            modifications=modifications
        )

        self._generate_spectrum_feature_plots(
            df=selected_dtps,
            feature_names=feature_names
        )

        self._generate_species_plot(
            df=selected_dtps
        )

        st.markdown("# Spectrum overlap")
    

        public_id_selected_hash_list = dataset_selection
        # self._generate_indepth_plots(True, public_id=public_id, public_hash=selected_hash)

    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 4."""
        st.title("Results (All Data)")
        self._initialize_submitted_radios()
        self._generate_submitted_radios()
        self._generate_submitted_selectbox()
        self._display_submitted_results()

    def display_public_submission_ui(self) -> None:
        """Display the public submission section of the page in Tab 5."""
        # Initialize Unchecked submission box variable
        if self.variables_denovo.check_submission not in st.session_state:
            st.session_state[self.variables_denovo.check_submission] = False
        if self.variables_denovo.first_new_plot:
            self._generate_submission_ui_elements()

        if self.user_input[self.variables_denovo.meta_data]:
            params = self._load_user_parameters()
            st.session_state[self.variables_denovo.params_file_dict] = params.__dict__
            self.params_file_dict_copy = copy.deepcopy(params.__dict__)
            print(self.params_file_dict_copy)
            self._generate_additional_parameters_fields_submission()
            self._generate_comments_section()
            self._generate_confirmation_checkbox()
        else:
            params = None

        if st.session_state[self.variables_denovo.check_submission] and params != None:
            get_form_values = self.get_form_values()
            params = ProteoBenchParameters(**get_form_values)
            pr_url = self.submit_to_repository(params)
        if self.submission_ready == False:
            return
        if (
            st.session_state[self.variables_denovo.check_submission]
            and params != None
            and self.variables_denovo.submit in st.session_state
            and pr_url != None
        ):
            self.show_submission_success_message(pr_url)

    #####################
    ### TAB 1 METHODS ###
    #####################
    def _initialize_main_radios(self):
        """
        Initialize the radios for the main data.
        """
        # Radio for level (Peptide or Amino Acid)
        if self.variables_denovo.radio_level_id_uuid not in st.session_state.keys():
            st.session_state[self.variables_denovo.radio_level_id_uuid] = uuid.uuid4()
        
        if st.session_state[self.variables_denovo.radio_level_id_uuid] not in st.session_state.keys():
            st.session_state[st.session_state[self.variables_denovo.radio_level_id_uuid]] = (
                self.variables_denovo.default_level
            )

        # Radio for evaluation type (Exact or Mass-Based)
        if self.variables_denovo.radio_evaluation_id_uuid not in st.session_state.keys():
            st.session_state[self.variables_denovo.radio_evaluation_id_uuid] = uuid.uuid4()
        
        if st.session_state[self.variables_denovo.radio_evaluation_id_uuid] not in st.session_state.keys():
            st.session_state[st.session_state[self.variables_denovo.radio_evaluation_id_uuid]] = (
                self.variables_denovo.default_evaluation
            )

    def _generate_main_radios(self) -> None:
        """
        Create the radios input.
        """
        # TODO: Maybe add a bit of description?
        st.markdown(
            open(
                self.variables_denovo.description_radios_md, "r"
            ).read()
        )

        st.radio(
            "Select at which level precision is calculated",
            options=["Peptide", "Amino Acid"],
            horizontal=True,
            key=st.session_state[self.variables_denovo.radio_level_id_uuid],
            help="Toggle between different levels of precision calculation"
        )

        st.radio(
            "Select the stringency of evaluation",
            options=["Exact", "Mass-based"],
            horizontal=True,
            key=st.session_state[self.variables_denovo.radio_evaluation_id_uuid],
            help="Toggle between amino acid identify (Exact) matching and an equal mass-based matching."
        )


    def _generate_main_selectbox(self):
        """
        Create the selectbox for the Streamlit UI.
        """
        if self.variables_denovo.selectbox_id_uuid not in st.session_state.keys():
            st.session_state[self.variables_denovo.selectbox_id_uuid] = uuid.uuid4()
        
        try:
            st.selectbox(
                "Select label to plot",
                [
                    "None",
                    "checkpoint",
                    "n_beams",
                    "precursor_mass_tolerance",
                    "decoding_strategy"
                ],
                key=st.session_state[self.variables_denovo.selectbox_id_uuid],
            )
        except Exception as e:
            st.error(f"Unable to create the selectbox {e}", icon="🚨")

    def _display_existing_results(self):
        """
        Display the results section of the page for existing data.
        """
        self._initialize_main_data_points()

        try:
            fig_metric = PlotDataPoint.plot_metric(
                benchmark_metrics_df=st.session_state[self.variables_denovo.all_datapoints],
                label=st.session_state[st.session_state[self.variables_denovo.selectbox_id_uuid]],
                level=self.level_mapping[
                    st.session_state[st.session_state[self.variables_denovo.radio_level_id_uuid]]
                ],
                evaluation_type=self.evaluation_type_mapping[
                    st.session_state[st.session_state[self.variables_denovo.radio_evaluation_id_uuid]]
                ]
            )
            st.plotly_chart(
                fig_metric,
                use_container_width=True,
                key=self.variables_denovo.fig_metric
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")
        
        st.dataframe(st.session_state[self.variables_denovo.all_datapoints])
        self._display_download_section()


    def _initialize_main_data_points(self):
        """
        Initialize the all_datapoionts variable in the session state.
        """
        if self.variables_denovo.all_datapoints not in st.session_state.keys():
            st.session_state[self.variables_denovo.all_datapoints] = None
            st.session_state[self.variables_denovo.all_datapoints] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_denovo.all_datapoints]
            )

    def _display_download_section(self, reset_uuid=False) -> None:
        """
        Render the selector and area for raw data download.

        Parameters
        ----------
        reset_uuid : bool, optional
            Whether to reset the UUID, by default False.
        """
        # TODO: What to put in secrets.toml to make this work?
        if len(st.session_state[self.variables_denovo.all_datapoints]) == 0:
            st.error("No data available for download.", icon="🚨")
            return

        downloads_df = st.session_state[self.variables_denovo.all_datapoints][["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        if self.variables_denovo.placeholder_downloads_container not in st.session_state.keys() or reset_uuid:
            st.session_state[self.variables_denovo.placeholder_downloads_container] = st.empty()
            st.session_state[self.variables_denovo.download_selector_id_uuid] = uuid.uuid4()

        with st.session_state[self.variables_denovo.placeholder_downloads_container].container(border=True):
            st.subheader("Download raw datasets")

            st.selectbox(
                "Select dataset",
                downloads_df["intermediate_hash"],
                index=None,
                key=st.session_state[self.variables_denovo.download_selector_id_uuid],
                format_func=lambda x: downloads_df["id"][x],
            )

            if (
                st.session_state[st.session_state[self.variables_denovo.download_selector_id_uuid]] != None
                and st.secrets["storage"]["dir"] != None
            ):
                dataset_path = (
                    st.secrets["storage"]["dir"]
                    + "/"
                    + st.session_state[st.session_state[self.variables_denovo.download_selector_id_uuid]]
                )
                if os.path.isdir(dataset_path):
                    files = os.listdir(dataset_path)
                    for file_name in files:
                        path_to_file = dataset_path + "/" + file_name
                        with open(path_to_file, "rb") as file:
                            st.download_button(file_name, file, file_name=file_name)
                else:
                    st.write("Directory for this dataset does not exist, this should not happen.")
    
    #####################
    ### TAB 2 METHODS ###
    #####################
    def _generate_input_fields(self):
        """
        Create the input section of the form.
        """
        st.subheader("Input files")
        st.markdown(open(self.variables_denovo.description_input_file_md, "r").read())
        self.user_input["input_format"] = st.selectbox(
            "Software tool",
            self.parsesettingsbuilder.INPUT_FORMATS,
            help=self.variables_denovo.texts.Help.input_format,
        )
        self.user_input["input_csv"] = st.file_uploader(
            "Software tool result file", help=self.variables_denovo.texts.Help.input_file
        )

    def _generate_additional_parameters_fields(self):
        """
        Create the additional parameters section of the form and initialize the parameter fields.
        """
        with open(self.variables_denovo.additional_params_json) as file:
            config = json.load(file)
        for key, value in config.items():
            if key.lower() == "software_name":
                editable = False
            else:
                editable = True
        
            if key == "comments_for_plotting":
                self.user_input[key] = self._generate_input_widget(
                    self.user_input["input_format"],
                    value,
                    editable
                )
            else:
                self.user_input[key] = None

    def _process_submission_form(self):
        """
        Handle the form submission logic.

        Returns
        -------
        bool, optional
            Whether the submission was handled unsuccessfully.
        """
        if not self.user_input["input_csv"]:
            st.error(":x: Please provide a result file", icon="🚨")
            return False
        self._execute_proteobench()
        self.first_point_plotted = True

        # Inform the user with a link to the next tab
        st.info(
            "Form submitted successfully! Please navigate to the 'Results In-Depth' or 'Results New Data' tab for the next step."
        )

    def _execute_proteobench(self):
        """
        Execute the benchmarking process and returns the results.

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
            The benchmarking results, all data points, and the input data frame.
        """
        if self.variables_denovo.all_datapoints_submitted not in st.session_state:
            self._initialize_main_data_points()
        
        result_performance, all_datapoints, input_df = self._run_benchmarking_process()
        st.session_state[self.variables_denovo.all_datapoints_submitted] = all_datapoints

        self._set_highlight_column_in_submitted_data()

        st.session_state[self.variables_denovo.result_perf] = result_performance
        st.session_state[self.variables_denovo.input_df] = input_df

    def _run_benchmarking_process(self):
        """
        Execute the benchmarking process and returns the results.

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
            The benchmarking results, all data points, and the input data frame.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(self.user_input["input_csv"].getvalue().decode("utf-8"))
            temp_file_path = tmp_file.name

        # reload buffer: https://stackoverflow.com/a/64478151/9684872
        self.user_input["input_csv"].seek(0)

        if st.session_state[self.variables_denovo.radio_level_id_submitted_uuid] in st.session_state.keys():
            set_level_val = st.session_state[st.session_state[self.variables_denovo.radio_level_id_submitted_uuid]]
        else:
            set_level_val = self.variables_denovo.default_level

        if st.session_state[self.variables_denovo.radio_evaluation_id_submitted_uuid] in st.session_state.keys():
            set_evaluation_val = st.session_state[
                st.session_state[self.variables_denovo.radio_evaluation_id_submitted_uuid]
            ]
        else:
            set_evaluation_val = self.variables_denovo.default_evaluation

        if self.variables_denovo.all_datapoints_submitted in st.session_state.keys():
            all_datapoints = st.session_state[self.variables_denovo.all_datapoints_submitted]
        else:
            all_datapoints = st.session_state[self.variables_denovo.all_datapoints]

        st.markdown(
        f"""**Benchmarking Inputs:**

            - `input_file_loc`: `{temp_file_path}`
            - `input_format`: `{self.user_input["input_format"]}`
            - `user_input keys`: `{list(self.user_input.keys())}`
            - `all_datapoints`: `{type(all_datapoints)} with {len(all_datapoints)} entries`
            - `level`: `{set_level_val}`
            - `evaluation_type`: `{set_evaluation_val}`
            """
        )

        return self.ionmodule.benchmarking(
            input_file_loc=temp_file_path,
            input_format=self.user_input["input_format"],
            user_input=self.user_input,
            all_datapoints=all_datapoints,
            level=self.level_mapping[set_level_val],
            evaluation_type=self.evaluation_type_mapping[set_evaluation_val],
        )

    def _set_highlight_column_in_submitted_data(self):
        """
        Initialize the highlight column in the data points.
        """
        df = st.session_state[self.variables_denovo.all_datapoints_submitted]
        if (
            self.variables_denovo.highlight_list_submitted not in st.session_state.keys()
            and "Highlight" not in df.columns
        ):
            df.insert(0, "Highlight", [False] * len(df.index))
        elif "Highlight" not in df.columns:
            df.insert(0, "Highlight", st.session_state[self.variables_denovo.highlight_list_submitted])
        elif "Highlight" in df.columns:
            df["Highlight"] = df["Highlight"].astype(bool).fillna(False)
        st.session_state[self.variables_denovo.all_datapoints_submitted] = df

    
    #####################
    ### TAB 3 METHODS ###
    #####################
    def _generate_indepth_plots(
        self, recalculate: bool, public_id: Optional[str], public_hash: Optional[str]
    ) -> go.Figure:
        """
        Generate and return plots based on the current benchmark data in Tab 2.5.

        Parameters
        ----------
        recalculate : bool
            Whether to recalculate the plots.
        public_id : Optional[str], optional
            The dataset to plot, either "Uploaded dataset" or name of public run.
        public_hash : Optional[str], optional
            The hash of the selected public dataset. If None, the uploaded dataset is displayed.

        Returns
        -------
        go.Figure
            The generated plots for the selected dataset.
        """
        raise NotImplementedError()


    def _generate_ptm_plots(self, df, modifications):
        st.markdown('# PTMs')
        st.markdown('### Overview PTM precision')

        fig = PlotDataPoint.plot_ptm_overview(
            self=PlotDataPoint(),
            benchmark_metrics_df=df,
            mod_labels=modifications
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=self.variables_denovo.fig_ptm_overview
        )

        st.markdown('### Precision per modification')
        tabs = st.tabs(modifications)
        tab_dict = {
            mod_label: tab for mod_label, tab in zip(modifications, tabs)
        }

        for mod_label, tab in tab_dict.items():
            with tab:
                st.header(mod_label)
                fig = PlotDataPoint.plot_ptm_specific(
                    self=PlotDataPoint(),
                    benchmark_metrics_df=df,
                    mod_label=mod_label
                )
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=self.variables_denovo.fig_ptm_specific + mod_label
                )


    def _generate_spectrum_feature_plots(self, df, feature_names):
        st.markdown("# Spectrum features")

        exact_mode = st.toggle(
            label='Exact evaluation mode',
            value=False,
            key=self.variables_denovo.evaluation_mode_toggle_tab3_features
        )
        if exact_mode:
            evaluation_type = 'exact'
        else:
            evaluation_type = 'mass'

        tabs = st.tabs(feature_names)
        tab_dict = {
            feature_name: tab for feature_name, tab in zip(feature_names, tabs)
        }

        for feature_name, tab in tab_dict.items():
            with tab:
                st.header(feature_name)
                fig = PlotDataPoint.plot_spectrum_feature(
                    self=PlotDataPoint(),
                    benchmark_metrics_df=df,
                    feature=feature_name,
                    evaluation_type=evaluation_type
                )
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=self.variables_denovo.fig_spectrum_feature + feature_name
                )

    def _generate_species_plot(self, df):
        st.markdown("# Species")

        exact_mode = st.toggle(
            label='Exact evaluation mode',
            value=False,
            key=self.variables_denovo.evaluation_mode_toggle_tab3_species
        )
        if exact_mode:
            evaluation_type = 'exact'
        else:
            evaluation_type = 'mass'

        fig = PlotDataPoint.plot_species_overview(
            self=PlotDataPoint(),
            benchmark_metrics_df=df,
            evaluation_type=evaluation_type
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=self.variables_denovo.fig_species_overview
        )


    #####################
    ### TAB 4 METHODS ###
    #####################
    def _initialize_submitted_radios(self) -> None:
        """
        Initialize the radios for the submitted data.
        """
        if self.variables_denovo.radio_level_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_denovo.radio_level_id_submitted_uuid] = uuid.uuid4()
        if st.session_state[self.variables_denovo.radio_level_id_submitted_uuid] not in st.session_state.keys():
            st.session_state[st.session_state[self.variables_denovo.radio_level_id_submitted_uuid]] = (
                self.variables_denovo.default_level
            )

        if self.variables_denovo.radio_evaluation_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_denovo.radio_evaluation_id_submitted_uuid] = uuid.uuid4()
        if st.session_state[self.variables_denovo.radio_evaluation_id_submitted_uuid] not in st.session_state.keys():
            st.session_state[st.session_state[self.variables_denovo.radio_evaluation_id_submitted_uuid]] = (
                self.variables_denovo.default_evaluation
            )

    def _generate_submitted_radios(self) -> None:
        """
        Create the radios input.
        """
        # TODO: Maybe add a bit of description?
        st.markdown(
            open(
                self.variables_denovo.description_radios_md, "r"
            ).read()
        )

        st.radio(
            "Select at which level precision is calculated",
            options=["Peptide", "Amino Acid"],
            index=0,
            horizontal=True,
            key=st.session_state[self.variables_denovo.radio_level_id_submitted_uuid],
            help="Toggle between different levels of precision calculation"
        )

        st.radio(
            "Select the stringency of evaluation",
            options=["Exact", "Mass-based"],
            index=0,
            horizontal=True,
            key=st.session_state[self.variables_denovo.radio_evaluation_id_submitted_uuid],
            help="Toggle between amino acid identify (Exact) matching and an equal mass-based matching."
        )

    def _generate_submitted_selectbox(self) -> None:
        """
        Create the selectbox for the Streamlit UI.
        """
        if self.variables_denovo.selectbox_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_denovo.selectbox_id_submitted_uuid] = uuid.uuid4()

        try:
            st.selectbox(
                "Select label to plot",
                [
                    "None",
                    "checkpoint",
                    "n_beams",
                    "precursor_mass_tolerance",
                    "decoding_strategy"
                ],
                key=st.session_state[self.variables_denovo.selectbox_id_submitted_uuid],
            )
        except Exception as e:
            st.error(f"Unable to create the selectbox: {e}", icon="🚨")

    def _display_submitted_results(self) -> None:
        """
        Display the results section of the page for submitted data.
        """
        self._initialize_submitted_data_points()

        try:
            fig_metric = PlotDataPoint.plot_metric(
                benchmark_metrics_df=st.session_state[self.variables_denovo.all_datapoints_submitted],
                label=st.session_state[st.session_state[self.variables_denovo.selectbox_id_submitted_uuid]],
            )
            st.plotly_chart(
                fig_metric,
                use_container_width=True,
                key=self.variables_denovo.fig_metric_submitted
            )
        except Exception as e:
            st.error(f"Umable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_denovo.table_id_uuid] = uuid.uuid4()
        st.data_editor(
            st.session_state[self.variables_denovo.all_datapoints_submitted],
            key=st.session_state[self.variables_denovo.table_id_uuid],
            on_change=self._handle_submitted_table_edits,
        )

        st.title("Public submission")
        st.markdown(
            "If you want to make this point — and the associated data — publicly available, please go to “Public Submission"
        )

    def _initialize_submitted_data_points(self) -> None:
        """
        Initialize the all_datapoints variable in the session state.
        """
        if self.variables_denovo.all_datapoints_submitted not in st.session_state.keys():
            st.session_state[self.variables_denovo.all_datapoints_submitted] = None
            st.session_state[self.variables_denovo.all_datapoints_submitted] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_denovo.all_datapoints_submitted]
            )

    def _handle_submitted_table_edits(self) -> None:
        """Callback function for handling edits made to the data table in the UI."""
        edits = st.session_state[st.session_state[self.variables_denovo.table_id_uuid]]["edited_rows"].items()
        for k, v in edits:
            try:
                st.session_state[self.variables_denovo.all_datapoints_submitted][list(v.keys())[0]].iloc[k] = list(
                    v.values()
                )[0]
            except TypeError:
                return
        st.session_state[self.variables_denovo.highlight_list_submitted] = list(
            st.session_state[self.variables_denovo.all_datapoints_submitted]["Highlight"]
        )
        st.session_state[self.variables_denovo.placeholder_table] = st.session_state[
            self.variables_denovo.all_datapoints_submitted
        ]

        if len(st.session_state[self.variables_denovo.all_datapoints]) == 0:
            st.error("No datapoints available for plotting", icon="🚨")

        try:
            fig_metric = PlotDataPoint.plot_metric(
                benchmark_metrics_df=st.session_state[self.variables_denovo.all_datapoints],
                label=st.session_state[st.session_state[self.variables_denovo.selectbox_id_uuid]],
                level=self.level_mapping[
                    st.session_state[st.session_state[self.variables_denovo.radio_level_id_uuid]]
                ],
                evaluation_type=self.evaluation_type_mapping[
                    st.session_state[st.session_state[self.variables_denovo.radio_evaluation_id_uuid]]
                ]
            )
        except Exception as e:
            st.error(f"Unable to plot the datapoints: {e}", icon="🚨")

        st.session_state[self.variables_denovo.fig_metric] = fig_metric

    #####################
    ### TAB 5 METHODS ###
    #####################
    def _generate_submission_ui_elements(self) -> None:
        """
        Create the UI elements necessary for data submission, including metadata uploader and comments section.
        """
        try:
            self._copy_dataframes_for_submission()
            self.submission_ready = True
        except:
            self.submission_ready = False
            st.error(":x: Please provide a result file", icon="🚨")
        self._generate_metadata_uploader()

    def _copy_dataframes_for_submission(self) -> None:
        """
        Create copies of the dataframes before submission.
        """
        if st.session_state[self.variables_denovo.all_datapoints_submitted] is not None:
            st.session_state[self.variables_denovo.all_datapoints_submission] = st.session_state[
                self.variables_denovo.all_datapoints_submitted
            ].copy()
        if st.session_state[self.variables_denovo.input_df] is not None:
            st.session_state[self.variables_denovo.input_df_submission] = st.session_state[
                self.variables_denovo.input_df
            ].copy()
        if st.session_state[self.variables_denovo.result_perf] is not None:
            st.session_state[self.variables_denovo.result_performance_submission] = st.session_state[
                self.variables_denovo.result_perf
            ].copy()

    def _generate_metadata_uploader(self) -> None:
        """
        Create the file uploader for meta data.
        """
        self.user_input[self.variables_denovo.meta_data] = st.file_uploader(
            "Meta data for searches",
            help=self.variables_denovo.texts.Help.meta_data_file,
            accept_multiple_files=True,
        )

    def _load_user_parameters(self) -> Any:
        """
        Read and process the parameter files provided by the user.

        Returns
        -------
        Any
            The parsed parameters.
        """
        params = None

        try:
            params = self.ionmodule.load_params_file(
                self.user_input[self.variables_denovo.meta_data], self.user_input["input_format"]
            )
            st.session_state[self.variables_denovo.params_json_dict] = (
                params.__dict__ if hasattr(params, "__dict__") else params
            )

        except KeyError:
            st.error("Parsing of meta parameters file for this software is not supported yet.", icon="🚨")
        except Exception as e:
            input_f = self.user_input["input_format"]
            st.error(
                f"Unexpected error while parsing file. Make sure you provided a meta parameters file produced by {input_f}: {e}",
                icon="🚨",
            )
        return params

    def _generate_additional_parameters_fields_submission(self) -> None:
        """
        Create the additional parameters section of the form and initializes the parameter fields.
        """
        st.markdown(self.variables_denovo.texts.ShortMessages.initial_parameters)

        # Load JSON config
        with open(self.variables_denovo.additional_params_json) as file:
            config = json.load(file)

        # Check if parsed values exist in session state
        parsed_params = st.session_state.get(self.variables_denovo.params_json_dict, {})

        st_col1, st_col2, st_col3 = st.columns(3)
        input_param_len = int(len(config.items()) / 3)

        for idx, (key, value) in enumerate(config.items()):
            if key.lower() == "software_name":
                editable = False
            else:
                editable = True

            if idx < input_param_len:
                with st_col1:
                    self.user_input[key] = self.generate_input_widget(
                        self.user_input["input_format"], value, key, editable=editable
                    )
            elif idx < input_param_len * 2:
                with st_col2:
                    self.user_input[key] = self.generate_input_widget(
                        self.user_input["input_format"], value, key, editable=editable
                    )
            else:
                with st_col3:
                    self.user_input[key] = self.generate_input_widget(
                        self.user_input["input_format"], value, key, editable=editable
                    )

    def _generate_comments_section(self) -> None:
        """
        Create the text area for submission comments.
        """
        self.user_input["comments_for_submission"] = st.text_area(
            "Comments for submission",
            placeholder=self.variables_denovo.texts.ShortMessages.parameters_additional,
            height=200,
        )
        st.session_state[self.variables_denovo.meta_data_text] = self.user_input["comments_for_submission"]


    def _generate_confirmation_checkbox(self) -> None:
        """
        Create the confirmation checkbox for metadata correctness.
        """
        st.session_state[self.variables_denovo.check_submission] = st.checkbox(
            "I confirm that the metadata is correct",
        )
        self.stop_duplicating = True


    ###############################
    ### GENERAL UTILITY METHODS ###
    ###############################
    def _generate_input_widget(self, input_format: str, content: dict, key: str = "", editable: bool = True) -> Any:
        """
        Generate input fields in the Streamlit UI based on the specified format and content.

        Parameters
        ----------
        input_format : str
            The input format.
        content : dict
            The content of the input fields.
        key : str
            The key of the input fields.
        editable : bool
            Whether the input fields are editable.

        Returns
        -------
        Any
            The input fields.
        """
        field_type = content.get("type")
        if field_type == "text_area":
            return self.generate_text_area_widget(input_format, content, editable=editable)
        elif field_type == "text_input":
            return self._generate_text_input(input_format, content, key, editable=editable)
        elif field_type == "number_input":
            return self._generate_number_input(content, key, editable=editable)
        elif field_type == "selectbox":
            return self._generate_selectbox(input_format, content, key, editable=editable)
        elif field_type == "checkbox":
            return self._generate_checkbox(content=content, key=key, editable=editable)