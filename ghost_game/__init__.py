from pathlib import Path

from flask import Flask

from .config import Config
from .extensions import db, migrate
from .routes.api import api_bp
from .routes.pages import pages_bp


BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    return app
