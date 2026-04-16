# Move Sample Annotation to module_settings.toml

## Problem

`condition_mapper` and `run_mapper` are **sample annotation** (experimental design), not tool-specific parse settings. Yet they're duplicated in every per-tool TOML — identical base content with only tool-specific column name suffixes (e.g., `" Intensity"` for FragPipe, `" Normalized Area"` for PEAKS, `".raw"` for MSAID).

This is redundant: the core mapping (raw file name → sample name → condition) is the same for all tools within a module. The suffixes are already stripped by `_clean_run_name()`.

## Current state (example: DIA Astral, 8 per-tool TOMLs)

Each tool TOML repeats:

```toml
[condition_mapper]
"LFQ_Astral_DIA_15min_50ng_Condition_A_REP1" = "A"
"LFQ_Astral_DIA_15min_50ng_Condition_A_REP2" = "A"
# ... 6 entries

[run_mapper]
"LFQ_Astral_DIA_15min_50ng_Condition_A_REP1" = "Condition_A_Sample_Alpha_01"
"LFQ_Astral_DIA_15min_50ng_Condition_A_REP2" = "Condition_A_Sample_Alpha_02"
# ... 6 entries
```

Tool-specific variants only differ in suffixes on the keys:
- Most tools: `"LFQ_..._REP1"` (bare name)
- FragPipe: `"LFQ_..._REP1 Intensity"`
- PEAKS: `"LFQ_..._REP1 Normalized Area"`
- MSAID: `"LFQ_..._REP1.raw"`

These suffixes are already handled by `_clean_run_name()` regex normalization.

## Proposed structure in module_settings.toml

Replace two separate dicts with one table-like structure:

```toml
[[samples]]
raw_file = "LFQ_Astral_DIA_15min_50ng_Condition_A_REP1"
sample_name = "Condition_A_Sample_Alpha_01"
condition = "A"

[[samples]]
raw_file = "LFQ_Astral_DIA_15min_50ng_Condition_A_REP2"
sample_name = "Condition_A_Sample_Alpha_02"
condition = "A"

[[samples]]
raw_file = "LFQ_Astral_DIA_15min_50ng_Condition_A_REP3"
sample_name = "Condition_A_Sample_Alpha_03"
condition = "A"

[[samples]]
raw_file = "LFQ_Astral_DIA_15min_50ng_Condition_B_REP1"
sample_name = "Condition_B_Sample_Alpha_01"
condition = "B"

[[samples]]
raw_file = "LFQ_Astral_DIA_15min_50ng_Condition_B_REP2"
sample_name = "Condition_B_Sample_Alpha_02"
condition = "B"

[[samples]]
raw_file = "LFQ_Astral_DIA_15min_50ng_Condition_B_REP3"
sample_name = "Condition_B_Sample_Alpha_03"
condition = "B"
```

This is a single source of truth: one row per sample, three columns (raw_file, sample_name, condition). The old `condition_mapper` and `run_mapper` are derived from it.

## Implementation steps

### Step 1: Add `[[samples]]` to module_settings.toml files

Add the table to all 9 module_settings.toml files. Keep `condition_mapper` and `run_mapper` in per-tool TOMLs for backward compatibility during transition.

### Step 2: Load sample annotation in `load_module_settings()`

Extend `ModuleSettings` dataclass:

```python
@dataclass
class SampleAnnotation:
    raw_file: str
    sample_name: str
    condition: str


@dataclass
class ModuleSettings:
    species_dict: Dict[str, str]
    species_expected_ratio: Dict[str, Any]
    min_count_multispec: int
    analysis_level: str
    samples: List[SampleAnnotation]

    @property
    def condition_mapper(self) -> Dict[str, str]:
        return {s.raw_file: s.condition for s in self.samples}

    @property
    def run_mapper(self) -> Dict[str, str]:
        return {s.raw_file: s.sample_name for s in self.samples}

    @property
    def replicate_to_raw(self) -> Dict[str, List[str]]:
        result = defaultdict(list)
        for s in self.samples:
            result[s.condition].append(s.raw_file)
        return dict(result)
```

### Step 3: Update `ParseSettingsQuant` to accept sample annotation

`ParseSettingsQuant.__init__` currently reads `condition_mapper` and `run_mapper` from the per-tool TOML. Change it to accept them as parameters (from `ModuleSettings`), falling back to the per-tool TOML if not provided.

### Step 4: Remove `condition_mapper` and `run_mapper` from per-tool TOMLs

Once all code reads from module_settings, delete from all ~77 per-tool TOMLs.

### Step 5: Remove `replicate_to_raw` from `ParsedInput`

`replicate_to_raw` is now a property of `ModuleSettings`. `ParsedInput` only contains the parsed DataFrame.

## Impact on wide-format handling

For wide-format tools, `_handle_data_format()` uses `condition_mapper.keys()` as `value_vars` for the melt. After cleanup, the column names in the DataFrame still have tool-specific suffixes. The `_clean_run_name()` normalization already handles this — it's applied to column names via `_fix_colnames()` before `_handle_data_format()` runs.

So the cleaned `condition_mapper` keys (from module_settings, without suffixes) will match the cleaned column names. No change needed in the melt logic.

## Files to modify

- 9x `module_settings.toml` — add `[[samples]]`
- `proteobench/io/parsing/new_parse_input.py` — extend `ModuleSettings`, add `SampleAnnotation`
- `proteobench/io/parsing/parse_settings.py` — `ParseSettingsQuant.__init__` accepts sample annotation
- ~77 per-tool TOMLs — remove `[condition_mapper]` and `[run_mapper]`
- Tests

## Relationship to other TODOs

This is a follow-up to the parsing/benchmarking separation. Once done, per-tool TOMLs contain only:
- `[mapper]` — column renames (truly tool-specific)
- `[general]` — `decoy_flag`, `contaminant_flag`, `run_name_cleanup`
- `[modifications_parser]` — optional, tool-specific modification handling

Everything else (species, sample annotation, expected ratios) lives in `module_settings.toml`.
