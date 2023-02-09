from git import Repo
import os
from tempfile import TemporaryDirectory

def clone_pr(
        df_new,
        token,
        username="Proteobot",
        remote_git="github.com/Proteobot/Results_Module2_quant_DDA.git",
        branch_name="new_branch"
    ):
    t_dir = TemporaryDirectory().name

    clone_repo(
            clone_dir=t_dir,
            token=token,
            remote_git=remote_git,
            username=username
        )

    # do the pd.write_json() here!!!
    #f = open(os.path.join(t_dir,"newf.txt"),"w")
    #f.write("asdfsdaf")
    #f.close()

    pr_github(
        clone_dir=t_dir,
        token=token,
        remote_git=remote_git,
        username=username,
        branch_name=branch_name
    )

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