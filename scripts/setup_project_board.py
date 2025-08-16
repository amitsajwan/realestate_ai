#!/usr/bin/env python
"""
Create/Update a GitHub Project (v2) board for this repo and auto-triage issues.
- Creates a Project (v2) under the repository owner
- Adds a custom single-select field "Timeline" with options: Now, Next, Later
- Adds repo issues to the project and sets Timeline based on milestone title mapping:
  Week 1 -> Now, Week 2 -> Next, Weeks 3-4 -> Later

Env (provided by GitHub Actions):
- GITHUB_TOKEN (automatic)
- GITHUB_REPOSITORY: owner/repo

Usage (in GitHub Actions):
  python scripts/setup_project_board.py --title "CRM Roadmap"
"""
import argparse
import os
import sys
import requests

GQL = "https://api.github.com/graphql"
TOKEN = os.getenv("GITHUB_TOKEN")
REPO_FULL = os.getenv("GITHUB_REPOSITORY")  # owner/repo

if not TOKEN or not REPO_FULL:
    print("Missing GITHUB_TOKEN or GITHUB_REPOSITORY", file=sys.stderr)
    sys.exit(1)

S = requests.Session()
S.headers.update({
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
})


def gql(query, variables=None):
    r = S.post(GQL, json={"query": query, "variables": variables or {}}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"GraphQL HTTP {r.status_code}: {r.text}")
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]


def get_owner_id(login: str):
    q = """
    query($login:String!) {
      repositoryOwner(login: $login) { id __typename }
    }
    """
    d = gql(q, {"login": login})
    owner = d["repositoryOwner"]
    if not owner:
        raise RuntimeError("Owner not found")
    return owner["id"]


def find_project(owner_login: str, title: str):
    q = """
    query($login:String!, $first:Int!) {
      repositoryOwner(login:$login) {
        ... on Organization { projectsV2(first:$first) { nodes { id title } } }
        ... on User { projectsV2(first:$first) { nodes { id title } } }
      }
    }
    """
    d = gql(q, {"login": owner_login, "first": 50})
    nodes = d["repositoryOwner"]["projectsV2"]["nodes"] or []
    for p in nodes:
        if p["title"].strip().lower() == title.strip().lower():
            return p["id"]
    return None


def create_project(owner_id: str, title: str):
    m = """
    mutation($ownerId:ID!, $title:String!) {
      createProjectV2(input:{ownerId:$ownerId, title:$title}) {
        projectV2 { id }
      }
    }
    """
    d = gql(m, {"ownerId": owner_id, "title": title})
    return d["createProjectV2"]["projectV2"]["id"]


def ensure_field(project_id: str, name: str, options: list[str]):
    # Check existing fields
    q = """
    query($id:ID!) { node(id:$id) { ... on ProjectV2 { fields(first:50) { nodes { id name dataType ... on ProjectV2SingleSelectField { options { id name } } } } } } }
    """
    d = gql(q, {"id": project_id})
    fields = d["node"]["fields"]["nodes"]
    for f in fields:
        if f["name"].lower() == name.lower():
            # Ensure all options exist (for single select)
            if f.get("dataType") == "SINGLE_SELECT":
                existing = {o["name"] for o in f.get("options", [])}
                if set(options).issubset(existing):
                    return f["id"], {o["name"]: o["id"] for o in f.get("options", [])}
            # If name matches but not single select, create a new one with a suffix
            name = f"{name} (v2)"
            break
    # Create new field
    m = """
    mutation($projectId:ID!, $name:String!, $options:[ProjectV2SingleSelectFieldOptionInput!]!) {
      createProjectV2Field(input:{projectId:$projectId, dataType:SINGLE_SELECT, name:$name, singleSelectOptions:$options}) {
        projectV2Field { id }
      }
    }
    """
    opts = [{"name": o} for o in options]
    d = gql(m, {"projectId": project_id, "name": name, "options": opts})
    field_id = d["createProjectV2Field"]["projectV2Field"]["id"]
    # Re-query to get option IDs
    d2 = gql(q, {"id": project_id})
    for f in d2["node"]["fields"]["nodes"]:
        if f["id"] == field_id:
            return field_id, {o["name"]: o["id"] for o in f.get("options", [])}
    raise RuntimeError("Failed to retrieve created field options")


def list_repo_issues(owner: str, repo: str):
    q = """
    query($owner:String!, $repo:String!, $n:Int!) {
      repository(owner:$owner, name:$repo) {
        issues(first:$n, states:OPEN, orderBy:{field:CREATED_AT, direction:ASC}) {
          nodes { id number title milestone { title } }
        }
      }
    }
    """
    d = gql(q, {"owner": owner, "repo": repo, "n": 100})
    return d["repository"]["issues"]["nodes"]


def add_item(project_id: str, content_id: str):
    m = """
    mutation($projectId:ID!, $contentId:ID!) {
      addProjectV2ItemById(input:{projectId:$projectId, contentId:$contentId}) { item { id } }
    }
    """
    d = gql(m, {"projectId": project_id, "contentId": content_id})
    return d["addProjectV2ItemById"]["item"]["id"]


def ensure_item_and_set_field(project_id: str, item_content_id: str, field_id: str, option_id: str):
    item_id = add_item(project_id, item_content_id)
    m = """
    mutation($projectId:ID!, $itemId:ID!, $fieldId:ID!, $optionId:String!) {
      updateProjectV2ItemFieldValue(input:{projectId:$projectId, itemId:$itemId, fieldId:$fieldId, value:{singleSelectOptionId:$optionId}}) { projectV2Item { id } }
    }
    """
    gql(m, {"projectId": project_id, "itemId": item_id, "fieldId": field_id, "optionId": option_id})


def timeline_option_for_milestone(title: str | None) -> str | None:
    if not title:
        return None
    t = title.strip().lower()
    if t == "week 1":
        return "Now"
    if t == "week 2":
        return "Next"
    if t in ("weeks 3-4", "weeks 3–4"):
        return "Later"
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="CRM Roadmap")
    args = parser.parse_args()

    owner, repo = REPO_FULL.split("/", 1)
    owner_id = get_owner_id(owner)

    project_id = find_project(owner, args.title)
    if not project_id:
        project_id = create_project(owner_id, args.title)
        print(f"Created project: {args.title}")
    else:
        print(f"Using existing project: {args.title}")

    field_id, options = ensure_field(project_id, name="Timeline", options=["Now", "Next", "Later"])

    issues = list_repo_issues(owner, repo)
    for issue in issues:
        ms_title = issue.get("milestone", {}).get("title") if issue.get("milestone") else None
        opt_name = timeline_option_for_milestone(ms_title)
        try:
            item_id = add_item(project_id, issue["id"])  # add first; if already exists, API still succeeds by creating a new item
        except Exception as e:
            # try to continue
            print(f"Add item failed for #{issue['number']}: {e}")
            continue
        if opt_name and opt_name in options:
            try:
                ensure_item_and_set_field(project_id, issue["id"], field_id, options[opt_name])
            except Exception as e:
                print(f"Set field failed for #{issue['number']}: {e}")

    print("Project setup completed.")


if __name__ == "__main__":
    main()
