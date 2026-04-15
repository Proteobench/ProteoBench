# Duplicated Benchmarking Code Across Module Classes

## Problem

The `benchmarking()` method is copy-pasted across 9 files with ~70 lines each (~630 lines total of near-identical code). Only 2 modules (DDA QExactive, DDA Astral) delegate to the shared `run_benchmarking()` function.

## The 9 copies

| File | Score class | Datapoint class | Precursor attr |
|------|-------------|-----------------|----------------|
| `quant_lfq_ion_DIA_AIF.py` | `QuantScoresHYE` | `QuantDatapointHYE` | `self.precursor_column_name` |
| `quant_lfq_ion_DIA_Astral.py` | `QuantScoresHYE` | `QuantDatapointHYE` | `self.precursor_column_name` |
| `quant_lfq_ion_DIA_diaPASEF.py` | `QuantScoresHYE` | `QuantDatapointHYE` | `self.precursor_column_name` |
| `quant_lfq_ion_DIA_ZenoTOF.py` | `QuantScoresHYE` | `QuantDatapointHYE` | `self.precursor_column_name` |
| `quant_lfq_ion_DIA_singlecell.py` | `QuantScoresHYE` | `QuantDatapointHYE` | `self.precursor_name` * |
| `quant_lfq_ion_DIA_Plasma.py` | `QuantScoresPYE` | `QuantDatapointPYE` | `self.precursor_name` * |
| `quant_lfq_peptidoform_DDA.py` | `QuantScoresHYE` | `QuantDatapointHYE` | `self.precursor_column_name` |
| `quant_lfq_peptidoform_DIA.py` | `QuantScoresHYE` | `QuantDatapointHYE` | `self.precursor_column_name` |
| `quant_base_module.py` | `QuantScoresHYE` | `QuantDatapointHYE` | `self.precursor_column_name` |

\* Inconsistent naming: `precursor_name` vs `precursor_column_name` — same purpose.

## The 2 modules that already delegate

| File | Delegates to |
|------|-------------|
| `quant_lfq_ion_DDA_QExactive.py` | `run_benchmarking()` |
| `quant_lfq_ion_DDA_Astral.py` | `run_benchmarking_with_timing()` |

## What differs between the copies

Almost nothing:

1. **Score class**: `QuantScoresHYE` (7 modules) vs `QuantScoresPYE` (Plasma only)
2. **Datapoint class**: `QuantDatapointHYE` (7 modules) vs `QuantDatapointPYE` (Plasma only)
3. **Precursor attribute name**: `self.precursor_column_name` (7 modules) vs `self.precursor_name` (singlecell, Plasma)
4. **Error handling**: All use identical try/except blocks with the same exception types and messages
5. **Variable naming**: `intermediate_metric_structure` (6 modules) vs `intermediate_data_structure` (singlecell, Plasma)

## Proposed fix

### Step 1: Normalize attribute naming -- DONE
- [x] Rename `self.precursor_name` → `self.precursor_column_name` in singlecell and Plasma

### Step 2: Make score/datapoint classes configurable on the base class -- DONE
Add class attributes to `QuantModule`:
```python
class QuantModule:
    quant_score_class = QuantScoresHYE
    datapoint_class = QuantDatapointHYE
```
Plasma overrides:
```python
class DIAQuantIonModulePlasma(QuantModule):
    quant_score_class = QuantScoresPYE
    datapoint_class = QuantDatapointPYE
```

### Step 3: Composition — pipeline logic stays in `benchmarking.py`, base class delegates -- PARTIALLY DONE

**Done:** Base class delegates to `run_benchmarking()` with `quant_score_class`/`datapoint_class` params. All subclass overrides deleted.

**Not done:** `run_benchmarking()` still takes `input_file, parse_settings_dir, module_id` and does parsing internally. The target signature (accepting `ParsedInput` + `ModuleSettings` directly) is Phase 3 of `TODO_separate_parsing_benchmarking.md`.

**Design principle**: The pipeline implementation lives in `benchmarking.py` (composition), not in the base class (inheritance). The base class `QuantModule.benchmarking()` is a thin delegation method — it wires up module attributes (`self.parse_settings_dir`, `self.module_id`, etc.) and passes them to `run_benchmarking()`.

Generalize `run_benchmarking()` in `benchmarking.py` to accept `ParsedInput`, `ModuleSettings`, and score/datapoint classes. This is also where `QuantScoresHYE` gets constructed — `run_benchmarking()` builds the score object from `ModuleSettings`, so modules don't need to know about `species_expected_ratio` or `species_dict` directly.

New `run_benchmarking()` signature:
```python
def run_benchmarking(
    standard_format: pd.DataFrame,       # from ParsedInput
    replicate_to_raw: dict,              # from ParsedInput
    module_settings: ModuleSettings,     # species config, from load_module_settings()
    input_format: str,
    user_input: dict,
    precursor_column_name: str,
    all_datapoints: Optional[pd.DataFrame] = None,
    default_cutoff_min_prec: int = 3,
    add_datapoint_func=None,
    max_nr_observed: int = None,
    quant_score_class=QuantScoresHYE,
    datapoint_class=QuantDatapointHYE,
) -> tuple[DataFrame, DataFrame]:
    # Species processing
    standard_format = process_species(standard_format, module_settings)

    # Score construction — uses ModuleSettings, not passed separately
    quant_score = quant_score_class(
        precursor_column_name,
        module_settings.species_expected_ratio,
        module_settings.species_dict,
    )

    # Scoring
    intermediate = quant_score.generate_intermediate(standard_format, replicate_to_raw)
    ...
```

Note: `QuantScoresHYE` stays as-is — it's the computation engine. `run_benchmarking()` constructs it from `ModuleSettings`. No need for modules to handle species config directly.

Base class delegates:
```python
class QuantModule:
    quant_score_class = QuantScoresHYE
    datapoint_class = QuantDatapointHYE

    def benchmarking(self, input_file, input_format, ...):
        parsed = parse_input(input_file, input_format, self.module_id, self.parse_settings_dir, ...)
        module_settings = load_module_settings(self.parse_settings_dir)
        return run_benchmarking(
            standard_format=parsed.standard_format,
            replicate_to_raw=parsed.replicate_to_raw,
            module_settings=module_settings,
            ...,
            quant_score_class=self.quant_score_class,
            datapoint_class=self.datapoint_class,
        )
```

Subclasses only set attributes — no `benchmarking()` override needed:
```python
class DIAQuantIonModulePlasma(QuantModule):
    quant_score_class = QuantScoresPYE
    datapoint_class = QuantDatapointPYE
```

All 8 subclass `benchmarking()` overrides are deleted.

### Step 4: Delete ~560 lines of duplicated code -- DONE
Deleted `benchmarking()` from all 10 subclass files (8 DIA/peptidoform + 2 DDA).
Also deleted `run_benchmarking_with_timing()` and `benchmarking_2()` (unused).

### Step 5: Drop `input_df` from return value -- NOT DONE

Currently `run_benchmarking()` returns `(intermediate, all_datapoints, input_df)`.
**Cannot simply remove** — webinterface uses `input_df`:
- `tab2_upload_results.py:169` stores it in `st.session_state[variables.input_df]`
- `tab6_submit_results.py:251` copies it for submission

Needs a webinterface migration plan before this can happen.

## Files to modify

- `proteobench/modules/quant/quant_base_module.py` — add class attrs, thin `benchmarking()` using `parse_input()` + `run_benchmarking()`
- `proteobench/modules/quant/benchmarking.py` — new signature: accepts `ParsedInput` fields + `ModuleSettings` + class params
- `proteobench/modules/quant/quant_lfq_ion_DDA_QExactive.py` — delete `benchmarking()` (already delegates, now base handles it)
- `proteobench/modules/quant/quant_lfq_ion_DDA_Astral.py` — delete `benchmarking()` + `benchmarking_2()`
- `proteobench/modules/quant/quant_lfq_ion_DIA_AIF.py` — delete `benchmarking()`
- `proteobench/modules/quant/quant_lfq_ion_DIA_Astral.py` — delete `benchmarking()`
- `proteobench/modules/quant/quant_lfq_ion_DIA_diaPASEF.py` — delete `benchmarking()`
- `proteobench/modules/quant/quant_lfq_ion_DIA_ZenoTOF.py` — delete `benchmarking()`
- `proteobench/modules/quant/quant_lfq_ion_DIA_singlecell.py` — rename attr, delete `benchmarking()`
- `proteobench/modules/quant/quant_lfq_ion_DIA_Plasma.py` — rename attr, set class attrs, delete `benchmarking()`
- `proteobench/modules/quant/quant_lfq_peptidoform_DDA.py` — delete `benchmarking()`
- `proteobench/modules/quant/quant_lfq_peptidoform_DIA.py` — delete `benchmarking()`
- Callers unpacking 3 return values → update to 2

## Relationship to parsing/benchmarking separation

This implements Phase 3 and Phase 4 from `TODO_separate_parsing_benchmarking.md` in one step. By collapsing all modules to delegate through the base class first, the `ParsedInput` + `ModuleSettings` signature change happens in one place (`benchmarking.py` + `quant_base_module.py`).
