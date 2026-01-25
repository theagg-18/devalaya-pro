# Linux Support Guide

The Devalaya Billing System supports Linux, but the build process works slightly differently than on Windows because **PyInstaller cannot cross-compile**. This means you cannot build a Linux app while on Windows; you must run the build script **on a Linux machine**.

## 1. Running from Source (Easiest)
On Linux (Ubuntu / Raspberry Pi OS / Fedora), you generally don't need a "setup.exe". You can run the source code directly.

1.  **Install Python3 & Pip**:
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip python3-venv git
    ```
2.  **Clone & Install**:
    ```bash
    git clone https://github.com/theagg-18/devalaya-pro.git
    cd devalaya-pro
    pip3 install -r requirements.txt
    ```
3.  **Run**:
    ```bash
    python3 launcher.py
    ```

## 2. Building a Standalone Binary (Like the .exe)
If you want a single file that works without users installing Python/Pip (e.g., to distribute to clients using Linux):

1.  **Boot into Linux**.
2.  **Prepare the Environment**:
    ```bash
    # Install Python dev tools (needed for some compilations)
    sudo apt install python3-dev
    pip3 install -r requirements.txt
    ```
3.  **Run Build Script**:
    The same script works!
    ```bash
    python3 build_exe.py
    ```
4.  **Result**:
    *   Output: `dist/DevalayaBilling` (No extension).
    *   This is your executable.
    *   You can copy this file, along with `temple.db` (if you have one), to any compatible Linux version.

## 3. Installation & Shortcuts (The "Installer" equivalent)
Linux doesn't use `.iss` installers. Instead, you create a `.desktop` file so it appears in the Application Menu.

### Creating a Desktop Shortcut
1.  Move the binary to a permanent folder, e.g., `/opt/Devalaya/DevalayaBilling`.
2.  Create a desktop entry:
    ```bash
    nano ~/.local/share/applications/devalaya.desktop
    ```
3.  Paste this content:
    ```ini
    [Desktop Entry]
    Name=Devalaya Billing System
    Comment=Temple Billing System
    Exec=/opt/Devalaya/DevalayaBilling
    Icon=/opt/Devalaya/static/favicon.ico
    Terminal=true
    Type=Application
    Categories=Office;Utility;
    ```
4.  Make it executable:
    ```bash
    chmod +x ~/.local/share/applications/devalaya.desktop
    ```
5.  Now users can find it in their System Menu.

## Troubleshooting Linux Specifics
*   **Domain (.local)**: Linux resolves `.local` defaults using `Avahi`. It usually works out of the box on Ubuntu/Debian.
*   **Ports**: Port 5000 is standard. If firewall is active (`ufw`), ensure it is allowed:
    ```bash
    sudo ufw allow 5000/tcp
    ```
