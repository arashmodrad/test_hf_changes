#!/usr/bin/env python3
# .github/scripts/export_map_errors.py

import os
import re
import json
import csv
import argparse
from github import Github

def parse_frontmatter(body):
    """
    GitHub issue forms embed a JSON blob in an HTML comment:
    <!-- {"item-identifier":"POI-123","issue-description":"..."} -->
    """
    m = re.search(r"<!--\s*(\{.*?\})\s*-->", body, re.DOTALL)
    if not m:
        return {}
    return json.loads(m.group(1))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--label",    required=True)
    p.add_argument("--output",   default="issues.csv")
    args = p.parse_args()

    token = os.environ["GITHUB_TOKEN"]
    repo_name = os.environ["REPO"]
    gh = Github(token)
    repo = gh.get_repo(repo_name)

    issues = repo.get_issues(state="open", labels=[args.label])
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["number","item_identifier","description","user","created_at","url"])
        for issue in issues:
            data = parse_frontmatter(issue.body or "")
            item = data.get("item-identifier","").strip()
            desc = data.get("issue-description","").strip()
            w.writerow([
                issue.number,
                item,
                desc,
                issue.user.login,
                issue.created_at.isoformat(),
                issue.html_url
            ])

if __name__=="__main__":
    main()
