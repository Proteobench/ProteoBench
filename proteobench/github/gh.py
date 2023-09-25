import os
from tempfile import TemporaryDirectory

import pandas as pd
from git import Repo


def clone_repo_anon(
    clone_dir="K:/pb/",
    remote_git="https://github.com/Proteobench/Results_Module2_quant_DDA.git",
):
    repo = Repo.clone_from(remote_git, clone_dir)
    return clone_dir


def read_results_json_repo(
    remote_git_repo= "https://github.com/Proteobench/Results_Module2_quant_DDA.git"
):
    t_dir = TemporaryDirectory().name
    os.mkdir(t_dir)
    clone_repo_anon(
        t_dir,
        remote_git_repo
    )
    fname = os.path.join(t_dir, "results.json")
    all_datapoints = pd.read_json(fname)
    return all_datapoints


def clone_repo(
    clone_dir="K:/pb/",
    token="",
    remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
    username="Proteobot",
):
    remote = f"https://{username}:{token}@{remote_git}"
    repo = Repo.clone_from(remote, clone_dir)
    return clone_dir


def pr_github(
    clone_dir="K:/pb/",
    token="",
    remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
    username="Proteobot",
    branch_name="test",
    commit_message="New commit",
):
    remote = f"https://{username}:{token}@{remote_git}"
    repo = Repo(clone_dir)

    repo.git.pull()

    current = repo.create_head(branch_name)
    current.checkout()

    repo.git.add(A=True)
    repo.git.commit(m=commit_message)
    repo.git.push("--set-upstream", "origin", current)
