var socket = io();

socket.on('connect', function() {
  console.log('connected');
});

socket.on('newGame', function(msg){
  window.sessionStorage.setItem('room',msg.room);
  console.log('joined room');
})

socket.on('redirect', function (data) {
  window.location = data.url;
});

function newGhost(){
  socket.emit('newGame',{game:'ghost'});
}

function newRanwords(){
  socket.emit('newGame',{game:'ranwords'});
}
