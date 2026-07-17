#######
Modules
#######

A benchmark module compares data analysis workflows on one specific task, using a fixed input
dataset and a fixed set of metrics. Because each module defines exactly what goes in and how
results are scored, it only ever evaluates the characteristics that dataset and those metrics can
speak to — no single module tells you everything about a workflow.

Every module page includes:

- links to the raw data and (where relevant) the sequence database
- which output files to upload, and any tool-specific setup required
- suggested search parameters (a starting point — you don't have to match them exactly)
- what the module is meant to measure, and how the metric is calculated
- how to read the results

Modules are grouped below by acquisition mode. Jump into a module's web app directly, or read its
documentation first if you're not sure it's the right fit.

.. toctree::
    :maxdepth: 2

    dda/index
    dia/index

Downloading benchmark data
===========================

Every module's raw input data, together with the intermediate scoring file for each public
submission, is available for download from the `ProteoBench data server
<https://proteobench.cubimed.rub.de/datasets/>`_. From a module's web app page, use "Download raw
datasets" to pick a specific analysis and download its data.
