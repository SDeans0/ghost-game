var socket = io();

socket.on('connect', function() {
  socket.emit('joinGame',{url: window.location.href});
});

socket.on('joined room', function(msg){
  window.sessionStorage.setItem('room',msg.room);
  console.log('joined room');
})

socket.on('word', function(msg){
  document.getElementById("word_placeholder").innerHTML = msg.word;
})

socket.on('begin game', function(msg){
  alert('The game has started');
})

function start(){
  socket.emit('start',{room: window.sessionStorage.getItem('room')});
  console.log('start');
};
