:html_theme.sidebar_secondary.remove:
:sd_hide_title: true

####
Home
####

.. toctree::
    :maxdepth: 1
    :hidden:
    :glob:

    Home <self>
    Learn more <general-information/index.rst>
    Benchmarking modules <available-modules/index.rst>
    Developer guide <developer-guide/index.rst>
    Contributing <contributing.rst>
    Changelog <changelog.rst>

.. div:: landing-title
    :style: padding: 2rem 2rem 4rem 2rem; background: rgb(49, 65, 89); clip-path: polygon(0px 0px, 100% 0%, 100% 100%, 0% calc(100% - 3rem)); -webkit-clip-path: polygon(0px 0px, 100% 0%, 100% 100%, 0% calc(100% - 3rem));

    .. grid::
        :reverse:
        :gutter: 2 3 3 3
        :margin: 4 4 1 2

        .. grid-item::
            :columns: 12 5 5 5

            .. image:: ./_static/img/proteobench-header-hex-dark.svg
                :class: sd-m-auto sd-animate-grow50-rot20

        .. grid-item::
            :columns: 12 7 7 7
            :child-align: justify
            :class: sd-text-white sd-fs-3

            ProteoBench is an open platform for benchmarking proteomics data analysis workflows.

            .. button-link:: #proteobench-in-5-steps
                :outline:
                :color: white
                :class: sd-px-4 sd-fs-5

                Get Started


ProteoBench in 5 steps
=======================

.. image:: ./_static/img/proteobench-steps.png
    :class: sd-m-auto

1. **Choose a module** to benchmark your proteomics data analysis workflow
2. **Download the input data** from the module page
3. **Run your workflow** on the input data
4. **Upload the results** to ProteoBench
5. **Compare your workflow run** with validated benchmark runs

.. line-block::
    **Robbe Devreese**
    *VIB-UGent Center for Medical Biotechnology, VIB, Ghent, Belgium*
    *Department of Biomolecular Medicine, UGent, Ghent, Belgium*

.. line-block:: 
    **Nadezhda T. Doncheva**
    *Novo Nordisk Foundation Center for Protein Research, Faculty of Health and Medical Sciences, University of Copenhagen, Copenhagen, Denmark*

Available ProteoBench modules
==============================

.. For card colors, use:
.. proposed: info
.. in development: primary
.. active: success
.. archived: warning
.. withdrawn: danger

.. line-block::
    **Caroline Jachmann**
    *VIB-UGent Center for Medical Biotechnology, VIB, Ghent, Belgium*
    *Department of Biomolecular Medicine, UGent, Ghent, Belgium*

.. line-block:: 
    **Vedran Kasalica**
    *Netherlands eScience Center, Science Park 402, 1098 XH, Amsterdam, The Netherlands*

    .. grid-item-card:: DDA identification
        :link: #

        :bdg-info:`proposed`
        ^^^
        Benchmark the identification sensitivity and specificity of data dependent acquisition
        workflows using an entrapment strategy


    .. grid-item-card:: DDA quantification
        :link: #

.. line-block::
    **Alireza Nameni**
    *VIB-UGent Center for Medical Biotechnology, VIB, Ghent, Belgium*
    *Department of Biomolecular Medicine, UGent, Ghent, Belgium*

.. line-block::
    **Martin Rykær**
    *Novo Nordisk Foundation Center for Protein Research, Faculty of Health and Medical Sciences, University of Copenhagen, Copenhagen, Denmark*


    .. grid-item-card:: DIA quantification
        :link: #

.. line-block::
    **Sam van Puyenbroeck**
    *VIB-UGent Center for Medical Biotechnology, VIB, Ghent, Belgium*
    *Department of Biomolecular Medicine, UGent, Ghent, Belgium*

.. line-block::
    **Bart Van Puyvelde**
    *ProGenTomics, Laboratory of Pharmaceutical Biotechnology, Ghent University, Belgium*

    .. grid-item-card:: De novo identification
        :link: #

        :bdg-primary:`in development`
        ^^^
        Benchmark the identification sensitivity and specificity of de novo sequencing workflows


Join the ProteoBench community
===============================

.. grid::

    .. grid-item-card::
        :img-top: ./_static/img/icons/workflow-run-validated-with-padding.svg
        :img-alt: A check-marked shield in an encircled gear
        :class-card: sd-border-0
        :class-footer: sd-border-0
        :shadow: none
        :text-align: center

        Submit your results as a validated benchmark run to be shared with the community.
        +++
        .. button-link:: https://proteobench.cubimed.rub.de/
            :color: primary
            :expand:

            :fas:`upload` Upload your results

    .. grid-item-card::
        :img-top: ./_static/img/icons/discussion-with-padding.svg
        :img-alt: Two speech bubbles
        :class-card: sd-border-0
        :class-footer: sd-border-0
        :shadow: none
        :text-align: center

        Discuss modules, benchmarking runs, and comparisons with the community.
        +++
        .. button-link:: https://github.com/orgs/Proteobench/discussions/
            :color: primary
            :expand:

            :fas:`comments` Discussion forum

    .. grid-item-card::
        :img-top: ./_static/img/icons/contribute-with-padding.svg
        :img-alt: A user with a development symbol (</>)
        :class-card: sd-border-0
        :class-footer: sd-border-0
        :shadow: none
        :text-align: center

        Contribute to ProteoBench by developing new modules or improving existing ones.
        +++
        .. button-link:: https://github.com/Proteobench/ProteoBench
            :color: primary
            :expand:

            :fab:`github` GitHub repository


Contact
========

Questions or comments? Email us at `proteobench@eubic-ms.org <mailto:proteobench@eubic-ms.org?>`_.
