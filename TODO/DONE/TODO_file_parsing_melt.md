# Refactor wide-format loaders to return long format

## Problem

42 per-tool TOMLs still have `[condition_mapper]` and `[run_mapper]` because their loaders return wide-format DataFrames. The melt (wide-to-long) currently happens in `IntermediateFormatConverter._handle_data_format()` using `condition_mapper.keys()` as `value_vars`. To remove `condition_mapper` from these TOMLs, each loader must do its own melt and return a standardized long-format DataFrame with bare `Raw file` names.

## What each loader must do

Each wide-format loader should:
1. Load the vendor file
2. Identify the intensity/abundance columns (tool-specific pattern)
3. Melt wide-to-long: one row per precursor per sample
4. Clean `Raw file` values to bare names (strip tool-specific prefixes/suffixes)
5. Handle tool-specific modification parsing (where applicable)

After refactoring, all loaders return long-format DataFrames with at minimum a `Raw file` column containing bare sample names. The converter no longer needs to melt or know about tool-specific column naming.

## Loaders to refactor

### Tier 1: Simple (melt + strip suffix) — 5 loaders, ~30 TOMLs

| Loader | File:Line | Tool(s) | Column pattern | What to do |
|---|---|---|---|---|
| `_load_fragpipe()` | `load_input.py:106` | FragPipe (DDA) | `<name> Intensity`, `<name> Spectral Count`, etc. | Select `* Intensity` columns, melt, strip ` Intensity` from `Raw file` |
| `_load_fragpipe_diann_quant()` | `load_input.py:473` | FragPipe DIA-NN quant | `<name> Intensity` (some modules) | Same as FragPipe where suffix present |
| `_load_peaks()` | `load_input.py:580` | PEAKS | `<name> Normalized Area` | Select `* Normalized Area` columns, melt, strip suffix |
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

**Note:** PEAKS in DDA/peptidoform also has completely different naming (`Area Sample 1`) — same tier as WOMBAT.

## Current state

- 34 long-format TOMLs already cleaned (step 6, commit pending)
- `IntermediateFormatConverter` falls back to `[[samples]]` from `module_settings.toml` when `[condition_mapper]` is absent from per-tool TOML
- Wide-format TOMLs still have `[condition_mapper]` — converter uses it for the melt

## Relationship to AnnData vision

This refactoring aligns with the long-term goal of loaders returning AnnData-compatible structures (obs, var, layers). Each loader is responsible for its own format — the converter only does generic transformations.
