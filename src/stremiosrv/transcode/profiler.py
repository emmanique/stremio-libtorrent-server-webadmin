"""Resolve the effective transcoding execution profile.

The persisted WebAdmin execution profile is authoritative.

Environment variables remain a compatibility fallback for deployments
which do not yet have a persisted transcoding_profile.

Hardware probing is used only for legacy deployments where neither an
explicit profile nor an explicit runtime policy exists.
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
from pathlib import Path


CONFIG_FILE = os.getenv(
    "STREMIOSRV_EXTERNAL_CONFIG",
    "/config/admin-settings.json",
)

KNOWN_PROFILES = {
    "preserve",
    "vaapi-h264",
    "vaapi-hevc",
    "vaapi-full-h264",
    "vaapi-full-hevc",
    "nvenc-h264",
    "nvenc-hevc",
    "cpu-h264",
    "cpu-hevc",
}


def _configured_profile() -> str | None:
    try:
        data = json.loads(
            Path(CONFIG_FILE).read_text(
                encoding="utf-8"
            )
        )
    except (OSError, ValueError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    profile = str(
        data.get("transcoding_profile") or ""
    ).strip().lower()

    if profile in KNOWN_PROFILES:
        return profile

    return None


def _env_true(name: str) -> bool:
    return os.environ.get(
        name,
        "",
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


def _runtime_profile() -> str | None:
    hwaccel = os.environ.get(
        "TRANSCODING_HWACCEL",
        "",
    ).strip().lower()

    codec = os.environ.get(
        "TRANSCODING_VIDEO_CODEC",
        "",
    ).strip().lower()

    hwdecode = _env_true(
        "TRANSCODING_HW_DECODE"
    )

    if hwaccel == "vaapi":
        if codec == "hevc_vaapi":
            return (
                "vaapi-full-hevc"
                if hwdecode
                else "vaapi-hevc"
            )

        return (
            "vaapi-full-h264"
            if hwdecode
            else "vaapi-h264"
        )

    if hwaccel in {"nvenc", "nvidia"}:
        if codec == "hevc_nvenc":
            return "nvenc-hevc"
        return "nvenc-h264"

    if hwaccel in {"cpu", "software"}:
        if codec == "libx265":
            return "cpu-hevc"
        return "cpu-h264"

    if hwaccel in {"none", "disabled"}:
        return None

    return None


def _nvidia_available() -> bool:
    if not shutil.which("nvidia-smi"):
        return False

    try:
        result = subprocess.run(
            ["nvidia-smi", "-L"],
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False

    return (
        result.returncode == 0
        and b"GPU" in result.stdout
    )


def _vaapi_render_nodes() -> list[str]:
    return sorted(
        path
        for path in glob.glob(
            "/dev/dri/renderD*"
        )
        if os.path.exists(path)
    )


def detect_profile() -> str | None:
    # 1. Explicit WebAdmin execution profile.
    configured = _configured_profile()

    if configured:
        # "preserve" means that the Stremio core remains authoritative.
        # It is not itself a hardware acceleration backend.
        if configured == "preserve":
            return None
        return configured

    # 2. Compatibility runtime environment.
    if os.environ.get(
        "TRANSCODING_HWACCEL",
        "",
    ).strip():
        return _runtime_profile()

    # 3. Legacy hardware discovery.
    render_nodes = _vaapi_render_nodes()

    if render_nodes:
        return (
            "vaapi-"
            + os.path.basename(render_nodes[0])
        )

    if _nvidia_available():
        return "nvenc-linux"

    return None
