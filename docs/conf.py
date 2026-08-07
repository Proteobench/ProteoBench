"""
Configuration file for the Sphinx documentation builder.
"""

import os
import sys
from pathlib import Path

import proteobench

# Patch in webinterface to be an importable module (needed for API documentation)
sys.path.insert(0, str(Path("..", "webinterface").resolve()))
sys.path.insert(0, str(Path("..").resolve()))

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
exclude_patterns = ["_build", "_autosummary", "reference", "Thumbs.db", ".DS_Store", "module_grid_generated.rst"]

# GitHub-style heading anchors so in-page links like [here](#some-heading) resolve
# (used e.g. to link straight to a tool's setup section within a module page).
myst_heading_anchors = 3

# "colon_fence" enables :::{directive} syntax (used for nested sphinx-design grids/dropdowns in
# markdown pages, since backtick-fence nesting collides once you go two levels deep).
myst_enable_extensions = ["colon_fence"]

html_theme = "shibuya"
html_static_path = ["_static"]
templates_path = ["_templates"]
html_css_files = ["css/custom.css"]
html_theme_options = {
    "accent_color": "violet",
    "github_url": "https://github.com/proteobench/proteobench",
    "light_logo": "_static/proteobench-logo-horizontal.svg",
    "dark_logo": "_static/proteobench-logo-horizontal-inverted.svg",
    # Full site map in the sidebar on every page -- not just the current section's children.
    # Shibuya's sidebar is Sphinx's own global toctree (rooted at master_doc), unlike some
    # themes whose sidebar only shows the current top-level branch. toctree_collapse=False
    # renders every page into the sidebar HTML on every page load (so nothing needs a full
    # navigation to become visible), while globaltoc_expand_depth=0 keeps sections collapsed
    # by default -- only the active page's own ancestor chain auto-expands; everything else
    # is one click away via the expand arrow.
    "toctree_maxdepth": 4,
    "toctree_collapse": False,
    "toctree_titles_only": True,
    "toctree_includehidden": True,
    "globaltoc_expand_depth": 0,
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
                str(PROJECT_ROOT / "docs" / "contributing" / "api" / "proteobench"),
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
                str(PROJECT_ROOT / "docs" / "contributing" / "api" / "webinterface"),
                str(APP_ROOT),
            ]
        )

    def setup(app):
        app.connect("builder-inited", run_apidoc)
        app.connect("builder-inited", run_apidoc_webinterface)
