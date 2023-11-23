###################
Adding a new module
###################

Please use the template for adding a new benchmarking module.

Here we provide a comprehensive overview of how to set up a new module in ProteoBench


Naming convention
=================

We suggest to understand the following terms as they are crucial components:

    **Module**: All code and definitions for creating and comparing benchmarks of a new data type

    **Intermediate data structure** (`DataFrame`): Data structure needed for the calculation of the `datapoint`. It contains
    the transformed and annotated data of an uploaded data file.

    **Datapoint**: Metadata and benchmarking metrics for a given data set. A `datapoint` is the
    data needed for the benchmarking and should also be represented by a json object.


Programmatic structure
======================

The modules are located in the `proteobench/modules <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules>`\_ directory. We separated the benchmarking modules into a different steps
that allow for a more modular and portable implementation.

**Backend**

Each module implementation should contain the following classes:

1. :func:`~proteobench.modules.template.module.Module` contains the main functions reading the and processing the uploaded data set, generating the _intermediate_ structure and creating the _datapoint_, as well as adding it to our collection of _datapoints_.
2. :func:`~proteobench.modules.template.parse.ParseInputs` interfaces with the Streamlit interface providing formatting parameter definitions to create a standardized format from the uploaded files with respect to the given file format (e.g. MaxQuant output file)
3. :func:`~proteobench.modules.template.datapoint.Datapoint` is the data structure of _Datapoint_. It contains data set properties from the acquisition and processing (e.g. used peptide fdr) and functions to calculate the benchmarking metrics.
4. :func:`~proteobench.modules.template.plot.PlotDataPoint` are the functions to visualize the benchmarking metrics from the data points.
5. :func:`~proteobench.modules.template.parse.ParseInputs` contains the functions to parse the uploaded data files into the _intermediate_ structure. The input file parameters should be defined in the toml file like `proteobench/modules/template/io_parse_settings/parse_settings_format1.toml <https://github.com/Proteobench/ProteoBench/blob/main/proteobench/modules/template/io_parse_settings/parse_settings_format1.toml>`\_.

**Web interface**

The web interface is written in Streamlit. Each module gets assigned a specific "page".
There are only few changes necessary as the main calculations are done in

:func:`~webinterface.pages.TEMPLATE.StreamlitUI` contains the functions to create the web interface for the module.

_Relevant functions:_

:func:`~webinterface.pages.TEMPLATE.StreamlitUI.generate_input_field` creates the input fields for the metadate and the
input file format and type. They are given by in the `proteobench/modules/template/io_parse_settings <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules/template/io_parse_settings>`\_ folder,
same as for the backend of the module.

:func:`webinterface.pages.TEMPLATE.StreamlitUI.generate_results` gathers the data from the backend
and displays them in several figures. Here you will need to edit and adapt the code
to show the respective figures with the right metadata.

:func:`webinterface.pages.TEMPLATE.WebpageTexts` contains the text for the different parts of the web interface.

Change the text and the field names accordingly

**Documentation**

We strongly recommend to keep documenting your code. The documentation is written in Sphinx and
can be found in the `docs <https://github.com/Proteobench/ProteoBench/tree/main/docs>`\_ folder.

1.  `docs/proteobench/modules.rst <https://github.com/Proteobench/ProteoBench/tree/main/docs/proteobench/modules.rst>`\_ Here you can add a link to your new module
2.  `docs/proteobench/template.rst <https://github.com/Proteobench/ProteoBench/tree/main/docs/proteobench/template.rst>`\_ This template can be used to creat your own documentation file in reStructuredText (rst) format.
3.  `docs/webinterface/webinterface.rst <https://github.com/Proteobench/ProteoBench/tree/main/docs/webinterface/webinterface.rst>`\_ Here you should add a link to the new page in the web interface.

To work on the documentation and get a live preview, install the requirements and run
`sphinx-autobuild`:

.. code-block:: sh

    pip install .[docs]
    sphinx-autobuild  --watch ./ms2rescore ./docs/source/ ./docs/_build/html/

Then browse to http://localhost:8000 to watch the live preview.

.. note::

    Ensure to have changed all occurrences of ``template`` to the name of your new module.


Checklist
=========

This checklist is meant to help you add a new module to ProteoBench. It is not
meant to be exhaustive, but it should cover the most important steps.

1. Copy the `template <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modulestemplate>`_
   folder in the `proteobench/modules <https://github.com/Proteobench/ProteoBench/tree/main/proteobench/modules>`_
   directory to a new folder in the same directory. The name of the new directory should be the name
   of the module.
2. Define the input formats in the toml files of the `proteobench/modules/my_module/io_parse_settings`
   directory and `proteobench.modules.my_module.parse_settings.py`.
3. Modify the upload prodecures in the `proteobench/modules/my_module/parse.py`. This will ensure a
   standardized data structure for the benchmarking independently from the input file format.
4. Modify `proteobench/modules/my_module/datapoint.py` to define the requested metadata about the
   data acquisition and the benchmarking metrics, all to be stored in a datapoint. You might need to
   add some function(s) for further processing the standardized data structure.
5. Modify `proteobench/modules/my_module/plot.py` to create the figures for the web interface.
6. Modify `proteobench/modules/my_module/module.py` to harmonize all procedures called in the
   `benchmarking` function.
7. Copy `webinterface.pages.TEMPLATE <https://github.com/Proteobench/ProteoBench/tree/main/webinterface/pages/TEMPLATE>`\_
   to `webinterface.pages.my_module` and modify the functions to display the figures. Adapt the code
   according to ensure loading the right figures and data points.
8. Copy :doc:`api/proteobench/template` to
   `developer-guide/api/proteobench/my_module` and modify the documentation accordingly. Add entries
   to :doc:`api/proteobench/modules/index` and :doc:`api/webinterface/index`
