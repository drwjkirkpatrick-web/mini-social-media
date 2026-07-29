import os
import pytest
from config import Config, get_config


def test_config_defaults():
    cfg = Config()
    assert cfg.max_file_size_mb == 10
    assert "jpg" in cfg.allowed_photo_extensions
    assert cfg.rate_limit_login_attempts == 10
    assert cfg.feed_default_limit == 50


def test_config_env_override(monkeypatch):
    monkeypatch.setenv("MINI_SOCIAL_MAX_FILE_MB", "5")
    monkeypatch.setenv("MINI_SOCIAL_FEED_LIMIT", "25")
    cfg = Config.from_env()
    assert cfg.max_file_size_mb == 5
    assert cfg.feed_default_limit == 25


def test_config_asdict():
    cfg = Config()
    d = cfg.__dataclass_fields__
    assert "database_path" in d
    assert "secret_key" in d
