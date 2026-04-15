# Separate Parsing from Benchmarking

## Goal

Cleanly separate the parsing pipeline (load file, apply settings, convert format) from the benchmarking pipeline (species processing, scoring, datapoint generation). Currently these are tangled — parsing code handles species filtering, benchmarking functions receive raw file paths and format strings, and the same 3-step parsing sequence is copy-pasted across 5+ call sites.

## New module: `proteobench/io/parsing/new_parse_input.py`

Central entry point for parsing. Contains:

- `ParsedInput` — dataclass bundling `standard_format` + `replicate_to_raw`
- `ModuleSettings` — dataclass for module-level config (species, ratios, thresholds)
- `parse_input()` — encapsulates load -> settings -> convert
- `load_module_settings()` — reads `module_settings.toml`
- `process_species()` — standalone species column creation + multi-species filtering

## Step-by-step plan

### Phase 1: Create new interfaces -- DONE (commit 9b7cbe39)

- [x] Create `new_parse_input.py` with `ParsedInput`, `parse_input()`
- [x] Add `ModuleSettings`, `load_module_settings()`, `process_species()`
- [x] Add `[species_mapper]` to all 9 `module_settings.toml` files
- [x] Mark `[species_mapper]` in 77 per-tool TOMLs with `# TODO: remove` comment

### Phase 2: Remove species processing from `ParseSettingsQuant` -- DONE

- [x] Remove `_process_species_information()` from `ParseSettingsQuant` and `convert_to_standard_format()`
- [x] Remove `_species_dict`, `min_count_multispec`, `_species_expected_ratio` from `ParseSettingsQuant.__init__`
- [x] Remove `species_dict()` and `species_expected_ratio()` accessor methods
- [x] Reorder pipeline: `_handle_data_format` moved up right after `_fix_colnames`
- [x] `convert_to_standard_format()` now returns `pd.DataFrame` (not tuple)
- [x] Renamed `_create_replicate_mapping` to public `create_replicate_mapping`
- [x] Updated all 11 callers to unpack separately + call `process_species()` + use `ModuleSettings`
- [x] Updated plot generators to accept `species_expected_ratio` directly (not via `parse_settings`)
- [x] Removed `[species_mapper]` from all 77 per-tool TOMLs
- [x] Updated all tests

### Phase 3+4: Collapse module overrides + generalize run_benchmarking -- PARTIALLY DONE

See `TODO_duplicated_code_in_DIA_modules.md` for details.

**Done:**
- [x] Collapsed all 10 `benchmarking()` overrides into base class delegation
- [x] `run_benchmarking()` accepts `quant_score_class` and `datapoint_class` parameters
- [x] Base class `QuantModule.benchmarking()` delegates to `run_benchmarking()`
- [x] Plasma uses class attribute overrides (`QuantScoresPYE`, `QuantDatapointPYE`)
- [x] Deleted `run_benchmarking_with_timing()` and `benchmarking_2()` (unused)
- [x] Added 6 direct tests for `run_benchmarking()`
- [x] Net -964 lines of duplicated code

**Not done:**
- [ ] Change `run_benchmarking()` signature to accept `ParsedInput` + `ModuleSettings` instead of raw file paths — currently still does parsing internally
- [ ] Have base class call `parse_input()` then pass result to `run_benchmarking()`
- [ ] Remove `_load_input`, `_load_settings`, `_convert_format` helpers from `benchmarking.py`
- [ ] Remove `input_df` from return value — **blocked** by webinterface dependency (`tab2:169`, `tab6:251`)
- [ ] Update `utils/get_plots.py` to use `parse_input()`

### Phase 5: Cleanup

- [ ] Rename `new_parse_input.py` to `parse_input.py`
- [ ] Remove unused imports of `load_input_file` and `ParseSettingsBuilder` from module files
- [ ] Consider moving `parse_ion.py` sequence utilities (ProForma functions) to their own module

## Architecture after completion

```
Caller (module.benchmarking / webinterface / scripts)
  |
  |-- parse_input() --> ParsedInput (standard_format + replicate_to_raw)
  |
  |-- load_module_settings() --> ModuleSettings (species, ratios, thresholds)
  |
  |-- run_benchmarking(ParsedInput, ModuleSettings, ...)
        |-- process_species()
        |-- QuantScoresHYE (uses ModuleSettings for species config)
        |-- generate_intermediate()
        |-- generate_datapoint()
        |-- append_datapoint()
```

Parsing knows nothing about species or scoring. Benchmarking knows nothing about file formats or TOML settings.
