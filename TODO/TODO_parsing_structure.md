# Parsing Pipeline: Clear Module-per-Step Structure

## Problem

The parsing pipeline has three distinct steps, but the current file layout blurs the boundaries:

| Step | Responsibility | What it needs from TOML |
|------|---------------|------------------------|
| 1. Read vendor file | Load tool output into a raw DataFrame | Nothing (format-specific logic only) |
| 2. Convert to intermediate format | Rename columns, melt long-to-wide, label decoys, clean run names, process modifications | Per-tool: `[mapper]`, `[general]` (decoy_flag, contaminant_flag, run_name_cleanup), `[modifications_parser]` |
| 3. Score & benchmark | Species processing, condition stats, epsilon, datapoints | Module-level: `module_settings.toml` (species_dict, species_expected_ratio, min_count_multispec, `[[samples]]`) |

Currently `parse_ion.py` (907 lines) contains **both** step 1 (20+ `_load_*` functions) **and** step 2 helpers (`get_proforma_bracketed`, `aggregate_modification_column`, etc.). `parse_settings.py` contains step 2 orchestration (`ParseSettingsQuant.convert_to_standard_format`) **and** the builder. `parse_peptidoform.py` duplicates both step 1 loaders and step 2 helpers from `parse_ion.py`.

## Current file layout

```
proteobench/io/parsing/
    __init__.py
    parse_ion.py           # Step 1 loaders + Step 2 helpers (907 lines)
    parse_peptidoform.py   # Duplicates loaders + helpers from parse_ion.py
    parse_settings.py      # Step 2 orchestration (ParseSettingsQuant) + builder + de novo parser
    parse_denovo.py        # De novo specific loading (step 1 only)
    new_parse_input.py     # ModuleSettings, ParsedInput, parse_input() entry point
    utils.py               # MaxQuant fixed-mod helpers
    io_parse_settings/     # TOML configs (already split: Quant/ and denovo/)
```

## Current class responsibilities (the naming problem)

The "Settings" suffix is misleading. Here is what each class actually does:

| Current name | What it actually does | Better name |
|---|---|---|
| `ParseSettingsBuilder` | Reads `parse_settings_files.toml` to find the right per-tool TOML, loads it, instantiates the converter. A factory. | `ConverterFactory` or `ConverterBuilder` |
| `ParseSettingsQuant` | Holds TOML config **and** runs an 8-step conversion pipeline (`convert_to_standard_format`): rename columns, clean run names, melt wide-to-long, filter decoys, mark contaminants, process modifications, filter zeros, format by level. This is the conversion engine, not just settings. | `IntermediateFormatConverter` |
| `ParseModificationSettings` | Holds modification config from TOML **and** runs `convert_to_proforma()` on a DataFrame. Same pattern: config + transform bundled together. | `ModificationConverter` (or keep inside `IntermediateFormatConverter`) |

The pattern in all three: config loading and data transformation are coupled in one class. This is fine architecturally (the config is only used by the transform), but the names should say "converter" not "settings".

## Duplicated code between parse_ion.py and parse_peptidoform.py

Verified by diff — these are character-for-character identical in both files:

| Function | Lines | Verdict |
|---|---|---|
| `load_input_file()` | ~35 | Identical body (different `_LOAD_FUNCTIONS` dict) |
| `aggregate_modification_column()` | ~50 | Identical |
| `count_chars()` | ~25 | Identical |
| `get_stripped_seq()` | ~25 | Identical |
| `match_brackets()` | ~30 | Identical |
| `to_lowercase()` | ~15 | Identical |
| `get_proforma_bracketed()` | ~70 | Identical |
| `_load_wombat()` | ~30 | Near-identical (ion drops `"Protein Groups"` column) |
| `_load_custom()` | ~20 | Identical |
| `_load_peaks()` | ~20 | Identical |

Total: **~320 lines** of duplicated code.

Functions unique to `parse_peptidoform.py`: `_load_proteome_discoverer()`.
Functions unique to `parse_ion.py`: 15+ tool-specific loaders (MaxQuant, Sage, FragPipe, DIA-NN, AlphaDIA full version, etc.)

## Proposed layout

Organize by data type (`quant/`, `psm/`), mirroring the existing TOML config structure (`io_parse_settings/Quant/`, `io_parse_settings/denovo/`). Within each subpackage, separate step 1 (load) from step 2 (convert). Shared code (proforma helpers, common loaders) lives at the `parsing/` level.

```
proteobench/io/parsing/
    __init__.py
    io_parse_settings/              # TOML configs (unchanged, already has Quant/ and denovo/)

    # --- Shared across data types ---
    proforma.py                     # ProForma conversion helpers (pure functions):
                                    # get_proforma_bracketed(), aggregate_modification_column(),
                                    # match_brackets(), count_chars(), get_stripped_seq()
    load_input.py                   # Shared loaders used by both quant and psm:
                                    # load_input_file() dispatcher,
                                    # _load_csv(), _load_tsv(), _load_xlsx(),
                                    # _load_peaks(), _load_wombat(), _load_custom()
    utils.py                        # MaxQuant fixed-mod helpers (unchanged)

    # --- Quant: quantification data (ion + peptidoform) ---
    quant/
        __init__.py
        load_input.py               # Quant-specific loaders: _load_maxquant(), _load_diann(),
                                    # _load_alphadia(), _load_fragpipe(), _load_sage(),
                                    # _load_spectronaut(), _load_msaid(), _load_quantms(),
                                    # _load_metamorpheus(), _load_alphapept(),
                                    # _load_prolinestudio_msangel(), _load_i2masschroq(),
                                    # _load_fragpipe_diann_quant(),
                                    # _load_proteome_discoverer()
                                    # Plus quant-specific _LOAD_FUNCTIONS dict
        convert_to_intermediate.py  # IntermediateFormatConverter   (was ParseSettingsQuant)
                                    # ModificationConverter         (was ParseModificationSettings)
                                    # ConverterBuilder              (was ParseSettingsBuilder)
        module_settings.py          # ModuleSettings, SampleAnnotation, load_module_settings()
                                    # ParsedInput, parse_input(), process_species()
                                    # (renamed from new_parse_input.py once stable)

    # --- PSM: de novo / peptide-spectrum matching ---
    psm/
        __init__.py
        load_input.py               # De novo loaders: _load_adanovo(), _load_casanovo(), etc.
                                    # (extracted from parse_denovo.py)
        convert_to_intermediate.py  # DeNovoConverter (was ParseSettingsDeNovo)
                                    # Ground truth loading + feature extraction
```

### Why this structure

- **Mirrors the TOML layout**: `io_parse_settings/` already has `Quant/` and `denovo/` — the Python code follows suit.
- **Step 1 / step 2 separation per data type**: Each subpackage has `load_input.py` (step 1) and `convert_to_intermediate.py` (step 2).
- **Shared code at the parent level**: `proforma.py` and common loaders (`_load_csv`, `_load_peaks`, etc.) are shared — no duplication.
- **De novo is `psm/` not `denovo/`**: "PSM" (peptide-spectrum matching) is the general category. De novo is one approach within it. If other PSM-level analyses are added later, they fit here naturally.

## Class rename summary

| Old name | New name | File |
|---|---|---|
| `ParseSettingsQuant` | `IntermediateFormatConverter` | `quant/convert_to_intermediate.py` |
| `ParseModificationSettings` | `ModificationConverter` | `quant/convert_to_intermediate.py` |
| `ParseSettingsBuilder` | `ConverterBuilder` | `quant/convert_to_intermediate.py` |
| `ParseSettingsDeNovo` | `DeNovoConverter` | `psm/convert_to_intermediate.py` |

## Implementation order

1. **Extract `proforma.py`** -- move ProForma helpers out of `parse_ion.py`. Update imports. Run tests.
2. **Create `quant/` subpackage** -- move quant loaders into `quant/load_input.py`, shared loaders into `parsing/load_input.py`. Deduplicate with `parse_peptidoform.py`. Run tests.
3. **Move converter classes to `quant/convert_to_intermediate.py`** -- rename `ParseSettingsQuant` -> `IntermediateFormatConverter`, etc. Run tests.
4. **Remove sample annotation from per-tool TOMLs** (carried over from `TODO_move_sample_annotation_to_module_settings.md`, steps 3-5):
   - a. `IntermediateFormatConverter.__init__` accepts `condition_mapper`/`run_mapper` from `ModuleSettings` instead of reading them from per-tool TOML. Fall back to per-tool TOML during transition.
   - b. Remove `[condition_mapper]` and `[run_mapper]` from all ~77 per-tool TOMLs.
   - c. Remove `replicate_to_raw` from `ParsedInput` — it's now a property of `ModuleSettings`.
   - After this, per-tool TOMLs contain only: `[mapper]`, `[general]`, `[modifications_parser]`.
5. **Create `psm/` subpackage** -- move de novo loaders into `psm/load_input.py`, `ParseSettingsDeNovo` -> `psm/convert_to_intermediate.py` as `DeNovoConverter`. Run tests.
6. **Move `new_parse_input.py` to `quant/module_settings.py`** -- Run tests.
7. **Delete empty files** -- `parse_ion.py`, `parse_peptidoform.py`, `parse_settings.py`, `parse_denovo.py`.

Each step is a single commit. Tests must pass after each step (pure refactor, no behavior change).

## Deferred: Remove `input_df` from `benchmarking()` return value

(Carried over from `TODO_separate_parsing_benchmarking.md`, Phase 5)

`benchmarking()` returns `(intermediate, all_datapoints, input_df)`. The `input_df` is the raw vendor DataFrame — loaded a **second time** just to return it. The webinterface stores it in session state (`tab2:169`, `tab6:251-252`) but **never reads it back**. It appears to be dead code.

Action: confirm with Streamlit colleagues that `input_df` / `input_df_submission` are unused, then:
- Remove `input_df` from `benchmarking()` return (change to 2-tuple)
- Remove the duplicate `load_input_file()` call in `quant_base_module.py:334-336`
- Remove `st.session_state[variables.input_df]` writes in tab2/tab6
- Remove `input_df` / `input_df_submission` from all Variables dataclasses

## Relationship to other TODOs

- **TODO_move_sample_annotation_to_module_settings.md** (DONE) -- Steps 1-2 complete (committed). Steps 3-5 absorbed into implementation step 4 above.
- **TODO_duplicated_code_in_DIA_modules.md** (DONE) -- The duplication between `parse_ion.py` and `parse_peptidoform.py` (~320 lines) is resolved by extracting shared code to `proforma.py` and `parsing/load_input.py`.
- **TODO_separate_parsing_benchmarking.md** (DONE) -- Phases 1-4 complete. Remaining Phase 5 items absorbed here.
