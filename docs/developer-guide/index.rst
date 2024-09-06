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
    changelog


.. toctree::
   :caption: Python API
   :glob:
   :maxdepth: 3
   :hidden:

   api/*/index


Organization
============

The ProteoBench project is divided into two main parts:

Modules for Data Processing and Reporting
-----------------------------------------
These :doc:`developer-guide/api/proteobench/modules/index` process the data and generate reports.

Web Interface for Result Visualization
--------------------------------------
The :doc:`developer-guide/api/webinterface/index` displays the results and allows
comparison with publicly available data.
