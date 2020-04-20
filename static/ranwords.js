var socket = io('/ranwords');

socket.on('connect', function() {
  socket.emit('joinGame',{url: window.location.href});
});

socket.on('joined room', function(msg){
  window.sessionStorage.setItem('room',msg.room);
  console.log('joined room');
})

socket.on('word', function(msg){
  document.getElementById("word_placeholder").innerHTML = msg.word;
  document.getElementById("scratchpad").value = '';
})

socket.on('begin game', function(msg){
  alert('The game has started');
})

socket.on('message', function(msg){
  document.getElementById("scratchpad").value += msg.msg + '\n';
})

function start(){
  socket.emit('start',{room: window.sessionStorage.getItem('room')});
  console.log('start');
};

function message(){
  socket.emit('message',{room: window.sessionStorage.getItem('room'),msg:document.getElementById('entry').value});
  document.getElementById('entry').value = '';
  console.log('message');
};
