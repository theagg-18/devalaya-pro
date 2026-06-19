import requests
import json
import sys
import getpass

REPO = "theagg-18/devalaya-pro"
BRANCH = "main"

def protect_branch():
    print(f"--- Devalaya Branch Protection Setup ---")
    print(f"Target: {REPO}:{BRANCH}")
    
    token = getpass.getpass("Enter GitHub Personal Access Token (repo/admin scope): ").strip()
    if not token:
        print("Token required.")
        return

    url = f"https://api.github.com/repos/{REPO}/branches/{BRANCH}/protection"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Configuration Rules
    payload = {
        "required_status_checks": {
            "strict": True,
            "contexts": ["CodeQL"]
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False
    }

    print("\nAttempting to apply protection rules...")
    
    try:
        resp = requests.put(url, headers=headers, json=payload)
        
        if resp.status_code == 200:
            print(f"\n[SUCCESS] Branch '{BRANCH}' is now PROTECTED.")
            print("Rules Applied:")
            print("- 1 Review Required")
            print("- CodeQL Status Check Required")
            print("- No Force Pushes")
            print("- No Deletions")
        else:
            print(f"\n[ERROR] Failed to set protection: {resp.status_code}")
            print(resp.text)
            print("\nCheck if your token has 'repo' scope and you are an Admin.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    protect_branch()
