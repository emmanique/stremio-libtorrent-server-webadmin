"""Library integration helpers.

The Library addon can learn a cached torrent's IMDb identity from Stremio playback even when the
browser that owns the richer metadata is not the one rendering the catalog. Learned labels then
contain a stable ``metaId`` but may not contain artwork. Stremio's own addon examples use MetaHub
for IMDb poster previews, so add that deterministic fallback at the model boundary while preserving
any poster explicitly stored in the label.
"""
from __future__ import annotations

import re

from stremiosrv.library import addon_model as _addon_model

_METAHUB_POSTER = "https://images.metahub.space/poster/medium/{}/img"
_IMDB_ID = re.compile(r"^tt[0-9]+$")
_ORIGINAL_PREVIEW = _addon_model.preview
_ORIGINAL_META_FOR = _addon_model.meta_for


def _poster_for(entry: dict) -> str:
    label = entry.get("label") or {}
    explicit = str(label.get("poster") or "").strip()
    if explicit:
        return explicit
    meta_id = str(label.get("metaId") or "").split(":", 1)[0]
    return _METAHUB_POSTER.format(meta_id) if _IMDB_ID.fullmatch(meta_id) else ""


def _preview_with_poster(entry: dict) -> dict:
    item = _ORIGINAL_PREVIEW(entry)
    poster = _poster_for(entry)
    if poster:
        item.setdefault("poster", poster)
        item.setdefault("posterShape", "poster")
    return item


def _meta_with_poster(entry: dict) -> dict:
    item = _ORIGINAL_META_FOR(entry)
    poster = _poster_for(entry)
    if poster:
        item.setdefault("poster", poster)
        item.setdefault("posterShape", "poster")
    return item


# addon.py calls these functions through the addon_model module, so patching the two pure rendering
# functions here upgrades catalog/meta output without changing torrent matching or playback logic.
_addon_model.preview = _preview_with_poster
_addon_model.meta_for = _meta_with_poster
