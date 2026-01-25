# Software Update Guide

This document explains how to release and install updates for the Devalaya Billing System when using the Windows Installer method.

## 1. Developer Workflow (Releasing an Update)

When you have made code changes and want to release a new version (e.g., v1.6.1):

### Step 1: Update Version
1.  Open `version.py` in your code editor.
2.  Change `__version__ = "1.6.0"` to `"1.6.1"`.

### Step 2: Rebuild the Executable
1.  Open your terminal in the project folder.
2.  Run the build command:
    ```powershell
    python build_exe.py
    ```
    *This generates a new `dist\DevalayaBilling.exe` with your latest code.*

### Step 3: Update the Installer Script
1.  Open `setup.iss` in **Inno Setup**.
2.  Find the line `AppVersion=1.6.0` and change it to `AppVersion=1.6.1`.
    *   *Optional: Update `OutputBaseFilename` to `DevalayaBillingSetup_v1.6.1` so the installer filename reflects the version.*

### Step 4: Compile the Installer
1.  Click **Build** -> **Compile** (or the Play/Run button).
2.  Inno Setup will create the new installer file in the `Output` folder.

---

## 2. User Workflow (Installing the Update)

Distribute the new `DevalayaBillingSetup_v1.6.1.exe` to your users.

### How to Install
1.  **Backup (Optional but Recommended)**: It's always good practice to copy the `temple.db` file to a safe place before any major change, though the installer is designed to be safe.
2.  **Run the Setup**: Double-click the new installer file.
3.  **Follow the Wizard**: Click "Next", "Install", "Finish".
    *   **Do NOT uninstall the old version first.** Just install right over it.
    *   Windows might say "Folder already exists". This is normal. Click "Yes".

### What Happens to Data?
*   **Code & Features**: The old `.exe` is replaced with the new one.
*   **Database (`temple.db`)**: The installer **DOES NOT** touch this file. Your existing bills, products, and settings remain 100% safe.
*   **Backups**: `backups/` folder is also untouched.

### Verification
After installation, open the application. The version number at the bottom of the dashboard should now show `v1.6.1`.
