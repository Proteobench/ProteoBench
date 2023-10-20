project = "ProteoBench"
author = "EuBIC-MS"
description = "A Python-base platform for benchmarking data analysis in proteomics."

extensions = [
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
]

source_suffix = [".rst"]
master_doc = "index"
exclude_patterns = ["_build", "_autosummary", "Thumbs.db", ".DS_Store"]

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
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
        "image_light": "_static/img/proteobench-logo-horizontal.svg",
        "image_dark": "_static/img/proteobench-logo-horizontal-inverted.svg",
    },
}

# Intersphinx options
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "psims": ("https://mobiusklein.github.io/psims/docs/build/html/", None),
    "pyteomics": ("https://pyteomics.readthedocs.io/en/stable/", None),
}
