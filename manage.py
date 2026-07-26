from ghost_game import create_app
from ghost_game.extensions import db
from ghost_game.models import Player, Room, RoomEvent


app = create_app()


@app.shell_context_processor
def shell_context():
    return {
        "db": db,
        "Room": Room,
        "Player": Player,
        "RoomEvent": RoomEvent,
    }
