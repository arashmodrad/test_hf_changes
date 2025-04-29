#!/usr/bin/env python3
# .github/scripts/export_map_errors.py

import os
import re
import json 
import csv
import argparse
from github import Github # Make sure PyGithub is installed

def parse_issue_body(body: str) -> dict:
    data = {}
    if not body:
        return data
    lines = body.splitlines()
    current_section = None
    section_content = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("### "):
            if current_section:
                data[current_section] = "\n".join(section_content).strip()
            current_section = stripped_line[4:].strip()
            section_content = []
        elif current_section and stripped_line:
            section_content.append(stripped_line)
    if current_section:
        data[current_section] = "\n".join(section_content).strip()
    return data

def main():
    parser = argparse.ArgumentParser(description="Export GH issues with a specific label into CSV")
    parser.add_argument("--label", required=True, help="Label to filter issues (e.g. map-error)")
    parser.add_argument("--output", default="issues.csv", help="Name of the output CSV file")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("REPO")

    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        exit(1)
    if not repo_name:
        print("Error: REPO environment variable not set.")
        exit(1)

    try:
        gh = Github(token)
        repo = gh.get_repo(repo_name)
        print(f"Attempting to fetch issues with state='open' and label='{args.label}' from {repo_name}...")
        issues = repo.get_issues(state="open", labels=[args.label])
        issue_list = list(issues)
        print(f"Found {len(issue_list)} issues matching criteria.")
        if not issue_list:
            print("No issues found matching criteria. CSV will only contain header.")

        with open(args.output, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "issue_number",
                "item_identifier",
                "pick",
                "issue_type",
                "vpu",
                "topology_toid",
                "description",
                "reporter_user",
                "created_at_utc",
                "issue_url"
            ])
            for issue in issue_list:
                print(f"Processing issue #{issue.number}...")
                data = parse_issue_body(issue.body or "")
                print(f"Parsed data for issue #{issue.number}: {data}")
                writer.writerow([
                    issue.number,
                    data.get("Item Identifier", ""),
                    data.get("Pick", ""),
                    data.get("Issue Type", ""),
                    data.get("VPU", ""),
                    data.get("Topology toid", ""),
                    data.get("Describe the issue", ""),
                    issue.user.login,
                    issue.created_at.isoformat(),
                    issue.html_url
                ])
        print(f"Successfully exported issues to {args.output}")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()