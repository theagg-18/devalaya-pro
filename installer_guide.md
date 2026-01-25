# Creating the Windows Installer

This guide explains how to convert your standalone executable (`DevalayaBilling.exe`) into a professional Windows Installer (`setup.exe`) using **Inno Setup**.

## Prerequisites
1.  **Build the Exe First**: Ensure you have successfully run `python build_exe.py` and have the `dist\DevalayaBilling.exe` file.
2.  **Download Inno Setup**:
    *   Go to: [https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)
    *   Download and install "Inno Setup 6.x.x".

## Building the Installer
1.  Open **Inno Setup Compiler** from your Start Menu.
2.  Click **File** -> **Open**.
3.  Navigate to your project folder (where you cloned the repository) and select `setup.iss`.
4.  Click the **Compile** button (Run icon, or Build -> Compile).    *   It will read your `DevalayaBilling.exe`.
    *   It will compress it.
5.  **Done!**
    *   The final installer will be created in a new folder called `Output` inside your project directory.
    *   Filename: `DevalayaBillingSetup_v1.6.0.exe`.

## Installer Features
- **User-Friendly**: Standard Windows setup wizard.
- **Shortcuts**: Automatically creates Start Menu and Desktop shortcuts.
- **Permission Safe**: Installs to the User's AppData folder (`%LOCALAPPDATA%\Devalaya Billing System`) by default.
  - This ensures the application can write to its database (`temple.db`) without needing Administrator rights each time.
- **Safe Updates**: Installing a newer version over an older one **preserves** the existing `temple.db` and data.
## Distributing
You only need to send the `DevalayaBillingSetup_v1.6.0.exe` file to your users. They can simply double-click to install.
