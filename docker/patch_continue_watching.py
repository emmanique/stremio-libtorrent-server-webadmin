#!/usr/bin/env python3
"""Patch bundled Stremio Web so Continue Watching poster clicks resume safely.

Upstream ContinueWatchingItem -> LibItem already creates an onPlayClick handler only
when Core provides deepLinks.player. That handler carries the exact StreamBucket
source and Core resume position. MetaItem's normal poster click instead prefers the
details/streams deep link.

Do not rewrite MetaItem globally. Inject one small capture listener that only acts
on posters carrying MetaItem's poster-change-cursor marker (set by
ContinueWatchingItem). If that item has a play overlay, the poster click is routed
through the existing React play handler. If Core has no player deep link there is no
play overlay, so normal source selection remains the fallback.
"""
from __future__ import annotations

import pathlib
import sys

BUILD = pathlib.Path("/srv/stremio-server/build")
MARKER = "stremio-webadmin: continue-watching-player-click"

INJECTION = r"""
;/* stremio-webadmin: continue-watching-player-click */
(()=>{if(window.__stremioWebadminContinueWatchingPlayerClick)return;
window.__stremioWebadminContinueWatchingPlayerClick=true;
document.addEventListener("click",e=>{
 const t=e.target instanceof Element?e.target:null;if(!t)return;
 if(t.closest('[class*="play-icon-layer"]'))return;
 const p=t.closest('[class*="poster-change-cursor"]');if(!p)return;
 const b=p.closest("a,button");if(!b)return;
 const play=b.querySelector('[class*="play-icon-layer"]');if(!play)return;
 e.preventDefault();e.stopImmediatePropagation();
 play.dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true,view:window}));
},true);})();
"""


def patch_text(text: str) -> tuple[str, int]:
    if MARKER in text:
        return text, 0
    return text + INJECTION, 1


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
        print(f"[web-player] Continue Watching poster uses Core player when available ({path})")
    else:
        print("[web-player] continue-watching patch already applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
