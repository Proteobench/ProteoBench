import os
from tempfile import TemporaryDirectory

import pandas as pd
from git import Repo
from github import Github


def clone_repo_anon(
    clone_dir="K:/pb/",
    remote_git="https://github.com/Proteobench/Results_Module2_quant_DDA.git",
):
    repo = Repo.clone_from(remote_git, clone_dir)
    return clone_dir


def read_results_json_repo(
    remote_git_repo="https://github.com/Proteobench/Results_Module2_quant_DDA.git",
):
    t_dir = TemporaryDirectory().name
    os.mkdir(t_dir)
    clone_repo_anon(t_dir, remote_git_repo)
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
    token="YOUR_GITHUB_TOKEN",
    remote_git="Proteobot/Results_Module2_quant_DDA",
    username="Proteobot",
    branch_name="test",
    commit_message="New commit",
    repo_name="Proteobot/Results_Module2_quant_DDA",
):
    # Construct the remote URL with the token
    remote_url = f"https://{username}:{token}@{remote_git}"

    # Clone the repository if it doesn't exist
    try:
        repo = Repo(clone_dir)
    except:
        repo = Repo.clone_from(remote_url, clone_dir)

    # Fetch the latest changes from the remote
    origin = repo.remote(name="origin")
    origin.fetch()

    # Create and checkout the new branch
    current_branch = repo.create_head(branch_name)
    current_branch.checkout()

    # Stage all changes, commit, and push to the new branch
    repo.git.add(A=True)
    repo.index.commit(commit_message)
    repo.git.push("--set-upstream", "origin", current_branch)

    # Create a pull request using PyGithub
    g = Github(token)
    repo = g.get_repo(repo_name)
    base = repo.get_branch("master")
    head = f"{username}:{branch_name}"
    title = commit_message
    body = "Pull request body"

    pr = repo.create_pull(
        title=title,
        body=body,
        base=base.name,
        head=head,
    )

    pr_number = pr.number
    return pr_number
