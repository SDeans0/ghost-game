import json

import pytest
from werkzeug.exceptions import HTTPException

from ghost_game.extensions import db
from ghost_game.game_types import GameType
from ghost_game.models import Player, Room, RoomEvent
from ghost_game.services.game_service import save_room_state, submit_blackmaria_pass_cards


def _seed_blackmaria_room() -> Room:
    room = Room(name="test-blackmaria-room", game=GameType.BLACKMARIA.value, state="{}")
    players = [Player(token="token-a", room_name=room.name), Player(token="token-b", room_name=room.name), Player(token="token-c", room_name=room.name)]
    db.session.add(room)
    db.session.add_all(players)
    db.session.commit()
    save_room_state(room, {"n_players": 3, "players": [player.token for player in players]})
    return room


def test_submit_blackmaria_pass_cards_uses_server_state_player_count(app):
    with app.app_context():
        room = _seed_blackmaria_room()
        submit_blackmaria_pass_cards(
            room,
            {"player": 2, "n_players": 99, "cards": [{"suit": "hearts", "value": 7}]},
        )

        events = RoomEvent.query.order_by(RoomEvent.id.asc()).all()
        assert len(events) == 2
        receive_event, passed_event = events
        assert receive_event.event_type == "receive_cards"
        assert receive_event.recipient_token == "token-a"
        assert json.loads(receive_event.payload) == {"passing_cards": [{"suit": "hearts", "value": 7}]}
        assert passed_event.event_type == "passed_cards"
        assert passed_event.recipient_token is None
        assert json.loads(passed_event.payload) == {"sender": 2}


def test_submit_blackmaria_pass_cards_rejects_sender_out_of_range(app):
    with app.app_context():
        room = _seed_blackmaria_room()
        with pytest.raises(HTTPException) as exc_info:
            submit_blackmaria_pass_cards(room, {"player": 3, "n_players": 3, "cards": []})
        assert exc_info.value.code == 400
