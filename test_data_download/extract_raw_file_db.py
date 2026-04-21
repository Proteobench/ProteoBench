"""
Build a test-dataset catalog of ProteoBench submissions.

Subcommands:
    catalog     Download datapoint JSONs from all configured quant result repos and
                write one CSV row per submission. No raw quantification files are
                downloaded. Always downloads fresh (overwrites any existing folder
                under --json-dir for each repo).
    select      Reduce a catalog CSV to one representative row per
                (module, software_name, software_version) by picking the row with
                the smallest nr_prec (tiebreaker: lexicographic intermediate_hash).
    download    Download raw quantification files for the submissions listed in a
                catalog-style CSV. Files land at
                {json-dir}/{repo_name}/{intermediate_hash}/input_file.txt. Already
                present hashes are skipped.

Output CSV columns (catalog):
    module              - CONFIGS key (e.g. dda_qexactive)
    repo_name           - results repository name (e.g. Results_quant_ion_DDA)
    intermediate_hash
    software_name
    software_version
    nr_prec             - precursor count at the default cutoff (min_nr_observed=3)
    is_temporary
    old_new

Usage:
    uv run python extract_raw_file_db.py catalog [--output OUTPUT] \\
                                                 [--json-dir DIR] \\
                                                 [--modules KEY ...]
    uv run python extract_raw_file_db.py select [--input INPUT] [--output OUTPUT]
    uv run python extract_raw_file_db.py download [--input INPUT] \\
                                                  [--json-dir DIR] \\
                                                  [--output OUTPUT]
"""

import argparse
import json
import os
import shutil
from contextlib import chdir
from pathlib import Path

import pandas as pd

from proteobench.utils.server_io import get_merged_json, get_raw_data


CONFIGS = {
    "dda_qexactive": {"repo_url": "https://github.com/Proteobench/Results_quant_ion_DDA/archive/refs/heads/main.zip"},
    "dda_astral": {
        "repo_url": "https://github.com/Proteobench/Results_quant_ion_DDA_Astral/archive/refs/heads/main.zip"
    },
    "dda_peptidoform": {
        "repo_url": "https://github.com/Proteobench/Results_quant_peptidoform_DDA/archive/refs/heads/main.zip"
    },
    "dia_astral": {
        "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_Astral/archive/refs/heads/main.zip"
    },
    "dia_diapasef": {
        "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_diaPASEF/archive/refs/heads/main.zip"
    },
    "dia_aif": {"repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_AIF/archive/refs/heads/main.zip"},
    "dia_zenotof": {
        "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_ZenoTOF/archive/refs/heads/main.zip"
    },
    "dia_singlecell": {
        "repo_url": "https://github.com/Proteobench/Results_quant_ion_DIA_singlecell/archive/refs/heads/main.zip"
    },
}


def _download_module_jsons(repo_url: str, json_dir_root: Path) -> Path:
    """Download JSONs for one repo into `{json_dir_root}/{repo_name}/{repo_name}-main/`.

    Wipes any pre-existing `{json_dir_root}/{repo_name}` first so the download is
    authoritative. Returns the folder containing the *.json files.
    """
    repo_name = repo_url.split("/")[-5]
    target_parent = json_dir_root / repo_name
    target_json_dir = target_parent / f"{repo_name}-main"

    if target_parent.exists():
        shutil.rmtree(target_parent)

    json_dir_root.mkdir(parents=True, exist_ok=True)
    with chdir(json_dir_root):
        get_merged_json(repo_url=repo_url)

    if not target_json_dir.is_dir():
        raise RuntimeError(f"Expected extracted folder not found: {target_json_dir}")
    return target_json_dir


def cmd_catalog(args: argparse.Namespace) -> None:
    """Run the `catalog` subcommand."""
    module_keys = args.modules or list(CONFIGS.keys())
    json_dir_root = args.json_dir.resolve()

    rows: list[dict] = []
    for module_key in module_keys:
        repo_url = CONFIGS[module_key]["repo_url"]
        repo_name = repo_url.split("/")[-5]
        print(f"[{module_key}] downloading {repo_url}")
        json_dir = _download_module_jsons(repo_url, json_dir_root)

        json_files = sorted(json_dir.glob("*.json"))
        print(f"[{module_key}] read {len(json_files)} JSON file(s) from {json_dir}")

        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  skip {jf.name}: {e}")
                continue

            rows.append(
                {
                    "module": module_key,
                    "repo_name": repo_name,
                    "intermediate_hash": data.get("intermediate_hash", jf.stem),
                    "software_name": data.get("software_name", ""),
                    "software_version": data.get("software_version", ""),
                    "nr_prec": data.get("nr_prec"),
                    "is_temporary": data.get("is_temporary"),
                    "old_new": data.get("old_new", ""),
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)

    print(f"\nTotal rows: {len(df)}")
    print("\nRows per module:")
    print(df["module"].value_counts().to_string())
    print("\nUnique (software_name, software_version) per module:")
    unique_counts = df.groupby("module").apply(
        lambda g: g[["software_name", "software_version"]].drop_duplicates().shape[0],
        include_groups=False,
    )
    print(unique_counts.to_string())
    print(f"\nWritten to {args.output}")


def cmd_select(args: argparse.Namespace) -> None:
    """Run the `select` subcommand."""
    df = pd.read_csv(args.input)
    n_input = len(df)

    n_missing = int(df["nr_prec"].isna().sum())
    df = df.dropna(subset=["nr_prec"])

    group_cols = ["module", "software_name", "software_version"]
    selected = (
        df.sort_values(["nr_prec", "intermediate_hash"], kind="stable")
        .groupby(group_cols, dropna=False, as_index=False)
        .head(1)
        .reset_index(drop=True)
    )

    selected.to_csv(args.output, index=False)

    print(f"Input rows:           {n_input}")
    print(f"Dropped (nr_prec NA): {n_missing}")
    print(f"Selected rows:        {len(selected)}")
    print("\nSelected rows per module:")
    print(selected["module"].value_counts().to_string())
    print(f"\nWritten to {args.output}")


def get_datasets_to_download(df: pd.DataFrame, output_directory: Path) -> tuple[pd.DataFrame, dict]:
    """Check which datasets are already present in `output_directory`.

    Copied from `benchmark_analysis.py` — same idempotency logic.
    Returns (rows_still_to_download, {hash: extracted_dir} for rows already present).
    """
    hash_list = df["intermediate_hash"].tolist()
    existing_hashes = []
    hash_vis_dir: dict[str, str] = {}

    if output_directory.exists():
        for hash_dir in os.listdir(output_directory):
            if hash_dir in hash_list:
                existing_hashes.append(hash_dir)
                hash_vis_dir[hash_dir] = str(output_directory / hash_dir)

    if existing_hashes:
        df_to_download = df[~df["intermediate_hash"].isin(existing_hashes)]
        return df_to_download, hash_vis_dir
    return df, hash_vis_dir


def cmd_download(args: argparse.Namespace) -> None:
    """Run the `download` subcommand."""
    df = pd.read_csv(args.input)
    required = {"module", "repo_name", "intermediate_hash"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise SystemExit(f"Input CSV missing required columns: {sorted(missing_cols)}")

    json_dir_root = args.json_dir.resolve()
    json_dir_root.mkdir(parents=True, exist_ok=True)

    hash_to_dir: dict[str, str] = {}
    for repo_name, group in df.groupby("repo_name"):
        module_output_dir = json_dir_root / repo_name
        module_output_dir.mkdir(parents=True, exist_ok=True)

        df_to_download, already_present = get_datasets_to_download(group, module_output_dir)
        hash_to_dir.update(already_present)

        if len(df_to_download) > 0:
            print(
                f"[{repo_name}] downloading {len(df_to_download)} dataset(s) (already present: {len(already_present)})"
            )
            new_dirs = get_raw_data(df_to_download, output_directory=str(module_output_dir))
            hash_to_dir.update(new_dirs)
        else:
            print(f"[{repo_name}] all {len(group)} dataset(s) already present — skipping")

    out_rows = []
    for row in df.to_dict(orient="records"):
        h = row["intermediate_hash"]
        extract_dir = hash_to_dir.get(h)
        if extract_dir is None:
            row["input_file_path"] = ""
            row["input_file_size_bytes"] = None
            row["status"] = "not_on_server"
        else:
            inputs = sorted(Path(extract_dir).glob("input_file.*"))
            if inputs:
                inp = inputs[0]
                row["input_file_path"] = str(inp.relative_to(json_dir_root))
                row["input_file_size_bytes"] = inp.stat().st_size
                row["status"] = "ok"
            else:
                row["input_file_path"] = ""
                row["input_file_size_bytes"] = None
                row["status"] = "input_file_missing"
        out_rows.append(row)

    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(args.output, index=False)

    print(f"\nTotal rows:         {len(out_df)}")
    print("\nStatus breakdown:")
    print(out_df["status"].value_counts().to_string())
    print(f"\nWritten to {args.output}")


def build_database(results_dir: Path) -> pd.DataFrame:
    """Legacy: walk `results_dir` for locally-present module/hash folders and pair
    each intermediate_hash with its input_file.txt. Kept for the future `download`
    subcommand — not used by `catalog`.
    """
    rows = []

    for mod_dir in sorted(results_dir.iterdir()):
        if not mod_dir.is_dir():
            continue
        module = mod_dir.name

        main_dirs = list(mod_dir.glob("*-main"))
        if not main_dirs:
            continue
        json_dir = main_dirs[0]

        for hash_dir in sorted(mod_dir.iterdir()):
            if not hash_dir.is_dir() or hash_dir.name.endswith("-main"):
                continue

            intermediate_hash = hash_dir.name
            inp = hash_dir / "input_file.txt"
            jp = json_dir / f"{intermediate_hash}.json"

            if not jp.exists():
                rows.append(
                    {
                        "module": module,
                        "intermediate_hash": intermediate_hash,
                        "software_name": "",
                        "software_version": "",
                        "input_file_path": "",
                        "input_file_size_bytes": None,
                        "status": "json_missing",
                    }
                )
                continue

            meta = json.load(open(jp))
            software = meta.get("software_name", "")
            version = meta.get("software_version", "")

            if inp.exists():
                rel_path = inp.relative_to(results_dir)
                size = inp.stat().st_size
                status = "ok"
            else:
                rel_path = ""
                size = None
                status = "input_file_missing"

            rows.append(
                {
                    "module": module,
                    "intermediate_hash": intermediate_hash,
                    "software_name": software,
                    "software_version": version,
                    "input_file_path": str(rel_path),
                    "input_file_size_bytes": size,
                    "status": status,
                }
            )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_catalog = subparsers.add_parser(
        "catalog",
        help="Download datapoint JSONs for configured quant modules and write a catalog CSV.",
    )
    p_catalog.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "raw_file_db_full.csv",
        help="Output CSV path (default: ./raw_file_db_full.csv).",
    )
    p_catalog.add_argument(
        "--json-dir",
        type=Path,
        default=Path(__file__).parent / "temp_results",
        help="Directory under which per-repo JSON folders are placed (default: ./temp_results).",
    )
    p_catalog.add_argument(
        "--modules",
        nargs="+",
        choices=list(CONFIGS.keys()),
        default=None,
        help="Subset of module keys to process (default: all 8).",
    )
    p_catalog.set_defaults(func=cmd_catalog)

    p_select = subparsers.add_parser(
        "select",
        help="Reduce a catalog CSV to one representative row per (module, software, version).",
    )
    p_select.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent / "raw_file_db_full.csv",
        help="Input catalog CSV (default: ./raw_file_db_full.csv).",
    )
    p_select.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "raw_file_db_selected.csv",
        help="Output CSV path (default: ./raw_file_db_selected.csv).",
    )
    p_select.set_defaults(func=cmd_select)

    p_download = subparsers.add_parser(
        "download",
        help="Download raw quantification files for submissions in a CSV (full or selected).",
    )
    p_download.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent / "raw_file_db_selected.csv",
        help="Input CSV with module, repo_name, intermediate_hash columns (default: ./raw_file_db_selected.csv).",
    )
    p_download.add_argument(
        "--json-dir",
        type=Path,
        default=Path(__file__).parent / "json_dir",
        help="Root dir; raw files land at {json-dir}/{repo_name}/{hash}/ (default: ./json_dir).",
    )
    p_download.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "raw_file_db_downloaded.csv",
        help="Output CSV augmented with input_file_path, input_file_size_bytes, status (default: ./raw_file_db_downloaded.csv).",
    )
    p_download.set_defaults(func=cmd_download)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
