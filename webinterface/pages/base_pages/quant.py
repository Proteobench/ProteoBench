"""Streamlit-based web interface for ProteoBench."""

import copy
import logging
import tempfile
import uuid
from typing import Any, Dict

import pages.texts.proteobench_builder as pbb
import streamlit as st
from pages.pages_variables.Quant.lfq_DDA_ion_QExactive_variables import (
    VariablesDDAQuant,
)

from proteobench.io.params import ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import (
    DDAQuantIonModuleQExactive as IonModule,
)

from . import (
    tab1_results,
    tab2_form_upload_data,
    tab3_indepth_plots,
    tab4_display_results_submitted,
    tab5_public_submission,
)
from .inputs import generate_input_widget

logger: logging.Logger = logging.getLogger(__name__)


class QuantUIObjects:
    """Main class for the Streamlit interface of ProteoBench quantification.
    This class handles the creation of the Streamlit UI elements, including the main page layout,
    input forms, results display, and data submission elements.

    Parameters
    ----------
    variables_quant : VariablesDDAQuant
        The variables for the quantification module.
    ionmodule : IonModule
        The quantification module.
    parsesettingsbuilder : ParseSettingsBuilder
        The parse settings builder.
    """

    def __init__(
        self,
        variables_quant: VariablesDDAQuant,
        ionmodule: IonModule,
        parsesettingsbuilder: ParseSettingsBuilder,
        page_name: str = "/",
    ) -> None:
        """
        Initialize the Streamlit UI objects for the quantification modules.

        Parameters
        ----------
        variables_quant : VariablesDDAQuant
            The variables for the quantification module.
        ionmodule : IonModule
            The quantification module.
        parsesettingsbuilder : ParseSettingsBuilder
            The parse settings builder.
        """
        self.variables_quant: VariablesDDAQuant = variables_quant
        self.ionmodule: IonModule = ionmodule
        self.parsesettingsbuilder: ParseSettingsBuilder = parsesettingsbuilder
        self.user_input: Dict[str, Any] = {}
        self.page_name = page_name
        self.user_input: Dict[str, Any] = {}
        self.submission_ready = False
        self.params_file_dict_copy: Dict[str, Any] = {}

        # Create page config and sidebar
        pbb.proteobench_page_config()

        st.markdown(
            """
            <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        pbb.proteobench_sidebar(current_page=self.page_name)

        self.first_point_plotted = False
        st.session_state[self.variables_quant.submit] = False
        self.stop_duplicating = False

        if self.variables_quant.params_file_dict not in st.session_state.keys():
            st.session_state[self.variables_quant.params_file_dict] = {}
        if self.variables_quant.slider_id_submitted_uuid not in st.session_state.keys():
            st.session_state[self.variables_quant.slider_id_submitted_uuid] = str()

    def display_submission_form(self) -> None:
        """Create the main submission form for the Streamlit UI in Tab 2."""
        with st.form(key="main_form"):
            tab2_form_upload_data.generate_input_fields(
                variables_quant=self.variables_quant,
                parsesettingsbuilder=self.parsesettingsbuilder,
                user_input=self.user_input,
            )
            # TODO: Investigate the necessity of generating additional parameters fields in the first tab.
            tab2_form_upload_data.generate_additional_parameters_fields(
                variables_quant=self.variables_quant,
                user_input=self.user_input,
            )
            text = self.variables_quant.texts.ShortMessages.run_instructions
            st.markdown(text)
            submit_button = st.form_submit_button(
                "Parse and bench",
                help=self.variables_quant.texts.Help.parse_button,
            )

        if submit_button:
            self.process_submission_form()

    def process_submission_form(self) -> None:
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
        self.execute_proteobench()
        self.first_point_plotted = True

        # Inform the user with a link to the next tab
        st.info(
            "Form submitted successfully! Please navigate to the 'Results In-Depth' "
            "or 'Results New Data' tab for the next step."
        )

    def initialize_main_data_points(self) -> None:
        """
        Initialize the all_datapoints variable in the session state.
        """
        if self.variables_quant.all_datapoints not in st.session_state.keys():
            st.session_state[self.variables_quant.all_datapoints] = None
            st.session_state[self.variables_quant.all_datapoints] = self.ionmodule.obtain_all_data_points(
                all_datapoints=st.session_state[self.variables_quant.all_datapoints]
            )

    def set_highlight_column_in_submitted_data(self) -> None:
        """
        Initialize the highlight column in the data points.
        """
        df = st.session_state[self.variables_quant.all_datapoints_submitted]
        if (
            self.variables_quant.highlight_list_submitted not in st.session_state.keys()
            and "Highlight" not in df.columns
        ):
            df.insert(0, "Highlight", [False] * len(df.index))
        elif "Highlight" not in df.columns:
            df.insert(0, "Highlight", st.session_state[self.variables_quant.highlight_list_submitted])
        elif "Highlight" in df.columns:
            # Not sure how 'Highlight' column became object dtype
            df["Highlight"] = df["Highlight"].astype(bool).fillna(False)
        # only needed for last elif, but to be sure apply always:
        st.session_state[self.variables_quant.all_datapoints_submitted] = df

    def display_indepth_plots(self) -> None:
        """
        Display the dataset selection dropdown and plot the selected dataset (Tab 3).
        """
        # the key is a string and links to a pandas.DataFrame
        key_in_state = self.variables_quant.all_datapoints_submitted
        if key_in_state not in st.session_state.keys():
            st.error("No data available for plotting.", icon="🚨")
            return
        df = st.session_state[key_in_state]
        if df.empty:
            st.error("No data available for plotting.", icon="🚨")
            return
        downloads_df = df[["id", "intermediate_hash"]]
        downloads_df.set_index("intermediate_hash", drop=False, inplace=True)

        key_in_state = self.variables_quant.placeholder_dataset_selection_container
        if key_in_state not in st.session_state.keys():
            st.session_state[key_in_state] = st.empty()
            key_in_state = self.variables_quant.dataset_selector_id_uuid
            st.session_state[key_in_state] = uuid.uuid4()

        st.subheader("Select dataset to plot")

        dataset_options = [("Uploaded dataset", None)] + list(
            zip(downloads_df["id"], downloads_df["intermediate_hash"])
        )

        dataset_selection = st.selectbox(
            "Select dataset",
            dataset_options,
            index=0,
            key=st.session_state[self.variables_quant.dataset_selector_id_uuid],
            format_func=lambda x: x[0],
        )

        public_id, selected_hash = dataset_selection
        tab3_indepth_plots.generate_indepth_plots(
            variables_quant=self.variables_quant,
            parsesettingsbuilder=self.parsesettingsbuilder,
            user_input=self.user_input,
            recalculate=True,
            public_id=public_id,
            public_hash=selected_hash,
        )

    def execute_proteobench(self) -> None:
        """
        Execute the ProteoBench benchmarking process.
        """
        if self.variables_quant.all_datapoints_submitted not in st.session_state:
            self.initialize_main_data_points()

        result_performance, all_datapoints, input_df = self.run_benchmarking_process()
        st.session_state[self.variables_quant.all_datapoints_submitted] = all_datapoints

        self.set_highlight_column_in_submitted_data()

        st.session_state[self.variables_quant.result_perf] = result_performance

        st.session_state[self.variables_quant.input_df] = input_df

    def run_benchmarking_process(self):
        """
        Execute the benchmarking process and returns the results.

        Returns
        -------
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
            The benchmarking results, all data points, and the input data frame.
        """
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(self.user_input["input_csv"].getbuffer())

        # reload buffer: https://stackoverflow.com/a/64478151/9684872
        self.user_input["input_csv"].seek(0)
        if st.session_state[self.variables_quant.slider_id_submitted_uuid] in st.session_state.keys():
            set_slider_val = st.session_state[st.session_state[self.variables_quant.slider_id_submitted_uuid]]
        else:
            set_slider_val = self.variables_quant.default_val_slider

        if self.variables_quant.all_datapoints_submitted in st.session_state.keys():
            all_datapoints = st.session_state[self.variables_quant.all_datapoints_submitted]
        else:
            all_datapoints = st.session_state[self.variables_quant.all_datapoints]

        return self.ionmodule.benchmarking(
            self.user_input["input_csv"],
            self.user_input["input_format"],
            self.user_input,
            all_datapoints,
            default_cutoff_min_prec=set_slider_val,
        )

    def display_public_submission_ui(self) -> None:
        """
        Display the public submission section of the page in Tab 5.
        """
        # Initialize Unchecked submission box variable
        if self.variables_quant.check_submission not in st.session_state:
            st.session_state[self.variables_quant.check_submission] = False
        if self.variables_quant.first_new_plot:
            self.submission_ready = tab5_public_submission.generate_submission_ui_elements(
                variables_quant=self.variables_quant,
                user_input=self.user_input,
            )

        if self.user_input[self.variables_quant.meta_data]:
            params = tab5_public_submission.load_user_parameters(
                variables_quant=self.variables_quant,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
            )
            st.session_state[self.variables_quant.params_file_dict] = params.__dict__
            self.params_file_dict_copy = copy.deepcopy(params.__dict__)
            print(self.params_file_dict_copy)
            tab5_public_submission.generate_additional_parameters_fields_submission(
                variables_quant=self.variables_quant,
                user_input=self.user_input,
            )
            tab5_public_submission.generate_comments_section(
                variables_quant=self.variables_quant,
                user_input=self.user_input,
            )
            # ? stop_duplicating is not used?
            self.stop_duplicating = tab5_public_submission.generate_confirmation_checkbox(
                check_submission=self.variables_quant.check_submission
            )
        else:
            params = None

        pr_url = None
        if st.session_state[self.variables_quant.check_submission] and params is not None:
            get_form_values = tab5_public_submission.get_form_values(
                variables_quant=self.variables_quant,
            )
            params = ProteoBenchParameters(**get_form_values)
            pr_url = tab5_public_submission.submit_to_repository(
                variables_quant=self.variables_quant,
                ionmodule=self.ionmodule,
                user_input=self.user_input,
                params_from_file=self.params_file_dict_copy,
                params=params,
            )
        if not self.submission_ready:
            return
        if (
            st.session_state[self.variables_quant.check_submission]
            and params is not None
            and self.variables_quant.submit in st.session_state
            and pr_url is not None
        ):
            tab5_public_submission.show_submission_success_message(
                variables_quant=self.variables_quant,
                pr_url=pr_url,
            )

    @st.fragment
    def display_all_data_results_main(self) -> None:
        """Display the results for all data in Tab 1."""
        st.title("Results (All Data)")
        tab1_results.initialize_main_slider(
            slider_id_uuid=self.variables_quant.slider_id_uuid,
            default_val_slider=self.variables_quant.default_val_slider,
        )
        tab1_results.generate_main_slider(
            slider_id_uuid=self.variables_quant.slider_id_uuid,
            description_slider_md=self.variables_quant.description_slider_md,
            default_val_slider=self.variables_quant.default_val_slider,
        )
        tab1_results.generate_main_selectbox(selectbox_id_uuid=self.variables_quant.selectbox_id_uuid)
        tab1_results.display_existing_results(variables_quant=self.variables_quant, ionmodule=self.ionmodule)

    def display_all_data_results_submitted(self) -> None:
        """Display the results for all data in Tab 4."""
        st.title("Results (All Data)")
        tab4_display_results_submitted.initialize_submitted_slider(
            self.variables_quant.slider_id_submitted_uuid,
            self.variables_quant.default_val_slider,
        )
        tab4_display_results_submitted.generate_submitted_slider(self.variables_quant)
        tab4_display_results_submitted.generate_submitted_selectbox(self.variables_quant)
        tab4_display_results_submitted.display_submitted_results(
            variables_quant=self.variables_quant,
            ionmodule=self.ionmodule,
        )
