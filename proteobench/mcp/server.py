"""
MCP server exposing ProteoBench benchmarking to coding agents.

Run with ``python -m proteobench.mcp`` (stdio transport). Register in Claude Code with
``claude mcp add proteobench -- python -m proteobench.mcp``.

The server is module-agnostic and only uses what the modules already provide for the web interface.
It discovers every module class under ``proteobench.modules`` with a ``module_id`` listed in
``MODULE_SETTINGS_DIRS`` and relies on this interface:

- ``benchmarking(result_file, input_format, user_input, all_datapoints, input_file_secondary=...)``
  returning ``(intermediate, datapoints, input_df)``;
- ``obtain_all_data_points()``, ``load_params_file(files, input_format, json_file=...)``,
  ``EXTRACT_PARAMS_DICT`` and the ``PARAMS_JSON`` parameter template;
- ``get_plot_generator()``, whose metrics help texts explain the metrics.

The headline metrics are the top-level fields each datapoint class sets next to the nested ``results``.
A new module, or a new module category, therefore needs no changes here.
"""

from __future__ import annotations

import contextlib
import functools
import glob
import importlib
import inspect
import json
import os
import pkgutil
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import requests
import toml
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

import proteobench.modules
from proteobench.io.params import PARAMS_JSON_DIR, ProteoBenchParameters
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder
from proteobench.modules.constants import MODULE_SETTINGS_DIRS
from proteobench.utils.server_io import DATASETS_BASE_URL, download_file
from proteobench.validation import FastaReference, ModuleValidationConfig, validate_submission

# Local results of benchmark_result and downloaded public intermediates.
CACHE_DIR = Path(tempfile.gettempdir()) / "proteobench_mcp"

# Top-level datapoint fields that are neither parameters nor metrics.
BOOKKEEPING_FIELDS = {
    "id",
    "is_temporary",
    "intermediate_hash",
    "results",
    "comments",
    "submission_comments",
    "proteobench_version",
    "old_new",
}

mcp = MCPServer(
    "proteobench",
    instructions=(
        "Benchmark proteomics data analysis tool outputs against ProteoBench modules and compare with "
        "public results. Start with list_modules, then get_upload_info to see which files a tool needs, "
        "then benchmark_result. Call explain_metrics to learn how to interpret the metrics of a module, "
        "including whether higher or lower values are better. get_benchmark_inputs gives the raw files and "
        "FASTA to run a tool on; check_parsing diagnoses input problems; inspect_intermediate, "
        "compare_results and render_plots analyse a result (local or public) in depth."
    ),
)


def _quiet(func):
    """
    Redirect stdout to stderr and pass error messages to the agent.

    Core code prints, which would corrupt the stdio JSON-RPC stream. MCPServer hides the message of any
    exception that is not a ToolError, but the agent needs it (e.g. a ParseError) to fix its input.

    Parameters
    ----------
    func : Callable
        The tool function.

    Returns
    -------
    Callable
        The wrapped tool function.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # numpydoc ignore=GL08
        with contextlib.redirect_stdout(sys.stderr):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                raise ToolError(f"{type(exc).__name__}: {exc}") from exc

    return wrapper


def _discover_modules() -> dict[str, type]:
    """
    Find all module classes with a registered settings directory.

    Returns
    -------
    dict[str, type]
        Mapping of module_id to module class.
    """
    found = {}
    for info in pkgutil.walk_packages(proteobench.modules.__path__, "proteobench.modules."):
        for cls in vars(importlib.import_module(info.name)).values():
            module_id = vars(cls).get("module_id") if inspect.isclass(cls) else None
            if isinstance(module_id, str) and module_id in MODULE_SETTINGS_DIRS:
                found[module_id] = cls
    return dict(sorted(found.items()))


MODULES = _discover_modules()

# Fields of all parameter templates: public datapoints can carry parameter columns of other templates.
ALL_PARAM_FIELDS = {
    field
    for path in glob.glob(os.path.join(PARAMS_JSON_DIR, "*", "*.json"))
    for field in vars(ProteoBenchParameters(filename=path))
}


def _module_class(module_id: str) -> type:
    """
    Look up a module class by module_id.

    Parameters
    ----------
    module_id : str
        The module identifier.

    Returns
    -------
    type
        The module class.
    """
    if module_id not in MODULES:
        raise ValueError(f"Unknown module_id '{module_id}'. Valid: {sorted(MODULES)}")
    return MODULES[module_id]


def _builder(module_id: str) -> ParseSettingsBuilder:
    """
    Build the parse settings builder for a module.

    Parameters
    ----------
    module_id : str
        The module identifier.

    Returns
    -------
    ParseSettingsBuilder
        The builder for the module settings directory.
    """
    _module_class(module_id)
    return ParseSettingsBuilder(MODULE_SETTINGS_DIRS[module_id], module_id)


@functools.cache
def _module(module_id: str):
    """
    Return a cached module instance (anonymous, no GitHub token).

    Parameters
    ----------
    module_id : str
        The module identifier.

    Returns
    -------
    object
        The module instance.
    """
    # ponytail: one cached instance per server process; restart to pick up newly merged public datapoints.
    return _module_class(module_id)("")


@functools.cache
def _public_datapoints(module_id: str) -> pd.DataFrame:
    """
    Return the public datapoints of a module, cloned once per server process.

    Parameters
    ----------
    module_id : str
        The module identifier.

    Returns
    -------
    pd.DataFrame
        One row per public datapoint.
    """
    return _module(module_id).obtain_all_data_points()


def _params_json(module_id: str) -> str:
    """
    Return the path to the parameter field template of a module.

    Parameters
    ----------
    module_id : str
        The module identifier.

    Returns
    -------
    str
        Absolute path to the JSON template.
    """
    return os.path.join(PARAMS_JSON_DIR, _module_class(module_id).PARAMS_JSON)


@functools.cache
def _param_fields(module_id: str) -> tuple[str, ...]:
    """
    Return the parameter field names of a module.

    Parameters
    ----------
    module_id : str
        The module identifier.

    Returns
    -------
    tuple[str, ...]
        Field names defined by the module parameter template.
    """
    return tuple(vars(ProteoBenchParameters(filename=_params_json(module_id))))


def _json_safe(value: Any) -> Any:
    """
    Convert a value to a JSON-serialisable one (NaN to None, numpy scalars to Python).

    Parameters
    ----------
    value : Any
        The value to convert.

    Returns
    -------
    Any
        A JSON-serialisable value.
    """
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if not pd.api.types.is_scalar(value):
        return str(value)
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value


def _flatten(results: Any, prefix: str = "") -> dict:
    """
    Flatten a nested ``results`` dict to dot paths, keeping scalar leaves only.

    Parameters
    ----------
    results : Any
        The datapoint ``results`` field (keys may be int in-process and str when loaded from JSON).
    prefix : str
        Path prefix for recursion.

    Returns
    -------
    dict
        Dot path to scalar value; lists such as curves are left out.
    """
    out = {}
    if not isinstance(results, dict):
        return out
    for key, value in results.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            out |= _flatten(value, path + ".")
        elif pd.api.types.is_scalar(value):
            out[path] = _json_safe(value)
    return out


def _split_datapoint(row: pd.Series, module_id: str) -> tuple[dict, dict]:
    """
    Split a datapoint into its parameters and its headline metrics.

    Headline metrics are the top-level fields that are neither parameters nor bookkeeping, i.e. the
    summary values each datapoint class sets next to the nested ``results``.

    Parameters
    ----------
    row : pd.Series
        One datapoint.
    module_id : str
        The module identifier.

    Returns
    -------
    tuple[dict, dict]
        Parameters and headline metrics; empty and non-scalar values are left out.
    """
    own_params = set(_param_fields(module_id))
    params, metrics = {}, {}
    for key, value in row.items():
        if key in BOOKKEEPING_FIELDS or not pd.api.types.is_scalar(value):
            continue
        value = _json_safe(value)
        if value in (None, "None", "", "nan"):
            continue
        if key in own_params:
            params[key] = value
        elif key not in ALL_PARAM_FIELDS:
            metrics[key] = value
    return params, metrics


def _summarise(df: pd.DataFrame, module_id: str) -> list[dict]:
    """
    Reduce datapoints to their identifiers, parameters and headline metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Datapoints, one per row.
    module_id : str
        The module identifier.

    Returns
    -------
    list[dict]
        One dict per datapoint.
    """
    rows = []
    for _, row in df.iterrows():
        params, metrics = _split_datapoint(row, module_id)
        rows.append({"id": row.get("id"), "intermediate_hash": row.get("intermediate_hash"), **params, **metrics})
    return rows


def _compare(metrics: dict, public: pd.DataFrame) -> dict:
    """
    Place each headline metric of a new datapoint in the distribution of the public datapoints.

    Parameters
    ----------
    metrics : dict
        Headline metrics of the new datapoint.
    public : pd.DataFrame
        The public datapoints.

    Returns
    -------
    dict
        Per numeric metric: value, percentile (share of public values below it), public_min,
        public_median, public_max and n_public. Per text metric: value and public value counts.
    """
    out = {}
    for name, value in metrics.items():
        if name not in public:
            out[name] = {"value": value, "n_public": 0}
            continue
        if isinstance(value, str):
            counts = public[name].dropna().astype(str).value_counts()
            out[name] = {"value": value, "public_counts": {k: int(v) for k, v in counts.items()}}
            continue
        others = pd.to_numeric(public[name], errors="coerce").dropna()
        out[name] = {"value": value, "n_public": int(len(others))}
        if len(others):
            out[name] |= {
                "percentile": round(float((others < value).mean() * 100), 1),
                "public_min": float(others.min()),
                "public_median": float(others.median()),
                "public_max": float(others.max()),
            }
    return out


def _load_params(module_id: str, input_format: str, params_file: Optional[str]):
    """
    Parse a tool parameter file, if given.

    Parameters
    ----------
    module_id : str
        The module identifier.
    input_format : str
        The software tool name.
    params_file : str, optional
        Path to the tool parameter file.

    Returns
    -------
    ProteoBenchParameters or None
        The parsed parameters, or None without a parameter file.
    """
    if not params_file:
        return None
    return _module(module_id).load_params_file([params_file], input_format, json_file=_params_json(module_id))


@functools.cache
def _fasta(url: str, member: Optional[str]) -> FastaReference:
    """
    Download and cache a module reference FASTA.

    Parameters
    ----------
    url : str
        The FASTA (or zip) URL.
    member : str, optional
        The FASTA file name inside a zip archive.

    Returns
    -------
    FastaReference
        The reference protein identifiers.
    """
    return FastaReference.from_url(url, member_filename=member)


def _validate(module_id: str, input_format: str, input_df: pd.DataFrame, params) -> dict:
    """
    Run the submission validation profile of the module on a parsed result.

    Parameters
    ----------
    module_id : str
        The module identifier.
    input_format : str
        The software tool name.
    input_df : pd.DataFrame
        The parsed tool output, as returned by ``benchmarking``.
    params : ProteoBenchParameters or None
        The parsed parameters.

    Returns
    -------
    dict
        The validation report, or an ``error`` entry when validation could not run.
    """
    try:
        standard = _builder(module_id).build_parser(input_format).convert_to_standard_format(input_df)
        standard_df = standard[0] if isinstance(standard, tuple) else standard
        config = ModuleValidationConfig.from_parse_settings(MODULE_SETTINGS_DIRS[module_id], module_id, input_format)
        fasta = _fasta(config.fasta_url, config.fasta_filename) if config.fasta_url else None
        report = validate_submission(
            standard_df, parameters=params, fasta=fasta, config=config, input_format=input_format
        )
        return report.to_dict()
    except Exception as exc:  # validation is advisory; never lose the benchmark result over it
        return {"error": f"Validation could not run: {type(exc).__name__}: {exc}"}


def _json_default(value: Any) -> Any:
    """
    Serialise values that ``json`` does not handle (numpy scalars, timestamps).

    Parameters
    ----------
    value : Any
        The value to serialise.

    Returns
    -------
    Any
        A JSON-serialisable value.
    """
    return value.item() if hasattr(value, "item") else str(value)


def _local_dir(module_id: str, intermediate_hash: str) -> Path:
    """
    Return the directory where benchmark_result stores a local result.

    Parameters
    ----------
    module_id : str
        The module identifier.
    intermediate_hash : str
        The hash of the result.

    Returns
    -------
    Path
        The result directory.
    """
    return CACHE_DIR / "results" / module_id / intermediate_hash


def _public_intermediate(intermediate_hash: str) -> Path:
    """
    Download (once) the intermediate table of a public datapoint from the ProteoBench server.

    Parameters
    ----------
    intermediate_hash : str
        The hash of the public datapoint.

    Returns
    -------
    Path
        Local path to the intermediate CSV.
    """
    path = CACHE_DIR / "public" / intermediate_hash / "intermediate.csv"
    if not path.exists():
        zip_path = path.parent / "data.zip"
        try:
            download_file(f"{DATASETS_BASE_URL}{intermediate_hash}/{intermediate_hash}_data.zip", os.fspath(zip_path))
        except requests.HTTPError as exc:
            raise ValueError(
                f"The intermediate data of public datapoint {intermediate_hash} is not available on the "
                f"ProteoBench server ({exc.response.status_code})."
            ) from exc
        with zipfile.ZipFile(zip_path) as archive, archive.open("result_performance.csv") as src:
            with open(path, "wb") as dst:
                shutil.copyfileobj(src, dst)
        zip_path.unlink()
    return path


def _resolve(module_id: str, source: str) -> dict:
    """
    Find a result by local intermediate_hash or public datapoint id or hash.

    Parameters
    ----------
    module_id : str
        The module identifier.
    source : str
        An intermediate_hash returned by benchmark_result, or a public datapoint id or intermediate_hash.

    Returns
    -------
    dict
        Keys: kind ("local" or "public"), datapoint (pd.Series) and intermediate_path.
    """
    local = _local_dir(module_id, source)
    if (local / "datapoint.json").exists():
        datapoint = pd.Series(json.loads((local / "datapoint.json").read_text()))
        return {"kind": "local", "datapoint": datapoint, "intermediate_path": local / "intermediate.csv"}
    public = _public_datapoints(module_id)
    match = public[(public.get("id") == source) | (public.get("intermediate_hash") == source)]
    if match.empty:
        raise ValueError(
            f"'{source}' is neither an intermediate_hash from benchmark_result nor a public datapoint id or "
            f"intermediate_hash of {module_id} (see get_public_results)."
        )
    datapoint = match.iloc[0]
    path = _public_intermediate(datapoint["intermediate_hash"])
    return {"kind": "public", "datapoint": datapoint, "intermediate_path": path}


def _describe_source(module_id: str, src: dict) -> dict:
    """
    Summarise a resolved result for tool output.

    Parameters
    ----------
    module_id : str
        The module identifier.
    src : dict
        A result as returned by ``_resolve``.

    Returns
    -------
    dict
        Keys: kind, id, intermediate_hash and software_name.
    """
    datapoint = src["datapoint"]
    return {
        "kind": src["kind"],
        "id": _json_safe(datapoint.get("id")),
        "intermediate_hash": _json_safe(datapoint.get("intermediate_hash")),
        "software_name": _json_safe(datapoint.get("software_name")),
    }


def _input_loader(module_id: str):
    """
    Return the input file loader that a module's benchmarking uses.

    Each module file imports the ``load_input_file`` of its category (ion, peptidoform, de novo); the
    first one found along the class hierarchy is the one ``benchmarking`` calls.

    Parameters
    ----------
    module_id : str
        The module identifier.

    Returns
    -------
    Callable
        ``load_input_file(path, input_format[, secondary])``.
    """
    for cls in _module_class(module_id).__mro__:
        loader = getattr(sys.modules.get(cls.__module__), "load_input_file", None)
        if loader is not None:
            return loader
    raise ValueError(f"No input file loader found for {module_id}.")


def _remote_size_mb(url: str) -> Optional[float]:
    """
    Return the size of a remote file in MB, if the server reports it.

    Parameters
    ----------
    url : str
        The file URL.

    Returns
    -------
    float or None
        Size in MB, or None when unknown.
    """
    try:
        length = requests.head(url, allow_redirects=True, timeout=30).headers.get("content-length")
        return round(int(length) / 1e6, 1) if length else None
    except (requests.RequestException, ValueError):
        return None


def _records(df: pd.DataFrame) -> list[dict]:
    """
    Convert DataFrame rows to JSON-safe dicts.

    Parameters
    ----------
    df : pd.DataFrame
        The rows to convert.

    Returns
    -------
    list[dict]
        One dict per row; long text values are shortened.
    """
    out = []
    for row in df.to_dict(orient="records"):
        safe = {str(k): _json_safe(v) for k, v in row.items()}
        out.append({k: v[:200] if isinstance(v, str) else v for k, v in safe.items()})
    return out


@mcp.tool()
@_quiet
def list_modules() -> list[dict]:
    """
    List the ProteoBench benchmark modules.

    Returns
    -------
    list[dict]
        Per module: module_id, category, class name, public results repository and a one-line
        description.
    """
    out = []
    for module_id, cls in MODULES.items():
        repo = inspect.signature(cls.__init__).parameters.get("proteobench_repo_name")
        out.append(
            {
                "module_id": module_id,
                "category": cls.__module__.split(".")[2],
                "class": cls.__name__,
                "results_repo": repo.default if repo else None,
                "description": (cls.__doc__ or "").strip().split("\n")[0],
            }
        )
    return out


@mcp.tool()
@_quiet
def explain_metrics(module_id: str) -> dict:
    """
    Explain how the metrics of a module are calculated and how to interpret them.

    These are the same texts the ProteoBench web interface shows under "How are the metrics calculated?".

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.

    Returns
    -------
    dict
        Keys: main (Markdown explanation of the main plot metrics) and in_depth (explanation of the
        in-depth metrics of a single run).
    """
    generator = _module(module_id).get_plot_generator()
    return {
        "main": generator.get_metrics_help_markdown(),
        "in_depth": generator.get_in_depth_metrics_help_markdown(),
    }


@mcp.tool()
@_quiet
def list_supported_tools(module_id: str) -> list[str]:
    """
    List the software tool names accepted as input_format for a module.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.

    Returns
    -------
    list[str]
        Tool names; most modules also accept "Custom" for a generic tab-separated format.
    """
    return _builder(module_id).INPUT_FORMATS


@mcp.tool()
@_quiet
def get_upload_info(module_id: str, input_format: str) -> dict:
    """
    Describe which files to provide for a tool, and how ProteoBench reads them.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    input_format : str
        The software tool name, from list_supported_tools.

    Returns
    -------
    dict
        Keys: upload_info (result file and parameter file guidance), parse_settings (the tool's parse
        settings, e.g. column mapping, decoy and contaminant flags, run name to condition mapping) and
        params_file_supported.
    """
    builder = _builder(module_id)
    if input_format not in builder.PARSE_SETTINGS_FILES:
        raise ValueError(f"'{input_format}' is not supported. Supported: {builder.INPUT_FORMATS}")
    settings = toml.load(builder.PARSE_SETTINGS_FILES[input_format])
    return {
        "upload_info": builder.get_upload_info(input_format),
        "parse_settings": {k: v for k, v in settings.items() if not k.startswith("upload_info")},
        "params_file_supported": input_format in getattr(_module_class(module_id), "EXTRACT_PARAMS_DICT", {}),
    }


@mcp.tool()
@_quiet
def get_public_results(
    module_id: str,
    software_name: Optional[str] = None,
    sort_by: Optional[str] = None,
    descending: bool = False,
    limit: int = 20,
) -> dict:
    """
    Return public ProteoBench datapoints of a module with their parameters and headline metrics.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    software_name : str, optional
        Keep only datapoints of this tool (case-insensitive).
    sort_by : str, optional
        Headline metric or parameter to sort on; see explain_metrics for which direction is better.
    descending : bool
        Sort from high to low.
    limit : int
        Maximum number of datapoints returned.

    Returns
    -------
    dict
        Keys: total, returned, and datapoints (identifiers, parameters and headline metrics).
    """
    df = _public_datapoints(module_id)
    if software_name and "software_name" in df:
        df = df[df["software_name"].astype(str).str.lower() == software_name.lower()]
    if sort_by:
        if sort_by not in df:
            raise ValueError(f"Unknown sort_by '{sort_by}'. Columns: {sorted(df.columns)}")
        df = df.sort_values(sort_by, ascending=not descending, na_position="last")
    rows = _summarise(df.head(limit), module_id)
    return {"total": len(df), "returned": len(rows), "datapoints": rows}


@mcp.tool()
@_quiet
def benchmark_result(
    module_id: str,
    input_format: str,
    result_file: str,
    params_file: Optional[str] = None,
    secondary_file: Optional[str] = None,
    software_version: str = "dev",
    validate: bool = True,
) -> dict:
    """
    Benchmark a tool output file locally and compare it with the public datapoints of the module.

    Nothing is submitted. All metrics and the intermediate table are written to local files for
    further inspection. Use explain_metrics to interpret the values.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    input_format : str
        The software tool name, from list_supported_tools.
    result_file : str
        Local path to the tool result file (see get_upload_info).
    params_file : str, optional
        Local path to the tool parameter file. Without it, parameter fields stay empty.
    secondary_file : str, optional
        Second result file, for tools whose output spans two files (e.g. AlphaDIA).
    software_version : str
        Version label, used when the parameter file does not provide one.
    validate : bool
        Also run the submission validation checks of the module (advisory).

    Returns
    -------
    dict
        Keys: intermediate_hash, identical_public_datapoint (ids of public datapoints with the same hash),
        comparison (per headline metric: value, percentile among public datapoints, public min, median
        and max), metrics_json (path to all metrics as flattened dot paths), intermediate_csv (path)
        and validation (report). The intermediate_hash identifies this result in inspect_intermediate,
        compare_results and render_plots.
    """
    module = _module(module_id)
    params = _load_params(module_id, input_format, params_file)
    user_input = dict.fromkeys(_param_fields(module_id)) | {"software_version": software_version}
    if params is not None:
        user_input |= {k: v for k, v in vars(params).items() if v is not None}
    user_input |= {"software_name": input_format, "input_format": input_format, "comments_for_plotting": ""}

    # Empty DataFrame: compute the new datapoint alone, so a result identical to a public one still scores.
    intermediate, datapoints, input_df = module.benchmarking(
        result_file, input_format, user_input, pd.DataFrame(), input_file_secondary=secondary_file
    )
    new = datapoints.iloc[-1]
    new_hash = new["intermediate_hash"]
    _, headline = _split_datapoint(new, module_id)
    public = _public_datapoints(module_id)
    identical = public.loc[public.get("intermediate_hash") == new_hash, "id"].tolist() if "id" in public else []

    out_dir = _local_dir(module_id, new_hash)
    out_dir.mkdir(parents=True, exist_ok=True)
    intermediate.to_csv(out_dir / "intermediate.csv", index=False)
    (out_dir / "metrics.json").write_text(json.dumps(_flatten(new["results"]), indent=1))
    (out_dir / "datapoint.json").write_text(json.dumps(dict(new), default=_json_default))
    return {
        "module_id": module_id,
        "intermediate_hash": new_hash,
        "identical_public_datapoint": identical or None,
        "comparison": _compare(headline, public),
        "metrics_json": os.fspath(out_dir / "metrics.json"),
        "intermediate_csv": os.fspath(out_dir / "intermediate.csv"),
        "validation": _validate(module_id, input_format, input_df, params) if validate else None,
    }


@mcp.tool()
@_quiet
def get_benchmark_inputs(module_id: str, download_dir: Optional[str] = None) -> dict:
    """
    Return the input files of a module benchmark (raw MS files and FASTA) and the expected run names.

    Run the tool under test on these files, then pass its output to benchmark_result. The raw data
    archives are large (often several GB); check size_mb before downloading.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    download_dir : str, optional
        If given, download the files into this local directory (archives are not extracted).

    Returns
    -------
    dict
        Keys: files (per file: url, size_mb and, after download, path) and condition_mapper (run name to
        condition, the run names the result file must use).
    """
    cls, builder = _module_class(module_id), _builder(module_id)
    input_format = builder.INPUT_FORMATS[0]
    config = ModuleValidationConfig.from_parse_settings(MODULE_SETTINGS_DIRS[module_id], module_id, input_format)
    urls = {"raw_data": getattr(cls, "RAW_DATA_URL", None), "fasta": config.fasta_url}
    files = {name: {"url": url, "size_mb": _remote_size_mb(url)} for name, url in urls.items() if url}
    if download_dir:
        for info in files.values():
            info["path"] = download_file(info["url"], os.path.join(download_dir, info["url"].rsplit("/", 1)[-1]))
    return {
        "module_id": module_id,
        "files": files,
        "condition_mapper": getattr(builder.build_parser(input_format), "condition_mapper", None),
    }


@mcp.tool()
@_quiet
def check_parsing(module_id: str, input_format: str, result_file: str, secondary_file: Optional[str] = None) -> dict:
    """
    Parse a result file into the ProteoBench standard format without scoring it, and report problems.

    Use this when benchmark_result fails or gives unexpected numbers, or while writing an exporter for
    the Custom format.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    input_format : str
        The software tool name, from list_supported_tools.
    result_file : str
        Local path to the tool result file.
    secondary_file : str, optional
        Second result file, for tools whose output spans two files (e.g. AlphaDIA).

    Returns
    -------
    dict
        Keys: ok, stage ("load", "convert" or "done"), error (when not ok), input (rows, columns),
        missing_mapped_columns (columns the parse settings expect but the file lacks), standard (rows,
        columns), rows_per_run, missing_runs (expected run names not found), runs_per_condition,
        flag_counts (True counts of boolean columns, e.g. species, decoy or contaminant flags),
        run_name_corrections and example_rows.
    """
    builder = _builder(module_id)
    if input_format not in builder.PARSE_SETTINGS_FILES:
        raise ValueError(f"'{input_format}' is not supported. Supported: {builder.INPUT_FORMATS}")
    report = {"module_id": module_id, "input_format": input_format, "ok": False}
    try:
        args = [result_file, input_format] + ([secondary_file] if secondary_file else [])
        input_df = _input_loader(module_id)(*args)
    except Exception as exc:
        return report | {"stage": "load", "error": f"{type(exc).__name__}: {exc}"}
    parser = builder.build_parser(input_format)
    report["input"] = {"rows": len(input_df), "columns": [str(c) for c in input_df.columns]}
    report["missing_mapped_columns"] = [c for c in getattr(parser, "mapper", {}) or {} if c not in input_df.columns]
    try:
        converted = parser.convert_to_standard_format(input_df)
    except Exception as exc:
        return report | {"stage": "convert", "error": f"{type(exc).__name__}: {exc}"}
    standard, groups = converted if isinstance(converted, tuple) else (converted, None)
    report |= {"ok": True, "stage": "done", "standard": {"rows": len(standard), "columns": list(standard.columns)}}
    if "Raw file" in standard:
        report["rows_per_run"] = {str(k): int(v) for k, v in standard["Raw file"].value_counts().items()}
        expected = getattr(parser, "condition_mapper", None) or {}
        report["missing_runs"] = [run for run in expected if run not in report["rows_per_run"]]
    if groups:
        report["runs_per_condition"] = {str(k): list(v) for k, v in dict(groups).items()}
    report["flag_counts"] = {c: int(standard[c].sum()) for c in standard.columns if standard[c].dtype == bool}
    report["run_name_corrections"] = [str(c) for c in getattr(parser, "run_name_corrections", []) or []]
    report["example_rows"] = _records(standard.head(3))
    return report


@mcp.tool()
@_quiet
def extract_parameters(module_id: str, input_format: str, params_file: str) -> dict:
    """
    Show which parameters ProteoBench reads from a tool parameter file.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    input_format : str
        The software tool name, from list_supported_tools.
    params_file : str
        Local path to the tool parameter file (see get_upload_info).

    Returns
    -------
    dict
        Keys: parsed (parameter to value) and not_parsed (template parameters without a value).
    """
    if input_format not in getattr(_module_class(module_id), "EXTRACT_PARAMS_DICT", {}):
        raise ValueError(f"No parameter parser for '{input_format}' in {module_id}.")
    values = {k: _json_safe(v) for k, v in vars(_load_params(module_id, input_format, params_file)).items()}
    parsed = {k: v for k, v in values.items() if v not in (None, "None", "", "nan")}
    return {"parsed": parsed, "not_parsed": [k for k in values if k not in parsed]}


@mcp.tool()
@_quiet
def inspect_intermediate(
    module_id: str,
    source: str,
    query: Optional[str] = None,
    columns: Optional[list[str]] = None,
    sort_by: Optional[str] = None,
    descending: bool = False,
    group_by: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """
    Query the intermediate table (one row per precursor, spectrum or identification) of a result.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    source : str
        An intermediate_hash from benchmark_result, or a public datapoint id or intermediate_hash.
    query : str, optional
        A pandas ``DataFrame.query`` filter, e.g. ``"species == 'YEAST' and nr_observed >= 3"``.
    columns : list[str], optional
        Columns to return (default: all).
    sort_by : str, optional
        Column to sort on.
    descending : bool
        Sort from high to low.
    group_by : str, optional
        Column to group on; returns the row count and the median of the numeric columns per group
        instead of rows.
    limit : int
        Maximum number of rows returned.

    Returns
    -------
    dict
        Keys: source, rows_total, rows_matched, columns (all available columns) and rows or groups.
    """
    src = _resolve(module_id, source)
    df = pd.read_csv(src["intermediate_path"])
    out = {"source": _describe_source(module_id, src), "rows_total": len(df), "columns": list(df.columns)}
    if query:
        df = df.query(query)
    out["rows_matched"] = len(df)
    if group_by:
        numeric = [c for c in (columns or df.columns) if c != group_by and pd.api.types.is_numeric_dtype(df[c])]
        grouped = df.groupby(group_by)
        summary = grouped[numeric].median().add_prefix("median_")
        summary.insert(0, "rows", grouped.size())
        return out | {"groups": _records(summary.reset_index().head(limit))}
    if sort_by:
        df = df.sort_values(sort_by, ascending=not descending, na_position="last")
    return out | {"rows": _records(df[columns or df.columns].head(limit))}


@mcp.tool()
@_quiet
def compare_results(
    module_id: str, source_a: str, source_b: str, key_columns: Optional[list[str]] = None, examples: int = 10
) -> dict:
    """
    Compare two results: overlap of their intermediate rows, parameter differences and metrics.

    Typical use: compare a local result with the best public datapoint, or with an older version of
    the same tool, to see which precursors (or spectra) only one of them reports.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    source_a : str
        An intermediate_hash from benchmark_result, or a public datapoint id or intermediate_hash.
    source_b : str
        Same as source_a, for the second result.
    key_columns : list[str], optional
        Columns that identify a row in the intermediate tables (default: the first column, e.g.
        "precursor ion" or "spectrum_id"). Check key_unique in the output; if False, pass more columns.
    examples : int
        Number of example keys listed for rows found in only one result.

    Returns
    -------
    dict
        Keys: a and b (source descriptions), key_columns, key_unique, overlap (shared, only_a, only_b;
        None with a note and the common columns when the key is not unique),
        examples_only_a, examples_only_b, merged_csv (outer join of both tables with _a/_b suffixes and a
        _merge column, for further analysis), parameter_differences and metrics (headline metrics of
        both).
    """
    src_a, src_b = _resolve(module_id, source_a), _resolve(module_id, source_b)
    df_a, df_b = pd.read_csv(src_a["intermediate_path"]), pd.read_csv(src_b["intermediate_path"])
    keys = key_columns or [df_a.columns[0]]
    missing = [k for k in keys if k not in df_a or k not in df_b]
    if missing:
        raise ValueError(f"Key columns {missing} not in both tables. Columns: {sorted(set(df_a) & set(df_b))}")
    params_a, metrics_a = _split_datapoint(src_a["datapoint"], module_id)
    params_b, metrics_b = _split_datapoint(src_b["datapoint"], module_id)
    out = {
        "a": _describe_source(module_id, src_a),
        "b": _describe_source(module_id, src_b),
        "key_columns": keys,
        "key_unique": not (df_a.duplicated(keys).any() or df_b.duplicated(keys).any()),
        "parameter_differences": {
            k: [params_a.get(k), params_b.get(k)]
            for k in sorted(set(params_a) | set(params_b))
            if params_a.get(k) != params_b.get(k)
        },
        "metrics": {k: [metrics_a.get(k), metrics_b.get(k)] for k in sorted(set(metrics_a) | set(metrics_b))},
    }
    if not out["key_unique"]:
        # A non-unique key would multiply rows in the join; ask for a better key instead.
        return out | {
            "overlap": None,
            "note": "key_columns do not identify rows uniquely; pass more columns as key_columns.",
            "common_columns": sorted(set(df_a) & set(df_b)),
        }
    merged = df_a.merge(df_b, on=keys, how="outer", suffixes=("_a", "_b"), indicator=True)
    counts = merged["_merge"].value_counts()

    def example_keys(side: str) -> list:  # numpydoc ignore=GL08
        return _records(merged.loc[merged["_merge"] == side, keys].head(examples))

    out_dir = CACHE_DIR / "comparisons" / module_id
    out_dir.mkdir(parents=True, exist_ok=True)
    merged_csv = out_dir / f"{src_a['datapoint']['intermediate_hash']}_vs_{src_b['datapoint']['intermediate_hash']}.csv"
    merged.to_csv(merged_csv, index=False)

    return out | {
        "overlap": {
            "shared": int(counts.get("both", 0)),
            "only_a": int(counts.get("left_only", 0)),
            "only_b": int(counts.get("right_only", 0)),
        },
        "examples_only_a": example_keys("left_only"),
        "examples_only_b": example_keys("right_only"),
        "merged_csv": os.fspath(merged_csv),
    }


@mcp.tool()
@_quiet
def render_plots(
    module_id: str,
    source: str,
    output_dir: Optional[str] = None,
    image_format: str = "html",
    include_main: bool = True,
) -> dict:
    """
    Write the in-depth plots of a result, and the main plot with all public datapoints, to files.

    These are the plots of the ProteoBench web interface. Use image_format "png" to view them as
    images (requires the ``kaleido`` package); "html" keeps them interactive.

    Parameters
    ----------
    module_id : str
        The module identifier, from list_modules.
    source : str
        An intermediate_hash from benchmark_result, or a public datapoint id or intermediate_hash.
    output_dir : str, optional
        Directory for the plot files (default: a directory next to the cached result).
    image_format : str
        "html" or "png".
    include_main : bool
        Also render the main plot: all public datapoints, plus the result when it is local.

    Returns
    -------
    dict
        Keys: source, files (plot name to path) and errors (plot name to error, for plots that failed).
    """
    if image_format not in ("html", "png"):
        raise ValueError("image_format must be 'html' or 'png'.")
    src = _resolve(module_id, source)
    module, generator = _module(module_id), _module(module_id).get_plot_generator()
    out_dir = Path(output_dir) if output_dir else src["intermediate_path"].parent / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    figures, errors = {}, {}
    # Most plot generators draw the in-depth plots from the intermediate table; de novo draws them from the
    # datapoint (its nested results). Try the table first and fall back to the datapoint.
    parse_settings = _builder(module_id).build_parser(src["datapoint"]["software_name"])
    attempts = []
    for performance in (lambda: pd.read_csv(src["intermediate_path"]), lambda: src["datapoint"].to_frame().T):
        try:
            figures |= generator.generate_in_depth_plots(performance(), parse_settings=parse_settings)
            break
        except Exception as exc:
            attempts.append(f"{type(exc).__name__}: {exc}")
    else:
        errors["in_depth"] = " | ".join(attempts)
    if include_main:
        try:
            datapoints = _public_datapoints(module_id).copy()
            if src["kind"] == "local":
                datapoints = pd.concat([datapoints, src["datapoint"].to_frame().T], ignore_index=True)
            filtered = module.filter_data_point(datapoints) if hasattr(module, "filter_data_point") else None
            # Modules without filtering return None.
            datapoints = filtered if filtered is not None else datapoints

            # label="None" is the web interface default (no point labels); the "" default fails.
            figures["main"] = generator.plot_main_metric(datapoints, label="None")
        except Exception as exc:
            errors["main"] = f"{type(exc).__name__}: {exc}"
    files = {}
    for name, figure in figures.items():
        if not hasattr(figure, "write_html"):
            continue
        path = out_dir / f"{name}.{image_format}"
        try:
            figure.write_html(path) if image_format == "html" else figure.write_image(path)
            files[name] = os.fspath(path)
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
    return {"source": _describe_source(module_id, src), "files": files, "errors": errors}


def main() -> None:
    """Run the server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
