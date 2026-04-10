# Local usage

All ProteoBench modules can be executed locally. Simply install the
`proteobench` Python package from PyPI:

```bash
pip install proteobench
```

## Running the web interface locally

After installing the package, you can launch the Streamlit web interface:

```bash
cd webinterface/
streamlit run Home.py
```

This will open the ProteoBench application in your web browser at `http://localhost:8501`.

## Programmatic usage

You can also use ProteoBench modules directly from Python scripts. Here is an example of parsing parameters from a tool's configuration file:

```python
from proteobench.io.params.diann import extract_params

# Parse DIA-NN parameters from a log file
with open("report.log.txt", "rb") as f:
    params = extract_params(f)

print(params.software_name)       # "DIA-NN"
print(params.fixed_mods)          # "C[Carbamidomethyl]"
print(params.enzyme)              # "Trypsin"
```

Each parameter parser module in `proteobench.io.params` provides an `extract_params()` function that returns a `ProteoBenchParameters` object containing all parsed and normalized parameters.

## Output

When running a benchmark module, ProteoBench produces:
- A **pandas DataFrame** containing the benchmark metrics for each precursor ion or peptide
- **Interactive Plotly figures** visualizing the benchmark results
- A **parameter summary** extracted from the tool's configuration file

Check out the {ref}`proteobench` documentation for more information.

---

> **DOCUMENTATION GAPS**
>
> - **Usage examples**: No code examples showing how to run a module locally (e.g. importing a module, calling `extract_params()`, running a benchmark).
> - **CLI usage**: No documentation on whether ProteoBench can be used from the command line.
> - **Programmatic API**: No examples of how to use the Python API for batch processing or scripting.
> - **Output format**: No description of what local execution produces (files, DataFrames, plots).
