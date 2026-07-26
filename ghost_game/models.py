from datetime import datetime, UTC

from .extensions import db


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4), unique=True, nullable=False)
    game = db.Column(db.String(32), nullable=False)
    state = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    players = db.relationship("Player", backref="room", lazy=True, cascade="all, delete-orphan")


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    room_name = db.Column(db.String(4), db.ForeignKey("room.name"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))


class RoomEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(4), db.ForeignKey("room.name"), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    recipient_token = db.Column(db.String(64), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
