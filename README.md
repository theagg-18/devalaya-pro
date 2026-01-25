# Devalaya Billing System

A robust, cross-platform billing and temple management system designed for ease of use and reliability.

## Features
*   **Point of Sale**: Fast and efficient billing interface for temple services.
*   **User Management**: Role-based access control (Admin/Cashier).
*   **Reporting**: Detailed financial reports and dashboards.
*   **Cross-Platform**: Runs on Windows, Linux, and Raspberry Pi.
*   **Offline First**: Works without an internet connection (updates via Zip allowed).
*   **Malayalam Calendar**: Built-in star (Nakshatra) calculation using Skyfield (Offline) with Panchangam utility.

## Quick Start

### Windows
1.  Double-click **`manager.bat`**.
2.  Choose **Option 1 (Install)** to setup the environment and create Desktop shortcuts.
3.  Launch the server using the **"Start Devalaya Server"** shortcut.

### Linux / Raspberry Pi
1.  Open a terminal in the project directory.
2.  Run:
    ```bash
    bash manager.sh
    ```
3.  Choose **Option 1 (Install)**.
4.  Launch from your Application Menu or Desktop.

## System Manager
The included `manager` tool allows you to:
*   **Install/Reinstall**: Setup dependencies and shortcuts.
*   **Update**: Pull changes from Git (Online) or install from `update.zip` (Offline).
*   **Control Server**: Start, Stop, Pause, or Resume the server process.

## Project Structure
*   **`app.py`**: Development server entry point.
*   **`run_prod.py`**: Production server entry point (Waitress/Gunicorn).
*   **`manager.py`**: System management utility.
*   **`migrations/`**: Database schema update scripts.
*   **`maintenance/`**: Diagnostic and fix scripts.
*   **`routes/`**: Application logic and API endpoints.
*   **`templates/` & `static/`**: Frontend assets.

## License
This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.
