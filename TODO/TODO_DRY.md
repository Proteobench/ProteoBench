# DRY Violations Report — ProteoBench

**Date:** 2026-04-14  
**Scope:** `proteobench/` core library, `webinterface/pages/`, `test/`  
**Files analyzed:** 62  
**Violations found:** 13 (High: 5 | Medium: 6 | Low: 2)

---

## High Severity

### VIO-001: ~50 near-identical test functions in test_parse_settings.py

- **Type:** Test duplication
- **Location:** `test/test_parse_settings.py` (~4800 lines)
- **Description:** Every test function follows an identical 3-step body: construct a `ParseSettingsBuilder` for one (module, software) pair, call `convert_to_standard_format()`, assert column membership and row count. The only variation is the input CSV path, the module ID string, and the software name string. File grows linearly with every new software/module combination.
- **Fix:** `@pytest.mark.parametrize` over a list of `(module_id, software_name, input_csv_path, expected_columns, expected_min_rows)` tuples. Collapses ~50 functions into 1 parametrized test + a data table (~95% reduction).

### VIO-002: 40+ structurally identical Plotly functions in quantplot.py (~9400 lines)

- **Type:** Structural duplication
- **Location:** `proteobench/plot/quant/quantplot.py` (lines 390–9430)
- **Description:** `QuantScorePlot` has 40+ methods. Scatter-trace functions follow a near-identical pattern repeated across 15+ function pairs/groups: filter df by metric column, groupby software name, loop groups appending `go.Scatter(...)` traces with identical marker/opacity/name args, `fig.update_layout(...)` with identical template/font/axis settings. At least 8 near-identical `fig.update_layout` calls.
- **Fix:** Extract `_make_scatter_traces(df, x_col, y_col, color_col)`, `_apply_standard_layout(fig, x_title, y_title)`, and `_filter_and_group(df, metric_col, min_count)` helpers. Collapse median/mean pairs into single function with `agg` parameter.

### VIO-003: 5 Streamlit page files are literally the same 24 lines

- **Type:** Literal duplication
- **Locations:**
  - `webinterface/pages/4_DDA_Quantification_ion_level.py`
  - `webinterface/pages/5_DIA_Quantification_ion_level.py`
  - `webinterface/pages/6_DDA_Quantification_peptidoform_level.py`
  - `webinterface/pages/7_DIA_Quantification_peptidoform_level.py`
  - `webinterface/pages/8_DDA_Quantification_ion_TMT.py`
- **Description:** Each file is the same 24-line script. Only difference is which module class is imported. `diff` between pages 4 and 5 shows 2 line differences in 24 total lines.
- **Fix:** Shared `_run_quant_page(module_cls)` in `base_pages/` called by each thin page file (shrink to ~5 lines each). Or a single factory page reading module ID from filename.

### VIO-004: Per-species metric blocks repeated 3x (HUMAN/YEAST/ECOLI)

- **Type:** Structural duplication
- **Location:** `proteobench/datapoint/quant_datapoint.py` (lines 400–2400)
- **Description:** The datapoint computation iterates the same statistical block (filter to species, compute median epsilon, compute median CV, count identified) three separate times with only the species name string and expected ratio changing. Species names appear as bare string literals.
- **Fix:** Define `SPECIES = ["HUMAN", "YEAST", "ECOLI"]` as module-level constant (or load from TOML). Wrap per-species block in loop. Use dict for expected ratios.

### VIO-005: 17 param extractor files with identical scaffolding

- **Type:** Structural duplication
- **Locations:** All files in `proteobench/io/params/` (alphadia.py, diann.py, sage.py, maxquant.py, fragger.py, spectronaut.py, proteome_discoverer.py, and 10 more)
- **Description:** Each extractor defines one function `extract_params_<software>(parameter_file)` with identical try/except guard pattern, logger init, and `ProteoBenchParameters(...)` construction. Parsing logic necessarily differs but structural scaffolding is pure boilerplate.
- **Fix:** Extract `_safe_get(d, key, default=None)` helper in `base_params.py`. Consider a `ParameterExtractor` base class or protocol.

---

## Medium Severity

### VIO-006: 5 module subclasses are empty pass-throughs

- **Type:** Logic duplication across classes
- **Locations:**
  - `proteobench/modules/quant/module_quant_lfq_DDA_ion.py`
  - `proteobench/modules/quant/module_quant_lfq_DIA_ion.py`
  - `proteobench/modules/quant/module_quant_lfq_DDA_peptidoform.py`
  - `proteobench/modules/quant/module_quant_lfq_DIA_peptidoform.py`
  - `proteobench/modules/quant/module_quant_lfq_DDA_ion_TMT.py`
- **Description:** Each subclass body only sets `module_id` and `precursor_column_name`. No methods overridden. May be intentional extension points.
- **Fix (if not intentional):** Factory function or `QuantModule.for_module(module_id)` class method. Or move attributes into `module_settings.toml`.

### VIO-007: 4 module test files are structurally identical (2-line diff)

- **Type:** Test duplication
- **Locations:**
  - `test/test_DDA_quant_ion_module.py`
  - `test/test_DIA_quant_ion_module.py`
  - `test/test_DDA_quant_peptidoform_module.py`
  - `test/test_DIA_quant_peptidoform_module.py`
- **Fix:** Parametrize via single `conftest.py` fixture or `@pytest.mark.parametrize`.

### VIO-008: Column name string literals scattered across 3 modules

- **Type:** Magic value duplication
- **Locations:** `proteobench/score/quant/quantscores.py`, `proteobench/datapoint/quant_datapoint.py`, `proteobench/plot/quant/quantplot.py`
- **Description:** Column names like `"log2_A_vs_B"`, `"nr_observed"`, `"epsilon"`, `"CV"`, `"precursor_ion"`, `"peptidoform"` used as bare string literals across all three. Typo risk.
- **Fix:** Create `proteobench/io/parsing/column_names.py` with a `StrEnum` or constants.

### VIO-009: `logger = logging.getLogger(__name__)` in every params file

- **Type:** Structural boilerplate
- **Note:** Idiomatic Python. No action required unless migrating to loguru/structlog.

### VIO-010: median/mean plot function pairs identical except for one aggregation string

- **Type:** Literal duplication
- **Location:** `proteobench/plot/quant/quantplot.py` (pairs throughout file)
- **Fix:** Merge each pair into single function with `agg: Literal["median", "mean"] = "median"` parameter.

### VIO-011: `benchmarking()` and `run_benchmarking()` overlap pipeline steps

- **Type:** Structural duplication
- **Location:** `proteobench/modules/quant/quant_base_module.py`
- **Fix:** Extract common pipeline skeleton into `_execute_pipeline(input_df, params)`.

---

## Low Severity

### VIO-012: `ProteoBenchParameters(field=None)` defaults repeated in every extractor

- **Fix:** Ensure all optional fields have `field(default=None)` on the dataclass itself.

### VIO-013: Module ID strings duplicated between subclass files and constants.py

- **Fix:** Import ID from `constants.py` into each subclass file for single source of truth.

---

## Recommended Priority Order

1. **VIO-001** — test parametrization (~4500 lines reducible, biggest bang for effort)
2. **VIO-002** — quantplot helpers (9400-line file, highest maintenance burden)
3. **VIO-004** — species loop (bug incubator: fix one species block, forget the other two)
4. **VIO-008** — column name constants (silent typo risk across 3 modules)
5. **VIO-003** — page factory (any UI change must be made 5 times today)
6. **VIO-007** — module test parametrization
7. **VIO-010** — median/mean pair merge
8. **VIO-005** — extractor scaffolding helpers
9. **VIO-006** — empty subclasses (discuss before acting)
10. **VIO-011** — pipeline method consolidation
11. **VIO-012** — dataclass defaults cleanup
12. **VIO-013** — module ID constant imports
