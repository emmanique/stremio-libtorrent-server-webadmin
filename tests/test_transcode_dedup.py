from pathlib import Path

import pytest

from stremiosrv.transcode import converter as mod


class FakeProc:
    created = []

    def __init__(self, argv, stdout=None, stderr=None):
        self.argv = argv
        self.returncode = None
        self.terminated = False
        self.killed = False
        FakeProc.created.append(self)

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


@pytest.fixture(autouse=True)
def fake_popen(monkeypatch):
    FakeProc.created = []
    monkeypatch.setattr(mod.subprocess, "Popen", FakeProc)


@pytest.fixture
def decision():
    return {
        "video": {
            "action": "transcode",
            "codec": "hevc",
        },
        "audio": {
            "action": "copy",
            "codec": "aac",
        },
    }


def test_same_workload_different_job_ids_uses_one_ffmpeg(tmp_path, decision):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    a = c.ensure_job("client-a", "http://example/video.mkv", decision)
    b = c.ensure_job("client-b", "http://example/video.mkv", decision)

    assert len(FakeProc.created) == 1
    assert a == b
    assert c.active_count() == 1


def test_different_media_uses_different_ffmpeg(tmp_path, decision):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    a = c.ensure_job("client-a", "http://example/a.mkv", decision)
    b = c.ensure_job("client-b", "http://example/b.mkv", decision)

    assert len(FakeProc.created) == 2
    assert a != b
    assert c.active_count() == 2


def test_different_decision_is_not_deduplicated(tmp_path, decision):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    other = {
        **decision,
        "video": {
            **decision["video"],
            "scale_width": 1280,
        },
    }

    c.ensure_job("client-a", "http://example/video.mkv", decision)
    c.ensure_job("client-b", "http://example/video.mkv", other)

    assert len(FakeProc.created) == 2
    assert c.active_count() == 2


def test_destroy_one_alias_does_not_stop_shared_encoder(tmp_path, decision):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    c.ensure_job("client-a", "http://example/video.mkv", decision)
    c.ensure_job("client-b", "http://example/video.mkv", decision)

    proc = FakeProc.created[0]

    c.stop("client-a")

    assert proc.terminated is False
    assert c.active_count() == 1

    c.stop("client-b")

    assert proc.terminated is True
    assert c.active_count() == 0


def test_job_file_for_alias_resolves_shared_output(tmp_path, decision):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    root_a = c.ensure_job(
        "client-a",
        "http://example/video.mkv",
        decision,
    )
    root_b = c.ensure_job(
        "client-b",
        "http://example/video.mkv",
        decision,
    )

    assert root_a == root_b

    expected = root_a / "seg0.m4s"

    assert c.job_file("client-a", "seg0.m4s") == expected
    assert c.job_file("client-b", "seg0.m4s") == expected


def test_touch_alias_keeps_shared_workload_alive(tmp_path, decision, monkeypatch):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    now = [100.0]
    monkeypatch.setattr(mod.time, "monotonic", lambda: now[0])

    c.ensure_job("client-a", "http://example/video.mkv", decision)
    c.ensure_job("client-b", "http://example/video.mkv", decision)

    now[0] = 200.0
    c.touch("client-b")

    now[0] = 250.0

    reaped = c.reap_idle(100.0)

    assert reaped == []
    assert c.active_count() == 1


def test_stop_all_terminates_shared_encoder_once(tmp_path, decision):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    c.ensure_job("client-a", "http://example/video.mkv", decision)
    c.ensure_job("client-b", "http://example/video.mkv", decision)

    proc = FakeProc.created[0]

    c.stop_all()

    assert proc.terminated is True
    assert c.active_count() == 0
    assert len(FakeProc.created) == 1


def test_concurrent_same_workload_creates_one_encoder(tmp_path, decision):
    import threading

    c = mod.Converter(str(tmp_path), "vaapi-h264")

    barrier = threading.Barrier(3)
    results = []
    errors = []

    def worker(job_id):
        try:
            barrier.wait()
            results.append(
                c.ensure_job(
                    job_id,
                    "http://example/video.mkv",
                    decision,
                )
            )
        except Exception as exc:
            errors.append(exc)

    a = threading.Thread(target=worker, args=("client-a",))
    b = threading.Thread(target=worker, args=("client-b",))

    a.start()
    b.start()

    barrier.wait()

    a.join(timeout=5)
    b.join(timeout=5)

    assert not a.is_alive()
    assert not b.is_alive()
    assert errors == []

    assert len(FakeProc.created) == 1
    assert len(results) == 2
    assert results[0] == results[1]
    assert c.active_count() == 1


def test_rebinding_job_id_to_new_workload_releases_old_owner(
    tmp_path,
    decision,
):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    c.ensure_job(
        "client-a",
        "http://example/one.mkv",
        decision,
    )

    first = FakeProc.created[0]

    c.ensure_job(
        "client-a",
        "http://example/two.mkv",
        decision,
    )

    assert len(FakeProc.created) == 2

    # Rebinding the final owner must terminate the superseded workload
    # immediately rather than leaving it alive until idle GC.
    assert first.terminated is True
    assert c.active_count() == 1

    # Only the replacement workload remains registered.
    assert len(c._jobs) == 1
    assert len(c._workload_jobs) == 1
    assert c._job_workload["client-a"] in c._jobs

    replacement = FakeProc.created[1]
    assert replacement.terminated is False

    c.stop("client-a")

    assert replacement.terminated is True
    assert c.active_count() == 0


def test_two_clients_destroy_in_reverse_order(tmp_path, decision):
    c = mod.Converter(str(tmp_path), "vaapi-h264")

    c.ensure_job(
        "client-a",
        "http://example/video.mkv",
        decision,
    )
    c.ensure_job(
        "client-b",
        "http://example/video.mkv",
        decision,
    )

    proc = FakeProc.created[0]

    c.stop("client-b")

    assert proc.terminated is False
    assert c.active_count() == 1

    c.stop("client-a")

    assert proc.terminated is True
    assert c.active_count() == 0
