from pathlib import Path

import pytest

from ghost_game import create_app
from ghost_game.extensions import db


@pytest.fixture()
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
