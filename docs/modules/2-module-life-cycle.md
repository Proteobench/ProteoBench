# Benchmark module life cycle

Anybody can propose a new benchmark module, and discuss on the validity of current modules. There are 6 phases in the benchmark modules life cycle:
1. Module proposal
2. Implementation
3. Beta 
4. Live
5. Archived
6. Withdrawn


## Proposal

*Module proposals are not accepted yet. If you are interested, stay tuned.*

Proposals can be started by opening a thread on GitHub Discussions, using a specific template. One of the ProteoBench maintainers will be assigned as editor.  
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

## Implementation

*Implementation may or may not be done by the people who made the proposal.*

Once fully reviewed and accepted, the editor moves the Proposal from Discussions to Issues. Based on this new issue (which can be labeled as “new benchmark module”), describing the finalized Proposal, the module can be implemented and documented in the ProteoBench codebase. Finally, a pull request (PR) can be opened.

After two positive code reviews by ProteoBench maintainers, the PR can be merged. The PR MUST meet the following requirements:
1. Proper documentation of the benchmarking module
2. Proper documentation of the code
3. All code should follow Black styling
4. The latest commit of the PR should pass the continuous integration tests

## Beta

When the PR is merged, the new module enters a beta stage, where its code base is part of the Python package, and it is present on the web platforms. However, a prominent banner states that the module is still in “Beta”. After a minimal period of one month and approval by the initial proposers and external reviewers, the beta label can be removed.

## Live

The benchmark module is accessible to the community without restriction.

## Archived

Benchmark modules that are still valid but superseded by a better alternative. We still display the module on the web platforms and in the stable code base, but do not accept new reference runs anymore. A banner is also displayed, stating the status.

## Withdrawn

Benchmark modules that in hindsight proved to be flawed in any way and should no longer be used in any context. Code is removed from the Python package, and the module and its results are removed from the web platforms.
