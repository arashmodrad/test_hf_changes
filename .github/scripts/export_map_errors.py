#!/usr/bin/env python3
# .github/scripts/export_map_errors.py

import os
import re
import json # Keep json import, though not used in the new parse
import csv
import argparse
from github import Github # Make sure PyGithub is installed

# --- MODIFIED parse_issue_body FUNCTION ---
def parse_issue_body(body: str) -> dict:
    """
    Parses the issue body looking for markdown headers
    to extract Item Identifier and Description.
    This is a workaround if the Issue Form doesn't embed the JSON comment.
    """
    data = {}
    if not body:
        return data

    # Split the body into lines
    lines = body.splitlines()

    # Flags to know which section we are currently in
    in_item_identifier_section = False
    in_description_section = False

    item_identifier_lines = []
    description_lines = []

    for line in lines:
        # Normalize line (strip whitespace) for easier comparison
        stripped_line = line.strip()

        # Check for the start of the Item Identifier section
        if stripped_line == "### Item Identifier":
            # Reset state, start collecting lines for this section
            in_item_identifier_section = True
            in_description_section = False
            continue # Skip the header line itself

        # Check for the start of the Description section
        elif stripped_line == "### Describe the issue":
             # Reset state, start collecting lines for this section
            in_item_identifier_section = False
            in_description_section = True
            continue # Skip the header line itself

        # If we are not in any specific section, ignore the line (e.g. lines before first header)
        if not in_item_identifier_section and not in_description_section:
            continue

        # If we are in a section, collect the line content
        if in_item_identifier_section:
            # Item identifier is usually a single line after the header
            # We'll take the first non-empty line found in this section
            if stripped_line and 'item-identifier' not in data: # Only take the first non-empty line
                 data['item-identifier'] = stripped_line
                 # We found it, stop collecting for this section
                 in_item_identifier_section = False # Treat it as single-line field

        elif in_description_section:
            # Description can be multiple lines. Collect all non-empty lines.
            if stripped_line:
                description_lines.append(stripped_line)

    # Join description lines into a single string
    if description_lines:
        data['issue-description'] = "\n".join(description_lines) # Join with newline

    return data
# --- END MODIFIED parse_issue_body FUNCTION ---


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

        # --- Keep logging and list conversion from previous version ---
        issue_list = list(issues)
        print(f"Found {len(issue_list)} issues matching criteria.")
        if not issue_list:
             print("No issues found matching criteria. CSV will only contain header.")
        # --- End logging ---

        with open(args.output, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(["issue_number", "item_identifier", "description", "reporter_user", "created_at_utc", "issue_url"])

            # --- Loop over the list ---
            for issue in issue_list:
            # --- End loop ---
                print(f"Processing issue #{issue.number}...")
                # --- CALL THE NEW PARSING FUNCTION ---
                data = parse_issue_body(issue.body or "") # Use issue.body or empty string
                # --- END CALL ---
                print(f"Parsed data for issue #{issue.number}: {data}") # Added logging

                # Extract the specific fields using the new data dictionary
                # .strip() is applied to the collected lines in the parsing function now,
                # but applying again here is harmless for robustness.
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