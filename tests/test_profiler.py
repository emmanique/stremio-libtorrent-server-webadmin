import json

import stremiosrv.transcode.profiler as profiler


def _config(tmp_path, profile):
    path = tmp_path / "admin-settings.json"
    path.write_text(
        json.dumps(
            {"transcoding_profile": profile}
        ),
        encoding="utf-8",
    )
    return path


def test_persisted_full_vaapi_profile_is_authoritative(
    tmp_path,
    monkeypatch,
):
    path = _config(
        tmp_path,
        "vaapi-full-h264",
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(path),
    )

    monkeypatch.setenv(
        "TRANSCODING_HWACCEL",
        "vaapi",
    )
    monkeypatch.setenv(
        "TRANSCODING_VIDEO_CODEC",
        "h264_vaapi",
    )
    monkeypatch.setenv(
        "TRANSCODING_HW_DECODE",
        "false",
    )

    assert (
        profiler.detect_profile()
        == "vaapi-full-h264"
    )


def test_persisted_full_hevc_profile_is_authoritative(
    tmp_path,
    monkeypatch,
):
    path = _config(
        tmp_path,
        "vaapi-full-hevc",
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(path),
    )

    monkeypatch.setenv(
        "TRANSCODING_HWACCEL",
        "vaapi",
    )
    monkeypatch.setenv(
        "TRANSCODING_VIDEO_CODEC",
        "h264_vaapi",
    )
    monkeypatch.setenv(
        "TRANSCODING_HW_DECODE",
        "false",
    )

    assert (
        profiler.detect_profile()
        == "vaapi-full-hevc"
    )


def test_preserve_is_not_a_hardware_backend(
    tmp_path,
    monkeypatch,
):
    path = _config(
        tmp_path,
        "preserve",
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(path),
    )

    assert profiler.detect_profile() is None


def test_environment_is_compatibility_fallback(
    tmp_path,
    monkeypatch,
):
    missing = (
        tmp_path
        / "missing-admin-settings.json"
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(missing),
    )

    monkeypatch.setenv(
        "TRANSCODING_HWACCEL",
        "vaapi",
    )
    monkeypatch.setenv(
        "TRANSCODING_VIDEO_CODEC",
        "h264_vaapi",
    )
    monkeypatch.setenv(
        "TRANSCODING_HW_DECODE",
        "false",
    )

    assert (
        profiler.detect_profile()
        == "vaapi-h264"
    )


def test_environment_full_vaapi_fallback(
    tmp_path,
    monkeypatch,
):
    missing = (
        tmp_path
        / "missing-admin-settings.json"
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(missing),
    )

    monkeypatch.setenv(
        "TRANSCODING_HWACCEL",
        "vaapi",
    )
    monkeypatch.setenv(
        "TRANSCODING_VIDEO_CODEC",
        "h264_vaapi",
    )
    monkeypatch.setenv(
        "TRANSCODING_HW_DECODE",
        "true",
    )

    assert (
        profiler.detect_profile()
        == "vaapi-full-h264"
    )


def test_render_node_discovery_is_not_fixed_to_128(
    tmp_path,
    monkeypatch,
):
    missing = (
        tmp_path
        / "missing-admin-settings.json"
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(missing),
    )

    monkeypatch.delenv(
        "TRANSCODING_HWACCEL",
        raising=False,
    )

    monkeypatch.setattr(
        profiler,
        "_vaapi_render_nodes",
        lambda: [
            "/dev/dri/renderD129"
        ],
    )

    monkeypatch.setattr(
        profiler,
        "_nvidia_available",
        lambda: False,
    )

    assert (
        profiler.detect_profile()
        == "vaapi-renderD129"
    )


def test_nvidia_legacy_fallback(
    tmp_path,
    monkeypatch,
):
    missing = (
        tmp_path
        / "missing-admin-settings.json"
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(missing),
    )

    monkeypatch.delenv(
        "TRANSCODING_HWACCEL",
        raising=False,
    )

    monkeypatch.setattr(
        profiler,
        "_vaapi_render_nodes",
        lambda: [],
    )

    monkeypatch.setattr(
        profiler,
        "_nvidia_available",
        lambda: True,
    )

    assert (
        profiler.detect_profile()
        == "nvenc-linux"
    )


def test_full_profile_semantics_are_unambiguous(
    tmp_path,
    monkeypatch,
):
    path = _config(
        tmp_path,
        "vaapi-full-h264",
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(path),
    )

    assert (
        profiler.detect_profile()
        == "vaapi-full-h264"
    )


def test_non_full_profile_semantics_are_unambiguous(
    tmp_path,
    monkeypatch,
):
    path = _config(
        tmp_path,
        "vaapi-h264",
    )

    monkeypatch.setattr(
        profiler,
        "CONFIG_FILE",
        str(path),
    )

    assert (
        profiler.detect_profile()
        == "vaapi-h264"
    )
