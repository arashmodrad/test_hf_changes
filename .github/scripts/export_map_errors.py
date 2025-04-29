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
    # Setup argument parsing for label and output file name
    parser = argparse.ArgumentParser(description="Export GH issues with a specific label into CSV")
    parser.add_argument("--label", required=True, help="Label to filter issues (e.g. map-error)")
    parser.add_argument("--output", default="issues.csv", help="Name of the output CSV file")
    args = parser.parse_args()

    # Get GitHub Token and Repo name from environment variables set by GitHub Actions
    # REPO will be in the format "owner/repo" (e.g., "arashmodrad/test_hf_changes")
    token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("REPO")

    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        exit(1)
    if not repo_name:
        print("Error: REPO environment variable not set.")
        exit(1)

    try:
        # Authenticate with GitHub API
        gh = Github(token)
        # Get the repository object
        repo = gh.get_repo(repo_name)

        # Fetch issues with the specified label that are currently open
        print(f"Fetching issues with label '{args.label}' from {repo_name}...")
        issues = repo.get_issues(state="open", labels=[args.label])

        # Open the specified output CSV file for writing
        # newline="" is crucial for csv module to prevent extra blank rows
        with open(args.output, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write the header row for the CSV
            writer.writerow(["issue_number", "item_identifier", "description", "reporter_user", "created_at_utc", "issue_url"])

            # Iterate through the fetched issues
            for issue in issues:
                print(f"Processing issue #{issue.number}...")
                # Parse the structured data from the issue body
                data = parse_frontmatter(issue.body or "") # Use issue.body or empty string if body is None

                # Extract the specific fields, providing default empty strings if keys are missing
                # .strip() removes leading/trailing whitespace
                item_identifier = data.get("item-identifier", "").strip()
                issue_description = data.get("issue-description", "").strip()

                # Write a row to the CSV file
                writer.writerow([
                    issue.number, # Issue number
                    item_identifier, # Data from the 'item-identifier' form field
                    issue_description, # Data from the 'issue-description' form field
                    issue.user.login, # GitHub username of the reporter
                    issue.created_at.isoformat(), # Timestamp in ISO 8601 format (UTC)
                    issue.html_url # URL of the issue on GitHub
                ])
        print(f"Successfully exported issues to {args.output}")

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)


if __name__ == "__main__":
    main()