import os
import json
import base64
from github import Github

# Path to the GitHub Actions event payload
event_path = os.environ.get("GITHUB_EVENT_PATH")
if not event_path or not os.path.exists(event_path):
    print("No event payload found.")
    exit(1)

with open(event_path, "r") as f:
    event = json.load(f)

# Only proceed if this is a PR comment event
if "pull_request" not in event.get("issue", {}):
    print("Not a PR comment event.")
    exit(0)

pr_number = event["issue"]["number"]
comment_body = event["comment"]["body"]
repo_full_name = event["repository"]["full_name"]
token = os.environ.get("GITHUB_TOKEN")

if not token:
    print("No GITHUB_TOKEN found in environment.")
    exit(1)

gh = Github(token)
repo = gh.get_repo(repo_full_name)
pr = repo.get_pull(pr_number)

print(f"Comment: {comment_body}")
print("Changed files and their contents:")

for file in pr.get_files():
    print(f"\n=== {file.filename} ===")
    cf = repo.get_contents(file.filename, ref=pr.head.sha)
    content = base64.b64decode(cf.content).decode("utf-8")
    print(content)
