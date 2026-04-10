# DDA quantification - peptidoform level (QExactive)

This module compares the sensitivity and quantification accuracy for data acquired with data-dependent acquisition (DDA) on a Q Exactive HF-X Orbitrap (Thermo Fisher).
It is based on the DDA quantification module "ion-level" described [here](#2-quant-lfq-ion-dda). Data and metrics are the same, the difference is that in this module we focus on peptidoform quantities summarised from the precursor ion quantities. 

## How to use

Click [here](https://proteobench.cubimed.rub.de/Quant_LFQ_DDA_peptidoform) if you want to submit your results or when you want to explore the module.

**We are working on the documentation: more information coming soon.**

---

> **DOCUMENTATION GAPS**
>
> The following sections are present in other quantification modules (e.g. Module 2 DDA ion, Module 5 diaPASEF) but missing here:
>
> - **Metric calculation**: How metrics are calculated, epsilon definition, CV, log2-transformation
> - **Suggested parameters table**: Recommended parameters for fair comparison (missed cleavages, FDR, modifications, etc.)
> - **Tool-specific instructions**: Step-by-step instructions for each supported tool (input files, parameter files, column mappings)
> - **Table of supported tools**: Overview of required input files for metric calculation and public submission
> - **Custom format specification**: Column definitions for the generic tab-delimited input format
> - **TOML file description**: Explanation of the TOML configuration for parsing
> - **Result description**: Column definitions of the output/result DataFrame
> - **Public submission instructions**: How to submit a benchmark run for public usage
> - **FASTA database**: Link to the FASTA file and description of species/contaminants
> - **Clarification**: How does this module differ from Module 2 beyond "peptidoform vs ion level"? What aggregation is applied?
