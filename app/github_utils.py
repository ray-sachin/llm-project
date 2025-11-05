# app/github_utils.py
import os
import time
import requests
from github import Github
from github import GithubException
import httpx
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
USERNAME = os.getenv("GITHUB_USERNAME")
g = Github(GITHUB_TOKEN)

def create_repo(repo_name: str, description: str = ""):
    """
    Create a public repository with the given name.
    """
    user = g.get_user()
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

def enable_pages(repo_name: str, branch: str = "main", retries: int = 3, delay: int = 2):
    """
    Enable GitHub Pages via the REST API.
    """
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("USERCODE")
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
        elif response.status_code == 422:  # Already exists
            print("⚠ Pages already enabled.")
            return True
        else:
            print(f"Pages API attempt {attempt+1} failed:", response.status_code, response.text)
            time.sleep(delay)

    print("❌ Failed to enable GitHub Pages after retries.")
    return False

def generate_mit_license(owner_name=None):
    year = datetime.utcnow().year
    owner = owner_name or USERNAME or "Owner"
    return f"""MIT License

Copyright (c) {year} {owner}

Permission is hereby granted, free of charge, to any person obtaining a copy...
[Full MIT license text omitted here for brevity — replace in production with full license text]
"""
