from flask import Blueprint, redirect, render_template, url_for

from ghost_game.models import Room

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
@pages_bp.route("/index")
def index():
    """Render the landing page."""
    return render_template("index.html")


@pages_bp.route("/<game>/<room>")
def start_game(game: str, room: str):
    """Render a game page when the requested room exists.

    Args:
        game: Game identifier from the URL path.
        room: Room identifier from the URL path.
    """
    exists = Room.query.filter_by(name=room, game=game).first()
    if exists is not None:
        return render_template(f"{game}_page.html")
    return redirect(url_for("pages.index"))
