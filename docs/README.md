# Docs creation

In order to build the docs you need to 

  1. Install sphinx and additional support packages
  2. Build the package reference files
  3. Run sphinx to create a local html version

The documentation is build using readthedocs automatically.

Install the docs dependencies of the package (as speciefied in toml):

```bash
# in main folder
pip install ".[docs]"
```

## Build docs using Sphinx command line tools

Command to be run from `path/to/docs`, i.e. from within the `docs` package folder: 

Options:
  - `--separate` to build separate pages for each (sub-)module

```bash	
# pwd: docs
# apidoc
sphinx-apidoc --force --implicit-namespaces --module-first -o developer-guide/api/proteobench ../proteobench/
# webinterface is not importable as it's not a package
sphinx-apidoc --force --implicit-namespaces --module-first -o developer-guide/api/webinterface ../webinterface
# build docs
sphinx-build -n -W --keep-going -b html ./ ./_build/
```
