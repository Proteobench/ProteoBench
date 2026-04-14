"""
Leaderboard utilities for aggregating submitter statistics across all modules.

Discovers data repositories via the module registry and reads submitter
identity from the stored JSON datapoints.
"""

import json
import logging
import os
import tempfile

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def _read_submitters_from_repo(clone_dir: str) -> list[dict]:
    """Read submitter identity from all JSON files in a cloned repo directory."""
    records = []
    if not os.path.isdir(clone_dir):
        return records
    for fname in os.listdir(clone_dir):
        if not fname.endswith(".json") or fname == "results.json":
            continue
        fpath = os.path.join(clone_dir, fname)
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
            sid = data.get("submitter_id", "")
            if sid:
                records.append(
                    {
                        "submitter_id": sid,
                        "submitter_name": data.get("submitter_name", sid),
                        "submitter_provider": data.get("submitter_provider", ""),
                    }
                )
        except Exception:
            continue
    return records


@st.cache_data(ttl=3600, show_spinner="Loading leaderboard data...")
def get_leaderboard_data() -> pd.DataFrame:
    """
    Aggregate submitter statistics from all module data repositories.

    Discovers repos from the module registry, clones each, and counts
    submissions per submitter.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: submitter_id, submitter_name,
        submitter_provider, submissions — sorted descending.
    """
    from pages.utils.module_registry import get_all_data_repo_urls
    from proteobench.github.gh import GithubProteobotRepo

    repo_urls = get_all_data_repo_urls()
    all_records = []

    for repo_url in repo_urls:
        try:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            clone_dir = os.path.join(tempfile.gettempdir(), "pb_leaderboard", repo_name)
            gh = GithubProteobotRepo(
                token=st.secrets.get("gh", {}).get("token_read"),
                clone_dir=clone_dir,
                remote_git=repo_url,
            )
            gh.clone_repo()
            all_records.extend(_read_submitters_from_repo(clone_dir))
        except Exception as e:
            logger.debug(f"Could not read repo {repo_url}: {e}")
            continue

    if not all_records:
        return pd.DataFrame(columns=["submitter_id", "submitter_name", "submitter_provider", "submissions"])

    df = pd.DataFrame(all_records)
    leaderboard = (
        df.groupby("submitter_id")
        .agg(
            submitter_name=("submitter_name", "first"),
            submitter_provider=("submitter_provider", "first"),
            submissions=("submitter_id", "count"),
        )
        .sort_values("submissions", ascending=False)
        .reset_index()
    )

    return leaderboard
