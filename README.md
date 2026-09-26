# Stremio Server WebAdmin 2.0.18

[![Fast CI](https://github.com/emmanique/stremio-libtorrent-server-webadmin/actions/workflows/ci-fast.yml/badge.svg?branch=main)](https://github.com/emmanique/stremio-libtorrent-server-webadmin/actions/workflows/ci-fast.yml)
[![Full regression](https://github.com/emmanique/stremio-libtorrent-server-webadmin/actions/workflows/regression.yml/badge.svg?branch=main)](https://github.com/emmanique/stremio-libtorrent-server-webadmin/actions/workflows/regression.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-3DA639.svg)](LICENSE)

Self-hosted Stremio streaming platform with an open libtorrent server, WebAdmin, Pi-hole, hardware transcoding support and optional CyberGhost/OpenVPN routing through Gluetun.

Version **2.0.18** keeps upstream server/core **1.6.15** and introduces the maintenance/deployment refactor: a clean production package, generic first-install configuration, explicit backup/upgrade procedures, reusable branch governance and separated Fast CI / Dependencies / Full regression / Release gates.

> This repository does not bundle movies, series, torrent indexes or third-party content addons.

---

## 2.0.18 at a glance

- **Clean deployment package:** production releases now contain only Compose/launcher/configuration/backup/documentation files; source, tests and CI tooling stay in the repository.
- **Generic first-install baseline:** no fixed LAN IP, personal allowlist, Angola-only timezone or mandatory VAAPI device is assumed.
- **Safe launcher configuration:** `start.sh` reads literal values from the local `.env` without sourcing it and preserves environment-variable precedence.
- **Upgrade protection:** `scripts/backup-before-upgrade.sh` captures `.env`, resolved Compose/image state and persistent configuration volumes before an upgrade.
- **Branch simplification:** only `main` and `development` are permanent; feature/fix/release/hotfix branches are temporary.
- **Separated CI:** Fast CI covers deterministic merge gates, Dependencies isolates dependency changes, Full regression executes integration/build/smoke/deployment-package tests, and Release publishes only after those contracts pass.
- **Self-contained GitHub workflows:** new workflows use runner-native `git`, `docker`, `uv` and `gh` commands instead of external composite Actions, avoiding the repository's zero-job `startup_failure` behaviour.
- **Current versions:** upstream server/core **1.6.15**; fork/WebAdmin/VPN **2.0.18**.

## Installation and upgrade model

Production hosts should use the **deployment ZIP/TAR attached to a GitHub Release**, not a full source checkout. The deployment package contains only the supported runtime surface: Compose files, launchers, `.env.example`, backup tooling and operational documentation. Source code, tests, GitHub Actions and development tooling remain in the repository only.

### New installation

1. Install Docker Engine with the Docker Compose plugin.
2. Download the deployment package for the desired release and extract it into a dedicated directory such as `/opt/stremio-webadmin`.
3. Create the local configuration once:

```bash
cp .env.example .env
```

4. Review at minimum these values before first start:
   - `TZ`;
   - `PIHOLE_PASSWORD`;
   - `VPN_LAN_CIDRS` when the LAN is not in `192.168.0.0/16`;
   - `IPADDRESS_SOURCE` / `IPADDRESS` on multi-homed or statically bound hosts;
   - optional image pins when a fixed release is preferred over `:latest`;
   - optional GPU overrides only after the local VAAPI/NVIDIA path is validated.
5. Validate the resolved topology before starting:

```bash
sh start.sh config
```

6. Start the platform:

```bash
sh start.sh
```

The default baseline is hardware-neutral and CPU-safe. `start.sh` detects a usable VAAPI/NVIDIA runtime and only adds the corresponding overlay when the host supports it.

### Upgrade

The local `.env` and Docker volumes are **installation state** and must not be replaced by a release package. Before every upgrade:

```bash
sh scripts/backup-before-upgrade.sh
```

Use `--with-cache` only when the large cache volume must also be archived:

```bash
sh scripts/backup-before-upgrade.sh --with-cache
```

Then extract the new deployment package over the installation directory while preserving the existing `.env`. Compare configuration changes:

```bash
diff -u .env .env.example || true
```

Reconcile any newly introduced variables manually, validate the new Compose model, then start:

```bash
sh start.sh config
sh start.sh
```

Do **not** use `docker compose down -v` for a routine upgrade. It deletes persistent volumes. The backup script preserves configuration/state volumes and records the resolved Compose/image state so an upgrade can be rolled back deliberately.

### Development and releases

Only `main` and `development` are long-lived branches. Feature/fix/release/hotfix branches are temporary. Normal development merges into `development`; a release branch is cut from `development`, validated by **Full regression**, merged into `main`, tagged and published. See `docs/BRANCHING.md` and `docs/TESTING.md`.

## 2.0.17 at a glance

- **GPU backend selection:** `GPU_BACKEND=auto` detects the usable runtime backend and prefers Intel/DRM VAAPI when a valid render node is present.
- **Render-node discovery:** Intel VAAPI is no longer tied to `/dev/dri/renderD128`; `start.sh` can discover the actual Intel render node on the host and expose the matching overlay.
- **Runtime verification:** WebAdmin performs real FFmpeg self-tests before marking VAAPI/NVENC profiles selectable. Compiled encoder names alone are not treated as proof that a hardware path works.
- **NVIDIA capability gating:** an NVIDIA device/runtime can be detected without exposing NVENC profiles when the real encoder test fails.
- **Intel H.264 compatibility:** H.264 VAAPI includes the low-power/CQP path required by some Intel generations.
- **Profile safety:** the recommended profile is shown after runtime validation but is not silently applied; the operator explicitly selects it.
- **Transcoding lifecycle:** idle timeout, GC interval and maximum job age are exposed through Compose while preserving the normal per-job HLS lifecycle.
- **Persistent configuration:** dedicated transcoding profile fields are protected from being overwritten by generic WebAdmin configuration saves.
- **Current versions:** upstream server/core **1.6.15**; fork/WebAdmin/VPN **2.0.17**.

## 2.0.15 at a glance

- **Subtitle track IDs:** `subtitles.json` and `subtitles.vtt` now use the same FFmpeg global stream index.
- **Streaming extraction:** embedded WebVTT is streamed from FFmpeg instead of buffering the whole track behind a 60-second timeout.
- **Controlled failures:** invalid tracks return 404 and subtitle-probe timeouts return 504 instead of HTTP 500.
- **Process cleanup:** FFmpeg subtitle extractors are reaped if the client disconnects.

### 2.0.14 UI and HLS reliability


- **WebAdmin actions:** Save configuration and Restart server now use explicit button semantics, robust error handling and visible status feedback.
- **No stale UI after upgrade:** the WebAdmin page is served with no-store/no-cache headers.
- **Real HLS release gate:** CI executes FFmpeg and requires a generated multi-audio master playlist, preventing a repeat of the 2.0.14 header-initialization failure.
- **Multi-audio preserved:** alternate audio renditions remain in the HLS audio group.
- **Native subtitles preserved:** embedded subtitles stay on the existing Stremio subtitle API instead of unsupported subtitle-only HLS variants.

### 2.0.14 HLS media-track attempt


- **Multi-audio HLS:** transcoded playback exposes every probed audio track as an HLS audio rendition instead of keeping only the first track.
- **Selectable subtitles:** supported text subtitle tracks are converted to WebVTT and published as HLS subtitle renditions, enabling the native player selector.
- **Safe subtitle filtering:** bitmap subtitle codecs such as PGS/DVD/DVB are not sent to the WebVTT encoder, preventing a subtitle incompatibility from killing playback.
- **Browser-compatible audio:** multi-track presentations normalise alternate tracks to AAC stereo; the established single-track HLS path stays unchanged.
- **VAAPI baseline preserved:** the 2.0.12 HEVC Main 10 software-decode + VAAPI-encode path is not changed by this release.

### 2.0.12 runtime reliability baseline


```text
Upstream Core   1.6.15
Upstream Server 1.6.15
Fork            2.0.12
WebAdmin        2.0.12
VPN Gateway     2.0.12
```

Version sources:

```text
pyproject.toml
SERVER_VERSION
FORK_VERSION
webadmin/WEBADMIN_VERSION
```

`SERVER_VERSION` and `pyproject.toml` must match the integrated upstream server/core release. `FORK_VERSION` and `webadmin/WEBADMIN_VERSION` must match the 2.x fork release. These version lines are intentionally independent.

## What is implemented today

## 2.0.12 runtime reliability hotfix

Version 2.0.12 addresses regressions found during live validation of 2.0.11.

- **VAAPI transcoding:** full-GPU profiles now detect high-bit-depth H.264/HEVC sources that are unsafe for the hardware decode path and fall back to software decode while keeping VAAPI hardware encode. This fixes real HEVC Main 10 failures such as `No support for codec hevc profile 2` without silently falling back to CPU encoding.
- **Recommended Intel/DRM profile:** the runtime recommender prefers `vaapi-h264` over the full-GPU variant when both pass the synthetic self-test, because encode-only VAAPI proved more robust across real-world source profiles.
- **Transcoding telemetry:** Requested, Effective and Actual status now reflects the explicit execution profile rather than stale legacy `auto/vaapi/h264_vaapi` values.
- **Log clearing:** Application and Docker-container logs use persistent clear cursors, while WebAdmin and updater logs are physically reset. **Clean selected** and **Clean all** now cover every exposed source without modifying Docker's logging-driver files.
- **Configuration/restart feedback:** after a verified save or successful server restart, WebAdmin reloads the configuration from the persistent backend so the UI shows the committed state instead of stale form values.
- **My Library:** per-file playback actions are now clearly labelled **Watch** instead of a small circular play icon, while playback still hands off to the native Stremio player for audio, subtitles, traffic/statistics and casting.

### 2.0.11 My Library native player hand-off

My Library can now launch cached/downloaded media directly into the bundled Stremio Web player instead of maintaining a second playback implementation.

- **Watch** is available on playable cached/downloaded titles.
- Multi-file season packs expose per-file/episode play controls when the torrent file index is known.
- The hand-off uses Stremio's canonical encoded torrent Stream deep-link, so playback keeps the standard **audio-track selector**, **subtitle selector**, **torrent traffic/statistics panel**, casting controls and the existing direct-stream/transcoding policy.
- When a single file index is not known, My Library can leave `fileIdx` unset and let the streaming server perform its normal media-file selection.
- Orphaned part files are never exposed as playable media.

This keeps My Library focused on catalog/download/cache management while the established Stremio player remains the single playback surface.


The 2.0.8 milestone introduced the following platform baseline, which remains part of the current 2.x line:

- unified `compose.yaml` runtime for Stremio Server, WebAdmin, Pi-hole and the persistent Gluetun gateway;
- VPN configuration and enable/disable lifecycle from WebAdmin, without a separate `compose.vpn.yaml`;
- persistent WebAdmin/server configuration in `/config/admin-settings.json`, with atomic save, read-back verification and reliable server restart;
- persistent Pi-hole DNS chain through the Gluetun private DNS bridge;
- VPN validation covering container health, control API, tunnel state, public IP, DNS, Pi-hole upstream, Stremio routing and kill switch;
- automatic VAAPI/GPU overlay detection while keeping the base Compose hardware-agnostic;
- copy-first transcoding policy: compatible H.264 can remain Direct Stream while incompatible HEVC can be converted to H.264 with VAAPI;
- full-GPU VAAPI profiles with hardware decode, `scale_vaapi` and hardware encode when the host supports them;
- automatic repair of a stale Stremio → Gluetun network namespace after Gluetun container recreation;
- versioned Server, WebAdmin and VPN images published through the validated release workflow;
- transactional server update metadata and rollback support exposed through WebAdmin;
- live per-session transcoding monitoring in WebAdmin, correlating each active FFmpeg process with its own job log and exposing Direct Stream/Transcoding state, source → target video/audio codecs, execution engine, PID, elapsed time, CPU/RAM, FFmpeg progress and the applied policy decision.

### 2.0.5 transcoding policy

The explicit transcoding profile now respects the Direct Stream codec allow-list instead of preserving every upstream `-c:v copy` decision unconditionally.

With a typical `vaapi-full-h264` configuration and `h264` as the Direct Stream video codec:

```text
H.264 source
  → video=copy preserved; source=h264; direct=yes
  → no unnecessary video transcode

HEVC/H.265 source
  → video=copy(hevc)->h264_vaapi
  → VAAPI hardware decode
  → scale_vaapi
  → H.264 VAAPI hardware encode
```

If codec probing cannot determine the source codec, the wrapper fails safely by preserving the original copy decision.

### 2.0.6 Gluetun namespace lifecycle

Stremio uses the Gluetun network namespace. Docker binds that relationship to a concrete Gluetun container ID when the Stremio container is created. If Gluetun is later recreated, an unchanged Stremio container can otherwise remain attached to the old namespace.

`start.sh` now performs a post-start integrity check:

```text
Gluetun starts / becomes healthy
          │
          ▼
Compare current Gluetun container ID
with Stremio NetworkMode
          │
     ┌────┴────┐
     │         │
   match     stale
     │         │
     ▼         ▼
   no-op   recreate only Stremio
               │
               ▼
         verify repaired namespace
```

The repair reuses the active Compose configuration and hardware overlay selection. Pi-hole and WebAdmin are not recreated merely to repair this relationship.

### 2.0.7 live transcoding monitor

WebAdmin now provides a live per-session view of active FFmpeg work instead of relying only on the most recently modified transcoding log. Each active process is correlated with its own job log, which makes simultaneous Direct Stream and transcoding sessions distinguishable.

The monitor exposes, when available:

```text
Session action      Direct Stream / Transcoding
Video               source codec → target codec
Audio               source codec → target codec
Engine              copy / VAAPI / CPU / other active engine
Process             PID and elapsed time
Resources           CPU % and memory %
Progress            FPS and processing speed
Policy              active ffmpeg-policy decision
```

If the policy line does not expose the source codec, WebAdmin can recover it from the corresponding FFmpeg stream metadata in that session's log. Process telemetry is read-only and does not change the transcoding decision.

This feature does **not** yet claim automatic client-capability detection. Unknown client playback capability continues to use the validated safe transcoding policy: compatible H.264 can remain Direct Stream while incompatible HEVC can be converted to H.264 using the selected hardware profile such as VAAPI.



### 2.0.8 runtime stability and verified telemetry

Version 2.0.8 hardens the 2.0.7 observability and runtime lifecycle without changing the integrated upstream core version.

Key improvements include:

- configuration save/read-back verification and restart validation;
- explicit Requested, Effective and Actual transcoding state;
- FFmpeg PID, CPU, memory, elapsed-time and per-session progress telemetry;
- reliable parsing and preservation of the active `ffmpeg-policy` decision;
- automatic VAAPI profile verification on a fresh WebAdmin process;
- verified `vaapi-full-h264` hardware decode/encode execution when supported;
- Stremio health validation across VPN enable/disable transitions;
- hardened DIRECT-mode DNS forwarding through Pi-hole and the gateway resolver;
- safer trusted-certificate refresh with validation before replacement.

The integrated server/core remains **1.6.15**. Platform, WebAdmin and VPN gateway are released as **2.0.8**.


---

# Architecture

## One stack, two operating states

Version 2.x removes the old split between `compose.yaml` and `compose.vpn.yaml`.

The platform always starts from:

```bash
docker compose up -d
```

or:

```bash
sh start.sh
```

Runtime topology:

```text
                         Host / LAN
                             │
               ┌─────────────┼─────────────┐
               │             │             │
               ▼             ▼             ▼
          WebAdmin :8090  Pi-hole :8053  Published Stremio ports
               │             │             │
               │             │             ▼
               │             └──────► stremio-gluetun
               │                        │
               │                        │ persistent network namespace
               │                        ▼
               └────────────────► stremio-libtorrent-server
```

Gluetun is always present as the stable gateway/network namespace.

Its internal VPN state is independent:

```text
VPN OFF
  Gluetun container: running
  OpenVPN tunnel:    stopped
  Stremio egress:    direct

VPN ON
  Gluetun container: running
  OpenVPN tunnel:    running
  Stremio egress:    VPN

VPN ON + tunnel failure
  Gluetun container: running
  OpenVPN tunnel:    failed/recovering
  Stremio egress:    blocked/fail-closed
```

The gateway container is not stopped when the user disables VPN.

---

# First installation

Clone the repository:

```bash
git clone https://github.com/emmanique/stremio-libtorrent-server-webadmin.git
cd stremio-libtorrent-server-webadmin
sh start.sh
```

The initial installation does **not** require a VPN account.

Expected initial state:

```text
stremio-gluetun             running / DIRECT
stremio-libtorrent-server   running
stremio-webadmin            running
stremio-pihole              running
```

Access points for a host such as `192.168.1.245`:

| Service | Address |
| --- | --- |
| Web Player | `http://192.168.1.245:8080` |
| WebAdmin | `http://192.168.1.245:8090` |
| Streaming API | `http://192.168.1.245:11470` |
| Trusted HTTPS / Library | `https://<trusted-host>:12470/` |
| Pi-hole Admin | `http://192.168.1.245:8053/admin/` |
| BitTorrent | `6881/tcp` and `6881/udp` |

To override automatic LAN IP detection:

```bash
IPADDRESS=192.168.1.245 sh start.sh
```

---

# VPN

VPN configuration is performed from:

```text
WebAdmin → VPN
```

A fresh installation shows VPN as disabled until a valid CyberGhost/OpenVPN profile exists.

A CyberGhost ZIP is expected to contain:

```text
openvpn.ovpn
ca.crt
client.crt
client.key
```

The profile also stores the generated OpenVPN username/password in the private `vpn-data` volume.

## State model

```text
NOT CONFIGURED
      │
      ▼
CONFIGURED / OFF
      │ Enable VPN
      ▼
STARTING
   ┌──┴────┐
   ▼       ▼
CONNECTED ERROR
   │
   │ Disable VPN
   ▼
DIRECT
```

VPN enable state is persistent.

If the host reboots while VPN was enabled, the supervisor restores the requested VPN state instead of intentionally returning to direct mode.

## Profile change

Changing the active VPN profile does not restart the Gluetun container. Only the VPN child/tunnel is recycled so the Stremio network namespace remains stable.

## Compatibility launcher

`start-vpn.sh`, `start-vpn.ps1` and `start-vpn.bat` are retained only for compatibility.

They now start the same unified Compose stack. VPN itself is controlled from WebAdmin.

---

# Trusted HTTPS certificates and VPN routing

The streaming container can fetch a trusted `*.519b6502d940.stremio.rocks` certificate and expose the trusted HTTPS endpoint on port `12470`.

For a LAN address such as `192.168.1.244`, the trusted hostname is:

```text
192-168-1-244.519b6502d940.stremio.rocks
```

The current certificate fetch path uses the streaming container network namespace. The bundled certificate helper first discovers the public egress IP through `api.ipify.org` and then requests the certificate from `api.strem.io`.

### VPN-on certificate renewal note

When VPN is enabled, the streaming container shares Gluetun's network namespace. The certificate helper therefore sees the **VPN public IP**, not necessarily the normal WAN egress used when the certificate was originally obtained. On some VPN exits, certificate acquisition/renewal can fail even though general Internet access and streaming continue to work.

The runtime does not delete the persistent certificate when a refresh fails. If a valid certificate already exists in the Stremio cache it remains available to nginx. However, when the automatic refresh path fails, an explicit `SERVER_URL` is recommended so the Web Player continues to target the trusted endpoint.

Example:

```bash
SERVER_URL=https://192-168-1-244.519b6502d940.stremio.rocks:12470/
```

Operationally, if a trusted certificate is approaching expiry and refresh fails while VPN is ON:

1. temporarily switch VPN to DIRECT/OFF;
2. restart/recreate the Stremio server so the certificate helper can fetch through the direct egress;
3. confirm the new certificate expiry;
4. enable VPN again.

Do not delete a still-valid certificate merely because refresh failed. Certificate persistence is stored with the Stremio cache and survives normal upgrades/recreates.

---

# Configuration persistence and restart reliability

Version 2.x treats configuration persistence as a release-blocking capability.

WebAdmin mounts:

```text
stremio-config:/config
```

read/write.

Stremio mounts the same volume:

```text
stremio-config:/config:ro
```

The save path is:

```text
/config/admin-settings.json
```

Save flow:

```text
WebAdmin
   │
   ▼
atomic write to temporary file
   │
   ▼
fsync
   │
   ▼
atomic replace
   │
   ▼
read-back verification
   │
   ▼
docker exec Stremio:
cat /config/admin-settings.json
   │
   ▼
saved values must match
```

The Server restart endpoint uses Docker directly:

```text
POST /api/restart
      │
      ▼
docker restart stremio-libtorrent-server
      │
      ▼
StartedAt must change
      │
      ▼
curl 127.0.0.1:11470/health
inside the Stremio container
```

This management path does not depend on the VPN being connected.

Required behavior:

| VPN state | Save configuration | Restart Server |
| --- | --- | --- |
| Not configured | Yes | Yes |
| Configured / OFF | Yes | Yes |
| Connected | Yes | Yes |
| VPN error | Yes | Yes |

---

# Pi-hole and DNS

Pi-hole uses one stable internal upstream:

```text
172.30.0.10#1053
```

The persistent gateway exposes this private DNS bridge.

In DIRECT mode:

```text
Stremio
   ↓
Pi-hole
   ↓
Gateway DNS bridge
   ↓
configured public resolver
   ↓
Internet
```

In VPN mode:

```text
Stremio
   ↓
Pi-hole
   ↓
Gateway DNS bridge
   ↓
Gluetun resolver
   ↓
VPN tunnel
```

The Pi-hole performance/security baseline remains controlled through Compose `FTLCONF_*` values.

To expose Pi-hole DNS to the LAN:

```bash
docker compose -f compose.yaml -f compose.dns.yaml up -d
```

---

# Transcoding

The project keeps a copy-first policy: compatible media remains Direct Stream whenever possible. An explicit execution profile changes how required video transcoding is executed; it does not force every stream to transcode.

Supported execution profiles:

```text
Preserve Stremio decision
H.264 VAAPI — GPU encode only
HEVC VAAPI — GPU encode only
H.264 VAAPI — Full GPU
HEVC VAAPI — Full GPU
H.264 NVIDIA NVENC
HEVC NVIDIA NVENC
H.264 CPU / libx264
HEVC CPU / libx265
```

Hardware profiles are selectable only after real FFmpeg runtime verification.

## Automatic backend selection

Use the launcher for normal operation:

```bash
GPU_BACKEND=auto sh start.sh
```

or for an explicit pull/recreate:

```bash
GPU_BACKEND=auto sh start.sh pull
GPU_BACKEND=auto sh start.sh up -d --force-recreate
```

AUTO behavior:

```text
valid Intel/DRM render node
        │
        └──► VAAPI overlay + runtime self-tests

no usable VAAPI + NVIDIA runtime
        │
        └──► NVIDIA overlay + real NVENC self-tests

no usable hardware backend
        │
        └──► CPU fallback
```

AUTO may expose more than one detected accelerator for capability testing, but WebAdmin only offers profiles whose encoder self-test succeeds.

## VAAPI device discovery

Leave `VAAPI_DEVICE` empty unless a specific render node must be forced:

```bash
GPU_BACKEND=auto
VAAPI_DEVICE=
```

`start.sh` prefers an Intel render node by PCI vendor ID and can therefore handle hosts where the usable device is `renderD128`, `renderD129` or another render node.

Do not copy a render-node value from another server without validating the local host.

## Intel media driver

Modern Intel GPUs such as Tiger Lake / Iris Xe normally use the Intel media driver:

```bash
LIBVA_DRIVER_NAME=iHD
```

A typical validation is:

```bash
docker exec stremio-libtorrent-server \
  vainfo --display drm --device /dev/dri/renderD128
```

A healthy iHD initialization includes:

```text
Trying to open .../iHD_drv_video.so
va_openDriver() returns 0
```

If `LIBVA_DRIVER_NAME` is explicitly present but empty in the container, libva can attempt to load `_drv_video.so` and fail. On an affected Intel host, set `LIBVA_DRIVER_NAME=iHD` explicitly.

Older Intel generations may require a different VAAPI driver; verify with `vainfo` rather than assuming `iHD`.

## Runtime profile verification

Refresh the hardware/profile matrix:

```bash
curl -fsS -X POST \
  http://<LAN-IP>:8090/api/transcoding/profiles/refresh
```

Inspect the result:

```bash
curl -fsS http://<LAN-IP>:8090/api/transcoding/profiles
```

For a validated Intel full-GPU H.264 path, the expected state is similar to:

```text
selected    = preserve
recommended = vaapi-full-h264
device      = /dev/dri/renderD128

vaapi  detected=true  runtime=true  h264=true  hevc=true  selectable=true
nvidia detected=false runtime=false h264=false hevc=false selectable=false
cpu    detected=true  runtime=true  h264=true  hevc=true  selectable=true
```

`selected=preserve` is not an error. The recommender does not silently change the operator's execution profile.

Apply a verified profile explicitly:

```bash
curl -fsS -X PUT \
  http://<LAN-IP>:8090/api/transcoding/profile \
  -H 'Content-Type: application/json' \
  -d '{"profile":"vaapi-full-h264","quality":22}'
```

## Transcoding job lifecycle

Compose exposes:

```text
STREMIOSRV_TRANSCODE_IDLE_TIMEOUT
STREMIOSRV_TRANSCODE_GC_INTERVAL
STREMIOSRV_TRANSCODE_GC_MAX_AGE
```

The Compose production fallbacks are `300`, `60` and `600` seconds respectively. More aggressive values can be useful for testing abandoned-job cleanup but should be treated as explicit operator overrides, especially a short idle timeout that may affect long pauses.

## Manual overlays

Manual overlay invocation remains available for diagnostics:

VAAPI:

```bash
docker compose -f compose.yaml -f compose.vaapi.yaml up -d
```

NVIDIA:

```bash
docker compose -f compose.yaml -f compose.gpu.yaml up -d
```

For normal installs and upgrades, prefer `start.sh` so render-node discovery and backend selection remain consistent.


---

# Persistent data

Normal upgrades preserve named volumes.

Important volumes:

```text
stremio-cache
stremio-config
webadmin-data
pihole-etc
pihole-dnsmasq
vpn-data
gluetun-data
```

Do not use:

```bash
docker compose down -v
```

for routine upgrades.

---

# Upgrading from a previous version

The normal upgrade path preserves named Docker volumes and therefore keeps WebAdmin settings, Stremio configuration/cache, Pi-hole data and VPN profile/state.

Never use `docker compose down -v` for a routine upgrade.

## Upgrade using the stable `:latest` images

The validated release workflow publishes Server, WebAdmin and VPN images with versioned tags plus the moving aliases `:2` and `:latest`.

For a normal Git-based installation:

```bash
cd ~/stremio-libtorrent-server-webadmin

git switch main
git pull --ff-only origin main
```

Keep the image variables on `:latest`:

```text
STREMIO_IMAGE=ghcr.io/emmanique/stremio-libtorrent-server-webadmin:latest
WEBADMIN_IMAGE=ghcr.io/emmanique/stremio-libtorrent-server-webadmin-webadmin:latest
VPN_IMAGE=ghcr.io/emmanique/stremio-libtorrent-server-webadmin-vpn:latest
```

For hardware auto-detection, leave the VAAPI device unset unless the host requires an explicit override:

```text
GPU_BACKEND=auto
VAAPI_DEVICE=
```

Then pull and recreate through the launcher:

```bash
GPU_BACKEND=auto sh start.sh pull

GPU_BACKEND=auto \
sh start.sh up -d --force-recreate
```

`start.sh` detects the LAN IPv4, selects the hardware overlay and persists the detected `IPADDRESS` for subsequent Compose/WebAdmin operations.

## Post-upgrade validation

First verify images and container state:

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'

docker inspect stremio-libtorrent-server \
  --format 'SERVER={{.Config.Image}}'

docker inspect stremio-webadmin \
  --format 'WEBADMIN={{.Config.Image}}'

docker inspect stremio-gluetun \
  --format 'VPN={{.Config.Image}}'
```

Ports are bound to the detected `IPADDRESS`, not necessarily to `127.0.0.1`. Therefore use the actual LAN address for host-side health checks:

```bash
curl -fsS http://<LAN-IP>:11470/health
curl -fsS http://<LAN-IP>:8090/health
curl -fsS http://<LAN-IP>:8090/api/component-versions
```

Example for `192.168.1.244`:

```bash
curl -fsS http://192.168.1.244:11470/health
curl -fsS http://192.168.1.244:8090/health
```

The Stremio container intentionally has no host port listing of its own because it shares Gluetun's network namespace. Published Stremio ports appear on `stremio-gluetun`.

Then validate the transcoding matrix:

```bash
curl -fsS -X POST \
  http://<LAN-IP>:8090/api/transcoding/profiles/refresh
```

For Intel hosts, also verify the active VAAPI driver and local render node. Do not assume that a device number validated on another server applies to this one.

If the previous installation used the old `compose.vpn.yaml` topology, do not continue launching that file. Version 2.x uses the unified `compose.yaml`; `start-vpn.sh` is retained only as a compatibility wrapper and VPN enable/disable is controlled from WebAdmin.


## Rollback after an upgrade

If an upgrade must be rolled back, keep the persistent volumes and return the repository to the previous release tag, for example `v2.0.5`:

```bash
cd ~/stremio-libtorrent-server-webadmin
git fetch --tags origin
git checkout v2.0.5
docker compose pull
sh start.sh
```

Do not use `down -v` during rollback. After validation, return to the stable branch with `git checkout main`.

## Development 2.x installation

```bash
git fetch --prune origin
git checkout develop/2.x
git pull --ff-only origin develop/2.x
sh start.sh
```

---

# Published images

## GitHub Container Registry

```text
ghcr.io/emmanique/stremio-libtorrent-server-webadmin:2.0.17
ghcr.io/emmanique/stremio-libtorrent-server-webadmin-webadmin:2.0.17
ghcr.io/emmanique/stremio-libtorrent-server-webadmin-vpn:2.0.17
```

Stable moving aliases:

```text
:2
:latest
```

These aliases are updated only by the validated 2.x release workflow.

## Docker Hub

```text
edmanique/stremio-libtorrent-server-webadmin:2.0.17
edmanique/stremio-libtorrent-server-webadmin:webadmin-2.0.17
edmanique/stremio-libtorrent-server-webadmin:vpn-2.0.17
```

---

# Repository automation

The repository uses five permanent workflows for CI, dependency validation, coordinated version bumps, releases and selective upstream review.

See [docs/WORKFLOWS.md](docs/WORKFLOWS.md) for the complete operating model.

---

# Development model

2.x uses dedicated branches:

```text
feature/*
    │
    ▼
develop/2.x
    │
    ▼
release/2.x.y
    │
    ▼
main
    │
    ▼
v2.x.y
```

Urgent fixes:

```text
main
  │
  ▼
hotfix/2.x.y
  │
  ├──► main
  └──► develop/2.x
```

See [docs/BRANCHING-2X.md](docs/BRANCHING-2X.md).

---

# CI/CD for 2.x

## 2.x Continuous Validation

`.github/workflows/2x-ci.yml`

Validates:
- unified component versions;
- Python/Ruff syntax and style;
- shell scripts;
- WebAdmin JavaScript syntax;
- unified Compose and overlays;
- full pytest suite;
- Save Configuration regression;
- Server Restart regression;
- VPN single-Compose regression;
- Server/WebAdmin/VPN Docker builds;
- image smoke tests.

## 2.x Dependency Validation

`.github/workflows/2x-dependency-validation.yml`

Runs for dependency changes and validates:
- `uv.lock`;
- Python dependency consistency;
- dependency audit;
- runtime-sensitive tests;
- Docker builds.

## Dependency updates

`.github/dependabot.yml`

Dependabot checks weekly:
- root Python packages;
- WebAdmin Python packages;
- root/WebAdmin/VPN Docker bases;
- GitHub Actions.

Updates target `develop/2.x`, not `main`.

## 2.x Release

`.github/workflows/2x-release.yml`

Triggered manually with the target release version (for example `2.0.7`). The workflow validates the release contract and creates the corresponding `v2.x.y` tag/release.

The release workflow:
1. validates version consistency;
2. runs the complete test gate;
3. validates Compose;
4. builds Server, WebAdmin and VPN images;
5. smoke-tests images;
6. publishes GHCR versioned, `:2` and `:latest` tags;
7. mirrors the validated images to Docker Hub when credentials are configured;
8. creates or updates the GitHub Release from `docs/releases/v2.x.y.md`.

Legacy 1.x release automation is isolated from 2.x tags.

---

# Repository structure

```text
compose.yaml
compose.dns.yaml
compose.vaapi.yaml
compose.gpu.yaml

start.sh
start-vpn.sh                 compatibility wrapper

src/                         Stremio server
webadmin/                    WebAdmin
vpn/                         persistent gateway/VPN supervisor
docker/                      runtime wrappers and publishing helpers
tests/                       unit and regression tests
tools/                       host-side validation tools

docs/BRANCHING-2X.md
docs/releases/
VERSIONING.md

.github/workflows/2x-ci.yml
.github/workflows/2x-dependency-validation.yml
.github/workflows/2x-release.yml
.github/dependabot.yml
```

---

# Security notes

- WebAdmin has access to the Docker socket and must remain on a trusted LAN/VPN.
- Do not expose port 8090 directly to the public Internet.
- VPN credentials, private keys and certificates remain in `vpn-data`.
- Keep the VPN kill switch enabled.
- Do not store passwords, tokens or VPN credentials in tracked `.env` files.
- Treat Library Addon URLs/tokens as secrets.
- A trusted `stremio.rocks` certificate is persistent; if renewal fails while VPN is enabled, keep the valid certificate and retry renewal through DIRECT/OFF mode rather than deleting it.

---

# Release information

Current stable release:

[docs/releases/v2.0.17.md](docs/releases/v2.0.17.md)

Versioning:

[VERSIONING.md](VERSIONING.md)

Branch strategy:

[docs/BRANCHING-2X.md](docs/BRANCHING-2X.md)

---

## License

MIT. See [LICENSE](LICENSE).
