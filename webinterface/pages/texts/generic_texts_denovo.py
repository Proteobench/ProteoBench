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

        title = "De Novo Identification (DDA - HCD) Module"

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

        warning_archived = """This module is in ARCHIVED phase. The figure presented below 
            and the metrics calculation will no longer be updated. See module documentation 
            for more details.
            """

        warning_alpha = """This module is in ALPHA phase. It  remains to be fully discussed 
            with experts and should be used with caution.
            """

        warning_beta = """This module is in BETA phase. The figure presented below and 
            the metrics calculation may change in the near future.
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
        **Precision vs AUC**

        This setting determines which metric is shown on the **x-axis** of the accuracy plot. The **y-axis always shows the amino-acid level metric**, while the x-axis represents the peptide-level metric.

        **Precision**
        Precision measures how many of the reported identifications are correct, considering every prediction
        (no score threshold applied). A high precision means that most reported sequences are accurate.

        *Precision = correct predictions ÷ all predictions*

        This option is useful when you want to evaluate the **reliability of reported sequences** at a single,
        fixed operating point.

        **AUC**
        AUC (average precision) is the area under the tool's precision-vs-coverage curve, swept across every
        possible score threshold. A high AUC means the tool stays precise even as more of its lower-confidence
        predictions are included, not just at its single default operating point.

        This option is useful when you want to evaluate a tool's **overall ranking quality** rather than one
        specific threshold. It can be `N/A` for tools that don't report a real per-residue confidence score.

        **Note:**
        Both metrics can be calculated at the **peptide level** or **amino-acid level**. In the plot, the selected peptide-level metric is displayed on the **x-axis**, while the corresponding amino-acid metric is shown on the **y-axis**.

        **Reading the four background regions**

        The plot background is shaded from light (bottom-left) to dark (top-right): the further
        into the top-right corner a point sits, the better it's performing on both axes at once.
        The dashed lines at the midpoint of each axis also split the plot into four named regions:

        - **Good performance** (top-right): both peptide- and amino-acid-level metrics are high.
        - **Near-miss** (top-left): peptide-level is low but amino-acid-level is high. Often
          suggests a very similar peptide -- usually only one or a few residues off from the
          true sequence.
        - **Low performance** (bottom-left): both metrics are low.
        - **Alternative candidate** (bottom-right): peptide-level is high but amino-acid-level
          is low. Suggests a fully different peptide when wrong, rather than a near match --
          this can indicate an alternative candidate that a database search might miss, or that
          the spectrum quality was too low to call any part of the sequence correctly. This
          region is expected to be sparse: amino-acid-level correctness dominates the tally in
          most realistic cases, so most tools land at or above the diagonal rather than below it.
        """

        radio_evaluation = """
        **Exact vs Mass-based evaluation**

        This setting determines how predicted peptide sequences are considered **correct** when computing accuracy metrics.

        **Exact**
        Only predictions that match the ground-truth peptide sequence exactly are considered correct.
        This requires the **same amino acids and modifications in the same order**.

        This option provides the most **strict evaluation of de novo sequencing accuracy**. Two toggles let you
        relax this strictness for ambiguities that are inherent to the data (see below).

        **Mass-based**
        Predictions are considered correct if they match the ground-truth sequence based on **cumulative fragment masses**.
        The algorithm identifies the longest **mass-matching prefix and suffix** between the predicted and reference sequence.

        Two mass tolerances are used during matching:
        *Cumulative mass threshold* – maximum allowed mass difference (50ppm) between cumulative fragment masses.
        *Individual mass threshold* – maximum allowed mass difference (20ppm) between individual amino acids.

        This allows equivalent interpretations such as **isobaric amino acids (e.g. I/L)** or small sequence shifts that preserve peptide mass.

        This option provides a more **tolerant evaluation reflecting ambiguity in mass spectrometry data**.

        **Note:**
        Mass-based evaluation counts both **exact matches and mass-equivalent matches**, while exact evaluation only counts **perfect sequence matches**
        (subject to the ambiguity toggles below).
        """

        toggle_il = """
        **Allow I/L mismatches**

        Isoleucine (I) and Leucine (L) have identical mass, so a de novo model cannot distinguish
        them from the spectrum alone -- many tools only ever predict one of the two. When this
        toggle is on, a predicted I is counted as correct for a ground-truth L (and vice versa)
        under **Exact** evaluation.

        This toggle is forced on and disabled under **Mass-based** evaluation, since mass-based
        matching already can't tell I and L apart regardless of this setting.
        """

        toggle_deamidation = """
        **Allow deamidation mismatches (Q↔E, N↔D)**

        Deamidation converts glutamine (Q) to a residue that is essentially identical in mass to
        glutamate (E), and asparagine (N) to one essentially identical in mass to aspartate (D).
        A de novo model may therefore predict the plain acidic residue (E or D) where the ground
        truth has the deamidated amide (Q or N). When this toggle is on, such a prediction is
        counted as correct under **Exact** evaluation.

        This toggle is forced on and disabled under **Mass-based** evaluation, since mass-based
        matching already can't tell these apart regardless of this setting.
        """

        dataset_selection_indepth = """
        Determine which results to include in the in-depth comparisons below

        The **Uploaded dataset** represents the results of the data submitted by the you, the user.

        All other datasets consist of previously uploaded datasets by the ProteoBench-team and/or other users that submitted their results, validated by the ProteoBench team.

        In the plots below, results from specific *de novo* models can be hidden as well without having to unselect the results in the multiselect box.
        """

    class Description:
        """Descriptions for de novo in-depth plots and evaluation views."""

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
