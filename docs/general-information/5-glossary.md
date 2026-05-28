# Glossary

We adopted the ontology proposed by [PSI-MS](https://github.com/HUPO-PSI/psi-ms-CV/blob/master/psi-ms.obo). 
Here are the terms specific to ProteoBench:

## Benchmark module
A benchmark module compares the performance of different data analysis workflows based on module-specific, predefined metrics. It provides a specific set of input files (e.g., mass spectrometry files and a sequence database) and it requires specific workflow output files (e.g., identified peptides). Based on these workflow output files, metrics are calculated as defined by the module and can be compared to previously validated benchmark runs. As each benchmark module defines specific workflow input files and metrics, it evaluates only a limited set of characteristics of the data analysis workflow.

## Metric
A single number resulting from an aggregated calculation of the workflow output which allows for a comparison between different benchmark runs.

## Workflow
A combination of data analysis tools with associated parameters that takes workflow input files (provided by a benchmark module) and generates workflow output files. Based on the workflow output files, metrics can be calculated describing the workflow performance.

## Benchmark run
The result of running a workflow with specific parameter values and calculating the benchmark metrics based on the workflow output. 

## Workflow metadata
A set of parameter values (e.g., missed cleavages, mass tolerance), workflow properties (e.g., software name, software version), and workflow configuration files that include all information required to fully understand and re-execute a given workflow. This should include the workflow options, as well as a detailed description of the click sequence and/or potential supplemental parameters unique to the workflow.

### Structured workflow metadata
A fixed set of metadata to be provided through a form with every benchmark run that is submitted for validation. 

### Unstructured workflow metadata
Additional metadata that is specific to a workflow and can therefore not be presented in a structured submission form and requires a free-form text field instead. The metadata does not need to be written as full text, but should be fully comprehensible.

## Workflow configuration files
Files that contain parameters for a workflow or for a data analysis tool within a workflow. These files can be specific to the workflow or to the data analysis tool and help to re-execute it with the same parameters (e.g., mqpar.xml).

## Validated benchmark run
A benchmark run accepted by the ProteoBench team to be made publicly available as part of the ProteoBench repository. For validation, the submission must include the workflow output files, structured metadata, unstructured metadata, and (if applicable) workflow configuration files. The workflow metadata must include all information needed to fully understand and re-execute the workflow; i.e., the benchmark run must be fully reproducible. 
