#####################
Benchmarking Modules
#####################

Here you find the modules and their documentation in ProteoBench.

Each module documentation includes:

- links to the raw data
- fasta files
- which files to upload
- which search parameters we *suggest* (feel free to deviate!)
- what the module is meant to benchmark
- which metrics we calculate
- and more!

If you want to jump right into looking at public results, or uploading your own results, you can go to https://proteobench.cubimed.rub.de/ and click on the module you are interested in. You can also find the links to the webserver in the module documentations below.

Before diving into a specific module, you may also want to read:

- :doc:`What is a benchmark module? <1-description-benchmark-module>`
- :doc:`Parameters parsed for public submission <12-parsed-parameters-for-public-submission>`


Are you looking for...
----------------------

...an example module to get started?
-------------------------------------

.. grid::

   .. grid-item-card:: LFQ of precursor ions with DDA (QExactive)
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-shadow-sm sd-mb-4

      :bdg-info:`beta`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DDA_ion_QExactive>`__ · :doc:`Documentation <active-modules/2-quant-lfq-ion-dda>`


...a quantification module for DIA data?
-----------------------------------------

.. grid::

   .. grid-item-card:: LFQ of precursor ions with diaPASEF
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-info:`beta`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_diaPASEF>`__ · :doc:`Documentation <active-modules/5-quant-lfq-ion-dia-diapasef>`


   .. grid-item-card:: LFQ of precursor ions with DIA Astral data
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-info:`beta`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_Astral>`__ · :doc:`Documentation <active-modules/7-quant-lfq-ion-dia-Astral_2Th>`


   .. grid-item-card:: LFQ of precursor ions with ZenoTOF 8600 - ZenoSWATH data
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-info:`beta`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_ZenoTOF>`__ · :doc:`Documentation <active-modules/10-quant-lfq-ion-dia-ZenoTOF>`


...a quantification module for DDA data?
-----------------------------------------

.. grid::

   .. grid-item-card:: LFQ of precursor ions with DDA (QExactive)
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-info:`beta`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DDA_ion_QExactive>`__ · :doc:`Documentation <active-modules/2-quant-lfq-ion-dda>`


   .. grid-item-card:: LFQ of peptidoforms with DDA (QExactive)
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-info:`beta`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DDA_peptidoform>`__ · :doc:`Documentation <active-modules/3-quant-lfq-peptidoform-dda>`


   .. grid-item-card:: LFQ of precursor ions with DDA Astral data
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-info:`beta`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DDA_ion_Astral>`__ · :doc:`Documentation <active-modules/8-quant-lfq-ion-dda-Astral>`

... Identification modules?
---------------------------

.. grid::


   .. grid-item-card:: De novo identification
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-success:`alpha`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/denovo_DDA_HCD>`__ · :doc:`Documentation <active-modules/11-denovo-dda-hcd>`


...a module to validate reported FDR control?
-----------------------------------------------

.. grid::

   .. grid-item-card:: DIA Ion Entrapment (Astral)
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-success:`alpha`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Entrapment_DIA_ion_Astral>`__ · :doc:`Documentation <active-modules/13-entrapment-ion-dia-astral>`


...a usecase specific module?
-----------------------------

.. grid::

   .. grid-item-card:: Low Input LFQ, DIA
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-success:`alpha`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_lowinput>`__ · :doc:`Documentation <active-modules/9-quant-lfq-ion-dia-lowinput>`


   .. grid-item-card:: Human Plasma LFQ, DIA
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-success:`alpha`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_Plasma>`__ · :doc:`Documentation <active-modules/12-quant-lfq-ion-dia-plasma>`


...an archived module?
----------------------

.. grid::

   .. grid-item-card:: LFQ of precursor ions with DIA, AIF
      :columns: 6 6 6 6
      :padding: 1
      :class-card: sd-mb-4

      :bdg-dark:`archived`
      ^^^
      +++
      `Web app <https://proteobench.cubimed.rub.de/Quant_LFQ_DIA_ion_AIF>`__ · :doc:`Documentation <archived-modules/4-quant-lfq-ion-dia-aif>`

.. toctree::
    :maxdepth: 2
    :glob:
    :hidden:

    1-description-benchmark-module
    12-parsed-parameters-for-public-submission
    active-modules/index
    archived-modules/index
