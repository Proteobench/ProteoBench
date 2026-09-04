# Glossary

ProteoBench follows the ontology proposed by
[PSI-MS](https://github.com/HUPO-PSI/psi-ms-CV/blob/master/psi-ms.obo). Below are terms specific to
ProteoBench.

## Benchmark module

Compares the performance of different data analysis workflows using module-specific, predefined
metrics. It provides a specific set of input files (e.g. mass spectrometry files and a sequence
database) and requires specific workflow output files (e.g. identified peptides). Metrics are
calculated from those output files as defined by the module, and can be compared to previously
validated benchmark runs. Because each module defines specific inputs and metrics, it evaluates
only a limited set of workflow characteristics.

(benchmark-run)=
## Benchmark run

The result of running a workflow with specific parameter values and calculating the benchmark
metrics from the workflow output.

### Validated benchmark run

A benchmark run accepted by the ProteoBench team to be made publicly available. Validation
requires the workflow output files, structured metadata, unstructured metadata, and (if
applicable) workflow configuration files. The metadata must include everything needed to fully
understand and re-execute the workflow — the run must be fully reproducible.

## Metric

A single number resulting from an aggregated calculation of the workflow output, allowing
comparison between benchmark runs.

## Intermediate format

The module-specific standardized table ProteoBench computes from a workflow output before
deriving metrics. Stored as `result_performance.csv` and identified by the `intermediate_hash`. See
[Intermediate format](intermediate-format.md) for the full specification.

(open-source-software)=
## Open source software

A tool is considered open source if its code is publicly available in its latest version,
whatever the license.

## Workflow

A combination of data analysis tools and their parameters that takes workflow input files
(provided by a benchmark module) and produces workflow output files. Metrics describing workflow
performance are calculated from those output files.

## Workflow configuration files

Files containing parameters for a workflow or a data analysis tool within it. These help
re-execute the workflow with the same parameters (e.g. `mqpar.xml`).

## Workflow metadata

Parameter values (e.g. missed cleavages, mass tolerance), workflow properties (e.g. software name
and version), and workflow configuration files sufficient to fully understand and re-execute a
workflow — including a description of the click sequence and/or supplemental parameters unique to
the workflow.

### Structured workflow metadata

A fixed set of metadata provided through a form with every benchmark run submitted for validation.

### Unstructured workflow metadata

Additional metadata specific to a workflow that can't fit a structured form, provided as free-form
text instead. It doesn't need to be full prose, but should be fully comprehensible.
