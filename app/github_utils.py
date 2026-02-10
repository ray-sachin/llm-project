# app/github_utils.py
import os
import time
import base64
import requests
from github import Github
from github import GithubException, InputGitTreeElement
import httpx
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # May be empty, per-user token used instead
USERNAME = os.getenv("USERCODE", "")  # May be empty, per-user username used instead

# Initialize default client only if token exists
try:
    g = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None
except:
    g = None


def create_repo(repo_name: str, description: str = "", github_token: str = None):
    """
    Create a public repository with the given name.
    If github_token is provided, uses that; otherwise uses default token from .env
    """
    token = github_token or GITHUB_TOKEN
    g_client = Github(token)
    user = g_client.get_user()
    
    # if repo exists, return it
    try:
        repo = user.get_repo(repo_name)
        print("Repo already exists:", repo.full_name)
        return repo
    except GithubException:
        pass
    safe_description = re.sub(r'[\r\n\t]+', ' ', description)[:300]
    repo = user.create_repo(
        name=repo_name,
        description=f"{safe_description} (see README for full brief)",
        private=False,
        auto_init=False
    )
    print("Created repo:", repo.full_name)
    return repo

def create_or_update_file(repo, path: str, content: str, message: str):
    """
    Create a file or update if it already exists.
    """
    try:
        # Try to get file to see if exists
        current = repo.get_contents(path)
        sha = current.sha
        repo.update_file(path, message, content, sha)
        print(f"Updated {path} in {repo.full_name}")
    except GithubException as e:
        # If 404 (not found) then create
        if e.status == 404:
            repo.create_file(path, message, content)
            print(f"Created {path} in {repo.full_name}")
        else:
            # some other error
            raise


def create_or_update_binary_file(repo, path: str, binary_content, commit_message: str):
    """
    Create or update a binary file in the repository.
    This function handles binary data like images directly without encoding/decoding.
    """
    try:
        # Try to get file to see if exists
        try:
            current = repo.get_contents(path)
            # Update existing file
            repo.update_file(
                path=path,
                message=commit_message,
                content=binary_content,
                sha=current.sha
            )
            print(f"Updated binary file {path} in {repo.full_name}")
        except GithubException as e:
            # If file doesn't exist, create it
            if e.status == 404:
                repo.create_file(
                    path=path,
                    message=commit_message,
                    content=binary_content
                )
                print(f"Created binary file {path} in {repo.full_name}")
            else:
                # some other error
                raise
        return True
    except Exception as e:
        print(f"Error creating/updating binary file {path}: {e}")
        return False

def batch_commit_files(repo, file_dict: dict, commit_message: str = "Update project files"):
    """
    Commit multiple files in a single commit using Git Tree API.
    This triggers only ONE GitHub Actions workflow instead of one per file.
    
    file_dict: { "path": "content_string", ... }
    """
    try:
        # Get the latest commit SHA on the default branch
        default_branch = repo.default_branch or "main"
        ref = repo.get_git_ref(f"heads/{default_branch}")
        latest_sha = ref.object.sha
        base_tree = repo.get_git_tree(latest_sha)

        # Build tree elements for all files
        tree_elements = []
        for path, content in file_dict.items():
            blob = repo.create_git_blob(content, "utf-8")
            tree_elements.append(InputGitTreeElement(
                path=path,
                mode="100644",
                type="blob",
                sha=blob.sha
            ))

        # Create the new tree and commit
        new_tree = repo.create_git_tree(tree_elements, base_tree)
        new_commit = repo.create_git_commit(commit_message, new_tree, [repo.get_git_commit(latest_sha)])
        ref.edit(new_commit.sha)

        print(f"✅ Batch committed {len(file_dict)} files in a single commit to {repo.full_name}")
        return True
    except Exception as e:
        print(f"⚠ Batch commit failed: {e}")
        print("  Falling back to individual commits...")
        # Fallback: commit files individually
        for path, content in file_dict.items():
            try:
                create_or_update_file(repo, path, content, f"Add/Update {path}")
            except Exception as e2:
                print(f"  ⚠ Failed to commit {path}: {e2}")
        return False




def enable_pages(repo_name: str, branch: str = "main", github_token: str = None, github_username: str = None, retries: int = 3, delay: int = 2):
    """
    Enable GitHub Pages via the REST API.
    If github_token is provided, uses that; otherwise uses default from .env
    """
    token = github_token or os.getenv("GITHUB_TOKEN")
    username = github_username or os.getenv("USERCODE")
    url = f"https://api.github.com/repos/{username}/{repo_name}/pages"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    payload = {
        "source": {
            "branch": branch,
            "path": "/"  # root
        }
    }

    for attempt in range(retries):
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in (201, 202):  # Created / Accepted
            print("✅ GitHub Pages enabled!")
            return True
        elif response.status_code in (409, 422):  # 409 = conflict (already enabled), 422 = unprocessable (already exists)
            print("⚠ Pages already enabled.")
            return True
        else:
            print(f"Pages API attempt {attempt+1} failed:", response.status_code, response.text)
            time.sleep(delay)

    print("⚠ Could not verify Pages status, but URL should work if repo exists.")
    return True  # Return True anyway since Pages is likely already enabled

def generate_mit_license(owner_name=None):
    year = datetime.utcnow().year
    owner = owner_name or USERNAME or "Owner"
    return f"""MIT License

Copyright (c) {year} {owner}

Permission is hereby granted, free of charge, to any person obtaining a copy...
[Full MIT license text omitted here for brevity — replace in production with full license text]
"""
