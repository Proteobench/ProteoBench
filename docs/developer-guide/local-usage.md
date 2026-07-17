# Local usage

All ProteoBench modules can be executed locally. Simply install the
`proteobench` Python package from PyPI:

```bash
pip install proteobench
```

Check out the [ProteoBench API documentation](https://proteobench.readthedocs.io/) for more information.

## Step-by-step example notebook

For a hands-on, runnable walkthrough of the core pipeline (load a search engine output file,
convert it to ProteoBench's standard format, compute scores, generate a datapoint, and plot the
results) without using the web app or any network access, see
[`examples/local_usage_walkthrough.ipynb`](https://github.com/Proteobench/ProteoBench/blob/main/examples/local_usage_walkthrough.ipynb)
in the repository. It uses a small example file already bundled under `test/data/`, so it runs
offline in a few seconds.
