import json
import random
from typing import Any
from uuid import uuid4

from flask import abort, current_app
from sqlalchemy.exc import IntegrityError

import words
from ghost_game.extensions import db
from ghost_game.game_types import GameType
from ghost_game.models import Player, Room, RoomEvent

def _random_room_name() -> str:
    """Generate a multi-word room name candidate.

    Returns:
        str: A lowercase, hyphen-joined room identifier.
    """
    first, second, third = random.sample(words.words, 3)
    return f"{first.lower()}-{second.lower()}-{third.lower()}"


def create_room(game: GameType) -> Room:
    """Create and persist a room for the selected game type.

    Args:
        game: The requested game type.

    Returns:
        Room: The created room record.

    Raises:
        RuntimeError: If a unique room name cannot be allocated.
    """
    max_room_name_retries = int(current_app.config["ROOM_NAME_RETRIES"])
    for _ in range(max_room_name_retries):
        room = Room(name=_random_room_name(), game=game.value, state="{}")
        db.session.add(room)
        try:
            db.session.commit()
            return room
        except IntegrityError:
            db.session.rollback()
    raise RuntimeError("Could not allocate a unique room name")


def get_room_or_404(room_name: str) -> Room:
    """Fetch a room by name or abort with a 404.

    Args:
        room_name: Room identifier.

    Returns:
        Room: Matching room model.
    """
    room = Room.query.filter_by(name=room_name).first()
    if room is None:
        abort(404, "Room not found")
    return room


def ensure_player_in_room(room_name: str, player_token: str) -> Player:
    """Validate that a player token belongs to the room.

    Args:
        room_name: Room identifier.
        player_token: Player authentication token.

    Returns:
        Player: The matching player model.
    """
    player = Player.query.filter_by(room_name=room_name, token=player_token).first()
    if player is None:
        abort(403, "Invalid player token for this room")
    return player


def get_or_create_player(room: Room, player_token: str | None = None) -> Player:
    """Get an existing room player by token or create a new player.

    Args:
        room: Room model.
        player_token: Optional existing player token.

    Returns:
        Player: Existing or newly created player.
    """
    if player_token:
        existing = Player.query.filter_by(token=player_token, room_name=room.name).first()
        if existing is not None:
            return existing
    player = Player(token=uuid4().hex, room_name=room.name)
    db.session.add(player)
    db.session.commit()
    return player


def list_room_players(room_name: str) -> list[Player]:
    """Return all players in a room in insertion order.

    Args:
        room_name: Room identifier.

    Returns:
        list[Player]: Ordered list of players in the room.
    """
    return Player.query.filter_by(room_name=room_name).order_by(Player.id.asc()).all()


def emit_event(room_name: str, event_type: str, payload: dict[str, Any], recipient_token: str | None = None) -> RoomEvent:
    """Persist a room event for broadcast or a specific recipient.

    Args:
        room_name: Room identifier.
        event_type: Event type string.
        payload: JSON-serializable event payload.
        recipient_token: Optional recipient-specific player token.

    Returns:
        RoomEvent: The persisted room event model.
    """
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
    """Fetch room events after a cursor for a player or broadcast stream.

    Args:
        room_name: Room identifier.
        since_id: Exclusive event ID cursor.
        player_token: Optional player token for recipient-scoped events.

    Returns:
        list[dict[str, Any]]: Serialized events ordered by event ID.
    """
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
    """Load the stored room state payload.

    Args:
        room: Room model with serialized state.

    Returns:
        dict[str, Any]: Deserialized state object.
    """
    return json.loads(room.state or "{}")


def save_room_state(room: Room, state: dict[str, Any]) -> None:
    """Persist room state as serialized JSON.

    Args:
        room: Room model to update.
        state: State object to store.
    """
    room.state = json.dumps(state)
    db.session.commit()


def start_ghost_game(room: Room) -> None:
    """Initialize and emit start events for a ghost game room.

    Args:
        room: Room to initialize.
    """
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
    """Initialize and emit start events for a random words game.

    Args:
        room: Room to initialize.
    """
    word = random.choice(words.words)
    emit_event(room.name, "word", {"word": word})
    emit_event(room.name, "begin_game", {"message": "Begin the game"})


def start_blackmaria_game(room: Room, n_players: int) -> None:
    """Initialize blackmaria game state and deal starting hands.

    Args:
        room: Room to initialize.
        n_players: Number of active players.
    """
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
    """Submit a chat message for the random words game.

    Args:
        room: Room receiving the message.
        msg: Message content.
    """
    emit_event(room.name, "message", {"msg": msg})


def submit_blackmaria_card(room: Room, payload: dict[str, Any]) -> None:
    """Submit a card-play event for blackmaria.

    Args:
        room: Room receiving the action.
        payload: Card-play payload.
    """
    emit_event(room.name, "card_played", payload)


def submit_blackmaria_pass_cards(room: Room, payload: dict[str, Any]) -> None:
    """Submit a pass-cards event and route cards to next player.

    Args:
        room: Room receiving the action.
        payload: Payload containing sender and cards.
    """
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
