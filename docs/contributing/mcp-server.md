# MCP server for coding agents

ProteoBench includes a [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server. It lets
a coding agent (for example Claude Code, Codex, Cursor or VS Code Copilot) benchmark a result file and compare
it with the public ProteoBench results, without the web interface. A typical use is the development of
a new quantification, de novo or identification tool: the agent runs the tool, benchmarks the output, reads the metrics, changes
the code, and repeats.

The server runs locally and reads local files. It does not submit results. Submission still goes
through the web interface.

## Installation

```bash
pip install 'proteobench[mcp]'
```

Register the server with your agent. For Claude Code:

```bash
claude mcp add proteobench -- python -m proteobench.mcp
```

Other clients take the same command (`python -m proteobench.mcp`, stdio transport) in their MCP
configuration file. Use the Python interpreter of the environment where ProteoBench is installed.

## Tools

| Tool | Purpose |
|------|---------|
| `list_modules` | List the benchmark modules (all categories) with their `module_id` |
| `list_supported_tools` | List the tool names accepted as `input_format` for a module |
| `get_upload_info` | Which result file and parameter file to provide, and the parse settings (column mapping, run names per condition) |
| `explain_metrics` | How the metrics of a module are calculated and interpreted (the same texts as "How are the metrics calculated?" in the web interface) |
| `get_public_results` | Public datapoints of a module with parameters and headline metrics, optionally filtered by tool and sorted |
| `benchmark_result` | Benchmark a local result file, compare it with the public datapoints, and run the submission validation checks |
| `get_benchmark_inputs` | The raw MS files and FASTA to run a tool on (URLs, sizes, optional download) and the run names the result must use |
| `check_parsing` | Parse a result file without scoring it, and report problems: missing columns, unmatched run names, row counts, flag counts |
| `extract_parameters` | Show which parameters ProteoBench reads from a tool parameter file, and which it could not read |
| `inspect_intermediate` | Filter, sort or group the intermediate table of a result (one row per precursor, spectrum or identification) |
| `compare_results` | Compare two results: rows found by only one of them, parameter differences and metrics |
| `render_plots` | Write the in-depth plots and the main plot of a result to HTML (or PNG with `kaleido`) |

`benchmark_result` returns the headline metrics of the result (for example `nr_feature`,
`median_abs_epsilon_eq_species`, `precision_peptide` or `category_paired`). For each, it gives the
percentile among the public datapoints and the public minimum, median and maximum. It also returns the
validation report and paths to two local files: all metrics as flattened dot paths (for example
`3.nr_feature` or `peptide.mass.precision`) and the intermediate table. Whether a higher or lower value
is better is explained by `explain_metrics`. Without a parameter file the result is still benchmarked,
but parameter fields are left empty. A tool that ProteoBench does not support yet can use the `Custom`
input format where a module offers it (see `get_upload_info`).

The last three tools accept a *source*: the `intermediate_hash` returned by `benchmark_result`, or the
id or `intermediate_hash` of a public datapoint. Intermediate tables of public datapoints are downloaded
from the ProteoBench server when needed.

## Example

Ask the agent, for example:

> Benchmark `results/evidence.txt` (MaxQuant, parameters in `results/mqpar.xml`) against the QExactive
> DDA module and tell me how it compares on accuracy and depth.

The agent calls `list_modules`, then `benchmark_result`, and reports how the metrics compare with the public results.

## Making a new module available

The server discovers modules automatically: every class under `proteobench/modules/` with a `module_id`
in `MODULE_SETTINGS_DIRS`. It only uses what a module already provides for the web interface: the
`PARAMS_JSON` parameter template, the `RAW_DATA_URL` of the input files, the parse settings, `benchmarking()`, and the metrics help texts of its
plot generator. The headline metrics are the top-level fields that the datapoint class sets. No change
to the server is needed. `test/test_mcp_server.py` checks that every discovered module provides these.

## Notes

- Public results are downloaded once per server process. Restart the server (start a new session, reconnect with /mcp) to see newly merged
  datapoints. In practice, however, datapoints are merged slower than coding agents can code 😉.
- Local results, downloaded public intermediate tables, comparisons and plots are stored under
  `proteobench_mcp/` in the system temporary directory.
- To inspect the server by hand, use the MCP Inspector:
  `npx @modelcontextprotocol/inspector python -m proteobench.mcp`.
