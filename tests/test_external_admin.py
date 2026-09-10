import json


def test_external_config_applies_only_known_settings(tmp_path, monkeypatch):
    from stremiosrv.config import Settings
    from stremiosrv.external_config import apply_external_overrides

    path = tmp_path / "admin-settings.json"
    path.write_text(json.dumps({"max_streams": 7, "unknown": "ignored"}))
    monkeypatch.setenv("STREMIOSRV_EXTERNAL_CONFIG", str(path))
    settings = Settings()
    apply_external_overrides(settings)
    assert settings.max_streams == 7
    assert not hasattr(settings, "unknown")


def test_webadmin_has_required_routes():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[1] / "webadmin" / "app.py"
    spec = importlib.util.spec_from_file_location("separate_webadmin", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    app = module.app

    paths = {route.path for route in app.routes}
    assert {"/api/status", "/api/config", "/api/restart", "/api/update", "/api/logs"} <= paths
