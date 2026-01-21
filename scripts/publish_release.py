import os
import requests
import json
import shutil
import mimetypes
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
        data = resp.json()
        print(f"\n[SUCCESS] Release created: {data.get('html_url')}")
        
        # Check for dist folder and offer to upload
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dist_dir = os.path.join(base_dir, "dist")
        
        if os.path.exists(dist_dir) and input("\nFound 'dist' folder. Zip and upload portable release? (y/n): ").lower() == 'y':
            zip_name = f"Devalaya-Portable-v{VERSION}.zip"
            zip_path = os.path.join(base_dir, zip_name)
            
            print(f"Zipping {zip_name}...")
            shutil.make_archive(zip_path.replace('.zip', ''), 'zip', dist_dir)
            
            upload_asset(data['upload_url'], zip_path, token)
            
            # Cleanup zip
            if os.path.exists(zip_path):
                os.remove(zip_path)
    else:
        print(f"\n[ERROR] Failed to create release: {resp.status_code}")
        print(resp.text)

def upload_asset(upload_url, file_path, token):
    print(f"Uploading {os.path.basename(file_path)}...")
    
    # Clean URL (remove templates like {?name,label})
    url = upload_url.split('{')[0]
    
    params = {'name': os.path.basename(file_path)}
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/zip"
    }
    
    with open(file_path, 'rb') as f:
        data = f.read()
        
    resp = requests.post(url, headers=headers, params=params, data=data)
    
    if resp.status_code == 201:
        print(f"[SUCCESS] Uploaded: {resp.json().get('browser_download_url')}")
    else:
        print(f"[ERROR] Upload failed: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    create_release()
