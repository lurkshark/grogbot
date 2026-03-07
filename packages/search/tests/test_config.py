from __future__ import annotations

from pathlib import Path

from grogbot_search.config import CONFIG_ENV_VAR, load_config


def test_load_config_env_override(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    db_path = tmp_path / "data" / "search.db"
    config_path.write_text(f"[search]\ndb_path = '{db_path}'\n")
    monkeypatch.setenv(CONFIG_ENV_VAR, str(config_path))

    config = load_config()

    assert config.db_path == db_path
    assert db_path.parent.exists()


def test_load_config_path_argument(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_ENV_VAR, raising=False)
    config_path = tmp_path / "config.toml"
    db_path = tmp_path / "other" / "search.db"
    config_path.write_text(f"[search]\ndb_path = '{db_path}'\n")

    config = load_config(config_path)

    assert config.db_path == db_path
    assert db_path.parent.exists()
