"""
Configuration file for the Sphinx documentation builder.
"""
import os
import sys
from pathlib import Path

import proteobench

# Patch in webinterface to be an importable module (needed for API documentation)
sys.path.insert(0, str(Path('..', 'webinterface').resolve()))
sys.path.insert(0, str(Path('..').resolve()))

project = "ProteoBench"
author = "EuBIC-MS"
description = "A Python-base platform for benchmarking data analysis in proteomics."
version = proteobench.__version__

extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx_new_tab_link",
    "sphinx_copybutton",
]

source_suffix = [".rst"]
master_doc = "index"
exclude_patterns = ["_build", "_autosummary", "reference", "Thumbs.db", ".DS_Store"]

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
templates_path = ["_templates"]
html_css_files = ["css/custom.css"]
html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/proteobench/proteobench",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        }
    ],
    "logo": {
        "image_light": "_static/proteobench-logo-horizontal.svg",
        "image_dark": "_static/proteobench-logo-horizontal-inverted.svg",
    },
    # "switcher": {
    #     "json_url": "_static/switcher.json",
    #     "version_match": version,
    # },
    # "navbar_center": ["version", "version-switcher", "navbar-nav"],
}

# Intersphinx options
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "psims": ("https://mobiusklein.github.io/psims/docs/build/html/", None),
    "pyteomics": ("https://pyteomics.readthedocs.io/en/stable/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "plotly": ("https://plotly.com/python-api-reference/", None),
}

# -- Setup for sphinx-apidoc -------------------------------------------------

# sphinx-apidoc needs to be called manually if Sphinx is running there.
# https://github.com/readthedocs/readthedocs.org/issues/1139

if os.environ.get("READTHEDOCS") == "True":
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).parent.parent
    PACKAGE_ROOT = PROJECT_ROOT / "proteobench"

    def run_apidoc(_):
        from sphinx.ext import apidoc

        apidoc.main(
            [
                "--force",
                "--implicit-namespaces",
                "--module-first",
                "--separate",
                "-o",
                str(PROJECT_ROOT / "docs" / "developer-guide" / "api" / "proteobench"),
                str(PACKAGE_ROOT),
            ]
        )
        
    # webinterface is not a package, so it was added to the path manually above
 
    APP_ROOT = PROJECT_ROOT / "webinterface"

    def run_apidoc_webinterface(_):
        from sphinx.ext import apidoc

        apidoc.main(
            [
                "--force",
                "--implicit-namespaces",
                "--module-first",
                "--separate",
                "-o",
                str(PROJECT_ROOT / "docs" / "developer-guide" / "api" / "webinterface"),
                str(APP_ROOT),
            ]
        )
    
    def setup(app):
        app.connect("builder-inited", run_apidoc)
        app.connect("builder-inited", run_apidoc_webinterface)
