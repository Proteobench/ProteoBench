This module compares the MS1-level quantification tools for
data-dependent acquisition (DDA) on an Astral. The raw files provided for
this module are presented in the comprehensive LFQ benchmark
dataset from Van Puyvelde et al., manuscript in progress.
The samples contain tryptic peptides from Homo sapiens,
Saccharomyces cerevisiae, and Escherichia coli, mixed in different
ratios (condition A and condition B), with three replicates of each
condition. With these samples, we calculate three metrics:
- To estimate the sensitivity of the workflows, we report the
number of unique precursors (charged modified sequence) quantified
in a minimum of 1 to 6 runs.
- To estimate the accuracy of the workflows, we report the mean
absolute difference between measured and expected log2-transformed
fold changes between conditions for proteins of the same species.

ProteoBench plots these three metrics to visualize workflow outputs
    from different tools, with different versions, and/or different
sets of parameters for the search and quantification.
The full description of the pre-processing steps and metrics
calculation is available [here](https://proteobench.readthedocs.io/en/stable/available-modules/8-quant-lfq-ion-dda-astral/).
