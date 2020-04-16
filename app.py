from flask import Flask, render_template, request,redirect,url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import flask_sqlalchemy as sql

import random, string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
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
    room_name = db.Column(db.Integer, db.ForeignKey('room.name'),
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

@app.route('/<room>')
def ghost(room):
    exists = Room.query.filter_by(name=room).first()
    if exists is not None:
        return render_template('ghost_page.html')
    else:
        return redirect(url_for('index'))

##### Socketio responses

@socketio.on('newGame')
def new_game():
    room_name = ''.join(random.choice(string.ascii_lowercase) for i in range(4))
    room = Room(room_name)
    db.session.add(room)
    db.session.commit()
    print(url_for('ghost',room=room_name))
    emit('redirect', {'url': url_for('ghost',room=room_name)})

@socketio.on('joinGame')
def join_game(data):
    room = data['url'].replace('/','')[-4:]
    join_room(room)
    db.session.add(User(request.sid,room))
    db.session.commit()
    emit('joined room',{'room':room},room=request.sid)

@socketio.on('start')
def start_game(game_data):
    '''Starts the game'''
    word_corpus = ['Codenames','Werewolf','Catan','Croquet','Hall?']
    word = random.choice(word_corpus)
    room = game_data['room']
    print(game_data)
    players = User.query.filter_by(room_name=room).all()
    random.shuffle(players)
    ghost = players.pop()
    for player in players:
        emit('word',{'word':word},room=player.sid)
    emit('word',{'word':'You are the ghost!'},room=ghost.sid)
    emit('begin game',{'message':'Begin the game'},room=room)

@socketio.on('connect')
def connect():
    print('client connected')

@socketio.on('disconnect')
def disconnect():
    player = User.query.filter_by(sid=request.sid).first()
    if player is not None:
        db.session.delete(player)
        db.session.commit()
        room = Room.query.filter_by(name=player.room_name).first().Users
        if room.Users is None:
            db.session.delete(room)
            db.session.commit()

if __name__ == '__main__':
    socketio.run(app)
