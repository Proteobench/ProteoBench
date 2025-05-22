============================
Modifying an existing module
============================

We recommend keeping the given structure in a module.

For adding new input files from data analysis softwares:

- add a toml file for the tool parsing
- add a parameter parsing function for the tool
- extend the documentation of the module for instruction of the new tools

For adding new benchmarking metrics: Add the new metrics to
the ``datapoint.py`` file and the ``plot.py`` file for visualization.


.. note::

    Note that changing the intermediate format and the data point structure might
    have an impact on the other modules. Therefore we recommend
    to define them stringently from the start.
