###############
Developer guide
###############

.. toctree::
    :caption: Getting started
    :maxdepth: 3
    :hidden:

    development-setup
    local-usage
    modifying-module
    reviewing-new-point-pr
    changelog

.. toctree:: 
    :caption: Architecture and new modules
    :maxdepth: 2
    :hidden:

    repo_layout
    adding-module
    
    modules/index

.. toctree::
   :caption: Python API
   :glob:
   :maxdepth: 3
   :hidden:

   api/proteobench/proteobench
   api/webinterface/webinterface


Organization
============

The ProteoBench project is divided into two main parts:

Modules for Data Processing and Reporting
-----------------------------------------
These :ref:`proteobench` process the data and generate reports.

Web Interface for Result Visualization
--------------------------------------
The :ref:`webinterface` displays the results and allows
comparison with publicly available data.
