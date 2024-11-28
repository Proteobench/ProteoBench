import os
from typing import Optional, Union

import pandas as pd
from git import Repo, exc
from github import Github


class GithubProteobotRepo:
    """
    A class to manage interactions with GitHub repositories for Proteobot and Proteobench.

    This class facilitates cloning repositories, reading JSON results, managing branches,
    and automating pull requests using Git and PyGithub.

    Attributes:
        token (Optional[str]): Personal Access Token (PAT) for GitHub. Used for authenticated access.
        clone_dir (Optional[str]): Directory to clone the Proteobench repository.
        clone_dir_pr (Optional[str]): Directory to clone the Proteobot repository.
        proteobench_repo_name (str): Name of the Proteobench repository.
        proteobot_repo_name (str): Name of the Proteobot repository.
        username (str): GitHub username.
        repo (Optional[Repo]): GitPython repository object for interacting with the local repo.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        clone_dir: Optional[str] = None,
        clone_dir_pr: Optional[str] = None,
        proteobench_repo_name: str = "Proteobench/Results_Module2_quant_DDA",
        proteobot_repo_name: str = "Proteobot/Results_Module2_quant_DDA",
        username: str = "Proteobot",
    ):
        """
        Initializes the GithubProteobotRepo class with the required parameters.

        Parameters:
            token (Optional[str]): GitHub Personal Access Token (PAT). Default is None.
            clone_dir (Optional[str]): Directory to clone the Proteobench repository.
            clone_dir_pr (Optional[str]): Directory to clone the Proteobot repository.
            proteobench_repo_name (str): Name of the Proteobench repository. Default is Proteobench/Results_Module2_quant_DDA.
            proteobot_repo_name (str): Name of the Proteobot repository. Default is Proteobot/Results_Module2_quant_DDA.
            username (str): GitHub username. Default is Proteobot.
        """
        self.token: Optional[str] = token
        self.clone_dir: Optional[str] = clone_dir
        self.clone_dir_pr: Optional[str] = clone_dir_pr
        self.proteobot_repo_name: str = proteobot_repo_name
        self.proteobench_repo_name: str = proteobench_repo_name
        self.username: str = username
        self.repo: Optional[Repo] = None

    def get_remote_url_anon(self) -> str:
        """
        Constructs the anonymous remote URL for the Proteobench repository.

        Returns:
            str: Remote URL for anonymous access.
        """
        remote: str = f"https://github.com/{self.proteobench_repo_name}.git"
        return remote

    @staticmethod
    def clone(remote_url: str, clone_dir: str) -> Repo:
        """
        Clones a Git repository from a remote URL to a local directory.

        Parameters:
            remote_url (str): URL of the remote repository.
            clone_dir (str): Local directory to clone the repository.

        Returns:
            Repo: GitPython repository object for the cloned repository.
        """
        try:
            repo: Repo = Repo(clone_dir)
        except (exc.NoSuchPathError, exc.InvalidGitRepositoryError):
            repo = Repo.clone_from(remote_url.rstrip("/"), clone_dir)
        return repo

    def clone_repo_anonymous(self) -> Repo:
        """
        Clones the Proteobench repository anonymously.

        Returns:
            Repo: GitPython repository object for the cloned repository.
        """
        remote_url: str = self.get_remote_url_anon()
        repo: Repo = self.clone(remote_url, self.clone_dir)
        return repo

    def read_results_json_repo(self) -> pd.DataFrame:
        """
        Reads the results.json file from the cloned repository.

        Returns:
            pd.DataFrame: DataFrame containing the parsed JSON results.
        """
        f_name: str = os.path.join(self.clone_dir, "results.json")
        all_datapoints: pd.DataFrame = pd.read_json(f_name)
        return all_datapoints

    def clone_repo(self) -> Repo:
        """
        Clones the Proteobench repository using either anonymous or authenticated access.

        Returns:
            Repo: GitPython repository object for the cloned repository.
        """
        if self.token is None:
            self.repo = self.clone_repo_anonymous()
        else:
            remote: str = f"https://{self.username}:{self.token}@github.com/{self.proteobench_repo_name}.git"
            self.repo = self.clone(remote, self.clone_dir)
        return self.repo

    def clone_repo_pr(self) -> Repo:
        """
        Clones the Proteobot repository for creating a pull request.

        Returns:
            Repo: GitPython repository object for the cloned repository.
        """
        if self.token is None:
            self.repo = self.clone_repo_anonymous()
        else:
            remote: str = f"https://{self.username}:{self.token}@github.com/{self.proteobot_repo_name}.git"
            self.repo = self.clone(remote, self.clone_dir_pr)
        return self.repo

    def create_branch(self, branch_name: str) -> Repo.heads:
        """
        Creates and checks out a new branch in the local repository.

        Parameters:
            branch_name (str): Name of the branch to be created.

        Returns:
            Repo.heads: The newly created branch.
        """
        origin = self.repo.remote(name="origin")
        origin.fetch()
        current_branch = self.repo.create_head(branch_name)
        current_branch.checkout()
        return current_branch

    def commit(self, commit_name: str, commit_message: str) -> None:
        """
        Commits all changes in the local repository and pushes them to the remote repository.

        Parameters:
            commit_name (str): Name of the commit.
            commit_message (str): Detailed message for the commit.
        """
        self.repo.git.add(A=True)
        self.repo.index.commit("\n".join([commit_name, commit_message]))
        self.repo.git.push("--set-upstream", "origin", self.repo.active_branch)

    def create_pull_request(self, commit_name: str, commit_message: str) -> int:
        """
        Creates a pull request on GitHub using PyGithub.

        Parameters:
            commit_name (str): Title of the pull request.
            commit_message (str): Detailed description of the pull request.

        Returns:
            int: Pull request number.
        """
        g: Github = Github(self.token)
        repo = g.get_repo(self.proteobot_repo_name)
        base = repo.get_branch("master")
        head: str = f"{self.username}:{self.repo.active_branch.name}"

        pr = repo.create_pull(
            title=commit_name,
            body=commit_message,
            base=base.name,
            head=head,
        )

        pr_number: int = pr.number
        return pr_number
