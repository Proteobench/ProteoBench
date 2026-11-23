This module benchmarks DIA precursor-level quantification on plasma samples spiked with low-abundant yeast and E. coli digests (PYE).

Runs can be visualized privately and submitted publicly for community comparison.

Main plot dimensions:
- X-axis: absolute log2 fold-change error for spike-ins (YEAST + ECOLI)
- Y-axis: number of quantified spike-in precursors (the counts per individual species are reported in the hover text and in the results table)
- Dot size: HUMAN plasma dynamic range, calculated per condition as the difference between the 90th and the 10th percentile of the log10-transformed mean precursor intensities, averaged over conditions A and B. The value is expressed in orders of magnitude: 3.0 means that the central 80% of the quantified plasma precursors span three orders of magnitude in intensity.
- Dot opacity: HUMAN plasma quantification accuracy (darker = better)

Dot size and dot opacity are min-max normalised over the displayed benchmark runs, so they encode the ranking within the displayed set. The raw values are reported in the hover text.

Release stage: **BETA**.

