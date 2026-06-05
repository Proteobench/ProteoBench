# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProteoBench is a community-curated benchmarking platform for proteomics data analysis pipelines. It compares outputs from mass spectrometry tools (MaxQuant, DIA-NN, FragPipe, Spectronaut, AlphaDIA, Sage, PEAKS, MSAID, AlphaPept, i2MassChroQ, ProlineStudio, MSAngel, WOMBAT, MetaMorpheus, quantms, Proteome Discoverer) across different acquisition modes (DDA/DIA) and instrument types (QExactive, Astral, diaPASEF, AIF, ZenoTOF, single-cell). It also hosts a de novo sequencing module (Casanovo, InstaNovo, and related tools).

The core library (`proteobench/`) processes tool outputs into a standardized format and computes quantification metrics. A Streamlit web app (`webinterface/`) provides the interactive UI. Benchmark results are stored as individual JSON files and submitted via GitHub pull requests to separate results repositories (e.g., `Proteobench/Results_quant_ion_DDA`).

## Common Commands

```bash
# Install for development
pip install -e '.[dev]'

# Optional extras: docs tooling, or the web app (streamlit>1.27, scipy)
pip install -e '.[docs]'
pip install -e '.[web]'

# Run all tests
pytest

# Run a single test file
pytest test/test_parse_params_maxquant.py

# Run a single test by name
pytest test/test_module_quant_ion_DDA_QExactive.py -k "test_benchmarking_return_types"

# Run tests via nox (uses uv backend)
nox --session "tests"

# Run notebooks via nox
nox --session "test_notebooks"

# Check formatting (CI uses black ~=23.0)
black --check proteobench

# Fix formatting
black proteobench

# Lint (CI only fails on E9,F63,F7,F82)
flake8 . --select=E9,F63,F7,F82

# Start the web interface
cd webinterface && streamlit run Home.py

# Build docs with live preview
pip install -e '.[docs]'
sphinx-autobuild --watch ./proteobench ./docs/ ./docs/_build/html/

# Build docs via nox (supports --serve and -b linkcheck)
nox --session "docs"
nox --session "docs" -- --serve
nox --session "docs" -- -b linkcheck

# Update parameter documentation (CI checks this is up-to-date)
# Must be run from inside docs/ (uses relative input path)
cd docs && python parse_tables.py

# Update module grid on docs homepage (CI checks this is up-to-date)
python docs/generate_module_grid.py

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## Code Style

- **Black** formatter: line-length 120, target Python 3.11
- **isort**: profile "black"
- **flake8**: max-line-length 120. CI hard-fails only on E9,F63,F7,F82, but also runs two non-blocking flake8 passes: a full `--exit-zero` pass and a bugbear/comprehensions pass (`--select=B,C4`). The `[dev]` extra includes `flake8-bugbear` and `flake8-comprehensions`.
- **numpydoc** validation on all code except `test/`, `exceptions.py`, `noxfile.py`, `jupyter_notebooks/`, `docs/parse_tables.py`
- Python >= 3.11 required; CI tests on 3.11, 3.12, 3.13

## Architecture

### Package Layout (important)

Scoring and datapoint code are **top-level packages**, not nested under `modules/`:

- `proteobench/score/`: `score_base.py` (`ScoreBase` ABC), `quantscoresHYE.py` (`QuantScoresHYE`), `quantscoresPYE.py` (`QuantScoresPYE`), `denovoscores.py` (`DenovoScores`)
- `proteobench/datapoint/`: `datapoint_base.py` (`DatapointBase` ABC), `quant_datapoint.py` (`QuantDatapointHYE`, `QuantDatapointPYE`), `denovo_datapoint.py` (`DenovoDatapoint`)
- `proteobench/plotting/`: `plot_generator_base.py` (`PlotGeneratorBase` ABC) plus HYE/PYE/DeNovo generators
- `proteobench/modules/`: thin module classes (quant, denovo, rescoring) that orchestrate the pipeline

So, for example, `from proteobench.score.quantscoresHYE import QuantScoresHYE` and `from proteobench.datapoint.quant_datapoint import QuantDatapointHYE`.

### Core Benchmarking Pipeline

The reference entry point is `run_benchmarking()` in `proteobench/modules/quant/benchmarking.py`. **Only two modules actually delegate to it:** `DDAQuantIonModuleQExactive.benchmarking()` calls `run_benchmarking()`, and `DDAQuantIonAstralModule.benchmarking()` calls `run_benchmarking_with_timing()` (a profiling variant returning an extra `timings` dict with per-step durations) and slices `[:3]`. The Astral DDA module also exposes a `benchmarking_2()` that returns the full 4-tuple including `timings`. **All other quant modules implement the same load/parse/score/datapoint pipeline inline within their own `benchmarking()` methods** rather than calling the shared helper.

In `run_benchmarking()`, each step is a helper wrapped with `handle_benchmarking_error(<ExceptionType>, ...)`, which maps raised exceptions to the custom exception hierarchy (see `proteobench/exceptions.py`). Note that `run_benchmarking_with_timing()` calls the underlying functions directly and does **not** apply this error wrapping.

**Pipeline steps (decorated helpers in `run_benchmarking`):**

1. **Load input** (`_load_input`, `ParseError`) - `io/parsing/parse_ion.py:load_input_file()` dispatches to format-specific loaders via the `_LOAD_FUNCTIONS` dict (17 entries). AlphaDIA has special handling: auto-detects matrix vs long format between two files and supports v1 (TSV) and v2 (parquet).

2. **Load settings** (`_load_settings`, `ParseSettingsError`) - `ParseSettingsBuilder(parse_settings_dir, module_id).build_parser(input_format)` loads the tool's TOML config and builds a `ParseSettingsQuant` parser.

3. **Convert to standard format** (`_convert_format`, `ConvertStandardFormatError`) - `ParseSettingsQuant.convert_to_standard_format()` runs a 10-step pipeline: validate/rename columns, create replicate mapping, filter decoys, clean run names via `_clean_run_name()` regex, mark contaminants, process species (filter multi-species by `min_count_multispec`), process modifications to ProForma notation, melt wide-to-long if needed (with run-name cleanup on the `Raw file` column), filter zero intensities, format by analysis level (create the "precursor ion" or "peptidoform" column).

4. **Create quant scores** (`_create_quant_scores`, `QuantificationError`) - instantiates `QuantScoresHYE(precursor_column_name, species_expected_ratio, species_dict)`.

5. **Generate intermediate** (`_generate_intermediate`, `IntermediateFormatGenerationError`) - `QuantScoresHYE.generate_intermediate()`:
   - `compute_condition_stats()`: Groups by precursor/condition, computes log2 intensities, CV (= Intensity_std/Intensity_mean), pivots wide with columns like `log_Intensity_mean_A`, `CV_B`. Calculates `log2_A_vs_B = log_Intensity_mean_A - log_Intensity_mean_B`.
   - `compute_epsilon()`: Filters to single-species precursors (`unique==1`), assigns `log2_expectedRatio` per species (e.g., log2(2.0) for YEAST), computes `epsilon = log2_A_vs_B - log2_expectedRatio` (accuracy) plus the empirical per-species centers `log2_empirical_median`/`log2_empirical_mean` and `epsilon_precision_median`/`epsilon_precision_mean = log2_A_vs_B - empirical_center` (precision/reproducibility). When no single-species precursors remain it returns an empty DataFrame with the expected columns.

6. **Generate datapoint** (`_generate_datapoint`, `DatapointGenerationError`) - `QuantDatapointHYE.generate_datapoint()`:
   - Computes `intermediate_hash` = SHA1 of the intermediate DataFrame string representation (`intermediate.to_string()`).
   - Calls `get_metrics()` for `min_nr_observed` thresholds `1..max_nr_observed` (default 6; configurable, the Plasma/PYE path uses 12), producing a nested dict `{threshold: {metric_name: value, ...}, ...}`.
   - Metrics include: epsilon accuracy (`{median,mean}_abs_epsilon_global` and `_eq_species`, plus per-species), epsilon precision (`*_abs_epsilon_precision_global`/`_eq_species`), per-species empirical centers (`{median,mean}_log2_empirical_{SPECIES}`), CV quantiles (`CV_median`/`q75`/`q90`/`q95`), `roc_auc` (abs-log2FC based), precursor counts (`nr_prec`), and `variance_epsilon_global`. Note: `compute_roc_auc_directional()` is implemented but is **not** invoked by `get_metrics()`, so only the abs-based ROC-AUC is stored.
   - Returns a `pd.Series` with all datapoint fields.

7. **Append datapoint** (`_append_datapoint`, `DatapointAppendError`) - calls the supplied `add_datapoint_func`. Deduplication by `intermediate_hash` (rejecting duplicate submissions) is performed inside that function (e.g., `check_new_unique_hash()` in `quant_base_module.py`), not in `_append_datapoint` itself.

### Intermediate DataFrame Structure

After scoring, each row is one precursor/peptidoform. Key columns: precursor ion (or peptidoform), species flags (HUMAN/YEAST/ECOLI), species, `log2_A_vs_B`, `log2_expectedRatio`, `epsilon`, `log2_empirical_median`, `log2_empirical_mean`, `epsilon_precision_median`, `epsilon_precision_mean`, `CV_A`, `CV_B`, `log_Intensity_mean_A`/`B`, `nr_observed`, plus per-raw-file intensity columns.

### Results Dictionary Structure

The `results` field in each datapoint is `{1: {...}, 2: {...}, ..., N: {...}}` where keys are `min_nr_observed` thresholds (1..max_nr_observed, default N=6) and values contain all metrics for that threshold. This allows querying performance at different stringency levels. The default display threshold (`default_cutoff_min_prec`) is 3. Keys are integers when generated in-process; the legacy/filter code also handles string keys for JSON-loaded data.

### Accuracy vs Precision Metrics

- **Accuracy (epsilon)**: `log2_A_vs_B - log2_expectedRatio`, deviation from the known/expected species ratio. Requires ground truth.
- **Precision (epsilon_precision)**: `log2_A_vs_B - empirical_center`, deviation from the empirical per-species center. Measures reproducibility.
- **Modes**: "global" aggregates all species as one population; "eq_species" takes the mean of per-species aggregations (equal weighting regardless of count).

### Legacy Compatibility

Old datapoints have `{metric}_abs_epsilon` without a mode suffix. New datapoints have both `{metric}_abs_epsilon_global` and `{metric}_abs_epsilon_eq_species`. Plotting and filtering code (`filter_df_numquant_epsilon`) tries the new mode-suffixed key first and falls back to the legacy key. Species-weighted mode filters out old datapoints that lack the new metrics.

### Exception Hierarchy (`proteobench/exceptions.py`)

The benchmarking-step exceptions subclass `ProteobenchError` (lowercase b):

```
ProteobenchError
├── ParseError                              # Input file loading
├── ParseSettingsError                      # TOML settings loading
├── ConvertStandardFormatError              # Standard format conversion
├── IntermediateFormatGenerationError        # Scoring
├── QuantificationError                     # Quant score creation
├── DatapointGenerationError                # Datapoint creation
├── DatapointAppendError                    # Appending to collection
└── PlotError                               # Plotting

DatasetAlreadyExistsOnServerError           # standalone Exception subclass
```

**Caveat (likely an unintentional code bug worth flagging before relying on it):** `exceptions.py` also defines a near-duplicate base class `ProteoBenchError` (capital B) and defines `ParseError` twice (the second definition, subclassing `ProteobenchError`, wins). `ValidationError` subclasses `ProteoBenchError` (capital B), so it sits in a separate branch from the benchmarking-step exceptions. Treat the capitalization carefully and consider consolidating these.

Each `run_benchmarking()` step wraps its errors into the appropriate type via `handle_benchmarking_error`.

### TOML-Based Parse Settings

Each software tool + module combination has a TOML file in `proteobench/io/parsing/io_parse_settings/Quant/lfq/<DDA|DIA>/<ion|peptidoform>/<instrument>/`. The master mapping is `io_parse_settings/parse_settings_files.toml` (maps `module_id` sections to TOML filenames). Each settings directory also has a `module_settings.toml`.

`io_parse_settings/tool_metadata.toml` is a platform-wide metadata file with one section:
- `[open_source].tools`: list of tool names whose source code is publicly available (13 entries: AdaNovo, AlphaDIA, AlphaPept, Casanovo, DeepNovo, i2MassChroQ, InstaNovo, MetaMorpheus, Pi-HelixNovo, Pi-PrimeNovo, PointNovo, Sage, ProlineStudio). Used by `get_open_source_tools()` in `parse_settings.py` to populate the `open_source` (✅) column in the Benchmark Results table. Names must match the `software_name` values set in `io/params/*.py`.

**Parser classes.** There are three classes in `parse_settings.py`:
- `ParseSettingsQuant`: parser for all quant modules.
- `ParseSettingsDeNovo`: parser for `denovo_DDA_HCD`. It uses different TOML sections (`[mapper]`, `[spectrum_id_mapper]`, `[sequence_mapper]`) and loads a ground-truth CSV (`GROUND_TRUTH_FILENAME`), checking `GROUND_TRUTH_DIR_SERVER`, then `GROUND_TRUTH_DIR_LOCAL_DENOVO`, then downloading from `GROUND_TRUTH_URL`.
- `ParseModificationSettings`: backs the optional `[modifications_parser]` section, attached by `ParseSettingsBuilder.build_parser()` only when that section is present.

**Quant tool TOML structure:**
- `[mapper]`: column renames (e.g., `"Sequence" = "Sequence"`)
- `[condition_mapper]`: raw file name -> condition ("A"/"B"). Keys are normalized at init via `_clean_run_name()` (extensions like `.mzML`, `.raw` are stripped automatically).
- `[run_mapper]`: raw file name -> display name (also normalized at init)
- `[species_mapper]`: protein ID flag -> species (e.g., `"_YEAST" = "YEAST"`)
- `[general]`: `contaminant_flag`, `decoy_flag`, and optionally `run_name_cleanup` (regex to override the default extension-stripping pattern)
- `[modifications_parser]` (optional): `parse_column`, `before_aa`, `isalpha`, `isupper`, `pattern` (regex), `modification_dict` (mass -> name)
- `[upload_info]`: human-readable guidance shown in the web UI when the tool is selected. Keys: `datapoint_file` (filename), `datapoint_file_description` (shown above the result-file uploader in Tab 2), `params_file` (filename), `params_file_description` (shown above the metadata uploader in Tab 6). Markdown is supported in description strings. The Custom format uses `datapoint_file_description` to embed a module-specific link to the documentation. Missing `[upload_info]` is handled gracefully — no message is shown.
- `[upload_info_overrides.<tool_name>]` (optional): per-tool overrides applied on top of `[upload_info]` when `ParseSettingsBuilder.get_upload_info(tool_name)` is called. Used when multiple tool names share the same TOML file but require different upload guidance. Example: `parse_settings_diann.toml` is shared by "DIA-NN" and "FragPipe (DIA-NN quant)"; the override supplies the correct `.workflow` params description for the latter.

### Run Name Cleanup (`_clean_run_name`)

File/column names from tool outputs may include extensions (`.mzML`, `.raw`, `.mzML.gz`, `.d`, `.wiff`) or tool-specific suffixes (`_uncalibrated` from FragPipe DIA-NN, see #827). The `_clean_run_name()` method on `ParseSettingsQuant` strips these using a regex so they match the `condition_mapper` keys. The default regex is:
```
(?:\.mzML\.gz|\.mzML|\.raw|\.RAW|\.d|\.wiff|_uncalibrated)$
```
It also strips path prefixes, but path stripping is **disabled for DataFrame column names** (`strip_path=False`) so columns like PEAKS' `m/z` are not mangled; it is applied (with `strip_path=True`) to `Raw file` column values and to `condition_mapper`/`run_mapper` keys at init. To override per-tool, add to the TOML:
```toml
[general]
run_name_cleanup = "(?:\\.custom_suffix|\\.raw)$"
```

**Module settings TOML structure:**
- `[species_expected_ratio.<SPECIES>]`: `A_vs_B` (float ratio), `color` (hex)
- `[general]`: `min_count_multispec` (int), `level` ("ion" or "peptidoform")

The `MODULE_TO_CLASS` dict at the bottom of `parse_settings.py` routes module IDs to parser classes: all `quant_lfq_*` modules use `ParseSettingsQuant`, and `denovo_DDA_HCD` uses `ParseSettingsDeNovo`. (The dict contains a benign duplicate `quant_lfq_DDA_ion_Astral` key, and has no `quant_lfq_DIA_peptidoform` entry, matching that module being an unregistered stub.)

`io/parsing/utils.py` provides ProForma fixed-modification helpers: `add_fixed_mod(proforma, mod_name, aas)` and `add_maxquant_fixed_modifications(params, result_perf)`.

### Parameter Extraction (`proteobench/io/params/`)

Each tool has an `extract_params` function that reads native config files (XML for MaxQuant, `.workflow` for FragPipe, `.log.txt` for DIA-NN, YAML for AlphaPept/WOMBAT, JSON for Sage/quantms, TOML for MetaMorpheus, `.txt` for Spectronaut/PEAKS, `.xlsx` for Proline) and returns a `ProteoBenchParameters` object. These are mapped in `QuantModule.EXTRACT_PARAMS_DICT` (`modules/quant/quant_base_module.py`). `load_params_file()` calls `EXTRACT_PARAMS_DICT[input_format](...)` and then overrides `params.software_name = input_format` (so the dict key wins, e.g. `wombat.py` sets `'Wombat'` internally but the displayed name is `'WOMBAT'`). In that dict, `'Proteome Discoverer'` currently reuses `extract_params_spectronaut` (marked TODO, needs a dedicated extractor) and `'FragPipe (DIA-NN quant)'` reuses `extract_params_fragger`.

A `maxdia.py` parser exists (delegating to MaxQuant's parser) but is **not** wired into `EXTRACT_PARAMS_DICT`, so it is not currently selectable; its module-level imports also reference `maxquant` directly rather than the fully qualified path.

`ProteoBenchParameters` (`io/params/__init__.py`) is a dataclass that loads field definitions from JSON files in `io/params/json/Quant/` (default `quant_lfq_DDA_ion.json`). Each JSON key has either a `"value"` or `"placeholder"` sub-key. The class coerces the string `"None"` to `np.nan`, provides `fill_none()`, and a custom `__repr__` that hides None-valued attributes.

### Module System (`proteobench/modules/`)

Each quant benchmark module is a thin subclass of `QuantModule` that sets `module_id`, GitHub repo names, and typically a precursor column. The `MODULE_SETTINGS_DIRS` dict in `modules/constants.py` maps module IDs to their TOML config directories (10 entries; `quant_lfq_DIA_peptidoform` is deliberately absent).

`QuantModule.__init__` defaults `self.precursor_column_name = ""`. Most modules override it (e.g. `"precursor ion"` / `"peptidoform"`), but `DIAQuantIonModulediaSC` and `DIAQuantIonModulePlasma` instead set `self.precursor_name` (used in their inline benchmarking), leaving `precursor_column_name` empty.

The `MODULE_CLASSES` dict in `utils/server_io.py` maps module class-name strings to classes for programmatic instantiation, but it currently lists **only 7** modules (QExactive DDA; AIF, Astral, diaPASEF, single-cell DIA; DDA and DIA peptidoform). It does **not** include the Astral DDA, ZenoTOF, Plasma, or de novo modules; `make_submission()` raises `ValueError` for those names.

### Rescoring Module (`proteobench/modules/rescoring/`)

A placeholder for a future rescoring module. Currently a stub: `module_rescoring.py` defines only a module-level `is_implemented()` returning `False`; `__init__.py` is a docstring. No module class, `module_id`, parse settings, or `MODULE_SETTINGS_DIRS`/`MODULE_CLASSES` registration exists yet, and it is not wired into the benchmarking pipeline or web interface.

### Plotting System (`proteobench/plotting/`)

`PlotGeneratorBase` (abstract) defines four abstract methods: `plot_main_metric()`, `generate_in_depth_plots()`, `get_in_depth_plot_layout()` (column/title layout for the UI), and `get_in_depth_plot_descriptions()` (per-plot description strings). There are **three** concrete implementations:

**`LFQHYEPlotGenerator`** (HYE = Human-Yeast-Ecoli mixed-species benchmarks):
- **Main metric plot** (`plot_main_metric()`): Scatter of metric value (x) vs `nr_prec` (y), one trace per software tool. Supports `metric="Median"/"Mean"/"ROC-AUC"`, `mode="Global"/"Species-weighted"` (default `Species-weighted`), and `colorblind_mode=True` (uses marker shapes, not color alone). Selecting `Species-weighted` or `ROC-AUC` invokes `_filter_datapoints_with_metric()` to drop legacy datapoints lacking the new mode-suffixed columns. The `software_colors` dict maps **18** tools to hex colors; `software_markers` maps the same 18 tools to plotly marker symbols.
- **In-depth plots** (`generate_in_depth_plots()`):
  - `logfc`: Log2 fold-change distribution curves per species with expected-ratio vertical lines
  - `cv`: CV violin plot for Condition A and B
  - `ma_plot`: MA plot (`log2_A_vs_B` vs mean abundance) colored by species

**`LFQPYEPlotGenerator`** (PYE = Plasma-Yeast-Ecoli, for the Plasma module):
- Main metric plot (`_plot_plasma_scatterplot`) uses `QuantDatapointPYE` metrics and encodes four visual dimensions: x = absolute log2 fold-change error of spike-ins, y = number of quantified spike-in precursors, marker size = human-plasma dynamic range (min-max normalized), marker opacity = human-plasma accuracy (lower error = darker). It maintains its own 18-tool `software_colors` dict (same keys as HYE, different hex values).
- `generate_in_depth_plots()` returns `logfc`, `cv`, `ma_plot`, plus the plasma-specific `dynamic_range_plot` (human-plasma dynamic range with epsilon trend and per-species dropdown) and `missing_values_plot` (distribution of missing values). Note the dict key is `dynamic_range_plot`, not `dynamic_range`.

**`DeNovoPlotGenerator`** (de novo sequencing):
- `plot_main_metric()` scatters a peptide-level metric (x) vs an amino-acid-level metric (y), with kwargs `level` (`"precision"`/`"recall"`), `evaluation_type` (`"mass"`/`"exact"`), and `colorblind_mode`.
- In-depth plots: `ptm_overview`, `ptm_specific` (per modification), `spectrum_feature` (per feature and evaluation type), `species_overview` (per evaluation type).
- A module-level `flatten_results_column()` helper flattens the nested `results['peptide'|'aa']['mass'|'exact']['precision'|'recall'|'coverage']` structure into columns used by `plot_main_metric`. `software_colors`/`software_markers` map 7 tools (AdaNovo, Casanovo, DeepNovo, PepNet, Pi-HelixNovo, Pi-PrimeNovo, PEAKS).

### De Novo Module (`proteobench/modules/denovo/`)

Parallel hierarchy to the quant modules. `DeNovoModule` in `denovo_base.py` follows the same pattern as `QuantModule` but uses `DenovoScores` (`proteobench/score/denovoscores.py`) for scoring and `DenovoDatapoint` (`proteobench/datapoint/denovo_datapoint.py`) for datapoints. The working pipeline lives in the concrete `DDAHCDDeNovoModule` in `denovo_DDA_HCD.py` (`module_id = "denovo_DDA_HCD"`); `DeNovoModule.benchmarking()`/`filter_data_point()` are early-return stubs, and both modules' `is_implemented()` return `False` (the docstrings claiming "True" are stale). Uses `ParseSettingsDeNovo` for parsing.

De novo scoring (`DenovoScores.generate_intermediate`) compares ground-truth vs predicted peptidoforms via prefix/suffix mass matching (cum_mass_threshold = 50 Da, ind_mass_threshold = 20 Da), classifying each PSM as `match_type` in {exact, mass, mismatch} and adding columns `aa_matches_dn`/`aa_matches_gt`, `aa_exact_dn`/`aa_exact_gt`, `pep_match`. `DenovoDatapoint.results` is a nested dict `{'peptide': {'exact'|'mass': {precision, recall, coverage}}, 'aa': {...}, 'in_depth': {PTM, Spectrum, Species}}`; the flat fields `precision_peptide`/`recall_peptide`/`precision_aa`/`recall_aa` are populated from the chosen evaluation type. In-depth metrics cover PTM correctness (6 modifications), spectrum-feature breakdowns (missing fragmentation sites, peptide length, % explained intensity), and per-species match-type proportions (9 species).

The web interface uses `DeNovoUIObjects` (in `webinterface/pages/base_pages/denovo.py`) with different controls (Precision/Recall radio instead of a slider, Exact/Mass-based evaluation type). Its "Compare Results" tab actually dispatches to `display_indepth_plots`, rendering PTM overview, per-modification PTM tabs, spectrum-feature tabs, and species overview, with exact/mass toggles.

### GitHub Integration (`proteobench/github/gh.py`)

`GithubProteobotRepo` manages two repos:
- **Proteobench repo** (e.g., `Proteobench/Results_quant_ion_DDA`): Public read-only results. Cloned anonymously for reading. Each result is a separate JSON file named `{intermediate_hash}.json`.
- **Proteobot repo** (e.g., `Proteobot/Results_quant_ion_DDA`): Fork used for PRs. Authenticated clone for writing.

Submission flow: clone Proteobot repo -> create branch (with unique hash suffix) -> write JSON -> commit -> push -> create PR against Proteobot master. PRs are labeled based on `submission_source`: `"web-server"` -> `server-submission` label, `"local"` -> `local-submission` + `do-not-merge` labels with `[LOCAL - DO NOT MERGE]` prefix, `"resubmission-script"` -> `batch-resubmission` label. `is_official_server()` checks whether `"storage"` is in `st.secrets` to determine if running on the production server; `get_submission_source()` returns `"web-server"` or `"local"` accordingly.

### Web Interface (`webinterface/`)

Streamlit multi-page app. Entry point: `Home.py` (`StreamlitPageHome`, inherits from the `StreamlitPage` ABC in `_base.py`).

**Inheritance chain:**
1. `BaseStreamlitUI` (`pages/base.py`): Top-level entry point. Constructor signature is `(variables, texts, ionmodule, parsesettingsbuilder, uiobjects, page_name)`. Reads `st.secrets["gh"]["token"]`, instantiates `ionmodule(token)`, `parsesettingsbuilder`, and the UIObjects, then `main_page()` builds `st.tabs()` from `get_tab_config()` and dispatches to UIObjects methods via `getattr`. At the top of every tab it calls `_render_tab_header()` (module title, a "Go to module documentation" link button, and a warning banner) and it wires up the optional guided tour.
2. `BaseUIModule` (`pages/base_pages/base.py`): ABC with `render_plot_options_expander()` (callback-based layout for filter and selector controls in `st.columns`), five abstract tab methods (`display_all_data_results_main`, `display_submission_form`, `display_indepth_plots`, `display_all_data_results_submitted`, `display_public_submission_ui`), and a non-abstract `get_tour_steps()` hook returning `None` by default.
3. `QuantUIObjects` (`pages/base_pages/quant.py`): Concrete implementation for quant modules. Tabs 1, 3, and 4 use `@st.fragment` for partial reruns. Overrides `get_tour_steps()` to return the quant tour. Delegates to the tab module functions.
4. `DeNovoUIObjects` (`pages/base_pages/denovo.py`): Concrete implementation for de novo modules with different controls (Precision/Recall, Exact/Mass-based radios, no slider).

**Page structure:** Each module page (e.g., `pages/2_Quant_LFQ_DDA_ion_QExactive.py`) instantiates `BaseStreamlitUI` with keyword args:
1. `variables`: a `Variables*` dataclass **instance** from `pages/pages_variables/` (defines session state keys with unique prefixes, plus sidebar metadata for module registry discovery and a `texts` attribute)
2. `texts`: a `WebpageTexts` class (UI copy)
3. `ionmodule`: the backend module **class** (instantiated with the token inside `BaseStreamlitUI`)
4. `parsesettingsbuilder`: the `ParseSettingsBuilder` class
5. `uiobjects`: `QuantUIObjects` or `DeNovoUIObjects`
6. `page_name`: the sidebar label

**6 tabs per quant module** (de novo has 5, Plasma has 5):
1. View Public Results - load all datapoints, filter by slider, plot scatter, show ag-grid table, download datasets
2. Upload New Results (Private) - file upload (with AlphaDIA two-file support), software selector, keyword field, runs `ionmodule.benchmarking()`
3. View Single Result - dataset selector dropdown (uploaded + all public), in-depth plots (fold change, CV, MA), performance table, pMultiQC report generation
4. View Public + New Results - same as tab 1 but includes submitted data merged
5. Compare Two Results - click-to-select two workflows on the scatter plot, compare precursor overlap (stacked bar) and parameter differences (table)
6. Submit New Results - metadata file upload, dynamic parameter form from JSON config, comments, confirmation checkbox, PR creation via `ionmodule.clone_pr()`

For the de novo page the 5 tabs are View Public Results, Upload New Results (Private), View Public + New Results, "Compare Results" (which dispatches to `display_indepth_plots`), and Submit New Results (no dedicated "View Single Result" tab).

**Tab implementations** are in `webinterface/pages/base_pages/tabs/`:
- `tab1_view_public_results.py`: `display_existing_results()` (Tab 1 orchestrator)
- `tab2_upload_results.py`: `process_submission_form()` (file upload and benchmarking)
- `tab3_view_single_result.py`: `generate_indepth_plots()` (in-depth analysis; also `create_pmultiqc_report_section()` which runs `multiqc` via subprocess)
- `tab4_view_public_and_new_results.py`: `display_submitted_results()` (Tab 4 orchestrator)
- `tab5_compare_results.py`: `display_workflow_comparison()` (two-workflow comparison)
- `tab6_submit_results.py`: `submit_to_repository()` (PR creation workflow)

**UI utilities** in `webinterface/pages/base_pages/utils/`:
- `inputs.py`: `generate_input_widget()` (dynamic form-field factory from JSON config; 5 widget types: text_input, text_area, number_input, selectbox, checkbox). This is the only location of this factory.
- `metricplot.py`: `render_metric_plot()` (interactive Plotly scatter with click-to-select; extracts the ProteoBench ID from hovertext)
- `resulttable.py`: `render_aggrid()` (ag-grid table with column-level color coding), `configure_aggrid()` (builds gridOptions, color-coding columns by category: identifier/parameter/result/technical/additional), `prepare_display_dataframe()` (column ordering/filtering, row highlight, numeric rounding), `add_open_source_column()` (inserts the `open_source` ✅ column after `software_name` for tools in `tool_metadata.toml`), and `OPEN_SOURCE_TOOLS` (lowercase set loaded at import time via `get_open_source_tools()`)
- `general.py`: `clean_dataframe_for_export()` (CSV export cleanup)

**Banner** (`pages/base_pages/banner.py`): `display_banner(variables)` renders an archived/alpha/beta warning banner based on the module's `archived_warning`/`alpha_warning`/`beta_warning` flags using texts from `variables.texts.ShortMessages`. Invoked by `BaseStreamlitUI._render_tab_header()`.

**Texts package** (`pages/texts/`): `proteobench_builder.py` centralizes Streamlit page setup (`proteobench_page_config()`, `proteobench_sidebar()` which renders the searchable, categorized module navigation with ALPHA/BETA/ARCH badges driven by `pages/utils/module_registry.py`, and `render_links()`; it can inject analytics JS from `st.secrets["tracking"]["html_js"]`). Static UI copy lives in `generic_texts.py` (`WebpageTexts` with nested `ShortMessages` and `Help` classes), `generic_texts_dia.py`, and `generic_texts_denovo.py` (which adds a `Description` class).

**Future pages** (`pages/future_pages/`): non-active page stubs. Currently holds `6_Quant_LFQ_peptidoform_DIA_AIF.py`, a stale prototype (marked TODO-remove) referencing an obsolete StreamlitUI API and import paths that no longer exist; it is not discovered or run by the app.

**Guided tour:** an optional onboarding tour built on the third-party `streamlit_tour` library (driver.js under the hood). Step definitions live in `pages/base_pages/tour_steps.py`: `get_homepage_tour_steps()` and `get_quant_tour_steps(module_name)` (the `_tab_step()` helper targets the Nth tab button). `Home.py` shows an opt-in container and a "Take a Tour" sidebar button; `BaseStreamlitUI.main_page()` starts/finishes module tours and injects `.driver-active` pointer-events CSS so Streamlit selectbox portals remain clickable during the tour. State is tracked via session keys `_tour_opted_in`, `_home_tour_in_progress`, `_module_tour_in_progress`, `_module_tour_completed`.

**Module registry** (`pages/utils/module_registry.py`): a cached (`@st.cache_resource`) `get_all_modules()` rglobs `*_variables.py` files and builds `ModuleMetadata` (fields: `label`, `path`, `file_path`, `category`, `release_stage`, `keywords`, `title`, `doc_url`, `results_repo`). `release_stage` is derived from the `archived_warning`/`alpha_warning`/`beta_warning` flags (default `"live"`). Categories are `"DDA"`, `"DIA"`, `"Archived"`. `filter_modules()` powers sidebar search and filtering.

**Secrets** (`webinterface/.streamlit/secrets.toml`, gitignored):
- `st.secrets["gh"]["token"]` - GitHub token for PR creation
- `st.secrets["storage"]["dir"]` - Storage directory for intermediate data
- `st.secrets["tracking"]` - Matomo analytics: `matomo_endpoint`, `matomo_idsite`, `matomo_token` (checked together in `Home.py`), plus optional `html_js` for injecting analytics JS
- `st.secrets["hosting"]["information"]` - Custom hosting info

**Streamlit config** (`webinterface/.streamlit/config.toml`): Light theme, max upload 1000MB, custom sidebar navigation disabled (uses its own implementation), widget state duplication warning disabled.

Changes to `webinterface/` auto-reload; changes to `proteobench/` require a server restart.

### Session State Architecture

The webinterface uses Streamlit's `st.session_state` extensively (~328 occurrences across ~18 files). The key pattern is **UUID indirection**:
```python
# A known key stores a UUID
st.session_state[variables.slider_id_uuid] = uuid.uuid4()
# That UUID is used as the widget's key
st.select_slider(..., key=st.session_state[variables.slider_id_uuid])
# The value lives at the UUID key
value = st.session_state[st.session_state[variables.slider_id_uuid]]
```

Session state serves 4 purposes: widget state (via UUID keys), data cache (DataFrames), plot cache (Plotly figures), and flow control (submit flags, highlight lists, tour state).

### Streamlit Coupling in Core Library

Three files in `proteobench/` import Streamlit (coupling violations):
1. `modules/quant/quant_base_module.py:18` - `import streamlit as st`, uses `st.error()` in `check_new_unique_hash()` (line ~352)
2. `github/gh.py:24` - `import streamlit as st` (in try/except), uses `st.secrets` in `is_official_server()` (line ~26)
3. `modules/denovo/denovo_base.py:14` - same pattern as quant_base_module (`st.error()` at line ~280)

These would need to be decoupled for any framework migration (replace `st.error()` with exceptions, replace `st.secrets` with env vars).

## Testing

### Test Structure

Tests in `test/` use pytest. No `conftest.py` (uses defaults). ~74 `def test_` functions across 20 test files; `pytest --collect-only` reports ~186 tests after parametrization.

**Test data locations:**
- `test/data/quant/quant_lfq_ion_DDA_QExactive/` - DDA sample files (~12MB)
- `test/data/quant/quant_lfq_ion_DIA_AIF/` - DIA sample files (~9MB)
- `test/data/quant/quant_lfq_peptidoform_DDA/` - Peptidoform sample files
- `test/data/denovo/` - de novo configs and result files (~8.5MB)
- `test/data/intermediate_files/` - Reference intermediate results
- `test/params/` - Parameter files for all tools (~124 top-level files, ~130 including `test/params/denovo/`, ~9MB)
- `test/data/quant/quant_lfq_proteingroup_DIA_Astral/` exists but is currently empty; empty legacy dirs `test/data/dda_quant/` and `test/data/dia_quant/` remain.

### Test Patterns

**Parametrized tool testing:** Module tests use `@pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)` (each module test file defines its own list) to test the supported tools in one class.

**GitHub mocking:** Tests that involve GitHub use `monkeypatch.setattr` to mock `GithubProteobotRepo.clone_repo` and `read_results_json_repo`:
```python
monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", lambda *a, **kw: None)
monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.read_results_json_repo", lambda *a, **kw: pd.DataFrame())
```

**Module test classes follow this pattern:**
1. `TestSoftwareToolOutputParsing` - file loading, parse settings creation, standard format conversion
2. `TestQuantScores` - intermediate metric generation
3. `TestDDAQuantIonModule` (or `TestDIAQuantIonModule`) - full benchmarking pipeline, return types, datapoint deduplication, error handling

Only two module-level test files exist: `test_module_quant_ion_DDA_QExactive.py` and `test_module_quant_ion_DIA_AIF.py`. The Astral, diaPASEF, ZenoTOF, single-cell, Plasma, peptidoform, and de novo modules have data/params but no dedicated `test_module_*` file.

**Parameter parsing tests:** Each parser has a `test_parse_params_*.py` file (alphadia, alphapept, diann, fragger, i2masschroq, maxquant, metamorpheus, msangel, peaks, proline, quantms, sage, spectronaut, wombat) that reads native format files and compares extracted parameters against expected CSV/JSON output.

**Other test files (not module/param tests):**
- `test_quant_datapoint.py` - unit tests for `QuantDatapointHYE`/`QuantScoresHYE` (epsilon accuracy/precision metrics); the largest test file (~18 functions across `TestQuantDatapointHYE`, `TestEpsilonPrecision`, `TestQuantScoresComputeEpsilon`)
- `test_parse_settings.py` - `TestParseSettingsQuant` validates each step of `convert_to_standard_format()`
- `test_plot_quant.py` - `TestPlotDataPoint`
- `test_modules_constants.py` - parametrized check that every `MODULE_SETTINGS_DIRS` entry resolves to an existing directory
- `test_github_repo.py` - tests for `GithubProteobotRepo`

### What CI Validates

Every PR to main:
1. Black formatting check on `proteobench/`
2. Flake8 lint on 3 Python versions (3.11, 3.12, 3.13): hard-fail on E9,F63,F7,F82, plus non-blocking full and bugbear/comprehensions passes
3. Full pytest suite on 3 Python versions
4. Parameter documentation check: runs `docs/parse_tables.py` and fails if `docs/parsing_overview.tsv` has a git diff
5. Module grid check: runs `docs/generate_module_grid.py` and fails if `docs/module_grid_generated.rst` has a git diff

Separate workflow for the webinterface (`test-streamlit.yml`):
1. `check-formatting`: Black runs on `src: proteobench` (not webinterface)
2. `linting`: flake8 on `webinterface/` (`--max-complexity=10 --max-line-length=127`)

## Key Patterns for Adding/Modifying

### Adding a new software tool to an existing module

1. Create a TOML parse settings file (e.g., `parse_settings_newtool.toml`) in the instrument directory under `io/parsing/io_parse_settings/`
2. Add the filename mapping to `parse_settings_files.toml` under the relevant module section
3. Add an `extract_params` function in `io/params/newtool.py`
4. Register it in `QuantModule.EXTRACT_PARAMS_DICT` in `modules/quant/quant_base_module.py`
5. Add a color entry in the relevant plot generator's `software_colors` dict (`LFQHYEPlotGenerator`, and `LFQPYEPlotGenerator` for plasma, each maintains its own dict)
6. If the tool is open source, add its `software_name` to the `[open_source].tools` list in `io/parsing/io_parse_settings/tool_metadata.toml`
7. Add an `[upload_info]` section to the TOML with `datapoint_file`, `datapoint_file_description`, `params_file`, and `params_file_description`. If the new tool reuses an existing TOML (e.g., shares the DIA-NN report format), add an `[upload_info_overrides."New Tool Name"]` table to that TOML instead of creating a new one.
8. Add test data file to `test/data/quant/<module>/` and parameter files to `test/params/`
9. Add the tool to test parametrization in the relevant `test_module_quant_*.py`
10. Run `cd docs && python parse_tables.py` to update parameter documentation

### Adding a new benchmark module

1. Create a module class in `modules/quant/` inheriting `QuantModule`, setting `module_id`, the precursor column, and repo names
2. Add the settings directory to `MODULE_SETTINGS_DIRS` in `modules/constants.py`
3. Register the parse settings class in `MODULE_TO_CLASS` in `parse_settings.py`
4. Create TOML configs: `module_settings.toml` + per-tool parse settings in the new directory
5. Add the module class to `MODULE_CLASSES` in `utils/server_io.py` (needed for programmatic submission)
6. Create a Streamlit page in `webinterface/pages/`
7. Create a `Variables*` dataclass in `webinterface/pages/pages_variables/Quant/` — the dataclass **must** include `sidebar_label`, `sidebar_path`, `sidebar_category`, `doc_url`, `documentation_description`, and the appropriate release-stage flag (`alpha_warning`/`beta_warning`/`archived_warning`) for the documentation homepage grid to be generated correctly
8. Add module markdown files in `webinterface/pages/markdown_files/`
9. The module is auto-discovered by `module_registry.py` if the Variables dataclass has the sidebar metadata fields
10. Add a test file and test data

### Adding a new parameter JSON for submission forms

Parameter field definitions are in `proteobench/io/params/json/`. Present files: `Quant/quant_lfq_DDA_ion.json`, `Quant/quant_lfq_DDA_peptidoform.json`, `Quant/quant_lfq_DIA_ion.json`, `Quant/quant_lfq_DIA_peptidoform.json`, and `denovo/denovo_DDA_HCD.json` (there is no proteingroup JSON). Each key defines a field with `type`, `label`, `value`/`placeholder`, and optional `options`. The Variables dataclass `additional_params_json` field points to the correct JSON for each module.

## All Module Classes and Repositories

### Quant Modules (`proteobench/modules/quant/`)

| Class | module_id | precursor_col | Proteobot Repo | Implemented |
|-------|-----------|---------------|----------------|-------------|
| `DDAQuantIonModuleQExactive` | `quant_lfq_DDA_ion_QExactive` | `precursor ion` | `Results_quant_ion_DDA` | Yes |
| `DDAQuantIonAstralModule` | `quant_lfq_DDA_ion_Astral` | `precursor ion` | `Results_quant_ion_DDA_Astral` | Yes |
| `DIAQuantIonModuleAIF` | `quant_lfq_DIA_ion_AIF` | `precursor ion` | `Results_quant_ion_DIA` | No (archived) |
| `DIAQuantIonModulediaPASEF` | `quant_lfq_DIA_ion_diaPASEF` | `precursor ion` | `Results_quant_ion_DIA_diaPASEF` | No |
| `DIAQuantIonModuleAstral` | `quant_lfq_DIA_ion_Astral` | `precursor ion` | `Results_quant_ion_DIA_Astral` | No |
| `DIAQuantIonModuleZenoTOF` | `quant_lfq_DIA_ion_ZenoTOF` | `precursor ion` | `Results_quant_lfq_DIA_ion_ZenoTOF` | No |
| `DIAQuantIonModulediaSC` | `quant_lfq_DIA_ion_singlecell` | `precursor ion`* | `Results_quant_ion_DIA_singlecell` | No |
| `DIAQuantIonModulePlasma` | `quant_lfq_DIA_ion_plasma` | `precursor ion`* | `Results_quant_ion_DIA_plasma` | No |
| `DDAQuantPeptidoformModule` | `quant_lfq_DDA_peptidoform` | `peptidoform` | `Results_quant_peptidoform_DDA` | No |
| `DIAQuantPeptidoformModule` | `quant_lfq_DIA_peptidoform` | `peptidoform` | `Results_quant_peptidoform_DIA` | No (stub, raises NotImplementedError) |

*The single-cell and Plasma modules set `self.precursor_name` instead of `self.precursor_column_name`, so the documented value is the intent but `precursor_column_name` stays `""` at runtime.

### De Novo Module (`proteobench/modules/denovo/`)

| Class | module_id | Proteobot Repo |
|-------|-----------|----------------|
| `DDAHCDDeNovoModule` | `denovo_DDA_HCD` | `Results_denovo_lfq_DDA_HCD` |

De novo `EXTRACT_PARAMS_DICT` (`denovo_base.py`): AdaNovo, Casanovo, DeepNovo, InstaNovo, Pi-HelixNovo, Pi-PrimeNovo, PointNovo.

### Score, Datapoint, and Plotting Class Hierarchy

| Layer | ABC | HYE Implementation | PYE (Plasma) | De Novo |
|-------|-----|-------------------|--------------|---------|
| Score (`proteobench/score/`) | `ScoreBase` | `QuantScoresHYE` | `QuantScoresPYE` | `DenovoScores` |
| Datapoint (`proteobench/datapoint/`) | `DatapointBase` | `QuantDatapointHYE` | `QuantDatapointPYE` | `DenovoDatapoint` |
| Plotting (`proteobench/plotting/`) | `PlotGeneratorBase` | `LFQHYEPlotGenerator` | `LFQPYEPlotGenerator` | `DeNovoPlotGenerator` |

`QuantScoresPYE` is a thin pass-through over `QuantScoresHYE`; all plasma-specific metrics (spike-in fold-change error, dynamic range, human-plasma epsilon) are computed in `QuantDatapointPYE._get_plasma_metrics`. `QuantDatapointPYE` extends `QuantDatapointHYE` with `median/mean_abs_log2_fc_error_spike_ins`, `nr_quantified_spike_ins`, `dynamic_range_human_plasma`, and `median/mean_abs_epsilon_human_plasma`. The plasma metrics path defaults `max_nr_observed` to 12 when `None`; the inherited HYE thresholds still default to 6 (the `QuantDatapointPYE.generate_datapoint` docstring claiming 6 for the plasma path is a doc bug).

### Tools Supported Per Module (from `parse_settings_files.toml`)

**DDA ion (QExactive + Astral):** MaxQuant, FragPipe, DIA-NN, Sage, AlphaPept, PEAKS, ProlineStudio, MSAngel, i2MassChroQ, WOMBAT, quantms, MetaMorpheus, Custom

**DDA peptidoform:** WOMBAT, PEAKS, Proteome Discoverer, Custom

**DIA ion (AIF, diaPASEF, Astral, ZenoTOF):** DIA-NN, MaxQuant, FragPipe, FragPipe (DIA-NN quant), Spectronaut, AlphaDIA, MSAID, PEAKS, Custom

**DIA ion (single-cell):** Same as DIA + Sage

**DIA ion (Plasma):** DIA-NN, Spectronaut, FragPipe (DIA-NN quant), AlphaDIA, PEAKS, Custom

**De novo (DDA HCD):** parse_settings_files.toml lists AdaNovo, Casanovo, DeepNovo, InstaNovo, Pi-HelixNovo, Pi-PrimeNovo, PepNet. The input loaders in `parse_denovo.py:_LOAD_FUNCTIONS` are AdaNovo, Casanovo, DeepNovo, InstaNovo, PepNet, Pi-HelixNovo, Pi-PrimeNovo, Custom. Note the mismatch: `EXTRACT_PARAMS_DICT` contains `PointNovo` (which has no loader) but not `PepNet` or `Custom`; `PepNet` has a loader but no parameter extractor.

### Webinterface Pages

| File | Variables Class | Module Class | UIObjects | Entry Pattern |
|------|----------------|-------------|-----------|---------------|
| `2_Quant_LFQ_DDA_ion_QExactive.py` | `VariablesDDAQuant` | `DDAQuantIonModuleQExactive` | `QuantUIObjects` | `BaseStreamlitUI` |
| `3_Quant_LFQ_DIA_ion_AIF.py` | `VariablesDIAQuant` | `DIAQuantIonModuleAIF` | `QuantUIObjects` | `BaseStreamlitUI` |
| `4_Quant_LFQ_DIA_ion_diaPASEF.py` | `VariablesDIAQuantdiaPASEF` | `DIAQuantIonModulediaPASEF` | `QuantUIObjects` | `BaseStreamlitUI` |
| `5_Quant_LFQ_DDA_peptidoform.py` | `VariablesDDAQuant` (peptidoform) | `DDAQuantPeptidoformModule` | `QuantUIObjects` | `BaseStreamlitUI` |
| `6_Quant_LFQ_DIA_ion_Astral.py` | `VariablesDIAQuantAstral` | `DIAQuantIonModuleAstral` | `QuantUIObjects` | `BaseStreamlitUI` |
| `7_denovo_DDA_HCD.py` | `VariablesDDADeNovo` | `DDAHCDDeNovoModule` | `DeNovoUIObjects` | `BaseStreamlitUI` subclass `StreamlitUI`, overrides `get_tab_config()` for 5 tabs |
| `8_Quant_LFQ_DDA_ion_Astral.py` | `VariablesDDAQuantAstral` | `DDAQuantIonAstralModule` | `QuantUIObjects` | `BaseStreamlitUI` |
| `9_Quant_LFQ_DIA_ion_singlecell.py` | `VariablesDIAQuantSC` | `DIAQuantIonModulediaSC` | `QuantUIObjects` | `BaseStreamlitUI` |
| `10_Quant_LFQ_DIA_ion_ZenoTOF.py` | `VariablesDIAQuantZenoTOF` | `DIAQuantIonModuleZenoTOF` | `QuantUIObjects` | `BaseStreamlitUI` |
| `11_Quant_LFQ_DIA_ion_Plasma.py` | `VariablesDIAQuantPlasma` | `DIAQuantIonModulePlasma` | `QuantUIObjects` | Standalone `StreamlitUI` (not `BaseStreamlitUI`), 5 tabs, delegates to `QuantUIObjects` |

## Documentation (`docs/`)

Built with Sphinx using the `pydata_sphinx_theme`. Extensions: myst_parser (Markdown support), sphinx_design (grids), napoleon (NumPy docstrings), autodoc, intersphinx (links to Python, pandas, plotly, psims, pyteomics).

### Documentation Structure

- `docs/general-information/`: About, glossary, module lifecycle stages (proposal -> alpha -> beta -> live -> archived -> withdrawn), module proposal process, troubleshooting, contributors
- `docs/available-modules/active-modules/`: one `.md` per active module (9 files) plus `index.rst`
- `docs/available-modules/archived-modules/`: archived module docs (AIF)
- `docs/available-modules/in-development/`: directory exists but is currently empty
- `docs/available-modules/12-parsed-parameters-for-public-submission.md`: comprehensive parameter parsing documentation (source for `parse_tables.py`)
- `docs/developer-guide/`: setup, local usage, adding modules, modifying modules, reviewing PRs, repo layout, changelog
- `docs/templates_emails_module_proposal/`: email templates for expert review solicitation
- The `docs/` root also contains `README.md` and `HUPO2025SelfGuidedTour.pdf`.

### Auto-Generated Documentation

`docs/parse_tables.py` extracts parameter tables from `available-modules/12-parsed-parameters-for-public-submission.md`, combines them into a pivot table, and writes a tab-separated file named `parsing_overview.tsv` (must be run from inside `docs/`). CI validates this is up-to-date. ReadTheDocs runs `sphinx-apidoc` automatically for API docs.

`docs/generate_module_grid.py` AST-parses all `*_variables.py` files (no Streamlit import) to generate `docs/module_grid_generated.rst`, which is included by `docs/index.rst` as the homepage module card grid. CI validates this is up-to-date. Discussion-only modules (no Variables dataclass yet) are listed in `docs/module_in_discussion_grid_extra.yaml`.

## CI/CD Workflows (`.github/workflows/`)

### `python-package.yml` - Main testing
- Triggers: push to main, PRs to main
- `check-formatting`: Black ~=23.0 on `proteobench/`
- `lint-and-test` (matrix: Python 3.11, 3.12, 3.13): flake8 (hard-fail E9,F63,F7,F82; non-blocking full and B/C4 passes), pytest, parameter docs check

### `test-streamlit.yml` - Web interface
- Triggers: push to main, PRs to main
- `check-formatting`: Black on `src: proteobench` (not webinterface)
- `linting`: flake8 on `webinterface/` (`--max-complexity=10 --max-line-length=127`)

### `automated_release.yml` - Release to PyPI
- Triggers: GitHub release published
- `test-again`: pytest on Python 3.11
- `build-and-release`: builds wheel
- `publish`: publishes to PyPI via `pypa/gh-action-pypi-publish` using the `PYPI_PASSWORD` secret

## Pre-commit Hooks (`.pre-commit-config.yaml`)

16 hook IDs across 7 repos: black (24.4.2), blacken-docs (1.16.0, black==24.*), flake8 (7.1.0, `--max-line-length=127 --select=E9,F63,F7,F82`), pre-commit-hooks (v4.6.0: check-added-large-files, check-case-conflict, check-merge-conflict, check-symlinks, check-yaml, debug-statements, mixed-line-ending, name-tests-test `--pytest-test-first`, requirements-txt-fixer), validate-pyproject (v0.16), check-jsonschema (0.28.2: check-dependabot, check-github-workflows), numpydoc-validation (v1.8.0, excludes test/, exceptions.py, noxfile.py, jupyter_notebooks/, parse_tables.py). The `end-of-file-fixer` and `trailing-whitespace` hooks are intentionally commented out (too many legacy files without a trailing newline).

## Streamlit Utilities (`webinterface/streamlit_utils.py`)

- `StreamlitLogger`: context manager that captures Python logging output and displays it in a Streamlit placeholder. Supports `accumulate` (append to previous) and `persist` (keep after context exit).
- `display_error(friendly_message, exception, suggestions, technical_details)`: shows a user-friendly error with `st.error`, an optional suggestion list with `st.info`, and expandable technical details.
- `get_error_suggestions(exception, context)`: analyzes the exception type/message and a `context` dict (reads `context["input_format"]`) and returns `(friendly_message, suggestions_list)`. Handles missing runs, invalid format, parser errors, missing columns.
- `save_dataframe(df)`: cached CSV export function.
- `hide_streamlit_menu()`: injects CSS to hide the Streamlit hamburger menu.

## Homepage (`webinterface/Home.py` + `UI_utils.py`)

The homepage ("ProteoBench Overview") renders 5 stat boxes (active modules, modules in discussion/development, supported workflows/tools, submitted points, monthly visits from Matomo), a "Submissions per Module" faceted bar chart (clicking a bar opens an `@st.dialog` tool-breakdown pie chart via `_show_tool_breakdown`), and the guided tour opt-in. `UI_utils.py` provides:
- `get_n_modules()`, `get_n_modules_proposed()`, `get_n_supported_tools()`, `get_n_submitted_points()`: count statistics
- `parse_proteobench_index()`: parses `docs/index.rst`, counting modules by `:bdg-` status badge
- `get_monthly_visits(api_endpoint, token, id_site)`: fetches Matomo `nb_visits` for the last 30 days via API
- `get_module_submission_data()`: cached (1h TTL) concurrent download of each module's results-repo tarball from `api.github.com/repos/Proteobench/{repo}/tarball/main`, returning `{repo_name: {software_name: count}}`
- `build_submissions_figure()`: faceted bar chart of submission counts per module category (excludes archived modules)
- `build_tool_pie_chart()`: drill-down pie chart of tool breakdown per module
- `stat_box()` / `get_base64_image()`: render the glass stat cards and inline PNG icons

## Jupyter Notebooks (`jupyter_notebooks/`)

The `jupyter_notebooks/` directory is **gitignored and not tracked** in the repository. On a fresh checkout it contains no notebooks; any analysis notebooks, marimo scripts, or Makefiles there are local-only artifacts and should not be assumed to exist.

## Resubmission Script (`resubmit_datapoints.py`)

A ~1780-line CLI script for reprocessing previously submitted datapoints with corrections. It imports all module classes, maintains a repo->module registry, pulls GitHub PRs for parameter corrections, and processes zip archives. It reads the hash-folder data directory from the `PROTEOBENCH_DATA_DIR` environment variable. CLI flags: `--output-dir`, `--module`, `--hash` (nargs +), `--software`, `--dry-run`, `--log-file` (default `resubmit_log.txt`), `--verbose`, `--no-zip`, `--create-pr` (opens PRs on Proteobot repos with updated datapoint JSONs; requires `GITHUB_TOKEN` with push access), `--delete-failed` (removes failed datapoints' JSONs when `--create-pr` is set). Used for batch resubmission rounds when parameter parsing or scoring changes.

## Version Management

- Version is derived entirely from git tags via `setuptools_scm` (configured in `pyproject.toml`). There is no hardcoded version string to bump.
- Accessed at runtime via `importlib.metadata.version("proteobench")` in `proteobench/__init__.py`.
- Release workflow: optionally update `CHANGELOG.md`, then create a git tag / GitHub release, which triggers `automated_release.yml` to build and publish to PyPI.
- `CHANGELOG.md` (Keep a Changelog format) is titled "Changelog - pre 0.2.10"; its most recent dated entry is `[0.2.9] - 2024-05-21`. Post-0.2.9 release notes live in GitHub Releases.

## Project Metadata

- **License**: Apache 2.0
- **Authors**: Robbin Bouwmeester, Henry Webel, Witold Wolski
- **Contact**: proteobench@eubic-ms.org
- **Organization**: EuBIC-MS
- **Security** (`SECURITY.md`): report vulnerabilities via a GitHub issue or email

## Key External Resources

- **Public server for intermediate data**: `https://proteobench.cubimed.rub.de/datasets/` (`DATASETS_BASE_URL` in `server_io.py`)
- **Results repositories** (GitHub): `Proteobench/Results_quant_ion_DDA`, `Proteobench/Results_quant_ion_DDA_Astral`, `Proteobench/Results_quant_ion_DIA`, `Proteobench/Results_quant_ion_DIA_diaPASEF`, `Proteobench/Results_quant_ion_DIA_Astral`, `Proteobench/Results_quant_lfq_DIA_ion_ZenoTOF`, `Proteobench/Results_quant_ion_DIA_singlecell`, `Proteobench/Results_quant_ion_DIA_plasma`, `Proteobench/Results_quant_peptidoform_DDA`, `Proteobench/Results_denovo_lfq_DDA_HCD`
- **PR submission repositories**: same names under the `Proteobot/` organization
- **Documentation**: `https://proteobench.readthedocs.io/`
- **Web app**: `https://proteobench.cubimed.rub.de/`
- **PyPI**: `https://pypi.org/project/proteobench/`
- **BioRxiv manuscript**: linked from README and docs

## Utility Functions (`proteobench/utils/`)

- `server_io.py`: `dataset_folder_exists()` checks the public server; `get_merged_json()` downloads and merges all result JSONs from a results repo; `get_raw_data()` downloads intermediate-data ZIPs from the public server; `make_submission()` runs the full submission pipeline programmatically (using `MODULE_CLASSES`); `download_file(url, local_path, chunk_size=8192)` streams downloads.
- `submission.py`: `get_submission_dict()` builds submission metadata.
- `get_plots.py`: `make_indepth_plots()` generates plots for a given `intermediate_hash`; `get_plot_dict()` computes per-datapoint missing-value statistics; `get_missing_percentage_plot()` plots total peptide ions vs missing percentage.
