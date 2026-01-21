import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGES_DIR = os.path.join(BASE_DIR, "packages")
REQUIREMENTS_FILE = os.path.join(BASE_DIR, "requirements.txt")

def download_packages():
    print(f"Downloading dependencies to {PACKAGES_DIR}...")
    if not os.path.exists(PACKAGES_DIR):
        os.makedirs(PACKAGES_DIR)
    
    # Ensure pywin32 and winshell are in requirements or added explicitly
    packages = []
    if os.path.exists(REQUIREMENTS_FILE):
        packages.append("-r")
        packages.append(REQUIREMENTS_FILE)
    
    # Add extra packages strictly needed for manager
    extra_pkgs = ["pywin32", "winshell"]
    packages.extend(extra_pkgs)

    # Command: pip download -d packages <packages>
    cmd = [sys.executable, "-m", "pip", "download", "-d", PACKAGES_DIR] + packages
    
    try:
        subprocess.check_call(cmd)
        print("\n[SUCCESS] All packages downloaded.")
        print("You can now zip this project. The 'packages' folder will be included.")
        print("The installer will automatically detect and use these offline files.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Failed to download packages: {e}")

if __name__ == "__main__":
    download_packages()
