#!/bin/bash
# VPS Setup Script for Auto_Encodes Bot
# Run this on a fresh Ubuntu 22.04 VPS as root or with sudo

set -e

echo "=============================="
echo " Auto_Encodes VPS Setup Script"
echo "=============================="

# 1. Update system
echo "[1/5] Updating system..."
apt-get update -qq && apt-get upgrade -y -qq

# 2. Install Docker
echo "[2/5] Installing Docker..."
apt-get install -y -qq ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 3. Create downloads directory
echo "[3/5] Creating downloads directory..."
mkdir -p downloads

# 4. Set up .env file
echo "[4/5] Setting up environment variables..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  Please fill in your .env file before continuing!"
  echo "    Edit it with: nano .env"
  echo ""
  read -p "Press Enter once you've filled in .env to continue..."
fi

# 5. Build and start bot
echo "[5/5] Building and starting bot..."
docker compose up -d --build

echo ""
echo "✅ Bot is running! Use these commands to manage it:"
echo "   View logs:   docker compose logs -f"
echo "   Stop bot:    docker compose down"
echo "   Restart bot: docker compose restart"
