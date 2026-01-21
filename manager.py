import os
import sys
import subprocess
import shutil
import zipfile
import platform
import time


# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_URL = "https://github.com/theagg-18/devalaya-pro"
UPDATE_ZIP_NAME = "update.zip"
REQUIREMENTS_FILE = "requirements.txt"
DB_MIGRATION_PATTERN = "migrate_*.py"
APP_PORT = 5000

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 50)
    print("   DEVALAYA BILLING SYSTEM - SYSTEM MANAGER")
    print("=" * 50)

def install_dependencies():
    print("\n[+] Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
    print("[+] Dependencies installed.")

def create_shortcuts():
    system = platform.system()
    cwd = os.getcwd()
    
    if system == "Windows":
        print("\n[+] Creating Windows Shortcuts...")
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            
            # Shortcut for Manager
            path = os.path.join(desktop, "Devalaya Manager.lnk")
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = os.path.join(cwd, "manager.bat")
            shortcut.WorkingDirectory = cwd
            shortcut.IconLocation = os.path.join(cwd, "static", "favicon.ico") # Assuming favicon exists
            shortcut.save()
            print(f"Created: {path}")

            # Shortcut for Server
            path = os.path.join(desktop, "Start Devalaya Server.lnk")
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = os.path.join(cwd, "run_prod.py")
            shortcut.Arguments = "" # run_prod is python script so might need python.exe as target if not associated
            # Better to link to a bat file for server or use python executable
            python_exe = sys.executable
            # Re-doing server shortcut to use python.exe directly to avoid association issues
            shortcut.Targetpath = python_exe
            shortcut.Arguments = f'"{os.path.join(cwd, "run_prod.py")}"'
            shortcut.WorkingDirectory = cwd
            shortcut.IconLocation = os.path.join(cwd, "static", "favicon.ico")
            shortcut.save()
            print(f"Created: {path}")
            
        except ImportError:
            print("[-] pywin32 not found. Installing to create shortcuts...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32", "winshell"])
            create_shortcuts() # Retry
        except Exception as e:
            print(f"[-] Failed to create shortcuts: {e}")

    elif system == "Linux":
        print("\n[+] Creating Linux .desktop files...")
        home = os.path.expanduser("~")
        apps_dir = os.path.join(home, ".local", "share", "applications")
        desktop_dir = os.path.join(home, "Desktop")
        
        if not os.path.exists(apps_dir):
            os.makedirs(apps_dir)
            
        # Icon path
        icon_path = os.path.join(cwd, "static", "favicon.ico") # keeping simple, png better for linux
        
        # Manager .desktop
        manager_content = f"""[Desktop Entry]
Name=Devalaya Manager
Exec="{os.path.join(cwd, 'manager.sh')}"
Icon={icon_path}
Terminal=true
Type=Application
Categories=Utility;
"""
        manager_path = os.path.join(apps_dir, "devalaya-manager.desktop")
        with open(manager_path, "w") as f:
            f.write(manager_content)
        os.chmod(manager_path, 0o755)
        
        # Link to desktop
        if os.path.exists(desktop_dir):
            shutil.copy(manager_path, os.path.join(desktop_dir, "devalaya-manager.desktop"))
            print(f"Created: {os.path.join(desktop_dir, 'devalaya-manager.desktop')}")

        # Server .desktop
        server_content = f"""[Desktop Entry]
Name=Start Devalaya Server
Exec={sys.executable} "{os.path.join(cwd, 'run_prod.py')}"
Icon={icon_path}
Terminal=true
Type=Application
Categories=Utility;
"""
        server_path = os.path.join(apps_dir, "devalaya-server.desktop")
        with open(server_path, "w") as f:
            f.write(server_content)
        os.chmod(server_path, 0o755)
        
        if os.path.exists(desktop_dir):
            shutil.copy(server_path, os.path.join(desktop_dir, "devalaya-server.desktop"))
            print(f"Created: {os.path.join(desktop_dir, 'devalaya-server.desktop')}")

def run_migrations():
    print("\n[+] Checking for database migrations...")
    migrations_dir = "migrations"
    
    if not os.path.exists(migrations_dir):
        print("Migrations directory not found.")
        return

    files = [f for f in os.listdir(migrations_dir) if f.startswith('migrate_') and f.endswith('.py')]
    if not files:
        print("No migration scripts found.")
        return

    # Add current directory to PYTHONPATH so scripts can import config/database
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    for f in files:
        print(f"Running {f}...")
        try:
            script_path = os.path.join(migrations_dir, f)
            subprocess.run([sys.executable, script_path], check=True, env=env)
        except subprocess.CalledProcessError as e:
            print(f"[-] Error running {f}: {e}")

def start_production_server():
    print("Starting Production Server...")
    # Get python executable (use current sys.executable)
    python_exe = sys.executable
    
    if platform.system() == 'Windows':
            subprocess.Popen([python_exe, "run_prod.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
            subprocess.Popen([python_exe, "run_prod.py"], start_new_session=True)
    time.sleep(2)

def stop_server(proc):
    print("Stopping server...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except psutil.TimeoutExpired:
        proc.kill()
    print("Server stopped.")

def update_system(silent=False):
    print("\n--- UPDATE SYSTEM ---")
    
    # Check if server is running
    proc = get_server_process()
    was_running = False
    if proc:
        print("[!] Server is currently running. It will be stopped for the update.")
        stop_server(proc)
        was_running = True
        time.sleep(1)
    
    # 1. Offline Update
    update_zip_path = os.path.join(BASE_DIR, UPDATE_ZIP_NAME)
    if os.path.exists(update_zip_path):
        print(f"[!] Found {UPDATE_ZIP_NAME}. Detected Offline Update.")
        if silent:
            choice = 'y'
        else:
            choice = input("Do you want to install this update? (y/n): ").lower()
        if choice == 'y':
            print("Extracting update...")
            try:
                with zipfile.ZipFile(update_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(BASE_DIR)
                print("[+] Files extracted successfully.")
                
                # Backup/Rename the zip file so it doesn't prompt again
                backup_name = os.path.join(BASE_DIR, f"{UPDATE_ZIP_NAME}.bak_{int(time.time())}")
                os.rename(update_zip_path, backup_name)
                print(f"[+] Backup created: {backup_name}")
                
            except Exception as e:
                print(f"[-] Error extracting zip: {e}")
                return
    
    # 2. Online Update
    # 2. Online Update
    elif os.path.exists(os.path.join(BASE_DIR, ".git")):
        print("[*] Git repository detected. Checking for online updates...")
        try:
            # Ensure we are in the repo root
            os.chdir(BASE_DIR)
            subprocess.run(["git", "pull"], check=True)
            print("[+] Code updated from Git.")
        except subprocess.CalledProcessError:
            print("[-] Git pull failed. Check internet connection or local changes.")
        except FileNotFoundError:
            print("[-] Git command not found.")
    else:
        # 3. Online Update (Non-Git: Download from GitHub)
        print("[*] No local update source. Checking GitHub for releases...")
        try:
            import urllib.request
            import urllib.error
            import json
            import version  # Import local version module

            api_url = "https://api.github.com/repos/theagg-18/devalaya-pro/releases/latest"
            tags_url = "https://api.github.com/repos/theagg-18/devalaya-pro/tags"
            headers = {'User-Agent': 'Devalaya-Manager'}
            
            latest_tag = None
            zip_url = None

            # 1. Try Releases
            try:
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_tag = data.get('tag_name')
                    zip_url = data.get('zipball_url')
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    print(f"[-] Failed to check releases. GitHub API returned {e.code}")
                    return
                # If 404, fall through to tags

            # 2. Try Tags (Fallback)
            if not latest_tag:
                print("[*] No formal release found. Checking tags...")
                try:
                    req = urllib.request.Request(tags_url, headers=headers)
                    with urllib.request.urlopen(req) as response:
                        tags = json.loads(response.read().decode('utf-8'))
                        if tags:
                            latest_tag = tags[0].get('name')
                            zip_url = tags[0].get('zipball_url')
                except Exception as e:
                    print(f"[-] Failed to check tags: {e}")
                    return

            if not latest_tag or not zip_url:
                print("[-] No updates found (No releases or tags).")
                return
                
            # Simple version compare
            current_ver = version.__version__
            print(f"[*] Current: {current_ver}, Latest: {latest_tag}")
            
            # Remove 'v' prefix for comparison if needed, but string match usually enough for equality
            if latest_tag == f"v{current_ver}" or latest_tag == current_ver:
                print("[+] You are already using the latest version.")
                return

                print(f"[!] New version available: {latest_tag}")
                choice = input("Do you want to download and install this update? (y/n): ").lower()
                
                if choice == 'y':
                    print("Downloading update...")
                    temp_zip = os.path.join(BASE_DIR, "temp_update.zip")
                    
                    # Download
                    with urllib.request.urlopen(zip_url) as dl_resp, open(temp_zip, 'wb') as f:
                        shutil.copyfileobj(dl_resp, f)
                    
                    print("Extracting update...")
                    # GitHub zips have a root folder (e.g., devalaya-pro-v1.5.0-xyz/...)
                    # We need to extract contents of that folder to BASE_DIR
                    with zipfile.ZipFile(temp_zip, 'r') as zf:
                        root_folder = zf.namelist()[0].split('/')[0]
                        
                        temp_extract_dir = os.path.join(BASE_DIR, "temp_extract")
                        if os.path.exists(temp_extract_dir):
                            shutil.rmtree(temp_extract_dir)
                        os.makedirs(temp_extract_dir)
                        
                        zf.extractall(temp_extract_dir)
                        
                        # Move contents
                        source_dir = os.path.join(temp_extract_dir, root_folder)
                        for item in os.listdir(source_dir):
                            s = os.path.join(source_dir, item)
                            d = os.path.join(BASE_DIR, item)
                            if os.path.exists(d):
                                if os.path.isdir(d):
                                    # shutil.copytree requires dest to not exist or dirs_exist_ok in py3.8+
                                    # We can try to rely on overwrite loop or rmtree
                                    # Safe fallback: copytree with dirs_exist_ok=True if available
                                    if sys.version_info >= (3, 8):
                                        shutil.copytree(s, d, dirs_exist_ok=True)
                                    else:
                                        # Manual merge for older python? Unlikely needed but safe:
                                        # Just remove dest and copy
                                        shutil.rmtree(d)
                                        shutil.copytree(s, d)
                                else:
                                    os.remove(d)
                                    shutil.copy2(s, d)
                            else:
                                if os.path.isdir(s):
                                    shutil.copytree(s, d)
                                else:
                                    shutil.copy2(s, d)
                                    
                    # Cleanup
                    os.remove(temp_zip)
                    shutil.rmtree(temp_extract_dir)
                    print("[+] Update installed successfully.")
                    
        except Exception as e:
            print(f"[-] Online update failed: {e}")
            return

    # 3. Post-Update Tasks
    install_dependencies()
    run_migrations()
    
    if was_running:
        print("\n[+] Restarting Server...")
        start_production_server()
        
    print("\n[SUCCESS] Update process completed.")

def get_server_process():
    try:
        import psutil
    except ImportError:
        return None

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check for python process running app.py or run_prod.py
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('run_prod.py' in arg or 'app.py' in arg for arg in cmdline):
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def server_control():
    try:
        import psutil
    except ImportError:
        print("\n[!] Error: 'psutil' module not found.")
        print("    Please select '1. Install (Setup & Shortcuts)' from the main menu first.")
        input("\nPress Enter to return to menu...")
        return

    while True:
        clear_screen()
        print_header()
        print(" SERVER CONTROL")
        print("----------------")
        
        proc = get_server_process()
        status = "STOPPED"
        if proc:
            status = "RUNNING"
            if proc.status() == psutil.STATUS_STOPPED: # Process suspended
                status = "PAUSED"
        
        print(f"Current Status: [{status}]")
        if proc:
            print(f"PID: {proc.pid}")
        
        print("\n1. Start Production Server")
        print("2. Start Dev Server (Debug Mode)")
        print("3. Stop Server")
        print("4. Pause Server")
        print("5. Resume Server")
        print("6. Back to Main Menu")
        
        choice = input("\nEnter choice: ")
        
        if choice == '1':
            if proc:
                print("Server is already running!")
            else:
                start_production_server()
        
        elif choice == '2':
             if proc:
                print("Server is already running!")
             else:
                print("Starting Dev Server (Debug Mode)...")
                # Prepare Env with DEBUG flag
                env = os.environ.copy()
                env["FLASK_DEBUG"] = "true"
                
                if platform.system() == 'Windows':
                     subprocess.Popen([sys.executable, "app.py"], creationflags=subprocess.CREATE_NEW_CONSOLE, env=env)
                else:
                     subprocess.Popen([sys.executable, "app.py"], start_new_session=True, env=env)
                time.sleep(2)

        elif choice == '3':
            if proc:
                stop_server(proc)
            else:
                print("Server is not running.")
            time.sleep(1)

        elif choice == '4':
            if proc and proc.status() != psutil.STATUS_STOPPED:
                print("Pausing server...")
                proc.suspend()
                print("Server paused.")
            else:
                print("Server not running or already paused.")
            time.sleep(1)

        elif choice == '5':
            if proc and proc.status() == psutil.STATUS_STOPPED:
                print("Resuming server...")
                proc.resume()
                print("Server resumed.")
            else:
                print("Server is not paused.")
            time.sleep(1)

        elif choice == '6':
            break

def uninstall():
    print("\n[!] WARNING: This will remove shortcuts and temporary files.")
    confirm = input("Are you sure? (y/n): ")
    if confirm.lower() != 'y':
        return

    print("Removing Shortcuts...")
    # Add logic to remove shortcuts (reverse of create_shortcuts)
    # Keeping it simple for now, notifying user
    if platform.system() == "Windows":
        try:
            import winshell
            desktop = winshell.desktop()
            p1 = os.path.join(desktop, "Devalaya Manager.lnk")
            p2 = os.path.join(desktop, "Start Devalaya Server.lnk")
            if os.path.exists(p1): os.remove(p1)
            if os.path.exists(p2): os.remove(p2)
            print("Shortcuts removed.")
        except:
             print("Could not remove shortcuts automatically.")
    
    print("Cleaning __pycache__...")
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
    
    print("[+] Uninstall clean up complete.")
    print("To fully remove the application, please delete this folder manually.")
    input("Press Enter to continue...")

def main_menu():
    while True:
        clear_screen()
        print_header()
        print("1. Install (Setup & Shortcuts)")
        print("2. Update System")
        print("3. Server Control (Start/Stop/Pause)")
        print("4. Uninstall (Cleanup)")
        print("5. Exit")
        
        choice = input("\nEnter choice: ")
        
        if choice == '1':
            install_dependencies()
            run_migrations()
            create_shortcuts()
            input("\nPress Enter to return to menu...")
        elif choice == '2':
            update_system()
            input("\nPress Enter to return to menu...")
        elif choice == '3':
            server_control()
        elif choice == '4':
            uninstall()
        elif choice == '5':
            sys.exit()

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--update':
            update_system(silent=True)
        else:
            main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit()
