import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "app.db"


@dataclass(frozen=True)
class AppConfig:
    secret_key: str
    sqlalchemy_database_uri: str
    sqlalchemy_track_modifications: bool = False
    room_name_retries: int = 100

    def as_flask_mapping(self) -> dict[str, str | bool | int]:
        return {
            "SECRET_KEY": self.secret_key,
            "SQLALCHEMY_DATABASE_URI": self.sqlalchemy_database_uri,
            "SQLALCHEMY_TRACK_MODIFICATIONS": self.sqlalchemy_track_modifications,
            "ROOM_NAME_RETRIES": self.room_name_retries,
        }


def load_config(environ: dict[str, str] | None = None) -> AppConfig:
    source = environ if environ is not None else os.environ
    secret_key = source.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is required")

    database_url = source.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    room_name_retries = int(source.get("ROOM_NAME_RETRIES", "100"))
    if room_name_retries < 1:
        raise RuntimeError("ROOM_NAME_RETRIES must be a positive integer")

    return AppConfig(
        secret_key=secret_key,
        sqlalchemy_database_uri=database_url,
        room_name_retries=room_name_retries,
    )
