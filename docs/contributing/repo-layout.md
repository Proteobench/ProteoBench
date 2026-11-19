# Repository layout

An overview of the repository's structure, covering its two main components: `proteobench` (the
core package) and `webinterface` (the Streamlit web app, where each module has its own page with
several tabs).

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

## The `proteobench` Python package

```bash
proteobench
├── __init__.py
├── datapoint
│   ├── __init__.py
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
│   ├── quantscoresHYE.py                 # Quantification-specific score calculator (QuantScoresHYE)
│   └── quant/                            # Legacy quantification scoring (deprecated structure)
└── utils
    ├── plotting                          # Utility functions for plotting
    └── __init__.py
```

## The `webinterface`

```bash
webinterface
├── .streamlit                            # Streamlit configuration
├── logos
├── pages
│   ├── base_pages                        # QuantUIObjects (e.g. used for plotting)
│   ├── markdown_files                    # text snippets for the web interface
│   ├── pages_variables                   # one dataclass per module: config + page definition
│   └── texts                             # text scopes for the web interface (short and help msgs)
│   ├── __init__.py
│   ├── 0_debug_session_state.py          # local-only debug page (PROTEOBENCH_DEBUG=1)
│   ├── base.py                           # run_page(), BaseStreamlitUI, DEFAULT_TABS
├── __init__.py
├── _base.py                              # Homepage
├── Home.py                               # Entry point and router: home page + one st.Page per module
├── README.md
├── requirements.txt
└── streamlit_utils.py                    # error display helpers and CSV export
```
