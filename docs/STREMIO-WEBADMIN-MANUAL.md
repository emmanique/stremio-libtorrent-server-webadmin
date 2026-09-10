# Stremio Libtorrent Server with Separate Web Admin

## Administration, Features and Configuration Manual

This manual applies to the initial distribution based on:

`https://github.com/emmanique/stremio-libtorrent-server-webadmin`

The distribution separates the streaming engine, administration interface and DNS service into independent containers. Rebuilding or replacing the Stremio container does not replace the Web Admin application or erase its configuration.

## 1. Architecture

| Component | Purpose | Published ports |
| --- | --- | --- |
| `stremio-libtorrent-server` | Torrent engine, streaming API, web player and transcoding | `8080`, `11470`, `12470`, `6881/TCP`, `6881/UDP` |
| `stremio-webadmin` | Administration interface, monitoring, configuration and update orchestration | `8090/TCP` |
| `stremio-pihole` | DNS filtering and DNS service for Stremio and the local network | `53/TCP`, `53/UDP`, `8053/TCP` |

All services use the dedicated `stremio-internal` Docker network. Pi-hole has the fixed internal address `172.30.0.53`, and the Stremio container uses that address as its DNS resolver.

### Persistent volumes

| Volume | Mounted by | Stored information |
| --- | --- | --- |
| `stremio-cache` | Stremio | Downloaded media, torrent state, pins, resume data and certificates |
| `stremio-config` | Web Admin (read/write), Stremio (read-only) | `admin-settings.json` containing settings changed in Web Admin |
| `webadmin-data` | Web Admin | Administrative audit log and software-update results |
| `pihole-etc` | Pi-hole | Pi-hole configuration and database |
| `pihole-dnsmasq` | Pi-hole | Additional DNS and dnsmasq rules |

Do not run `docker compose down -v` during a normal update. The `-v` option removes named volumes and therefore deletes persistent data.

## 2. Main features

### Dashboard and performance monitor

The dashboard reports server health, version, uptime, processor utilisation, load average, memory usage, network traffic, torrent transfer rates, peer count, active streams, cache consumption and free disk space. CPU and memory samples are displayed as rolling graphs.

### Stream, cache and pin management

- View active and cached content.
- Monitor download/upload speed, peers and progress.
- Pin content so that it remains available and is protected from normal cache eviction.
- Unpin content when permanent retention is no longer required.
- Remove a torrent from the active session.
- Permanently delete selected cached content.

Pinning still depends on available disk space. A pin is rejected when completing the selected content would leave insufficient operational space.

### All Configuration

The **All Configuration** page groups all supported Stremio parameters and provides a description, input type, current value and unit. Values are stored in `stremio-config` and read by Stremio on startup.

Fields shown in minutes are converted back to seconds before they are saved. This preserves compatibility with the Stremio configuration model.

Most changes require a Stremio restart. The Web Admin container remains running while Stremio restarts.

### Logs

The Logs page provides:

- Stremio container output.
- Docker container output.
- Web Admin audit records.
- Software-update result information.

Web Admin-owned logs can be cleared from the interface. Docker logging-driver output cannot be safely truncated from inside the Web Admin container; use host-side Docker log rotation for that source.

### Software updates

The update function checks and downloads the `main` branch of the configured fork. It validates archive paths, applies the small external-configuration adapter and builds a replacement Stremio image. If the expected integration point in `app.py` has changed, the update stops before replacing the active image.

After a successful build, activate the new Stremio image with:

```bash
docker compose up -d --force-recreate stremio-libtorrent-server
```

The Web Admin image, its state and all persistent volumes remain unchanged.

### Pi-hole

Pi-hole provides DNS filtering and is also used as the internal resolver for Stremio. Its administration interface is available on port `8053`. This distribution configures the Pi-hole administration password as empty; access must therefore be restricted to a trusted LAN or VPN.

## 3. Initial installation

### Requirements

- Linux host with Docker Engine and Docker Compose v2.
- LAN address assigned to the host.
- Ports `53/TCP` and `53/UDP` available on that LAN address.
- Sufficient storage for the configured cache.
- Internet access for image builds, GitHub updates, trackers and Pi-hole upstream DNS.

Create the environment file:

```bash
cp .env.example .env
nano .env
```

At minimum, set the actual LAN address:

```env
IPADDRESS=192.168.1.254
```

Validate and start the platform:

```bash
docker compose config
docker compose up -d --build
docker compose ps
```

### Access URLs

Replace `192.168.1.254` with the value configured in `IPADDRESS`.

| Service | URL |
| --- | --- |
| Web Admin | `http://192.168.1.254:8090` |
| Web Player | `http://192.168.1.254:8080` |
| Stremio API | `http://192.168.1.254:11470` |
| Pi-hole | `http://192.168.1.254:8053/admin/` |

## 4. Environment variables

These variables are normally defined in `.env` and expanded by Docker Compose.

| Variable | Type / format | Default | Description |
| --- | --- | --- | --- |
| `IPADDRESS` | IPv4 address | Required for Pi-hole | LAN address used to bind all published services. Using a specific address avoids binding DNS to `0.0.0.0` and allows coexistence with `systemd-resolved` on `127.0.0.53`/`127.0.0.54`. |
| `STREMIO_DATA_DIR` | Volume name or host path | `stremio-cache` | Storage location mounted as `/root/.stremio-server`. A host path can be used when existing cache and certificates must be retained. |
| `STREMIOSRV_BT_LISTEN_PORT` | Integer port | `6881` | BitTorrent listening and published TCP/UDP port. The router/firewall must forward the same port for inbound peers. |
| `CERT_FILE` | Filename | `certificates.pem` | Certificate/key PEM filename located in the Stremio data directory. |
| `SERVER_URL` | URL | Empty/automatic | External streaming-server URL advertised to clients. Leave empty when automatic discovery is appropriate. |
| `TZ` | IANA timezone | `Africa/Luanda` | Timezone used by Pi-hole, for example `Africa/Luanda` or `Europe/Lisbon`. |
| `PIHOLE_WEB_PORT` | Integer port | `8053` | Host port for the Pi-hole administration interface. |
| `PIHOLE_UPSTREAM_DNS` | Semicolon-separated IP addresses | `1.1.1.1;1.0.0.1` | Upstream resolvers used by Pi-hole. Do not point this value back to the Pi-hole host itself. |

### Internal service variables

The following values are already defined in `compose.yaml` and normally should not be changed.

| Variable | Service | Default | Purpose |
| --- | --- | --- | --- |
| `STREMIOSRV_CACHE_ROOT` | Stremio | `/root/.stremio-server` | Internal cache and state path. |
| `STREMIOSRV_EXTERNAL_CONFIG` | Stremio | `/config/admin-settings.json` | Read-only configuration file generated by Web Admin. |
| `WEBADMIN_STATE` | Web Admin | `/data` | Persistent Web Admin state path. |
| `STREMIO_CONFIG_FILE` | Web Admin | `/config/admin-settings.json` | File written when configuration is saved. |
| `STREMIO_URL` | Web Admin | `http://stremio-libtorrent-server:11470` | Internal URL used to call the Stremio API. |
| `STREMIO_CONTAINER` | Web Admin | `stremio-libtorrent-server` | Docker container managed by restart and log actions. |
| `STREMIO_IMAGE` | Web Admin | `stremio-libtorrent-server-webadmin:local` | Docker image tag produced by the update build. |
| `STREMIO_SOURCE_REPO` | Web Admin | Fork URL | Git source used for version checks and software updates. |
| `WEB_PLAYER_URL` | Web Admin | Derived from `IPADDRESS` | Player URL displayed and copied from the dashboard. |
| `FTLCONF_webserver_api_password` | Pi-hole | Empty | Pi-hole administrative password. Empty means no authentication. |
| `FTLCONF_dns_listeningMode` | Pi-hole | `all` | Allows Pi-hole to answer DNS queries arriving through Docker and the published LAN address. |
| `FTLCONF_dns_upstreams` | Pi-hole | From `PIHOLE_UPSTREAM_DNS` | Pi-hole upstream DNS resolver list. |

## 5. All Configuration variables

The environment-variable equivalent of each field is its uppercase name prefixed with `STREMIOSRV_`. For example, `cache_size` corresponds to `STREMIOSRV_CACHE_SIZE`. Values saved in Web Admin take effect from `admin-settings.json` when Stremio starts.

### Network and core service

| Web Admin field | Input type | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `http_port` | Number (port), read-only | `11470` | Internal HTTP API port. Port publishing is controlled by Compose. | Yes |
| `bt_listen_port` | Number (port) | `6881` | TCP/UDP port used to receive BitTorrent peers. The Compose-published port must match it. | Yes |
| `enable_upnp` | Checkbox | `true` | Requests automatic BitTorrent port mapping using UPnP/NAT-PMP. | Yes |
| `cache_root` | Text, read-only | `/root/.stremio-server` | Persistent Stremio cache and state directory. | Yes |
| `cert_file` | Text, read-only | `certificates.pem` | TLS certificate and private-key bundle inside `cache_root`. | Yes |

### Cache and storage

| Web Admin field | Input type / unit | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `cache_size` | Byte size | `18 GiB` | Maximum evictable media-cache budget. It should exceed the largest file expected to be streamed. | Yes |
| `cache_evict_interval` | Number, minutes | `1` | Interval between cache-eviction checks. Stored internally as 60 seconds. | Yes |
| `cache_evict_grace` | Number, minutes | `30` | Minimum idle period before recently served content can be evicted. | Yes |
| `resume_save_interval` | Number, minutes | `0.5` | Interval between fast-resume saves. Stored internally as 30 seconds. | Yes |
| `resume_retention_days` | Number, days | `365` | Maximum age of unused resume records. Zero disables expiry. | Yes |

Byte-size fields accept raw bytes or suffixes such as `64GiB`, `512MiB` and `1.5GiB`. `GiB` is binary, while `GB` is decimal. Rate limits are bytes per second, not bits per second.

### BitTorrent bandwidth and seeding

| Web Admin field | Input type / unit | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `bt_max_connections` | Number | `400` | Maximum simultaneous BitTorrent peer connections. | Yes |
| `download_rate_limit` | Byte size per second | `0` | Global torrent download cap. Zero means unlimited. | Yes |
| `upload_rate_limit` | Byte size per second | `0` | Global torrent upload cap. Zero means unlimited. | Yes |
| `idle_download_rate_limit` | Byte size per second | `1 MiB/s` | Per-torrent background cap while another title is being played. Zero disables this prioritisation. | Yes |
| `max_streams` | Number | `0` | Maximum concurrent playback streams. Zero means unlimited. | Yes |
| `seed_on_complete` | Checkbox | `true` | Continues uploading wanted data after download completion. | Yes |
| `max_seed_minutes` | Number, minutes | `0` | Maximum seeding duration after completion. Zero means unlimited. | Yes |
| `seed_policy_interval` | Number, minutes | `0.25` | Frequency of seeding-policy checks. Stored internally as 15 seconds. | Yes |

### Streaming and buffering

| Web Admin field | Input type / unit | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `readahead_bytes` | Byte size | `256 MiB` | High-priority buffer maintained ahead of the playback position. | Yes |
| `stream_piece_timeout` | Number, minutes | `0.5` | Maximum wait for each piece during established playback. Stored internally as 30 seconds. | Yes |
| `stream_first_piece_timeout` | Number, minutes | `2` | Maximum wait for the first piece after starting or seeking. | Yes |
| `max_streams` | Number | `0` | Limits simultaneous streaming sessions; zero is unlimited. | Yes |

Increasing the timeout may help a slow swarm, but it also increases the time the player appears frozen when a piece cannot be obtained.

### Transcoding

| Web Admin field | Input type / unit | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `transcode_profile` | Text | Empty | Hardware-transcoding profile. Empty enables automatic detection. | Yes |
| `transcode_gc_interval` | Number, minutes | `1` | Interval for detecting abandoned encoders and transcode directories. | Yes |
| `transcode_idle_timeout` | Number, minutes | `5` | Stops a transcode job that has not been read within this period. Zero disables the idle reaper. | Yes |
| `transcode_gc_max_age` | Number, minutes | `10` | Removes an unclaimed transcode directory older than this value. | Yes |

### Trackers and DHT

| Web Admin field | Input type / unit | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `extra_trackers` | Multiline text | Empty | Comma, space or newline-separated `udp`, `http(s)` or `ws(s)` tracker URLs appended to every torrent. | Yes |
| `tracker_list_url` | URL text | Empty | Optional remotely maintained tracker-list URL. Empty keeps operation static/offline-safe. | Yes |
| `tracker_list_refresh_hours` | Number, hours | `24` | Frequency at which the remote tracker list is refreshed. | Yes |
| `dht_bootstrap_nodes` | Text | Empty | Optional comma-separated DHT bootstrap nodes in `host:port` format. | Yes |

### Adaptive piece selection

| Web Admin field | Input type / unit | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `adaptive_picking` | Checkbox | `false` | Switches between sequential and parallel piece selection according to buffer health. | Yes |
| `adaptive_low_bytes` | Byte size | `64 MiB` | Buffer level below which strict sequential downloading is restored. | Yes |
| `adaptive_high_bytes` | Byte size | `256 MiB` | Buffer level above which parallel piece selection is allowed. | Yes |
| `adaptive_interval` | Number, minutes | `0.0333` | Controller evaluation interval. Stored internally as 2 seconds. | Yes |

This feature is experimental. The low threshold must remain below the high threshold.

### Next-episode prefetch

| Web Admin field | Input type / unit | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `prefetch_next` | Checkbox | `false` | Pre-downloads part of the next video file in the same torrent. | Yes |
| `prefetch_next_fraction` | Decimal fraction | `0.05` | Fraction of the next file to prefetch. `0.05` means 5%. | Yes |
| `prefetch_next_max_bytes` | Byte size | `128 MiB` | Maximum amount downloaded by prefetch. | Yes |
| `prefetch_trigger_fraction` | Decimal fraction | `0.90` | Playback position that starts prefetch. `0.90` means 90%. | Yes |

### Library interface

| Web Admin field | Input type | Default | Description | Restart |
| --- | --- | --- | --- | --- |
| `library_ui` | Checkbox | `false` | Enables the authenticated library download interface supplied by the fork. | Yes |
| `library_owner` | Text | Empty | Stremio account ID or email allowed to own the library. Empty uses trust-on-first-use. | Yes |
| `library_allow_http` | Checkbox | `false` | Allows library login over HTTP. Use only on a trusted LAN or VPN. | Yes |
| `library_addon_allow` | CIDR list | Empty/private defaults | Comma-separated networks allowed to access the library addon. | Yes |

## 6. Routine operations

### Check service status

```bash
docker compose ps
docker inspect stremio-libtorrent-server --format '{{.State.Health.Status}}'
```

### View logs

```bash
docker logs --tail=200 stremio-libtorrent-server
docker logs --tail=200 stremio-webadmin
docker logs --tail=200 stremio-pihole
```

### Restart only Stremio

```bash
docker compose restart stremio-libtorrent-server
```

### Rebuild only Stremio

```bash
docker compose up -d --build --force-recreate stremio-libtorrent-server
```

### Rebuild only Web Admin

```bash
docker compose up -d --build --force-recreate webadmin
```

### Back up persistent volumes

Stop write activity before taking a consistent backup. At minimum, protect the Stremio cache/configuration and Pi-hole configuration volumes. If `STREMIO_DATA_DIR` is a host path, back up that path using the host's normal backup system.

## 7. Troubleshooting

### Pi-hole cannot bind port 53

Confirm that `IPADDRESS` is the actual LAN address and that Compose is not publishing DNS on `0.0.0.0`:

```bash
docker compose config
sudo ss -lntup | grep ':53 '
```

`systemd-resolved` may continue listening on `127.0.0.53:53`; Pi-hole can coexist by binding to the LAN address.

### Web Admin reports that Stremio is unavailable

```bash
docker compose ps
docker logs --tail=200 stremio-libtorrent-server
docker exec stremio-webadmin python -c "import urllib.request; print(urllib.request.urlopen('http://stremio-libtorrent-server:11470/health').read())"
```

### Configuration does not appear to apply

Save the configuration, then restart only Stremio. Inspect the stored file:

```bash
docker exec stremio-webadmin cat /config/admin-settings.json
docker compose restart stremio-libtorrent-server
```

### Update build succeeds but the running version does not change

The build intentionally does not replace the running container automatically. Activate it explicitly:

```bash
docker compose up -d --force-recreate stremio-libtorrent-server
```

### Pin operation reports insufficient space

```bash
docker exec stremio-libtorrent-server df -h /root/.stremio-server
docker exec stremio-libtorrent-server du -h -d 1 /root/.stremio-server | sort -h
```

Reduce cached content, lower the configured cache budget or increase storage. Do not disable the disk-space guard without another mechanism preventing a full filesystem.

## 8. Security considerations

- Never expose ports `8090` or `8053` directly to the Internet.
- Restrict Web Admin and Pi-hole access with a host firewall, trusted VLAN or VPN.
- The Web Admin container has access to `/var/run/docker.sock` for logs, restart and image-build operations. Docker socket access is effectively privileged host access.
- Pi-hole administration has no password in this distribution. Add authentication or strict network controls before using it outside an isolated LAN.
- Use HTTPS for any library login or administrative access that crosses an untrusted network.
- Back up persistent volumes before upgrades and periodically test restoration.

## 9. Uninstallation

Stop and remove containers while preserving data:

```bash
docker compose down
```

Permanently remove containers and named volumes only when all stored cache, configuration, pins and Pi-hole data may be deleted:

```bash
docker compose down -v
```

The second command is destructive and is not part of a normal update procedure.
