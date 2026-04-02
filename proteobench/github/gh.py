"""
This module provides the `GithubProteobotRepo` class to interact with GitHub repositories related to Proteobot and Proteobench.
It allows cloning repositories, reading JSON result files, creating branches, committing changes, and creating pull requests.
"""

import logging
import os
from typing import Optional

import pandas as pd
from git import Repo, exc
from github import Github

logger = logging.getLogger(__name__)


def is_official_server() -> bool:
    """Check if running on the official ProteoBench server.

    Uses the presence of storage configuration in Streamlit secrets
    as the signal - only the production server has this configured.
    """
    try:
        import streamlit as st

        return "storage" in st.secrets.keys()
    except (ImportError, FileNotFoundError):
        return False


def get_submission_source() -> str:
    """Return the submission source: 'web-server' or 'local'."""
    return "web-server" if is_official_server() else "local"


class GithubProteobotRepo:
    """
    A class to interact with GitHub repositories related to Proteobot and Proteobench,
    allowing cloning, committing, and creating pull requests.

    Parameters
    ----------
    token : str | None, optional
        GitHub access token for authenticated access. Defaults to None.
    clone_dir : str
        Directory where the repository will be cloned.
    clone_dir_pr : str
        Directory for cloning pull request repositories.
    proteobench_repo_name : str, optional
        Name of the Proteobench repository. Defaults to "Proteobench/Results_quant_ion_DDA".
    proteobot_repo_name : str, optional
        Name of the Proteobot repository. Defaults to "Proteobot/Results_quant_ion_DDA".
    username : str, optional
        GitHub username for authentication. Defaults to "Proteobot".
    """

    def __init__(
        self,
        token: Optional[str] = None,
        clone_dir: str = None,
        clone_dir_pr: str = None,
        proteobench_repo_name: str = "Proteobench/Results_quant_ion_DDA",
        proteobot_repo_name: str = "Proteobot/Results_quant_ion_DDA",
        username: str = "Proteobot",
        branch: Optional[str] = None,
    ):
        """
        Initialize the GithubProteobotRepo class with required parameters for cloning and managing repositories.

        Parameters
        ----------
        token : str | None, optional
            GitHub access token for authenticated access. Defaults to None.
        clone_dir : str
            Directory where the repository will be cloned.
        clone_dir_pr : str
            Directory for cloning pull request repositories.
        proteobench_repo_name : str, optional
            Name of the Proteobench repository. Defaults to "Proteobench/Results_quant_ion_DDA".
        proteobot_repo_name : str, optional
            Name of the Proteobot repository. Defaults to "Proteobot/Results_quant_ion_DDA".
        username : str, optional
            GitHub username for authentication. Defaults to "Proteobot".
        """
        self.token = token
        self.clone_dir = clone_dir
        self.clone_dir_pr = clone_dir_pr
        self.proteobot_repo_name = proteobot_repo_name
        self.proteobench_repo_name = proteobench_repo_name
        self.username = username
        self.branch = branch
        self.repo = None

    def get_remote_url_anon(self) -> str:
        """
        Return the remote URL of the repository to be cloned anonymously (public access).

        Returns
        -------
        str
            The public GitHub URL of the Proteobench repository.
        """
        remote = f"https://github.com/{self.proteobench_repo_name}.git"
        return remote

    @staticmethod
    def clone(remote_url: str, clone_dir: str) -> Repo:
        """
        Clone the repository from the given remote URL to the specified directory.

        Parameters
        ----------
        remote_url : str
            The URL of the remote GitHub repository.
        clone_dir : str
            The directory where the repository will be cloned.

        Returns
        -------
        Repo
            The local repository object.

        Raises
        ------
        exc.NoSuchPathError
            If the specified directory does not exist.
        exc.InvalidGitRepositoryError
            If the directory is not a valid Git repository.
        """
        try:
            repo = Repo(clone_dir)
        except (exc.NoSuchPathError, exc.InvalidGitRepositoryError):
            repo = Repo.clone_from(remote_url.rstrip("/"), clone_dir, depth=1, no_single_branch=True)
        return repo

    @staticmethod
    def shallow_clone(remote_url: str, clone_dir: str) -> Repo:
        """
        Perform a shallow clone of the repository (only the latest commit).

        Parameters
        ----------
        remote_url : str
            The repository URL.
        clone_dir : str
            The target directory for cloning.

        Returns
        -------
        Repo
            The cloned repository object.
        """
        if os.path.exists(clone_dir):
            print(f"Repository already exists in {clone_dir}. Trying to use existing files.")
            try:
                return Repo(clone_dir)
            except exc.InvalidGitRepositoryError:
                print(f"Repository invalid, will clone again.")

        try:
            repo = Repo.clone_from(remote_url.rstrip("/"), clone_dir, depth=1, no_single_branch=True)
        except exc.GitCommandError as e:
            raise RuntimeError(f"Failed to clone the repository: {e}")

        return repo

    def clone_repo_anonymous(self) -> Repo:
        """
        Clone the Proteobench repository anonymously with a shallow clone (without authentication).

        If ``self.branch`` is set, the repository is cloned from the **Proteobot** repository
        (not Proteobench) and the specified branch is checked out. This allows reading JSON files
        from a PR branch that has not yet been merged into Proteobench (for testing purposes). When the clone directory
        already exists, the method fetches and checks out the requested branch to ensure the
        correct revision is used.

        Returns
        -------
        Repo
            The cloned repository object.
        """
        if self.branch is not None:
            # Branch is on the Proteobot repo (PR not yet merged into Proteobench)
            branch_remote_url = f"https://github.com/{self.proteobot_repo_name}.git"
            if os.path.exists(self.clone_dir):
                print(f"Repository already exists in {self.clone_dir}. Verifying branch...")
                try:
                    self.repo = Repo(self.clone_dir)
                    # Fetch the requested branch and check it out to ensure we're on the correct revision
                    remote = self.repo.remote("origin")
                    remote.fetch(self.branch, depth=1)
                    self.repo.git.checkout(self.branch)
                    print(f"Checked out branch '{self.branch}' in existing repository.")
                    return self.repo
                except exc.InvalidGitRepositoryError:
                    print("Repository invalid, will clone again.")
                except Exception as e:
                    print(f"Failed to fetch/checkout branch '{self.branch}': {e}. Recloning...")
                    # If fetch/checkout fails, remove the directory and reclone
                    import shutil

                    shutil.rmtree(self.clone_dir)
            self.repo = Repo.clone_from(branch_remote_url.rstrip("/"), self.clone_dir, depth=1, branch=self.branch)
            print(f"Cloned branch '{self.branch}' from {self.proteobot_repo_name}")
        else:
            remote_url = self.get_remote_url_anon()
            self.repo = self.shallow_clone(remote_url, self.clone_dir)
            print(f"Shallow cloned repository from {remote_url} to {self.clone_dir}")
        return self.repo

    def read_results_json_repo_single_file(self) -> pd.DataFrame:
        """
        Read the `results.json` file from the cloned Proteobench repository and returns the data as a DataFrame.

        Returns
        -------
        pd.DataFrame:
            A Pandas DataFrame containing the results from `results.json`.
        """
        f_name = os.path.join(self.clone_dir, "results.json")

        if not os.path.exists(f_name):
            raise FileNotFoundError(f"File '{f_name}' does not exist.")

        all_datapoints = pd.read_json(f_name)
        return all_datapoints

    def read_results_json_repo(self) -> pd.DataFrame:
        """
        Read all JSON result files from the cloned Proteobench repository.

        Returns
        -------
        pd.DataFrame
            A Pandas DataFrame containing aggregated results from multiple JSON files.
        """
        data = []
        if not os.path.exists(self.clone_dir):
            raise FileNotFoundError(f"Clone directory '{self.clone_dir}' does not exist.")

        for file in os.listdir(self.clone_dir):
            if file.endswith(".json") and file != "results.json":
                file_path = os.path.join(self.clone_dir, file)
                with open(file_path, "r") as f:
                    data.append(pd.read_json(f, typ="series"))
        if not data:
            try:
                self.read_results_json_repo_single_file()
            except FileNotFoundError:
                data = []

        return pd.DataFrame(data)

    def clone_repo(self) -> Repo:
        """
        Clone the Proteobench repository using either an anonymous or authenticated GitHub access token.

        If `token` is provided, it will use authenticated access; otherwise, it will clone anonymously.

        When ``self.branch`` is set, the repository is cloned from the **Proteobot** repository
        and the specified branch is checked out. If the directory already exists, the method
        fetches and checks out the requested branch to ensure the correct revision is used.

        Returns
        -------
        Repo
            The local repository object.
        """
        if self.token is None or self.token == "":
            self.repo = self.clone_repo_anonymous()
        else:
            if self.branch is not None:
                # Branch is on the Proteobot repo (PR not yet merged into Proteobench)
                remote = f"https://{self.username}:{self.token}@github.com/{self.proteobot_repo_name}.git"
                if os.path.exists(self.clone_dir):
                    print(f"Repository already exists in {self.clone_dir}. Verifying branch...")
                    try:
                        self.repo = Repo(self.clone_dir)
                        # Fetch the requested branch and check it out
                        remote_obj = self.repo.remote("origin")
                        remote_obj.fetch(self.branch, depth=1)
                        self.repo.git.checkout(self.branch)
                        print(f"Checked out branch '{self.branch}' in existing repository.")
                        return self.repo
                    except exc.InvalidGitRepositoryError:
                        print("Repository invalid, will clone again.")
                    except Exception as e:
                        print(f"Failed to fetch/checkout branch '{self.branch}': {e}. Recloning...")
                        import shutil

                        shutil.rmtree(self.clone_dir)
                self.repo = Repo.clone_from(remote.rstrip("/"), self.clone_dir, depth=1, branch=self.branch)
                print(f"Cloned branch '{self.branch}' from {self.proteobot_repo_name} with authentication")
            else:
                remote = f"https://{self.username}:{self.token}@github.com/{self.proteobench_repo_name}.git"
                self.repo = self.clone(remote, self.clone_dir)
        return self.repo

    def clone_repo_pr(self) -> Repo:
        """
        Clone the Proteobot repository (for pull request management) using either an anonymous or authenticated GitHub access token.

        If `token` is provided, it will use authenticated access; otherwise, it will clone anonymously.

        Returns
        -------
        Repo
            The local repository object for the pull request.
        """
        if self.token is None or self.token == "":
            self.repo = self.clone_repo_anonymous()
        else:
            remote = f"https://{self.username}:{self.token}@github.com/{self.proteobot_repo_name}.git"
            self.repo = self.clone(remote, self.clone_dir_pr)
        return self.repo

    def create_branch(self, branch_name: str) -> Repo.head:
        """
        Create a new branch and checks it out.

        Parameters
        ----------
        branch_name : str
            The name of the new branch to be created.

        Returns
        -------
        Repo.head
            The newly created branch object.
        """
        # Fetch the latest changes from the remote
        origin = self.repo.remote(name="origin")
        origin.fetch()

        # Create and checkout the new branch
        current_branch = self.repo.create_head(branch_name)
        current_branch.checkout()
        return current_branch

    def commit(self, commit_name: str, commit_message: str) -> None:
        """
        Stage all changes, commits them with the given commit name and message, and pushes the changes to the remote repository.

        Parameters
        ----------
        commit_name : str
            The name of the commit.
        commit_message : str
            The commit message.
        """
        # Stage all changes, commit, and push to the new branch
        self.repo.git.add(A=True)
        self.repo.index.commit("\n".join([commit_name, commit_message]))
        self.repo.git.push("--set-upstream", "origin", self.repo.active_branch)

    def create_pull_request(self, commit_name: str, commit_message: str, submission_source: str = "unknown") -> int:
        """
        Create a pull request on GitHub using the PyGithub API.

        Parameters
        ----------
        commit_name : str
            The title of the pull request.
        commit_message : str
            The body of the pull request.
        submission_source : str, optional
            Origin of the submission: 'web-server', 'local', or 'resubmission-script'.
            Defaults to 'unknown'.

        Returns
        -------
        int
            The pull request number assigned by GitHub.
        """
        g = Github(self.token)
        repo = g.get_repo(self.proteobot_repo_name)
        base = repo.get_branch("master")
        head = f"{self.username}:{self.repo.active_branch.name}"

        if submission_source == "local":
            commit_name = f"[LOCAL - DO NOT MERGE] {commit_name}"

        pr = repo.create_pull(
            title=commit_name,
            body=commit_message,
            base=base.name,
            head=head,
        )

        try:
            if submission_source == "local":
                pr.set_labels("local-submission", "do-not-merge")
            elif submission_source == "web-server":
                pr.set_labels("server-submission")
            elif submission_source == "resubmission-script":
                pr.set_labels("batch-resubmission")
        except Exception as e:
            logger.warning(f"Failed to set labels on PR #{pr.number}: {e}")

        logger.info(f"Created PR #{pr.number} with submission_source='{submission_source}'")

        return pr.number
