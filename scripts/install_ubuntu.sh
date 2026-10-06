#!/usr/bin/env bash
set -euo pipefail

# Install runtime dependencies for Ubuntu 24.04. Run from the repository root.
# This script does not create PostgreSQL users or modify Nginx/Systemd automatically.

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Please run with sudo: sudo ./scripts/install_ubuntu.sh" >&2
  exit 1
fi

APP_DIR="${APP_DIR:-$(pwd)}"
APP_USER="${SUDO_USER:-$USER}"

apt update
DEBIAN_FRONTEND=noninteractive apt install -y software-properties-common
add-apt-repository -y universe || true
apt update
DEBIAN_FRONTEND=noninteractive apt install -y \
  python3 python3-venv python3-pip python3-dev build-essential libpq-dev \
  libreoffice poppler-utils \
  tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-tra \
  fonts-noto-cjk \
  postgresql postgresql-contrib \
  nginx

if [[ ! -d "$APP_DIR/.venv" ]]; then
  sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"
fi
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip wheel
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

if [[ ! -f "$APP_DIR/.env" ]]; then
  sudo -u "$APP_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "Created $APP_DIR/.env — edit secrets/database settings before production use."
fi

mkdir -p "$APP_DIR/media" "$APP_DIR/staticfiles"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR/media" "$APP_DIR/staticfiles"

echo
echo "Runtime dependencies installed."
echo "Next: edit .env, configure PostgreSQL, then run migrations/collectstatic."
echo "See README.md -> Native Ubuntu 24.04 installation."
