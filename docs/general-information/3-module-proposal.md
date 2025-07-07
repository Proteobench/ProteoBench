# How to propose/discuss a new module

Anyone can start a discussion or more formally propose new module.

Proposals can be started by opening a [discussion on GitHub](https://github.com/orgs/Proteobench/discussions/new?category=potential-new-module-to-discuss), using a specific template. 
At least one expert, independent from both existing ProteoBench contributors and from the proposal submitters, should be contacted to give input on the proposal. If the module is developed and released before this is done, it will contain a very visible "caution" banner that will only be removed after getting input for external expert(s). You will find below how we propose expert input to be requested and at what stage. 

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

## Before starting the development

We advise to send an email to minimum one expert that can provide feedback on the proposal such as:

* Would some specific metrics be better tailored to the module objective?
* Are there some biases that are not accounted for in the proposal?
* Is the proposed data well suited for the aim of the module?
* What workflow runs (tools, parameters) should be included in the comparison when we release the module?

**A template for this email can be found [here](https://github.com/Proteobench/ProteoBench/tree/main/docs/templates_emails_module_proposal/first_request_expert_opinion.txt). Please put proteobench@eubic-ms.org in CC.**
We ask in the email that expert(s) answer within two weeks. If an expert accepts to contribute, all discussions should take place publicly on GitHub (an email template to send to expert(s) after they accept to contribute is available at the bottom of this document).

Switch to the label "waiting for expert input". It can be switched to "under development" after discussions with expert(s). In such case, experts should be listed as contributors of the module and mentionned in all communications about it. Discussions should take place publicly on GitHub. 

## When the module is released 

**If there is no discussion started with an external expert, please contact one at this stage.**

Send an email to minimum one expert that can provide feedback on the proposal such as:

* Would some specific metrics be better tailored to the module objective?
* Are there some biases that are not accounted for in the proposal?
* Is the proposed data well suited for the aim of the module?
* What workflow runs (tools, parameters) should be included in the comparison when we release the module?
* How clear is the module overall?
* How clear is the documentation?

Expert(s) should have access to an online version of the module, we ask that they signify they acceptance/refusal within two weeks. 
**A template for this email can be found [here](https://github.com/Proteobench/ProteoBench/tree/main/docs/templates_emails_module_proposal/second_request_expert_opinion.txt). Please put proteobench@eubic-ms.org in CC.** If an expert accepts to contribute, all discussions should take place publicly on GitHub (find below an email template to send to expert(s) after they accept to contribute).

# Information to send to experts when they accept to give inputs

When an expert accepts to contribute to the discussion of a new module, the coordinator should send them a detailed description on how to create a github account and comment in the discussion. **A template for this email can be found [here](https://github.com/Proteobench/ProteoBench/tree/main/docs/templates_emails_module_proposal/help_for_contributing_expert.txt). Do not forget to put proteobench@eubic-ms.org in CC.**
