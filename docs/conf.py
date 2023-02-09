import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from proteobench import __version__

project = 'ProteoBench'
author = 'EuBIC-MS'
release = __version__
github_project_url = "https://github.com/proteobench/proteobench/"
github_doc_root = "https://github.com/proteobench/proteobench/tree/main/docs/"

extensions = [
    'sphinx.ext.autodoc',
    "sphinx.ext.autosectionlabel",
    'sphinx.ext.autosummary',
    "sphinx.ext.napoleon",
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    "sphinx_rtd_theme",
    'sphinx_autodoc_typehints',
    "sphinx_mdinclude",
]
source_suffix = [".rst", ".md"]
master_doc = "index"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ('https://numpy.org/doc/stable/', None),
    "pandas": ('https://pandas.pydata.org/docs/', None),
}

autosummary_generate = True
autoclass_content = "both"
html_show_sourcelink = False
autodoc_inherit_docstrings = True
set_type_checking_flag = True
add_module_names = False

templates_path = ['_templates']
exclude_patterns = ["_build"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

autodoc_member_order = "bysource"
autoclass_content = "init"


def setup(app):
    config = {
        "enable_eval_rst": True,
    }
