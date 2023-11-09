============================
Modifying an existing module
============================

We recommend keeping the given structure in a module.

_For adding new input file types_: Use the :func:`~proteobench.modules.template.ParseInputs` class to define the parsing of the input files and a specific toml file for its layout.

_For adding new benchmarking metrics_: Add the new metrics to the ``datapoint.py`` file and the ``plot.py`` file for visualization.

_Note_ that changing the intermediate format and the data point structure might have an impact on the other modules. Therefore we recommend
to define them stringently from the start.
