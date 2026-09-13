"""Fork-owned update policy for Stremio Web Admin.

The upstream project is an input to this fork, never a runtime update source.
This module deliberately downloads and builds only the configured fork/branch.
It also exposes FORK_VERSION rather than the upstream package version as the
available WebAdmin release.
"""

from __future__ import annotations

import json
import os
import tarfile
import tempfile
import urllib.request
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import app as legacy

SOURCE_REPO = os.getenv(
    "STREMIO_SOURCE_REPO", "https://github.com/emmanique/stremio-libtorrent-server-webadmin"
).rstrip("/")
SOURCE_BRANCH = os.getenv("STREMIO_SOURCE_BRANCH", "main")
SOURCE_ARCHIVE = f"{SOURCE_REPO}/archive/refs/heads/{SOURCE_BRANCH}.tar.gz"
FORK_VERSION_URL = f"{SOURCE_REPO}/raw/{SOURCE_BRANCH}/FORK_VERSION"


def _request(url: str, timeout: int = 10) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "stremio-webadmin-fork"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def _remote_version() -> str:
    return _request(FORK_VERSION_URL, timeout=5).decode("utf-8").strip()


def github_version():
    try:
        version = _remote_version()
        return {
            "available": bool(version),
            "version": version or None,
            "repositoryUrl": SOURCE_REPO,
            "branch": SOURCE_BRANCH,
            "source": "fork",
        }
    except Exception:
        return {
            "available": False,
            "version": None,
            "repositoryUrl": SOURCE_REPO,
            "branch": SOURCE_BRANCH,
            "source": "fork",
        }


def update_worker():
    result = {"status": "failed", "finishedAt": datetime.now(UTC).isoformat()}
    try:
        with legacy.UPDATE_LOCK:
            legacy.STATE.mkdir(parents=True, exist_ok=True)
            payload = _request(SOURCE_ARCHIVE, timeout=60)
            with tempfile.TemporaryDirectory(dir=legacy.STATE) as td:
                root = Path(td).resolve()
                with tarfile.open(fileobj=BytesIO(payload), mode="r:gz") as tar:
                    for member in tar.getmembers():
                        target = (root / member.name).resolve()
                        if root not in target.parents and target != root:
                            raise RuntimeError("unsafe fork source archive")
                    tar.extractall(td, filter="data")

                dirs = [p for p in root.iterdir() if p.is_dir()]
                if len(dirs) != 1:
                    raise RuntimeError("invalid fork source archive")
                source = dirs[0]

                required = [
                    source / "Dockerfile",
                    source / "compose.yaml",
                    source / "FORK_VERSION",
                    source / "docker/webadmin_entrypoint.py",
                    source / "webadmin",
                ]
                missing = [str(p.relative_to(source)) for p in required if not p.exists()]
                if missing:
                    raise RuntimeError(
                        "fork archive is missing protected WebAdmin files: " + ", ".join(missing)
                    )

                version = (source / "FORK_VERSION").read_text(encoding="utf-8").strip()
                if not version:
                    raise RuntimeError("FORK_VERSION is empty")

                # Build exactly the fork archive. No upstream download and no source-code patching.
                legacy.client().images.build(
                    path=str(source), tag=legacy.IMAGE, rm=True, pull=True
                )

            result = {
                "status": "succeeded",
                "finishedAt": datetime.now(UTC).isoformat(),
                "version": version,
                "repositoryUrl": SOURCE_REPO,
                "branch": SOURCE_BRANCH,
                "message": (
                    "Fork image built successfully. Recreate stremio-libtorrent-server "
                    "to activate the new image."
                ),
            }
    except Exception as exc:
        result["message"] = str(exc)
    (legacy.STATE / "update-result.json").write_text(json.dumps(result, indent=2))


# Existing POST /api/update resolves update_worker from the legacy module globals
# at call time, so replacing it here changes update behaviour without duplicating
# the route or modifying the large WebAdmin application module.
legacy.update_worker = update_worker

# Replace only the version route so the UI shows the fork release, not the core
# package version inherited from andrewhack/stremio-libtorrent-server.
legacy.app.router.routes = [
    route for route in legacy.app.router.routes if getattr(route, "path", None) != "/api/github-version"
]
legacy.app.add_api_route("/api/github-version", github_version, methods=["GET"])

app = legacy.app
