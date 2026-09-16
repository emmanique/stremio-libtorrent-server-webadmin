#!/bin/sh
set -eu

CONFIG_DIR="${STREMIO_VPN_CONFIG_DIR:-/vpn}"

read_setting() {
    file="$1"
    fallback="${2:-}"
    if [ -f "$CONFIG_DIR/$file" ]; then
        sed -n '1p' "$CONFIG_DIR/$file" | tr -d '\r'
    else
        printf '%s' "$fallback"
    fi
}

VPN_SERVICE_PROVIDER="$(read_setting provider.txt "${VPN_SERVICE_PROVIDER:-cyberghost}")"
VPN_TYPE="openvpn"
OPENVPN_PROTOCOL="$(read_setting protocol.txt "${OPENVPN_PROTOCOL:-udp}")"
SERVER_COUNTRIES="$(read_setting country.txt "${SERVER_COUNTRIES:-}")"
SERVER_HOSTNAMES="$(read_setting hostname.txt "${SERVER_HOSTNAMES:-}")"
FIREWALL_OUTBOUND_SUBNETS="$(read_setting firewall_outbound_subnets.txt "${FIREWALL_OUTBOUND_SUBNETS:-192.168.0.0/16,10.0.0.0/8,172.30.0.0/24}")"

if [ "$VPN_SERVICE_PROVIDER" != "cyberghost" ]; then
    echo "[vpn] unsupported provider in this release: $VPN_SERVICE_PROVIDER" >&2
    exit 64
fi

case "$OPENVPN_PROTOCOL" in
    udp|tcp) ;;
    *)
        echo "[vpn] OPENVPN protocol must be udp or tcp" >&2
        exit 64
        ;;
esac

export VPN_SERVICE_PROVIDER VPN_TYPE OPENVPN_PROTOCOL
export SERVER_COUNTRIES SERVER_HOSTNAMES FIREWALL_OUTBOUND_SUBNETS

[ -f "$CONFIG_DIR/openvpn_user" ] && export OPENVPN_USER_SECRETFILE="$CONFIG_DIR/openvpn_user"
[ -f "$CONFIG_DIR/openvpn_password" ] && export OPENVPN_PASSWORD_SECRETFILE="$CONFIG_DIR/openvpn_password"
[ -f "$CONFIG_DIR/client.crt" ] && export OPENVPN_CLIENTCRT_SECRETFILE="$CONFIG_DIR/client.crt"
[ -f "$CONFIG_DIR/client.key" ] && export OPENVPN_CLIENTKEY_SECRETFILE="$CONFIG_DIR/client.key"

exec /gluetun-entrypoint "$@"
