#!/bin/bash
# Devalaya Pro — Oracle Cloud Free ARM setup
# Run as: bash setup_oracle.sh
set -e

echo "======================================"
echo "  Devalaya Pro — Oracle ARM Setup"
echo "======================================"

# 1. System update
echo "[1/5] Updating system..."
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
echo "[2/5] Installing Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"

# 3. Firewall — Oracle blocks ports via iptables by default.
#    Port 5000 stays closed to internet (cloudflared handles that).
#    Only SSH (22) needs to be open externally.
echo "[3/5] Checking firewall..."
sudo iptables -L INPUT --line-numbers | grep -E '22|ACCEPT' | head -5

# 4. Upload app or clone
echo "[4/5] Ready for app files."
echo "  Option A — git clone:"
echo "    git clone https://github.com/theagg-18/devalaya-pro.git app"
echo "    cd app"
echo ""
echo "  Option B — scp from your machine:"
echo "    scp -r /path/to/app ubuntu@<your-ip>:~/app"
echo "    cd ~/app"
echo ""

# 5. .env setup instructions
echo "[5/5] Create your .env file:"
echo ""
echo "  cp .env.example .env"
echo "  nano .env"
echo ""
echo "  Set these two values:"
echo "    SECRET_KEY=<run: python3 -c \"import secrets; print(secrets.token_hex(32))\">"
echo "    CLOUDFLARE_TUNNEL_TOKEN=<from Cloudflare dashboard>"
echo ""
echo "======================================"
echo "  After filling .env, run:"
echo "    docker compose up -d"
echo "    docker compose logs -f"
echo "======================================"
echo ""
echo "NOTE: Log out and back in (or run 'newgrp docker') before using Docker."
