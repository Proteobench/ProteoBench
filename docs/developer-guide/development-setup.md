## Development setup

### Prerequisites

- **Python >= 3.11** is required.
- Using a **virtual environment** is highly recommended.

### Local installation

Create a virtual environment and install the package after cloning it locally:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --editable '.[dev]'
```

### Pre-commit hooks

The repository uses [pre-commit](https://pre-commit.com/) for automated code quality checks. Install the hooks after cloning:

```bash
pip install pre-commit
pre-commit install
```

The following hooks run automatically on each commit:
- **black** - code formatting
- **flake8** - linting (checks E9, F63, F7, F82)
- **numpydoc-validation** - docstring format validation
- **pre-commit-hooks** - general checks (large files, merge conflicts, YAML validation, etc.)

### Code style

- Code is formatted with [black](https://github.com/psf/black).
- Docstrings follow the [numpydoc style](https://numpydoc.readthedocs.io/en/latest/format.html).
- Linting uses flake8 with selective error checks configured in `setup.cfg`.


### Unit tests

To run the tests run the command:

```bash
pytest test/
```

You can also indicate specific tests to run:

```bash
pytest test/test_parse_params_alphapept.py
```

### Testing the web interface locally

Start the web server locally with:

```bash
cd ./webinterface/
streamlit run Home.py
```

This will launch the Proteobench application in your web browser.


Changes to the code in `./webinterface` will trigger a reload of the web server.
However, changes in `./proteobench` require a full restart of the webserver
to be included.


### Documentation

To work on the documentation and get a live preview, install the requirements
and run `sphinx-autobuild`:

```bash
pip install -e '.[docs]'
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

---

> **DOCUMENTATION GAPS**
>
> - **Python version requirements**: No minimum Python version is documented. Consider adding supported versions (e.g. Python 3.10+).
> - **Virtual environment setup**: The page mentions "Using a virtual environment is highly recommended" but does not show how to create one (e.g. `python -m venv .venv` or conda instructions).
> - **Pre-commit hooks**: The repository has `.pre-commit-config.yaml` but there is no documentation on setting up pre-commit hooks (`pre-commit install`).
> - **Common development issues**: No guidance on troubleshooting development setup problems (e.g. dependency conflicts, platform-specific issues on Windows/WSL).
> - **Code style / linting**: No documentation on code formatting expectations (black, flake8, etc.) despite `setup.cfg` containing flake8 configuration.


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
