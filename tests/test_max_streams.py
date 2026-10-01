"""max_streams: the serve route refuses a new playback once the concurrent-stream cap is reached."""
from fastapi.testclient import TestClient

from stremiosrv.app import create_app
from stremiosrv.config import Settings


class _H:
    def has_metadata(self) -> bool:
        return True

    def is_active(self) -> bool:
        return False  # the requested torrent is NOT already being streamed


class _Eng:
    def get(self, ih):
        return _H()

    def add(self, ih, trackers=None):
        return _H()

    def active_torrent_count(self) -> int:
        return 1  # one other torrent is already streaming


def test_serve_rejects_when_at_max_streams() -> None:
    app = create_app(settings=Settings(max_streams=1), engine=_Eng())
    resp = TestClient(app).get("/aabbccddeeff/0")
    assert resp.status_code == 503
    assert b"max concurrent streams" in resp.content


def test_active_json_marks_open_stream_as_direct_without_ffmpeg() -> None:
    class ActiveH:
        def status(self):
            class S:
                info_hashes = type("IH", (), {"v1": "a" * 40})()
                download_rate = 0
                upload_rate = 0
                num_peers = 0
                total_done = 1024
                total_upload = 0
                progress = 1.0
            return S()

        def torrent_file(self):
            return type("TI", (), {"name": lambda self: "movie.mkv"})()

        def is_active(self):
            return True

        def focused_index(self):
            return 0

        def is_paused(self):
            return False

    class ActiveEng:
        def active(self):
            return [ActiveH()]

    app = create_app(settings=Settings(), engine=ActiveEng())
    resp = TestClient(app).get("/active.json")
    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["active"] is True
    assert row["playbackMode"] == "direct"
    assert row["focusedFileIdx"] == 0
