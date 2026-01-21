import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess

# Configuration
PYTHON_VERSION = "3.11.9"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist")
PYTHON_DIR = os.path.join(DIST_DIR, "python")
APP_DIR = os.path.join(DIST_DIR, "app")
REQUIREMENTS_FILE = os.path.join(BASE_DIR, "requirements.txt")

EXCLUDE_DIRS = {'.git', '.gemini', '__pycache__', 'dist', 'venv', 'env', '.venv', 'packages', 'updates', 'logs'}
EXCLUDE_FILES = {'temple.db', '.env'}

def download_file(url, dest):
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        sys.exit(1)

def build_portable():
    print(f"Building Portable Distribution in {DIST_DIR}...")
    
    # 1. Clean Dist
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)
    os.makedirs(PYTHON_DIR)
    
    # 2. Download Python Embeddable
    zip_path = os.path.join(DIST_DIR, "python.zip")
    download_file(PYTHON_URL, zip_path)
    
    print("Extracting Python...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(PYTHON_DIR)
    os.remove(zip_path)
    
    # 3. Configure Python (Enable site-packages)
    # The _pth file defaults to restricting imports. We need to uncomment "import site".
    # Construct "python311._pth" from "3.11.9"
    ver_parts = PYTHON_VERSION.split('.')
    ver_str = f"{ver_parts[0]}{ver_parts[1]}" # 311
    pth_file = os.path.join(PYTHON_DIR, f"python{ver_str}._pth")
    if os.path.exists(pth_file):
        with open(pth_file, 'r') as f:
            content = f.read()
        content = content.replace("#import site", "import site")
        with open(pth_file, 'w') as f:
            f.write(content)
            
    # 4. Install Pip
    get_pip_path = os.path.join(DIST_DIR, "get-pip.py")
    download_file(GET_PIP_URL, get_pip_path)
    
    python_exe = os.path.join(PYTHON_DIR, "python.exe")
    print("Installing Pip...")
    subprocess.check_call([python_exe, get_pip_path], cwd=DIST_DIR)
    os.remove(get_pip_path)
    
    # 5. Install Dependencies into Embedded Python
    print("Installing dependencies from requirements.txt...")
    # We must explicitly tell pip where to install because it's an embedded python
    # However, since we enabled 'import site', running python -m pip should mostly work.
    # To be safe, we rely on the pip installed in the previous step.
    
    try:
        subprocess.check_call([python_exe, "-m", "pip", "install", "-r", REQUIREMENTS_FILE], cwd=BASE_DIR)
        
        # Install explicit pywin32 if needed (often tricky in embedded, but pip usually handles it now)
        subprocess.check_call([python_exe, "-m", "pip", "install", "pywin32", "winshell"], cwd=BASE_DIR)
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)
        
    # 6. Copy App Source
    print("Copying Application Source...")
    os.makedirs(APP_DIR)
    for item in os.listdir(BASE_DIR):
        if item in EXCLUDE_DIRS or item in EXCLUDE_FILES:
            continue
        s = os.path.join(BASE_DIR, item)
        d = os.path.join(APP_DIR, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
            
    # 7. Create Launcher
    print("Creating Launcher...")
    launcher_bat = os.path.join(DIST_DIR, "Devalaya_Start.bat")
    
    # The batch file needs to use relative paths to find python and the app
    bat_content = f"""@echo off
set "DIST_DIR=%~dp0"
set "PYTHON_EXE=%DIST_DIR%python\\python.exe"
set "APP_DIR=%DIST_DIR%app"

echo Starting Devalaya Billing System...
echo Python: %PYTHON_EXE%
echo App: %APP_DIR%

cd /d "%APP_DIR%"
"%PYTHON_EXE%" run_prod.py
pause
"""
    with open(launcher_bat, "w") as f:
        f.write(bat_content)
        
    print("\n[SUCCESS] Portable build created!")
    print(f"Location: {DIST_DIR}")
    print("You can zip the 'dist' folder and distribute it. Users just run 'Devalaya_Start.bat'.")

if __name__ == "__main__":
    build_portable()
