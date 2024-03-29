from flask import Flask, render_template, request,redirect,url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import flask_sqlalchemy as sql

import random, string
import words
import time
import logging

logger = logging.getLogger()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/NomadSam/Desktop/GitHub/ghost-game/test.db'
socketio = SocketIO(app)
db = sql.SQLAlchemy(app)

##### Database

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4), unique=True, nullable=False)
    Users = db.relationship('User', backref='room', lazy=True)
    def __init__(self,name):
        self.name = name
    def __repr__(self):
        return '<Room %r>' % self.name

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.String(32),nullable=False)
    room_name = db.Column(db.String(4), db.ForeignKey('room.name'),
        nullable=False,unique=False)
    def __init__(self,sid,room_name):
        self.sid = sid
        self.room_name = room_name
    def __repr__(self):
        return '<User %r>' % self.sid

##### Application routes

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/<game>/<room>')
def start_game(game,room):
    exists = Room.query.filter_by(name=room).first()
    if exists is not None:
        return render_template(game+'_page.html')
    else:
        return redirect(url_for('index'))

##### Socketio responses

@socketio.on('newGame')
def new_game(data):
    room_name = ''.join(random.choice(string.ascii_lowercase) for i in range(4))
    room = Room(room_name)
    db.session.add(room)
    db.session.commit()
    print(url_for('start_game',game=data['game'],room=room_name))
    emit('redirect', {'url': url_for('start_game',game=data['game'],room=room_name)})

@socketio.on('joinGame',namespace='/blackmaria')
@socketio.on('joinGame',namespace='/ranwords')
@socketio.on('joinGame',namespace='/ghost')
def join_game(data):
    room = data['url'].replace('/','')[-4:]
    join_room(room)
    db.session.add(User(request.sid,room))
    db.session.commit()
    emit('joined room',{'room':room},room=request.sid)

@socketio.on('start',namespace='/ghost')
def start_game(game_data):
    '''Starts the game'''
    word = random.choice(words.words)
    room = game_data['room']
    print(game_data)
    players = User.query.filter_by(room_name=room).all()
    random.shuffle(players)
    ghost = players.pop()
    for player in players:
        emit('word',{'word':word},room=player.sid)
    emit('word',{'word':'You are the ghost!'},room=ghost.sid)
    emit('begin game',{'message':'Begin the game'},room=room)

@socketio.on('start',namespace='/ranwords')
def start_game(game_data):
    '''Starts the game'''
    word = random.choice(words.words)
    room = game_data['room']
    print(game_data)
    emit('word',{'word':word},room=room)
    emit('begin game',{'message':'Begin the game'},room=room)

@socketio.on('start',namespace='/blackmaria')
def start_game(game_data):
    '''Starts the game'''
    room = User.query.filter_by(room_name=game_data['room']).all()
    if len(room) >= game_data['n_players']:
        players = room[:game_data['n_players']]
        deck = [{'suit':suit,'value':value} for suit in ['clubs','spades','diamonds','hearts'] for value in range(2,15)]
        if game_data['n_players'] == 3:
            deck = deck[1:]
        hand_size = len(deck)//game_data['n_players']
        random.shuffle(deck)
        for index,player in enumerate(players):
            hand = deck[:hand_size]
            deck = deck[hand_size:]
            emit('begin game',{'hand':hand,'player':index,'n_players':game_data['n_players']},room=player.sid)
    else:
        emit('too few players',room=request.sid)

@socketio.on('message',namespace='/ranwords')
def message(data):
    '''Reflects a message to the scratchpad'''
    emit('message',{'msg':data['msg']},room=data['room'])

@socketio.on('card played',namespace='/blackmaria')
def card_played(data):
    emit('card played',data,room=data['room'])

@socketio.on('pass cards',namespace='/blackmaria')
def pass_cards(data):
    room = User.query.filter_by(room_name=data['room']).all()
    sender = int(data['player'])
    receiver = (sender +1) % int(data['n_players'])
    emit('receive cards',{'passing_cards':data['cards']},room=room[receiver].sid)
    time.sleep(0.25)
    emit('passed cards',{'sender':sender},room=data['room'])


@socketio.on('connect')
def connect():
    print('Client connected')

@socketio.on('disconnect')
@socketio.on('disconnect',namespace='/blackmaria')
@socketio.on('disconnect',namespace='/ranwords')
@socketio.on('disconnect',namespace='/ghost')
def disconnect():
    logger.log(1, f"Player disconnected: {request.sid}")
    player = User.query.filter_by(sid=request.sid).first()
    if player is not None:
        db.session.delete(player)
        db.session.commit()
        room = Room.query.filter_by(name=player.room_name).first()
        if room.Users == []:
            db.session.delete(room)
            db.session.commit()

if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0',port=8000)
