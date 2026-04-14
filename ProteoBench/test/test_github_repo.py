import os
import uuid
from tempfile import TemporaryDirectory

import pandas as pd
import pytest
import toml
from git import Head, Repo, exc

from proteobench.github.gh import (
    GithubProteobotRepo,  # Adjust the import to match your module's location
)

# Test data


def test_clone_repo_anonymous():
    tmp_dir = TemporaryDirectory()
    temp_dir_name = tmp_dir.name

    github_repo = GithubProteobotRepo("", temp_dir_name, proteobot_repo_name="Proteobench/Results_quant_ion_DDA")
    url = github_repo.get_remote_url_anon()
    # assert that url equal 'https://github.com/Proteobench/Results_quant_ion_DDA.git'
    # assert url == 'https://github.com/Proteobench/Results_quant_ion_DDA.git'
    repo = github_repo.clone_repo_anonymous()
    assert isinstance(repo, Repo)
    jsonfile = github_repo.read_results_json_repo()
    assert isinstance(jsonfile, pd.DataFrame)


# disable test store token in st.secrets, and add some code to read the token from st.secrets...
# create a function that reads the token from secrets.toml located in ~/.streamlit/secrets.toml
def read_token():
    try:
        with open(os.path.expanduser("~/.streamlit/secrets.toml")) as f:
            secrets = toml.load(f)
            return secrets["gh"]["token_test"]
    except FileNotFoundError:
        return ""


skip_condition = True


# exclude this test from the test run
@pytest.mark.skipif(skip_condition, reason="Skipping this test due to the skip condition being True")
def test_clone_repo():
    tmp_dir = TemporaryDirectory()
    temp_dir_name = tmp_dir.name
    token = read_token()
    github_repo = GithubProteobotRepo(
        token, temp_dir_name, proteobot_repo_name="wolski/Results_quant_ion_DDA", username="wolski"
    )
    github_repo.clone_repo()
    # generate random branch name

    branch = github_repo.create_branch("test_branch" + uuid.uuid4().hex[:6])
    github_repo.commit("test_commit")
    github_repo.create_pull_request("test_commit")
    assert isinstance(branch, Head)


if __name__ == "__main__":
    pytest.main()
