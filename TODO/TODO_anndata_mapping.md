# TODO: AnnData Mapping For Quant Parsing Rules

## Purpose

Define a TOML rule format for mapping quantification outputs in `test_data_download/json_dir/`
into AnnData.

This document now reflects the decisions already made. It is about the rule contract, not yet the
full implementation.

This TODO is meant to become source material for a future skill file that helps an AI:

- generate TOMLs for all vendor file types
- implement a Python program that reads those TOMLs
- convert vendor files into AnnData according to the TOML rules

## Decisions

### AnnData orientation

- `obs` = samples / runs
- `var` = quantified features
- `X` = primary quantitative matrix
- `layers` = additional per-sample-per-feature matrices
- `uns` = provenance, parser metadata, category mappings, anything not cleanly representable as
  `obs`, `var`, or matrix-shaped `layers`

### Axis keys

- `axis.obs_keys` defines the columns that become the AnnData observation axis
- `axis.var_keys` defines the columns that become the AnnData variable axis
- `var_keys` must be chosen per software
- Pragmatic rule for `var_keys`: use the smallest set of source columns that avoids duplicates in
  `var`

### Column naming

- Right-hand-side names must preserve the exact vendor column names
- Left-hand-side names may be cleaner internal names
- Clean names must live inside typed sections like `columns.obs`, `columns.var`, and `layers`
- No separate global alias table

### Numeric vs string layers

- Treat `layers` as numeric storage
- If a matrix-shaped vendor field is string-valued, encode it as integer factors in the layer
- Store the factor mapping in the TOML and in AnnData metadata

Examples:

- FragPipe `Match Type`
- FragPipe `Localization`

### Version fields

- `schema_version` = version of the TOML schema itself
- `file_version` = version of the specific parsing-rule TOML
- `software_version` = vendor software version metadata, when known

Filename convention:

- `parse_<softwareName>_<fileVersion>.toml`

Here `fileVersion` means the parsing-rule version, not the vendor software version.

### Long vs wide

- Long and wide should use the same top-level concepts
- The main difference is only how a layer finds its source data:
  - long: `source_column`
  - wide: `column_pattern`

### Wide-file obs creation

- Wide files still must define `obs`
- In the minimal case, `obs` is created from the `<sample>` token extracted by a layer regex
- For this stage, vendor-derived obs names should be kept as they are
- This is especially true for WOMBAT and Proteome Discoverer
- Additional obs annotation and normalization can happen in a second step later

### Duplicate handling

- Each TOML must define a duplicate policy for duplicate `(obs, var)` entries
- Allowed modes:
  - `error`
  - `aggregate`
  - `keep_first`
  - `keep_all_as_raw_table`
- Default recommendation: `error`, unless a software-specific aggregation rule is intentionally
  defined

## TOML Schema

This is the rule schema we want to support.

## Common Entries

These entries are valid for both long and wide rules.

- `schema_version`
  Purpose: version of the TOML schema
  Type: string
  Example: `"0.1"`

- `file_version`
  Purpose: version of this parsing-rule file
  Type: string
  Example: `"1"`

- `software_name`
  Purpose: human-readable software identifier
  Type: string
  Example: `"FragPipe"`

- `software_version`
  Purpose: vendor software version metadata
  Type: string
  Optional: yes

- `input_shape`
  Purpose: declares whether the rule is for long or wide input
  Type: string
  Allowed values: `"long"`, `"wide"`

- `[axis]`
  Purpose: defines the AnnData axes and the primary quantitative matrix

- `axis.obs_keys`
  Purpose: columns that define the observation axis
  Type: array of strings

- `axis.var_keys`
  Purpose: columns that define the variable axis
  Type: array of strings

- `axis.x_layer`
  Purpose: which parsed layer becomes `X`
  Type: string
  Value: must match one `layers.name`

- `[columns.obs]`
  Purpose: map internal obs field names to source values
  Type: key-value mapping
  Form: `Internal_Name = "Vendor column"` or `Internal_Name = "<sample>"`

- `[columns.var]`
  Purpose: map internal var field names to source vendor columns
  Type: key-value mapping
  Form: `Internal_Name = "Vendor column"`

- `[[layers]]`
  Purpose: defines one matrix-valued layer
  Required entry: `name`

- `layers.name`
  Purpose: internal layer name
  Type: string

- `[duplicates]`
  Purpose: duplicate handling policy

- `duplicates.mode`
  Purpose: duplicate handling mode
  Type: string
  Allowed values: `"error"`, `"aggregate"`, `"keep_first"`, `"keep_all_as_raw_table"`

## Long Rule Entries

These entries are valid when `input_shape = "long"`.

- `layers.source_column`
  Purpose: vendor column to pivot into this layer
  Type: string
  Required for long layers: yes

- `layers.encoding_mode`
  Purpose: declares how layer values are encoded
  Type: string
  Allowed values: `"numeric"`, `"factor"`
  Optional: yes

- `layers.categories`
  Purpose: mapping from vendor string values to integer factor codes
  Type: inline table or TOML table
  Required when `encoding_mode = "factor"`: yes

Long example:

```toml
schema_version = "0.1"
file_version = "1"
software_name = "DIA-NN"
software_version = "1.9.1"
input_shape = "long"

[axis]
obs_keys = ["Run"]
var_keys = ["Modified.Sequence", "Precursor.Charge"]
x_layer = "Precursor_Normalised"

[columns.obs]
File_Name = "File.Name"
Run = "Run"

[columns.var]
Modified_Sequence = "Modified.Sequence"
Protein_Ids = "Protein.Ids"
Precursor_Charge = "Precursor.Charge"
Genes = "Genes"

[[layers]]
name = "Precursor_Normalised"
source_column = "Precursor.Normalised"

[[layers]]
name = "Q_Value"
source_column = "Q.Value"

[[layers]]
name = "RT"
source_column = "RT"

[[layers]]
name = "Ms1_Area"
source_column = "Ms1.Area"

[duplicates]
mode = "error"
```

## Wide Rule Entries

These entries are valid when `input_shape = "wide"`.

- `layers.column_pattern`
  Purpose: regex that finds the source columns for this layer
  Type: string
  Required for wide layers: yes
  Requirement: should expose a named capture group `sample` when sample names are encoded in the
  column names

- `[sample_name_cleanup]`
  Purpose: cleanup applied to extracted `<sample>` tokens
  Optional: yes

- `sample_name_cleanup.pattern`
  Purpose: regex used to normalize extracted sample names
  Type: string

- `[sample_name_map]`
  Purpose: optional explicit mapping from extracted sample tokens to final obs names
  Optional: yes
  Recommendation for this project stage: usually do not use it; keep vendor-derived obs names as
  they are and add richer obs annotation later in a second step

- `layers.encoding_mode`
  Purpose: declares how layer values are encoded
  Type: string
  Allowed values: `"numeric"`, `"factor"`
  Optional: yes

- `layers.categories`
  Purpose: mapping from vendor string values to integer factor codes
  Type: inline table or TOML table
  Required when `encoding_mode = "factor"`: yes

Wide example:

```toml
schema_version = "0.1"
file_version = "1"
software_name = "FragPipe"
software_version = "23.0"
input_shape = "wide"

[axis]
obs_keys = ["sample"]
var_keys = ["Modified Sequence", "Charge"]
x_layer = "Intensity"

[columns.obs]
sample = "<sample>"

[columns.var]
Peptide_Sequence = "Peptide Sequence"
Modified_Sequence = "Modified Sequence"
Charge = "Charge"
Protein_ID = "Protein ID"
Gene = "Gene"

[[layers]]
name = "Intensity"
column_pattern = "^(?P<sample>.+) Intensity$"

[[layers]]
name = "Spectral_Count"
column_pattern = "^(?P<sample>.+) Spectral Count$"

[[layers]]
name = "Match_Type"
column_pattern = "^(?P<sample>.+) Match Type$"
encoding_mode = "factor"
categories = { "unmatched" = 0, "MS/MS" = 1, "MBR" = 2 }

[[layers]]
name = "Localization"
column_pattern = "^(?P<sample>.+) Localization$"
encoding_mode = "factor"

[sample_name_cleanup]
pattern = ""

[duplicates]
mode = "error"
```

## Software Families Already Seen

- Long-like:
  - DIA-NN
  - Spectronaut
  - AlphaDIA long export
  - MaxQuant evidence-like outputs

- Wide-like:
  - FragPipe
  - WOMBAT
  - AlphaDIA wide export

This is why the rule schema must support both exact source columns and regex-driven sample-column
detection.

## Recommended Implementation Path

1. Keep one shared TOML schema for both long and wide.
2. Implement rule validation first.
3. Implement long parsing with `source_column`.
4. Implement wide parsing with `column_pattern`.
5. Add factor encoding for string-valued layers.
6. Generate the first representative TOMLs:
   - one long example
   - one wide regex example
   - one wide explicit sample-mapping example
7. Add tests that verify:
   - all configured columns are represented
   - all rows are represented
   - `obs` and `var` axes are constructed as specified
   - `X` and `layers` match the TOML definition
