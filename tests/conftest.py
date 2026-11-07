import os
import pytest

os.environ.setdefault("IA_SECRET_KEY", "test-secret-key")
os.environ.setdefault("IA_PASSWORD", "test-password")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("GEMINI_MODEL", "test-model")

import db

@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(db.Config, "DB_PATH", tmp_path / "test.db")
