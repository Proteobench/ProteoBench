"""Streamlit-based web interface for ProteoBench."""

import json
import logging
import uuid
from datetime import datetime
from pprint import pformat

import streamlit as st
import streamlit_utils
from pages.pages_variables.dda_quant_variables import VariablesDDAQuant
from streamlit_extras.let_it_rain import rain

from proteobench.io.parsing.parse_settings_ion import (
    LOCAL_DEVELOPMENT,
    ParseSettingsBuilder,
)
from proteobench.modules.dda_quant_ion.module import IonModule
from proteobench.utils.plotting.plot import PlotDataPoint
from proteobench.utils.quant_datapoint import (
    filter_df_numquant_median_abs_epsilon,
    filter_df_numquant_nr_prec,
)

logger = logging.getLogger(__name__)

if "submission_ready" not in st.session_state:
    st.session_state["submission_ready"] = False


class StreamlitUI:
    """Proteobench Streamlit UI."""

    def __init__(self):
        """Proteobench Streamlit UI."""
        self.variables_dda_quant = VariablesDDAQuant()
        self.texts = WebpageTexts
        self.user_input = dict()

        st.set_page_config(
            page_title="Proteobench web server",
            page_icon=":rocket:",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        if self.variables_dda_quant.submit not in st.session_state:
            st.session_state[self.variables_dda_quant.submit] = False
        self._main_page()
        self._sidebar()

    def generate_input_field(self, input_format: str, content: dict):
        if content["type"] == "text_area":
            if "placeholder" in content:
                return st.text_area(content["label"], placeholder=content["placeholder"], height=content["height"])
            elif "value" in content:
                return st.text_area(content["label"], content["value"][input_format], height=content["height"])
        if content["type"] == "text_input":
            if "placeholder" in content:
                return st.text_input(content["label"], placeholder=content["placeholder"])
            elif "value" in content:
                return st.text_input(content["label"], content["value"][input_format])
        if content["type"] == "number_input":
            return st.number_input(
                content["label"],
                value=None,
                format=content["format"],
                min_value=content["min_value"],
                max_value=content["max_value"],
            )
        if content["type"] == "selectbox":
            return st.selectbox(
                content["label"],
                content["options"],
                content["options"].index(content["value"][input_format]),
            )
        if content["type"] == "checkbox":
            return st.checkbox(content["label"], content["value"][input_format])

    def _main_page(self):
        """Format main page."""
        st.title("DDA quantification - precursor ions")
        st.warning(
            "This module is in BETA phase. The figure presented below and the metrics calculation may change in the near future."
        )
        st.header("Description of the module")
        st.markdown(open("pages/markdown_files/DDA_Quant_ion/introduction.md", "r").read())
        st.header("Downloading associated files")
        st.markdown(open("pages/markdown_files/DDA_Quant_ion/file_description.md", "r").read(), unsafe_allow_html=True)

        st.header("Input and configuration")

        st.markdown(
            """
            Scroll down if you want to see the public benchmark runs publicly available
            today.
            """
        )

        with st.form(key="main_form"):
            st.subheader("Input files")
            st.markdown(open("pages/markdown_files/DDA_Quant_ion/input_file_description.md", "r").read())
            self.user_input["input_format"] = st.selectbox(
                "Software tool", ParseSettingsBuilder().INPUT_FORMATS, help=self.texts.Help.input_format
            )

            self.user_input["input_csv"] = st.file_uploader(
                "Software tool result file", help=self.texts.Help.input_file
            )

            st.markdown(
                """
                Additionally, you can fill out some information on the paramters that were 
                used for this benchmark run bellow. These will be printed when hovering on your point.
                """
            )
            with st.expander("Additional parameters"):
                with open("../webinterface/configuration/dda_quant.json") as file:
                    config = json.load(file)

                for key, value in config.items():
                    self.user_input[key] = self.generate_input_field(self.user_input["input_format"], value)

            st.markdown(
                """
                    Now, press `Parse and Bench` to calculate the metrics from your input. 
                    """
            )

            submit_button = st.form_submit_button("Parse and bench", help=self.texts.Help.parse_button)

        if submit_button:
            if self.user_input["input_csv"]:
                if self.variables_dda_quant.meta_file_uploader_uuid in st.session_state.keys():
                    del st.session_state[self.variables_dda_quant.meta_file_uploader_uuid]
                if self.variables_dda_quant.comments_submission_uuid in st.session_state.keys():
                    del st.session_state[self.variables_dda_quant.comments_submission_uuid]
                if self.variables_dda_quant.check_submission_uuid in st.session_state.keys():
                    del st.session_state[self.variables_dda_quant.check_submission_uuid]
                if self.variables_dda_quant.button_submission_uuid in st.session_state.keys():
                    del st.session_state[self.variables_dda_quant.button_submission_uuid]

                self._run_proteobench()
            else:
                st.error(":x: Please provide a result file")

        if self.variables_dda_quant.fig_logfc in st.session_state:
            self._populate_results()

        if "slider_id" in st.session_state.keys():
            default_val_slider = st.session_state[st.session_state["slider_id"]]
        else:
            default_val_slider = self.variables_dda_quant.default_val_slider

        if (
            self.variables_dda_quant.all_datapoints not in st.session_state
            or self.variables_dda_quant.first_new_plot == True
        ):
            st.session_state[self.variables_dda_quant.all_datapoints] = None
            all_datapoints = st.session_state[self.variables_dda_quant.all_datapoints]
            all_datapoints = IonModule().obtain_all_data_point(all_datapoints)

            all_datapoints["median_abs_epsilon"] = all_datapoints["results"].apply(
                filter_df_numquant_median_abs_epsilon, min_quant=default_val_slider
            )
            all_datapoints["nr_prec"] = all_datapoints["results"].apply(
                filter_df_numquant_nr_prec, min_quant=default_val_slider
            )

            if (
                self.variables_dda_quant.highlight_list not in st.session_state.keys()
                and "Highlight" not in all_datapoints.columns
            ):
                all_datapoints.insert(0, "Highlight", [False] * len(all_datapoints.index))
            elif "Highlight" not in all_datapoints.columns:
                all_datapoints.insert(0, "Highlight", st.session_state[self.variables_dda_quant.highlight_list])

            st.markdown(
                """
                    Choose with the slider below the minimum number of quantification value 
                    per raw file.  
                    Example: when 3 is selected, only the precursor ions quantified in 
                    3 or more raw files will be considered for the plot. 
                        """
            )

            st.session_state[self.variables_dda_quant.placeholder_slider] = st.empty()
            st.session_state[self.variables_dda_quant.placeholder_fig_compare] = st.empty()
            st.session_state[self.variables_dda_quant.placeholder_table] = st.empty()

            st.session_state["slider_id"] = uuid.uuid4()
            st.session_state["table_id"] = uuid.uuid4()

            st.session_state[self.variables_dda_quant.placeholder_slider].select_slider(
                label="Minimal ion quantifications (# samples)",
                options=[1, 2, 3, 4, 5, 6],
                value=default_val_slider,
                on_change=self.slider_callback,
                key=st.session_state["slider_id"],
            )

            fig_metric = PlotDataPoint.plot_metric(all_datapoints)

            st.session_state[self.variables_dda_quant.all_datapoints] = all_datapoints
            st.session_state[self.variables_dda_quant.fig_metric] = fig_metric

            st.session_state[self.variables_dda_quant.placeholder_fig_compare].plotly_chart(
                st.session_state[self.variables_dda_quant.fig_metric], use_container_width=True
            )

            st.session_state[self.variables_dda_quant.placeholder_table].data_editor(
                st.session_state[self.variables_dda_quant.all_datapoints],
                key=st.session_state["table_id"],
                on_change=self.table_callback,
            )

    def _populate_results(self):
        self.generate_results("", None, None, False, None)

    def _sidebar(self):
        """Format sidebar."""
        st.sidebar.image("logos/logo_funding/main_logos_sidebar.png", width=300)

    def _run_proteobench(self):
        # Run Proteobench
        st.header("Running Proteobench")
        status_placeholder = st.empty()
        status_placeholder.info(":hourglass_flowing_sand: Running Proteobench...")

        if self.variables_dda_quant.all_datapoints not in st.session_state:
            st.session_state[self.variables_dda_quant.all_datapoints] = None

        try:
            if "slider_id" in st.session_state.keys():
                default_val_slider = st.session_state[st.session_state["slider_id"]]
            else:
                default_val_slider = self.variables_dda_quant.default_val_slider

            result_performance, all_datapoints, input_df = IonModule().benchmarking(
                self.user_input["input_csv"],
                self.user_input["input_format"],
                self.user_input,
                st.session_state[self.variables_dda_quant.all_datapoints],
                default_cutoff_min_prec=default_val_slider,
            )

            st.session_state[self.variables_dda_quant.all_datapoints] = all_datapoints

            if "Highlight" not in st.session_state[self.variables_dda_quant.all_datapoints].columns:
                st.session_state[self.variables_dda_quant.all_datapoints].insert(
                    0, "Highlight", [False] * len(st.session_state[self.variables_dda_quant.all_datapoints].index)
                )
            else:
                st.session_state[self.variables_dda_quant.all_datapoints]["Highlight"] = [False] * len(
                    st.session_state[self.variables_dda_quant.all_datapoints].index
                )

        except Exception as e:
            status_placeholder.error(":x: Proteobench ran into a problem")
            st.exception(e)
        else:
            self.generate_results(status_placeholder, result_performance, all_datapoints, True, input_df)

    def table_callback(self):
        min_quant = st.session_state[st.session_state["slider_id"]]
        edits = st.session_state[st.session_state["table_id"]]["edited_rows"].items()
        for k, v in edits:
            try:
                st.session_state[self.variables_dda_quant.all_datapoints][list(v.keys())[0]].iloc[k] = list(v.values())[
                    0
                ]
            except TypeError:
                return
        st.session_state[self.variables_dda_quant.highlight_list] = list(
            st.session_state[self.variables_dda_quant.all_datapoints]["Highlight"]
        )
        st.session_state[self.variables_dda_quant.placeholder_table] = st.session_state[
            self.variables_dda_quant.all_datapoints
        ]

        fig_metric = PlotDataPoint.plot_metric(st.session_state[self.variables_dda_quant.all_datapoints])

        st.session_state[self.variables_dda_quant.fig_metric] = fig_metric

        if self.variables_dda_quant.result_perf in st.session_state.keys():
            self.plots_for_current_data(st.session_state[self.variables_dda_quant.result_perf], True, False, min_quant)

    def slider_callback(self):
        min_quant = st.session_state[st.session_state["slider_id"]]
        st.session_state[self.variables_dda_quant.all_datapoints]["median_abs_epsilon"] = [
            filter_df_numquant_median_abs_epsilon(v, min_quant=min_quant)
            for v in st.session_state[self.variables_dda_quant.all_datapoints]["results"]
        ]
        st.session_state[self.variables_dda_quant.all_datapoints]["nr_prec"] = [
            filter_df_numquant_nr_prec(v, min_quant=min_quant)
            for v in st.session_state[self.variables_dda_quant.all_datapoints]["results"]
        ]

        fig_metric = PlotDataPoint.plot_metric(st.session_state[self.variables_dda_quant.all_datapoints])

        st.session_state[self.variables_dda_quant.fig_metric] = fig_metric

        if self.variables_dda_quant.result_perf in st.session_state.keys():
            self.plots_for_current_data(st.session_state[self.variables_dda_quant.result_perf], True, False, min_quant)

    def generate_results(
        self,
        status_placeholder,
        result_performance,
        all_datapoints,
        recalculate,
        input_df,
    ):
        self.variables_dda_quant.first_new_plot
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if recalculate:
            status_placeholder.success(":heavy_check_mark: Finished!")

            # Show head of result DataFrame
        if self.variables_dda_quant.first_new_plot:
            st.header("Results")
            st.subheader("Sample of the processed file")
            st.markdown(
                """
                Here are the data from your benchmark run. The table contains the 
                precursor ion MS signal calculated from your input data. You can download 
                this table from `Download calculated ratios` below.
                """
            )
        if not recalculate:
            result_performance = st.session_state[self.variables_dda_quant.result_perf]
            all_datapoints = st.session_state[self.variables_dda_quant.all_datapoints]
            input_df = st.session_state[self.variables_dda_quant.input_df]
        if self.variables_dda_quant.first_new_plot:
            st.session_state[self.variables_dda_quant.df_head] = st.dataframe(result_performance.head(100))
        else:
            st.session_state[self.variables_dda_quant.df_head] = result_performance.head(100)

        if self.variables_dda_quant.first_new_plot:
            st.markdown(st.markdown(open("pages/markdown_files/DDA_Quant_ion/result_description.md", "r").read()))

        if "slider_id" in st.session_state.keys():
            default_val_slider = st.session_state[st.session_state["slider_id"]]
        else:
            default_val_slider = self.variables_dda_quant.default_val_slider

        fig_logfc = self.plots_for_current_data(
            result_performance, recalculate, self.variables_dda_quant.first_new_plot, slider_value=default_val_slider
        )

        if self.variables_dda_quant.first_new_plot:
            st.subheader("Mean error between conditions")
            st.markdown(
                """
                New figure including your benchmark run. The point corresponding to 
                your data will appear bigger than the public data sets already available 
                in ProteoBench.
                """
            )

        if recalculate:
            all_datapoints["weighted_sum"] = [
                filter_df_numquant_median_abs_epsilon(v, min_quant=default_val_slider)
                for v in all_datapoints["results"]
            ]
            all_datapoints["nr_prec"] = [
                filter_df_numquant_nr_prec(v, min_quant=default_val_slider) for v in all_datapoints["results"]
            ]

            fig_metric = PlotDataPoint.plot_metric(all_datapoints)
            st.session_state[self.variables_dda_quant.all_datapoints] = all_datapoints
            st.session_state[self.variables_dda_quant.fig_metric] = fig_metric
        else:
            fig_metric = st.session_state[self.variables_dda_quant.fig_metric]

        if self.variables_dda_quant.first_new_plot:
            st.markdown(
                """
                    Choose with the slider below the minimum number of quantification value 
                    per raw file.  
                    Example: when 3 is selected, only the precursor ions quantified in 
                    3 or more raw files will be considered for the plot. 
                        """
            )
            st.session_state["slider_id"] = uuid.uuid4()
            f = st.select_slider(
                label="Minimal ion quantifications (# samples)",
                options=[1, 2, 3, 4, 5, 6],
                value=default_val_slider,
                on_change=self.slider_callback,
                key=st.session_state["slider_id"],
            )

            placeholder_fig_compare = st.empty()
            placeholder_fig_compare.plotly_chart(
                st.session_state[self.variables_dda_quant.fig_metric], use_container_width=True
            )
            st.session_state[self.variables_dda_quant.placeholder_fig_compare] = placeholder_fig_compare

            st.session_state["table_id"] = uuid.uuid4()

            st.data_editor(
                st.session_state[self.variables_dda_quant.all_datapoints],
                key=st.session_state["table_id"],
                on_change=self.table_callback,
            )
        else:
            fig_metric = st.session_state[self.variables_dda_quant.fig_metric]
            st.session_state[self.variables_dda_quant.fig_metric].data[0].x = fig_metric.data[0].x
            st.session_state[self.variables_dda_quant.fig_metric].data[0].y = fig_metric.data[0].y

            st.session_state[self.variables_dda_quant.placeholder_fig_compare].plotly_chart(
                st.session_state[self.variables_dda_quant.fig_metric], use_container_width=True
            )

        sample_name = "%s-%s-%s-%s" % (
            self.user_input["input_format"],
            self.user_input["software_version"],
            self.user_input["enable_match_between_runs"],
            time_stamp,
        )

        # Download link
        if self.variables_dda_quant.first_new_plot:
            st.subheader("Download calculated ratios")
            random_uuid = uuid.uuid4()
            st.download_button(
                label="Download",
                data=streamlit_utils.save_dataframe(result_performance),
                file_name=f"{sample_name}.csv",
                mime="text/csv",
                key=f"{random_uuid}",
            )

            st.subheader("Add results to online repository")
            st.markdown(open("pages/markdown_files/DDA_Quant_ion/submit_description.md", "r").read())
        st.session_state[self.variables_dda_quant.fig_logfc] = fig_logfc
        st.session_state[self.variables_dda_quant.fig_metric] = fig_metric
        st.session_state[self.variables_dda_quant.result_perf] = result_performance
        st.session_state[self.variables_dda_quant.all_datapoints] = all_datapoints
        st.session_state[self.variables_dda_quant.input_df] = input_df

        # Create unique element IDs
        if self.variables_dda_quant.meta_file_uploader_uuid in st.session_state.keys():
            meta_file_uploader_uuid = st.session_state[self.variables_dda_quant.meta_file_uploader_uuid]
        else:
            meta_file_uploader_uuid = uuid.uuid4()
            st.session_state[self.variables_dda_quant.meta_file_uploader_uuid] = meta_file_uploader_uuid
        if self.variables_dda_quant.comments_submission_uuid in st.session_state.keys():
            comments_submission_uuid = st.session_state[self.variables_dda_quant.comments_submission_uuid]
        else:
            comments_submission_uuid = uuid.uuid4()
            st.session_state[self.variables_dda_quant.comments_submission_uuid] = comments_submission_uuid
        if self.variables_dda_quant.check_submission_uuid in st.session_state.keys():
            check_submission_uuid = st.session_state[self.variables_dda_quant.check_submission_uuid]
        else:
            check_submission_uuid = uuid.uuid4()
            st.session_state[self.variables_dda_quant.check_submission_uuid] = check_submission_uuid

        if self.variables_dda_quant.first_new_plot:
            self.user_input[self.variables_dda_quant.meta_data] = st.file_uploader(
                "Meta data for searches",
                help=self.texts.Help.meta_data_file,
                key=meta_file_uploader_uuid,
                accept_multiple_files=True,
            )

            self.user_input["comments_for_submission"] = st.text_area(
                "Comments for submission",
                placeholder="Anything else you want to let us know? Please specifically add changes in your search parameters here, that are not obvious from the parameter file.",
                height=200,
                key=comments_submission_uuid,
            )

            st.session_state[self.variables_dda_quant.meta_data_TEXT] = self.user_input["comments_for_submission"]

            st.session_state[self.variables_dda_quant.check_submission] = st.checkbox(
                "I confirm that the metadata is correct",
                key=check_submission_uuid,
            )

        # TODO: do we need a better handling of this?
        params = None
        if self.user_input[self.variables_dda_quant.meta_data]:
            try:
                print(self.user_input["input_format"])
                params = IonModule().load_params_file(
                    self.user_input[self.variables_dda_quant.meta_data], self.user_input["input_format"]
                )
                st.text(f"Parsed and selected parameters:\n{pformat(params.__dict__)}")
            except KeyError as e:
                st.error("Parsing of meta parameters file for this software is not supported yet.")
            except Exception as err:
                input_f = self.user_input["input_format"]
                st.error(
                    f"Unexpected error while parsing file. Make sure you provided a meta parameters file produced by {input_f}."
                )

        if st.session_state[self.variables_dda_quant.check_submission] and params != None:
            st.session_state["submission_ready"] = True

            if self.variables_dda_quant.button_submission_uuid in st.session_state.keys():
                button_submission_uuid = st.session_state[self.variables_dda_quant.button_submission_uuid]
            else:
                button_submission_uuid = uuid.uuid4()
                st.session_state[self.variables_dda_quant.button_submission_uuid] = button_submission_uuid
            submit_pr = st.button("I really want to upload it", key=button_submission_uuid)

            if submit_pr:
                st.session_state[self.variables_dda_quant.submit] = True
                user_comments = self.user_input["comments_for_submission"]
                if not LOCAL_DEVELOPMENT:
                    submit_df = st.session_state[self.variables_dda_quant.all_datapoints]
                    if "Highlight" in submit_df.columns:
                        # TODO it seems that pandas trips over this sometime, even though it is present...
                        try:
                            submit_df.drop("Highlight", inplace=True, axis=1)
                        except:
                            pass

                    pr_url = IonModule().clone_pr(
                        submit_df,
                        params,
                        st.secrets["gh"]["token"],
                        username="Proteobot",
                        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
                        branch_name="new_branch",
                        submission_comments=user_comments,
                    )
                else:
                    # TODO, what is this?
                    DDA_QUANT_RESULTS_PATH = IonModule().write_json_local_development(
                        st.session_state[self.variables_dda_quant.all_datapoints], params
                    )

                if not pr_url:
                    del st.session_state[self.variables_dda_quant.submit]
                else:
                    id = str(all_datapoints[all_datapoints["old_new"] == "new"].iloc[-1, :]["intermediate_hash"])

                    if "storage" in st.secrets.keys():
                        IonModule().write_intermediate_raw(
                            st.secrets["storage"]["dir"],
                            id,
                            input_df,
                            result_performance,
                            self.user_input[self.variables_dda_quant.meta_data],
                        )
        if self.variables_dda_quant.submit in st.session_state:
            if st.session_state[self.variables_dda_quant.submit]:
                # status_placeholder.success(":heavy_check_mark: Successfully uploaded data!")
                st.subheader("SUCCESS")
                st.markdown(
                    """
                    **It will take a few working days for your point to be added to the plot**
                    """
                )
                try:
                    st.write(f"Follow your submission approval here: [{pr_url}]({pr_url})")
                except UnboundLocalError:
                    # Happens when pr_url is not defined, e.g., local dev
                    pass

                st.session_state[self.variables_dda_quant.submit] = False
                rain(emoji="🎈", font_size=54, falling_speed=5, animation_length=1)
        self.variables_dda_quant.first_new_plot = False

    def plots_for_current_data(self, result_performance, recalculate, first_new_plot, slider_value):
        # filter result_performance dataframe on nr_observed column
        result_performance = result_performance[result_performance["nr_observed"] >= slider_value]

        if recalculate:
            parse_settings = ParseSettingsBuilder().build_parser(self.user_input["input_format"])

            fig_logfc = PlotDataPoint.plot_fold_change_histogram(
                result_performance, parse_settings.species_expected_ratio()
            )
            fig_CV = PlotDataPoint.plot_CV_violinplot(result_performance)
            st.session_state[self.variables_dda_quant.fig_cv] = fig_CV
            st.session_state[self.variables_dda_quant.fig_logfc] = fig_logfc
        else:
            fig_logfc = st.session_state[self.variables_dda_quant.fig_logfc]
            fig_CV = st.session_state[self.variables_dda_quant.fig_cv]

        if first_new_plot:
            # Use st.beta_columns to arrange the figures side by side
            col1, col2 = st.columns(2)
            col1.subheader("Log2 Fold Change distributions by species.")
            col1.markdown(
                """
                    Left Panel : log2 fold changes calculated from your data
                """
            )
            col1.plotly_chart(fig_logfc, use_container_width=True)

            col2.subheader("Coefficient of variation distribution in Group A and B.")
            col2.markdown(
                """
                    Right Panel Panel : CV calculated from your data
                """
            )
            col2.plotly_chart(fig_CV, use_container_width=True)

        else:
            pass
        return fig_logfc


class WebpageTexts:
    class ShortMessages:
        no_results = "No results available for this module."

    class Help:
        input_file = """
            Output file of the software tool. More information on the accepted format can 
            be found [here](https://proteobench.readthedocs.io/en/latest/modules/3-DDA-Quantification-ion-level/)
            """

        pull_req = """
            It is open to the public indefinitely.
            """

        input_format = """
            Please select the software you used to generate the results. If it is not yet 
            implemented in ProteoBench, you can use a tab-delimited format that is described 
            further [here](https://proteobench.readthedocs.io/en/latest/modules/3-DDA-Quantification-ion-level/)
        """

        parse_button = """
            Click here to see the output of your benchmark run
        """

        meta_data_file = """
            Please add a file with meta data that contains all relevant information about 
            your search parameters. See [here](https://proteobench.readthedocs.io/en/latest/modules/3-DDA-Quantification-ion-level/)
            for all compatible parameter files.
        """


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
    StreamlitUI()
