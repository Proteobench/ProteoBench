# Parameter homogenization

When adding a new parameter parser to ProteoBench, all extracted parameters must be
**homogenized** to a canonical format before being stored. This ensures that the same
setting (e.g. "Carbamidomethylation on cysteine") is represented identically regardless
of which software tool produced it. Without homogenization, filtering and comparison
across tools would not work as desired.

This page documents the canonical formats and the reusable helpers available for each
parameter type.

## Modifications

### Target format (ProForma-like)

All modifications must be converted to a **ProForma-like** notation:

```
Residue[ModificationName]
```

Multiple modifications are separated by `, ` (comma-space).

| Raw input (examples)                     | Canonical output                          |
|------------------------------------------|-------------------------------------------|
| `Carbamidomethyl (C)`                    | `C[Carbamidomethyl]`                      |
| `Oxidation (M)`                          | `M[Oxidation]`                            |
| `Phospho (STY)`                          | `S[Phospho], T[Phospho], Y[Phospho]`     |
| `Acetyl (Protein N-term)`                | `Protein N-term[Acetyl]`                  |
| `Acetyl (N-term)`                        | `N-term[Acetyl]`                          |
| `57.02146@C`                             | `C[Carbamidomethyl]`                      |
| `Oxidation on M`                         | `M[Oxidation]`                            |
| `Oxidation of M`                         | `M[Oxidation]`                            |
| `Oxidation@M`                            | `M[Oxidation]`                            |

**Terminal modifications** use these residue prefixes:

| Prefix             | Meaning                    |
|--------------------|----------------------------|
| `N-term`           | Peptide N-terminus, or when distinction is not made         |
| `C-term`           | Peptide C-terminus, or when distinction is not made         |
| `Protein N-term`   | Protein N-terminus         |
| `Protein C-term`   | Protein C-terminus         |

### Choosing a homogenization approach

Different software tools use different notation styles. Pick the approach that
matches your tool's raw format:

#### 1. MaxQuant-style: `ModName (Residues)`

Tools using this notation: MaxQuant, Spectronaut, Proline, quantms, MSAID,
MSAngel (Mascot mode).

Import and use the dynamic parser from `maxquant.py`:

```python
from proteobench.io.params.maxquant import _homogenize_mods

params.fixed_mods = _homogenize_mods(raw_fixed_mods_string)
params.variable_mods = _homogenize_mods(raw_variable_mods_string)
```

This parser dynamically handles `ModName (Residues)` notation. Multi-letter
residues like `STY` are expanded to one entry per amino acid. Terminal qualifiers
(`N-term`, `Protein N-term`, etc.) are recognized automatically. A small
`MODIFICATION_MAPPING` fallback dict handles edge cases without parentheses
(e.g. `Cys-Cys`).

The default separator is `,`. Pass `sep="; "` if your tool uses semicolons:

```python
params.fixed_mods = _homogenize_mods(raw_string, sep="; ")
```

#### 2. MetaMorpheus-style: `ModName on Residue`

Tools using this notation: MetaMorpheus.

Use the `_homogenize_mod` function from `metamorpheus.py`, which parses
`{modname} on {residue}` dynamically. Terminal qualifiers `(Pep N-Term)` and
`(Prot N-Term)` are detected automatically.

#### 3. X!Tandem-style: `ModName of Residue`

Tools using this notation: MSAngel (X!Tandem mode), WOMBAT-P.

Import from `msangel.py`:

```python
from proteobench.io.params.msangel import _homogenize_mod_xtandem

params.fixed_mods = ", ".join(_homogenize_mod_xtandem(m) for m in raw_list)
```

#### 4. AlphaDIA-style: `ModName@Residue`

Tools using this notation: AlphaDIA.

Use the `homogenize_modification_string()` function from `alphadia.py`, which
splits on `@` and reformats to `Residue[ModName]`.

#### 5. Mass-shift based

Tools using this notation: MSFragger/FragPipe, Sage.

When the tool identifies modifications by mass shift rather than name, use a
`MASS_TO_MOD` dictionary to look up the modification name by mass within a
tolerance (typically 0.001 Da). See `fragger.py` and `sage.py` for examples.

For unknown masses, fall back to using the mass value as the name:
`K[4.025107]`.

#### 6. Static mapping

When none of the above patterns apply (e.g. PEAKS, i2MassChroQ, AlphaPept),
define a `MODIFICATION_MAPPING` dictionary in your parser module that maps raw
strings to canonical format:

```python
MODIFICATION_MAPPING = {
    "Carbamidomethylation (+57.02)": "C[Carbamidomethyl]",
    "Oxidation (M) (+15.99)": "M[Oxidation]",
}
```

Apply it when assigning:

```python
params.fixed_mods = ", ".join(MODIFICATION_MAPPING.get(m, m) for m in raw_list)
```

## Enzyme names

Enzyme normalization is handled **centrally** by the `_ENZYME_MAP` in
`proteobench/io/params/__init__.py`. It is applied automatically when
`params.fill_none()` or `normalize_dataframe_columns()` is called.

If your tool uses a non-standard enzyme name, add a lowercase mapping to
`_ENZYME_MAP`:

```python
_ENZYME_MAP = {
    "trypsin": "Trypsin",
    "trypsin/p": "Trypsin/P",
    "stricttrypsin": "Trypsin/P",
    "lys-c": "Lys-C",
    # ... add new mappings here (keys must be lowercase)
}
```

Individual parsers do **not** need to normalize enzyme names themselves, though
doing so is harmless.

## Mass tolerances

Tolerances should be formatted as bracket-enclosed ranges with units:

```
[-10 ppm, 10 ppm]
[-0.02 Da, 0.02 Da]
```

If the tool uses automatic calibration (e.g. DIA-NN, Spectronaut), store
`"Dynamic"` or `"0"` - these should be normalized to `"Automatic calibration"`.

## Integer parameters

The following parameters must be stored as **integers** (or `None` if unavailable):

- `allowed_miscleavages`
- `min_peptide_length`
- `max_peptide_length`
- `max_mods`
- `min_precursor_charge`
- `max_precursor_charge`

Make sure to convert string values with `int()` in your parser. The central
normalization also coerces these fields via `pd.to_numeric()`, but it is best
practice to store them as integers from the start.

## Boolean parameters

`enable_match_between_runs` and `semi_enzymatic` should be stored as Python
`bool` values (`True`/`False`), not strings.

## FDR values

FDR values should be stored as **decimals between 0 and 1** (e.g. `0.01` for 1%).
If the tool reports percentages, divide by 100. The central normalization in
`__init__.py` also handles this: values >= 1 are automatically divided by 100.

## Missing values

If a parameter is not available for a given tool, set it to `None`. The
`params.fill_none()` call replaces sentinel strings like `"not specified"`,
`"N/A"`, `"None"`, and `""` with proper `None`/`NaN` values.

## Checklist for new parsers

When adding a new parameter parser:

1. Create `proteobench/io/params/<toolname>.py`
2. Implement `extract_params()` returning a `ProteoBenchParameters` object
3. **Homogenize modifications** using one of the approaches above, or a new approach
4. Format tolerances as `[-value unit, value unit]`
5. Store FDR as decimal (0-1)
6. Add any new enzyme names to `_ENZYME_MAP` in `__init__.py`
7. Call `params.fill_none()` before returning
8. Add test data files and expected output CSVs in `test/params/`
9. Run existing tests to verify nothing is broken

# Note

If you notice anything wrong with the current parameter parsing approaches, do not hesitate to create an issue on [GitHub](https://github.com/Proteobench/ProteoBench/issues)