#!/usr/bin/env bash
# Bootstraps a fresh Amazon Linux 2023 EC2 instance to run this app via
# docker-compose.prod.yml behind Nginx with a free Let's Encrypt certificate.
#
# Run this AFTER you've SSH'd into the instance and cloned the repo:
#   git clone <this-repo-url> svvd-thorur
#   cd svvd-thorur
#   sudo bash deploy/aws/setup-ec2.sh
#
# It installs Docker, the Docker Compose plugin, Nginx, and Certbot. It does
# NOT start the app or issue a certificate — see DEPLOY_AWS.md for those
# remaining steps (they need your .env secrets and your domain to already
# point at this instance first).

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (sudo bash deploy/aws/setup-ec2.sh)" >&2
  exit 1
fi

echo "==> Updating packages"
dnf update -y

echo "==> Installing Docker"
dnf install -y docker
systemctl enable --now docker
usermod -aG docker "${SUDO_USER:-ec2-user}"

echo "==> Installing Docker Compose plugin"
mkdir -p /usr/local/lib/docker/cli-plugins
COMPOSE_VERSION="v2.29.7"
curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

echo "==> Installing Nginx and Certbot"
dnf install -y nginx augeas-libs
python3 -m venv /opt/certbot
/opt/certbot/bin/pip install --upgrade pip
/opt/certbot/bin/pip install certbot certbot-nginx
ln -sf /opt/certbot/bin/certbot /usr/bin/certbot
systemctl enable --now nginx

echo "==> Done."
echo "Next: log out/in (or 'newgrp docker') so your user can run docker without sudo,"
echo "then follow DEPLOY_AWS.md to configure .env, start the stack, and issue the TLS cert."
