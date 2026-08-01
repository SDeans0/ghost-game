from pathlib import Path

from flask import Flask

from .config import load_config
from .extensions import db, migrate
from .routes.api import api_bp
from .routes.pages import pages_bp


BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    """Create and configure the Flask application instance.

    Returns:
        Flask: Configured application with extensions and blueprints.
    """
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_mapping(load_config().as_flask_mapping())

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    return app
