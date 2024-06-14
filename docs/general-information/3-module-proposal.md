# How to propose/discuss a new module

Anyone can start a discussion or more formally propose new module.

Proposals can be started by opening a [discussion on GitHub](https://github.com/orgs/Proteobench/discussions/new?category=potential-new-module-to-discuss), using a specific template. One of the ProteoBench maintainers will be assigned as editor.  
At least two reviewers, independent from both existing ProteoBench contributors and from the proposal submitters, should be contacted to review the proposal.

Required information for a proposal:

1. A **description of the new module**:
    - Which aspect of proteomics data analysis is benchmarked?
    - Added value compared to already existing modules?
2. **Input data**:
    - Provide a persistent identifier for the dataset (e.g., PXD, or DOI) (If this does not exist yet, publish the data on Zenodo and provide this DOI)
    - Optionally, provide DOI to the dataset publication
    - If only a subset of the referenced dataset is used, describe which subset.
    - Describe why this dataset was selected.
3. **Workflow output data** (data to be uploaded to ProteoBench for metric calculation)
4. Specify the **minimal information needed from the workflow for metric calculation**. This can be an existing (standardized) file format, or a simple well-described CSV file.
5. **Structured metadata**: Which information is needed to sufficiently describe each benchmark run (e.g., workflow parameters).
6. **Metrics**:
    - Description of the benchmark metrics
    - Methodology for calculating benchmark metrics
7. How can the metric for each benchmark run be shown in a **single visualization** (optionally add a mock figure)
8. **External reviewers**: Optionally propose at least two reviewers (see above)
9. Will you be able to work on the implementation (coding) yourself, with additional help from the ProteoBench maintainers?
