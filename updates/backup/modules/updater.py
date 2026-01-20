import os
import sys
import shutil
import zipfile
import threading
import time
import subprocess
import requests
import logging
from flask import current_app

# Global Maintenance Flag
MAINTENANCE_MODE = False
UPDATE_STATUS = "Idle"
LAST_ERROR = None

# Constants
BASE_DIR = os.getcwd()
BACKUP_DIR = os.path.join(BASE_DIR, 'updates', 'backup')
TEMP_DIR = os.path.join(BASE_DIR, 'updates', 'temp')
EXCLUDE_DIRS = {'.git', '.gemini', '__pycache__', 'backups', 'updates', 'venv', 'env'}
EXCLUDE_FILES = {'temple.db', '.env', 'debug_checkout.log'}

def set_maintenance_mode(active):
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = active
    
def get_status():
    return {
        'maintenance': MAINTENANCE_MODE,
        'status': UPDATE_STATUS,
        'error': LAST_ERROR
    }

def safe_copy_tree(src, dst):
    """Copy directory tree processing ignores."""
    if not os.path.exists(dst):
        os.makedirs(dst)
        
    for item in os.listdir(src):
        # Skip excluded
        if item in EXCLUDE_DIRS or item in EXCLUDE_FILES:
            continue
            
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        
        # Special handling for static/uploads
        if item == 'static':
            if not os.path.exists(d):
                os.makedirs(d)
            for static_item in os.listdir(s):
                if static_item == 'uploads':
                    continue # Don't touch uploads
                s_static = os.path.join(s, static_item)
                d_static = os.path.join(d, static_item)
                if os.path.isdir(s_static):
                    shutil.copytree(s_static, d_static)
                else:
                    shutil.copy2(s_static, d_static)
            continue

        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

def perform_update(update_source, is_url=True):
    global UPDATE_STATUS, LAST_ERROR, MAINTENANCE_MODE
    
    try:
        # STEP 1: Lock System
        UPDATE_STATUS = "Step 1/7: Locking System..."
        MAINTENANCE_MODE = True
        time.sleep(1) # Allow requests to drain
        
        # Clean previous runs
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(BACKUP_DIR)
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
            
        # STEP 2: Backup
        UPDATE_STATUS = "Step 2/7: Creating Rollback Backup..."
        safe_copy_tree(BASE_DIR, BACKUP_DIR)
        
        # STEP 3: Fetch & Extract
        UPDATE_STATUS = "Step 3/7: Downloading & Extracting..."
        os.makedirs(TEMP_DIR)
        
        zip_path = os.path.join(BASE_DIR, 'update_package.zip')
        
        if is_url:
            # Download from GitHub or URL
            r = requests.get(update_source, stream=True)
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            # Local file copy
            shutil.copy(update_source, zip_path)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(TEMP_DIR)
            
        # Handle GitHub archives usually having a root folder
        extracted_items = os.listdir(TEMP_DIR)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(TEMP_DIR, extracted_items[0])):
            # Move content up
            root_folder = os.path.join(TEMP_DIR, extracted_items[0])
            for item in os.listdir(root_folder):
                shutil.move(os.path.join(root_folder, item), TEMP_DIR)
            os.rmdir(root_folder)
            
        # STEP 4: Validation
        UPDATE_STATUS = "Step 4/7: Validating Update..."
        required_files = ['app.py', 'database.py', 'version.py']
        for f in required_files:
            if not os.path.exists(os.path.join(TEMP_DIR, f)):
                raise Exception(f"Validation Failed: {f} missing in update")
        
        # Test compile
        try:
            import compileall
            if not compileall.compile_dir(TEMP_DIR, quiet=1):
                raise Exception("Python syntax check failed")
        except Exception as e:
            raise Exception(f"Code validation failed: {e}")
            
        # STEP 5: Apply Update (Atomic Switch)
        UPDATE_STATUS = "Step 5/7: Switching Versions..."
        
        # Safe Delete current files (keeping data)
        for item in os.listdir(BASE_DIR):
            if item in EXCLUDE_DIRS or item in EXCLUDE_FILES or item == 'updates':
                continue
            path = os.path.join(BASE_DIR, item)
            if item == 'static':
                # Special static handling to preserve uploads
                for static_item in os.listdir(path):
                    if static_item == 'uploads': continue
                    p = os.path.join(path, static_item)
                    if os.path.isdir(p): shutil.rmtree(p)
                    else: os.remove(p)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
                
        # Move new files in
        safe_copy_tree(TEMP_DIR, BASE_DIR)
        
        # Run Migrations (Optional but recommended here)
        # Using subprocess to run manager commands or direct DB calls
        
        # STEP 6: Restart
        UPDATE_STATUS = "Step 6/7: Restarting Service..."
        MAINTENANCE_MODE = False # Will be reset by restart anyway
        
        # Trigger Restart
        if sys.platform == 'win32':
            # Windows restart
            args = [sys.executable] + sys.argv
            subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
            os._exit(0)
        else:
            # Unix exec
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
    except Exception as e:
        UPDATE_STATUS = "Rollback Initiated..."
        logging.exception(f"Update failed: {e}")
        LAST_ERROR = "Update failed. See server logs for details."
        rollback()

def rollback():
    global UPDATE_STATUS
    try:
        UPDATE_STATUS = "Rolling back changes..."
        # Restore from Backup
        if os.path.exists(BACKUP_DIR):
             # Clear current
             for item in os.listdir(BASE_DIR):
                if item in EXCLUDE_DIRS or item in EXCLUDE_FILES or item == 'updates':
                    continue
                path = os.path.join(BASE_DIR, item)
                if os.path.isdir(path): shutil.rmtree(path)
                else: os.remove(path)
                
             # Copy back
             safe_copy_tree(BACKUP_DIR, BASE_DIR)
             
        UPDATE_STATUS = f"Rollback Complete. Error: {LAST_ERROR}"
        MAINTENANCE_MODE = False
    except Exception as e:
        logging.exception(f"Rollback failed: {e}")
        UPDATE_STATUS = "CRITICAL: Rollback Failed! Check server logs."

def start_update_thread(source, is_url=True):
    t = threading.Thread(target=perform_update, args=(source, is_url))
    t.start()
