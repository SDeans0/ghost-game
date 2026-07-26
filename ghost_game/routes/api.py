from flask import Blueprint, jsonify, request, url_for

from ghost_game.services.game_service import (
    create_room,
    ensure_player_in_room,
    get_or_create_player,
    get_room_or_404,
    poll_events,
    start_blackmaria_game,
    start_ghost_game,
    start_ranwords_game,
    submit_blackmaria_card,
    submit_blackmaria_pass_cards,
    submit_ranwords_message,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.post("/rooms")
def create_room_route():
    data = request.get_json(silent=True) or {}
    game = data.get("game")
    room = create_room(game)
    return (
        jsonify({
            "room": room.name,
            "game": room.game,
            "url": url_for("pages.start_game", game=room.game, room=room.name),
        }),
        201,
    )


@api_bp.post("/rooms/<room>/join")
def join_room_route(room: str):
    room_obj = get_room_or_404(room)
    data = request.get_json(silent=True) or {}
    player = get_or_create_player(room_obj, data.get("player_token"))
    return jsonify({"room": room_obj.name, "game": room_obj.game, "player_token": player.token})


@api_bp.get("/rooms/<room>/events")
def poll_room_events(room: str):
    get_room_or_404(room)
    try:
        since_id = int(request.args.get("since_id", default="0"))
    except ValueError:
        return jsonify({"error": "since_id must be an integer"}), 400

    player_token = request.args.get("player_token")
    events = poll_events(room, since_id, player_token)
    return jsonify({"events": events})


@api_bp.post("/rooms/<room>/start")
def start_room_game(room: str):
    room_obj = get_room_or_404(room)
    data = request.get_json(silent=True) or {}
    player_token = data.get("player_token")

    if player_token:
        ensure_player_in_room(room_obj.name, player_token)

    if room_obj.game == "ghost":
        start_ghost_game(room_obj)
    elif room_obj.game == "ranwords":
        start_ranwords_game(room_obj)
    elif room_obj.game == "blackmaria":
        start_blackmaria_game(room_obj, int(data.get("n_players", 0)))

    return jsonify({"ok": True})


@api_bp.post("/rooms/<room>/actions")
def room_actions(room: str):
    room_obj = get_room_or_404(room)
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    payload = data.get("payload", {})
    player_token = data.get("player_token")

    if not player_token:
        return jsonify({"error": "player_token is required"}), 400

    ensure_player_in_room(room_obj.name, player_token)

    if room_obj.game == "ranwords" and action == "message":
        submit_ranwords_message(room_obj, payload.get("msg", ""))
    elif room_obj.game == "blackmaria" and action == "card_played":
        submit_blackmaria_card(room_obj, payload)
    elif room_obj.game == "blackmaria" and action == "pass_cards":
        submit_blackmaria_pass_cards(room_obj, payload)
    else:
        return jsonify({"error": "Unsupported action"}), 400

    return jsonify({"ok": True})
