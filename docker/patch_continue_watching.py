#!/usr/bin/env python3
"""Patch the bundled Stremio Web Continue Watching poster click.

The upstream ContinueWatchingItem renders LibItem/MetaItem.  MetaItem prefers
metaDetailsStreams over deepLinks.player for the poster href, while its explicit
Play action already uses deepLinks.player.  For Continue Watching we want the
poster to use the Core-provided player deep link so Core can restore both the
selected stream and libraryItem.state.timeOffset.

This operates on the bundled, minified web build at image start.  It is deliberately
fail-closed: exactly one known MetaItem precedence expression must be found, otherwise
no JavaScript is changed.
"""
from __future__ import annotations

import pathlib
import re
import sys

BUILD = pathlib.Path("/srv/stremio-server/build")
MARKER = "stremio-webadmin: continue-watching-player-first"

# Terser keeps these property names. Find compact ternaries and then validate the
# property order instead of pinning minified variable/operator spelling.
PATTERN = re.compile(
    r"(?P<obj>[A-Za-z_$][\\w$]*)\\?(?P<body>[^;{}]{1,900}?):null"
)


def patch_text(text: str) -> tuple[str, int]:
    if MARKER in text:
        return text, 0

    matches = []
    for candidate in PATTERN.finditer(text):
        body = candidate.group("body")
        a = body.find(".metaDetailsStreams")
        b = body.find(".metaDetailsVideos")
        c = body.find(".player")
        if a >= 0 and b > a and c > b:
            matches.append(candidate)
    if len(matches) != 1:
        return text, -len(matches)

    m = matches[0]
    old = m.group(0)
    # Swap every streams/player property inside this one precedence expression:
    # typeof checks and returned values both need to move together.
    token = "__CW_PLAYER_TOKEN__"
    new = old.replace(".metaDetailsStreams", "." + token)
    new = new.replace(".player", ".metaDetailsStreams")
    new = new.replace("." + token, ".player")
    # A JS comment is safe between statements and makes the patch idempotent.
    replacement = new
    return text[:m.start()] + replacement + text[m.end():] + "\n/* " + MARKER + " */\n", 1


def main() -> int:
    files = sorted(BUILD.rglob("scripts/main.js"))
    if len(files) != 1:
        print(f"[web-player] continue-watching patch skipped: main.js count={len(files)}")
        return 0

    path = files[0]
    text = path.read_text(encoding="utf-8")
    patched, status = patch_text(text)
    if status == 1:
        path.write_text(patched, encoding="utf-8")
        print(f"[web-player] continue-watching poster -> Core player deep link ({path})")
    elif status == 0:
        print("[web-player] continue-watching patch already applied")
    else:
        print(f"[web-player] continue-watching patch skipped: candidate count={-status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
