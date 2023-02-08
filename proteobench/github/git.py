from git import Repo
import os

def clone_repo(
        clone_dir="K:/pb/",
        token="",
        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
        username= "Proteobot"
    ):
    remote = f"https://{username}:{token}@{remote_git}"
    repo = Repo.clone_from(remote, clone_dir)
    return clone_dir

def pr_github(
        clone_dir="K:/pb/",
        token="",
        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
        username= "Proteobot",
        branch_name="test"
    ):
    remote = f"https://{username}:{token}@{remote_git}"
    repo = Repo(clone_dir)
    
    repo.git.pull()

    current = repo.create_head(branch_name)
    current.checkout()

    repo.git.add(A=True)
    repo.git.commit(m="Some commit message")
    repo.git.push('--set-upstream', 'origin', current)