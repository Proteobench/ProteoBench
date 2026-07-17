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
├── examples                # Runnable notebooks / walkthroughs (see local-usage.md)
├── img                     # Logos and Icons used in documentation
├── jupyter_notebooks       # Data Analysis for Paper and manual correction of results scripts (gitignored)
├── proteobench             # Main package of the project
├── scripts                 # Maintenance/utility scripts
├── test                    # Test for proteobench Python package
└── webinterface            # Streamlit web interface
├── .gitignore
├── .pre-commit-config.yaml
├── .readthedocs.yml
├── CHANGELOG.md
├── CLAUDE.md               # Repository guide for AI coding assistants
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── noxfile.py
├── pyproject.toml          # ProteoBench Python package configuration (main; also holds flake8/black config)
├── README.md               # main README for GitHub repository
├── resubmit_datapoints.py  # CLI script for reprocessing previously submitted datapoints
├── SECURITY.md
```

## ProteoBench python package

Let's see the overview of the `proteobench` package (the version is derived from git tags via
`setuptools_scm`, so there is no hardcoded version to reference here):

```bash
proteobench
├── __init__.py
├── datapoint
│   ├── __init__.py
│   ├── datapoint_base.py                 # Abstract base class for all datapoints
│   ├── quant_datapoint.py                # Quantification datapoints (QuantDatapointHYE, QuantDatapointPYE)
│   ├── denovo_datapoint.py               # De novo sequencing datapoint (DenovoDatapoint)
│   └── entrapment_datapoint.py           # Entrapment FDR-validation datapoint
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
│   ├── denovo                            # De novo sequencing module
│   ├── entrapment                        # Entrapment FDR-validation module
│   ├── rescoring                         # Rescoring module (placeholder, not yet implemented)
│   └── constants.py
├── plotting                              # Modular plotting architecture
│   ├── __init__.py
│   ├── plot_generator_base.py            # Abstract base class for all plot generators
│   ├── plot_generator_lfq_HYE.py         # LFQ HYE-specific plot generator implementation
│   ├── plot_generator_lfq_PYE.py         # LFQ PYE (plasma) plot generator implementation
│   ├── plot_generator_denovo.py          # De novo plot generator implementation
│   └── plot_generator_entrapment.py      # Entrapment plot generator implementation
├── score                                 # Score calculation (computing benchmarking metrics)
│   ├── __init__.py
│   ├── score_base.py                     # Abstract base class for all score calculators
│   ├── quantscoresHYE.py                 # Quantification score calculator (QuantScoresHYE)
│   ├── quantscoresPYE.py                 # Quantification score calculator, plasma variant (QuantScoresPYE)
│   ├── denovoscores.py                   # De novo sequencing score calculator (DenovoScores)
│   └── entrapmentscores.py               # Entrapment FDR-validation score calculator (EntrapmentScores)
├── validation                            # Framework-agnostic submission validation (see submission-validation.rst)
│   ├── __init__.py
│   ├── checks.py
│   ├── config.py
│   ├── context.py
│   ├── exceptions.py
│   ├── fasta.py
│   ├── profiles.py
│   ├── protein_ids.py
│   └── validator.py
└── utils
    ├── plotting                          # Utility functions for plotting
    └── __init__.py
```

## Webinterface

```bash
webinterface
├── .streamlit                            # Streamlit configuration (config.toml, secrets.toml)
├── logos
├── pages
│   ├── base.py                            # BaseStreamlitUI: tab dispatch, guided tour
│   ├── base_pages                        # QuantUIObjects / DeNovoUIObjects / EntrapmentUIObjects, tabs/, utils/
│   ├── future_pages                      # Non-active page stubs
│   ├── markdown_files                    # text snippets for the web interface
│   ├── pages_variables                   # variables dataclass per module
│   ├── texts                             # text scopes for the web interface (short and help msgs)
│   ├── utils                             # module_registry.py, tour_steps.py
│   ├── __init__.py
│   ├── 0_debug_session_state.py
│   ├── 2_Quant_LFQ_DDA_ion_QExactive.py
│   ├── 3_Quant_LFQ_DIA_ion_AIF.py
│   ├── 4_Quant_LFQ_DIA_ion_diaPASEF.py
│   ├── 5_Quant_LFQ_DDA_peptidoform.py
│   ├── 6_Quant_LFQ_DIA_ion_Astral.py
│   ├── 7_denovo_DDA_HCD.py
│   ├── 8_Quant_LFQ_DDA_ion_Astral.py
│   ├── 9_Quant_LFQ_DIA_ion_lowinput.py
│   ├── 10_Quant_LFQ_DIA_ion_ZenoTOF.py
│   ├── 11_Quant_LFQ_DIA_ion_Plasma.py
│   └── 12_Entrapment_DIA_ion_Astral.py
├── __init__.py
├── _base.py                              # StreamlitPage ABC (top-level entry point)
├── Home.py                               # Entry point (StreamlitPageHome, homepage overview)
├── UI_utils.py                           # Homepage stats, submission charts (used by Home.py)
├── README.md
├── requirements.txt
└── streamlit_utils.py                    # StreamlitLogger, display_error, save_dataframe, hide_streamlit_menu
```
