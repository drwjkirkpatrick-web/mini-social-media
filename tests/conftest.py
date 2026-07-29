"""
Pytest fixtures for mini-social-media.
NOTE: Uses :memory: database for tests to avoid side effects.
WHY: Each test gets a clean, fast database.
"""

import pytest
import os
import sys
import tempfile

# Ensure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import app as app_module


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear in-memory rate limit store between tests."""
    import auth
    auth._rate_limit_store.clear()


@pytest.fixture
def test_db(monkeypatch):
    """Create a temp-file database for each test."""
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr(database, "DATABASE_PATH", path)
    database.init_database()
    yield database
    os.unlink(path)


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Flask test client with temp-file DB and temp uploads."""
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr(database, "DATABASE_PATH", path)
    database.init_database()
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setenv("MINI_SOCIAL_DB", path)
    app_module.app.config["TESTING"] = True
    app_module.app.config["WTF_CSRF_ENABLED"] = False
    with app_module.app.test_client() as c:
        yield c
    os.unlink(path)
