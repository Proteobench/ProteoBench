"""
Generic texts for the ProteoBench web interface.
"""


class WebpageTexts:
    """
    Generic texts for the ProteoBench web interface.
    """

    class ShortMessages:
        """
        Short messages for the de novo identification module.
        """

        privacy_notice = "https://www.ruhr-uni-bochum.de/en/privacy-notice"

        legal_notice = "https://www.ruhr-uni-bochum.de/en/legal-notice"

        no_results = "No results available for this module."

        title = "De Novo Identification (DDA - HCD) Module -ALPHA-"

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
        Help texts for the De Novo Identification (DDA - HCD) Module.
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

        radio_level = """
        **Precision vs Recall**

        This setting determines which metric is shown on the **x-axis** of the accuracy plot. The **y-axis always shows the amino-acid level metric**, while the x-axis represents the peptide-level metric.

        **Precision**  
        Precision measures how many of the reported identifications are correct. A high precision means that most predictions above the selected score threshold are accurate.

        *Precision = correct predictions ÷ predictions above threshold*

        This option is useful when you want to evaluate the **reliability of reported sequences**.

        **Recall**  
        Recall measures how many of the total spectra were correctly identified. A high recall means that a large fraction of spectra receive a correct prediction.

        *Recall = correct predictions ÷ total spectra*

        This option is useful when you want to evaluate the **identification coverage of the dataset**.

        **Note:**  
        Both metrics can be calculated at the **peptide level** or **amino-acid level**. In the plot, the selected peptide-level metric is displayed on the **x-axis**, while the corresponding amino-acid metric is shown on the **y-axis**.
        """

        radio_evaluation = """
        **Exact vs Match-based evaluation**

        This setting determines how predicted peptide sequences are considered **correct** when computing accuracy metrics.

        **Exact**  
        Only predictions that match the ground-truth peptide sequence exactly are considered correct.  
        This requires the **same amino acids and modifications in the same order**.

        This option provides the most **strict evaluation of de novo sequencing accuracy**.

        **Match-based**  
        Predictions are considered correct if they match the ground-truth sequence based on **cumulative fragment masses**.  
        The algorithm identifies the longest **mass-matching prefix and suffix** between the predicted and reference sequence.

        Two mass tolerances are used during matching:  
        *Cumulative mass threshold* – maximum allowed mass difference (50ppm) between cumulative fragment masses.  
        *Individual mass threshold* – maximum allowed mass difference (20ppm) between individual amino acids.

        This allows equivalent interpretations such as **isobaric amino acids (e.g. I/L)** or small sequence shifts that preserve peptide mass.

        This option provides a more **tolerant evaluation reflecting ambiguity in mass spectrometry data**.

        **Note:**  
        Match-based evaluation counts both **exact matches and mass-equivalent matches**, while exact evaluation only counts **perfect sequence matches**.
        """

        dataset_selection_indepth = """
        Determine which results to include in the in-depth comparisons below

        The **Uploaded dataset** represents the results of the data submitted by the you, the user.

        All other datasets consist of previously uploaded datasets by the ProteoBench-team and/or other users that submitted their results, validated by the ProteoBench team.

        In the plots below, results from specific *de novo* models can be hidden as well without having to unselect the results in the multiselect box.
        """

    class Description:
        ptm_overview = """
        This plot shows the **precision of predicted post-translational modifications (PTMs)** for each de novo sequencing tool. Each point represents a modification present in the dataset with its precision on the Y-axis.

        Precision is calculated as:

        *Precision = correctly predicted modifications ÷ total amino acids with this modification in the gold standard*

        A modification is counted as **correct** when it is predicted on the correct amino acid in the correct position, without requiring the full peptide sequence to be correctly predicted.

        Because different de novo engines support different PTMs, this plot highlights **which modifications are reliably identified and which ones are frequently missed or misassigned**.

        **Note:**  
        The dataset contains gold standard PSMs with specific PTMs. Tools that do not support certain modifications will show a precision of 0.
        """

        ptm_specific = """
        This plot compares how frequently a modification is predicted by a de novo tool relative to how often it occurs in the gold-standard dataset.

        Each point represents a de novo sequencing tool.

        The **x-axis (Precision – Ground-truth)** shows the fraction of ground-truth modifications that were correctly identified by the tool:

        Precision (Ground-truth) = correctly predicted modifications ÷ total modifications in the gold standard

        The **y-axis (Precision – de novo)** shows the fraction of predicted modifications that were correct:

        Precision (de novo) = correctly predicted modifications ÷ total predicted modifications

        Together, these axes show the **balance between modification recovery and prediction specificity**. Some tools may predict many modifications, increasing the chance of identifying true ones but also introducing more incorrect predictions.

        **How to interpret the plot**

        - **Top-right:** The tool predicts the modification frequently and most predictions are correct. This indicates strong performance for this PTM.
        - **Top-left:** The tool predicts the modification rarely, but when it does it is usually correct. This indicates conservative prediction.
        - **Bottom-right:** The tool predicts the modification often but many predictions are incorrect. This suggests overprediction.
        - **Bottom-left:** The tool rarely predicts the modification and most predictions are incorrect, indicating poor performance for this PTM.

        This plot therefore helps distinguish between tools that **predict modifications conservatively** and those that **predict them aggressively**, which may increase true positives but also false positives.
        """

        spectrum_features_overview = """
        These plots show how de novo sequencing accuracy changes as a function of different **spectral or peptide features**. Each tab corresponds to one feature, such as peptide length, missing fragmentation sites, or explained intensity.

        For each feature value (or binned range), the plot shows the **fraction of correctly predicted spectra**. Each line represents a de novo sequencing tool.

        The evaluation mode determines how predictions are considered correct:
        - **Exact** – only predictions that match the ground-truth sequence exactly are counted as correct.
        - **Match-based** – predictions that match the ground-truth sequence by cumulative fragment mass are also counted as correct.

        **Feature definitions**

        - **Peptide Length**  
        Number of amino acids in the ground-truth peptide sequence.

        - **Missing Fragmentation Sites**  
        Number of peptide bond cleavages for which no matching fragment ions are observed in the spectrum. A higher value indicates **less complete fragmentation**, which typically makes sequencing more difficult.

        - **% Explained Intensity**  
        Fraction of the total spectrum intensity that can be explained by fragments from the predicted peptide sequence. Higher values generally indicate **better agreement between the prediction and the spectrum**.

        **How to interpret the plots**

        - **Higher curves** indicate better sequencing accuracy for that feature range.
        - **Downward trends** often highlight conditions where de novo sequencing becomes more challenging (e.g. longer peptides or spectra with missing fragment ions).
        - Differences between tools can reveal **which algorithms handle difficult spectra or peptides more robustly**.

        Each point also represents a subset of spectra with the same feature value or within the same feature bin.

        **NOTE:**

        When less spectra are collected in a given bin (as seen by low bars under the lineplot), the pattern might become highly erratic.
        """

        species = """
        This plot shows de novo sequencing precision stratified by the **species of origin of the spectra**. Each point represents the prediction accuracy for spectra belonging to a specific organism in the dataset.

        Precision is calculated as the **fraction of spectra that were correctly sequenced** within each species group, with the number of peptides belonging to a species indicated by the size of the bars below the lineplot.

        Depending on the selected evaluation mode:
        - **Exact** – only predictions that match the ground-truth peptide sequence exactly are counted as correct.
        - **Match-based** – predictions that match the ground-truth sequence by cumulative fragment mass are also counted as correct.

        By separating the results per species, this plot highlights whether certain tools perform differently across **organisms with distinct proteomes and peptide characteristics**.

        **How to interpret the plot**

        - **Higher precision** indicates that a larger fraction of spectra from that species were correctly sequenced.
        - Differences between tools for a given species may reflect how well their models generalize to **different biological backgrounds**.
        - Lower performance for certain organisms can arise from factors such as **differences in peptide composition, modification patterns, or representation in training datasets**.

        Each species label corresponds to the organism from which the benchmark spectra were derived.

        For a full description related to the source of the data for each species, see the full module description. 
        """