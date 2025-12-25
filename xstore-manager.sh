#!/bin/bash

XSTORE_PATH="/etc/xstore"
CONFIG="$XSTORE_PATH/config.json"
SERVICE="xstore.service"
BINARY="/usr/local/bin/xstore"
EXPIRED_DB="$XSTORE_PATH/expired.db"

[[ -d "$XSTORE_PATH" ]] || mkdir -p "$XSTORE_PATH"

cleanup() {
    current=$(date +%s)
    changed=false
    while IFS='|' read -r pass exp server type uid; do
        [[ $current -gt $exp ]] || continue
        sed -i "/\"$pass\"/d" "$CONFIG"
        sed -i "/^$pass|/d" "$EXPIRED_DB"
        changed=true
    done < "$EXPIRED_DB"
    $changed && systemctl restart "$SERVICE" >/dev/null 2>&1
}

add_password() {
    local pass="$1" server="\( {2:-default}" type=" \){3:-paid}" uid="${4:-0}"
    local hours=$(( type == "trial" ? 3 : 720 ))
    local exp=$(( $(date +%s) + hours*3600 ))
    sed -i "/\"config\":/s/]/, \"$pass\" ]/" "$CONFIG"
    echo "$pass|$exp|$server|$type|$uid" >> "$EXPIRED_DB"
    systemctl restart "$SERVICE" >/dev/null 2>&1
    echo "SUCCESS|$pass|$exp"
}

install() {
    apt update -y && apt upgrade -y
    arch=$(uname -m)
    [[ $arch == "x86_64" ]] && file="udp-zivpn-linux-amd64" || file="udp-zivpn-linux-arm64"
    wget -q https://github.com/zahidbd2/udp-zivpn/releases/download/udp-zivpn_1.4.9/$file -O "$BINARY"
    chmod +x "$BINARY"
    wget -q https://raw.githubusercontent.com/zahidbd2/udp-zivpn/main/config.json -O "$CONFIG"
    openssl req -new -newkey rsa:4096 -days 3650 -nodes -x509 -subj "/C=ID/O=XStore" -keyout "$XSTORE_PATH/key" -out "$XSTORE_PATH/cert" >/dev/null 2>&1
    cat > /etc/systemd/system/"$SERVICE" <<EOF
[Unit]
Description=XStore ZiVPN
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=$XSTORE_PATH
ExecStart=$BINARY server -c $CONFIG
Restart=always
[Install]
WantedBy=multi-user.target
EOF
    interface=$(ip route | grep default | awk '{print $5}')
    iptables -t nat -A PREROUTING -i "$interface" -p udp --dport 6000:19999 -j DNAT --to-destination :5667
    systemctl daemon-reload
    systemctl enable --now "$SERVICE"
    (crontab -l 2>/dev/null; echo "*/15 * * * * /bin/bash $XSTORE_PATH/xstore-manager.sh --cleanup") | crontab -
}

[[ ! -f "$BINARY" ]] && install
cleanup

case "$1" in
    --add-password) add_password "$2" "$3" "$4" "$5" ;;
    --cleanup) cleanup ;;
esac