# Parameter homogenization

When adding a new parameter parser to ProteoBench, all extracted parameters must be
**homogenized** to a canonical format before being stored. This ensures that the same setting (e.g.
"Carbamidomethylation on cysteine") is represented identically regardless of which software tool
produced it — without homogenization, filtering and comparison across tools wouldn't work.

This page documents the canonical formats and the reusable helpers available for each parameter
type.

## Modifications

### Target format (ProForma-like)

All modifications must be converted to a **ProForma-like** notation:

```
Residue[ModificationName]
```

Multiple modifications are separated by `, ` (comma-space).

| Raw input (examples) | Canonical output |
|---|---|
| `Carbamidomethyl (C)` | `C[Carbamidomethyl]` |
| `Oxidation (M)` | `M[Oxidation]` |
| `Phospho (STY)` | `S[Phospho], T[Phospho], Y[Phospho]` |
| `Acetyl (Protein N-term)` | `Protein N-term[Acetyl]` |
| `Acetyl (N-term)` | `N-term[Acetyl]` |
| `57.02146@C` | `C[Carbamidomethyl]` |
| `Oxidation on M` | `M[Oxidation]` |
| `Oxidation of M` | `M[Oxidation]` |
| `Oxidation@M` | `M[Oxidation]` |

**Terminal modifications** use these residue prefixes:

| Prefix | Meaning |
|---|---|
| `N-term` | Peptide N-terminus, or when no distinction is made |
| `C-term` | Peptide C-terminus, or when no distinction is made |
| `Protein N-term` | Protein N-terminus |
| `Protein C-term` | Protein C-terminus |

### Choosing a homogenization approach

Different tools use different notation styles. Pick the approach matching your tool's raw format.

**1. MaxQuant-style: `ModName (Residues)`** — MaxQuant, Spectronaut, Proline, quantms, MSAID,
MSAngel (Mascot mode).

```python
from proteobench.io.params.maxquant import _homogenize_mods

params.fixed_mods = _homogenize_mods(raw_fixed_mods_string)
params.variable_mods = _homogenize_mods(raw_variable_mods_string)
```

Multi-letter residues like `STY` are expanded to one entry per amino acid, and terminal qualifiers
(`N-term`, `Protein N-term`, etc.) are recognized automatically. A small `MODIFICATION_MAPPING`
fallback dict handles edge cases without parentheses (e.g. `Cys-Cys`). The default separator is
`,`; pass `sep="; "` for tools using semicolons.

**2. MetaMorpheus-style: `ModName on Residue`** — MetaMorpheus. Use `_homogenize_mod` from
`metamorpheus.py`, which parses `{modname} on {residue}` dynamically and detects `(Pep N-Term)` /
`(Prot N-Term)` qualifiers automatically.

**3. X!Tandem-style: `ModName of Residue`** — MSAngel (X!Tandem mode), WOMBAT-P.

```python
from proteobench.io.params.msangel import _homogenize_mod_xtandem

params.fixed_mods = ", ".join(_homogenize_mod_xtandem(m) for m in raw_list)
```

**4. AlphaDIA-style: `ModName@Residue`** — AlphaDIA. Use `homogenize_modification_string()` from
`alphadia.py`, which splits on `@` and reformats to `Residue[ModName]`.

**5. Mass-shift based** — MSFragger/FragPipe, Sage. When the tool identifies modifications by mass
shift rather than name, use a `MASS_TO_MOD` dictionary to look up the name by mass within a
tolerance (typically 0.001 Da); see `fragger.py` and `sage.py`. For unknown masses, fall back to
the mass value as the name (e.g. `K[4.025107]`).

**6. Static mapping** — when none of the above apply (e.g. PEAKS, i2MassChroQ, AlphaPept), define a
`MODIFICATION_MAPPING` dict in your parser module:

```python
MODIFICATION_MAPPING = {
    "Carbamidomethylation (+57.02)": "C[Carbamidomethyl]",
    "Oxidation (M) (+15.99)": "M[Oxidation]",
}
params.fixed_mods = ", ".join(MODIFICATION_MAPPING.get(m, m) for m in raw_list)
```

## Enzyme names

Handled centrally by `_ENZYME_MAP` in `proteobench/io/params/__init__.py`, applied automatically
when `params.fill_none()` or `normalize_dataframe_columns()` is called. If your tool uses a
non-standard enzyme name, add a lowercase mapping:

```python
_ENZYME_MAP = {
    "trypsin": "Trypsin",
    "trypsin/p": "Trypsin/P",
    "stricttrypsin": "Trypsin/P",
    "lys-c": "Lys-C",
    # ... add new mappings here (keys must be lowercase)
}
```

Individual parsers don't need to normalize enzyme names themselves, though doing so is harmless.

## Mass tolerances

Format as bracket-enclosed ranges with units:

```
[-10 ppm, 10 ppm]
[-0.02 Da, 0.02 Da]
```

If the tool uses automatic calibration (e.g. DIA-NN, Spectronaut), store `"Dynamic"` or `"0"` —
these are normalized to `"Automatic calibration"`.

## Integer parameters

Store these as **integers** (or `None` if unavailable): `allowed_miscleavages`,
`min_peptide_length`, `max_peptide_length`, `max_mods`, `min_precursor_charge`,
`max_precursor_charge`. Convert string values with `int()` in your parser; the central
normalization also coerces via `pd.to_numeric()`, but storing as integers from the start is best
practice.

## Boolean parameters

`enable_match_between_runs` and `semi_enzymatic` should be Python `bool` values (`True`/`False`),
not strings.

## FDR values

Store as **decimals between 0 and 1** (e.g. `0.01` for 1%); divide by 100 if the tool reports
percentages. The central normalization in `__init__.py` also handles this: values ≥ 1 are
automatically divided by 100.

## Missing values

If a parameter isn't available, set it to `None`. `params.fill_none()` replaces sentinel strings
like `"not specified"`, `"N/A"`, `"None"`, and `""` with proper `None`/`NaN` values.

## Checklist for new parsers

1. Create `proteobench/io/params/<toolname>.py`.
2. Implement `extract_params()` returning a `ProteoBenchParameters` object.
3. Homogenize modifications using one of the approaches above (or a new one).
4. Format tolerances as `[-value unit, value unit]`.
5. Store FDR as a decimal (0–1).
6. Add any new enzyme names to `_ENZYME_MAP` in `__init__.py`.
7. Call `params.fill_none()` before returning.
8. Add test data files and expected output CSVs in `test/params/`.
9. Run existing tests to verify nothing else broke.

If you notice anything wrong with the current parsing approaches, open an issue on
[GitHub](https://github.com/Proteobench/ProteoBench/issues).
