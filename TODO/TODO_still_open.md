# TODO: Still Open

Consolidation of remaining work, drawn from previous TODO files. Text blocks are
extracted verbatim from the source TODOs where applicable; each section cites
its source.

---

## 1. Parsing Pipeline: Remaining Restructuring

_Sources: `TODO_parsing_structure.md`, `TODO_step_by_step_apr16.md`_

Current state of `proteobench/io/parsing/`:
```
__init__.py
convert_to_intermediate.py   # step 3 done — rename landed here, not in quant/
load_input.py                # step 2 done — moved from parse_ion.py
new_parse_input.py           # still at this path; needs to become quant/module_settings.py
parse_denovo.py              # still at top level; needs to become psm/load_input.py + psm/convert_to_intermediate.py
proforma.py                  # step 1 done
utils.py
io_parse_settings/           # TOML configs
```

### 1.1 Create `quant/` subpackage (deferred)

_From `TODO_step_by_step_apr16.md` Step 4:_

> **What:** Move files into `parsing/quant/`:
> - `parse_settings.py` → `quant/convert_to_intermediate.py` (minus
>   `ParseSettingsDeNovo` + `MODULE_TO_CLASS` denovo entry)
> - `new_parse_input.py` → `quant/module_settings.py`
> - `load_input.py` → `quant/load_input.py`
>
> **Imports to update:**
> - All `from proteobench.io.parsing.parse_settings import ...` (~18 sites)
> - All `from proteobench.io.parsing.new_parse_input import ...` (~10 sites)
> - All `from proteobench.io.parsing.load_input import ...` (~5 sites, created
>   in step 2)
>
> **Risk:** Medium — many import updates, but mechanical. Can use re-exports at
> old locations during transition.

Note in `TODO_step_by_step_apr16.md`: "Steps 4-5 (quant/psm subpackages)
**deferred** — high churn, low value at this point."

### 1.2 Create `psm/` subpackage (deferred)

_From `TODO_step_by_step_apr16.md` Step 5:_

> **What:**
> - Move `parse_denovo.py` loaders → `psm/load_input.py`
> - Move `ParseSettingsDeNovo` (now `DeNovoConverter`) →
>   `psm/convert_to_intermediate.py`
>
> **Imports to update (2 sites):**
> - `denovo_DDA_HCD.py` — `from proteobench.io.parsing.parse_denovo import load_input_file`
> - `denovo_base.py` — same
>
> **Risk:** Low — only 2 import sites.

Also pending here: rename `ParseSettingsDeNovo` → `DeNovoConverter` (not yet
done; only the quant-side names were renamed in commit `2553d4bc`).

### 1.3 Delete `parse_denovo.py` (depends on §1.2)

Listed in `TODO_parsing_structure.md` step 7: "Delete empty files —
`parse_ion.py`, `parse_peptidoform.py`, `parse_settings.py`, `parse_denovo.py`."
All except `parse_denovo.py` are gone.

### 1.4 Remove `input_df` from `benchmarking()` return value

_From `TODO_parsing_structure.md` — Deferred section:_

> `benchmarking()` returns `(intermediate, all_datapoints, input_df)`. The
> `input_df` is the raw vendor DataFrame — loaded a **second time** just to
> return it. The webinterface stores it in session state (`tab2:169`,
> `tab6:251-252`) but **never reads it back**. It appears to be dead code.
>
> Action: confirm with Streamlit colleagues that `input_df` /
> `input_df_submission` are unused, then:
> - Remove `input_df` from `benchmarking()` return (change to 2-tuple)
> - Remove the duplicate `load_input_file()` call in `quant_base_module.py:334-336`
> - Remove `st.session_state[variables.input_df]` writes in tab2/tab6
> - Remove `input_df` / `input_df_submission` from all Variables dataclasses

---

## 2. Wide-format Loader Refactoring (step 7)

_Source: `TODO_file_parsing_melt.md`_

### Problem

> 42 per-tool TOMLs still have `[condition_mapper]` and `[run_mapper]` because
> their loaders return wide-format DataFrames. The melt (wide-to-long) currently
> happens in `IntermediateFormatConverter._handle_data_format()` using
> `condition_mapper.keys()` as `value_vars`. To remove `condition_mapper` from
> these TOMLs, each loader must do its own melt and return a standardized
> long-format DataFrame with bare `Raw file` names.

**Correction to state:** commit `1b89cc9e` has since removed
`[condition_mapper]` / `[run_mapper]` from *all* per-tool TOMLs. The converter
now falls back to `[[samples]]` in `module_settings.toml` via Tier-2 resolution
in `IntermediateFormatConverter.__init__`. The PEAKS diaPASEF case
(see `DONE_summary.md` §1.5) required restoring `[run_mapper]` because the
`LFQ_` prefix defeats `_clean_run_name`. Refactoring loaders to return long
format is still the correct end state — it eliminates the Tier-2 fallback
fragility exposed by that PEAKS case.

### What each loader must do

> Each wide-format loader should:
> 1. Load the vendor file
> 2. Identify the intensity/abundance columns (tool-specific pattern)
> 3. Melt wide-to-long: one row per precursor per sample
> 4. Clean `Raw file` values to bare names (strip tool-specific prefixes/suffixes)
> 5. Handle tool-specific modification parsing (where applicable)

### Tier 1: Simple (melt + strip suffix) — 5 loaders, ~30 TOMLs

| Loader | File:Line | Tool(s) | Column pattern | What to do |
|---|---|---|---|---|
| `_load_fragpipe()` | `load_input.py:106` | FragPipe (DDA) | `<name> Intensity`, `<name> Spectral Count`, etc. | Select `* Intensity` columns, melt, strip ` Intensity` from `Raw file` |
| `_load_fragpipe_diann_quant()` | `load_input.py:473` | FragPipe DIA-NN quant | `<name> Intensity` (some modules) | Same as FragPipe where suffix present |
| `_load_peaks()` | `load_input.py:580` | PEAKS | `<name> Normalized Area` | Select `* Normalized Area` columns, melt, strip suffix. **Also handle `LFQ_` prefix seen in PEAKS diaPASEF (see regression test `test/test_peaks_diapasef_regression.py`).** |
| `_load_sage()` | `load_input.py:89` | Sage | `<name>.mzML` | Melt, strip `.mzML` (already handled by `_clean_run_name`) |
| `_load_custom()` | `load_input.py:215` | Custom | bare names | Melt to long |
| `_load_alphadia()` | `load_input.py:366` | AlphaDIA | bare names (wide path) | Already complex auto-detect; wide path needs melt |

### Tier 2: Medium (prefix + suffix stripping) — 1 loader, ~4 TOMLs

| Loader | File:Line | Tool(s) | Column pattern | What to do |
|---|---|---|---|---|
| `_load_prolinestudio_msangel()` | `load_input.py:155` | ProlineStudio, MSAngel | `abundance_<name>` or `abundance_<name>.mgf` | Strip `abundance_` prefix, strip `.mgf`, melt, modification parsing already done in loader |

### Tier 3: Hard (completely different naming) — 2 loaders, ~8 TOMLs

| Loader | File:Line | Tool(s) | Column pattern | What to do |
|---|---|---|---|---|
| `_load_wombat()` | `load_input.py:125` | WOMBAT | `abundance_A_1`, `abundance_B_2` etc. | Column names bear no resemblance to raw file names. Needs full custom mapping. May need to keep `condition_mapper` or embed sample mapping in the loader. |
| `_load_proteome_discoverer()` | `load_input.py:626` | Proteome Discoverer | `Abundances (Normalized): F1: Sample, ConditionA` | Completely tool-specific naming. Same situation as WOMBAT. |

> **Note:** PEAKS in DDA/peptidoform also has completely different naming
> (`Area Sample 1`) — same tier as WOMBAT.

### Relationship to AnnData vision

> This refactoring aligns with the long-term goal of loaders returning
> AnnData-compatible structures (obs, var, layers). Each loader is responsible
> for its own format — the converter only does generic transformations.

---

## 3. Large Files in `jupyter_notebooks/`

_Source: `TODO_test_datastes.md`_

> **Total size**: 42GB
> **Files > 1MB**: 503 files
>
> ## Issue
> The `jupyter_notebooks/` directory contains numerous large temporary and
> extracted files that should be reviewed for:
> - Cleanup (if no longer needed)
> - Addition to `.gitignore` (if regenerated during analysis)
> - External storage strategy (if needed for reference)

### Largest file categories

> #### input_file.* (Various formats: .txt, .csv, .tsv)
> - 42M `.../temp_results/Results_quant_ion_DDA/e0ab1339.../input_file.txt`
> - 42M `.../temp_results/e0ab1339.../input_file.txt`  (duplicated under `dda/`)
> - 42M `.../extracted_files/e0ab1339.../input_file.txt` (duplicated again)
> - 41M `.../temp_results/Results_quant_ion_DIA_Astral/b3425225.../input_file.csv`
> - … (many more 38–42 MB files across DDA/DIA modules)
>
> #### result_performance.csv
> - 42M `.../Results_quant_ion_DIA_Astral/2eb6eca.../result_performance.csv`
> - … (multiple 38–42 MB files)
>
> #### SVG Graphics
> - 41M `.../figures_manuscript/pair_quantifications.svg`
>
> ## Directory Structure
> - `temp_results/` — Temporary benchmark result files
> - `extracted_files/` — Extracted/unpacked benchmark files (duplicates of temp_results)
> - `figures_manuscript/` — Generated manuscript figures (includes large SVG)
>
> ## Actions Needed
> - [ ] Review purpose of temp_results and extracted_files directories
> - [ ] Determine if files are actively used or can be deleted
> - [ ] Consider adding directories to `.gitignore`
> - [ ] Review if manuscript figures need to be in version control
> - [ ] Consider external storage for reference data if needed

**Cross-reference:** the new `test_data_download/` tooling (commit `cdca2c46`)
provides a reproducible, idempotent test-dataset catalog and may supersede the
`jupyter_notebooks/.../temp_results/` duplicates entirely. Decision on whether
to deprecate `jupyter_notebooks/.../temp_results/` + `extracted_files/` is
part of this item.

---

## 4. Test Harness Wiring (beyond CSV catalog)

_Source: `TODO_creating_test_harness.md` — explicitly out of scope for the CLI task_

The CLI (catalog → select → download) is done; the actual test harness that
consumes `raw_file_db_downloaded.csv` is not. From the original TODO:

> **Out of scope**: de novo modules, DIA Plasma, any test-harness wiring
> (pytest fixtures, regression checks, CI integration).

Open items:
- pytest fixtures that load one row per `(module, software, version)` from
  `raw_file_db_downloaded.csv` and feed the input file into the corresponding
  module's benchmarking pipeline
- reference intermediate DataFrames stored alongside the input files (or a
  hash of the intermediate as the regression assertion)
- CI integration — decide whether this runs on every PR (expensive, needs
  large downloads) or on a schedule
- de novo module coverage (explicitly excluded from the CLI scope; same
  catalog design could extend to `Results_denovo_lfq_DDA_HCD`)
- DIA Plasma module coverage

### Open questions carried over

_From `TODO_creating_test_harness.md`:_

> - **Which JSON field to use as "nr_precursors"?** Candidates in `results` dict
>   (keyed by `min_nr_observed` threshold 1–6): `nr_prec`. Threshold choice
>   matters — threshold 1 reflects raw precursor count, threshold 3 reflects
>   the default display stringency. Inspect a few JSONs and pick deliberately.
> - **Exclude any submissions by default?** e.g. local-submission tagged,
>   draft/do-not-merge. Check whether such flags are present in the JSONs.
