#!/usr/bin/env python3
"""
Resubmission script for ProteoBench datapoints.

Re-runs the ProteoBench benchmarking pipeline on previously submitted datapoints,
incorporating user parameter corrections from Proteobot PR bodies when available.

Usage:
    # Dry run — list what would be processed
    python resubmit_datapoints.py --dry-run

    # Reprocess a single datapoint to a test directory
    python resubmit_datapoints.py --output-dir /tmp/pb_test --hash abc123def456

    # Reprocess all datapoints of a specific module
    python resubmit_datapoints.py --module quant_lfq_DDA_ion_QExactive --output-dir /tmp/pb_test

    # Reprocess all MaxQuant submissions in-place
    python resubmit_datapoints.py --software MaxQuant

Environment variables:
    PROTEOBENCH_DATA_DIR  Path to the directory containing hash folders with zip archives (required)
    GITHUB_TOKEN          GitHub token for API access (required for PR listing)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import re
import sys
import tempfile
import time
import uuid
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from proteobench.github.gh import GithubProteobotRepo
from proteobench.io.parsing.utils import add_maxquant_fixed_modifications
from proteobench.modules.denovo.denovo_base import DeNovoModule
from proteobench.modules.denovo.denovo_DDA_HCD import DDAHCDDeNovoModule
from proteobench.modules.quant.quant_base_module import QuantModule
from proteobench.modules.quant.quant_lfq_ion_DDA_Astral import DDAQuantIonAstralModule
from proteobench.modules.quant.quant_lfq_ion_DDA_QExactive import (
    DDAQuantIonModuleQExactive,
)
from proteobench.modules.quant.quant_lfq_ion_DIA_AIF import DIAQuantIonModuleAIF
from proteobench.modules.quant.quant_lfq_ion_DIA_Astral import DIAQuantIonModuleAstral
from proteobench.modules.quant.quant_lfq_ion_DIA_diaPASEF import (
    DIAQuantIonModulediaPASEF,
)
from proteobench.modules.quant.quant_lfq_ion_DIA_Plasma import DIAQuantIonModulePlasma
from proteobench.modules.quant.quant_lfq_ion_DIA_singlecell import (
    DIAQuantIonModulediaSC,
)
from proteobench.modules.quant.quant_lfq_ion_DIA_ZenoTOF import DIAQuantIonModuleZenoTOF
from proteobench.modules.quant.quant_lfq_peptidoform_DDA import (
    DDAQuantPeptidoformModule,
)
from proteobench.modules.quant.quant_lfq_peptidoform_DIA import (
    DIAQuantPeptidoformModule,
)

# ---------------------------------------------------------------------------
# Registry: repo suffix -> (module_id, module_class, params_json_path)
#
# ** To add a new module, add ONE line here. **
#
# params_json_path is relative to the proteobench package directory.
# ---------------------------------------------------------------------------
_PARAMS_JSON_DIR = Path(__file__).parent / "proteobench" / "io" / "params" / "json"

REPO_MODULE_REGISTRY: dict[str, tuple[str, type, Path]] = {
    # fmt: off
    # Quant — DDA ion
    "Results_quant_ion_DDA":              ("quant_lfq_DDA_ion_QExactive",   DDAQuantIonModuleQExactive,  _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DDA_ion.json"),
    "Results_quant_ion_DDA_Astral":       ("quant_lfq_DDA_ion_Astral",      DDAQuantIonAstralModule,     _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DDA_ion.json"),
    # Quant — DDA peptidoform
    "Results_quant_peptidoform_DDA":      ("quant_lfq_DDA_peptidoform",     DDAQuantPeptidoformModule,   _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DDA_peptidoform.json"),
    # Quant — DIA ion
    "Results_quant_ion_DIA":              ("quant_lfq_DIA_ion_AIF",         DIAQuantIonModuleAIF,        _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DIA_ion.json"),
    "Results_quant_ion_DIA_diaPASEF":     ("quant_lfq_DIA_ion_diaPASEF",   DIAQuantIonModulediaPASEF,   _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DIA_ion.json"),
    "Results_quant_ion_DIA_singlecell":   ("quant_lfq_DIA_ion_singlecell", DIAQuantIonModulediaSC,      _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DIA_ion.json"),
    "Results_quant_ion_DIA_Astral":       ("quant_lfq_DIA_ion_Astral",     DIAQuantIonModuleAstral,     _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DIA_ion.json"),
    "Results_quant_lfq_DIA_ion_ZenoTOF":  ("quant_lfq_DIA_ion_ZenoTOF",   DIAQuantIonModuleZenoTOF,    _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DIA_ion.json"),
    "Results_quant_ion_DIA_plasma":       ("quant_lfq_DIA_ion_Plasma",     DIAQuantIonModulePlasma,     _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DIA_ion.json"), 
    # Quant — DIA peptidoform
    "Results_quant_peptidoform_DIA":      ("quant_lfq_DIA_peptidoform",     DIAQuantPeptidoformModule,   _PARAMS_JSON_DIR / "Quant" / "quant_lfq_DIA_peptidoform.json"),
    # De novo
    "Results_denovo_lfq_DDA_HCD":        ("denovo_DDA_HCD",                DDAHCDDeNovoModule,          _PARAMS_JSON_DIR / "denovo" / "denovo_DDA_HCD.json"),
    # fmt: on
}

# Inverted: module_id -> (repo_suffix, module_class, params_json_path)
MODULE_ID_REGISTRY: dict[str, tuple[str, type, Path]] = {v[0]: (k, v[1], v[2]) for k, v in REPO_MODULE_REGISTRY.items()}
logger = logging.getLogger("resubmit")


def setup_logging(log_file: str, verbose: bool = False) -> None:
    """Configure logging to both file and console."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)-7s] %(message)s"

    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def _gh_headers(token: str) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def _gh_get(url: str, token: str, params: dict | None = None) -> requests.Response:
    """GET with rate-limit awareness."""
    resp = requests.get(url, headers=_gh_headers(token), params=params or {}, timeout=30)
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        reset = int(resp.headers.get("X-RateLimit-Reset", 0))
        wait = max(reset - int(time.time()), 5)
        logger.warning(f"Rate-limited. Waiting {wait}s …")
        time.sleep(wait)
        resp = requests.get(url, headers=_gh_headers(token), params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp


def _gh_get_paginated(url: str, token: str, params: dict | None = None) -> list[dict]:
    """GET all pages of a paginated GitHub API endpoint."""
    params = dict(params or {})
    params.setdefault("per_page", 100)
    results: list[dict] = []
    while url:
        resp = _gh_get(url, token, params)
        results.extend(resp.json())
        # Follow 'next' link header
        url = None
        if "Link" in resp.headers:
            for part in resp.headers["Link"].split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip().strip("<>")
                    params = {}  # params are already embedded in the next URL
                    break
    return results


# Build hash → module mapping from Proteobench repo contents
def build_hash_to_module_mapping(
    token: str,
    module_filter: str | None = None,
) -> dict[str, tuple[str, str, type, Path]]:
    """
    Scan all Proteobench/Results_* repos to build a mapping:
        intermediate_hash -> (module_id, repo_suffix, module_class, params_json_path)

    Parameters
    ----------
    token : str
        GitHub API token.
    module_filter : str, optional
        If set, only scan the repo for this module_id.

    Returns
    -------
    dict
        Mapping of intermediate_hash to (module_id, repo_suffix, module_class, params_json_path).
    """
    mapping: dict[str, tuple[str, str, type, Path]] = {}

    for repo_suffix, (module_id, module_class, params_json) in REPO_MODULE_REGISTRY.items():
        if module_filter and module_id != module_filter:
            continue

        org_repo = f"Proteobench/{repo_suffix}"
        logger.info(f"Scanning {org_repo} for datapoint hashes …")

        try:
            url = f"https://api.github.com/repos/{org_repo}/contents/"
            items = _gh_get(url, token).json()
        except requests.HTTPError as e:
            logger.warning(f"Could not list {org_repo}: {e}")
            continue

        if not isinstance(items, list):
            logger.warning(f"Unexpected response from {org_repo}: {items}")
            continue

        count = 0
        for item in items:
            name = item.get("name", "")
            if name.endswith(".json") and name != "results.json":
                h = name[:-5]  # strip .json
                mapping[h] = (module_id, repo_suffix, module_class, params_json)
                count += 1

        logger.info(f"  Found {count} datapoints in {org_repo}")

    logger.info(f"Total hash→module mappings: {len(mapping)}")
    return mapping


_json_cache: dict[str, dict] = {}


def fetch_datapoint_json(intermediate_hash: str, repo_suffix: str, token: str) -> dict:
    """Fetch and cache the JSON content of a datapoint from a Proteobench repo."""
    cache_key = f"{repo_suffix}/{intermediate_hash}"
    if cache_key in _json_cache:
        return _json_cache[cache_key]

    url = f"https://api.github.com/repos/Proteobench/{repo_suffix}/contents/{intermediate_hash}.json"
    resp = _gh_get(url, token)
    data = resp.json()

    import base64

    content = base64.b64decode(data["content"]).decode("utf-8")
    dp = json.loads(content)
    _json_cache[cache_key] = dp
    return dp


# Regex to extract hash from PR body: "datasets/<hash>/"
_RE_DATASET_HASH = re.compile(r"datasets/([a-f0-9]{20,})/")

# Regex to find any standalone 40-char hex string
_RE_HEX40 = re.compile(r"(?<![a-f0-9])([a-f0-9]{40})(?![a-f0-9])")

# Regex to extract parameter change lines:
#   - **key**: `old_value` → `new_value`
_RE_PARAM_CHANGE = re.compile(r"-\s*\*\*(\w+)\*\*:\s*`([^`]*)`\s*→\s*`([^`]*)`")

# Regex to extract persisted corrections from comment.txt
# Format: CORRECTION:<key>=<value>
_RE_PERSISTED_CORRECTION = re.compile(r"^CORRECTION:(\w+)=(.*)$", re.MULTILINE)


def _load_persisted_corrections(comment_path: str | None) -> dict[str, str]:
    """
    Load parameter corrections previously persisted in comment.txt.

    These are written by earlier resubmission runs so that user corrections
    survive across multiple re-runs.

    Returns
    -------
    dict
        {param_key: corrected_value_str}
    """
    if not comment_path or not os.path.exists(comment_path):
        return {}

    with open(comment_path, "r", encoding="utf-8") as f:
        content = f.read()

    persisted: dict[str, str] = {}
    for match in _RE_PERSISTED_CORRECTION.finditer(content):
        key, val = match.group(1), match.group(2)
        persisted[key] = val

    return persisted


def _serialize_corrections_for_persistence(
    corrections: dict[str, tuple[str, str]],
) -> str:
    """
    Serialize parameter corrections into a machine-readable block
    that can be appended to comment.txt and parsed on future runs.

    Format:
        --- PERSISTED_CORRECTIONS ---
        CORRECTION:key1=value1
        CORRECTION:key2=value2
        --- END_PERSISTED_CORRECTIONS ---
    """
    if not corrections:
        return ""

    lines = ["--- PERSISTED_CORRECTIONS ---"]
    for key, (_, new_val) in corrections.items():
        lines.append(f"CORRECTION:{key}={new_val}")
    lines.append("--- END_PERSISTED_CORRECTIONS ---")
    return "\n".join(lines)


def _extract_hash_from_pr(
    pr: dict,
    token: str,
    org_repo: str,
) -> str | None:
    """
    Try to extract the intermediate hash from a PR using multiple strategies:

    1. Dataset URL in body  (``datasets/<hash>/``)
    2. Any 40-char hex string in body or title
    3. PR head branch ref (may contain the hash)
    4. PR files endpoint:
       a. filename ``<hash>.json``
       b. 40-char hex in the patch diff (e.g. ``"intermediate_hash": "<hash>"``)
    """
    pr_num = pr.get("number", "?")
    body = pr.get("body", "") or ""
    title = pr.get("title", "") or ""

    # Strategy 1: dataset URL in body
    m = _RE_DATASET_HASH.search(body)
    if m:
        return m.group(1)

    # Strategy 2: bare 40-char hex in body or title
    for text in (body, title):
        m = _RE_HEX40.search(text)
        if m:
            return m.group(1)

    # Strategy 3: head branch ref (Proteobot often names it after the hash)
    head_ref = pr.get("head", {}).get("ref", "") or ""
    m = _RE_HEX40.search(head_ref)
    if m:
        return m.group(1)

    # --- At this point, strategies 1-3 failed. Build diagnostic info ---
    pr_diag_parts = [f"PR #{pr_num} in {org_repo}"]
    if not body:
        pr_diag_parts.append("body=empty")
    else:
        pr_diag_parts.append(f"body={len(body)}ch")
    if not title:
        pr_diag_parts.append("title=empty")
    else:
        pr_diag_parts.append(f"title={title!r}")
    if head_ref:
        pr_diag_parts.append(f"branch={head_ref!r}")

    # Strategy 4: list changed files
    try:
        files_url = pr.get("url", "") + "/files"
        files_response = _gh_get(files_url, token)
        files = files_response.json()
        if isinstance(files, list):
            filenames = [f.get("filename", "") for f in files]
            has_patch = any(f.get("patch") for f in files)

            if not filenames:
                pr_diag_parts.append("files=none")
            else:
                pr_diag_parts.append(f"files={filenames}")
                if not has_patch:
                    pr_diag_parts.append("patch=omitted")

            # 4a: filename is <hash>.json
            for f in files:
                fname = f.get("filename", "")
                base = fname.rsplit("/", 1)[-1]
                if base.endswith(".json"):
                    candidate = base[:-5]
                    if _RE_HEX40.fullmatch(candidate):
                        return candidate

            # 4b: search patch content for "intermediate_hash" or any 40-char hex
            for f in files:
                patch = f.get("patch", "") or ""
                if patch:
                    m = _RE_HEX40.search(patch)
                    if m:
                        return m.group(1)
        else:
            pr_diag_parts.append(f"files_response={type(files).__name__}")
    except Exception as e:
        pr_diag_parts.append(f"files_error={e}")

    logger.debug(f"  {' | '.join(pr_diag_parts)} → no hash found")
    return None


def _parse_param_corrections(body: str) -> dict[str, tuple[str, str]]:
    """
    Parse parameter correction lines from a PR body.

    Returns
    -------
    dict
        {param_key: (old_value_str, new_value_str)}
        Empty dict if no "Parameter changes detected" section or
        if the section says "No parameter changes detected".
    """
    if not body:
        return {}

    # Check if there's a "Parameter changes detected" section
    if "Parameter changes detected" not in body:
        return {}

    # Check for the explicit "No parameter changes detected" message
    if "No parameter changes detected" in body:
        return {}

    corrections: dict[str, tuple[str, str]] = {}
    for match in _RE_PARAM_CHANGE.finditer(body):
        key, old_val, new_val = match.group(1), match.group(2), match.group(3)
        corrections[key] = (old_val, new_val)

    return corrections


def build_hash_to_pr_corrections(
    token: str,
    repo_suffixes: set[str],
) -> dict[str, dict[str, tuple[str, str]]]:
    """
    Scan merged PRs in Proteobot repos to build:
        intermediate_hash -> {param_key: (old_value, new_value)}

    PRs without parameter changes return an empty dict for that hash
    (meaning: use parsed params as-is). Hashes not found in any PR
    will not appear in the mapping (→ skip that datapoint).

    Parameters
    ----------
    token : str
        GitHub API token.
    repo_suffixes : set[str]
        Set of repo suffixes to scan (e.g., {"Results_quant_ion_DDA"}).

    Returns
    -------
    dict
        Mapping of intermediate_hash to parameter corrections dict.
    """
    mapping: dict[str, dict[str, tuple[str, str]]] = {}

    for repo_suffix in sorted(repo_suffixes):
        org_repo = f"Proteobot/{repo_suffix}"
        logger.info(f"Scanning merged PRs in {org_repo} …")

        try:
            url = f"https://api.github.com/repos/{org_repo}/pulls"
            prs = _gh_get_paginated(url, token, params={"state": "closed"})
        except requests.HTTPError as e:
            logger.warning(f"Could not list PRs for {org_repo}: {e}")
            continue

        pr_count = 0
        for pr in prs:
            # Only merged PRs
            if not pr.get("merged_at"):
                continue

            body = pr.get("body", "") or ""

            # Extract the intermediate hash using multi-strategy fallback
            intermediate_hash = _extract_hash_from_pr(pr, token, org_repo)
            if not intermediate_hash:
                # Diagnostic already logged inside _extract_hash_from_pr
                continue

            corrections = _parse_param_corrections(body)

            # Only store the FIRST (i.e. original) PR's corrections for a given hash.
            # Resubmission PRs don't contain parameter corrections, so they'd
            # overwrite the original corrections with an empty dict.
            if intermediate_hash not in mapping:
                mapping[intermediate_hash] = corrections
            elif corrections and not mapping[intermediate_hash]:
                # Edge case: earlier PR had no corrections, later one does
                mapping[intermediate_hash] = corrections

            pr_count += 1

        logger.info(f"  Matched {pr_count} merged PRs with hashes in {org_repo}")

    logger.info(f"Total hash→PR-corrections mappings: {len(mapping)}")
    return mapping


def discover_datapoints(
    data_dir: str,
) -> dict[str, Path]:
    """
    Scan PROTEOBENCH_DATA_DIR for hash folders containing a zip archive.

    Returns
    -------
    dict
        {intermediate_hash: Path_to_zip}
    """
    found: dict[str, Path] = {}
    data_path = Path(data_dir)

    if not data_path.is_dir():
        logger.error(f"Data directory does not exist: {data_dir}")
        return found

    for entry in data_path.iterdir():
        if not entry.is_dir():
            continue
        h = entry.name
        zip_path = entry / f"{h}_data.zip"
        if zip_path.is_file():
            found[h] = zip_path
        else:
            logger.debug(f"  No zip found for hash {h}, skipping")

    logger.info(f"Found {len(found)} hash folders with zip archives on disk")
    return found


def _safe_extract_member(zf: zipfile.ZipFile, member_name: str, tmp_dir: str) -> str | None:
    """
    Safely extract a zip member, validating the path to prevent Zip Slip attacks.

    Parameters
    ----------
    zf : zipfile.ZipFile
        Open zip file object.
    member_name : str
        Name of the member to extract.
    tmp_dir : str
        Base directory for extraction.

    Returns
    -------
    str | None
        Absolute path to extracted file, or None if path validation failed.
    """
    # Normalize the member name and check for path traversal attempts
    member_normalized = os.path.normpath(member_name)

    # Reject absolute paths
    if os.path.isabs(member_normalized):
        logger.warning(f"Rejecting zip member with absolute path: {member_name}")
        return None

    # Reject paths containing .. or starting with /
    if member_normalized.startswith("..") or "/.." in member_normalized or "\\.." in member_normalized:
        logger.warning(f"Rejecting zip member with path traversal: {member_name}")
        return None

    # Construct the target path and verify it's within tmp_dir
    tmp_dir_abs = os.path.abspath(tmp_dir)
    target_path = os.path.abspath(os.path.join(tmp_dir, member_normalized))

    # Ensure the resolved path is still within tmp_dir
    if not target_path.startswith(tmp_dir_abs + os.sep) and target_path != tmp_dir_abs:
        logger.warning(f"Rejecting zip member that resolves outside tmp_dir: {member_name}")
        return None

    # Create parent directory if needed
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)

    # Safely extract the member
    with zf.open(member_name) as source, open(target_path, "wb") as target:
        target.write(source.read())

    return target_path


def extract_zip_contents(zip_path: Path, tmp_dir: str) -> dict[str, str]:
    """
    Extract relevant files from a datapoint zip archive.

    Returns
    -------
    dict with keys:
        "input_file": path to extracted input file
        "input_file_secondary": path or None
        "param_files": list of paths to param files
        "result_performance": path to result_performance.csv
        "comment": path to comment.txt
        "input_file_ext": extension of the input file
        "param_file_ext": extension of parameter files
    """
    result: dict[str, Any] = {
        "input_file": None,
        "input_file_secondary": None,
        "param_files": [],
        "result_performance": None,
        "comment": None,
        "input_file_ext": ".txt",
        "param_file_ext": ".txt",
    }

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            # Safely extract the member, validating path to prevent Zip Slip
            extracted = _safe_extract_member(zf, member, tmp_dir)

            # Skip if extraction failed due to path validation
            if extracted is None:
                continue

            if member.startswith("input_file_secondary"):
                result["input_file_secondary"] = extracted
            elif member.startswith("input_file"):
                result["input_file"] = extracted
                _, ext = os.path.splitext(member)
                if ext:
                    result["input_file_ext"] = ext
            elif member.startswith("param_"):
                result["param_files"].append(extracted)
                _, ext = os.path.splitext(member)
                if ext:
                    result["param_file_ext"] = ext
            elif member == "result_performance.csv":
                result["result_performance"] = extracted
            elif member == "comment.txt":
                result["comment"] = extracted

    # Sort param files by name to ensure correct ordering
    result["param_files"].sort()
    return result


def reconstruct_user_input(dp_json: dict, params_json_path: Path) -> dict[str, Any]:
    """
    Reconstruct the user_input dict from a datapoint JSON.

    The mapping between JSON datapoint fields and user_input keys is an identity
    mapping (same key names).  Additionally, user_input["comments_for_plotting"]
    is set from the JSON "comments" field.
    """
    user_input: dict[str, Any] = defaultdict(lambda: "")

    # Load the param config JSON to know which keys to expect
    with open(params_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Set all keys from the config, pulling values from the datapoint JSON
    for key in config:
        user_input[key] = dp_json.get(key, None)

    # Map the "comments" field to the expected key
    user_input["comments_for_plotting"] = dp_json.get("comments", "")

    return dict(user_input)


def _coerce_value(val_str: str) -> Any:
    """
    Coerce a string value parsed from a PR body back to a Python type.
    Handles None, nan, numeric, and string values.
    """
    if val_str == "None":
        return None
    if val_str == "nan":
        return np.nan
    # Try numeric
    try:
        # Integer first
        if "." not in val_str:
            return int(val_str)
        return float(val_str)
    except (ValueError, OverflowError):
        pass
    return val_str


def apply_pr_corrections(
    user_input: dict[str, Any],
    parsed_params: Any,
    corrections: dict[str, tuple[str, str]],
    intermediate_hash: str,
) -> dict[str, Any]:
    """
    Apply parameter corrections from a PR to the user_input dict.
    Also logs whether current parsing already produces the corrected value.

    Parameters
    ----------
    user_input : dict
        The reconstructed user_input dict.
    parsed_params : object
        The freshly parsed ProteoBenchParameters object.
    corrections : dict
        {param_key: (old_value_str, new_value_str)} from PR body.
    intermediate_hash : str
        For logging context.

    Returns
    -------
    dict
        Updated user_input.
    """
    if not corrections:
        return user_input

    for key, (old_str, new_str) in corrections.items():
        new_val = _coerce_value(new_str)
        old_val = _coerce_value(old_str)

        # What did the current parsing produce?
        auto_parsed = getattr(parsed_params, key, "[MISSING]")

        # Compare: does current parsing now produce the corrected value?
        auto_matches_new = _values_equal(auto_parsed, new_val)
        auto_matches_old = _values_equal(auto_parsed, old_val)

        if auto_matches_new:
            logger.info(
                f"  [{intermediate_hash[:12]}] {key}: parsing now auto-produces "
                f"corrected value '{new_str}' (override not needed)"
            )
        elif auto_matches_old:
            logger.info(
                f"  [{intermediate_hash[:12]}] {key}: parsing still produces "
                f"old value '{old_str}', applying override → '{new_str}'"
            )
        else:
            logger.warning(
                f"  [{intermediate_hash[:12]}] {key}: unexpected parsed value "
                f"'{auto_parsed}' (expected old='{old_str}' or new='{new_str}'). "
                f"Applying new value '{new_str}'"
            )

        # Always apply the user-corrected value
        user_input[key] = new_val

        # Also update the parsed_params object so it's consistent
        if hasattr(parsed_params, key):
            setattr(parsed_params, key, new_val)

    return user_input


def _values_equal(a: Any, b: Any) -> bool:
    """Compare two values, handling NaN and None correctly."""
    if a is None and b is None:
        return True
    if isinstance(a, float) and isinstance(b, float):
        if np.isnan(a) and np.isnan(b):
            return True
    try:
        return str(a) == str(b)
    except Exception:
        return a == b


def compare_results(
    old_csv_path: str,
    new_intermediate: pd.DataFrame,
) -> dict[str, Any]:
    """
    Compare old and new result_performance DataFrames.

    Returns a summary dict with:
        changed: bool
        old_rows, new_rows: int
        added_cols, removed_cols: list[str]
        numeric_diffs: dict of summary stats for changed numeric columns
    """
    summary: dict[str, Any] = {
        "changed": False,
        "old_rows": 0,
        "new_rows": 0,
        "added_cols": [],
        "removed_cols": [],
        "numeric_diffs": {},
    }

    try:
        old_df = pd.read_csv(old_csv_path)
    except Exception as e:
        summary["changed"] = True
        summary["error"] = f"Could not read old CSV: {e}"
        return summary

    summary["old_rows"] = len(old_df)
    summary["new_rows"] = len(new_intermediate)

    old_cols = set(old_df.columns)
    new_cols = set(new_intermediate.columns)
    summary["added_cols"] = sorted(new_cols - old_cols)
    summary["removed_cols"] = sorted(old_cols - new_cols)

    if summary["added_cols"] or summary["removed_cols"]:
        summary["changed"] = True

    if len(old_df) != len(new_intermediate):
        summary["changed"] = True

    # Compare numeric columns that exist in both
    common_cols = old_cols & new_cols
    for col in sorted(common_cols):
        if not pd.api.types.is_numeric_dtype(old_df[col]) or not pd.api.types.is_numeric_dtype(new_intermediate[col]):
            continue

        if len(old_df) != len(new_intermediate):
            # Can't do element-wise comparison with different lengths
            continue

        try:
            diff = (old_df[col] - new_intermediate[col]).dropna()
            if diff.abs().sum() > 1e-10:
                summary["changed"] = True
                summary["numeric_diffs"][col] = {
                    "mean_abs_diff": float(diff.abs().mean()),
                    "max_abs_diff": float(diff.abs().max()),
                    "n_changed": int((diff.abs() > 1e-10).sum()),
                }
        except Exception:
            pass

    return summary


def write_updated_zip(
    original_zip_path: Path,
    new_intermediate: pd.DataFrame,
    output_dir: str | None,
    intermediate_hash: str,
    resubmit_note: str,
) -> str:
    """
    Rebuild the zip with updated result_performance.csv and comment.txt.

    If output_dir is set, write to {output_dir}/{hash}/.
    Otherwise, overwrite in-place.
    """
    if output_dir:
        dest_dir = Path(output_dir) / intermediate_hash
    else:
        dest_dir = original_zip_path.parent

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_zip = dest_dir / f"{intermediate_hash}_data.zip"

    # Read old zip contents
    old_members: dict[str, bytes] = {}
    with zipfile.ZipFile(original_zip_path, "r") as zf_old:
        for member in zf_old.namelist():
            old_members[member] = zf_old.read(member)

    # Rebuild zip
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf_new:
        for member_name, content in old_members.items():
            if member_name == "result_performance.csv":
                # Replace with new data
                new_csv = new_intermediate.to_csv(index=False)
                zf_new.writestr("result_performance.csv", new_csv)
            elif member_name == "comment.txt":
                # Append resubmission note
                old_comment = content.decode("utf-8", errors="replace")
                updated_comment = old_comment + "\n\n" + resubmit_note
                zf_new.writestr("comment.txt", updated_comment)
            else:
                # Keep as-is
                zf_new.writestr(member_name, content)

    return str(dest_zip)


def write_updated_files(
    original_zip_path: Path,
    new_intermediate: pd.DataFrame,
    output_dir: str | None,
    intermediate_hash: str,
    resubmit_note: str,
) -> str:
    """
    Write updated outputs as loose files (no zip) for easier inspection.

    Produces:
        {dest_dir}/input_file*           — original input file(s)
        {dest_dir}/param_*               — original parameter files
        {dest_dir}/result_performance.csv — NEW
        {dest_dir}/comment.txt           — updated with resubmit note
    """
    if output_dir:
        dest_dir = Path(output_dir) / intermediate_hash
    else:
        dest_dir = original_zip_path.parent

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Extract all original members from zip
    with zipfile.ZipFile(original_zip_path, "r") as zf_old:
        for member in zf_old.namelist():
            content = zf_old.read(member)
            out_path = dest_dir / member

            if member == "result_performance.csv":
                new_csv = new_intermediate.to_csv(index=False)
                out_path.write_text(new_csv, encoding="utf-8")
            elif member == "comment.txt":
                old_comment = content.decode("utf-8", errors="replace")
                updated_comment = old_comment + "\n\n" + resubmit_note
                out_path.write_text(updated_comment, encoding="utf-8")
            else:
                out_path.write_bytes(content)

    return str(dest_dir)


def write_datapoint_json(
    json_data: dict[str, Any],
    output_dir: str,
    intermediate_hash: str,
) -> str:
    """
    Write a datapoint JSON to the output directory.

    Produces:
        {output_dir}/{intermediate_hash}/{intermediate_hash}.json

    Parameters
    ----------
    json_data : dict
        The datapoint dict (from ``pd.Series.to_dict()``).
    output_dir : str
        Root output directory.
    intermediate_hash : str
        Hash identifying the datapoint (used for subdirectory and filename).

    Returns
    -------
    str
        Path to the written JSON file.
    """
    dest_dir = Path(output_dir) / intermediate_hash
    dest_dir.mkdir(parents=True, exist_ok=True)

    json_path = dest_dir / f"{intermediate_hash}.json"
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2, default=str)

    return str(json_path)


# Batch PR creation for Proteobot repos

# Mapping from repo suffix → proteobot repo full name
_PROTEOBOT_REPO_MAP: dict[str, str] = {suffix: f"Proteobot/{suffix}" for suffix in REPO_MODULE_REGISTRY}

# Mapping from repo suffix → proteobench repo full name
_PROTEOBENCH_REPO_MAP: dict[str, str] = {suffix: f"Proteobench/{suffix}" for suffix in REPO_MODULE_REGISTRY}


def create_batch_pr(
    token: str,
    repo_suffix: str,
    datapoint_updates: list[dict[str, Any]],
    hashes_to_delete: list[str] | None = None,
) -> str | None:
    """
    Create a single PR on a Proteobot Results repo with all updated datapoint JSONs.

    Each element of *datapoint_updates* should have:
        - ``old_hash``: the original intermediate_hash (file to remove if changed)
        - ``new_hash``: the new intermediate_hash (file to create)
        - ``json_data``: the full datapoint dict to serialise

    Parameters
    ----------
    token : str
        GitHub token (must have push access to the Proteobot repo).
    repo_suffix : str
        Repository suffix, e.g. ``Results_quant_ion_DDA``.
    datapoint_updates : list[dict]
        List of update dicts as described above.
    hashes_to_delete : list[str], optional
        Intermediate hashes whose JSON files should be deleted from the repo
        (used when ``--delete-failed`` is set).

    Returns
    -------
    str | None
        URL of the created PR, or ``None`` on failure.
    """
    hashes_to_delete = hashes_to_delete or []
    if not datapoint_updates and not hashes_to_delete:
        return None

    if not token:
        logger.error(f"Cannot create PR for {repo_suffix}: no GITHUB_TOKEN set.")
        return None

    proteobot_name = _PROTEOBOT_REPO_MAP.get(repo_suffix)
    proteobench_name = _PROTEOBENCH_REPO_MAP.get(repo_suffix)
    if not proteobot_name or not proteobench_name:
        logger.error(f"Unknown repo suffix: {repo_suffix}")
        return None

    logger.info(
        f"Creating PR on {proteobot_name} with {len(datapoint_updates)} update(s), "
        f"{len(hashes_to_delete)} deletion(s) …"
    )

    with tempfile.TemporaryDirectory() as clone_dir, tempfile.TemporaryDirectory() as clone_dir_pr:
        gh_repo = GithubProteobotRepo(
            token=token,
            clone_dir=clone_dir,
            clone_dir_pr=clone_dir_pr,
            proteobench_repo_name=proteobench_name,
            proteobot_repo_name=proteobot_name,
        )

        try:
            gh_repo.clone_repo_pr()
        except Exception as e:
            logger.error(f"Failed to clone {proteobot_name}: {e}")
            return None

        # Create a unique branch for the batch resubmission
        hash_input = f"resubmit_{datetime.now().isoformat()}_{uuid.uuid4()}".encode("utf-8")
        short_hash = hashlib.sha256(hash_input).hexdigest()[:10]
        branch_name = f"resubmit_batch_{short_hash}"

        try:
            gh_repo.create_branch(branch_name)
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return None

        # Write / replace JSON files in the cloned repo
        changes_made = 0
        for upd in datapoint_updates:
            old_hash = upd["old_hash"]
            new_hash = upd["new_hash"]
            json_data = upd["json_data"]

            new_json_path = os.path.join(clone_dir_pr, f"{new_hash}.json")

            # When the hash changed, use `git mv` so GitHub renders the PR diff
            # as a rename+edit rather than an unrelated delete+create.
            if old_hash != new_hash:
                old_json_path = os.path.join(clone_dir_pr, f"{old_hash}.json")
                if os.path.exists(old_json_path):
                    # Use relative paths for git commands (relative to repo root)
                    gh_repo.repo.git.mv(f"{old_hash}.json", f"{new_hash}.json")
                    logger.debug(f"  git mv {old_hash[:12]}.json → {new_hash[:12]}.json")

            # Write (or overwrite after rename) the new content
            with open(new_json_path, "w") as f:
                json.dump(json_data, f, indent=2, default=str)
            changes_made += 1
            logger.debug(f"  Wrote {new_hash[:12]}.json")

        # Delete JSON files for failed datapoints (if requested)
        deletions_made = 0
        for del_hash in hashes_to_delete:
            del_path = os.path.join(clone_dir_pr, f"{del_hash}.json")
            if os.path.exists(del_path):
                # Use relative path for git command (relative to repo root)
                gh_repo.repo.git.rm(f"{del_hash}.json")
                deletions_made += 1
                logger.debug(f"  git rm {del_hash[:12]}.json (failed resubmission)")
            else:
                logger.warning(f"  [{del_hash[:12]}] JSON not found in repo, skipping deletion")

        if changes_made == 0 and deletions_made == 0:
            logger.warning(f"No JSON changes to commit for {repo_suffix}")
            return None

        n_updates = len(datapoint_updates)
        n_deletions = deletions_made
        action_parts = []
        if n_updates:
            action_parts.append(f"resubmit {n_updates} datapoint(s)")
        if n_deletions:
            action_parts.append(f"delete {n_deletions} failed datapoint(s)")
        commit_name = f"{'; '.join(action_parts).capitalize()} via batch resubmission script"
        commit_message = f"Batch resubmission using ProteoBench v{_get_proteobench_version()}.\n\n"
        if n_deletions:
            commit_message += "\n\nDeleted (failed resubmission):\n" + "\n".join(
                f"  {h[:12]}" for h in hashes_to_delete[:n_deletions]
            )

        try:
            gh_repo.commit(commit_name, commit_message)
            pr_number = gh_repo.create_pull_request(commit_name, commit_message)
            pr_url = f"https://github.com/{proteobot_name}/pull/{pr_number}"
            logger.info(f"  PR created: {pr_url}")
            return pr_url
        except Exception as e:
            logger.error(f"Failed to create PR for {repo_suffix}: {e}")
            return None


def _get_proteobench_version() -> str:
    """Get the current proteobench version string."""
    try:
        import proteobench

        return proteobench.__version__
    except Exception:
        return "unknown"


# Module instance cache

_module_cache: dict[str, Any] = {}


def get_module_instance(
    module_id: str,
    module_class: type,
    token: str,
) -> Any:
    """Get or create a cached module instance."""
    if module_id in _module_cache:
        return _module_cache[module_id]

    logger.info(f"Instantiating module {module_id} ({module_class.__name__}) …")
    try:
        instance = module_class(token=token)
        _module_cache[module_id] = instance
        return instance
    except NotImplementedError:
        logger.warning(f"Module {module_id} raises NotImplementedError — skipping")
        _module_cache[module_id] = None
        return None
    except Exception as e:
        logger.error(f"Failed to instantiate {module_id}: {e}")
        _module_cache[module_id] = None
        return None


# Main reprocessing logic


def reprocess_datapoint(
    intermediate_hash: str,
    zip_path: Path,
    module_id: str,
    repo_suffix: str,
    module_class: type,
    params_json_path: Path,
    corrections: dict[str, tuple[str, str]],
    token: str,
    output_dir: str | None,
    no_zip: bool = False,
) -> dict[str, Any]:
    """
    Reprocess a single datapoint.

    Returns a status dict with keys: status, message, comparison, ...
    """
    result: dict[str, Any] = {
        "hash": intermediate_hash,
        "module_id": module_id,
        "status": "unknown",
        "message": "",
    }

    # --- 6a: Extract zip ---
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            extracted = extract_zip_contents(zip_path, tmp_dir)
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Failed to extract zip: {e}"
            return result

        if not extracted["input_file"]:
            result["status"] = "error"
            result["message"] = "No input_file found in zip"
            return result

        # --- Load persisted corrections from previous resubmission runs ---
        persisted = _load_persisted_corrections(extracted.get("comment"))

        # --- 6b: Get input_format from JSON ---
        try:
            dp_json = fetch_datapoint_json(intermediate_hash, repo_suffix, token)
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Failed to fetch datapoint JSON: {e}"
            return result

        input_format = dp_json.get("software_name")
        if not input_format:
            result["status"] = "error"
            result["message"] = "No software_name in datapoint JSON"
            return result

        result["software_name"] = input_format

        # --- 6c: Reconstruct user_input ---
        user_input = reconstruct_user_input(dp_json, params_json_path)
        user_input["input_format"] = input_format

        # --- 6d: Re-parse parameter file & apply corrections ---
        module_instance = get_module_instance(module_id, module_class, token)
        if module_instance is None:
            result["status"] = "skipped"
            result["message"] = "Module not instantiable (NotImplementedError or error)"
            return result

        parsed_params = None
        if extracted["param_files"]:
            # Wrap param file paths in BytesIO so extract_params functions that
            # expect file-like objects (e.g. FragPipe, quantms) work correctly.
            param_file_objects: list[io.BytesIO] = []
            for p in extracted["param_files"]:
                with open(p, "rb") as fh:
                    param_file_objects.append(io.BytesIO(fh.read()))

            try:
                if isinstance(module_instance, QuantModule):
                    parsed_params = module_instance.load_params_file(
                        param_file_objects,
                        input_format,
                        json_file=str(params_json_path),
                    )
                else:
                    parsed_params = module_instance.load_params_file(
                        param_file_objects,
                        input_format,
                    )
            except Exception as e:
                logger.warning(
                    f"  [{intermediate_hash[:12]}] Could not parse param file: {e}. "
                    f"Proceeding with user_input from JSON only."
                )

        # Merge: PR corrections take priority, then persisted corrections fill gaps.
        # This ensures that if a PR has corrections, those are used;
        # but if the hash changed and the PR can't be found, persisted corrections survive.
        effective_corrections: dict[str, tuple[str, str]] = dict(corrections)
        for key, val_str in persisted.items():
            if key not in effective_corrections:
                effective_corrections[key] = ("(persisted)", val_str)
                logger.info(
                    f"  [{intermediate_hash[:12]}] {key}: using persisted correction "
                    f"from previous run → '{val_str}'"
                )

        # Apply effective corrections (PR + persisted)
        if effective_corrections:
            n_from_pr = len(corrections)
            n_persisted = len(effective_corrections) - n_from_pr
            logger.info(
                f"  [{intermediate_hash[:12]}] Applying {len(effective_corrections)} parameter "
                f"correction(s) ({n_from_pr} from PR, {n_persisted} persisted)"
            )
            if parsed_params:
                user_input = apply_pr_corrections(user_input, parsed_params, effective_corrections, intermediate_hash)
            else:
                # No parsed params, just apply corrections directly to user_input
                for key, (_, new_str) in effective_corrections.items():
                    user_input[key] = _coerce_value(new_str)
                    logger.info(
                        f"  [{intermediate_hash[:12]}] {key}: applied correction → '{new_str}' "
                        f"(no parsed params to compare)"
                    )
        else:
            logger.info(f"  [{intermediate_hash[:12]}] No parameter corrections " f"(using parsed/JSON params as-is)")

        # If we have parsed params, update user_input with auto-parsed values for
        # fields not already overridden by corrections
        if parsed_params:
            for key, val in parsed_params.__dict__.items():
                if key not in effective_corrections and key in user_input:
                    user_input[key] = val

        # --- 6e/f: Run benchmarking ---
        try:
            # Pass input_file as a positional arg to avoid kwarg name mismatch:
            # some subclasses use "input_file", others "input_file_loc".
            input_file_val = extracted["input_file"]
            kwargs: dict[str, Any] = {
                "input_format": input_format,
                "user_input": user_input,
                "all_datapoints": None,
            }

            # Module-specific kwargs
            is_denovo = isinstance(module_instance, DeNovoModule)

            if is_denovo:
                # evaluation_type
                eval_type = dp_json.get("evaluation_type", "mass")
                kwargs["evaluation_type"] = eval_type
            else:
                # Quant modules
                default_cutoff = 3  # default
                results_dict = dp_json.get("results", {})
                if isinstance(results_dict, dict) and results_dict:
                    try:
                        cutoffs = [int(k) for k in results_dict.keys()]
                        default_cutoff = min(cutoffs) if cutoffs else 3
                    except (ValueError, TypeError):
                        pass
                kwargs["default_cutoff_min_prec"] = default_cutoff

                # AlphaDIA secondary file
                if extracted["input_file_secondary"]:
                    kwargs["input_file_secondary"] = extracted["input_file_secondary"]

            # MaxQuant fixed modifications handling
            if input_format == "MaxQuant" and parsed_params:
                pass  # Applied after benchmarking below
            intermediate_result, all_dp, _ = module_instance.benchmarking(input_file_val, **kwargs)

            # MaxQuant post-processing
            if input_format == "MaxQuant" and parsed_params:
                try:
                    intermediate_result = add_maxquant_fixed_modifications(parsed_params, intermediate_result)
                except Exception as e:
                    logger.warning(f"  [{intermediate_hash[:12]}] MaxQuant fixed mod handling failed: {e}")

            # --- Extract the new datapoint JSON ---
            # The new datapoint is the last row of all_dp (marked old_new="new").
            # Replicate what clone_pr() does: set is_temporary=False, then serialise.
            try:
                new_datapoint = all_dp.iloc[-1].copy()
                new_datapoint["is_temporary"] = False
                # Apply parsed params on top (like clone_pr does with datapoint_params)
                if parsed_params:
                    for k, v in parsed_params.__dict__.items():
                        new_datapoint[k] = v
                # Apply effective corrections on top of that
                if effective_corrections:
                    for key, (_, new_val) in effective_corrections.items():
                        new_datapoint[key] = _coerce_value(new_val)

                # Preserve fields from the original submission that must not be
                # recalculated or overwritten during resubmission.
                _PRESERVE_FIELDS = (
                    "id",  # contains original submission timestamp
                    "intermediate_hash",  # keeps JSON filename stable for clean PR diffs
                    "color",
                    "hover_text",
                    "scatter_size",
                    "submission_comments",
                )
                for _field in _PRESERVE_FIELDS:
                    _val = dp_json.get(_field)
                    if _val is not None:
                        new_datapoint[_field] = _val
                        logger.debug(f"  [{intermediate_hash[:12]}] Preserved original {_field}: {_val}")

                new_dp_hash = intermediate_hash
                result["new_hash"] = new_dp_hash
                result["json_data"] = new_datapoint.to_dict()
                result["repo_suffix"] = repo_suffix

            except Exception as e:
                logger.warning(f"  [{intermediate_hash[:12]}] Failed to extract datapoint JSON: {e}")
                # Non-fatal: we can still write the zip/files

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Benchmarking failed: {e}"
            logger.error(f"  [{intermediate_hash[:12]}] Benchmarking error: {e}")
            return result

        # --- 6g: Compare old vs new ---
        comparison = {"changed": False}
        if extracted["result_performance"]:
            comparison = compare_results(extracted["result_performance"], intermediate_result)
            result["comparison"] = comparison
        else:
            result["comparison"] = {"changed": True, "note": "no old result_performance.csv"}

        # --- 6h: Write updated outputs ---
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        correction_summary = ""
        if effective_corrections:
            lines = [f"  {k}: '{old}' → '{new}'" for k, (old, new) in effective_corrections.items()]
            correction_summary = "Parameter corrections applied:\n" + "\n".join(lines)

        # Persist all effective corrections so future runs can recover them
        persisted_block = _serialize_corrections_for_persistence(effective_corrections)

        change_summary = ""
        if comparison.get("changed"):
            parts = []
            if comparison.get("old_rows") != comparison.get("new_rows"):
                parts.append(f"Row count: {comparison.get('old_rows')} → {comparison.get('new_rows')}")
            if comparison.get("added_cols"):
                parts.append(f"Added columns: {comparison['added_cols']}")
            if comparison.get("removed_cols"):
                parts.append(f"Removed columns: {comparison['removed_cols']}")
            n_diffs = sum(d.get("n_changed", 0) for d in comparison.get("numeric_diffs", {}).values())
            if n_diffs:
                parts.append(f"Numeric value changes across {n_diffs} cells")
            change_summary = "Changes detected:\n" + "\n".join(f"  {p}" for p in parts)
        else:
            change_summary = "No changes detected in result_performance.csv"

        resubmit_note = (
            f"--- Resubmitted on {timestamp} ---\n" f"{change_summary}\n" f"{correction_summary}\n" f"{persisted_block}"
        ).strip()

        try:
            write_fn = write_updated_files if no_zip else write_updated_zip
            written = write_fn(zip_path, intermediate_result, output_dir, intermediate_hash, resubmit_note)
            result["status"] = "success" if comparison.get("changed") else "unchanged"
            result["message"] = f"Written to {written}"
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Failed to write output: {e}"

        # --- Write datapoint JSON to output-dir (for testing / inspection) ---
        if output_dir and "json_data" in result:
            try:
                new_hash = result.get("new_hash", intermediate_hash)
                json_path = write_datapoint_json(result["json_data"], output_dir, intermediate_hash)
                logger.info(f"  [{intermediate_hash[:12]}] Datapoint JSON written to {json_path}")
            except Exception as e:
                logger.warning(f"  [{intermediate_hash[:12]}] Failed to write datapoint JSON: {e}")

    return result


# CLI Entry Point


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-run ProteoBench benchmarking on previously submitted datapoints.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Write results to this directory instead of in-place. "
        "When omitted, updates are written in-place in PROTEOBENCH_DATA_DIR.",
    )
    parser.add_argument(
        "--module",
        default=None,
        help="Filter: only process datapoints for this module_id " "(e.g. quant_lfq_DDA_ion_QExactive).",
    )
    parser.add_argument(
        "--hash",
        nargs="+",
        default=None,
        help="Filter: only process these intermediate hash(es).",
    )
    parser.add_argument(
        "--software",
        default=None,
        help="Filter: only process datapoints from this software " "(e.g. MaxQuant, DIA-NN).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be processed without executing.",
    )
    parser.add_argument(
        "--log-file",
        default="resubmit_log.txt",
        help="Path for the run log (default: resubmit_log.txt).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Write output as loose files instead of a zip archive (easier for testing).",
    )
    parser.add_argument(
        "--create-pr",
        action="store_true",
        help="Create pull requests on Proteobot repos with updated datapoint JSONs. "
        "Requires GITHUB_TOKEN with push access to Proteobot repos. "
        "Without this flag, JSONs are only written to --output-dir (if set).",
    )
    parser.add_argument(
        "--delete-failed",
        action="store_true",
        help="When --create-pr is set, also delete the JSON files of datapoints that "
        "failed resubmission from the Proteobot repo. Has no effect without --create-pr.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    data_dir = os.environ.get("PROTEOBENCH_DATA_DIR")
    if not data_dir:
        print("ERROR: PROTEOBENCH_DATA_DIR environment variable is not set.")
        print("Set it to the directory containing hash folders with zip archives.")
        sys.exit(1)

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("WARNING: GITHUB_TOKEN not set. API rate limits will be very low (60/hr).")
        print("Set GITHUB_TOKEN for better throughput.")

    if args.create_pr and not token:
        print("ERROR: --create-pr requires GITHUB_TOKEN with push access to Proteobot repos.")
        sys.exit(1)

    setup_logging(args.log_file, verbose=args.verbose)

    logger.info("=" * 70)
    logger.info("ProteoBench Datapoint Resubmission")
    logger.info(f"  Data dir:    {data_dir}")
    logger.info(f"  Output dir:  {args.output_dir or '(in-place)'}")
    logger.info(f"  Module:      {args.module or '(all)'}")
    logger.info(f"  Hash filter: {args.hash or '(all)'}")
    logger.info(f"  Software:    {args.software or '(all)'}")
    logger.info(f"  Dry run:     {args.dry_run}")
    logger.info(f"  No zip:      {args.no_zip}")
    logger.info(f"  Create PR:   {args.create_pr}")
    logger.info("=" * 70)

    # --- Step 3: Build hash → module mapping ---
    logger.info("Building hash → module mapping from Proteobench repos …")
    hash_to_module = build_hash_to_module_mapping(token, module_filter=args.module)
    if not hash_to_module:
        logger.error("No datapoint hashes found in any Proteobench repo. Exiting.")
        sys.exit(1)

    # --- Step 4: Build hash → PR corrections mapping ---
    # Only scan repos that have matching hashes
    relevant_repo_suffixes = {info[1] for info in hash_to_module.values()}
    logger.info("Building hash → parameter corrections mapping from Proteobot PRs …")
    hash_to_corrections = build_hash_to_pr_corrections(token, relevant_repo_suffixes)

    # --- Step 5: Discover datapoints on disk ---
    logger.info("Discovering datapoint zip archives on disk …")
    disk_datapoints = discover_datapoints(data_dir)

    # --- Intersect and filter ---
    processable: list[tuple[str, Path, str, str, type, Path, dict]] = []
    skipped_no_module = 0
    skipped_filter = 0
    skipped_no_data = 0

    # Track hashes with PRs but missing data (failed resubmissions)
    missing_data_hashes: dict[str, tuple[str, str]] = {}  # hash -> (module_id, repo_suffix)

    for h, zip_path in sorted(disk_datapoints.items()):
        # Must be in a known module
        if h not in hash_to_module:
            skipped_no_module += 1
            continue

        module_id, repo_suffix, module_class, params_json = hash_to_module[h]

        # --hash filter
        if args.hash and h not in args.hash:
            skipped_filter += 1
            continue

        # --software filter (requires fetching JSON — defer to processing or pre-fetch)
        if args.software:
            try:
                dp_json = fetch_datapoint_json(h, repo_suffix, token)
                sw = dp_json.get("software_name", "")
                if sw != args.software:
                    skipped_filter += 1
                    continue
            except Exception:
                skipped_filter += 1
                continue

        corrections = hash_to_corrections.get(h, {})
        processable.append((h, zip_path, module_id, repo_suffix, module_class, params_json, corrections))

    # Check for hashes in Proteobench repos but missing data in the data directory
    # These are considered failed resubmissions (cannot reprocess without data)
    for h in hash_to_module.keys():
        # Skip if already in processable list (has data)
        if h in disk_datapoints:
            continue

        module_id, repo_suffix, module_class, params_json = hash_to_module[h]

        # Apply hash filter if specified
        if args.hash and h not in args.hash:
            continue

        # Apply software filter if specified
        if args.software:
            try:
                dp_json = fetch_datapoint_json(h, repo_suffix, token)
                sw = dp_json.get("software_name", "")
                if sw != args.software:
                    continue
            except Exception:
                continue

        # Track as missing data (failed resubmission)
        missing_data_hashes[h] = (module_id, repo_suffix)
        skipped_no_data += 1
        logger.warning(f"  {h[:12]}: exists in Proteobench but no data in {data_dir}, marking as failed resubmission")

    logger.info(f"Processable: {len(processable)}")
    logger.info(f"Skipped (no module match): {skipped_no_module}")
    logger.debug(f"  Skipped hashes (no module): {[h[:12] for h in disk_datapoints if h not in hash_to_module]}")
    logger.info(f"Skipped (filter): {skipped_filter}")
    logger.info(f"Failed (no data in {data_dir}): {skipped_no_data}")

    if args.dry_run:
        logger.info("--- DRY RUN: would process the following datapoints ---")
        for h, _, mid, _, _, _, corr in processable:
            correction_info = f" ({len(corr)} param corrections)" if corr else " (no corrections)"
            logger.info(f"  {h[:12]}…  module={mid}{correction_info}")
        if missing_data_hashes:
            logger.info("--- DRY RUN: would mark the following as FAILED (no data) ---")
            for h, (mid, repo_suffix) in missing_data_hashes.items():
                logger.info(f"  {h[:12]}…  module={mid}  reason=missing data in {data_dir}")
        logger.info("--- DRY RUN complete ---")
        return

    # --- Step 6: Reprocess each datapoint ---
    counts = {"success": 0, "unchanged": 0, "error": 0, "skipped": 0}
    failed_items: list[tuple[str, str, str, str]] = []  # (hash, module_id, repo_suffix, message)
    repo_failed_deletions: dict[str, list[str]] = defaultdict(list)  # repo_suffix → [hashes]

    # First, add all missing data hashes as failures
    for h, (module_id, repo_suffix) in missing_data_hashes.items():
        failure_msg = f"Data not found in {data_dir}"
        failed_items.append((h, module_id, repo_suffix, failure_msg))
        counts["error"] += 1
        if args.delete_failed:
            repo_failed_deletions[repo_suffix].append(h)
        logger.error(f"  [{h[:12]}] FAILED: {failure_msg}")

    # Collect JSON updates per repo for batch PR creation
    # Key: repo_suffix → list of {"old_hash": ..., "new_hash": ..., "json_data": ...}
    repo_json_updates: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for i, (h, zip_path, module_id, repo_suffix, module_class, params_json, corrections) in enumerate(processable, 1):
        logger.info(f"[{i}/{len(processable)}] Processing {h[:12]}… (module={module_id})")

        result = reprocess_datapoint(
            intermediate_hash=h,
            zip_path=zip_path,
            module_id=module_id,
            repo_suffix=repo_suffix,
            module_class=module_class,
            params_json_path=params_json,
            corrections=corrections,
            token=token,
            output_dir=args.output_dir,
            no_zip=args.no_zip,
        )

        status = result["status"]
        counts[status] = counts.get(status, 0) + 1
        msg = result.get("message", "")

        if status == "error":
            logger.error(f"  [{h[:12]}] FAILED: {msg}")
            failed_items.append((h, module_id, repo_suffix, msg))
            if args.delete_failed:
                repo_failed_deletions[repo_suffix].append(h)
        elif status == "unchanged":
            logger.info(f"  [{h[:12]}] UNCHANGED: {msg}")
        elif status == "skipped":
            logger.info(f"  [{h[:12]}] SKIPPED: {msg}")
        else:
            logger.info(f"  [{h[:12]}] SUCCESS: {msg}")

        # Collect JSON update for PR creation (both success and unchanged)
        if status in ("success", "unchanged") and "json_data" in result:
            repo_json_updates[result.get("repo_suffix", repo_suffix)].append(
                {
                    "old_hash": h,
                    "new_hash": result.get("new_hash", h),
                    "json_data": result["json_data"],
                }
            )

    # --- Step 7: Create PRs to Proteobot repos (if requested) ---
    pr_urls: list[str] = []
    all_repo_suffixes = set(repo_json_updates) | set(repo_failed_deletions)
    if args.create_pr and all_repo_suffixes:
        logger.info("=" * 70)
        logger.info("Creating PRs on Proteobot repos …")
        for repo_suffix in sorted(all_repo_suffixes):
            updates = repo_json_updates.get(repo_suffix, [])
            deletions = repo_failed_deletions.get(repo_suffix, []) if args.delete_failed else []
            n_del = len(deletions)
            logger.info(f"  {repo_suffix}: {len(updates)} update(s), {n_del} deletion(s)")
            pr_url = create_batch_pr(token, repo_suffix, updates, hashes_to_delete=deletions)
            if pr_url:
                pr_urls.append(pr_url)
    elif args.create_pr:
        logger.info("No successful datapoint updates or deletions to create PRs for.")

    # --- Summary ---
    logger.info("=" * 70)
    logger.info("Resubmission complete.")
    logger.info(f"  Succeeded (changed):  {counts.get('success', 0)}")
    logger.info(f"  Unchanged:            {counts.get('unchanged', 0)}")
    logger.info(f"  Failed:               {counts.get('error', 0)}")
    logger.info(f"  Skipped:              {counts.get('skipped', 0)}")

    if failed_items:
        logger.info("  Failed datapoints:")
        for fh, fmod, frep, fmsg in failed_items:
            deleted_note = " [scheduled for deletion]" if args.delete_failed else ""
            logger.info(f"    {fh[:12]}…  module={fmod}  reason: {fmsg}{deleted_note}")

    if repo_json_updates:
        total_jsons = sum(len(v) for v in repo_json_updates.values())
        logger.info(f"  JSON datapoints:      {total_jsons} across {len(repo_json_updates)} repo(s)")
        if args.output_dir:
            logger.info(f"  JSONs written to:     {args.output_dir}")
        if pr_urls:
            logger.info(f"  PRs created:          {len(pr_urls)}")
            for url in pr_urls:
                logger.info(f"    {url}")
        elif args.create_pr:
            logger.info("  PRs created:          0 (all failed)")

    logger.info("=" * 70)


if __name__ == "__main__":
    main()


# Example commands
#
# 1. Dry run — list what would be processed (no changes made):
#
#    PROTEOBENCH_DATA_DIR=/path/to/data GITHUB_TOKEN=ghp_xxx \
#        python resubmit_datapoints.py --dry-run
#
# 2. Reprocess a single datapoint to a test directory (loose files, no zip):
#
#    PROTEOBENCH_DATA_DIR=/path/to/data GITHUB_TOKEN=ghp_xxx \
#        python resubmit_datapoints.py \
#        --output-dir /tmp/pb_test \
#        --no-zip \
#        --hash d01e87b997b8c01e2c40f3604e9c0ca7efcd7d4a
#
# 3. Reprocess all datapoints for a specific module to a test directory:
#
#    PROTEOBENCH_DATA_DIR=/path/to/data GITHUB_TOKEN=ghp_xxx \
#        python resubmit_datapoints.py \
#        --output-dir /tmp/pb_test \
#        --module quant_lfq_DDA_ion_QExactive
#
# 4. Reprocess all MaxQuant submissions and write JSONs to output dir:
#
#    PROTEOBENCH_DATA_DIR=/path/to/data GITHUB_TOKEN=ghp_xxx \
#        python resubmit_datapoints.py \
#        --output-dir /tmp/pb_test \
#        --software MaxQuant
#
# 5. Reprocess a single datapoint and create a PR on the Proteobot repo:
#
#    PROTEOBENCH_DATA_DIR=/path/to/data GITHUB_TOKEN=ghp_xxx \
#        python resubmit_datapoints.py \
#        --hash d01e87b997b8c01e2c40f3604e9c0ca7efcd7d4a \
#        --create-pr
#
# 6. Full resubmission — reprocess ALL datapoints and create PRs:
#
#    PROTEOBENCH_DATA_DIR=/path/to/data GITHUB_TOKEN=ghp_xxx \
#        python resubmit_datapoints.py --create-pr
