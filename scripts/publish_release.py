import os
import requests
import json
import sys

# Append root to path to import version
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import version

VERSION = version.__version__
REPO = "theagg-18/devalaya-pro"

def get_release_notes(ver):
    for entry in version.VERSION_HISTORY:
        if entry['version'] == ver:
            changes = "\n- ".join(entry['changes'])
            return f"**Devalaya Pro v{ver}**\n\n### Changes\n- {changes}"
    return f"Devalaya Pro v{ver}"

def create_release():
    print(f"--- Devalaya Release Publisher v{VERSION} ---")
    print(f"Target Repo: {REPO}")
    
    token = input("Enter GitHub Personal Access Token (repo scope): ").strip()
    if not token:
        print("Token required.")
        return

    notes = get_release_notes(VERSION)
    print("\nRelease Notes Preview:")
    print("-" * 20)
    print(notes)
    print("-" * 20)
    
    if input("Proceed? (y/n): ").lower() != 'y':
        return

    api_url = f"https://api.github.com/repos/{REPO}/releases"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "tag_name": f"v{VERSION}",
        "name": f"v{VERSION}",
        "body": notes,
        "draft": False,
        "prerelease": False
    }

    resp = requests.post(api_url, headers=headers, json=payload)
    
    if resp.status_code == 201:
        print(f"\n[SUCCESS] Release created: {resp.json().get('html_url')}")
    else:
        print(f"\n[ERROR] Failed to create release: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    create_release()
