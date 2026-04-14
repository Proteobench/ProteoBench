# Dead Code Analysis: `proteobench/`

**Date:** 2026-04-14
**Scope:** `proteobench/` package (57 Python files analyzed)

---

## Definitely Unused (High Confidence -- Safe to Remove)

### 1. `proteobench/utils/get_plots.py` -- Entire file is broken & orphaned

- Imports modules that no longer exist (`quant_lfq_ion_DDA`, `plot_quant`)
- Would crash at import time
- Zero references from any other file in the project

### 2. `proteobench/io/params/maxdia.py` -- Orphaned module

- Never imported anywhere in the codebase
- Broken imports: uses `from maxquant import ...` instead of relative imports (`from .maxquant import ...`)
- Not registered in any `EXTRACT_PARAMS_DICT`

### 3. `proteobench/exceptions.py` -- `ValidationError` class (lines 23-25)

- Defined but never imported, raised, or caught anywhere

### 4. `proteobench/exceptions.py` -- `PlotError` class (lines 65-68)

- Defined but never imported, raised, or caught anywhere

### 5. `proteobench/modules/quant/benchmarking.py` -- Unused imports (lines 5-6)

- `ProcessPoolExecutor`, `as_completed` from `concurrent.futures`
- `partial` from `functools`
- Only `wraps` is actually used in this file

### 6. `proteobench/datapoint/quant_datapoint.py` -- `compute_roc_auc_directional()` (lines 166-249)

- Defined but never called anywhere in the codebase
- Only `compute_roc_auc` (without "directional") is used

### 7. `proteobench/plotting/plot_generator_denovo.py` -- `plot_species_specific()` (lines 700-701)

- Empty stub method (body is just `pass`)
- Never called by any code

---

## Probably Unused (Medium Confidence -- Remove After Verification)

### 8. `proteobench/modules/rescoring/` -- Entire package is a stub

- Contains only a single function `is_implemented()` that returns `False`
- Never imported anywhere in the project
- Placeholder for a future feature that was never built

### 9. `proteobench/modules/denovo/denovo_base.py` -- Unreachable code in `filter_data_point()` (lines 205-223)

- Bare `return` on line 205 makes all subsequent code unreachable
- Related imports `filter_df_numquant_epsilon` and `filter_df_numquant_nr_prec` (lines 17-19) are only used in the unreachable block

### 10. `proteobench/modules/denovo/denovo_base.py` -- Unreachable code in `benchmarking()` (line 254)

- Bare `return` on line 254 makes the entire method body dead code
- Actual benchmarking logic lives in the subclass `DDAHCDDeNovoModule`

### 11. `proteobench/exceptions.py` -- Duplicate exception hierarchy

- Two base classes: `ProteobenchError` (line 1, lowercase 'b') and `ProteoBenchError` (line 11, uppercase 'B')
- Two `ParseError` classes: lines 17-19 and lines 29-32; the second shadows the first
- The first `ParseError` (inheriting from `ProteoBenchError`) is effectively dead

### 12. `proteobench/utils/submission.py` -- `get_submission_dict()` never imported

- Zero references from any code in `proteobench/` or `webinterface/`
- May have been used by notebooks or external scripts at some point

### 13. `proteobench/modules/quant/quant_lfq_peptidoform_DIA.py` -- Module with missing configuration

- Uses `module_id = "quant_lfq_DIA_peptidoform"` (line 48)
- This ID is **not registered** in `MODULE_SETTINGS_DIRS` in `constants.py`
- Would fail with `KeyError` at runtime
- No active webinterface page (only in `future_pages/`)

### 14. `proteobench/datapoint/denovo_datapoint.py` -- `get_prc_curve()` (lines 45-65)

- Defined at module level but never called anywhere in the codebase

### 15. Unused imports across multiple files

- `Dict` from `typing` in `quant_lfq_ion_DDA_QExactive.py` (line 7) and `quant_lfq_ion_DDA_Astral.py` (line 7)
- `QuantificationError` in `denovo_DDA_HCD.py` (line 16)

---

## Structural Issues (Not Dead Code, But Worth Noting)

### 16. `webinterface/pages/future_pages/` -- Broken pages

- `6_Quant_LFQ_peptidoform_DIA_AIF.py` imports from paths that don't exist
- Would crash if loaded by Streamlit
- The directory name signals these are inactive, but they add confusion

### 17. `proteobench/score/quantscoresPYE.py` -- Trivial subclass

- `QuantScoresPYE` extends `QuantScoresHYE` with zero additional behavior
- `__init__` just calls `super().__init__()`, `generate_intermediate` just calls `super().generate_intermediate()`
- Used by `quant_lfq_ion_DIA_Plasma.py`, so not dead, but could be replaced with direct `QuantScoresHYE` usage

### 18. `proteobench/exceptions.py` -- Consolidation needed

- Two near-identical base exception classes (`ProteobenchError` vs `ProteoBenchError`) should be merged into one
- All subclasses should inherit from the single consolidated base

---

## Suggested Cleanup Order

1. **Remove broken/orphaned files:** `utils/get_plots.py`, `io/params/maxdia.py`
2. **Remove unused classes/functions:** `ValidationError`, `PlotError`, `compute_roc_auc_directional`, `plot_species_specific`, `get_prc_curve`
3. **Remove unused imports** in `benchmarking.py`, `quant_lfq_ion_DDA_QExactive.py`, `quant_lfq_ion_DDA_Astral.py`, `denovo_DDA_HCD.py`
4. **Clean up dead code blocks** in `denovo_base.py` (unreachable code after bare `return`)
5. **Decide on stubs:** remove `modules/rescoring/` if no plans to implement, remove or fix `quant_lfq_peptidoform_DIA.py`
6. **Consolidate exception hierarchy** in `exceptions.py`
7. **Clean up `future_pages/`** -- remove or archive broken page files
