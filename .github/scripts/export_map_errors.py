#!/usr/bin/env python3
# .github/scripts/export_map_errors.py

import os
import re
import json
import csv
import argparse
from github import Github


def parse_frontmatter(body: str) -> dict:
    """
    GitHub Issue Forms embed a JSON blob in an HTML comment:
    <!-- {"item-identifier":"POI-123","issue-description":"..."} -->
    """
    match = re.search(r'<!--\s*(\{.*?\})\s*-->', body, re.DOTALL)
    if not match:
        return {}
    return json.loads(match.group(1))


def main():
    parser = argparse.ArgumentParser(description="Export GH issues with a specific label into CSV")
    parser.add_argument("--label", required=True, help="Label to filter issues (e.g. map-error)")
    parser.add_argument("--output", default="issues.csv", help="Name of the output CSV file")
    args = parser.parse_args()

    token = os.environ["GITHUB_TOKEN"]
    repo_name = os.environ["REPO"]
    gh = Github(token)
    repo = gh.get_repo(repo_name)

    issues = repo.get_issues(state="open", labels=[args.label])
    with open(args.output, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["number", "item_identifier", "description", "user", "created_at", "url"])
        for issue in issues:
            data = parse_frontmatter(issue.body or "")
            writer.writerow([
                issue.number,
                data.get("item-identifier", "").strip(),
                data.get("issue-description", "").strip(),
                issue.user.login,
                issue.created_at.isoformat(),
                issue.html_url
            ])

if __name__ == "__main__":
    main()