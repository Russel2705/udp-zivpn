#!/bin/bash

CONFIG_DIR="/etc/xstore"
CONFIG_ENV="$CONFIG_DIR/config.env"
SERVERS_FILE="$CONFIG_DIR/servers.txt"
MANAGER="$CONFIG_DIR/xstore-manager.sh"
BOT="$CONFIG_DIR/xstore-bot.py"
QRIS_LINK_VAR="$CONFIG_DIR/qris_link.txt"

green() { echo -e "\e[32m$1\e[0m"; }
yellow() { echo -e "\e[33m$1\e[0m"; }

[[ -f "$CONFIG_ENV" ]] && { yellow "Sudah terinstall."; exit 0; }

mkdir -p $CONFIG_DIR
chmod 700 $CONFIG_DIR

yellow "XStore Installer GoPay QRIS Manual"
read -p "Bot Token Telegram: " bot_token
read -p "Telegram ID Owner (admin): " owner_id
read -p "Link gambar QRIS GoPay (upload ke Telegram/Imgur): " qris_link

cat > $CONFIG_ENV <<EOF
BOT_TOKEN="$bot_token"
OWNER_ID="$owner_id"
EOF
echo "$qris_link" > $QRIS_LINK_VAR
chmod 600 $CONFIG_ENV $QRIS_LINK_VAR

> $SERVERS_FILE
while true; do
    read -p "Key server (kosong selesai): " key
    [[ -z "$key" ]] && break
    read -p "Nama server: " name
    read -p "IP server: " ip
    read -p "Harga premium 30 hari (Rp): " price
    echo "$key|$name|$ip|$price" >> $SERVERS_FILE
done

wget -O $MANAGER https://raw.githubusercontent.com/Russel2705/udp-zivpn/main/xstore-manager.sh
wget -O $BOT https://raw.githubusercontent.com/Russel2705/udp-zivpn/main/xstore-bot.py
chmod +x $MANAGER

bash $MANAGER

green "Install selesai. pip install python-telegram-bot python-dotenv"
green "Jalankan bot: python $BOT"
