#!/usr/bin/env bash
set -e

# 安裝系統更新與必要套件
sudo apt update
sudo apt upgrade -y

sudo apt install -y \
    apache2 \
    php \
    libapache2-mod-php \
    python3 \
    python3-pip \
    python3-venv \
    default-libmysqlclient-dev \
    libssl-dev libffi-dev \
    libsasl2-dev libldap2-dev \
    imagemagick \
    libreoffice \
    openjdk-8-jdk

# 啟用 Apache + PHP
sudo a2enmod php
sudo systemctl restart apache2

# （可選）建立 Python 虛擬環境
python3 -m venv venv
source venv/bin/activate

# 更新 pip／setuptools／wheel
pip install --upgrade pip setuptools wheel pillow

# 安裝 Python 依賴 — 根據你的需求選擇是否要 superset
# 這裡只是示範: 若你要用 superset，解開下面兩行
# pip install apache-superset --break-system-packages
# pip install marshmallow==3.20.1 --break-system-packages

# 若要使用 superset，可啟用以下區塊：
# export SUPERSET_SECRET_KEY="請你自己設定 secret"
# export FLASK_APP=superset
# superset db upgrade
# superset fab create-admin
# superset load-examples
# superset init
# superset run -h 0.0.0.0 -p 8088

# 安裝其他 Python 套件（如果 ix3-TMT 後端有 requirements.txt，可改成 pip install -r requirements.txt）
# 例如：
# pip install <必要的第三方套件>

# 將 repo clone 到本地
git clone https://github.com/linjose/ix3-TMT.git
cd ix3-TMT

# 若有資料庫需求（PostgreSQL / MySQL / MariaDB / sqlite / 其他）——
# 需要先設定好資料庫，再調整 config

# 設定檔 / 權限調整（依照專案需求）
# 例如：
# chmod -R 755 .

echo "ix3-TMT 安裝完成／基本環境已建立。請依 README 或文件進行後續設定。"
