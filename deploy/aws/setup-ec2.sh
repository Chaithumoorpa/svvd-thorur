#!/usr/bin/env bash
# Bootstraps an EC2 instance (Amazon Linux 2023 or Ubuntu) to run this app via
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

. /etc/os-release
echo "==> Detected OS: $PRETTY_NAME"

case "$ID" in
  amzn)
    LOGIN_USER="${SUDO_USER:-ec2-user}"

    echo "==> Updating packages"
    dnf update -y

    echo "==> Installing Docker"
    dnf install -y docker
    systemctl enable --now docker

    echo "==> Installing Nginx and Certbot"
    dnf install -y nginx augeas-libs
    python3 -m venv /opt/certbot
    /opt/certbot/bin/pip install --upgrade pip
    /opt/certbot/bin/pip install certbot certbot-nginx
    ln -sf /opt/certbot/bin/certbot /usr/bin/certbot
    systemctl enable --now nginx

    echo "==> Installing Docker Compose plugin"
    mkdir -p /usr/local/lib/docker/cli-plugins
    COMPOSE_VERSION="v2.29.7"
    curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    ;;

  ubuntu|debian)
    LOGIN_USER="${SUDO_USER:-ubuntu}"

    echo "==> Updating packages"
    apt-get update -y

    echo "==> Installing Docker (official repo, includes the compose plugin)"
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL "https://download.docker.com/linux/${ID}/gpg" -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" \
      > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker

    echo "==> Installing Nginx"
    apt-get install -y nginx
    systemctl enable --now nginx

    echo "==> Installing Certbot (snap, per Certbot's own recommendation on Ubuntu/Debian)"
    snap install core 2>/dev/null || true
    snap refresh core 2>/dev/null || true
    snap install --classic certbot
    ln -sf /snap/bin/certbot /usr/bin/certbot
    ;;

  *)
    echo "Unrecognized OS '$ID' - this script only handles Amazon Linux and Ubuntu/Debian." >&2
    exit 1
    ;;
esac

usermod -aG docker "$LOGIN_USER"

echo "==> Done."
echo "Next: log out/in (or 'newgrp docker') so your user can run docker without sudo,"
echo "then follow DEPLOY_AWS.md to configure .env, start the stack, and issue the TLS cert."
