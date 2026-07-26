from ghost_game.extensions import db
from ghost_game.models import Player, Room
from ghost_game.game_types import GameType


def test_create_room_rejects_unknown_game(client):
    response = client.post("/api/rooms", json={"game": "unknown"})
    assert response.status_code == 400


def test_create_room_uses_multiword_name(client):
    response = client.post("/api/rooms", json={"game": "ghost"})
    assert response.status_code == 201
    room_name = response.get_json()["room"]
    parts = room_name.split("-")
    assert len(parts) == 3
    assert all(parts)


def test_create_room_uses_configured_room_name_words(client):
    client.application.config["ROOM_NAME_WORDS"] = ("temperate", "normal", "solder")
    response = client.post("/api/rooms", json={"game": "ghost"})
    assert response.status_code == 201
    room_name = response.get_json()["room"]
    parts = room_name.split("-")
    assert len(parts) == 3
    assert set(parts) == {"temperate", "normal", "solder"}


def test_create_room_route_accepts_valid_enum(client):
    response = client.post("/api/rooms", json={"game": GameType.RANWORDS.value})
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["game"] == GameType.RANWORDS.value


def test_protected_action_requires_player_token(client):
    create_response = client.post("/api/rooms", json={"game": GameType.RANWORDS.value})
    room_name = create_response.get_json()["room"]
    response = client.post(
        f"/api/rooms/{room_name}/actions",
        json={"action": "message", "payload": {"msg": "hello"}},
    )
    assert response.status_code == 400


def test_start_route_validates_token_membership(client):
    create_response = client.post("/api/rooms", json={"game": GameType.GHOST.value})
    room_name = create_response.get_json()["room"]
    with client.application.app_context():
        room = Room.query.filter_by(name=room_name).first()
        other_room = Room(name="other-mini-anchor", game=GameType.GHOST.value, state="{}")
        db.session.add(other_room)
        db.session.add(Player(token="token-1", room_name=room.name))
        db.session.add(Player(token="token-2", room_name=other_room.name))
        db.session.commit()

    response = client.post(f"/api/rooms/{room_name}/start", json={"player_token": "token-2"})
    assert response.status_code == 403
