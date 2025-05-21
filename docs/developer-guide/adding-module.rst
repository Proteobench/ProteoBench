#################################
Adding a new quantification module
#################################

Here we provide a comprehensive overview of how to set up a new module in ProteoBench,
currently focused on quantification modules. As more module types are added, we might need
to create a verson of this page for non-quant modules.


Terms
=====

The following terms capture the crucial components:

   *Module*: All code and definitions for creating and comparing
   benchmarks of a new data type.

   *Intermediate data structure* (:class:`DataFrame`): Data structure needed for the
   calculation of the ``datapoint``, e.g. :class:`QuantDatapoint`. It contains
   the transformed and annotated data of an uploaded data file.

   *Datapoint*: Metadata and benchmarking metrics for a given data set. A ``datapoint``, e.g. :class:`QuantDatapoint`,
   is the data needed for the benchmarking and should also be represented by a json object.

Naming convention
=================

New modules and classes should be given descriptive names, and fit into existing naming schemes.
Go from general to specific properties, and make clear what distinguishes the module 
from existing ones, e.g. :class:`DIAQuantPeptidoformModule`.

The modules are stored in the Python package ``proteobench`` in the
``modules`` subpackage: `proteobench.modules <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules/quant/>`_. 

Programmatic structure
======================

The modules are located in the 
`proteobench/modules <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules>`_ 
directory. We separated the benchmarking modules into a different steps
that allow for a more modular and portable implementation.

Backend
------- 

We make an example of an ``quant`` module implementation, where you should use or extend
certain classes and do the following steps:

1. :class:`~proteobench.modules.quant.quant_base_module.QuantModule` contains the main functions reading 
   the and processing the uploaded data set, generating the *intermediate* metric structure
   and creating the ``datapoint``, as well as adding it to our collection of ``datapoints``.
   You can subclass it and implement the ``benchmarking`` method and the ``is_implemented``
   method, initializing it with custom parameters in the ``__init__`` method.
2. Functions in :file:`proteobench/io/parsing/parse_ion.py` provide the functions used to parse
   precursor (`open on GitHub <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/parsing>`_)
3. :file:`~proteobench/io/parsing.io_parse_settings/parse_settings_file.toml` links the settings to 
   parse the uploaded data files into the **intermediate** metric structure used by
   :file:`proteobench/io/parsing/parse_ion.py` per module. The settings file 
   parameters should be defined in the toml file in a folder for a module 
   :file:`proteobench/io/parse/io_parse_settings/Quant/lfq/DDA/ion/`,
   for example
   `parse_settings_alphadia <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/parsing/io_parse_settings/Quant/lfq/DIA/ion/Astral/parse_settings_alphadia.toml>`_.
4. :class:`~proteobench.datapoint.quant_datapoint.QuantDatapoint` is the data structure 
   (as a dataclass)of :class:`DataPoint` for quant modules. It contains data set properties 
   from the acquisition and processing 
   (e.g. used peptide fdr).
5. :class:`~proteobench.plotting.plot_quant.PlotDataPoint` is the class with methods to visualize
   the benchmarking metrics from the ``DataPoints``.
6. Functions in :file:`proteobench/io/params` provide the functions used to parse
   parameter setting files for data analysis tools
   (`open on GitHub <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/parsing>`_)
7. The possibility to adapt the parsed results before submission is customized based on
   a module specific json file in
   `proteobench/io/params/json/Quant <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/params/json/Quant>`_

Web interface
-------------

The web interface is written in Streamlit. Each module gets assigned a specific ``page``.
There are only few changes necessary as the main calculations are done in

:class:`~webinterface.pages.base_pages.quant.QuantUIObjects` contains most functionionality to 
create the web interface for each quantification module.

.. warning::
   QuantUIObjects should be simplified.

:file:`webinterface.pages.pages_variables` contains files with ``dataclass``\ es for the 
text for the different modules in the interface.

Relevant functions in :class:`~webinterface.pages.base_pages.quant.QuantUIObjects`
...................................................................................

:meth:`~webinterface.pages.base_pages.quant.QuantUIObjects.generate_input_field` creates 
the input fields for the metadate and the
input file format and type. They are given by in the
`proteobench/modules/parsing/io_parse_settings <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules/io/io_parse_settings>`_ folder,
same as for the backend of the module.

:meth:`~webinterface.pages.base_pages.quant.QuantUIObjects.generate_results` gathers the data from the backend
and displays them in several figures. Here you will need to edit and adapt the code
to show the respective figures with the right metadata.

Change the text and the field names accordingly in the ``dataclass``
in `webinterface.pages.pages_variables <https://github.com/Proteobench/ProteoBench/tree/main/webinterface/pages/pages_variables>`_.

Documentation
-------------

We strongly recommend to keep documenting your code. The documentation is written in Markdown or richtext
and can be found in the `docs <https://github.com/Proteobench/ProteoBench/tree/main/docs>`_ folder. We
use Sphinx and myst-parser to build the website.

1. `docs/proteobench/available-modules <https://github.com/Proteobench/ProteoBench/tree/main/docs/proteobench/available-modules>`_
   Here you can add a file for your new module, using any of the existing module descriptions as a template.
2. `API documentation for your module <https://proteobench.readthedocs.io/en/latest/developer-guide/api/webinterface/webinterface.pages/#submodulest>`_ 
   will be added automatically. You can see it on the readthedocs page built specifically for your pull request.

To work locally on the documentation and get a live preview, install the requirements and run
`sphinx-autobuild`:

.. code-block:: sh

    pip install '.[docs]'
    # selecting the docs folder to watch for changes
    sphinx-autobuild  --watch ./docs ./docs/source/ ./docs/_build/html/

Then browse to http://localhost:8000 to watch the live preview.


Checklist
=========

This checklist is meant to help you add a new module to ProteoBench. It is not
meant to be exhaustive, but it should cover the most important steps. See one of the
recent examples of adding modules, e.g in
`PR 638 <https://github.com/Proteobench/ProteoBench/pull/638/files>`_
to see which files these authors had to add or modify.

1. Subclass :class:`~proteobench.modules.quant.quant_base_module.QuantModule` and replace
   the :func:`benchmarking` method with your own implementation. You can copy from other
   modules in the folder 
   `proteobench/modules <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules>`_
2. Define the input formats using toml files in a new subfolder of
   `proteobench/io/parsing/io_parse_settings <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/parsing/io_parse_settings>`_
3. Check, modify or add a parsing procedures in
   `proteobench/io/parsing <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/parsing>`_
   e.g. :file:`parse_ion.py` or :file:`parse_peptidoform.py`.
4. Check, modify or add datapoint classes to
   `proteobench/datapoint <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/datapoint>`_
   for storing the intermediate data structure.
5. Check, modify or add plotting classes to
   `proteobench/plotting <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/plotting>`_
   to create the figures for the web interface.
6. Check, modify or add parameter parsing for new tools in
   `proteobench/io/params <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/io/params>`_
7. Add a new page defining the module webinterface to
   `webinterface/pages <https://github.com/Proteobench/ProteoBench/tree/main/webinterface/pages>`_
   using the base functionality and adding ``pages_variables`` dataclasses.
