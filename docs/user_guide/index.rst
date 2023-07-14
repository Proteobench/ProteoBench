###########
User guide
###########

Welcome to the user guide of ProteoBench.

*****************
Installation
*****************


ProteoBench can be installed as Python package using the usual pip command:

.. code-block:: bash

    pip install proteobench

or, without pip, by cloning the repository and running the setup script:

.. code-block:: bash

    git clone https://github.com/Proteobench/ProteoBench
    cd proteobench
    python setup.py install


********************************
Local usage
********************************






********************************
Development
********************************



=======================
Adding a new modules
=======================

Here we provide a (hopefully) comprensive documentation of how to set up a new module in ProteoBench

-----------------------
Naming convention
-----------------------

We suggest to understand the following terms as they are crucial components:

_module_ All code and definitions for creating and comparing benchmarks of a new data type

_datapoint_ Metadata and benchmarking metrics for a given data set. A `datapoint` is the 
data needed for the benchmarking and should also be represented by a json object.

_intermediate_ Intermediate data structure (`DataFrame`) needed for the calculation of the `datapoint`. It contains 
the transformed and annotated data of an uploaded data file.


-----------------------
Programmatic structure
-----------------------

TODO: something weird with the structure

Each module implementation should contain the following classes:

1. :py:meth:`~proteobench.modules.template.ModuleInterface` contains the main
functions reading the and processing the uploaded data set, generating the _intermediate_ structure and 
creating the _datapoint_, as well as adding it to our collection of _datapoints_.

2. :py:meth:`~proteobench.modules.template.ParseInputsInterface` interfaces with the Streamlit interface providing
formatting parameter definitions to create a standardized format from the uploaded files with respect to the given file format (e.g. MaxQuant output file)

3. :py:meth:`~proteobench.modules.template.datapoint` TODO data structure of _datapoint_. Contains data set properties from 
the acquisition and processing (e.g. used peptide fdr) and functions to calculate the benchmarking metrics. 

4. :py:meth:`~proteobench.modules.template.plot` TODO

5. :py:meth:`~proteobench.modules.template.ParseInputs` TODO

-----------------------
Checklist
-----------------------


This checklist is meant to help you add a new module to ProteoBench. It is not
meant to be exhaustive, but it should cover the most important steps.

1. Copy the `template` folder in the `proteobench/modules` directory to a new
   folder in the same directory. The name of the new
   directory should be the name of the module. 

2. Create a new file called `__init__.py` in the directory you just created.

3. Create a new file called `my_module.py` in the directory you just created.
   This file will contain the code of your module.

4. Create a new file called `my_module_test.py` in the directory you just
    created. This file will contain the tests for your module.

5. Create a new file called `my_module_doc.py` in the directory you just
    created. This file will contain the documentation for your module.

6. Create a new file called `my_module_config.py` in the directory you just



================================
Modifying an existing module
================================
