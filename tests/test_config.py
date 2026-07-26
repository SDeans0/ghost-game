import pytest

from ghost_game.config import load_config


def test_load_config_requires_secret_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        load_config({})


def test_load_config_uses_provided_values():
    config = load_config({"SECRET_KEY": "abc", "DATABASE_URL": "sqlite:///custom.db"})
    assert config.secret_key == "abc"
    assert config.sqlalchemy_database_uri == "sqlite:///custom.db"
