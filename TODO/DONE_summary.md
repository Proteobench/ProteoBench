# DONE Summary

Consolidated record of completed refactoring and tooling work. Text blocks are
extracted verbatim from the original TODO files where applicable; each block is
annotated with the commit SHA that landed it.

---

## 1. Parsing Pipeline Refactoring

Master plan: `TODO_parsing_structure.md`. Concrete step list:
`TODO_step_by_step_apr16.md`.

### 1.1 Extract `proforma.py` — commit `5d1c1ced`

_From `TODO_step_by_step_apr16.md` Step 1:_

> **What:** Move 7 pure functions from `parse_ion.py` to `parsing/proforma.py`.
>
> **Functions to move:**
> - `aggregate_modification_column()`
> - `aggregate_modification_sites_column()`
> - `count_chars()`
> - `get_stripped_seq()`
> - `match_brackets()`
> - `to_lowercase()`
> - `get_proforma_bracketed()`
>
> **Imports to update (1 site):**
> - `parse_settings.py` — `from .parse_ion import get_proforma_bracketed` →
>   `from .proforma import get_proforma_bracketed`
>
> **Risk:** Low. Pure functions, no state.

Commit message: "Extract proforma.py and add SampleAnnotation to ModuleSettings".

### 1.2 Extract `load_input.py` + delete dead `parse_peptidoform.py` — commit `b1964a14`

_From `TODO_step_by_step_apr16.md` Step 2:_

> **What:** Move `load_input_file()` dispatcher + all `_load_*` functions from
> `parse_ion.py` to `parsing/load_input.py`. Delete `parse_peptidoform.py`
> (dead code). Delete `parse_ion.py` (now empty).
>
> **Imports to update (5 sites + 2 notebooks):**
> - `new_parse_input.py` — `from proteobench.io.parsing.parse_ion import load_input_file`
>   → `from proteobench.io.parsing.load_input import load_input_file`
> - `quant_base_module.py:334` — same
> - `test/test_module_quant_ion_DDA_QExactive.py` — same
> - `test/test_module_quant_ion_DIA_AIF.py` — same
> - 2 jupyter notebooks (best-effort)
>
> **Risk:** Low. Move + delete dead code.

Commit message: "Rename parse_ion.py to load_input.py and delete parse_peptidoform.py".

Resolves the duplication catalog from `TODO_parsing_structure.md`:

> Total: **~320 lines** of duplicated code.
>
> Functions unique to `parse_peptidoform.py`: `_load_proteome_discoverer()`.
> Functions unique to `parse_ion.py`: 15+ tool-specific loaders (MaxQuant, Sage,
> FragPipe, DIA-NN, AlphaDIA full version, etc.)

### 1.3 Rename converter classes — commit `2553d4bc`

_From `TODO_step_by_step_apr16.md` Step 3:_

> **What:** Rename in `parse_settings.py`:
> - `ParseSettingsQuant` → `IntermediateFormatConverter`
> - `ParseModificationSettings` → `ModificationConverter`
> - `ParseSettingsBuilder` → `ConverterBuilder`

Commit message: "Rename parse_settings.py to convert_to_intermediate.py and rename classes".

Note: rename happened in place — the file was renamed `parse_settings.py` →
`convert_to_intermediate.py` but not moved into a `quant/` subpackage. The
subpackage move (step 4 / step 5 below) remains open.

### 1.4 Add `[[samples]]` and remove `[condition_mapper]` / `[run_mapper]` from per-tool TOMLs — commits `80745c3c`, `1daaa4f1`, `1b89cc9e`

_From `TODO_step_by_step_apr16.md` Step 6:_

> **What:** (Minimal step 6 — long-format tools only)
> - a. `IntermediateFormatConverter.__init__` accepts optional `condition_mapper`
>      parameter from `ModuleSettings`. Falls back to per-tool TOML if not provided.
> - b. `parse_input()` loads `ModuleSettings` and passes `condition_mapper` to
>      converter.
> - c. Remove `[condition_mapper]` and `[run_mapper]` from **34 long-format**
>      per-tool TOMLs.
> - d. Remove dead `run_mapper` from converter (never used after init).
> - Wide-format tools keep `[condition_mapper]` in TOML — they need loader
>   refactoring first (step 8).

- `80745c3c` Add `[[samples]]` table to all module_settings.toml files
- `1daaa4f1` refactor(step6-minimal): remove condition_mapper/run_mapper from 34 long-format TOMLs
- `1b89cc9e` refactor(step6-complete): remove condition_mapper/run_mapper from all remaining per-tool TOMLs

Note: commit `1b89cc9e` went beyond the minimal plan and removed the mappers
from wide-format TOMLs too. The fallback (Tier 2 resolution via `[[samples]]`)
carries the wide-format cases for now. One exception surfaced later — see
PEAKS diaPASEF fix below.

### 1.5 PEAKS diaPASEF bug fix — commit `794d25e0`

Not originally in any TODO; discovered via the marimo benchmark_analysis
regressions. From the commit:

> PEAKS wide-format columns use an `LFQ_<sample>` prefix that `_clean_run_name`
> cannot strip, so condition_mapper keys never intersected the cleaned column
> names and melt() received an empty value_vars set. The run_mapper maps each
> `LFQ_<sample>` key to its bare sample name, enabling Tier-2 resolution in
> `IntermediateFormatConverter.__init__`.
>
> Adds a regression test that synthesizes a PEAKS diaPASEF DataFrame and
> verifies both the column overlap and the full convert_to_standard_format
> path.

Restored a `[run_mapper]` section to
`io_parse_settings/Quant/lfq/DIA/ion/diaPASEF/parse_settings_peaks.toml`.
Regression test at `test/test_peaks_diapasef_regression.py`.

This is a stopgap until the wide-format loader refactor (see
`TODO_still_open.md` §2) teaches `_load_peaks()` to return bare sample names
directly.

---

## 2. Test Dataset Catalog CLI — commit `cdca2c46`

_From `TODO_creating_test_harness.md`:_

> ## Goal
>
> Assemble a reproducible test dataset: for each
> `(module, software_name, software_version)` triple across the quant modules,
> pick one representative submission and download its quantification input file
> to local disk. This dataset will later be used to drive parsing/benchmarking
> regression tests — the harness itself is out of scope for this task.
>
> ## CLI design
>
> Three subcommands, each producing or consuming a CSV.
>
> ### 1. `catalog` — build full database of available submissions
> Downloads JSON metadata only (via `get_merged_json`) for each configured module,
> writes one CSV row per submission. No raw files downloaded.
>
> ### 2. `select` — reduce to one row per (module, software, version)
> Reads a catalog CSV, groups by `(module, software_name, software_version)`,
> keeps the row with the smallest `nr_precursors`. Deterministic tiebreaker:
> lexicographic `intermediate_hash`.
>
> ### 3. `download` — fetch raw files for a database CSV
> Reads any CSV from `catalog` or `select`, downloads the corresponding input
> files via `get_raw_data` into a target directory. Idempotent: skips hashes
> already present locally.
>
> ## Deliverables
>
> - Updated `extract_raw_file_db.py` with `catalog`, `select`, `download`
>   subcommands.
> - No change to `benchmark_analysis.py`.
> - No test code yet.

All three subcommands shipped in `test_data_download/extract_raw_file_db.py`,
driven by `test_data_download/Makefile`. Output CSVs:
`raw_file_db_full.csv`, `raw_file_db_selected.csv`,
`raw_file_db_downloaded.csv`. Idempotent download verified.

Also shipped in the same commit: `test_data_download/marimo/benchmark_analysis.py`
+ `marimo/index.py` + `marimo/Makefile` for per-module HTML report generation
across all 8 quant modules.

---

## 3. Related TODOs Already Absorbed

From `TODO_parsing_structure.md` cross-references (already in `TODO/DONE/`):

> - **TODO_move_sample_annotation_to_module_settings.md** (DONE) — Steps 1-2
>   complete (committed). Steps 3-5 absorbed into implementation step 4 above.
> - **TODO_duplicated_code_in_DIA_modules.md** (DONE) — The duplication between
>   `parse_ion.py` and `parse_peptidoform.py` (~320 lines) is resolved by
>   extracting shared code to `proforma.py` and `parsing/load_input.py`.
> - **TODO_separate_parsing_benchmarking.md** (DONE) — Phases 1-4 complete.
>   Remaining Phase 5 items absorbed into `TODO_still_open.md` §1.5.
