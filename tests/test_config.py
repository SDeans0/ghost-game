import pytest

from ghost_game.config import load_config


def test_load_config_requires_secret_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        load_config({})


def test_load_config_uses_provided_values():
    config = load_config({"SECRET_KEY": "abc", "DATABASE_URL": "sqlite:///custom.db", "ROOM_NAME_RETRIES": "25"})
    assert config.secret_key == "abc"
    assert config.sqlalchemy_database_uri == "sqlite:///custom.db"
    assert config.room_name_retries == 25


def test_load_config_rejects_non_positive_retry_count():
    with pytest.raises(RuntimeError, match="ROOM_NAME_RETRIES"):
        load_config({"SECRET_KEY": "abc", "ROOM_NAME_RETRIES": "0"})


def test_load_config_uses_custom_room_name_words():
    config = load_config({"SECRET_KEY": "abc", "ROOM_NAME_WORDS": "temperate,mini,solder"})
    assert config.room_name_words == ("temperate", "mini", "solder")
