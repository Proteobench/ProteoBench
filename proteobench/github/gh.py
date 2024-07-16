import os
from tempfile import TemporaryDirectory

import pandas as pd
import toml
from git import Repo, exc
from github import Github

DDA_QUANT_RESULTS_REPO = "https://github.com/Proteobench/Results_quant_ion_DDA.git"


# current usage
# self.dda_quant_results_repo = DDA_QUANT_RESULTS_REPO
# clone_repo(clone_dir=t_dir, token=token, remote_git=remote_git, username=username)
# pr_id = pr_github(
#            clone_dir=t_dir,
#            token=token,
#            remote_git=remote_git,
#            username=username,
#            branch_name=branch_name,
#            commit_message=commit_message,
#        )
#
# all_datapoints = read_results_json_repo(self.dda_quant_results_repo)

class GithubRepo:
    def __init__(self, token,
                 clone_dir="K:/pb/",
                 remote_git="https://github.com/Proteobench/Results_Module2_quant_DDA.git",
                 username="Proteobot"):
        self.token = token
        self.clone_dir = clone_dir
        self.remote_git = remote_git
        self.username = username

    def read_results_json_repo(self):
        Repo.clone_from(self.remote_git, self.clone_dir)
        f_name = os.path.join(self.clone_dir, "results.json")
        all_datapoints = pd.read_json(f_name)
        return all_datapoints

    def get_remote_url(self):
        remote = f"https://{self.username}:{self.token}@{self.remote_git}"
        return remote

    def clone_repo(self):
        remote_url = self.get_remote_url()
        repo = Repo.clone_from(remote_url, self.clone_dir)
        return self.clone_dir

    def pr_github(self,  branch_name, commit_message, repo_name="Proteobot/Results_Module2_quant_DDA"):
        remote_url = self.get_remote_url()

        # Clone the repository if it doesn't exist
        try:
            repo = Repo(self.clone_dir)
        except (exc.NoSuchPathError, exc.InvalidGitRepositoryError):
            repo = Repo.clone_from(remote_url, self.clone_dir)

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
        g = Github(self.token)
        repo = g.get_repo(repo_name)
        base = repo.get_branch("master")
        head = f"{self.username}:{branch_name}"

        pr = repo.create_pull(
            title=commit_message,
            body="Pull request body",
            base=base.name,
            head=head,
        )

        pr_number = pr.number
        return pr_number
