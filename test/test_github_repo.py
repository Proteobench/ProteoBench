import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import unittest
from git import Repo, exc
from github import Github
from proteobench.github.gh import GithubRepo  # Adjust the import to match your module's location

# Test data
TEST_TOKEN = "test_token"
TEST_CLONE_DIR = "test_dir"
TEST_REMOTE_GIT = "https://github.com/test/repo.git"
TEST_USERNAME = "test_user"


@pytest.fixture
def github_repo():
    return GithubRepo(token=TEST_TOKEN, clone_dir=TEST_CLONE_DIR, remote_git=TEST_REMOTE_GIT, username=TEST_USERNAME)


def test_get_remote_url(github_repo):
    expected_url = f"https://{TEST_USERNAME}:{TEST_TOKEN}@{TEST_REMOTE_GIT}"
    assert github_repo.get_remote_url() == expected_url


@patch.object(Repo, "clone_from")
def test_clone_repo_success(mock_clone_from, github_repo):
    mock_clone_from.return_value = None  # Simulate successful clone
    assert github_repo.clone_repo() == TEST_CLONE_DIR
    mock_clone_from.assert_called_once_with(github_repo.get_remote_url(), TEST_CLONE_DIR)


@patch.object(Repo, "clone_from")
def test_clone_repo_failure(mock_clone_from, github_repo):
    mock_clone_from.side_effect = exc.GitCommandError("error", 1)  # Simulate clone failure
    with pytest.raises(exc.GitCommandError):
        github_repo.clone_repo()


@patch.object(Repo, "clone_from")
@patch("proteobench.github.gh.pd.read_json")
def test_read_results_json_repo(mock_read_json, mock_clone_from, github_repo):
    test_data = pd.DataFrame({"column1": [1, 2], "column2": ["a", "b"]})
    mock_read_json.return_value = test_data
    mock_clone_from.return_value = None  # Simulate successful clone

    with patch("builtins.open", unittest.mock.mock_open(read_data='{"column1": [1, 2], "column2": ["a", "b"]}')):
        result = github_repo.read_results_json_repo()
        pd.testing.assert_frame_equal(result, test_data)
        mock_clone_from.assert_called_once_with(TEST_REMOTE_GIT, TEST_CLONE_DIR)
        mock_read_json.assert_called_once_with(os.path.join(TEST_CLONE_DIR, "results.json"))

if __name__ == "__main__":
    pytest.main()
