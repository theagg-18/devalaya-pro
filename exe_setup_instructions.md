# Devalaya Billing System - Executable Setup Guide

## Overview
This document explains how to build and use the standalone executable (`.exe`) version of the Devalaya Billing System. This allows running the application without installing Python or managing dependencies on the target machine.

## Build Instructions
To create the `.exe` file, run the following command in your project directory:

```powershell
python build_exe.py
```

This script will:
1. Install `pyinstaller` if missing.
2. Package the application, static files, and templates into a single file.
3. Output the result to `dist/DevalayaBilling.exe`.

## Installation & Deployment
1. **Locate the Exe**: Go to the `dist` folder.
2. **Copy to Target**: Copy `DevalayaBilling.exe` to a folder on the host computer (e.g., `C:\DevalayaBilling\`).
3. **Data Persistence**:
   - The first time you run the exe, it will create `temple.db` and a `backups` folder **in the same directory** as the exe.
   - **IMPORTANT**: If you have existing data, copy your `temple.db` to this directory *before* or *after* running the exe.
   - **Environment Variables**: If you use a custom `.env` file, copy it to the same directory as the exe.

## Running the Application
Double-click `DevalayaBilling.exe` to start.

- A console window will open showing the server status.
- The default web browser will automatically open to `http://localhost:5000`.
- **Do not close the console window**; this stops the server.

## Network Access (Other Devices)
To access the billing system from other devices (Tablets, Phones, other PCs) on the same Wi-Fi/Network:

1. Look at the console output when you start the exe. It will display:
   ```
   ACCESS INSTRUCTIONS:
    1. On this PC:      http://localhost:5000
    2. Other Devices:   http://192.168.1.5:5000
       OR Domain:       http://devalaya-pro.local:5000
   ```
2. On the other device, open a browser and type:
   - **http://devalaya-pro.local:5000** (Preferred)
   - OR the IP address shown (e.g., `http://192.168.1.5:5000`)

   *Note: `.local` domains work natively on Android, iOS, macOS, and Linux. On Windows, ensure Bonjour (via iTunes) or equivalent mDNS support is available, though Windows 10/11 often supports this out of the box.*

## Updates
To update the application:
1. Build the new version using `python build_exe.py`.
2. Replace the old `DevalayaBilling.exe` with the new one.
3. **Keep** your `temple.db` and `backups` folder; do not delete them.

- **Configuration**: `config.py` and `app.py` have been modified to detect if they are running in "frozen" mode (exe) and adjust paths accordingly (`sys._MEIPASS` for assets, `sys.executable` dir for data).

## Troubleshooting "Domain Not Working"
If `http://devalaya-pro.local:5000` is not accessible:

1.  **Check Console Output**: When the server starts, it will print `[*] Local Domain: http://devalaya-pro.local:5000`. If it says `ERROR`, note the message.
2.  **Firewall**: The Windows Firewall (or Antivirus) must allow `DevalayaBilling.exe` to access the network.
    - When you run it for the first time, Windows usually asks to "Allow Access" to Private Networks. Make sure to click **Allow**.
3.  **Bonjour Service**: On older Windows versions, you may need to install "Bonjour Print Services" for Windows to resolve `.local` domains. (Windows 10/11 usually works without this).
4.  **Fallback**: If the domain persists in failing, use the **IP Address** shown in the console (e.g., `http://192.168.1.5:5000`).
