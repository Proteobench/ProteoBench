import pages.texts.proteobench_builder as pbb
import streamlit as st


class BaseStreamlitUI:
    """
    Streamlit UI for the DDA quantification - precursor ions module.
    """

    def __init__(self, variables, texts, ionmodule, parsesettingsbuilder, uiobjects, page_name):
        """
        Initialize the Streamlit UI for the DDA quantification - precursor ions module.
        """
        self.variables = variables
        self.texts = texts

        self.user_input = dict()

        pbb.proteobench_page_config()

        if self.variables.submit not in st.session_state:
            st.session_state[self.variables.submit] = False
        try:
            token = st.secrets["gh"]["token"]
        except KeyError:
            token = ""
        self.ionmodule = ionmodule(token=token)
        self.parsesettingsbuilder = parsesettingsbuilder(
            module_id=self.ionmodule.module_id, parse_settings_dir=self.variables.parse_settings_dir
        )

        self.uiobjects = uiobjects(self.variables, self.ionmodule, self.parsesettingsbuilder, page_name=page_name)

    def main_page(self) -> None:
        """
        Set up the main page layout for the Streamlit application.
        """
        # Create tabs
        (
            tab_results_all,
            tab_submission_details,
            tab_indepth_plots,
            tab_multqc_plot,
            tab_results_new,
            tab_public_submission,
        ) = st.tabs(
            [
                "Public Benchmark Runs",
                "Submit New Data",
                "Results In-Depth",
                "pMultiQC Plot",
                "Results New Data",
                "Public Submission",
            ]
        )

        with tab_results_all:
            st.title(self.variables.title)
            st.link_button(
                "Go to module documentation",
                url=self.variables.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            if self.variables.alpha_warning:
                st.warning(
                    "This module is in ALPHA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.uiobjects.display_all_data_results_main()

        # Tab 2: Submission Details
        with tab_submission_details:
            st.title(self.variables.title)

            st.link_button(
                "Go to module documentation",
                url=self.variables.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            if self.variables.alpha_warning:
                st.warning(
                    "This module is in ALPHA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.uiobjects.display_submission_form()

        # Tab 3: in-depth plots current data
        with tab_indepth_plots:
            st.title(self.variables.title)

            st.link_button(
                "Go to module documentation",
                url=self.variables.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            if self.variables.alpha_warning:
                st.warning(
                    "This module is in ALPHA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.uiobjects.display_indepth_plots()

        # Tab 3_1: pMultiQC plot based on intermediate data

        with tab_multqc_plot:
            st.title("pMultiQC Report for selected dataset.")
            # self.uiobjects.display_multqc_plot()

            self.uiobjects.display_pmultiqc_report()

        # Tab 4: Results (New Submissions)
        with tab_results_new:
            st.title(self.variables.title)
            st.link_button(
                "Go to module documentation",
                url=self.variables.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            if self.variables.alpha_warning:
                st.warning(
                    "This module is in ALPHA phase. The figure presented below and the metrics calculation may change in the near future."
                )

            self.uiobjects.display_all_data_results_submitted()

        # Tab 5: Public Submission
        with tab_public_submission:
            st.title(self.variables.title)
            st.link_button(
                "Go to module documentation",
                url=self.variables.doc_url,
                type="secondary",
                help="link to the module documentation",
            )
            if self.variables.beta_warning:
                st.warning(
                    "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            if self.variables.alpha_warning:
                st.warning(
                    "This module is in ALPHA phase. The figure presented below and the metrics calculation may change in the near future."
                )
            self.uiobjects.display_public_submission_ui()
