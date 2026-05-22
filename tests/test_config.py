import json
import os
from pathlib import Path

from app.config import Config


def test_config_uses_env_var_when_set(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    cfg = Config.load()
    assert cfg.data_dir == tmp_path
    assert cfg.db_path == tmp_path / "dados.db"
    assert cfg.anexos_dir == tmp_path / "anexos"
    assert cfg.backups_dir == tmp_path / "backups"


def test_config_creates_dirs_if_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    Config.load()
    assert (tmp_path / "anexos").is_dir()
    assert (tmp_path / "backups").is_dir()


def test_config_persists_preferences(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    cfg = Config.load()
    cfg.backup_folder = tmp_path / "custom_backups"
    cfg.backup_retention = 50
    cfg.save()

    reloaded = Config.load()
    assert reloaded.backup_folder == tmp_path / "custom_backups"
    assert reloaded.backup_retention == 50


def test_config_persists_sidebar_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    cfg = Config.load()
    assert cfg.sidebar_collapsed is False  # default
    cfg.sidebar_collapsed = True
    cfg.save()
    reloaded = Config.load()
    assert reloaded.sidebar_collapsed is True
