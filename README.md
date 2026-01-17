# Devalaya Pro

A robust, offline-first billing system designed for Raspberry Pi servers in temple counters. Built with Flask, SQLite, and vanilla HTML/CSS.

## Features

- **Offline-First**: Works entirely without internet.
- **Role-Based Access**: Admin and Cashier roles.
- **Multi-Mode Billing**:
  - **Vazhipadu**: Devotee Name, Star, Multiple Vazhipadu.
  - **Donation**: Quick Item + Amount billing.
- **Batch Printing**: Group multiple devotees into a single print job.
- **Printer Management**: Smart CUPS integration with online status checks.
- **Reports**: Daily revenue and cashier performance.
- **Backup**: One-click local database backup.

## Requirements

- Raspberry Pi 4 (Recommended) or any Linux/Windows PC.
- Python 3.9+
- Thermal Printer (ESC/POS compatible via USB).
- USB SSD (Recommended for Database storage on RPi).

## Setup Guide

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/devalaya-pro.git
cd devalaya-pro

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file:
```bash
cp .env.example .env
```
Edit `.env` to point `DB_PATH` to your USB SSD mount point (e.g., `/mnt/usb_ssd/temple.db`).

### 3. Running the Server

```bash
python app.py
```
Access the application at `http://localhost:5000`.

### 4. Initial Login

- **Admin**: `admin` / `1234`
- **Cashier**: Create a cashier in Admin -> Users first.

## Raspberry Pi Production Setup

To run as a service on boot:

1. Create a systemd service file `/etc/systemd/system/temple.service`:
   ```ini
   [Unit]
   Description=Devalaya Pro Server
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/devalaya-pro
   ExecStart=/usr/bin/python3 app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
2. Enable and start:
   ```bash
   sudo systemctl enable temple
   sudo systemctl start temple
   ```

## Printer Setup (CUPS)

Ensure CUPS is installed:
```bash
sudo apt install cups
sudo usermod -aG lpadmin pi
```
Add printers via `http://localhost:631` or use the Admin -> Printer settings page to discover connected printers (requires `lpstat`).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the [GNU General Public License v3 (GPLv3)](LICENSE).
