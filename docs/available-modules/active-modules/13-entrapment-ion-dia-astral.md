# DIA Ion Entrapment - Astral

This module uses entrapment peptides to assess whether the false discovery rate (FDR) reported by a DIA search engine is reliable. It is based on the entrapment approach described in [Wen et al., 2025](https://www.nature.com/articles/s41592-025-02719-x).

> **This module is in alpha stage. Results and interfaces may change.**

## Purpose

FDR control is a central assumption in proteomics data analysis. When a search engine reports 1% FDR, the actual proportion of false discoveries should not exceed 1%. This module tests that assumption empirically by spiking a known set of "entrapment" peptides into the search space. These peptides cannot be present in the sample (they are derived from a shuffled or decoupled database), so any identification of an entrapment peptide represents a false discovery.

It is important to note that different search engines calculate the FDR on different levels - within a run, globally, on the precursor level, peptidoform level, protein group level, ... .
This module tests the **global precursor ion level FDR**. Search engines that do not calculate the FDR on this level can not be benchmarked with this module.

Three metrics are computed:

- **Lower bound FDP**: minimum estimate of the false discovery proportion, based on the raw count of entrapment identifications.
- **Combined FDP** (upper bound): corrected upper bound accounting for the 1:1 target-to-entrapment ratio in the search database.
- **Paired FDP** (upper bound): refined upper bound using a paired peptide mapping, which accounts for entrapment peptides that are harder to identify than their target counterparts.

Each workflow submission is classified as:

- **Valid**: the upper bound FDP is lower than the reported FDR threshold.
- **Inconclusive**: the lower bound is lower than the declared FDR but the upper bound is higher. This means that the actual FDP could be lower or higher than the reported FDR, therefore we can not say if the FDR is valid or not.
- **Invalid**: even the lower bound is higher than the declared FDR threshold.

## Critical requirements before running

> **Do not rename the raw files after download.** File names are used for run mapping and must match exactly.

> **Use the pre-digested entrapment FASTA — do not enable in-silico digestion.** The entrapment FASTA already contains peptide sequences (not full proteins). Enabling digestion in your search engine will lead to identified peptides without matched entrapments, which makes FDP calculation less accurate.

> **Do not add any variable modifications.**

## Data set

The benchmark dataset consists of three technical replicates of a 50ng HeLa digest acquired on an Orbitrap Astral (Thermo Fisher Scientific) in DIA mode with a 15-minute gradient. The mass spectrometer was operated in positive ionization mode with data-independent acquisition, with a full MS scans over a mass range of m/z 380-980 with detection in the Orbitrap at a resolution of 240,000. In each cycle of data-independent acquisition, 300 windows of 2 Th were used to isolate and fragment all precursor ions from 380 to 980 m/z. A normalized collision energy of 25% was used for HCD fragmentation. MS2 scan range was set from 150 to 2000 m/z with detection in the Astral with a maximum injection time of 3 ms. Full details on the dataset can be found in [this preprint](https://www.biorxiv.org/content/10.64898/2026.01.29.702266v2)

The files can be downloaded from the [ProteoBench server](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/):

- Single archive with FASTA: [all_data_Entrapment_DIA_Astral.tar.gz](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/all_data_Entrapment_DIA_Astral.tar.gz).

- [LFQ_Astral_DIA_15min_50ng_Human_01.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/LFQ_Astral_DIA_15min_50ng_Human_01.raw)
- [LFQ_Astral_DIA_15min_50ng_Human_02.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/LFQ_Astral_DIA_15min_50ng_Human_02.raw)
- [LFQ_Astral_DIA_15min_50ng_Human_03.raw](https://proteobench.cubimed.rub.de/raws/DIA-astral-entrapment/LFQ_Astral_DIA_15min_50ng_Human_03.raw)

**It is imperative not to rename the files once downloaded.**

The entrapment FASTA (`ProteoBenchFASTA_Entrapment_Human_with_contaminants_entrapment_pep.txt`) is available from the ProteoBench server. It contains human peptide sequences alongside a matched set of entrapment peptide sequences (suffixed `_p_target` to allow classification). **This file is pre-digested: do not apply enzymatic digestion in your search engine settings.**

## Metric calculation

ProteoBench reads the search engine output, maps runs to samples, and classifies each precursor identification as either a **target** or an **entrapment** hit based on the tag in the fasta.

The three FDP estimates are computed from the resulting set and compared to the reported FDR threshold, which is inferred from the q-value column of the output file. PEAKS reports no q-value column, so one is derived from its score (see the PEAKS section).

## How to use

### Suggested parameters

The module currently accepts DIA-NN, FragPipe, FragPipe with DIA-NN quantification, AlphaDIA, and PEAKS output. Use the suggested parameters in Table 1 for a fair comparison between tools.

**Table 1. Suggested parameters**

| Parameter | Value |
|---|---|
| PSM / precursor FDR | 0.01 |
| Spectral library | Predicted from entrapment FASTA |
| Digestion | **None** (FASTA is pre-digested) |
| Fixed modifications | Carbamidomethylation (C) |
| Variable modifications | **None** |
| Precursor charge range | 1–5 |
| Precursor m/z range | 400–1000 |
| Fragment m/z range | 100–1800 |

### Submit your run for public usage

After uploading and privately inspecting your results, you can submit the run for public display. Upload the parameter file associated with your search (see tool-specific sections below), fill in the `Comments for submission` field if needed, confirm the metadata is correct, and press `I really want to upload it`.

You will receive a link to a GitHub pull request. Save it — it contains your run's unique identifier and allows you to communicate with the ProteoBench maintainers. Accepted submissions become publicly visible within a few working days.

**Table 2. Input files required for metric calculation and public submission**

| Tool | Input file | Parsed FDR Column | Parameter file |
|---|---|---|---|
| DIA-NN | `report.tsv` or `report.parquet` | Lib.Q.Value | `report.log.txt` |
| FragPipe (DIA-NN quant) | `report.tsv` or `report.parquet` | Global.Q.Value | FragPipe `.workflow` |
| AlphaDIA | `precursors.parquet` | qval | AlphaDIA `log.txt` |
| PEAKS | `dia_db.precursor.csv` | derived from -10LgP (see below) | `parameters.txt` |

## Tool-specific settings

### [DIA-NN](https://github.com/vdemichev/DiaNN)

1. Import the raw `.raw` files.
2. Add the entrapment FASTA. Do not enable "Contaminants" — contaminants are already included in the FASTA.
3. **Disable in-silico digestion.** The FASTA is pre-digested; use '--cut ' in the additional parameter fields to disable enzymatic cleavage.
4. Enable library-free search / FASTA-based library generation (activates deep-learning prediction of spectra, RTs, and IMs).
5. Do not set verbosity / log level higher than 1, otherwise parameter parsing will fail.
6. Upload `report.tsv` or `report.parquet` for metric calculation, and `report.log.txt` for public submission.

### FragPipe with DIA-NN quantification

FragPipe workflows that produce a DIA-NN-style report are submitted as **FragPipe (DIA-NN quant)**. ProteoBench parses the precursor identifications from the DIA-NN report and extracts workflow metadata from the FragPipe `.workflow` file.

1. Use the ProteoBench entrapment FASTA as the sequence database. Do not add a second contaminant database.
2. Configure the search without enzymatic digestion. The FASTA contains pre-digested peptide entries, so in-silico digestion must remain disabled throughout the FragPipe/DIA-NN workflow. MSFragger Protein Digestion settings:

```
Load Rules:    nocleavage
Cuts 1:        @
No cuts 1:     @
```

To set these via the GUI: MSFragger tab -> Protein Digestion -> Load Rules = "nocleavage"; Cuts 1 = "@"; No cuts 1 = "@".
3. Keep variable modifications disabled. Carbamidomethylation (C) may be used as the fixed modification.
4. Use the DIA-NN report generated by FragPipe (`report.tsv` or `report.parquet`) for metric calculation.
5. Upload the FragPipe `.workflow` file for public submission. Do not upload the DIA-NN log as the parameter file for this workflow type.

### [AlphaDIA](https://github.com/MannLabs/alphadia)

AlphaDIA submissions are parsed from precursor-level output. The entrapment module currently expects AlphaDIA 2.x-style precursor output.

1. Use the ProteoBench entrapment FASTA and disable additional contaminants.
2. Configure AlphaDIA for a no-enzyme / pre-digested FASTA search: set "no-cleave" as the enzyme parameter.
3. Keep variable modifications disabled. Use Carbamidomethylation (C) as the fixed modification if alkylation was applied.
4. Upload `precursors.parquet` for metric calculation.
5. Upload the AlphaDIA `log.txt` file for public submission.

### [PEAKS](https://www.bioinfor.com/)

PEAKS submissions are parsed from the DIA database search precursor export. **This is a different file than the one used by the quantification modules**, which read the LFQ feature table (`lfq-features.csv`). The entrapment module needs precursor-level identifications, so upload `dia_db.precursor.csv` from the DIA DB search export instead.

1. Use the ProteoBench entrapment FASTA as the target database. Do not add a contaminant database.
2. Set `Digest Mode` to `NO_DIGESTION` and `Enzyme` to `None`, so no in-silico digestion is applied to the pre-digested FASTA.
3. Keep variable modifications empty. Use Carbamidomethylation as the fixed modification if alkylation was applied.
4. Set the precursor FDR to 1% in the `Precursor Filter` settings.
5. Upload `dia_db.precursor.csv` for metric calculation.
6. Upload the PEAKS parameter export (`parameters.txt`) for public submission.

**Reported FDR threshold for PEAKS.** `dia_db.precursor.csv` has no q-value column. ProteoBench derives one by back-transforming the PEAKS score, `q = 10 ** (-(-10LgP) / 10)`, and uses it exactly as the q-value of the other tools: to infer the reported FDR threshold, to rank precursors for the paired FDP, and to build the FDP-versus-threshold curve.

The back-transform is the inverse of the definition PEAKS uses. As described in the [PEAKS database search scoring documentation](https://www.bioinfor.com/dbscoring-tutorial/) and in [Zhang et al., 2012](https://doi.org/10.1074/mcp.M111.010587), PEAKS converts its internal LDF score to a P-value and reports `-10lgP = -10 * log10(P)`. The important detail is how that P-value is defined: it is the probability that a **false identification** scores above the observed score, not the probability that an individual random peptide matches the spectrum. PEAKS documents this distinction explicitly, on the grounds that a false identification arises from the many random peptides in the database rather than from a single one. Because the definition is taken over the distribution of false identifications, it already absorbs the size of the search space and lands on the same scale as a global precursor q-value.

Two observations on the ProteoBench entrapment data are consistent with this:

- The entrapment-derived false discovery proportion tracks the derived q-value within a constant factor over the accessible range (1e-3 to 1e-2), rather than diverging from it.
- The precursor FDR filter sets the floor of the export. On the reference data, a 1% precursor FDR filter floors both the precursor and the peptide export at exactly `-10LgP = 20.0000`, that is `q = 0.010000`, so the maximum derived q-value reproduces the threshold that was applied.

#### How the derived value differs from a target-decoy q-value

The PEAKS P-value and a conventional q-value share the same numerator, the expected number of false identifications scoring above the threshold `x`. They differ in what that numerator is divided by:

| Quantity | Denominator | Reads as |
|---|---|---|
| PEAKS P-value | `m0`, the total number of false identifications in the search | "1% of all false identifications score better than this" |
| Target-decoy q-value | `R(x)`, the number of identifications accepted at this threshold | "1% of what I accepted is false" |

Written out, `P(x) = E[V(x)] / m0` and `FDR(x) = E[V(x)] / R(x)`, so the two are related by

```
q(x) ~ P(x) * m0 / R(x)
```

They coincide only when `m0` is close to `R(x)`, which is not generally the case. This is why a P-value threshold is not an FDR threshold even though both lie in `[0, 1]` and both are quoted as percentages.

The entrapment measurement recovers that `m0 / R(x)` correction factor directly. On the reference dataset:

| Derived q (= P) | Accepted IDs `R(t)` | Lower bound FDP | Ratio | Combined FDP | Ratio |
|---|---|---|---|---|---|
| 1e-3 | 40 698 | 0.00135 | 1.35 | 0.00270 | 2.70 |
| 3e-3 | 44 689 | 0.00405 | 1.35 | 0.00810 | 2.70 |
| 5e-3 | 46 448 | 0.00670 | 1.34 | 0.01339 | 2.68 |
| 1e-2 | 48 983 | 0.01286 | 1.29 | 0.02572 | 2.57 |

The combined estimate, which corrects for the 1:1 entrapment ratio, puts the true FDR at roughly 2.6 times the PEAKS P-value across the whole range. Two further differences follow from the definitions:

- **Dependence on sample composition.** `P(x)` depends only on the modelled distribution of false match scores, so two searches of the same database return the same `P` for the same score. `q(x)` also depends on how many correct identifications were made, so the same score maps to a different q-value on a clean sample than on a poor one. This module is particularly exposed to the difference, because searching a pre-digested database of 2.8 million peptides without enzymatic cleavage makes `m0` large.
- **Estimation method and resolution.** `P(x)` is parametric: PEAKS fits the false match score distribution, so `P` is continuous and can be arbitrarily small. A target-decoy q-value is a ratio of counts, so its smallest non-zero step corresponds to a single decoy hit, about `1 / R`. See the second caveat below.

#### Caveats

**The reported threshold is only verified at 1%.** Because `-10lgP = -10 * log10(P)`, a P-value of 0.05 maps to 13.01, 0.01 maps to 20.00, and 0.001 maps to 30.00. On the reference run the 1% precursor FDR filter produced a floor of exactly `-10lgP = 20.0000`, so the derived q-value reproduces the applied threshold at that setting. Note that this is also the point where PEAKS' conventional `-10lgP >= 20` default cutoff sits, and other precursor FDR settings have not yet been checked against ProteoBench. If you submit a run filtered at a different precursor FDR, **check that the reported FDR threshold shown for your run matches the value you set**, and report a mismatch as a [GitHub issue](https://github.com/Proteobench/ProteoBench/issues/new). A threshold read too low would compare the empirical FDP against too strict a value, which can produce a false `invalid` verdict but not a false `valid` one.

**The high-confidence tail is finer-grained than any FDR estimate can be.** On the reference dataset the derived value takes 4 529 distinct values across 48 983 precursors, spaced 0.01 apart on the `-10lgP` scale, so it is effectively continuous rather than a step function. The resolution floor of a decoy-counted q-value here would be `1 / 48 983 = 2.0e-5`, and 45% of precursors fall below it, down to a minimum of `2.4e-11`. A rate of `2.4e-11` would require on the order of 4e10 identifications before a single false one is expected, so it cannot be read as an FDR estimate.

This does not affect any reported metric. Every threshold the module uses is 1e-3 or larger, and in that region there are tens of thousands of identifications and hundreds of entrapment hits, so the derived value carries genuine FDR-scale information. Below that region it serves only to order precursors, which is all the module requires there: the `Score` column of the intermediate result is a rank rather than a value, the paired FDP compares ranks, and no threshold is ever placed in the tail.

## Result description

After uploading, you will see the FDP bounds plotted against the FDR estimate reported by the search engine. A valid (conservative) FDR calculation has the empirical upper bound below the declared FDR threshold.

You can also compare the results with other submissions in the 'View Public + New Results' Tab. The following plots are shown:

- **Forest plot**: one horizontal interval per workflow, showing the lower bound FDP to the paired FDP upper bound. The declared FDR threshold is marked with a diamond.
- **FDP / FDR ratio vs # IDs**: scatter plot of paired FDP divided by the declared FDR (x-axis) against the number of identifications at 1% FDR (y-axis). Points to the left of x = 1 have an empirical FDP below the declared threshold.

## Define parameters

For public submission, the following parameters are extracted from the parameter file. If a parameter is not in the file, add it in `Comments for submission`.

- Software tool name and version
- FDR threshold for PSM / precursor, peptide, and protein level
- Precursor and fragment m/z range
- Precursor mass tolerance
- Fragment mass tolerance
- Fixed and variable modifications
- Minimum and maximum precursor charge
- Enzyme (should be "None" for this module)

**DISCLAIMER**: Parameter files may contain file paths that reveal personal usernames, system architecture, or directory structures (FASTA location, raw data location, tool installation paths). Review and sanitize file paths before submission to avoid disclosing institutional or personal identifiers.

Once submitted, a pull request link is shown. Save it to track your submission. Contact us via a [GitHub issue](https://github.com/Proteobench/ProteoBench/issues/new) or [email](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query) if you encounter any problems.
