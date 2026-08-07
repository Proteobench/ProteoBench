# Propose a module

Anyone can start a discussion or formally propose a new benchmark module.

Open a [discussion on GitHub](https://github.com/orgs/Proteobench/discussions/new?category=potential-new-module-to-discuss)
using the template. At least one expert, independent from both the existing ProteoBench
contributors and the proposal submitters, should be contacted for input. If a module is developed
and released before that happens, it carries a visible "Alpha" caution banner (see
[Module lifecycle](../concepts/module-lifecycle.md)) until external expert input is obtained.

## Sending a new module proposal

Open a [discussion on GitHub](https://github.com/orgs/Proteobench/discussions/new?category=potential-new-module-to-discuss)
with the following information:

1. **Description of the new module**: which aspect(s) of proteomics data analysis is benchmarked,
   and its added value compared to existing modules.
2. **Input data**: a persistent identifier for the dataset (PXD or DOI — publish to Zenodo first if
   one doesn't exist yet), optionally a DOI for the dataset publication, which subset is used (if
   any) and why, and why this dataset was selected.
3. **Workflow output data**: the data to be uploaded to ProteoBench for metric calculation.
4. **Minimal information needed from the workflow** for metric calculation — an existing
   (standardized) file format, or a simple, well-described CSV.
5. **Structured metadata**: which information is needed to sufficiently describe each benchmark
   run (e.g. workflow parameters).
6. **Metrics**: a description of the benchmark metrics and the methodology for calculating them.
7. **A single visualization** showing the metric for each benchmark run (a mock figure is fine).
8. **External experts**: optionally, propose at least two experts who didn't participate in the
   module's design. They can give input and/or fully collaborate on design and development.
9. Whether you can implement the module yourself, with help from ProteoBench maintainers.

Label the discussion "to be discussed" so the community knows it's under review.

## Before starting development

Email at least one expert who can give feedback on:

- whether specific metrics would be better tailored to the module's objective
- biases not accounted for in the proposal
- whether the proposed data suits the module's aim
- what workflow runs (tools, parameters) should be included when the module is released

A template for this email is
[available here](https://github.com/Proteobench/ProteoBench/tree/main/docs/templates_emails_module_proposal/first_request_expert_opinion.txt) —
CC `proteobench@eubic-ms.org`. Ask experts to respond within two weeks. If an expert accepts, all
further discussion happens publicly on GitHub (a follow-up email template is linked below).

## Start development

When development starts, switch the proposal's label to "under development", or move it from
Discussions to Issues (labeled "new benchmark module"). Based on the finalized proposal, implement
and document the module in the codebase, then open a pull request. If an expert contributed early,
list them as a module contributor and mention them in related communications; keep discussion
public on GitHub.

The PR can be merged after two positive code reviews by ProteoBench maintainers, and must:

1. Properly document the benchmarking module.
2. Properly document the code.
3. Follow Black styling.
4. Pass CI on its latest commit.

## When the module is released

**If no discussion was started with an external expert yet, contact one now.** Email at least one
expert covering the same questions as above, plus:

- how clear the module is overall
- how clear the documentation is

Give the expert access to an online version of the module and ask for a response within two weeks.
A template is
[available here](https://github.com/Proteobench/ProteoBench/tree/main/docs/templates_emails_module_proposal/second_request_expert_opinion.txt) —
CC `proteobench@eubic-ms.org`. If they accept, keep discussion public on GitHub.

## Sending details to an expert who accepts

When an expert agrees to give input, send them instructions for creating a GitHub account and
commenting on the discussion. A template is
[available here](https://github.com/Proteobench/ProteoBench/tree/main/docs/templates_emails_module_proposal/help_for_contributing_expert.txt) —
CC `proteobench@eubic-ms.org`.
