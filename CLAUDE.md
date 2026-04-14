# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProteoBench is a community-curated benchmarking platform for proteomics data analysis pipelines. It compares outputs from mass spectrometry tools (MaxQuant, DIA-NN, FragPipe, Spectronaut, AlphaDIA, Sage, PEAKS, MSAID, AlphaPept, i2MassChroQ, ProlineStudio, MSAngel, WOMBAT, MetaMorpheus, quantms, Proteome Discoverer) across different acquisition modes (DDA/DIA) and instrument types (QExactive, Astral, diaPASEF, AIF, ZenoTOF, single-cell).

The core library (`proteobench/`) processes tool outputs into a standardized format and computes quantification metrics. A Streamlit web app (`webinterface/`) provides the interactive UI. Benchmark results are stored as individual JSON files and submitted via GitHub pull requests to separate results repositories (e.g., `Proteobench/Results_quant_ion_DDA`).

## Common Commands

```bash
# Install for development
pip install -e '.[dev]'

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
cd docs && python parse_tables.py

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## Code Style

- **Black** formatter: line-length 120, target Python 3.11
- **isort**: profile "black"
- **flake8**: max-line-length 120 (CI enforces strict errors only: E9,F63,F7,F82)
- **numpydoc** validation on all code except `test/`, `exceptions.py`, `noxfile.py`, `jupyter_notebooks/`, `docs/parse_tables.py`
- Python >= 3.11 required; CI tests on 3.11, 3.12, 3.13

## Architecture

### Core Benchmarking Pipeline

The entry point is `run_benchmarking()` in `proteobench/modules/quant/benchmarking.py`. Module subclasses (e.g., `DDAQuantIonModuleQExactive`) delegate to it. Each step is wrapped with `@handle_benchmarking_error` which maps exceptions to the custom exception hierarchy (see `proteobench/exceptions.py`). A profiling variant `run_benchmarking_with_timing()` returns an additional `timings` dict with per-step durations.

**Pipeline steps:**

1. **Load input** (`_load_input`) - `io/parsing/parse_ion.py:load_input_file()` dispatches to format-specific loaders via `_LOAD_FUNCTIONS` dict. AlphaDIA has special handling: auto-detects matrix vs long format between two files, supports v1 (TSV) and v2 (parquet).

2. **Load settings** (`_load_settings`) - `ParseSettingsBuilder` loads the tool's TOML config and builds a `ParseSettingsQuant` parser.

3. **Convert to standard format** (`_convert_format`) - `ParseSettingsQuant.convert_to_standard_format()` runs a 10-step pipeline: validate/rename columns, create replicate mapping, filter decoys, clean run names (strip file extensions via `_clean_run_name()` regex), mark contaminants, process species (filter multi-species by `min_count_multispec`), process modifications to ProForma notation, melt wide-to-long if needed (with run name cleanup on `Raw file` column), filter zero intensities, format by analysis level (create "precursor ion" or "peptidoform" column).

4. **Score** (`_generate_intermediate`) - `QuantScoresHYE.generate_intermediate()`:
   - `compute_condition_stats()`: Groups by precursor/condition, computes log2 intensities, CV (= Intensity_std/Intensity_mean), pivots wide with columns like `log_Intensity_mean_A`, `CV_B`. Calculates `log2_A_vs_B = log_Intensity_mean_A - log_Intensity_mean_B`.
   - `compute_epsilon()`: Filters to single-species precursors (unique=1), assigns `log2_expectedRatio` per species (e.g., log2(2.0) for YEAST), computes `epsilon = log2_A_vs_B - log2_expectedRatio` (accuracy) and `epsilon_precision = log2_A_vs_B - empirical_center` (precision/reproducibility).

5. **Datapoint** (`_generate_datapoint`) - `QuantDatapointHYE.generate_datapoint()`:
   - Computes `intermediate_hash` = SHA1 of the intermediate DataFrame string representation.
   - Calls `get_metrics()` for min_nr_observed thresholds 1-6, producing a nested dict: `{threshold: {metric_name: value, ...}, ...}`.
   - Metrics include: epsilon accuracy (global + per-species + eq_species weighted), epsilon precision, CV quantiles (median/q75/q90/q95), ROC-AUC (abs-based and directional), precursor counts, variance.
   - Returns a `pd.Series` with all datapoint fields.

6. **Aggregate** (`_append_datapoint`) - Deduplication via `intermediate_hash`; duplicate submissions are rejected.

### Intermediate DataFrame Structure

After scoring, each row is one precursor/peptidoform. Key columns: precursor ion (or peptidoform), species flags (HUMAN/YEAST/ECOLI), species, log2_A_vs_B, log2_expectedRatio, epsilon, epsilon_precision_median, epsilon_precision_mean, CV_A, CV_B, log_Intensity_mean_A/B, nr_observed, plus per-raw-file intensity columns.

### Results Dictionary Structure

The `results` field in each datapoint is: `{1: {...}, 2: {...}, ..., 6: {...}}` where keys are min_nr_observed thresholds and values contain all metrics for that threshold. This allows querying performance at different stringency levels. The default display threshold is 3.

### Accuracy vs Precision Metrics

- **Accuracy (epsilon)**: `log2_A_vs_B - log2_expectedRatio` -- deviation from the known/expected species ratio. Requires ground truth.
- **Precision (epsilon_precision)**: `log2_A_vs_B - empirical_center` -- deviation from the empirical per-species center. Measures reproducibility.
- **Modes**: "global" aggregates all species as one population; "eq_species" takes mean of per-species aggregations (equal weighting regardless of count).

### Legacy Compatibility

Old datapoints have `{metric}_abs_epsilon` without mode suffix. New datapoints have both `{metric}_abs_epsilon_global` and `{metric}_abs_epsilon_eq_species`. Plotting and filtering code tries the new key first, falls back to legacy. Species-weighted mode filters out old datapoints that lack the new metrics.

### TOML-Based Parse Settings

Each software tool + module combination has a TOML file in `proteobench/io/parsing/io_parse_settings/Quant/lfq/<DDA|DIA>/<ion|peptidoform>/<instrument>/`. The master mapping is in `io_parse_settings/parse_settings_files.toml` (maps module_id sections to TOML filenames). Each directory also has a `module_settings.toml`.

**Software-specific TOML structure:**
- `[mapper]`: column renames (e.g., `"Sequence" = "Sequence"`)
- `[condition_mapper]`: raw file name -> condition ("A"/"B"). Keys are normalized at init via `_clean_run_name()` — extensions like `.mzML`, `.raw` are stripped automatically.
- `[run_mapper]`: raw file name -> display name (also normalized at init)
- `[species_mapper]`: protein ID flag -> species (e.g., `"_YEAST" = "YEAST"`)
- `[general]`: `contaminant_flag`, `decoy_flag`, and optionally `run_name_cleanup` (regex to override the default extension-stripping pattern)
- `[modifications_parser]` (optional): `parse_column`, `before_aa`, `isalpha`, `isupper`, `pattern` (regex), `modification_dict` (mass -> name)

### Run Name Cleanup (`_clean_run_name`)

File/column names from tool outputs may include extensions (`.mzML`, `.raw`, `.mzML.gz`, `.d`, `.wiff`) or tool-specific suffixes (`_uncalibrated` from FragPipe DIA-NN, see #827). The `_clean_run_name()` method on `ParseSettingsQuant` strips these using a regex so they match the `condition_mapper` keys. The default regex is:
```
(?:\.mzML\.gz|\.mzML|\.raw|\.RAW|\.d|\.wiff|_uncalibrated)$
```
It also strips path prefixes. This is applied to: column names (wide format), `Raw file` column values (long format), and `condition_mapper`/`run_mapper` keys at init time. To override per-tool, add to the TOML:
```toml
[general]
run_name_cleanup = "(?:\\.custom_suffix|\\.raw)$"
```

**Module settings TOML structure:**
- `[species_expected_ratio.<SPECIES>]`: `A_vs_B` (float ratio), `color` (hex)
- `[general]`: `min_count_multispec` (int), `level` ("ion" or "peptidoform")

The `MODULE_TO_CLASS` dict at the bottom of `parse_settings.py` routes module IDs to parser classes. Currently all modules use `ParseSettingsQuant`.

### Parameter Extraction (`proteobench/io/params/`)

Each tool has an `extract_params` function that reads native config files (XML for MaxQuant, .workflow for FragPipe, .log.txt for DIA-NN, YAML for AlphaPept/WOMBAT, JSON for Sage/quantms, TOML for MetaMorpheus, .txt for Spectronaut/PEAKS, .xlsx for Proline) and returns a `ProteoBenchParameters` object. These are mapped in `QuantModule.EXTRACT_PARAMS_DICT`.

`ProteoBenchParameters` (`io/params/__init__.py`) is a dynamic dataclass that loads field definitions from JSON files in `io/params/json/Quant/` (e.g., `quant_lfq_DDA_ion.json`). Each JSON key has either a `"value"` or `"placeholder"` sub-key.

### Module System (`proteobench/modules/`)

Each benchmark module is a thin subclass of `QuantModule` that sets `module_id`, `precursor_column_name`, and GitHub repo names. The `MODULE_SETTINGS_DIRS` dict in `modules/constants.py` maps module IDs to their TOML config directories.

Module subclasses override `benchmarking()` to call `run_benchmarking()` from `modules/quant/benchmarking.py`. They also set default `proteobot_repo_name` and `proteobench_repo_name` for their results repositories.

The `MODULE_CLASSES` dict in `utils/server_io.py` maps module class names (strings) to actual classes for programmatic module instantiation.

### Exception Hierarchy (`proteobench/exceptions.py`)

```
ProteobenchError
├── ParseError                              # Input file loading
├── ParseSettingsError                      # TOML settings loading
├── ConvertStandardFormatError              # Standard format conversion
├── IntermediateFormatGenerationError        # Scoring
├── QuantificationError                     # Quant score creation
├── DatapointGenerationError                # Datapoint creation
├── DatapointAppendError                    # Appending to collection
├── PlotError                               # Plotting
└── ValidationError                         # General validation
DatasetAlreadyExistsOnServerError           # Separate hierarchy
```

Each benchmarking step wraps its errors into the appropriate type via `@handle_benchmarking_error`.

### Plotting System (`proteobench/plotting/`)

`PlotGeneratorBase` (abstract) defines the interface. Two concrete implementations exist:

**`LFQHYEPlotGenerator`** (HYE = Human-Yeast-Ecoli mixed-species benchmarks):
- **Main metric plot** (`plot_main_metric()`): Scatter of metric value (x) vs nr_prec (y), one trace per software tool. Supports `metric="Median"/"Mean"/"ROC-AUC"`, `mode="Global"/"Species-weighted"`, and `colorblind_mode=True` (uses marker shapes instead of colors only). The `software_colors` dict maps 19 tools to hex colors; `software_markers` maps to plotly marker symbols.
- **In-depth plots** (`generate_in_depth_plots()`):
  - `logfc`: Log2 fold change distribution curves per species with expected ratio vertical lines
  - `cv`: CV violin plot for Condition A and B
  - `ma_plot`: MA plot (log2FC vs mean abundance) colored by species

**`LFQPYEPlotGenerator`** (PYE = Plasma-Yeast-Ecoli, for the Plasma module):
- Same main metric plot but uses `QuantDatapointPYE` metrics
- Additional in-depth plots: `dynamic_range` (human plasma precursors), `missing_values_plot` (distribution of missing values)

### De Novo Module (`proteobench/modules/denovo/`)

Parallel hierarchy to the quant modules. `DeNovoModule` in `denovo_base.py` follows the same pattern as `QuantModule` but uses `DenovoScores` for scoring and `DeNovoDatapoint` for datapoints. Currently one concrete module: `DDAHCDDeNovoModule` in `denovo_DDA_HCD.py` (module_id: `"denovo_DDA_HCD"`). Uses `ParseSettingsDeNovo` for parsing. The web interface uses `DeNovoUIObjects` (in `webinterface/pages/base_pages/denovo.py`) with different controls (Precision/Recall radio instead of slider, Exact/Mass-based evaluation type).

### GitHub Integration (`proteobench/github/gh.py`)

`GithubProteobotRepo` manages two repos:
- **Proteobench repo** (e.g., `Proteobench/Results_quant_ion_DDA`): Public read-only results. Cloned anonymously for reading. Each result is a separate JSON file named `{intermediate_hash}.json`.
- **Proteobot repo** (e.g., `Proteobot/Results_quant_ion_DDA`): Fork used for PRs. Authenticated clone for writing.

Submission flow: clone Proteobot repo -> create branch (with unique hash suffix) -> write JSON -> commit -> push -> create PR against Proteobot master. PRs are labeled based on `submission_source`: `"web-server"` -> `server-submission` label, `"local"` -> `local-submission` + `do-not-merge` labels with `[LOCAL - DO NOT MERGE]` prefix, `"resubmission-script"` -> `batch-resubmission` label. The `is_official_server()` function checks `st.secrets` for storage configuration to determine if running on the production server; `get_submission_source()` returns `"web-server"` or `"local"` accordingly.

### Web Interface (`webinterface/`)

Streamlit multi-page app. Entry point: `Home.py` (inherits from `StreamlitPage` ABC in `_base.py`).

**Inheritance chain:**
1. `BaseStreamlitUI` (`pages/base.py`): Top-level entry point. Reads `st.secrets["gh"]["token"]`, instantiates ionmodule and ParseSettingsBuilder, creates the UIObjects, and calls `main_page()` which dynamically creates `st.tabs()` from `get_tab_config()` and dispatches to UIObjects methods via `getattr`.
2. `BaseUIModule` (`pages/base_pages/base.py`): ABC with `render_plot_options_expander()` (callback-based layout for filter and selector controls in `st.columns`) and abstract methods for each tab.
3. `QuantUIObjects` (`pages/base_pages/quant.py`): Concrete implementation for quant modules. Tabs 1 and 4 use `@st.fragment` for partial reruns. Delegates to tab module functions.
4. `DeNovoUIObjects` (`pages/base_pages/denovo.py`): Concrete implementation for de novo modules with different controls (Precision/Recall, Exact/Mass-based radios, no slider).

**Page structure:** Each module page (e.g., `pages/2_Quant_LFQ_DDA_ion_QExactive.py`) instantiates `BaseStreamlitUI` with:
1. A `Variables*` dataclass from `pages/pages_variables/` (defines all session state keys with unique prefixes to avoid collisions, plus sidebar metadata for module registry discovery)
2. The backend module class (e.g., `DDAQuantIonModuleQExactive`) — passed as a class, instantiated with token in BaseStreamlitUI
3. `ParseSettingsBuilder` — passed as a class
4. `QuantUIObjects` or `DeNovoUIObjects` — the UI orchestrator class

**6 tabs per quant module** (de novo has 5, Plasma has 5):
1. View Public Results - load all datapoints, filter by slider, plot scatter, show ag-grid table, download datasets
2. Upload New Results (Private) - file upload (with AlphaDIA two-file support), software selector, keyword field, runs `ionmodule.benchmarking()`
3. View Single Result - dataset selector dropdown (uploaded + all public), in-depth plots (fold change, CV, MA), performance table, pMultiQC report generation
4. View Public + New Results - same as tab 1 but includes submitted data merged
5. Compare Two Results - click-to-select two workflows on scatter plot, compare precursor overlap (stacked bar) and parameter differences (table)
6. Submit New Results - metadata file upload, dynamic parameter form from JSON config, comments, confirmation checkbox, PR creation via `ionmodule.clone_pr()`

**Tab implementations** are in `webinterface/pages/base_pages/tabs/`:
- `tab1_view_public_results.py`: `display_existing_results()` — main orchestrator for Tab 1
- `tab2_upload_results.py`: `process_submission_form()` — file upload and benchmarking
- `tab3_view_single_result.py`: `generate_indepth_plots()` — in-depth analysis
- `tab4_view_public_and_new_results.py`: `display_submitted_results()` — Tab 4 orchestrator
- `tab5_compare_results.py`: `display_workflow_comparison()` — two-workflow comparison
- `tab6_submit_results.py`: `submit_to_repository()` — PR creation workflow

**UI utilities** in `webinterface/pages/base_pages/utils/`:
- `inputs.py`: `generate_input_widget()` — dynamic form field factory from JSON config (5 widget types: text_input, text_area, number_input, selectbox, checkbox)
- `metricplot.py`: `render_metric_plot()` — interactive Plotly scatter with click-to-select (extracts ProteoBench ID from hovertext)
- `resulttable.py`: `render_aggrid()` — ag-grid table with column-level color coding
- `general.py`: `clean_dataframe_for_export()` — CSV export cleanup

**Session state management:** All keys defined in `pages_variables/` dataclasses with module-specific prefixes (e.g., `"lfq_ion_dda_quant"`, `"_dia_quant"`). Categories: data DataFrames, UI element UUIDs, form parameters, metadata.

**Secrets** (`webinterface/.streamlit/secrets.toml`, gitignored):
- `st.secrets["gh"]["token"]` - GitHub token for PR creation
- `st.secrets["storage"]["dir"]` - Storage directory for intermediate data
- `st.secrets["tracking"]["matomo_endpoint"]` - Analytics
- `st.secrets["hosting"]["information"]` - Custom hosting info

**Module registry** (`pages/utils/module_registry.py`): Auto-discovers modules from `*_variables.py` files, extracts metadata (label, path, category, release stage, keywords), enables sidebar search and filtering.

**Input field generation** (`pages/base_pages/inputs.py`): Factory function `generate_input_widget()` creates Streamlit widgets (text_area, text_input, number_input, selectbox, checkbox) from JSON parameter definitions with `on_change` callbacks.

**Streamlit config** (`webinterface/.streamlit/config.toml`): Light theme, max upload 1000MB, custom sidebar navigation disabled (uses own implementation), widget state duplication warning disabled.

Changes to `webinterface/` auto-reload; changes to `proteobench/` require server restart.

### Utility Functions (`proteobench/utils/`)

- `server_io.py`: `dataset_folder_exists()` checks public server, `get_merged_json()` downloads and merges all result JSONs from a results repo, `get_raw_data()` downloads intermediate data ZIPs from public server, `make_submission()` runs full submission pipeline programmatically.
- `submission.py`: `get_submission_dict()` builds submission metadata.
- `get_plots.py`: `make_indepth_plots()` generates plots for a given intermediate_hash.

### Plasma Module (`proteobench/modules/quant/quant_lfq_ion_DIA_Plasma.py`)

The Plasma module uses different datapoint and scoring classes:
- `QuantDatapointPYE` (in `datapoint/quant_datapoint.py`): Extends `QuantDatapointHYE` with plasma-specific metrics: `median/mean_abs_log2_fc_error_spike_ins`, `nr_quantified_spike_ins`, `dynamic_range_human_plasma_A/B`, `median/mean_abs_epsilon_human_plasma`. `max_nr_observed` defaults to 12 (vs 6 for HYE).
- `LFQPYEPlotGenerator` (in `plotting/plot_generator_lfq_PYE.py`): Adds `dynamic_range` and `missing_values_plot` in-depth plots.
- The Streamlit page (`11_Quant_LFQ_DIA_ion_Plasma.py`) uses a custom `StreamlitUI` class with 5 tabs (no Compare tab).

### Session State Architecture

The webinterface uses Streamlit's `st.session_state` extensively (~257 accesses). Key pattern is **UUID indirection**:
```python
# A known key stores a UUID
st.session_state[variables.slider_id_uuid] = uuid.uuid4()
# That UUID is used as the widget's key
st.select_slider(..., key=st.session_state[variables.slider_id_uuid])
# The value lives at the UUID key
value = st.session_state[st.session_state[variables.slider_id_uuid]]
```

Session state serves 4 purposes: widget state (via UUID keys), data cache (DataFrames), plot cache (Plotly figures), and flow control (submit flags, highlight lists).

### Streamlit Coupling in Core Library

Three files in `proteobench/` import Streamlit (coupling violations):
1. `modules/quant/quant_base_module.py:18` — `import streamlit as st`, uses `st.error()` in `check_new_unique_hash()`
2. `github/gh.py:24` — `import streamlit as st` (in try/except), uses `st.secrets` in `is_official_server()`
3. `modules/denovo/denovo_base.py:14` — same pattern as quant_base_module

These would need to be decoupled for any framework migration (replace `st.error()` with exceptions, replace `st.secrets` with env vars).

## Testing

### Test Structure

Tests in `test/` use pytest. No `conftest.py` -- uses defaults. ~182 test functions across 20+ files.

**Test data locations:**
- `test/data/quant/quant_lfq_ion_DDA_QExactive/` - DDA sample files (~13MB)
- `test/data/quant/quant_lfq_ion_DIA_AIF/` - DIA sample files (~9MB)
- `test/data/quant/quant_lfq_peptidoform_DDA/` - Peptidoform sample files
- `test/params/` - Parameter files for all tools (~122 files, ~6MB)
- `test/data/intermediate_files/` - Reference intermediate results

### Test Patterns

**Parametrized tool testing:** Most module tests use `@pytest.mark.parametrize("software_tool", TESTED_SOFTWARE_TOOLS)` to test all supported tools in one class.

**GitHub mocking:** Tests that involve GitHub use `monkeypatch.setattr` to mock `GithubProteobotRepo.clone_repo` and `read_results_json_repo`:
```python
monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.clone_repo", lambda *a, **kw: None)
monkeypatch.setattr("proteobench.github.gh.GithubProteobotRepo.read_results_json_repo", lambda *a, **kw: pd.DataFrame())
```

**Module test classes follow this pattern:**
1. `TestSoftwareToolOutputParsing` - Tests file loading, parse settings creation, standard format conversion
2. `TestQuantScores` - Tests intermediate metric generation
3. `TestDDAQuantIonModule` (or DIA equivalent) - Tests full benchmarking pipeline, return types, datapoint deduplication, error handling

**Parameter parsing tests:** Each tool has its own `test_parse_params_*.py` file that reads native format files and compares extracted parameters against expected CSV/JSON output.

### What CI Validates

Every PR to main:
1. Black formatting check on `proteobench/`
2. Flake8 lint on 3 Python versions (3.11, 3.12, 3.13)
3. Full pytest suite on 3 Python versions
4. Parameter documentation check: runs `docs/parse_tables.py` and fails if `docs/parsing_overview.tsv` has a git diff

Separate workflow for webinterface:
1. Black formatting check on `webinterface/`
2. Flake8 lint on `webinterface/` (max-complexity=10, max-line-length=127)

## Key Patterns for Adding/Modifying

### Adding a new software tool to an existing module

1. Create a TOML parse settings file (e.g., `parse_settings_newtool.toml`) in the instrument directory under `io/parsing/io_parse_settings/`
2. Add the filename mapping to `parse_settings_files.toml` under the relevant module section
3. Add an `extract_params` function in `io/params/newtool.py`
4. Register it in `QuantModule.EXTRACT_PARAMS_DICT` in `modules/quant/quant_base_module.py`
5. Add a color entry in `LFQHYEPlotGenerator.plot_main_metric()` `software_colors` dict
6. Add test data file to `test/data/quant/<module>/` and parameter files to `test/params/`
7. Add the tool to test parametrization in the relevant `test_module_quant_*.py`
8. Run `cd docs && python parse_tables.py` to update parameter documentation

### Adding a new benchmark module

1. Create a module class in `modules/quant/` inheriting `QuantModule`, setting `module_id`, `precursor_column_name`, and repo names
2. Add settings directory to `MODULE_SETTINGS_DIRS` in `modules/constants.py`
3. Register the parse settings class in `MODULE_TO_CLASS` in `parse_settings.py`
4. Create TOML configs: `module_settings.toml` + per-tool parse settings in new directory
5. Add module class to `MODULE_CLASSES` in `utils/server_io.py`
6. Create a Streamlit page in `webinterface/pages/`
7. Create a `Variables*` dataclass in `webinterface/pages/pages_variables/Quant/`
8. Add module markdown files in `webinterface/pages/markdown_files/`
9. The module will be auto-discovered by `module_registry.py` if the Variables dataclass has `sidebar_label`, `sidebar_path`, and `sidebar_category` fields
10. Add test file and test data

### Adding a new parameter JSON for submission forms

Parameter field definitions are in `proteobench/io/params/json/Quant/`. Variants: `quant_lfq_DDA_ion.json`, `quant_lfq_DDA_peptidoform.json`, `quant_lfq_DIA_ion.json`, `quant_lfq_DIA_peptidoform.json`, `quant_lfq_DIA_proteingroup.json`. Each key defines a field with `type`, `label`, `value`/`placeholder`, and optional `options`. The Variables dataclass `additional_params_json` field points to the correct JSON for each module.

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
| `DIAQuantIonModulediaSC` | `quant_lfq_DIA_ion_singlecell` | `precursor ion` | `Results_quant_ion_DIA_singlecell` | No |
| `DIAQuantIonModulePlasma` | `quant_lfq_DIA_ion_plasma` | `precursor ion` | `Results_quant_ion_DIA_plasma` | No |
| `DDAQuantPeptidoformModule` | `quant_lfq_DDA_peptidoform` | `peptidoform` | `Results_quant_peptidoform_DDA` | No |
| `DIAQuantPeptidoformModule` | `quant_lfq_DIA_peptidoform` | `peptidoform` | `Results_quant_peptidoform_DIA` | No (stub) |

### De Novo Module (`proteobench/modules/denovo/`)

| Class | module_id | Proteobot Repo |
|-------|-----------|----------------|
| `DDAHCDDeNovoModule` | `denovo_DDA_HCD` | `Results_denovo_lfq_DDA_HCD` |

De novo `EXTRACT_PARAMS_DICT`: AdaNovo, Casanovo, DeepNovo, InstaNovo, Pi-HelixNovo, Pi-PrimeNovo, PointNovo.

### Score, Datapoint, and Plotting Class Hierarchy

| Layer | ABC | HYE Implementation | PYE (Plasma) | De Novo |
|-------|-----|-------------------|--------------|---------|
| Score | `ScoreBase` | `QuantScoresHYE` | `QuantScoresPYE` | `DenovoScores` |
| Datapoint | `DatapointBase` | `QuantDatapointHYE` | `QuantDatapointPYE` | `DenovoDatapoint` |
| Plotting | `PlotGeneratorBase` | `LFQHYEPlotGenerator` | `LFQPYEPlotGenerator` | `DeNovoPlotGenerator` |

### Tools Supported Per Module (from `parse_settings_files.toml`)

**DDA ion (QExactive + Astral):** MaxQuant, FragPipe, DIA-NN, Sage, AlphaPept, PEAKS, ProlineStudio, MSAngel, i2MassChroQ, WOMBAT, quantms, MetaMorpheus, Custom

**DDA peptidoform:** WOMBAT, PEAKS, Proteome Discoverer, Custom

**DIA ion (AIF, diaPASEF, Astral, ZenoTOF):** DIA-NN, MaxQuant, FragPipe, FragPipe (DIA-NN quant), Spectronaut, AlphaDIA, MSAID, PEAKS, Custom

**DIA ion (single-cell):** Same as DIA + Sage

**DIA ion (Plasma):** DIA-NN, Spectronaut, FragPipe (DIA-NN quant), AlphaDIA, PEAKS, Custom

**De novo (DDA HCD):** AdaNovo, Casanovo, DeepNovo, InstaNovo, Pi-HelixNovo, Pi-PrimeNovo, PepNet

### Webinterface Pages

| File | Variables Class | Module Class | UIObjects | Entry Pattern |
|------|----------------|-------------|-----------|---------------|
| `2_Quant_LFQ_DDA_ion_QExactive.py` | `VariablesDDAQuant` | `DDAQuantIonModuleQExactive` | `QuantUIObjects` | `BaseStreamlitUI` |
| `3_Quant_LFQ_DIA_ion_AIF.py` | `VariablesDIAQuant` | `DIAQuantIonModuleAIF` | `QuantUIObjects` | `BaseStreamlitUI` |
| `4_Quant_LFQ_DIA_ion_diaPASEF.py` | `VariablesDIAQuantdiaPASEF` | `DIAQuantIonModulediaPASEF` | `QuantUIObjects` | `BaseStreamlitUI` |
| `5_Quant_LFQ_DDA_peptidoform.py` | `VariablesDDAQuantPeptidoform` | `DDAQuantPeptidoformModule` | `QuantUIObjects` | `BaseStreamlitUI` |
| `6_Quant_LFQ_DIA_ion_Astral.py` | `VariablesDIAQuantAstral` | `DIAQuantIonModuleAstral` | `QuantUIObjects` | `BaseStreamlitUI` |
| `7_denovo_DDA_HCD.py` | `VariablesDDADeNovo` | `DDAHCDDeNovoModule` | `DeNovoUIObjects` | Custom (5 tabs) |
| `8_Quant_LFQ_DDA_ion_Astral.py` | `VariablesDDAQuantAstral` | `DDAQuantIonAstralModule` | `QuantUIObjects` | `BaseStreamlitUI` |
| `9_Quant_LFQ_DIA_ion_singlecell.py` | `VariablesDIAQuantSC` | `DIAQuantIonModulediaSC` | `QuantUIObjects` | `BaseStreamlitUI` |
| `10_Quant_LFQ_DIA_ion_ZenoTOF.py` | `VariablesDIAQuantZenoTOF` | `DIAQuantIonModuleZenoTOF` | `QuantUIObjects` | `BaseStreamlitUI` |
| `11_Quant_LFQ_DIA_ion_Plasma.py` | `VariablesDIAQuantPlasma` | `DIAQuantIonModulePlasma` | `QuantUIObjects` | Custom (5 tabs) |

## Documentation (`docs/`)

Built with Sphinx using the `pydata_sphinx_theme`. Extensions: myst_parser (Markdown support), sphinx_design (grids), napoleon (NumPy docstrings), autodoc, intersphinx (links to Python, pandas, plotly, psims, pyteomics).

### Documentation Structure

- `docs/general-information/`: About, glossary, module lifecycle stages (proposal → alpha → beta → live → archived → withdrawn), module proposal process, troubleshooting, contributors
- `docs/available-modules/active-modules/`: One `.md` per active module (10 files)
- `docs/available-modules/archived-modules/`: Archived module docs (AIF)
- `docs/available-modules/in-development/`: In-development module docs
- `docs/available-modules/12-parsed-parameters-for-public-submission.md`: Comprehensive parameter parsing documentation for all tools (source for `parse_tables.py` auto-generation)
- `docs/developer-guide/`: Setup, local usage, adding modules, modifying modules, reviewing PRs, repo layout, changelog
- `docs/templates_emails_module_proposal/`: Email templates for expert review solicitation

### Auto-Generated Documentation

`docs/parse_tables.py` extracts parameter tables from `12-parsed-parameters-for-public-submission.md`, combines them into a pivot table, and exports to `docs/parsing_overview.tsv`. CI validates this is up-to-date. ReadTheDocs runs `sphinx-apidoc` automatically for API docs.

## CI/CD Workflows (`.github/workflows/`)

### `python-package.yml` — Main testing
- Triggers: push to main, PRs to main
- `check-formatting`: Black ~=23.0 on `proteobench/`
- `lint-and-test` (matrix: Python 3.11, 3.12, 3.13): flake8 (E9,F63,F7,F82), pytest, parameter docs check

### `test-streamlit.yml` — Web interface
- Triggers: push to main, PRs to main
- `check-formatting`: Black on `webinterface/`
- `linting`: flake8 on `webinterface/` (max-complexity=10, max-line-length=127)

### `automated_release.yml` — Release to PyPI
- Triggers: GitHub release published
- `test-again`: pytest on Python 3.11
- `build-and-release`: builds wheel
- `publish`: publishes to PyPI via `pypa/gh-action-pypi-publish` using `PYPI_PASSWORD` secret

## Pre-commit Hooks (`.pre-commit-config.yaml`)

11 hooks configured: black (24.4.2), blacken-docs, flake8 (selective E9/F63/F7/F82), check-added-large-files, check-case-conflict, check-merge-conflict, check-symlinks, check-yaml, debug-statements, mixed-line-ending, name-tests-test (pytest convention), validate-pyproject, check-jsonschema (dependabot + GitHub workflows), numpydoc-validation (excludes test/, exceptions.py, noxfile.py, jupyter_notebooks/, parse_tables.py).

## Streamlit Utilities (`webinterface/streamlit_utils.py`)

- `StreamlitLogger`: Context manager that captures Python logging output and displays it in a Streamlit placeholder. Supports `accumulate` (append to previous) and `persist` (keep after context exit).
- `display_error(friendly_message, exception, suggestions, technical_details)`: Shows user-friendly error with `st.error`, optional suggestion list with `st.info`, and expandable technical details.
- `get_error_suggestions(exception, user_input)`: Analyzes exception type/message and returns context-specific friendly message + suggestions list. Handles: missing runs, invalid format, parser errors, missing columns.
- `save_dataframe(df)`: Cached CSV export function.

## Homepage (`webinterface/Home.py` + `UI_utils.py`)

The homepage displays 5 stat boxes (active modules, proposed modules, supported tools, submitted datapoints, monthly visitors from Matomo). `UI_utils.py` provides:
- `get_n_modules()`, `get_n_modules_proposed()`, `get_n_supported_tools()`, `get_n_submitted_points()`: Count statistics
- `get_monthly_visitors()`: Fetches Matomo analytics via API
- `build_submissions_figure()`: Faceted bar chart showing submission counts per module category
- `build_tool_pie_chart()`: Drill-down pie chart of tool breakdown per module

## Jupyter Notebooks (`jupyter_notebooks/`)

- `analysis/post_analysis/quant/lfq/ion/dda/`: DDA manuscript figures, in-depth module analysis, Sage plots
- `analysis/post_analysis/quant/lfq/ion/dia/`: Astral/diaPASEF manuscript figures
- `analysis/post_analysis/quant/lfq/ion/`: Marimo `benchmark_analysis.py` notebooks with Makefile for generating plots across all modules (`make all`)
- `analysis/single_submission/`: Per-submission analysis notebooks
- `analysis/methionine_excision_analysis.ipynb`: Analysis of N-terminal methionine excision across tools (#504)
- `submission/`: Batch submission, individual submission, server resubmission notebooks

## Resubmission Script (`resubmit_datapoints.py`)

~750 line CLI script for reprocessing previously submitted datapoints with corrections. Supports: dry-run, hash filtering, module filtering, software filtering, output-dir specification. Imports all module classes, pulls GitHub PRs for parameter corrections, processes zip archives. Used for batch resubmission rounds when parameter parsing or scoring changes.

## Version Management

- Version derived from git tags via `setuptools_scm` (configured in `pyproject.toml`)
- Accessed at runtime via `importlib.metadata.version("proteobench")` in `proteobench/__init__.py`
- Release workflow: update `__init__.py` version + `CHANGELOG.md`, merge to main, create GitHub release -> CI builds and publishes to PyPI
- CHANGELOG uses Keep a Changelog format, latest: v0.2.9 (2024-05-21)

## Project Metadata

- **License**: Apache 2.0
- **Authors**: Robbin Bouwmeester, Henry Webel, Witold Wolski
- **Contact**: proteobench@eubic-ms.org
- **Organization**: EuBIC-MS
- **Security**: Report vulnerabilities via GitHub issues or email

## Key External Resources

- **Public server for intermediate data**: `https://proteobench.cubimed.rub.de/datasets/` (212+ datasets)
- **Results repositories** (GitHub): `Proteobench/Results_quant_ion_DDA`, `Proteobench/Results_quant_ion_DDA_Astral`, `Proteobench/Results_quant_ion_DIA`, `Proteobench/Results_quant_ion_DIA_diaPASEF`, `Proteobench/Results_quant_ion_DIA_Astral`, `Proteobench/Results_quant_lfq_DIA_ion_ZenoTOF`, `Proteobench/Results_quant_ion_DIA_singlecell`, `Proteobench/Results_quant_ion_DIA_plasma`, `Proteobench/Results_quant_peptidoform_DDA`, `Proteobench/Results_denovo_lfq_DDA_HCD`
- **PR submission repositories**: Same names but under `Proteobot/` organization
- **Documentation**: `https://proteobench.readthedocs.io/`
- **Web app**: `https://proteobench.cubimed.rub.de/`
- **PyPI**: `https://pypi.org/project/proteobench/`
- **BioRxiv manuscript**: linked from README and docs
