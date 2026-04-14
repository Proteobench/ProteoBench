============================
Modifying an existing module
============================

We recommend keeping the given structure in a module.

For adding new input files from data analysis softwares, i.e. a new tool to 
an existing benchmark module, you will need to:

- add a toml file for the tool parsing
- add a parameter parsing function for the tool
- extend the documentation of the module for instruction of the new tools

For adding new benchmarking metrics, you would need to add the new metrics to
the ``datapoint.py`` file and the ``plot.py`` file for visualization. In that
case have a look at the extended documentation of adding a new module,
:ref:`Adding a new module`.

As an example for adding a new tool, see how quantms was added to the DDA quantification
precursor ions module in
`PR #550 <https://github.com/Proteobench/ProteoBench/pull/550/files>`_.

.. note::

    Note that changing the intermediate format and the data point structure might
    have an impact on the other modules. Therefore we recommend
    to define them stringently from the start - not changing them later on.
