# TODO: Creating Test Harness — Test Dataset Collection

## Goal

Assemble a reproducible test dataset: for each `(module, software_name, software_version)` triple across the quant modules, pick one representative submission and download its quantification input file to local disk. This dataset will later be used to drive parsing/benchmarking regression tests — the harness itself is out of scope for this task.

## Scope

- **In scope**: the 8 quant module result repos listed in `benchmark_analysis.py`'s `CONFIGS` dict:
  - `dda_qexactive`, `dda_astral`, `dda_peptidoform`, `dia_astral`, `dia_diapasef`, `dia_aif`, `dia_zenotof`, `dia_singlecell`
- **Out of scope**: de novo modules, DIA Plasma, any test-harness wiring (pytest fixtures, regression checks, CI integration).

## Constraints

- **Do not modify `benchmark_analysis.py`.** Use it as reference only for:
  - module → repo URL mapping (`CONFIGS`)
  - download helpers: `proteobench.utils.server_io.get_merged_json`, `get_raw_data`
- **Extend the existing `extract_raw_file_db.py`** into a CLI. No new script.

## CLI design

Three subcommands, each producing or consuming a CSV. Selection rule: "smallest" submission per triple, using a precursor-count field from the datapoint JSON as a proxy for input-file size (file size is not stored in the JSON).

### 1. `catalog` — build full database of available submissions


Downloads JSON metadata only (via `get_merged_json`) for each configured module, writes one CSV row per submission. No raw files downloaded.

- Args:
  - `--output <csv>` (default: `raw_file_db_full.csv`)
  - `--modules <keys...>` (optional; default: all 8)
- Columns: `module`, `repo_url`, `intermediate_hash`, `software_name`, `software_version`, `nr_precursors`, plus any other identifiers useful for later diagnostics (e.g. submission date if present).

### 2. `select` — reduce to one row per (module, software, version)

Reads a catalog CSV, groups by `(module, software_name, software_version)`, keeps the row with the smallest `nr_precursors`. Deterministic tiebreaker: lexicographic `intermediate_hash`.

- Args:
  - `--input <csv>` (catalog from step 1)
  - `--output <csv>` (default: `raw_file_db.csv`)

### 3. `download` — fetch raw files for a database CSV

Reads any CSV from `catalog` or `select`, downloads the corresponding input files via `get_raw_data` into a target directory. Idempotent: skips hashes already present locally.

- Args:
  - `--input <csv>`
  - `--output-dir <dir>`
- After download, writes/updates a CSV with `input_file_path`, `input_file_size_bytes`, `status` columns (matches current `raw_file_db.csv` schema).

## Open questions (resolve during implementation)

- **Which JSON field to use as "nr_precursors"?** Candidates in `results` dict (keyed by `min_nr_observed` threshold 1–6): `nr_prec`. Threshold choice matters — threshold 1 reflects raw precursor count, threshold 3 reflects the default display stringency. Inspect a few JSONs and pick deliberately.
- **Exclude any submissions by default?** e.g. local-submission tagged, draft/do-not-merge. Check whether such flags are present in the JSONs.

## Deliverables

- Updated `extract_raw_file_db.py` with `catalog`, `select`, `download` subcommands.
- No change to `benchmark_analysis.py`.
- No test code yet.
