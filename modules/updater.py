import os
import sys
import shutil
import zipfile
import threading
import time
import subprocess
import requests
from flask import current_app
import logging

# Global Maintenance Flag
MAINTENANCE_MODE = False
UPDATE_STATUS = "Idle"
LAST_ERROR = None

# Constants
BASE_DIR = os.getcwd()
BACKUP_DIR = os.path.join(BASE_DIR, 'updates', 'backup')
TEMP_DIR = os.path.join(BASE_DIR, 'updates', 'temp')
EXCLUDE_DIRS = {'.git', '.gemini', '__pycache__', 'backups', 'updates', 'venv', 'env', '.venv', 'logs'}
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
            
        # STEP 4: Validation (Basic Zip Check)
        UPDATE_STATUS = "Step 4/6: Validating Update Package..."
        if not zipfile.is_zipfile(zip_path):
             raise Exception("Invalid Update Package (Not a Zip)")
             
        # STEP 5: Spawn Manager for Atomic Update
        UPDATE_STATUS = "Step 5/6: Handing over to Update Manager..."
        
        # We need to spawn manager.py --update
        # This new process will:
        # 1. Stop this server
        # 2. Extract the update
        # 3. Restart this server
        
        python_executable = sys.executable
        manager_script = os.path.join(BASE_DIR, 'manager.py')
        
        cmd = [python_executable, manager_script, '--update']
        
        print(f"Spawning Update Manager: {cmd}")
        
        if sys.platform == 'win32':
             subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
             subprocess.Popen(cmd, start_new_session=True)
             
        UPDATE_STATUS = "Update Manager Started. Server will restart shortly."
        MAINTENANCE_MODE = False 
        
    except Exception as e:
        # Log full exception details server-side
        logging.error("Update failed, initiating rollback.", exc_info=True)
        UPDATE_STATUS = "Rollback Initiated..."
        # Store a generic, non-sensitive error summary for clients
        LAST_ERROR = "Update failed. Rollback has been initiated. Check server logs for details."
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
        # Log full rollback failure details without exposing them to clients
        logging.error("CRITICAL: Rollback failed.", exc_info=True)
        UPDATE_STATUS = "CRITICAL: Rollback Failed! Check server logs for details."

def start_update_thread(source, is_url=True):
    t = threading.Thread(target=perform_update, args=(source, is_url))
    t.start()
