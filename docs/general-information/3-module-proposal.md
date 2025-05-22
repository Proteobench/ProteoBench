# How to propose/discuss a new module

Anyone can start a discussion or more formally propose new module.

Proposals can be started by opening a [discussion on GitHub](https://github.com/orgs/Proteobench/discussions/new?category=potential-new-module-to-discuss), using a specific template. 
At least one expert, independent from both existing ProteoBench contributors and from the proposal submitters, should be contacted to give input on the proposal. This needs to be done when the module is ready for release. We also recommend to do it before starting development.

## Sending a new module proposal

Open a [discussion on GitHub](https://github.com/orgs/Proteobench/discussions/new?category=potential-new-module-to-discuss) with the following information:

1. A **description of the new module**:
    - Which aspect(s) of proteomics data analysis is benchmarked?
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

## Before starting the development (MANDATORY)

Send an email to minimum one expert that can provide feedback on the proposal such as:

* Would some specific metrics be better tailored to the module objective?
* Are there some biases that are not accounted for in the proposal?
* Is the proposed data well suited for the aim of the module?
* What workflow runs (tools, parameters) should be included in the comparison when we release the module?

**A template for this email can be found [here](docs/templates_emails_module_proposal/first_request_expert_opinion.txt). Please put proteobench@eubic-ms.org in CC.**
We ask in the email that experts answer within two weeks. 

Switch to the label "waiting for expert input". It can be switched to "under development" after discussions with expert(s). In such case, experts should be listed as contributors of the module and mentionned in all communications about it. 

## When the module is ready to be released (MANDATORY if no expert aggreed to collaborate already)

Send an email to minimum one expert that can provide feedback on the proposal such as:

* Would some specific metrics be better tailored to the module objective?
* Are there some biases that are not accounted for in the proposal?
* Is the proposed data well suited for the aim of the module?
* What workflow runs (tools, parameters) should be included in the comparison when we release the module?
* How clear is the module overall?
* How clear is the documentation?

Expert(s) should have access to an online version of the module, we ask that they signify they acceptance/refusal within two weeks. 
**A template for this email can be found [here](docs/templates_emails_module_proposal/second_request_expert_opinion.txt). Please put proteobench@eubic-ms.org in CC.**

Switch to the label "needs approval for release".

# Information to send to experts when they accept to give inputs

When an expert accepts to contribute to the discussion of a new module, the coordinator should send them a detailed description on how to create a github account and comment in the discussion. **A template for this email can be found [here](docs/templates_emails_module_proposal/help_for_contributing_expert.txt). Do not forget to put proteobench@eubic-ms.org in CC.**