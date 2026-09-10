"""Load administrator overrides from a volume owned by the separate Web Admin."""

from __future__ import annotations

import json
import os
from pathlib import Path

from stremiosrv.config import Settings


def apply_external_overrides(settings: Settings) -> None:
    path = Path(os.getenv("STREMIOSRV_EXTERNAL_CONFIG", "/config/admin-settings.json"))
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        allowed = {key: value for key, value in raw.items() if key in Settings.model_fields}
        validated = Settings(**allowed)
    except (OSError, ValueError, TypeError):
        return
    for key in allowed:
        setattr(settings, key, getattr(validated, key))
