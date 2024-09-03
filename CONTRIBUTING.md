# Contributing

This document briefly describes how to contribute to
[ProteoBench](https://github.com/proteobench/proteobench).



## Before you begin

If you have an idea for a feature, use case to add or an approach for a bugfix,
you are welcome to communicate it with the community by opening a
thread in
[GitHub Discussions](https://github.com/proteobench/proteobench/discussions)
or in [GitHub Issues](https://github.com/proteobench/proteobench/issues).

Not sure where to start? Great contributions to
[ProteoBench](https://github.com/proteobench/proteobench) include:

[TODO]

Also check out the [open issues](https://github.com/proteobench/proteobench/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22+label%3A%22help+wanted%22)
that carry the `good first issue` or `help wanted` labels.


## Development setup

### Local installation
Install the package and dependencies with pip:

Change into the directory where you cloned proteobench into, and run:

```
pip install -e .
```

Using a virtual environment is recommended.


### Unit tests

To run the tests run the command:

> We use pytest which also supports unittest if you prefer that.

```
pytest
```


### Testing the web interface locally

Start the web server locally with:

```
cd ./webinterface/
streamlit run Home.py
```

This will launch the Proteobench application in your web browser.


Changes to the code in `./webinterface` will trigger a reload of the web server.
However, changes in `./proteobench` require a full restart of the webserver
to be included.

### Enabling pre-commit hooks

The project contains a .pre-commit-config.yaml file that defines a set of checks that are run before each commit.

To enable pre-commit checks on your machine install :

```
pipx install pre-commit
```

To run all the pre-commit checks on all files, run:
```
pre-commit run --all-files
```

To enable automatic pre-commit checks, run:

```
pre-commit install 
```

### running tests, building notebooks and documentation.

You can use `nox` to run tests build notebooks and build the documentation.

to run test only 
```
nox --session "tests"
```

```
nox --session "test_notebooks"
```

```
nox --session "docs"
```

### Documentation

To work on the documentation and get a live preview, install the requirements
and run `sphinx-autobuild`:


```
pip install -e'.[docs]'
sphinx-autobuild  --watch ./proteobench ./docs/ ./docs/_build/html/
```

Then browse to http://localhost:8000 to watch the live preview.


## How to contribute

- Fork [ProteoBench](https://github.com/proteobench/proteobench) on GitHub to
  make your changes.
- Commit and push your changes to your
  [fork](https://help.github.com/articles/pushing-to-a-remote/).
- Ensure that the tests and documentation (both Python docstrings and files in
  `/docs/source/`) have been updated according to your changes. Python
  docstrings are formatted in the
  [numpydoc style](https://numpydoc.readthedocs.io/en/latest/format.html).
- Open a
  [pull request](https://help.github.com/articles/creating-a-pull-request/)
  with these changes. You pull request message ideally should include:

    - A description of why the changes should be made.
    - A description of the implementation of the changes.
    - A description of how to test the changes.

- The pull request should pass all the continuous integration tests which are
  automatically run by
  [GitHub Actions](https://github.com/proteobench/proteobench/actions).



## Release workflow

- When a new version is ready to be published:

    1. Change the `__version__` in `proteobench/__init__.py` following
       [semantic versioning](https://semver.org/).
    2. Update the changelog (if not already done) in `CHANGELOG.md` according to
       [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
    3. Merge all final changes with the `main` branch.
    4. Create a new release on GitHub.

- When a new GitHub release is made, the `Publish` GitHub Action is automatically
  triggered to build the Python package and publish it to PyPI. Upon a new PyPI release,
  the Bioconda automations will automatically update the Bioconda package. However,
  if dependencies are changed, the conda recipe will have to be updated accordingly.
