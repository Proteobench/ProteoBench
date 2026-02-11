###################
Adding a new module
###################

Here we provide a comprehensive overview of how to set up a new module in ProteoBench,
currently focused on quantification modules, where you only need to check and maybe 
slightly modify some components. For entirely new module types, you will need
to create a new version if it says 'check, modify or add' of a component.


Terms
=====

The following terms capture the crucial components:

   *Module*: All code and definitions for creating and comparing
   benchmarks of a new data type.

   *Intermediate data structure* (:class:`DataFrame`): Data structure needed for the
   calculation of the ``datapoint``, e.g. :class:`QuantDatapointHYE`. It contains
   the transformed and annotated data of an uploaded data file.

   *Datapoint*: Metadata and benchmarking metrics for a given data set. A ``datapoint``, e.g. :class:`QuantDatapointHYE`,
   is the data needed for the benchmarking and should also be represented by a json object.

Naming convention
=================

New modules and classes should be given descriptive names, and fit into existing naming schemes.
Go from general to specific properties, and make clear what distinguishes the module 
from existing ones, e.g. :class:`DIAQuantPeptidoformModule`.

The modules are stored in the Python package ``proteobench`` in the
``modules`` subpackage: `proteobench.modules <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules/quant/>`_. 

Programmatic structure
======================

The modules are located in the 
`proteobench/modules <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules>`_ 
directory. We separated the benchmarking modules into a different steps
that allow for a more modular and portable implementation.

Backend
------- 

The backend is organized into four main components that you can extend or customize:

**1. Module implementation** - Define how your benchmarking is performed
   - For quantification: Subclass :class:`~proteobench.modules.quant.quant_base_module.QuantModule`
   - Implement the ``benchmarking`` method with your specific logic
   - Initialize with custom parameters in the ``__init__`` method

**2. Data parsing** - Convert software output to standard format
   - Functions in :file:`proteobench/io/parsing/parse_ion.py` parse precursor ion data
   - :file:`proteobench/io/parsing/parse_settings.py` handles format conversion
   - Settings defined in TOML files in :file:`proteobench/io/parsing/io_parse_settings/`
   - For new software tools, extend :func:`~proteobench.io.parsing.parse_ion.load_input_file`

**3. Score calculation** - Compute benchmarking metrics
   - Base class: :class:`~proteobench.score.score_base.ScoreBase` (ABC)
   - For quantification: Use or extend :class:`~proteobench.score.quantscoresHYE.QuantScores`
   - Generates the ``intermediate`` data structure
   - For new module types: Create a new class inheriting from ``ScoreBase``
   - See :ref:`score-configuration` for detailed information

**4. Result representation** - Store benchmark results as datapoints
   - Base class: :class:`~proteobench.datapoint.datapoint_base.DatapointBase` (ABC)
   - For quantification: Use or extend :class:`~proteobench.datapoint.quant_datapoint_hye.QuantDatapointHYE`
   - Stores metadata and metrics for each benchmark run
   - For new module types: Create a new class inheriting from ``DatapointBase``
   - See :ref:`datapoint-configuration` for detailed information

**5. Visualization** - Create plots for web interface
   - Base class: :class:`~proteobench.plotting.plot_generator_base.PlotGeneratorBase` (ABC)
   - For LFQ modules: Use or extend :class:`~proteobench.plotting.plot_generator_lfq_HYE.LFQHYEPlotGenerator`
   - Generates module-specific visualizations
   - For new module types: Create a new class inheriting from ``PlotGeneratorBase``
   - See :ref:`plot-configuration` for detailed information

**6. Parameter parsing** - Parse tool-specific settings
   - Functions in :file:`proteobench/io/params` parse parameter setting files
   - Customize per software tool in :file:`proteobench/io/params/json/`

Architecture example
....................

Here's how these components work together for a quantification module:

.. code-block:: python

    # Module orchestrates the workflow
    module = QuantModule()
    
    # 1. Parse input file
    input_data = parse_ion.load_input_file(file_path, "MaxQuant")
    
    # 2. Calculate scores (generates intermediate data)
    score_calculator = QuantScores(...)
    intermediate = score_calculator.generate_intermediate(input_data, replicate_to_raw)
    
    # 3. Create datapoint from intermediate results
    datapoint = QuantDatapoint.generate_datapoint(intermediate, "MaxQuant", user_input)
    
    # 4. Generate plots for visualization
    plot_generator = LFQHYEPlotGenerator()
    plots = plot_generator.generate_in_depth_plots(performance_data, parse_settings)
    
    # 5. Store and display results
    # ... persist datapoint and plots to results repository

.. _plot-configuration:

Plot Configuration
..................

ProteoBench uses a modular plotting architecture where each module/module group defines its own plot generation
logic by subclassing :class:`~proteobench.plotting.plot_generator_base.PlotGeneratorBase`. This 
section explains how to configure plots for your module.

**Required Methods**

When creating a new plot generator, you must implement four abstract methods:

1. **generate_in_depth_plots()** - Creates the actual plot figures

   .. code-block:: python

       def generate_in_depth_plots(
           self, 
           performance_data: pd.DataFrame, 
           parse_settings: any, 
           **kwargs
       ) -> Dict[str, go.Figure]:
           """
           Generate module-specific plots.
           
           Returns
           -------
           Dict[str, go.Figure]
               Dictionary mapping plot names (keys) to plotly figures (values).
               Example: {"logfc": fig1, "cv": fig2, "ma_plot": fig3}
           """
           plots = {}
           
           # Example: fold change histogram
           plots["logfc"] = self._plot_fold_change_histogram(
               performance_data, 
               parse_settings.species_expected_ratio()
           )
           
           # Example: CV violin plot
           plots["cv"] = self._plot_cv_violinplot(performance_data)
           
           return plots

2. **get_in_depth_plot_layout()** - Defines how in-depth plots are displayed in the web interface

   .. code-block:: python

       def get_in_depth_plot_layout(self) -> list:
           """
           Define layout configuration for displaying plots.
           
           Returns
           -------
           list
               List of dictionaries, each defining a row of plots with:
               - "plots": list of plot names (keys from generate_in_depth_plots)
               - "columns": number of columns (1 or 2)
               - "titles": dict mapping plot names to display titles
           """
           return [
               {
                   "plots": ["logfc", "cv"],  # Two plots side-by-side
                   "columns": 2,
                   "titles": {
                       "logfc": "Log2 Fold Change distributions by species",
                       "cv": "Coefficient of variation distribution",
                   },
               },
               {
                   "plots": ["ma_plot"],  # Single plot, full width
                   "columns": 1,
                   "titles": {"ma_plot": "MA plot"},
               },
           ]

3. **get_in_depth_plot_descriptions()** - Provides help text for each plot

   .. code-block:: python

       def get_in_depth_plot_descriptions(self) -> Dict[str, str]:
           """
           Get descriptions shown to users for each plot.
           
           Returns
           -------
           Dict[str, str]
               Dictionary mapping plot names to descriptions
           """
           return {
               "logfc": "Log2 fold changes calculated from the performance data",
               "cv": "Coefficients of variation in Condition A and B",
               "ma_plot": "MA plot showing mean vs fold change",
           }

4. **plot_main_metric()** - Creates the main benchmarking plot (Tab 1)

   .. code-block:: python

       def plot_main_metric(
           self,
           result_df: pd.DataFrame,
           metric: str = "Median",
           hide_annot: bool = False,
           **kwargs
       ) -> go.Figure:
           """
           Generate the main performance metric plot.
           
           This plot appears on Tab 1 and shows all datapoints across time
           or other primary axis.
           
           Parameters
           ----------
           result_df : pd.DataFrame
               DataFrame with columns like 'results', 'software_name', etc.
           metric : str
               Which metric to display (e.g., "Median", "Mean")
           hide_annot : bool
               Whether to hide annotations
           **kwargs
               Additional module-specific parameters
               
           Returns
           -------
           go.Figure
               Plotly figure for the main metric
           """
           # Extract metric values from results
           all_metrics = [
               v2["median_abs_epsilon"] 
               for v in result_df["results"] 
               for v2 in v.values()
           ]
           
           # Create scatter plot
           fig = go.Figure()
           fig.add_trace(go.Scatter(
               x=result_df.index,
               y=all_metrics,
               mode='markers',
               # ... additional configuration
           ))
           
           return fig

**Example: Creating a Custom Plot Generator**

Here's a complete example for a hypothetical peptide identification module:

.. code-block:: python

    from proteobench.plotting.plot_generator_base import PlotGeneratorBase
    import plotly.graph_objects as go
    
    class PeptideIDPlotGenerator(PlotGeneratorBase):
        """Plot generator for peptide identification modules."""
        
        def generate_in_depth_plots(self, performance_data, **kwargs):
            plots = {}
            plots["score_dist"] = self._plot_score_distribution(performance_data)
            plots["fdr_curve"] = self._plot_fdr_curve(performance_data)
            return plots
        
        def get_in_depth_plot_layout(self):
            return [
                {
                    "plots": ["score_dist", "fdr_curve"],
                    "columns": 2,
                    "titles": {
                        "score_dist": "Score Distribution",
                        "fdr_curve": "FDR vs Number of IDs",
                    },
                }
            ]
        
        def get_in_depth_plot_descriptions(self):
            return {
                "score_dist": "Distribution of identification scores",
                "fdr_curve": "Trade-off between FDR and identification count",
            }
        
        def plot_main_metric(self, result_df, **kwargs):
            # Implementation of main metric plot
            fig = go.Figure()
            # ... create plot
            return fig
        
        def _plot_score_distribution(self, data):
            """Helper method to create score distribution plot."""
            fig = go.Figure()
            # ... implementation
            return fig
        
        def _plot_fdr_curve(self, data):
            """Helper method to create FDR curve plot."""
            fig = go.Figure()
            # ... implementation
            return fig

**Integrating Plots with Your Module**

After creating your plot generator, integrate it with your module class:

.. code-block:: python

    from proteobench.modules.quant.quant_base_module import QuantModule
    from proteobench.plotting.my_custom_plots import MyPlotGenerator
    
    class MyCustomModule(QuantModule):
        def __init__(self, token):
            super().__init__(token)
            self.plot_generator = MyPlotGenerator()  # Initialize plot generator
        
        def benchmarking(self, input_file, input_format, user_input, all_datapoints):
            # ... benchmarking logic ...
            
            # Generate plots using the plot generator
            plots = self.plot_generator.generate_in_depth_plots(
                performance_data=intermediate,
                parse_settings=parse_settings
            )
            
            # Main metric plot
            main_fig = self.plot_generator.plot_main_metric(all_datapoints)
            
            return intermediate, all_datapoints, input_df

.. _score-configuration:

Score Configuration
...................

ProteoBench uses a modular score calculation architecture where each module defines how to compute
benchmarking metrics by subclassing :class:`~proteobench.score.score_base.ScoreBase`. This section
explains how to configure score calculators for your module.

**Required Methods**

When creating a new score calculator, you must implement the abstract method from ``ScoreBase``:

1. **generate_intermediate()** - Computes metrics and creates the intermediate data structure

   .. code-block:: python

       def generate_intermediate(
           self,
           filtered_df: pd.DataFrame,
           replicate_to_raw: dict,
       ) -> pd.DataFrame:
           """
           Generate intermediate data structure with computed scores.
           
           This method processes the parsed input data and computes all
           benchmarking metrics needed for the module.
           
           Parameters
           ----------
           filtered_df : pd.DataFrame
               Parsed and filtered input data from the software tool
           replicate_to_raw : dict
               Mapping of replicate names to raw file names
               Example: {"A": ["run1.raw", "run2.raw"], "B": ["run3.raw", "run4.raw"]}
               
           Returns
           -------
           pd.DataFrame
               Intermediate dataframe containing:
               - Original input data columns
               - Computed metrics (fold changes, statistics, etc.)
               - Additional annotations needed for benchmarking
           """
           # 1. Select relevant columns from input
           relevant_data = filtered_df[["Raw file", "Precursor", "Intensity"]].copy()
           
           # 2. Add condition/replicate information
           replicate_df = self._convert_replicate_mapping(replicate_to_raw)
           relevant_data = pd.merge(relevant_data, replicate_df, on="Raw file")
           
           # 3. Compute condition statistics (mean, CV, etc.)
           stats_df = self._compute_condition_stats(relevant_data)
           
           # 4. Add species annotations
           species_df = filtered_df[["Precursor", "HUMAN", "YEAST", "ECOLI"]].drop_duplicates()
           stats_df = pd.merge(stats_df, species_df, on="Precursor")
           
           # 5. Compute performance metrics (epsilon, fold changes, etc.)
           result = self._compute_metrics(stats_df, self.expected_ratios)
           
           return result

**Example: Creating a Custom Score Calculator**

Here's a complete example for a hypothetical peptide identification module:

.. code-block:: python

    from proteobench.score.score_base import ScoreBase
    import pandas as pd
    import numpy as np
    
    class PeptideIDScores(ScoreBase):
        """Score calculator for peptide identification modules."""
        
        def __init__(self, fdr_threshold: float = 0.01):
            """
            Initialize the score calculator.
            
            Parameters
            ----------
            fdr_threshold : float
                FDR threshold for filtering identifications
            """
            self.fdr_threshold = fdr_threshold
        
        def generate_intermediate(
            self,
            filtered_df: pd.DataFrame,
            replicate_to_raw: dict,
        ) -> pd.DataFrame:
            """
            Generate intermediate data for peptide ID benchmarking.
            
            Computes metrics like:
            - Number of identifications at different FDR levels
            - Score distributions
            - Decoy hit rates
            """
            # 1. Filter by FDR
            filtered_df = filtered_df[filtered_df["q_value"] <= self.fdr_threshold]
            
            # 2. Add replicate information
            raw_to_replicate = self._invert_mapping(replicate_to_raw)
            filtered_df["replicate"] = filtered_df["Raw file"].map(raw_to_replicate)
            
            # 3. Compute identification statistics per replicate
            stats = filtered_df.groupby("replicate").agg({
                "Peptide": "nunique",  # Unique peptides
                "Protein": "nunique",  # Unique proteins
                "Score": ["mean", "std"],  # Score statistics
            }).reset_index()
            
            # 4. Compute overlap between replicates
            stats["overlap_score"] = self._compute_overlap(filtered_df)
            
            # 5. Add decoy information
            stats["decoy_rate"] = self._compute_decoy_rate(filtered_df)
            
            return stats
        
        def _invert_mapping(self, replicate_to_raw: dict) -> dict:
            """Convert replicate->raw mapping to raw->replicate."""
            return {
                raw: replicate 
                for replicate, raws in replicate_to_raw.items() 
                for raw in raws
            }
        
        def _compute_overlap(self, df: pd.DataFrame) -> float:
            """Compute peptide overlap between replicates."""
            replicates = df["replicate"].unique()
            if len(replicates) < 2:
                return 1.0
            
            peptide_sets = [
                set(df[df["replicate"] == rep]["Peptide"])
                for rep in replicates
            ]
            
            # Jaccard similarity
            intersection = set.intersection(*peptide_sets)
            union = set.union(*peptide_sets)
            return len(intersection) / len(union) if union else 0.0
        
        def _compute_decoy_rate(self, df: pd.DataFrame) -> float:
            """Compute rate of decoy hits."""
            total = len(df)
            decoys = len(df[df["Protein"].str.contains("DECOY")])
            return decoys / total if total > 0 else 0.0

.. _datapoint-configuration:

Datapoint Configuration
.......................

ProteoBench uses datapoints to store metadata and benchmarking results for each submission. Each module
defines its datapoint structure by subclassing :class:`~proteobench.datapoint.datapoint_base.DatapointBase`.
This section explains how to configure datapoints for your module.

**Required Components**

When creating a new datapoint class, you must:

1. **Define datapoint attributes** using ``@dataclass`` decorator

   .. code-block:: python

       from dataclasses import dataclass
       from proteobench.datapoint.datapoint_base import DatapointBase
       
       @dataclass
       class QuantDatapointHYE(DatapointBase):
           """
           Datapoint for LFQ quantification benchmarking.
           
           Stores both metadata (search parameters, software versions) and
           results (benchmarking metrics at different filtering levels).
           """
           # Metadata fields
           id: str
           software_name: str
           software_version: str
           search_engine: str
           ident_fdr_psm: float
           enable_match_between_runs: bool
           enzyme: str
           # ... other metadata ...
           
           # Results
           results: dict  # Contains metrics at different filters

2. **Implement generate_id()** - Create a unique identifier

   .. code-block:: python

       def generate_id(self) -> None:
           """
           Generate a unique hash ID for this benchmark run.
           
           The ID should be deterministic based on the input data and settings,
           allowing detection of duplicate submissions.
           """
           # Combine relevant fields into a string
           id_string = (
               f"{self.software_name}_{self.software_version}_"
               f"{self.search_engine}_{self.ident_fdr_psm}_"
               f"{self.enable_match_between_runs}_{self.enzyme}"
               # ... include all distinguishing parameters ...
           )
           
           # Create hash
           import hashlib
           self.id = hashlib.sha256(id_string.encode()).hexdigest()[:10]

3. **Implement generate_datapoint()** - Create datapoint from intermediate data

   .. code-block:: python

       @staticmethod
       def generate_datapoint(
           intermediate: pd.DataFrame,
           input_format: str,
           user_input: dict,
           **kwargs
       ) -> pd.Series:
           """
           Generate a datapoint from intermediate data and user input.
           
           Parameters
           ----------
           intermediate : pd.DataFrame
               Intermediate DataFrame with computed metrics
           input_format : str
               Software tool name (e.g., "MaxQuant", "FragPipe")
           user_input : dict
               Dictionary containing metadata from submission form
               
           Returns
           -------
           pd.Series
               Series containing the datapoint data, ready to be added to results
           """
           # 1. Compute metrics at different filtering levels
           results = {}
           for min_obs in [2, 3, 4, 5]:
               filtered = intermediate[intermediate["nr_observed"] >= min_obs]
               
               results[min_obs] = {
                   "median_abs_epsilon": filtered["abs_epsilon"].median(),
                   "mean_abs_epsilon": filtered["abs_epsilon"].mean(),
                   "nr_prec": len(filtered),
               }
           
           # 2. Create datapoint object
           import dataclasses
           datapoint = QuantDatapointHYE(
               id="",  # Will be set by generate_id()
               software_name=input_format,
               software_version=user_input.get("software_version", "unknown"),
               search_engine=user_input.get("search_engine", input_format),
               ident_fdr_psm=user_input.get("ident_fdr_psm", 0.01),
               enable_match_between_runs=user_input.get("enable_match_between_runs", False),
               enzyme=user_input.get("enzyme", "Trypsin"),
               results=results,
           )
           
           # 3. Generate unique ID
           datapoint.generate_id()
           
           # 4. Convert to pandas Series for storage
           return pd.Series(dataclasses.asdict(datapoint))

**Example: Creating a Custom Datapoint**

Here's a complete example for a hypothetical peptide identification module:

.. code-block:: python

    from dataclasses import dataclass
    from proteobench.datapoint.datapoint_base import DatapointBase
    import hashlib
    import dataclasses
    import pandas as pd
    
    @dataclass
    class PeptideIDDatapoint(DatapointBase):
        """Datapoint for peptide identification benchmarking."""
        
        # Metadata
        id: str
        software_name: str
        software_version: str
        database: str
        fdr_threshold: float
        
        # Results
        num_peptides: int
        num_proteins: int
        replicate_overlap: float
        
        def generate_id(self) -> None:
            """Generate unique ID based on metadata."""
            id_string = (
                f"{self.software_name}_{self.software_version}_"
                f"{self.database}_{self.fdr_threshold}"
            )
            self.id = hashlib.sha256(id_string.encode()).hexdigest()[:10]
        
        @staticmethod
        def generate_datapoint(
            intermediate: pd.DataFrame,
            input_format: str,
            user_input: dict,
            **kwargs
        ) -> pd.Series:
            """Generate datapoint from intermediate results."""
            metrics = intermediate.iloc[0]  # Assuming aggregated data
            
            datapoint = PeptideIDDatapoint(
                id="",
                software_name=input_format,
                software_version=user_input.get("software_version", "unknown"),
                database=user_input.get("database", "unknown"),
                fdr_threshold=user_input.get("fdr_threshold", 0.01),
                num_peptides=int(metrics["num_peptides"]),
                num_proteins=int(metrics["num_proteins"]),
                replicate_overlap=float(metrics["overlap_score"]),
            )
            
            datapoint.generate_id()
            return pd.Series(dataclasses.asdict(datapoint))

Web interface
-------------

The web interface is written in Streamlit. Each module gets assigned a
specific ``page``. There are only few changes necessary
as the main calculations are done in
:class:`~webinterface.pages.base_pages.quant.QuantUIObjects`. It contains most
functionality to create the web interface for each quantification module.

.. warning::
   QuantUIObjects should be simplified.

:file:`webinterface.pages.pages_variables` contains files with ``dataclass``\ es for the 
text for the different modules in the interface.

Relevant functions in :class:`~webinterface.pages.base_pages.quant.QuantUIObjects`
...................................................................................

- Tab 1: :meth:`~webinterface.pages.base_pages.quant.QuantUIObjects.display_all_data_results_main`
  shows the description of the module, which is defined in
  `webinterface/pages/pages_variables <https://github.com/Proteobench/ProteoBench/tree/main/webinterface/pages/pages_variables>`_
  where we define custom text and **unique** component names for each module
  (e.g. for the main plot)
  to not display on several pages the same plot in the streamlit webinterface.
- Tab 2: :meth:`~webinterface.pages.base_pages.quant.QuantUIObjects.display_submission_form`
  displays the submission form based on the module toml configurations in
  `proteobench/io/parsing/io_parse_settings <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/parsing/io_parse_settings>`_.
- Tab 2.5: :meth:`~webinterface.pages.base_pages.quant.QuantUIObjects.generate_current_data_plots`
  displays the metric plot if a new results were added to the module.
- Tab 3: :meth:`~webinterface.pages.base_pages.quant.QuantUIObjects.display_all_data_results_submitted`
- Tab 4: :meth:`~webinterface.pages.base_pages.quant.QuantUIObjects.display_public_submission_ui`
creates  the input fields for the metadata and the
input file format and type. They are given in the
`proteobench/modules/parsing/io_parse_settings <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules/io/io_parse_settings>`_ folder,
same as for the backend of the module.

:meth:`~webinterface.pages.base_pages.quant.QuantUIObjects.generate_results` gathers the data from the backend
and displays them in several figures. Here you will need to edit and adapt the code
to show the respective figures with the right metadata.

Change the text and the field names accordingly in the ``dataclass``
in `webinterface.pages.pages_variables <https://github.com/Proteobench/ProteoBench/tree/main/webinterface/pages/pages_variables>`_.

Storing results
----------------

Results are stored in separate GitHub repositories, where the Webinterface first adds
datapoints to an fork of the module-specific results directory. The core
functionality is in
`proteobench.github.gh <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/github>`_

1. Make a new repository in the
   `Proteobench organisation <https://github.com/Proteobench>`_
   and give it a sensible name, e.g. ``Proteobench/Results_quant_ion_DDA``.
2. Login to `Proteobot organisation <https://github.com/proteobot>`_
   (ask for the login details from relevant people)
3. Make a fork of the new repository under ``ProteoBench`` to ``Proteobot``



Documentation
-------------

We strongly recommend to keep documenting your code. The documentation is written in Markdown or richtext
and can be found in the `docs <https://github.com/Proteobench/ProteoBench/tree/main/docs>`_ folder. We
use Sphinx and myst-parser to build the website.

1. `docs/available-modules <https://github.com/Proteobench/ProteoBench/tree/main/docs/available-modules>`_
   Here you can add a file for your new module, using any of the existing module descriptions as a template.
2. `API documentation for your module <https://proteobench.readthedocs.io/en/latest/developer-guide/api/webinterface/webinterface.pages/#submodulest>`_ 
   will be added automatically. You can see it on the readthedocs page built specifically for your pull request.

To work locally on the documentation and get a live preview, install the requirements and run
`sphinx-autobuild`:

.. code-block:: sh

    pip install '.[docs]'
    # selecting the docs folder to watch for changes
    sphinx-autobuild  --watch ./docs ./docs/source/ ./docs/_build/html/

Then browse to http://localhost:8000 to watch the live preview.


Checklist
=========

This checklist is meant to help you add a new module to ProteoBench. It is not
meant to be exhaustive, but it should cover the most important steps. To see which 
files need to change for adding a module, have a look at one of the
recent examples. Adding a quant module (based on other quant modules):
`PR 703 <https://github.com/Proteobench/ProteoBench/pull/703/files>`_. Or for adding
a new type of module: 
`PR 727 <https://github.com/Proteobench/ProteoBench/pull/727/files>`_. 


1. Subclass :class:`~proteobench.modules.quant.quant_base_module.QuantModule` and replace
   the :func:`benchmarking` method with your own implementation. You can copy from other
   modules in the folder 
   `proteobench/modules <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules>`_
2. Define the input formats using toml files in a new subfolder of
   `proteobench/io/parsing/io_parse_settings <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/parsing/io_parse_settings>`_
3. Check, modify or add a parsing procedures in
   `proteobench/io/parsing <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/parsing>`_
   e.g. :file:`parse_ion.py` or :file:`parse_peptidoform.py`.
4. **Create a datapoint class** by subclassing
   :class:`~proteobench.datapoint.datapoint_base.DatapointBase` in
   `proteobench/datapoint <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/datapoint>`_.
   Define attributes for metadata and results, then implement:
   
   - :meth:`generate_id` - Create unique identifier for the benchmark run
   - :meth:`generate_datapoint` - Generate datapoint from intermediate data
   
   See :ref:`datapoint-configuration` for detailed examples.
5. **Create a score calculator** by subclassing
   :class:`~proteobench.score.score_base.ScoreBase` in
   `proteobench/score <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/score>`_.
   Implement the required method:
   
   - :meth:`generate_intermediate` - Compute metrics and create intermediate data structure
   
   See :ref:`score-configuration` for detailed examples.
6. **Create a plot generator** by subclassing
   :class:`~proteobench.plotting.plot_generator_base.PlotGeneratorBase` in
   `proteobench/plotting <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/plotting>`_.
   Implement the four required methods:
   
   - :meth:`generate_in_depth_plots` - Create plot figures
   - :meth:`get_in_depth_plot_layout` - Define plot display layout
   - :meth:`get_in_depth_plot_descriptions` - Provide plot descriptions
   - :meth:`plot_main_metric` - Create the main benchmarking plot
   
   See :ref:`plot-configuration` for detailed examples.
7. Check, modify or add parameter parsing for new tools in
   `proteobench/io/params <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/params>`_
8. Add a new page defining the module webinterface to
   `webinterface/pages <https://github.com/Proteobench/ProteoBench/tree/main/webinterface/pages>`_
   using the base functionality and adding ``pages_variables`` dataclasses.
9. Create a new results repository for the module in
   `Proteobench <https://github.com/Proteobench>`_ and 
   a fork in `Proteobot <https://github.com/proteobot>`_
