import json
import random
from typing import Any
from uuid import uuid4

from flask import abort
from sqlalchemy.exc import IntegrityError

import words
from ghost_game.extensions import db
from ghost_game.game_types import GameType
from ghost_game.models import Player, Room, RoomEvent

MAX_ROOM_NAME_RETRIES = 5
ROOM_ADJECTIVES = (
    "amber",
    "brisk",
    "calm",
    "frozen",
    "rapid",
    "tempered",
    "vivid",
)
ROOM_SIZES = (
    "mini",
    "micro",
    "small",
    "medium",
    "tall",
    "wide",
)
ROOM_NOUNS = (
    "anchor",
    "delta",
    "harbor",
    "lantern",
    "rocket",
    "solder",
    "thunder",
)


def _random_room_name() -> str:
    return f"{random.choice(ROOM_ADJECTIVES)}-{random.choice(ROOM_SIZES)}-{random.choice(ROOM_NOUNS)}"


def create_room(game: GameType) -> Room:
    for _ in range(MAX_ROOM_NAME_RETRIES):
        room = Room(name=_random_room_name(), game=game.value, state="{}")
        db.session.add(room)
        try:
            db.session.commit()
            return room
        except IntegrityError:
            db.session.rollback()
    raise RuntimeError("Could not allocate a unique room name")


def get_room_or_404(room_name: str) -> Room:
    room = Room.query.filter_by(name=room_name).first()
    if room is None:
        abort(404, "Room not found")
    return room


def ensure_player_in_room(room_name: str, player_token: str) -> Player:
    player = Player.query.filter_by(room_name=room_name, token=player_token).first()
    if player is None:
        abort(403, "Invalid player token for this room")
    return player


def get_or_create_player(room: Room, player_token: str | None = None) -> Player:
    if player_token:
        existing = Player.query.filter_by(token=player_token, room_name=room.name).first()
        if existing is not None:
            return existing
    player = Player(token=uuid4().hex, room_name=room.name)
    db.session.add(player)
    db.session.commit()
    return player


def list_room_players(room_name: str) -> list[Player]:
    return Player.query.filter_by(room_name=room_name).order_by(Player.id.asc()).all()


def emit_event(room_name: str, event_type: str, payload: dict[str, Any], recipient_token: str | None = None) -> RoomEvent:
    event = RoomEvent(
        room_name=room_name,
        event_type=event_type,
        payload=json.dumps(payload),
        recipient_token=recipient_token,
    )
    db.session.add(event)
    db.session.commit()
    return event


def poll_events(room_name: str, since_id: int, player_token: str | None = None) -> list[dict[str, Any]]:
    query = RoomEvent.query.filter(RoomEvent.room_name == room_name, RoomEvent.id > since_id)
    if player_token:
        query = query.filter((RoomEvent.recipient_token.is_(None)) | (RoomEvent.recipient_token == player_token))
    else:
        query = query.filter(RoomEvent.recipient_token.is_(None))

    events = query.order_by(RoomEvent.id.asc()).all()
    return [
        {
            "id": event.id,
            "type": event.event_type,
            "payload": json.loads(event.payload),
        }
        for event in events
    ]


def get_room_state(room: Room) -> dict[str, Any]:
    return json.loads(room.state or "{}")


def save_room_state(room: Room, state: dict[str, Any]) -> None:
    room.state = json.dumps(state)
    db.session.commit()


def start_ghost_game(room: Room) -> None:
    players = list_room_players(room.name)
    if len(players) < 1:
        abort(400, "At least one player is required")
    shuffled = players[:]
    random.shuffle(shuffled)
    ghost = shuffled.pop()
    word = random.choice(words.words)

    for player in shuffled:
        emit_event(room.name, "word", {"word": word}, recipient_token=player.token)
    emit_event(room.name, "word", {"word": "You are the ghost!"}, recipient_token=ghost.token)
    emit_event(room.name, "begin_game", {"message": "Begin the game"})


def start_ranwords_game(room: Room) -> None:
    word = random.choice(words.words)
    emit_event(room.name, "word", {"word": word})
    emit_event(room.name, "begin_game", {"message": "Begin the game"})


def start_blackmaria_game(room: Room, n_players: int) -> None:
    players = list_room_players(room.name)
    if len(players) < n_players:
        abort(400, "There are too few players in the room")

    selected_players = players[:n_players]
    deck = [
        {"suit": suit, "value": value}
        for suit in ["clubs", "spades", "diamonds", "hearts"]
        for value in range(2, 15)
    ]
    if n_players == 3:
        deck = deck[1:]

    hand_size = len(deck) // n_players
    random.shuffle(deck)

    state = {
        "n_players": n_players,
        "players": [player.token for player in selected_players],
    }
    save_room_state(room, state)

    for index, player in enumerate(selected_players):
        hand = deck[:hand_size]
        deck = deck[hand_size:]
        emit_event(
            room.name,
            "begin_game",
            {"hand": hand, "player": index, "n_players": n_players},
            recipient_token=player.token,
        )


def submit_ranwords_message(room: Room, msg: str) -> None:
    emit_event(room.name, "message", {"msg": msg})


def submit_blackmaria_card(room: Room, payload: dict[str, Any]) -> None:
    emit_event(room.name, "card_played", payload)


def submit_blackmaria_pass_cards(room: Room, payload: dict[str, Any]) -> None:
    state = get_room_state(room)
    players = state.get("players", [])
    n_players = int(payload.get("n_players", 0))
    sender = int(payload.get("player", 0))

    if not players or sender >= len(players) or n_players <= 0:
        abort(400, "Game has not started")

    receiver = (sender + 1) % n_players
    receiver_token = players[receiver]
    emit_event(room.name, "receive_cards", {"passing_cards": payload.get("cards", [])}, recipient_token=receiver_token)
    emit_event(room.name, "passed_cards", {"sender": sender})
