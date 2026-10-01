"""Regression tests for the bundled Stremio Web Continue Watching patch."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "docker" / "patch_continue_watching.py"
_SPEC = importlib.util.spec_from_file_location("patch_continue_watching", _PATH)
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MOD)


def test_meta_item_precedence_is_changed_to_player_first():
    source = (
        'x=e?"string"==typeof e.metaDetailsStreams?e.metaDetailsStreams:'
        '"string"==typeof e.metaDetailsVideos?e.metaDetailsVideos:'
        '"string"==typeof e.player?e.player:null:null;'
    )
    patched, status = _MOD.patch_text(source)
    assert status == 1
    assert patched.index(".player") < patched.index(".metaDetailsStreams")
    assert patched.count(".player") == 2
    assert patched.count(".metaDetailsStreams") == 2


def test_patch_is_fail_closed_when_expression_is_ambiguous():
    expr = (
        'x=e?"string"==typeof e.metaDetailsStreams?e.metaDetailsStreams:'
        '"string"==typeof e.metaDetailsVideos?e.metaDetailsVideos:'
        '"string"==typeof e.player?e.player:null:null;'
    )
    patched, status = _MOD.patch_text(expr + expr)
    assert status == -2
    assert patched == expr + expr


def test_patch_is_idempotent():
    source = (
        'x=e?"string"==typeof e.metaDetailsStreams?e.metaDetailsStreams:'
        '"string"==typeof e.metaDetailsVideos?e.metaDetailsVideos:'
        '"string"==typeof e.player?e.player:null:null;'
    )
    once, status = _MOD.patch_text(source)
    assert status == 1
    twice, status = _MOD.patch_text(once)
    assert status == 0
    assert twice == once
