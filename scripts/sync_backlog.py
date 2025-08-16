#!/usr/bin/env python
"""
Sync backlog YAML to GitHub Issues, Labels, and Milestones.

Requirements:
- env: GITHUB_TOKEN (repo scope), GITHUB_REPOSITORY (e.g., owner/name)
- file: .github/backlog.yml

Usage:
  python scripts/sync_backlog.py
"""
import os
import sys
import time
import json
from pathlib import Path

import requests
import yaml

GITHUB_API = "https://api.github.com"
BACKLOG_FILE = Path(".github/backlog.yml")

TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")  # e.g., owner/name

if not TOKEN or not REPO:
    print("GITHUB_TOKEN and GITHUB_REPOSITORY env vars are required", file=sys.stderr)
    sys.exit(1)

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})


def gh(method: str, path: str, **kwargs):
    url = f"{GITHUB_API}{path}"
    r = session.request(method, url, **kwargs)
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub API error {r.status_code}: {r.text}")
    return r.json() if r.text else {}


def ensure_label(label):
    name = label["name"]
    color = label.get("color", "cccccc")
    description = label.get("description", "")
    # Try update; if not exists, create
    try:
        gh("PATCH", f"/repos/{REPO}/labels/{name}", json={"new_name": name, "color": color, "description": description})
    except RuntimeError:
        gh("POST", f"/repos/{REPO}/labels", json={"name": name, "color": color, "description": description})


def ensure_milestone(title, description=""):
    # list milestones
    milestones = gh("GET", f"/repos/{REPO}/milestones?state=all")
    for m in milestones:
        if m["title"] == title:
            # update description if needed
            if (m.get("description") or "") != description:
                gh("PATCH", f"/repos/{REPO}/milestones/{m['number']}", json={"description": description})
            return m["number"]
    m = gh("POST", f"/repos/{REPO}/milestones", json={"title": title, "description": description})
    return m["number"]


def find_issue_by_title(title):
    # Search issues by title
    q = f"repo:{REPO} is:issue in:title \"{title}\""
    res = gh("GET", f"/search/issues?q={requests.utils.quote(q)}")
    for item in res.get("items", []):
        if item.get("title") == title:
            return item
    return None


def ensure_issue(issue, milestone_numbers):
    title = issue["title"]
    body = issue.get("body", "")
    labels = issue.get("labels", [])
    milestone_title = issue.get("milestone")
    milestone = milestone_numbers.get(milestone_title) if milestone_title else None

    existing = find_issue_by_title(title)
    if existing:
        # Update labels/body/milestone
        number = existing["number"]
        gh("PATCH", f"/repos/{REPO}/issues/{number}", json={
            "body": body,
            "labels": labels,
            "milestone": milestone,
            "state": "open",
        })
        return number
    new_issue = gh("POST", f"/repos/{REPO}/issues", json={
        "title": title,
        "body": body,
        "labels": labels,
        "milestone": milestone,
    })
    return new_issue["number"]


def main():
    if not BACKLOG_FILE.exists():
        print(f"Backlog file not found: {BACKLOG_FILE}", file=sys.stderr)
        sys.exit(1)

    with BACKLOG_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    for label in data.get("labels", []):
        ensure_label(label)

    milestone_numbers = {}
    for m in data.get("milestones", []):
        number = ensure_milestone(m.get("title"), m.get("description", ""))
        milestone_numbers[m["title"]] = number

    for issue in data.get("issues", []):
        ensure_issue(issue, milestone_numbers)

    print("Backlog sync completed.")


if __name__ == "__main__":
    main()
