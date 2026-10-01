#!/usr/bin/env python3
"""Patch bundled Stremio Web so the Continue Watching centre Play resumes safely.

Upstream ContinueWatchingItem -> LibItem already creates an onPlayClick handler only
when Core provides deepLinks.player. That handler carries the exact StreamBucket
source and Core resume position. MetaItem's normal poster click instead prefers the
details/streams deep link.

Do not rewrite MetaItem globally and do not change poster/search navigation. Inject one
small capture listener that acts only when the click is inside Continue Watching's
play-icon-layer. The existing React onPlayClick already carries Core's exact
deepLinks.player, so the listener only prevents the parent MetaItem/Button from also
handling that same click and reopening details/streams.
"""
from __future__ import annotations

import pathlib
import sys

BUILD = pathlib.Path("/srv/stremio-server/build")
MARKER = "stremio-webadmin: continue-watching-centre-play"

INJECTION = r"""
;/* stremio-webadmin: continue-watching-centre-play */
(()=>{if(window.__stremioWebadminContinueWatchingCentrePlay)return;
window.__stremioWebadminContinueWatchingCentrePlay=true;
document.addEventListener("click",e=>{
 const t=e.target instanceof Element?e.target:null;if(!t)return;
 const play=t.closest('[class*="play-icon-layer"]');if(!play)return;
 const poster=play.closest('[class*="poster-change-cursor"]');if(!poster)return;
 // Let React's own onPlayClick run; only mark the native event so MetaItem's
 // parent click handler prevents its details/streams navigation.
 e.selectPrevented=true;
},true);})();
"""usr/bin/env python3
"""Patch bundled Stremio Web so the Continue Watching centre Play resumes safely.

Upstream ContinueWatchingItem -> LibItem already creates an onPlayClick handler only
when Core provides deepLinks.player. That handler carries the exact StreamBucket
source and Core resume position. MetaItem's normal poster click instead prefers the
details/streams deep link.

Do not rewrite MetaItem globally and do not change poster/search navigation. Inject one
small capture listener that acts only when the click is inside Continue Watching's
play-icon-layer. The existing React onPlayClick already carries Core's exact
deepLinks.player, so the listener only prevents the parent MetaItem/Button from also
handling that same click and reopening details/streams.
"""
from __future__ import annotations

import pathlib
import sys

BUILD = pathlib.Path("/srv/stremio-server/build")
MARKER = "stremio-webadmin: continue-watching-centre-play"

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
        print(f"[web-player] Continue Watching centre Play uses Core player without parent stream navigation ({path})")
    else:
        print("[web-player] continue-watching patch already applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
