# Frequently asked questions

## What is ProteoBench?
ProteoBench is an open and collaborative platform for community-curated benchmarks that enables continuous, easy, and controlled comparison of proteomics data analysis workflows.

It provides a centralized web platform where developers and end-users can compare proteomics data analysis {ref}`workflows<workflow>` using standardized benchmark datasets, transparent evaluation metrics, and public comparison plots. This community-curated effort supports the controlled evaluation of tools developed or used by participants against other state-of-the-art workflows for specific proteomics applications. The ability to add new benchmark runs and modules allows ProteoBench to grow with the proteomics field. (See our goals and non-goals [here](../general-information/0-about.html#goals-and-non-goals))

The goal of ProteoBench is not to select or prescribe a single best one-size-fits-all data analysis workflow. Instead, ProteoBench aims to make workflow evaluation more transparent, reproducible, and comparable across tools, laboratories, software versions, and use cases.

## Who is ProteoBench intended for?

ProteoBench is intended for several user groups involved in the development, evaluation, or application of proteomics data analysis workflows.
For **end-users**, ProteoBench helps identify suitable workflows for specific analytical needs by allowing comparison with public reference results and state-of-the-art pipelines. This includes proteomics researchers, experimental laboratories, and core facilities that want to evaluate, document, or monitor routine analysis workflows.
For **end-users**, ProteoBench helps identify suitable workflows for specific analytical needs by allowing comparison with public reference results and state-of-the-art pipelines. This includes proteomics researchers, experimental laboratories, and core facilities that want to evaluate, document, or monitor routine analysis pipelines.

For **software and method developers**, ProteoBench provides a framework to identify the specific strengths and weaknesses of workflows, algorithms, software versions, or parameter choices. These insights can guide further development and support the contribution of new benchmark modules for emerging proteomics applications.

For the **wider proteomics community**, ProteoBench makes it easier to position newly published workflows within the context of the existing state of the art. It can therefore support reviewers, editors, and readers who require transparent evidence for claims about workflow performance.

## Do I need to run my workflow on a predefined data set?

Yes. To compare results meaningfully within a ProteoBench module, all submitted workflows must be evaluated on the benchmark dataset defined for that module. This ensures that differences between submitted results reflect differences in data analysis workflows rather than differences in sample composition, instrument configuration, acquisition design, or data quality.

Users who want to benchmark a different experimental design can contribute or request a new module. ProteoBench is modular by design, so new datasets, metrics, and use cases can be added as the community’s needs evolve.

## Do I need to use the exact same workflow parameters as other users?

No. ProteoBench does not require all users to run identical workflow parameters. In many modules, suggested parameters are provided to help users get started and to support comparable baseline analyses, but users may submit results generated with their own parameter choices.
The parameters used for all the public {ref}`benchmark runs <benchmark-run>` are collected upon submission and fully available to download so that users can interpret differences in performance in the context of software versions, workflow settings, search databases, quantification options, and other relevant configuration details. If you 'limit test' a specific parameter, we recommend documenting that in the comment field when you submit your benchmark run for public release.

## Do I need to use a specific FASTA database?
For modules where database choice affects the benchmark outcome, the recommended or required FASTA database is specified in the module documentation. Using the same database ensures that submitted results are comparable.
For modules where database choice affects the benchmark outcome, the recommended or required FASTA database is specified in the module documentation. Using the same database helps ensure that submitted results are comparable.

## Can I benchmark commercial software?
Yes. ProteoBench is designed to include results from commercial software when the software outputs all the workflow parameters/metadata in a format that can be parsed or converted into one of the supported submission formats. 
Yes. ProteoBench can include results from commercial software when the software output can be parsed or converted into one of the supported submission formats. 

## What should I do if my software is not directly supported?

If a tool-specific parser is not yet available, users can submit results using the custom tabular format described in the module documentation. This format defines the required columns for metric calculation and enables benchmarking of tools that are not yet natively supported.

Users and developers are encouraged to contact the ProteoBench community if they want a new parser to be added for a specific software package.

## Why are submissions reviewed before becoming public?

Manual review is used as a quality-control step to keep public benchmark results interpretable and reliable. The review process helps detect incomplete submissions, incorrect file types, incompatible module choices, missing metadata, or results that cannot be meaningfully compared with existing entries.

## Does ProteoBench run my workflow automatically?

ProteoBench evaluates submitted workflow outputs rather than executing every workflow centrally. Users download the benchmark data provided for their module of interest, process it with their local software or pipeline, and upload the relevant output files.

This design allows ProteoBench to support a wide range of tools, including commercial software, locally configured pipelines, and workflows under active development. 

## How do I find the input data associated with a benchmark module?
Each module provides a clear route to the required benchmark files, including raw MS files, search databases when applicable, example outputs, and documentation. The raw data are typically linked from the module documentation or from public repositories such as [ProteomeXchange](https://www.proteomexchange.org/), depending on the dataset.
Each module provides a clear route to the required benchmark files, including raw MS files, search databases when applicable, example outputs, and documentation. The raw data are typically linked from the module documentation or from public repositories such as ProteomeXchange, depending on the dataset.
If you do not find the information that you need to run your workflow, don't hesitate to contact us.

## What is QuantError?

QuantError is a module-specific metric used to assess quantitative accuracy when the expected abundance ratios are known. It compares observed quantitative values against expected values and summarizes how far a workflow deviates from the known experimental design.

QuantError should be interpreted together with the other module-specific metrics. A workflow that reports many quantified features is not necessarily optimal if the quantitative error is high.

## Does ProteoBench perform normalization or missing-value imputation?

ProteoBench does not apply post-processing steps that may affect the benchmark metrics. We consider normalization, missing-value handling, transfer steps, protein inference, and quantification strategies as integral parts of benchmarked workflows. They should be reported in the parameter files submitted alongside the workflow results upon public submission.

Where relevant, module documentation specifies which processing steps are performed by ProteoBench itself and which are expected to have been performed by the submitted workflow.
## How can I interpret differences between {ref}`benchmark runs <benchmark-run>`?

ProteoBench provides standardized metrics and visualizations that make differences between workflows visible. These differences may arise from many factors, including feature detection, spectral library generation, identification scoring, false discovery rate control, match-transfer strategies, normalization, missing-value handling, quantification algorithms, and software-specific defaults.

ProteoBench results should therefore be interpreted as workflow-level comparisons, not only as comparisons of individual algorithms. Where possible, users should inspect both the software version and the reported parameters before drawing conclusions.

## Does ProteoBench validate false discovery rates independently?

False discovery rate control is a central concern in proteomics benchmarking. ProteoBench modules can incorporate FDR-related analyses when appropriate datasets and metrics are available. Independent validation strategies, including entrapment-based approaches, are especially relevant for workflows where reported identifications and quantification accuracy depend strongly on tool-specific error-control procedures.

## How should I interpret the main plots in each module?

ProteoBench comparison plots should not be interpreted as universal rankings of software tools. A tool that performs well in one module, with one dataset or metric, may not be optimal for another biological question, instrument type, acquisition method, or analysis goal.



Users should consider:

- The benchmark module and dataset.
- The software version.
- The submitted parameters (e.g. FDR)
- The relevant metric definitions.
- The trade-off between sensitivity and accuracy.
- Whether the workflow resembles their own intended use case.

ProteoBench is best used as a transparent decision-support resource rather than as a single definitive ranking system.
ProteoBench does not point to a single best one-fits-all data analysis workflow; should not be used as evidence for generalized statements about a workflow’s performance, and should not be used by developers as single performance measure of their workflow.

## How can I follow updates or community discussions?

Ongoing discussions can be followed on the [ProteoBench Discussions page](https://github.com/orgs/Proteobench/discussions). Please not that to take part in the discussion a GitHub account is needed.

## How can I follow ProteoBench development and community discussions?

ProteoBench development and discussion are community-oriented. Users can follow the relevant repository, documentation pages, discussion forum, or community channels to receive updates about new modules, software parsers, benchmark datasets, documentation improvements, and public releases.

### For GitHub users

GitHub users can follow ProteoBench development through the main [ProteoBench GitHub repository](https://github.com/Proteobench/ProteoBench). This repository contains the source code, contribution information, issue tracking, and release history. Users who want to receive updates can watch or star the repository. If you are interested in a specific module, you can also watch the corresponding result repository listed [here](https://github.com/Proteobench).

Questions, proposals, and module-specific discussions can be followed through the [ProteoBench GitHub Discussions](https://github.com/Proteobench/ProteoBench/discussions) forum. This is the preferred route for users who want to participate in technical discussions, suggest new benchmark modules, discuss parser development, or contribute to the platform. Through this route, users can also register for discussion updates.

### For non-GitHub users

Users who do not use GitHub can follow ProteoBench through the [ProteoBench web application](https://proteobench.cubimed.rub.de/) and the [ProteoBench documentation](https://proteobench.readthedocs.io/en/stable/). These resources provide access to the public benchmark modules, available datasets, workflow comparison results, and user-facing documentation.

Community discussion also takes place through the [EuBIC-MS Slack workspace](https://eubic.slack.com/). Users can join the relevant ProteoBench channel there to ask questions, follow community updates, and discuss benchmark modules or workflow comparisons without requiring a GitHub account. More information about the EuBIC-MS community is available on the [EuBIC-MS website](https://eubic-ms.org/). We also have a [LinkedIn page](https://www.linkedin.com/company/proteobench/) where we post updates regarding the project.


## How can I contribute to ProteoBench?

Users can contribute by submitting their workflow outputs, reporting issues, improving documentation, proposing new modules, contributing parsers for additional software tools, sharing tutorial material, or participating in community discussions.

New benchmark modules are especially valuable when they address a clear community need, provide well-documented datasets, define appropriate metrics, and include example workflows that allow other users to reproduce or compare results.
