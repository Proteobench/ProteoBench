# How to propose/discuss a new module

Anyone can start a discussion or more formally propose new module.

Proposals can be started by opening a [discussion on GitHub](https://github.com/orgs/Proteobench/discussions/new?category=potential-new-module-to-discuss), using a specific template. One of the ProteoBench maintainers will be assigned as editor.  
At least one expert, independent from both existing ProteoBench contributors and from the proposal submitters, should be contacted to give inputs on the proposal. It needs to be done when the module is ready for release, we also recommand to do it before starting development.

## Sending a new module proposal

Open a [discussion on GitHub](https://github.com/orgs/Proteobench/discussions/new?category=potential-new-module-to-discuss) with the following information:

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
8. **External experts**: Optionally propose at least two experts who did not participate to the full design of the module proposed. They can choose to give inputs and/or can fully collaborate to the module design and/or development.
9. Will you be able to work on the implementation (coding) yourself, with additional help from the ProteoBench maintainers?

Use a label "to be discussed" so that the community knows that the proposal is under discussion.

## Before starting the development (OPTIONAL)

Send an email to minimum one expert that can provide feedbacks on the proposal such as:

* Would some specific metrics be better tailored to the module objective?
* Are there some biases that are not accounted for in the proposal?
* Is the proposed data well suited for the aim of the module?
* What workflow runs (tools, parameters) should be included in the comparison when we release the module?

**A template for this email can be found here(TODO). Please put proteobench@eubic-ms.org in CC.**

If they accept to help out, experts should be listed as contributors of the module. 
**A template for this email can be found here(TODO). Please put proteobench@eubic-ms.org in CC.**
This email template(TODO) can be sent to them to explain how they can contribute to the module proposal discussion. 

Switch to the label "waiting for expert input".

## When the module is ready to be released (MANDATORY)

Send an email to minimum one expert that can provide feedbacks on the proposal such as:

* Would some specific metrics be better tailored to the module objective?
* Are there some biases that are not accounted for in the proposal?
* Is the proposed data well suited for the aim of the module?
* What workflow runs (tools, parameters) should be included in the comparison when we release the module?
* How clear is the module overall?
* How clear is the documentation?

Expert(s) should have access to an online version of the module. 
**A template for this email can be found here(TODO). Please put proteobench@eubic-ms.org in CC.**

Switch to the label "needs approval for release".