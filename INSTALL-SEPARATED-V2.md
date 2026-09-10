# Stremio + Standalone Web Admin — Initial Setup

This distribution uses the `emmanique/stremio-libtorrent-server-webadmin` fork as its base and runs the Web Admin in an independent container. Rebuilding or updating Stremio will not overwrite the HTML, API, runtime state, or administrative logs.

## Volumes

| Volume | Primary Service | Contents |
|---|---|---|
| `stremio-cache` | Stremio | Cache, pins, certificates, and torrent state |
| `stremio-config` | Web Admin | Configurations edited via the dashboard; read by Stremio |
| `webadmin-data` | Web Admin | Audit logs, update results, and dashboard state |
| `pihole-etc` | Pi-hole | Pi-hole configuration and database |
| `pihole-dnsmasq` | Pi-hole | Additional DNS/DHCP rules |

## Installation

```bash
cp .env.example .env
nano .env
docker compose config
docker compose up -d --build
docker compose ps
```

Endpoints: Web Admin `http://IP:8090`, Player `http://IP:8080`, API `http://IP:11470`, and Pi-hole `http://IP:8053/admin/`.

Changes made under **All Configuration** are saved directly to the `stremio-config` volume. Restart Stremio via the dashboard button to apply them. Do not run `docker compose down -v` during an update.

## Updates via Dashboard

The Web Admin downloads the fork's `main` branch directly, verifies the archive, re-injects only the external configuration adapter, and builds the new Stremio image. If the integration point is missing or broken, the process aborts without altering the active image. After a successful build, deploy the new image using:

```bash
docker compose up -d --force-recreate stremio-libtorrent-server
```

The Web Admin remains active throughout this process.

## Security

The Web Admin has access to the Docker socket to inspect logs, restart Stremio, and build updates. For this reason, port 8090 must remain restricted to LAN/VPN access and never be exposed to the public Internet. Pi-hole is intentionally configured without a password per operator choice and requires the same network restriction.
