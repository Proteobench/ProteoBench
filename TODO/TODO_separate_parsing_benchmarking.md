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

### Phase 3: Migrate `run_benchmarking()` to accept `ParsedInput`

- [ ] Change `run_benchmarking()` signature to accept `ParsedInput` + `ModuleSettings` instead of raw file paths, format strings, settings dirs
- [ ] Have `run_benchmarking()` call `process_species()` and read species config from `ModuleSettings`
- [ ] Remove `_load_input`, `_load_settings`, `_convert_format` helper functions from `benchmarking.py`
- [ ] Remove `input_df` from `run_benchmarking()` return value (no caller uses it)
- [ ] Update `run_benchmarking_with_timing()` similarly

### Phase 4: Migrate module classes to use `parse_input()`

- [ ] Update `QuantModule.benchmarking()` in `quant_base_module.py` to call `parse_input()` then pass result to `run_benchmarking()`
- [ ] Collapse the 6 DIA module `benchmarking()` overrides — they duplicate the same pipeline and should delegate to the base class or `run_benchmarking()`
- [ ] Update `utils/get_plots.py` to use `parse_input()`
- [ ] Update tests

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
