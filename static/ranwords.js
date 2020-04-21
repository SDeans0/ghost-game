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

window.addEventListener( "load", function () {
  function sendData(formFields,username) {
    const message = username + ': ' + formFields.next().value[1];
    socket.emit('message',{room: window.sessionStorage.getItem('room'),msg:message});
  }

  // Access the form element...
  const form = document.getElementById( "entry" );

  // ...and take over its submit event.
  form.addEventListener( "submit", function ( event ) {
    event.preventDefault(event);
    console.log('called')
    const FD = new FormData( form );
    const formFields = FD.entries();
    const username = formFields.next().value[1];
    sendData(formFields,username);
    form.reset();
    document.getElementById('user').defaultValue = username;
  } );
} );
