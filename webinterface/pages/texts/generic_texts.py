"""
Generic texts for the ProteoBench web interface.
"""


class WebpageTexts:
    """
    Generic texts for the ProteoBench web interface.
    """

    class ShortMessages:
        """
        Short messages for the DDA quantification - precursor ions module.
        """

        privacy_notice = "https://www.ruhr-uni-bochum.de/en/privacy-notice"

        legal_notice = "https://www.ruhr-uni-bochum.de/en/legal-notice"

        no_results = "No results available for this module."

        title = "DDA quantification - precursor ions"

        initial_results = """
            Scroll down if you want to see the public benchmark runs publicly available
            today.
            """

        initial_parameters = """
            Additionally, you can fill out parameters for your search manually. Please,
            only fill out the parameters that are not already included in the input file.
            Only make changes if you are sure about the parameters you are changing.
            """

        run_instructions = """
            Now, press `Parse and Bench` to calculate the metrics from your input.
            """

        submission_result_description = """
            New figure including your benchmark run. The point corresponding to
            your data will appear bigger than the public data sets already available
            in ProteoBench.
            """

        submission_processing_warning = """
            **It will take a few working days for your point to be added to the plot**
            """

        parameters_additional = """Anything else you want to let us know? Please specifically
            add changes in your search parameters here, that are not obvious from the parameter file.
            """

    class Help:
        """
        Help texts for the DDA quantification - precursor ions module.
        """

        input_file = """
            Output file of the software tool. More information on the accepted format can
            be found [here](https://proteobench.readthedocs.io/en/latest/available-modules/4-quant-lfq-ion-dia-aif/)
            """

        pull_req = """
            It is open to the public indefinitely.
            """

        input_format = """
            Please select the software you used to generate the results. If it is not yet
            implemented in ProteoBench, you can use a tab-delimited format that is described
            further [here](https://proteobench.readthedocs.io/en/latest/available-modules/4-quant-lfq-ion-dia-aif/)
        """

        parse_button = """
            Click here to see the output of your benchmark run
        """

        meta_data_file = """
            Please add a file with meta data that contains all relevant information about
            your search parameters. See [here](https://proteobench.readthedocs.io/en/latest/available-modules/4-quant-lfq-ion-dia-aif/)
            for all compatible parameter files.
        """
