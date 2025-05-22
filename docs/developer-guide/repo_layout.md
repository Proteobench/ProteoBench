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

Let's see the overview for proteobench `0.8.11`:

```bash
proteobench
├── __init__.py
├── datapoint
│   └── quant_datapoint.py
├── exceptions.py
├── github
│   └── gh.py # sync with benchmark repos (retrieving and uploading result metrics)
├── io
│   ├── data
│   ├── params # parameter parsing (module unspecific) of data analysis software
│   └── parsing # parsing of output files of data analysis software, configuration tomls
│   ├── __init__.py
├── modules
│   ├── __init__.py
│   ├── quant          # quant contains the module specific code for quantification
│   └── rescoring
│   ├── constants.py
├── plotting
│   └── plot_quant.py  # only example code for Base Module
├── score
│   └── quant
│   ├── __init__.py
└── utils
    └── plotting
    ├── __init__.py
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
