#!/usr/bin/env python3
# .github/scripts/export_map_errors.py

import os
import re
import json
import csv
import argparse
# Make sure PyGithub is installed (handled by the workflow)
from github import Github


def parse_frontmatter(body: str) -> dict:
    """
    GitHub Issue Forms embed a JSON blob in an HTML comment:
    <!-- {"item-identifier":"POI-123","issue-description":"..."} -->
    This function extracts and parses that JSON.
    """
    # Regex to find the HTML comment containing the JSON string
    # re.DOTALL is important to match across newlines within the comment
    match = re.search(r'<!--\s*(\{.*?\})\s*-->', body, re.DOTALL)
    if not match:
        # If the comment isn't found (e.g., issue not created via the form)
        return {}
    try:
        # Parse the JSON string found in the first capturing group
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        # Handle cases where the JSON might be malformed (unlikely with GH Forms)
        print(f"Warning: Could not parse JSON from issue body: {body[:100]}...") # Print part of body for debugging
        return {}


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
        # Fetch issues
        issues = repo.get_issues(state="open", labels=[args.label])

        # --- ADD THIS LOGGING ---
        issue_list = list(issues) # Convert iterator to list to get count and iterate again
        print(f"Found {len(issue_list)} issues matching criteria.")
        if not issue_list:
             print("No issues found matching criteria. CSV will only contain header.")
        # --- END ADDED LOGGING ---


        with open(args.output, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(["issue_number", "item_identifier", "description", "reporter_user", "created_at_utc", "issue_url"])

            # --- CHANGE THIS LOOP TO USE THE LIST ---
            # for issue in issues: # Original loop
            for issue in issue_list: # Loop over the list instead
            # --- END CHANGE ---
                print(f"Processing issue #{issue.number}...")
                data = parse_frontmatter(issue.body or "")
                print(f"Parsed data for issue #{issue.number}: {data}") # Added logging

                item_identifier = data.get("item-identifier", "").strip()
                issue_description = data.get("issue-description", "").strip()

                writer.writerow([
                    issue.number,
                    item_identifier,
                    issue_description,
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