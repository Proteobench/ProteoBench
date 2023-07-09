import os
from tempfile import TemporaryDirectory

from git import Repo

from proteobench.modules.dda_quant.module import Module

def write_json_local_development(
    temporary_datapoints
):  
    t_dir = TemporaryDirectory().name
    os.mkdir(t_dir)

    current_datapoint = temporary_datapoints.iloc[-1]
    current_datapoint["is_temporary"] = False
    all_datapoints = Module().add_current_data_point(None, current_datapoint)

    # TODO write below to logger instead of std.out
    fname = os.path.join(t_dir, "results.json")
    print(f"Writing the json to: {fname}")

    f = open(os.path.join(t_dir, "results.json"), "w")
    all_datapoints.T.to_json(f)

    return os.path.join(t_dir, "results.json")

def clone_pr(
    temporary_datapoints,
    token,
    username="Proteobot",
    remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
    branch_name="new_branch",
):
    t_dir = TemporaryDirectory().name

    clone_repo(clone_dir=t_dir, token=token, remote_git=remote_git, username=username)
    current_datapoint = temporary_datapoints.iloc[-1]
    current_datapoint["is_temporary"] = False
    all_datapoints = Module().add_current_data_point(None, current_datapoint)
    branch_name = current_datapoint["id"]

    # do the pd.write_json() here!!!
    print(os.path.join(t_dir, "results.json"))
    f = open(os.path.join(t_dir, "results.json"), "w")
    
    all_datapoints.to_json(
        f,
        orient="records",
        indent=2
    )

    f.close()
    commit_message = "Added new run with id " + branch_name

    pr_github(
        clone_dir=t_dir,
        token=token,
        remote_git=remote_git,
        username=username,
        branch_name=branch_name,
        commit_message=commit_message,
    )


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
