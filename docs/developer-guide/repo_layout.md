# Layout of the Repository

This page gives an overview of the layout of the repository, describing the components which
make up the project ProteoBench.

We will dive into the following two main components:

- `proteobench`: The main package of the project, containing the core functionality and
  module-specific code
- `webinterface`: The streamlit web interface, where each module has it's own page with
  several tabs.

## Overall repository layout

```bash
ProteoBench
├── .github                 # GitHub Actions, Issue and Discussion templates
├── .vscode                 # VSCode settings for repository
├── docs                    # Documentation website using Sphinx
├── files_provided_to_users # probably accidentally added
├── img                     # Logos and Icons used in documentation
├── jupyter_notebooks       # Data Analysis for Paper and manual correction of results scripts
├── proteobench             # Main package of the project
├── test                    # Test for proteobench Python package
├── utilities               # currently: functionality to get dataset infos
└── webinterface            # Streamlit web interface
├── .gitignore
├── .pre-commit-config.yaml
├── .readthedocs.yml
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── noxfile.py
├── pyproject.toml          # ProteoBench Python package configuraton (main)
├── README.md               # main README for GitHub repository
├── SECURITY.md
├── setup.cfg               # ProteoBench Python package configuraton (flake8)
```

## ProteoBench python package

Let's see the overview for proteobench `0.11.0`:

```bash
proteobench
├── __init__.py
├── datapoint
│   ├── __init__.py
│   ├── datapoint_base.py                 # Abstract base class for all datapoints
│   └── quant_datapoint.py                # Quantification-specific datapoint implementations
├── exceptions.py                         # Custom exceptions
├── github
│   └── gh.py                             # Sync with benchmark repos (retrieving and uploading result metrics)
├── io
│   ├── data                              # Reference data files
│   ├── params                            # Parameter parsing (module unspecific) of data analysis software
│   ├── parsing                           # Parsing of output files of data analysis software, configuration tomls
│   └── __init__.py
├── modules
│   ├── __init__.py
│   ├── quant                             # Quant contains the module specific code for quantification
│   ├── rescoring                         # Rescoring module implementations
│   └── constants.py
├── plotting                              # Modular plotting architecture
│   ├── __init__.py
│   ├── plot_generator_base.py            # Abstract base class for all plot generators
│   └── plot_generator_lfq_HYE.py         # LFQ HYE-specific plot generator implementation
├── score                                 # Score calculation (computing benchmarking metrics)
│   ├── __init__.py
│   ├── score_base.py                     # Abstract base class for all score calculators
│   ├── quantscores.py                    # Quantification-specific score calculator (QuantScoresHYE)
│   └── quant/                            # Legacy quantification scoring (deprecated structure)
└── utils
    ├── plotting                          # Utility functions for plotting
    └── __init__.py
```

## Webinterface

```bash
webinterface
├── .streamlit                            # Streamlit configuration
├── logos
├── pages
│   ├── base_pages                        # QuantUIObjects (e.g. used for plotting)
│   ├── future_pages
│   ├── markdown_files                    # text snippets for the web interface
│   ├── pages_variables                   # variables each module (dataclasses)
│   └── texts                             # text scopes for the web interface (short and help msgs)
│   ├── __init__.py
│   ├── 2_Quant_LFQ_DDA_ion.py
│   ├── 3_Quant_LFQ_DIA_ion_AIF.py
│   ├── 4_Quant_LFQ_DIA_ion_diaPASEF.py
│   ├── 5_Quant_LFQ_DDA_peptidoform.py
│   ├── 6_Quant_LFQ_DIA_ion_Astral.py
├── __init__.py
├── _base.py                              # Homepage
├── Home.py                               # EntryPoint (using Homepage)
├── README.md
├── requirements.txt
└── streamlit_utils.py                    # mainly logging functionality (is it used?)
```
