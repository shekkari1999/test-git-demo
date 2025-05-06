import os
import json
import base64
import requests
from github import Github, GithubException  # import exception class

# 1) inputs from the Actions runner
EVENT_PATH   = os.environ["GITHUB_EVENT_PATH"]
FASTAPI_URL  = os.environ["FASTAPI_URL"]      # set in your repo’s secrets
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

# 2) load the GH event
with open(EVENT_PATH) as f:
    ev = json.load(f)

# only run on PR‐comments
pr_num    = ev["issue"]["number"]
repo_full = ev["repository"]["full_name"]
comment   = ev["comment"]["body"]

# 3) fetch PR files
gh   = Github(GITHUB_TOKEN)
repo = gh.get_repo(repo_full)
pr   = repo.get_pull(pr_num)

files = []
for f in pr.get_files():
    cf      = repo.get_contents(f.filename, ref=pr.head.sha)
    content = base64.b64decode(cf.content).decode("utf-8")
    files.append({"filename": f.filename, "content": content})

# 4) call your FastAPI
payload = {"comment": comment, "files": files}
resp    = requests.post(f"{FASTAPI_URL}/infer", json=payload)
suggest = resp.json()["generated_code"]

# 5) create or update the AI branch
base_ref   = pr.base.ref                        # e.g. "main"
base_sha   = repo.get_branch(base_ref).commit.sha
new_branch = f"ai-fix-pr-{pr_num}"
ref_full   = f"refs/heads/{new_branch}"
ref_short  = f"heads/{new_branch}"
try:
    repo.create_git_ref(ref_full, base_sha)
except GithubException as e:
    if e.status == 422:
        # branch already exists → move its tip
        repo.get_git_ref(ref_short).edit(base_sha)
    else:
        raise

# 6) update the file(s) in that branch
for file in files:
    path     = file["filename"]
    contents = repo.get_contents(path, ref=base_ref)
    repo.update_file(
        path=path,
        message=f"AI suggestion applied to {path}",
        content=suggest,
        sha=contents.sha,
        branch=new_branch
    )

# 7) open the PR
new_pr = repo.create_pull(
    title=f"🤖 AI suggestions for PR #{pr_num}",
    body="Applied AI model’s suggested changes.",
    head=new_branch,
    base=base_ref,
)
print("Created PR:", new_pr.html_url)
