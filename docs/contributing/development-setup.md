# Development setup

## Local installation

Clone the repository, then install it in editable mode with the development extras:

```bash
pip install --editable '.[dev]'
```

Using a virtual environment is highly recommended.

## Unit tests

```bash
pytest test/
```

You can also run a specific test file:

```bash
pytest test/test_parse_params_alphapept.py
```

## Testing the web interface locally

```bash
cd ./webinterface/
streamlit run Home.py
```

This launches the ProteoBench web app in your browser. Changes to `./webinterface` trigger a
reload; changes to `./proteobench` require a full restart of the server.

## Enabling pre-commit hooks

The repository ships a `.pre-commit-config.yaml` defining checks that run before each commit.

```bash
pipx install pre-commit
pre-commit install          # enable automatic checks on commit
pre-commit run --all-files  # run all checks once, on demand
```

## Running tests, notebooks, and docs via nox

```bash
nox --session "tests"
nox --session "test_notebooks"
nox --session "docs"
```

## Documentation

To work on the documentation with a live preview:

```bash
pip install -e '.[docs]'
sphinx-autobuild --watch ./proteobench ./docs/ ./docs/_build/html/
```

Then browse to <http://localhost:8000>.
