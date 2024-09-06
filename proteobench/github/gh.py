import os

import pandas as pd
from git import Repo, exc
from github import Github


class GithubProteobotRepo:
    def __init__(
        self,
        token=None,
        clone_dir=None,
        clone_dir_pr=None,
        proteobench_repo_name="Proteobench/Results_Module2_quant_DDA",
        proteobot_repo_name="Proteobot/Results_Module2_quant_DDA",
        username="Proteobot",
    ):
        self.token = token
        self.clone_dir = clone_dir
        self.clone_dir_pr = clone_dir_pr
        self.proteobot_repo_name = proteobot_repo_name
        self.proteobench_repo_name = proteobench_repo_name
        self.username = username
        self.repo = None

    def get_remote_url_anon(self):
        # if token is None, use the public remote
        remote = f"https://github.com/{self.proteobench_repo_name}.git"
        return remote

    @staticmethod
    def clone(remote_url, clone_dir):
        try:
            repo = Repo(clone_dir)
        except (exc.NoSuchPathError, exc.InvalidGitRepositoryError):
            repo = Repo.clone_from(remote_url.rstrip("/"), clone_dir)
        return repo

    def clone_repo_anonymous(self):
        remote_url = self.get_remote_url_anon()
        repo = self.clone(remote_url, self.clone_dir)
        return repo

    def read_results_json_repo(self):
        f_name = os.path.join(self.clone_dir, "results.json")
        all_datapoints = pd.read_json(f_name)
        return all_datapoints

    def clone_repo(self):
        if self.token is None:
            self.repo = self.clone_repo_anonymous()
        else:
            remote = f"https://{self.username}:{self.token}@github.com/{self.proteobench_repo_name}.git"
            self.repo = self.clone(remote, self.clone_dir)
        return self.repo

    def clone_repo_pr(self):
        if self.token is None:
            self.repo = self.clone_repo_anonymous()
        else:
            remote = f"https://{self.username}:{self.token}@github.com/{self.proteobot_repo_name}.git"
            self.repo = self.clone(remote, self.clone_dir_pr)
        return self.repo

    def create_branch(self, branch_name):
        # Fetch the latest changes from the remote
        origin = self.repo.remote(name="origin")
        origin.fetch()

        # Create and checkout the new branch
        current_branch = self.repo.create_head(branch_name)
        current_branch.checkout()
        return current_branch

    def commit(self, commit_name, commit_message):
        # Stage all changes, commit, and push to the new branch
        self.repo.git.add(A=True)
        self.repo.index.commit("\n".join([commit_name, commit_message]))
        self.repo.git.push("--set-upstream", "origin", self.repo.active_branch)

    def create_pull_request(self, commit_name, commit_message):
        # Create a pull request using PyGithub
        g = Github(self.token)
        repo = g.get_repo(self.proteobot_repo_name)
        base = repo.get_branch("master")
        head = f"{self.username}:{self.repo.active_branch.name}"

        pr = repo.create_pull(
            title=commit_name,
            body=commit_message,
            base=base.name,
            head=head,
        )

        pr_number = pr.number
        return pr_number
