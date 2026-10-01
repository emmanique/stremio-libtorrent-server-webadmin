"""Regression tests for the bundled Stremio Web Continue Watching patch."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "docker" / "patch_continue_watching.py"
_SPEC = importlib.util.spec_from_file_location("patch_continue_watching", _PATH)
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MOD)


def test_patch_injects_continue_watching_click_router_only():
    source = 'x=e?"string"==typeof e.metaDetailsStreams?e.metaDetailsStreams:"string"==typeof e.player?e.player:null:null;'
    patched, status = _MOD.patch_text(source)
    assert status == 1
    # The upstream MetaItem precedence must remain byte-for-byte unchanged.
    assert patched.startswith(source)
    assert patched.count(source) == 1
    assert _MOD.MARKER in patched
    assert 'poster-change-cursor' in patched
    assert 'play-icon-layer' in patched
    assert 'stopImmediatePropagation' in patched


def test_router_falls_back_when_no_core_player_overlay_exists():
    patched, status = _MOD.patch_text("bundle;")
    assert status == 1
    # No play overlay => listener returns without preventing normal poster navigation.
    assert 'if(!play)return;' in patched
    # Synthetic click on the existing React play overlay is allowed through.
    assert 'if(t.closest(\'[class*="play-icon-layer"]\'))return;' in patched


def test_patch_is_idempotent():
    once, status = _MOD.patch_text("bundle;")
    assert status == 1
    twice, status = _MOD.patch_text(once)
    assert status == 0
    assert twice == once
