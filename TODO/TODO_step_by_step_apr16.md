# Implementation Plan: Parsing Pipeline Restructuring (2026-04-16)

Master plan: `TODO_parsing_structure.md`

## Dependency map (from codebase analysis)

### `parse_ion.py` — imported by:
- `parse_settings.py` — `get_proforma_bracketed`
- `new_parse_input.py` — `load_input_file`
- `quant_base_module.py:334` — `load_input_file`
- `test/test_module_quant_ion_DDA_QExactive.py` — `load_input_file`
- `test/test_module_quant_ion_DIA_AIF.py` — `load_input_file`
- 2 jupyter notebooks — `load_input_file`

### `parse_settings.py` — imported by:
- `new_parse_input.py` — `ParseSettingsBuilder`
- 10 webinterface pages — `ParseSettingsBuilder`
- 2 webinterface base pages (`quant.py`, `denovo.py`) — `ParseSettingsBuilder`
- 2 denovo modules (`denovo_base.py`, `denovo_DDA_HCD.py`) — `ParseSettingsBuilder`
- `test/test_parse_settings.py` — `ParseSettingsBuilder`, `ParseSettingsQuant`
- `test/test_module_quant_ion_DDA_QExactive.py` — `ParseSettingsBuilder`
- `test/test_module_quant_ion_DIA_AIF.py` — `ParseSettingsBuilder`
- 2 jupyter notebooks — `ParseSettingsBuilder`

### `new_parse_input.py` — imported by:
- `modules/quant/benchmarking.py` — `ModuleSettings`, `process_species`
- `modules/quant/quant_base_module.py` — `load_module_settings`, `parse_input`
- `utils/get_plots.py` — `load_module_settings`, `parse_input`
- `webinterface/pages/base_pages/tabs/tab3_view_single_result.py` — `load_module_settings`
- `test/test_parse_settings.py` — `ModuleSettings`, `process_species`
- `test/test_new_parse_input.py` — all symbols
- `test/test_run_benchmarking.py` — `load_module_settings`, `parse_input`
- `test/test_module_quant_ion_DDA_QExactive.py` — `load_module_settings`, `process_species`
- `test/test_module_quant_ion_DIA_AIF.py` — `load_module_settings`, `process_species`

### `parse_peptidoform.py` — imported by: **nobody** (dead code)

### `parse_denovo.py` — imported by:
- `modules/denovo/denovo_DDA_HCD.py` — `load_input_file`
- `modules/denovo/denovo_base.py` — `load_input_file`

---

## Step 1: Extract `proforma.py`

**What:** Move 7 pure functions from `parse_ion.py` to `parsing/proforma.py`.

**Functions to move:**
- `aggregate_modification_column()`
- `aggregate_modification_sites_column()`
- `count_chars()`
- `get_stripped_seq()`
- `match_brackets()`
- `to_lowercase()`
- `get_proforma_bracketed()`

**Imports to update (1 site):**
- `parse_settings.py` — `from .parse_ion import get_proforma_bracketed` → `from .proforma import get_proforma_bracketed`

**Risk:** Low. Pure functions, no state.

---

## Step 2: Extract `load_input.py` + delete dead code

**What:** Move `load_input_file()` dispatcher + all `_load_*` functions from `parse_ion.py` to `parsing/load_input.py`. Delete `parse_peptidoform.py` (dead code). Delete `parse_ion.py` (now empty).

**Imports to update (5 sites + 2 notebooks):**
- `new_parse_input.py` — `from proteobench.io.parsing.parse_ion import load_input_file` → `from proteobench.io.parsing.load_input import load_input_file`
- `quant_base_module.py:334` — same
- `test/test_module_quant_ion_DDA_QExactive.py` — same
- `test/test_module_quant_ion_DIA_AIF.py` — same
- 2 jupyter notebooks (best-effort)

**Risk:** Low. Move + delete dead code.

---

## Step 3: Rename converter classes (in place, no file move)

**What:** Rename in `parse_settings.py`:
- `ParseSettingsQuant` → `IntermediateFormatConverter`
- `ParseModificationSettings` → `ModificationConverter`
- `ParseSettingsBuilder` → `ConverterBuilder`

Keep old names as aliases for backward compatibility:
```python
# Deprecated aliases — remove after all imports updated
ParseSettingsQuant = IntermediateFormatConverter
ParseModificationSettings = ModificationConverter
ParseSettingsBuilder = ConverterBuilder
```

**Imports to update (~18 sites):**
- 10 webinterface pages + 2 base pages — `ParseSettingsBuilder`
- 2 denovo modules — `ParseSettingsBuilder`
- 2 test files — `ParseSettingsBuilder` / `ParseSettingsQuant`
- `new_parse_input.py` — `ParseSettingsBuilder`
- 2 jupyter notebooks

comment: parse_settings.py should we not rename it to convert_to_intermediate?

**Risk:** Medium — many sites, but purely mechanical rename.

---

## Step 4: Create `quant/` subpackage

**What:** Move files into `parsing/quant/`:
- `parse_settings.py` → `quant/convert_to_intermediate.py` (minus `ParseSettingsDeNovo` + `MODULE_TO_CLASS` denovo entry)
- `new_parse_input.py` → `quant/module_settings.py`
- `load_input.py` → `quant/load_input.py`

**Imports to update:**
- All `from proteobench.io.parsing.parse_settings import ...` (~18 sites)
- All `from proteobench.io.parsing.new_parse_input import ...` (~10 sites)
- All `from proteobench.io.parsing.load_input import ...` (~5 sites, created in step 2)

**Risk:** Medium — many import updates, but mechanical. Can use re-exports at old locations during transition.

---

## Step 5: Create `psm/` subpackage

**What:**
- Move `parse_denovo.py` loaders → `psm/load_input.py`
- Move `ParseSettingsDeNovo` (now `DeNovoConverter`) → `psm/convert_to_intermediate.py`

**Imports to update (2 sites):**
- `denovo_DDA_HCD.py` — `from proteobench.io.parsing.parse_denovo import load_input_file`
- `denovo_base.py` — same

**Risk:** Low — only 2 import sites.

---

## Step 6: Remove sample annotation from long-format per-tool TOMLs

**What:** (Minimal step 6 — long-format tools only)
- a. `IntermediateFormatConverter.__init__` accepts optional `condition_mapper` parameter from `ModuleSettings`. Falls back to per-tool TOML if not provided.
- b. `parse_input()` loads `ModuleSettings` and passes `condition_mapper` to converter.
- c. Remove `[condition_mapper]` and `[run_mapper]` from **34 long-format** per-tool TOMLs.
- d. Remove dead `run_mapper` from converter (never used after init).
- Wide-format tools keep `[condition_mapper]` in TOML — they need loader refactoring first (step 8).

**Long-format tools (34 TOMLs — can remove now):**

| Tool | Modules | Key suffix | Handled by `_clean_run_name()` |
|------|---------|------------|-------------------------------|
| MaxQuant | DDA QEx, DDA Astral | bare | N/A |
| AlphaPept | DDA QEx, DDA Astral | bare | N/A |
| DIA-NN | DDA QEx, DDA Astral, all DIA | bare | N/A |
| MetaMorpheus | DDA QEx, DDA Astral | bare | N/A |
| i2MassChroQ | DDA QEx, DDA Astral | `.mzML` | Yes |
| quantms (msstats) | DDA QEx, DDA Astral | `.mzML` | Yes |
| Spectronaut | all DIA | bare | N/A |
| MaxDIA | DIA AIF, Astral, diaPASEF, ZenoTOF, singlecell | bare | N/A |
| MSAID | DIA AIF, Astral, diaPASEF, ZenoTOF, singlecell | `.raw`/`.d`/`.wiff` | Yes |

**Wide-format tools (42 TOMLs — keep for now, need loader refactoring):**

| Tool | Issue | What loader needs to do |
|------|-------|------------------------|
| FragPipe | ` Intensity` suffix on columns | Select intensity columns, melt, strip suffix |
| PEAKS | ` Normalized Area` suffix | Select area columns, melt, strip suffix |
| Sage | `.mzML` suffix on wide columns | Melt, strip extension |
| AlphaDIA | bare names (wide) | Melt |
| Custom | bare names (wide) | Melt |
| ProlineStudio/MSAngel | `abundance_` prefix | Strip prefix, melt, parse modifications |
| Proline | `abundance_` prefix + `.mgf` | Strip prefix+extension, melt |
| WOMBAT | completely different names (`abundance_A_1`) | Full custom mapping |
| Proteome Discoverer | completely different names | Full custom mapping |
| PEAKS (peptidoform) | completely different names (`Area Sample 1`) | Full custom mapping |

**Risk:** Medium — changes behavior for long-format tools only. These have simple key patterns already handled by `_clean_run_name()`.

---

## Step 7 (future): Refactor wide-format loaders

**What:** Move tool-specific data transformations into the loaders. Each wide-format loader should:
1. Load the vendor file
2. Select the relevant columns (e.g., ` Intensity` for FragPipe)
3. Melt wide-to-long format
4. Clean `Raw file` column values to bare names
5. Handle tool-specific modification parsing

After this, all loaders return standardized long-format DataFrames with bare names. The converter only does generic steps (filter decoys, mark contaminants, format by level). Then `[condition_mapper]` can be removed from all remaining wide-format TOMLs.

**Tools to refactor (by complexity):**
- Simple (melt + strip suffix): AlphaDIA, Custom, Sage, FragPipe, PEAKS
- Medium (prefix strip + melt): ProlineStudio/MSAngel, Proline
- Complex (custom mapping): WOMBAT, Proteome Discoverer, PEAKS peptidoform

This aligns with the long-term goal of loaders returning AnnData-compatible structures (obs, var, layers).

---

## Notes

- Steps 1-3 are **done** (committed).
- Steps 4-5 (quant/psm subpackages) **deferred** — high churn, low value at this point.
- Step 6 changes behavior for long-format tools only. Step 7 is the future loader refactoring.
- Each step is one commit.
