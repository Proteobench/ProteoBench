project = "ProteoBench"
copyright = "2023, EuBIC-MS"
author = "EuBIC-MS"
description = "A Python-base platform for benchmarking data analysis in proteomics."

extensions = [
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
]

source_suffix = [".rst"]
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
# html_static_path = ["_static"]
