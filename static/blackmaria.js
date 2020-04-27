let socket = io('/blackmaria');
let last_card = {suit:'',value:0};
let winner = 0;
let hand_points = 0;
let players = [];
let rounds = 0;
let player = -1;
let current_player = -1;
let cards_played = 0;
let hand = [];
let passing_cards = [];
let hand_element;
let passed = [];
let received_cards = [];


function getName(cardValue){
    if (cardValue < 11){
      return(cardValue);
    } else {
      let pictures = ['jack','queen','king','ace'];
      return(pictures[cardValue-11]);
    }
}

function getPoints(value,suit){
  if(suit === 'spades') {
    return(50);
  } else if (value < 14){
    return(Math.min(value,10))
  } else {
    return(15);
  }
}

function start(n){
  socket.emit('start',{n_players:n,room: window.sessionStorage.getItem('room')});
  console.log('start');
};

function playCard(elem){
  if (current_player===player && (elem.dataset.suit == last_card.suit || hand.filter(card => card.suit==last_card.suit).length === 0)) {
    hand = hand.filter(card => !(card.suit==elem.dataset.suit && card.value==elem.dataset.value));
    socket.emit('card played',{room: window.sessionStorage.getItem('room'),suit:elem.dataset.suit,value:elem.dataset.value,player:player})
    elem.parentNode.remove()
  }
}

function stageCard(elem){
  let staging_card;
  if(elem.dataset.suit == 'spades' && elem.dataset.value==12){
    alert("You can't pass the Black Maria");
  } else {
    for (var i=0; i<3; i++){
      staging_card = document.getElementById(i.toString());
      if (staging_card.getAttribute('src') == '/static/cards/blank_of_blanks.svg'){
        hand = hand.filter(card => !(card.suit==elem.dataset.suit && card.value==elem.dataset.value));
        elem.setAttribute('src','/static/cards/blank_of_blanks.svg');
        elem.setAttribute('onClick', '');
        staging_card.setAttribute('src', '/static/cards/' + getName(elem.dataset.value) + '_of_' + elem.dataset.suit + '.svg');
        staging_card.setAttribute('data-suit',elem.dataset.suit);
        staging_card.setAttribute('data-value',elem.dataset.value);
        staging_card.setAttribute('onClick', 'unstageCard(this)');
        passing_cards.push({suit:elem.dataset.suit,value: elem.dataset.value});
        break;
      }
    }
  }
}

function unstageCard(elem){
  let hand_card;
  //Remove the card from the passing array and add it to the hand
  hand.push({suit:elem.dataset.suit,value:elem.dataset.value});
  passing_cards = passing_cards.filter(card => !(card.suit==elem.dataset.suit && card.value==elem.dataset.value));
  // Find the first place you can put it back into the hand
  for (var i=0;i<hand.length+passing_cards.length;i++){
    let hand_card = document.getElementById('card_' + i.toString());
    if (hand_card.getAttribute('src') == '/static/cards/blank_of_blanks.svg'){
      elem.setAttribute('src','/static/cards/blank_of_blanks.svg');
      elem.setAttribute('onClick', '');
      hand_card.setAttribute('src','/static/cards/' + getName(elem.dataset.value) + '_of_' + elem.dataset.suit + '.svg');
      hand_card.setAttribute('data-suit',elem.dataset.suit);
      hand_card.setAttribute('data-value',elem.dataset.value);
      hand_card.setAttribute('onClick', 'stageCard(this)');
      break;
    }
  }
}

function passCards(elem){
  if (passing_cards.length === 3){
    socket.emit('pass cards',{cards:passing_cards,player:player,room:window.sessionStorage.getItem('room'),n_players:n_players});
    passed[player] = 1;
    passing_cards = [];
    for (var i=0; i<3; i++){
      staging_card = document.getElementById(i.toString());
      staging_card.src = '/static/cards/blank_of_blanks.svg';
      staging_card.setAttribute('onClick', '');
    }
    elem.remove();
    for (var i=0; i < hand.length+3;i++){
      card_img = document.getElementById('card_'+i.toString());
      card_img.setAttribute('onClick', '');
    }
  }
}

socket.on('receive cards', function(data){
  received_cards = data.passing_cards;
});

socket.on('passed cards',function(data){
  passed[data.sender] = 1;
  if(passed.reduce((a, b) => a + b, 0) == n_players){
    hand = hand.concat(received_cards);
    // Prepare the hand
    hand.sort(function(a,b){return(a.suit === b.suit ? (a.value > b.value ? 1 : -1) : (a.suit > b.suit ? 1 : -1))});
    // Put the new cards in the hand
    for (var i=0; i < hand.length;i++){
      card_img = document.getElementById('card_'+i.toString());
      card_img.src = '/static/cards/' + getName(hand[i].value) + '_of_' + hand[i].suit + '.svg';
      card_img.setAttribute('data-suit',hand[i].suit);
      card_img.setAttribute('data-value',hand[i].value);
      card_img.setAttribute('onClick', 'playCard(this)');
    }
  }
});


socket.on('card played', function(data){
  cards_played += 1;
  if (last_card.suit===''){
    for(var i=0;i<n_players;i++){
      document.getElementById(i.toString()).src = '/static/cards/blank_of_blanks.svg';
    };
  }
  document.getElementById(data.player).src = '/static/cards/' + getName(data.value) + '_of_' + data.suit + '.svg';
  if(last_card.suit==='' || ( data.suit == last_card.suit && Number(data.value) > Number(last_card.value) ) ){
    last_card.suit = data.suit;
    last_card.value = data.value;
    winner=data.player;
  };
  if(data.suit === 'hearts' || ( data.suit==='spades' && data.value==='12' ) ) {
    hand_points += getPoints(data.value,data.suit);
  };
  if(cards_played === n_players) {
    players[winner] += hand_points;
    current_player = winner;
    hand_points=0;
    cards_played = 0;
    last_card = {suit:'',value:0}
    // Shooting the moon
    if (players[winner]===149){
      for (var p=0;p<players.length; p++) {
        if (p!=winner){
          players[p] = 149;
        }
        else {
          players[p] = 0;
        }
        document.getElementById('tally_'+p.toString()).innerHTML = players[p].toString();
      }
      rounds = 0;
    } else {
      document.getElementById('tally_'+winner.toString()).innerHTML = players[winner].toString();
      rounds -= 1;
    }
  } else {
    current_player = (current_player + 1) % n_players;
  }
  if(rounds === 0){
    alert('game over')
  }

});

socket.on('connect', function() {
  socket.emit('joinGame',{url: window.location.href});
});

socket.on('joined room', function(msg){
  window.sessionStorage.setItem('room',msg.room);
  console.log('joined room');
});

socket.on('too few players',function(){
  alert('too few players')
})

socket.on('begin game', function(game_data){
  console.log('begin game')
  player = game_data.player;
  hand = game_data.hand;
  n_players = Number(game_data.n_players);
  rounds = hand.length;
  current_player = 0;
  cards_played = 0;
  players = new Array(n_players).fill(0);
  passed = new Array(n_players).fill(0);

  // Prepare the game play area
  let play_area = document.getElementById('Play area');
  let tally = document.getElementById('tally');
  hand_element = document.getElementById('hand');
  for (var i=0; i < n_players;i++){
    if (!document.getElementById(i.toString())){
      player_spot = document.createElement('div');
      player_spot.setAttribute('class','column');
      player_card = document.createElement('img');
      player_card.id=i.toString();
      player_card.src='/static/cards/blank_of_blanks.svg';
      player_card.setAttribute('data-suit','');
      player_card.setAttribute('data-value','');
      player_spot.appendChild(player_card);
      play_area.appendChild(player_spot);
      player_score_row = document.createElement('tr');
      player_name_cell = document.createElement('td');
      player_name_data = document.createTextNode('Player ' + (i+1).toString());
      if (i==player){
        player_name_cell.setAttribute('class',"is-selected");
      };
      player_name_cell.appendChild(player_name_data);
      player_score_cell = document.createElement('td');
      player_score_cell.id = 'tally_'+i.toString();
      player_score_data = document.createTextNode('0');
      player_score_cell.appendChild(player_score_data);
      player_score_row.appendChild(player_name_cell);
      player_score_row.appendChild(player_score_cell);
      tally.appendChild(player_score_row);
    } else {
      player_score_row = document.getElementById('tally_'+i.toString());
      player_score_row.innerHTML = '0';
      player_card = document.getElementById(i.toString());
      player_card.src='/static/cards/blank_of_blanks.svg';
      player_card.setAttribute('data-suit','');
      player_card.setAttribute('data-value','');
    }
  }
  // Remove the fourth card spot in a three player game
  console.log('noboi');
  if (n_players === 3 && document.getElementById('3')){
    console.log('yeboi');
    let fourth_card_slot = document.getElementById('3');
    fourth_card_slot.parentNode.remove();
  }
  // Unhide the table if it is hidden
  let table = document.getElementById('scoreboard');
  if (table.getAttribute('class')=="table is-centred is-hidden"){
    table.setAttribute('class',"table is-centred");
  }
  // Add a button to pass a card
  if (!document.getElementById('pass_button')){
    pass_button = document.createElement('button');
    pass_button.setAttribute('id','pass_button');
    pass_button.setAttribute('onClick','passCards(this)');
    pass_button.setAttribute('class',"button is-medium");
    pass_button.innerHTML='Pass Three Cards';
    play_area.appendChild(pass_button);
  }
  // Prepare the hand
  hand.sort(function(a,b){return(a.suit === b.suit ? (a.value > b.value ? 1 : -1) : (a.suit > b.suit ? 1 : -1))});
  // Clear any existing hand
  while (hand_element.firstChild) {
    hand_element.removeChild(hand_element.firstChild);
  }
  // Put the new cards in the hand
  for (var i=0; i < hand.length;i++){
    card_col = document.createElement('div');
    card_col.setAttribute('class','column content has-text-centered is-centered');
    card_img = document.createElement('img');
    card_img.src = '/static/cards/' + getName(hand[i].value) + '_of_' + hand[i].suit + '.svg';
    card_img.id='card_'+i.toString();
    card_img.setAttribute('data-suit',hand[i].suit);
    card_img.setAttribute('data-value',hand[i].value);
    card_img.setAttribute('onClick', 'stageCard(this)');
    card_col.appendChild(card_img);
    hand_element.appendChild(card_col);
  }
});
/*
window.addEventListener( "load", function () {
  function sendData(formFields,username) {
    const message = username + ': ' + formFields.next().value[1];
    console.log(message)
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
    console.log(username)
    sendData(formFields,username);
    form.reset();
    document.getElementById('user').defaultValue = username;
  } );
} );
*/
