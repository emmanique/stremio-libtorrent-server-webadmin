# 🎬 Stremio Libtorrent Server + WebAdmin

[![Latest release](https://img.shields.io/github/v/release/emmanique/stremio-libtorrent-server-webadmin?display_name=tag&sort=semver)](https://github.com/emmanique/stremio-libtorrent-server-webadmin/releases/latest)
[![Fork integration guard](https://github.com/emmanique/stremio-libtorrent-server-webadmin/actions/workflows/fork-guard.yml/badge.svg?branch=main)](https://github.com/emmanique/stremio-libtorrent-server-webadmin/actions/workflows/fork-guard.yml)
[![Library addon guard](https://github.com/emmanique/stremio-libtorrent-server-webadmin/actions/workflows/library-addon-guard.yml/badge.svg?branch=main)](https://github.com/emmanique/stremio-libtorrent-server-webadmin/actions/workflows/library-addon-guard.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-3DA639.svg)](LICENSE)

A self-hosted **Stremio streaming platform** built around an open `libtorrent` streaming server and extended with a dedicated **WebAdmin**, **Library / Cache UI**, **Stremio Library Addon**, **Pi-hole integration**, hardware-aware transcoding, safe package updates and automated release validation.

The normal installation is now **package-only**: Docker Compose pulls published images from GHCR instead of building the Server or WebAdmin locally.

> This repository does **not** bundle movies, series, torrent indexes or third-party content addons. It provides the streaming, cache, administration and integration infrastructure. What you stream depends on the sources/addons you configure in Stremio.

---

## What this fork adds

This project started from [`andrewhack/stremio-libtorrent-server`](https://github.com/andrewhack/stremio-libtorrent-server) and keeps the open streaming engine while adding a complete operational layer around it.

| Area | Added in this fork |
| --- | --- |
| **Deployment** | Full Docker Compose stack with Server, WebAdmin and Pi-hole; application images published in GHCR; no local build required for normal installation. |
| **WebAdmin** | Browser administration UI on port `8090` with connection URLs, QR code, health, CPU/RAM/network/torrent metrics, cache usage, stream management and runtime controls. |
| **Configuration** | Searchable **All configuration** page with grouped parameters, checkboxes, descriptions, persisted values and controlled server restart. |
| **Cache management** | View active/downloading/inactive cached items, capacity/free-space bar, pin/unpin, remove sessions and delete cached content. |
| **Logs** | Logs separated by source, normal/debug mode, refresh, clean selected source or clean all. |
| **Library UI** | Stremio-style poster shelves for downloaded/downloading content, add-by-magnet, continue watching, disk-budget awareness, keep/delete controls and series/episode detail. |
| **Library Addon** | Server-generated Stremio addon exposing cached titles as `My Library`, local stream sources and metadata/subtitle identity learning. |
| **Metadata** | Automatic high-confidence recognition of release names, Cinemeta lookup and MetaHub poster fallback for older/unlabelled cache entries. |
| **Addon management** | WebAdmin discovers server addons, exposes the manifest URL, management link, update status and Library title-management entry point. |
| **Updates** | Server update through immutable GHCR package, image-version validation, health check and automatic rollback. WebAdmin has its own independent package lifecycle. |
| **Networking** | Automatic host IPv4 detection through `start.sh`; trusted Stremio HTTPS endpoint; optional Pi-hole LAN DNS; optional VPN runtime through Gluetun. |
| **Transcoding** | Fork-owned FFmpeg policy, copy-first/direct-play controls, VAAPI support, NVIDIA/NVENC overlay and CPU fallback. |
| **Release safety** | Permanent `future` branch, full validation before promotion, fork/library guards, automated release packaging and anonymous GHCR pull verification. |

---

## Architecture

```text
                         Stremio clients
                    TV · Desktop · Browser
                              │
                 HTTP / trusted HTTPS / addon
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                  stremio-libtorrent-server                   │
│                                                              │
│  Web Player :8080        Streaming API :11470                │
│  HTTPS      :12470       Library UI     /library/            │
│                                                              │
│  libtorrent · cache · Range streaming · FFmpeg · addon       │
└──────────────────────────────┬───────────────────────────────┘
                               │
             ┌─────────────────┴──────────────────┐
             │                                    │
             ▼                                    ▼
┌───────────────────────────┐        ┌───────────────────────────┐
│         WebAdmin          │        │          Pi-hole          │
│           :8090           │        │        Web UI :8053       │
│                           │        │                           │
│ status · config · cache   │        │ DNS for internal stack    │
│ logs · updates · addons   │        │ optional LAN port 53      │
└───────────────────────────┘        └───────────────────────────┘
```

The default internal Docker network is `172.30.0.0/24`, with Pi-hole available to the Stremio service at `172.30.0.53`.

---

## Published images

The normal stack uses:

```text
ghcr.io/emmanique/stremio-libtorrent-server-webadmin:latest
ghcr.io/emmanique/stremio-libtorrent-server-webadmin-webadmin:latest
pihole/pihole:latest
```

The Server and WebAdmin packages are independently versioned. The authoritative version files are:

```text
SERVER_VERSION
FORK_VERSION                 # compatibility alias of SERVER_VERSION
webadmin/WEBADMIN_VERSION
pyproject.toml               # core stremiosrv package version
```

See [`VERSIONING.md`](VERSIONING.md) for the lifecycle rules.

---

# 🚀 Quick start

## Recommended managed installation

Requirements:

- Linux host
- Docker Engine
- Docker Compose v2
- LAN access to the host

Clone the repository:

```bash
git clone https://github.com/emmanique/stremio-libtorrent-server-webadmin.git
cd stremio-libtorrent-server-webadmin
```

Start everything:

```bash
sh start.sh
```

`start.sh` automatically detects the host IPv4 address and then performs the equivalent of:

```bash
docker compose pull
docker compose up -d
```

There is **no normal local application build**.

To force a specific LAN IP for one run:

```bash
IPADDRESS=192.168.1.244 sh start.sh
```

> Do not use `docker compose down -v` during a normal update. `-v` deletes persistent Docker volumes, including cache and configuration data.

---

## Minimal one-file installation

If you only want the published stack and do not need the launcher/overrides locally:

```bash
mkdir -p stremio-platform
cd stremio-platform

curl -fsSLO \
  https://raw.githubusercontent.com/emmanique/stremio-libtorrent-server-webadmin/main/compose.yaml

docker compose pull
docker compose up -d
```

For this mode, define `IPADDRESS` explicitly if you want ports and trusted-certificate generation tied to one LAN address:

```bash
IPADDRESS=192.168.1.244 docker compose up -d
```

---

## Access points

If the server address is `192.168.1.244`:

| Service | Address |
| --- | --- |
| **Web Player** | `http://192.168.1.244:8080` |
| **WebAdmin** | `http://192.168.1.244:8090` |
| **Streaming API** | `http://192.168.1.244:11470` |
| **HTTPS / Stremio endpoint** | `https://<trusted-stremio-host>:12470` |
| **Library UI** | `https://<trusted-stremio-host>:12470/library/` |
| **Pi-hole Admin** | `http://192.168.1.244:8053/admin/` |
| **BitTorrent** | `6881/tcp` + `6881/udp` by default |

When a specific `IPADDRESS` is used, Compose binds the published ports to that LAN address. In that case, `127.0.0.1:<published-port>` on the Docker host is not expected to answer; use the configured LAN IP or test inside the container.

For a more detailed installation walkthrough, see [`QUICKSTART.md`](QUICKSTART.md).

---

# 🖥️ WebAdmin

Open:

```text
http://SERVER_IP:8090
```

The WebAdmin is designed to manage the fork without editing files for routine operations.

## Dashboard

The main dashboard includes:

- detected server IP;
- Web Player URL;
- trusted TV/app streaming URL;
- Stremio Desktop launch flag;
- QR code for connection information;
- Server running/health state;
- certificate status;
- uptime, CPU and memory;
- rolling CPU/memory performance chart;
- network traffic;
- torrent/peer activity;
- cache used/capacity/free space;
- active, downloading and cached content;
- individual pin/unpin/remove/delete actions;
- seeding controls;
- concurrent-stream limit;
- download and upload bandwidth limits;
- Pi-hole Admin shortcut;
- component versions and update state.

## All configuration

The **All configuration** tab exposes the server parameters in searchable functional groups.

It supports:

- boolean values as checkboxes;
- text and numeric settings;
- parameter descriptions;
- locked/read-only values for reference;
- restart-required indicators;
- persistent configuration in `admin-settings.json`;
- controlled server restart from the UI.

WebAdmin-saved values take precedence over the corresponding environment defaults where supported.

## Logs

The Logs tab keeps operational output separated by origin, including application, Nginx, Docker/container, update and administrative events.

Available controls include:

- normal/debug logging mode;
- refresh;
- last lines by source;
- clear selected source;
- clear all log sources.

## Security note

WebAdmin has access to `/var/run/docker.sock` so it can manage the Stremio container and perform transactional updates. Treat port `8090` as an **administrative interface** and keep it restricted to a trusted LAN/VPN.

---

# 📚 Library / Cache

The Library UI is enabled by default in this fork:

```env
STREMIOSRV_LIBRARY_UI=true
```

Open the Library URL printed by `start.sh`, normally under the trusted HTTPS endpoint:

```text
https://<trusted-stremio-host>:12470/library/
```

## Library capabilities

The page can:

- reuse the Stremio profile/authentication available on the same origin;
- accept a magnet link and start a download;
- show downloading content with progress;
- show downloaded movies/series using poster cards;
- show **Continue watching** information;
- expose files still occupying disk even when metadata was not recognised;
- display cache capacity and free disk space;
- protect selected items from normal cache eviction;
- delete cached content;
- navigate series → season → episode → release details;
- show actual files present on disk for packs;
- warn when a new download risks exceeding the configured cache budget.

The cache is persistent in the `stremio-cache` Docker volume unless intentionally removed.

---

# 🧩 Library Addon for Stremio

When the Library is enabled, the server also exposes a Stremio addon.

From the Library page, use **Watch this library in Stremio**, or use the addon selector in WebAdmin under **How to Connect**.

The generated manifest can provide:

- `My Library` catalog;
- local stream sources for recognised content already present on the server;
- movie/series metadata;
- playback identity learning used to associate cached torrents with Stremio/IMDb IDs;
- poster/title enrichment for old cache entries that were created before learning data existed.

The addon URL includes a per-install secret token and is additionally protected by a private-network/CIDR guard. By default, the built-in private address ranges are used when `STREMIOSRV_LIBRARY_ADDON_ALLOW` is empty.

Treat the generated addon URL as a secret and do not publish it in logs, screenshots or public issues.

## Metadata recognition

For older/unlabelled cache content, the fork contains a conservative release-name recogniser. It can identify high-confidence movie/series names and episode markers, query Cinemeta and use MetaHub artwork fallback when appropriate.

Authoritative playback-learned labels remain the source of truth. Automatic recognition is used for presentation and is intentionally conservative when the title is ambiguous.

---

# 🎞️ Streaming and transcoding

The underlying server remains a real `libtorrent` client, not only an HTTP proxy. It can download files, maintain cache state and seed content according to the configured policy.

The fork adds a configurable FFmpeg policy with direct-play/copy preferences and hardware acceleration controls.

Default Compose parameters include:

```env
TRANSCODING_MODE=auto
TRANSCODING_HWACCEL=vaapi
TRANSCODING_VIDEO_CODEC=h264_vaapi
TRANSCODING_AUDIO_CODEC=aac
TRANSCODING_COPY_VIDEO=true
TRANSCODING_COPY_AUDIO=true
TRANSCODING_FALLBACK_CODEC=libx264
TRANSCODING_HW_DECODE=true
```

## VAAPI

On a Linux host exposing `/dev/dri`:

```bash
docker compose \
  -f compose.yaml \
  -f compose.vaapi.yaml \
  up -d
```

## NVIDIA / NVENC

On a host with the NVIDIA Container Toolkit and working NVIDIA runtime:

```bash
docker compose \
  -f compose.yaml \
  -f compose.gpu.yaml \
  up -d
```

The base stack does not require a GPU and retains software fallback.

---

# 🔒 Trusted HTTPS for Stremio clients

When `IPADDRESS` is available, the streaming runtime can obtain/use the trusted Stremio `*.stremio.rocks` endpoint expected by TV/client environments that reject self-signed certificates.

`start.sh` automatically detects the host IPv4 address from the Linux routing table, exports it to Compose and prints the main connection URLs.

If DHCP changes the host address, run again:

```bash
sh start.sh
```

The launcher will detect the current address instead of requiring the tracked `.env` file to be edited.

---

# 🛡️ Pi-hole integration

Pi-hole is part of the default stack.

By default:

- its Web UI is published on host port `8053`;
- DNS port `53` is available inside the Docker network for the Stremio runtime;
- host/LAN DNS port `53` is **not** published, avoiding conflicts with `systemd-resolved` or another local resolver.

To expose Pi-hole as DNS for the LAN:

```bash
docker compose \
  -f compose.yaml \
  -f compose.dns.yaml \
  up -d
```

Make sure TCP/UDP port `53` is free on the selected host address first.

You can bind DNS to a dedicated address with:

```env
PIHOLE_DNS_BIND_IP=192.168.1.244
PIHOLE_DNS_PORT=53
```

For real environments, set `PIHOLE_PASSWORD` and keep the management interface restricted to your trusted network.

---

# 🌐 VPN mode

`compose.vpn.yaml` provides a runtime-only VPN mode using Gluetun.

The Stremio runtime shares Gluetun's network namespace, so Internet/BitTorrent traffic follows the VPN kill-switch while selected LAN access can remain available.

Example:

```bash
WIREGUARD_PRIVATE_KEY='...' \
WIREGUARD_ADDRESSES='10.2.0.2/32' \
IPADDRESS='192.168.1.244' \
docker compose -f compose.vpn.yaml up -d
```

Important variables include:

```env
VPN_SERVICE_PROVIDER=protonvpn
VPN_TYPE=wireguard
VPN_PORT_FORWARDING=on
FIREWALL_OUTBOUND_SUBNETS=192.168.0.0/16,10.0.0.0/8
```

Inbound peers while using a VPN require a provider/configuration that supports port forwarding.

---

# 🔄 Updates

## Full stack

The normal package refresh is:

```bash
sh start.sh
```

or manually:

```bash
docker compose pull
docker compose up -d
```

Persistent volumes are kept.

## Server update from WebAdmin

The Server update lifecycle is package-based:

1. determine the available fork release;
2. pull the immutable GHCR Server tag;
3. validate the package/image version;
4. preserve the current image as rollback candidate;
5. replace only the streaming-server container;
6. wait for `/health`;
7. automatically restore the previous container if activation fails.

This avoids the older `git pull + local Docker build` path for normal Server updates.

## WebAdmin update

WebAdmin is an independent package:

```bash
docker compose pull webadmin
docker compose up -d --no-deps webadmin
```

Updating WebAdmin does not require rebuilding or recreating the streaming server.

---

# ⚙️ Important environment variables

The tracked `.env` contains operational defaults and intentionally leaves host-specific values blank.

| Variable | Purpose |
| --- | --- |
| `IPADDRESS` | Host LAN IPv4; normally detected by `start.sh`. |
| `SERVER_URL` | Optional explicit Stremio/HTTPS server URL. |
| `STREMIO_IMAGE` | Override/pin the Server GHCR image. |
| `WEBADMIN_IMAGE` | Override/pin the WebAdmin GHCR image. |
| `STREMIO_DATA_DIR` | Cache/state Docker volume name. |
| `STREMIOSRV_BT_LISTEN_PORT` | BitTorrent TCP/UDP listen port; default `6881`. |
| `STREMIOSRV_LIBRARY_UI` | Enable Library UI and addon integration. |
| `STREMIOSRV_LIBRARY_ALLOW_HTTP` | Allow Library addon HTTP mode when explicitly required. |
| `STREMIOSRV_LIBRARY_OWNER` | Optional Library owner restriction. |
| `STREMIOSRV_LIBRARY_ADDON_ALLOW` | CIDR/network allowlist for the addon. |
| `STREMIO_UPDATE_HEALTH_TIMEOUT` | Health validation timeout during transactional Server update. |
| `PIHOLE_WEB_PORT` | Pi-hole Web UI host port; default `8053`. |
| `PIHOLE_DNS_PORT` | Optional LAN DNS host port; default `53`. |
| `PIHOLE_PASSWORD` | Pi-hole administrator password. |
| `TRANSCODING_*` | Fork-owned transcoding/direct-play/FFmpeg policy. |

More server parameters are available through **WebAdmin → All configuration**.

Do not commit passwords, tokens, private keys or certificates to `.env`.

---

# 🩺 Health and troubleshooting

Show the resolved Compose configuration and detected address:

```bash
sh start.sh config
```

Check containers:

```bash
sh start.sh ps
```

Server health from the LAN address:

```bash
curl -fsS http://SERVER_IP:11470/health
```

Server health directly inside the container:

```bash
docker exec stremio-libtorrent-server \
  curl -fsS http://127.0.0.1:11470/health
```

Runtime statistics:

```bash
curl -fsS http://SERVER_IP:11470/stats.json | python3 -m json.tool
```

Logs:

```bash
docker compose logs --tail=200 stremio-libtorrent-server
docker compose logs --tail=200 webadmin
docker compose logs --tail=200 pihole
```

For Library-learning diagnostics, the playback metrics include counters such as:

```text
librarySubtitlesAsks
librarySubtitlesReports
libraryLabelsLearned
```

---

# 🧪 Development and release model

This fork deliberately separates development from stable releases.

```text
future
   │
   ▼
Future full validation
   │
   ├─ functional tests
   ├─ Python / shell validation
   ├─ Compose validation
   ├─ package-only stack validation
   ├─ WebAdmin package build
   └─ release identifier validation
   │
   ▼
main
   │
   ├─ Fork Integration Guard
   ├─ Library Addon Guard
   └─ Public Package Pull Check
   │
   ▼
version/tag release
   │
   ├─ build Server image
   ├─ build WebAdmin image
   ├─ smoke-test both
   ├─ publish GHCR packages
   └─ create/update GitHub Release
```

Fork-owned paths are protected from automatic upstream replacement. Upstream changes can still be reviewed and deliberately integrated without silently overwriting WebAdmin, Compose, versioning, update or Library-specific functionality.

---

# 📁 Main repository components

```text
compose.yaml                     Full Server + WebAdmin + Pi-hole stack
compose.dns.yaml                 Optional Pi-hole LAN DNS publication
compose.vaapi.yaml               VAAPI device overlay
compose.gpu.yaml                 NVIDIA/NVENC runtime overlay
compose.vpn.yaml                 Gluetun VPN runtime mode
start.sh                         Host-IP detection + pull + compose launcher

src/stremiosrv/                  Streaming server/core integration
src/stremiosrv/library/          Library UI, addon, labels and metadata

webadmin/                        Independent WebAdmin service
webadmin/static/                 Dashboard/config/log/addon UI

.github/workflows/               Validation, release and package checks
QUICKSTART.md                    Detailed deployment guide
VERSIONING.md                    Independent component version policy
docs/releases/                   Release-specific notes
```

---

# 🔐 Security considerations

- Keep WebAdmin (`8090`) on a trusted LAN/VPN because it can control Docker through the mounted Docker socket.
- Keep Pi-hole Admin (`8053`) restricted and configure an admin password.
- Do not publish Library addon manifest URLs: they contain the per-install access token.
- Keep the Library addon CIDR allowlist limited to networks that should reach it.
- Do not expose the raw Streaming API (`11470`) to the public Internet unless you understand and secure the surrounding network architecture.
- Store secrets outside version control.

---

# 📖 Credits

The streaming engine originates from:

- [`andrewhack/stremio-libtorrent-server`](https://github.com/andrewhack/stremio-libtorrent-server)

This fork adds the WebAdmin/platform integration, Library/Addon extensions, deployment/update lifecycle, Pi-hole integration and the operational/release controls described above.

WebAdmin branding: **Velha Guarda de Almada**.

Thanks to the Stremio, libtorrent, FFmpeg, Pi-hole, Docker and open-source communities whose projects make this stack possible.

---

# 📄 License

MIT — see [`LICENSE`](LICENSE).

Use the software responsibly and in accordance with the laws and content rights applicable in your jurisdiction.
