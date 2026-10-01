from __future__ import annotations

from stremiosrv.playback_sessions import PlaybackRegistry


def test_source_client_lifecycle_and_bytes():
    now = [100.0]
    registry = PlaybackRegistry(clock=lambda: now[0], active_window=15, retention=120)
    sid = registry.open_source("A" * 40, 3, "Mozilla/5.0")
    registry.note_bytes(sid, 4096)

    snap = registry.snapshot()
    assert len(snap["active"]) == 1
    row = snap["active"][0]
    assert row["infoHash"] == ("a" * 40)
    assert row["fileIdx"] == 3
    assert row["client"] == "browser"
    assert row["bytesServed"] == 4096
    assert row["state"] == "PLAYING"

    registry.close_source(sid)
    assert registry.snapshot()["active"] == []
    assert registry.snapshot()["sessions"][0]["state"] == "ENDED"


def test_ffmpeg_source_read_is_internal_not_user_playback():
    registry = PlaybackRegistry(clock=lambda: 100.0)
    sid = registry.open_source("b" * 40, 0, "Lavf/61.1.100")
    registry.note_bytes(sid, 1024)
    snap = registry.snapshot()
    assert snap["sessions"][0]["client"] == "ffmpeg"
    assert snap["sessions"][0]["state"] == "PLAYING"
    assert snap["sessions"][0]["active"] is False
    assert snap["active"] == []


def test_hls_job_correlates_client_to_source_and_expires():
    now = [100.0]
    registry = PlaybackRegistry(clock=lambda: now[0], active_window=15, retention=120)
    sid = registry.register_hls_job("job-1", "c" * 40, 2, "Mozilla/5.0")
    registry.touch_hls("job-1", "Mozilla/5.0")

    row = registry.snapshot()["active"][0]
    assert row["sessionId"] == sid
    assert row["kind"] == "hls"
    assert row["jobId"] == "job-1"
    assert row["infoHash"] == "c" * 40
    assert row["state"] == "PLAYING"

    now[0] += 16
    assert registry.snapshot()["active"] == []
    registry.end_hls("job-1")
    assert registry.snapshot()["sessions"][0]["state"] == "ENDED"


def test_registry_prunes_old_sessions():
    now = [100.0]
    registry = PlaybackRegistry(clock=lambda: now[0], active_window=5, retention=10)
    registry.open_source("d" * 40, 0, "Stremio")
    now[0] += 11
    snap = registry.snapshot()
    assert snap["sessions"] == []
    assert snap["active"] == []
