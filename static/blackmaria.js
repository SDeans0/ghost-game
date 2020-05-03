let socket = io('/blackmaria');

let suitEmoji = {'clubs':'♣️','hearts':'♥️','diamonds':'♦️','spades':'♠️'};
let last_card = {suit:'',value:0};
let winner = -1;
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
let play_area;
let tally;
let bookend;

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

function compare_cards(a,b){
  if (a.suit===b.suit){
    return(a.value > b.value);
  } else {
    let suits = ['clubs','diamonds','spades','hearts'];
    return suits.indexOf(a.suit) > suits.indexOf(b.suit);
  }
}

function start(n){
  socket.emit('start',{n_players:n,room: window.sessionStorage.getItem('room')});
  console.log('start');
};

function setTurn(){
  let turn=document.getElementById('turn');
  if (current_player < 0){
    turn.innerHTML = "Pass three cards to the next player"
  } else {
    turn.innerHTML = "It's Player " + (current_player +1).toString() +"'s turn";
  }
}

function setTrick(){
  let trick=document.getElementById('trick');
  if(winner < 0){
    trick.setAttribute('class','is-hidden');
  } else {
    trick.setAttribute('class','');
    trick.innerHTML = "Player " + (winner +1).toString() + " won the last trick"
  }
}

function setReceived(){
  let pass_item = document.getElementById('pass');
  if (received_cards.length===3){
    pass_item.setAttribute('class','');
    pass_text = 'Cards received from Player ' + (((player +n_players-1) % n_players) + 1).toString() + ': ';
    for (var i=0; i<3;i++){
      pass_text += 'the ' + getName(received_cards[i].value) + ' of ' + suitEmoji[received_cards[i].suit] + ', ';
    }
    pass_text =  pass_text.slice(0, -2); //Remove trailing comma
    pass_item.innerHTML = pass_text;
  } else {
    pass_item.setAttribute('class','is-hidden');
  }
}

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
    elem.parentNode.remove();
    for (var i=0; i < hand.length+3;i++){
      card_img = document.getElementById('card_'+i.toString());
      card_img.setAttribute('onClick', '');
    }
  }
}

socket.on('receive cards', function(data){
  let next_card;
  for (var i=0;i < data.passing_cards.length;i++){
    next_card = {'suit':data.passing_cards[i].suit,'value':Number(data.passing_cards[i].value)};
    received_cards.push(next_card);
  }
});

socket.on('passed cards',function(data){
  passed[data.sender] = 1;
  if(passed.reduce((a, b) => a + b, 0) == n_players){
    hand = hand.concat(received_cards);
    // Sort the cards
    console.log(hand);
    hand.sort(function(a,b){return(compare_cards(a,b))});
    console.log(hand);
    // Display the new cards in the hand
    for (var i=0; i < hand.length;i++){
      card_img = document.getElementById('card_'+i.toString());
      card_img.setAttribute('src', '/static/cards/' + getName(hand[i].value) + '_of_' + hand[i].suit + '.svg');
      card_img.setAttribute('data-suit',hand[i].suit);
      card_img.setAttribute('data-value',hand[i].value);
      card_img.setAttribute('onClick', 'playCard(this)');
    }
    current_player = 0;
    setTurn();
    setReceived();
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
    setTurn();
    setTrick();
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
    setTurn();
  }
  if(rounds === 0){
    alert('Game Over!')
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
  alert('There are too few players in the room.')
})

socket.on('begin game', function(game_data){
  console.log('begin game')
  // Extracting useful information from signal
  player = game_data.player;
  hand = game_data.hand;
  n_players = Number(game_data.n_players);
  rounds = hand.length;
  players = new Array(n_players).fill(0);
  passed = new Array(n_players).fill(0);
  // Resetting defaults
  last_card = {suit:'',value:0};
  winner = -1;
  hand_points = 0;
  current_player = -1;
  cards_played = 0;
  passing_cards = [];
  received_cards = [];
  // Selecting key elements from the game play area
  play_area = document.getElementById('Play area');
  bookend = document.getElementById('bookend');
  if(bookend){
    bookend.remove();
  }
  tally = document.getElementById('tally');
  hand_element = document.getElementById('hand');
  // Set up the empty playing cards and the score table
  for (var i=0; i < n_players;i++){
    // Only add a card if it isn't there already
    if (!document.getElementById(i.toString())){
      // Set up the cards
      player_spot = document.createElement('div');
      player_spot.setAttribute('class','column');
      player_card = document.createElement('img');
      player_card.id=i.toString();
      player_card.src='/static/cards/blank_of_blanks.svg';
      player_card.setAttribute('data-suit','');
      player_card.setAttribute('data-value','');
      player_spot.appendChild(player_card);
      play_area.appendChild(player_spot);
    }
    // Only add a table row if it isn't there already
    if(!document.getElementById('tally_'+i.toString())){
      // Set up the score table
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
      // If the table is there already, reset it
      player_score_cell = document.getElementById('tally_'+i.toString());
      player_score_cell.innerHTML = '0';
      if (i==player){
        player_score_cell.parentNode.childNodes[0].setAttribute('class',"is-selected");
      } else{
        player_score_cell.parentNode.childNodes[0].setAttribute('class',"");
      };
      // Wipe the card image
      player_card = document.getElementById(i.toString());
      player_card.src='/static/cards/blank_of_blanks.svg';
      player_card.setAttribute('data-suit','');
      player_card.setAttribute('data-value','');
    }
  }
  // Remove the fourth card spot in a three player game
  if (n_players === 3 && document.getElementById('3')){
    let fourth_card_slot = document.getElementById('3');
    fourth_card_slot.parentNode.remove();
  }
  // Unhide the table and information panel if they are hidden
  let table_col = document.getElementById('scoreboard');
  if (table_col.getAttribute('class').search("is-hidden")>=0){
    table_col.setAttribute('class',table_col.getAttribute('class').replace('is-hidden',''));
  }
  // Reset the information panel
  setTurn();
  setTrick();
  setReceived();
  // Add a button to pass a card
  if (!document.getElementById('pass_button')){
    pass_button_col = document.createElement('div');
    pass_button_col.setAttribute('class','column');
    pass_button = document.createElement('button');
    pass_button.setAttribute('id','pass_button');
    pass_button.setAttribute('onClick','passCards(this)');
    pass_button.setAttribute('class',"button is-medium");
    pass_button.innerHTML='Pass Three Cards';
    pass_button_col.appendChild(pass_button);
    play_area.appendChild(pass_button_col);
  }
  bookend = document.createElement('div');
  bookend.setAttribute('class','column is-1');
  bookend.setAttribute('id','bookend');
  play_area.appendChild(bookend);
  // Sort the cards
  hand.sort(function(a,b){return(compare_cards(a,b))});
  // Clear any existing hand
  while (hand_element.firstChild) {
    hand_element.removeChild(hand_element.firstChild);
  }
  // Put the new cards in the hand
  for (var i=0; i < hand.length;i++){
    card_col = document.createElement('div');
    card_col.setAttribute('class','column has-text-centered is-centered is-narrow');
    card_img = document.createElement('img');
    card_img.setAttribute('style','min-width:80px');
    card_img.setAttribute('style','max-width:120px');
    card_img.setAttribute('class','is-narrow');
    card_img.src = '/static/cards/' + getName(hand[i].value) + '_of_' + hand[i].suit + '.svg';
    card_img.id='card_'+i.toString();
    card_img.setAttribute('data-suit',hand[i].suit);
    card_img.setAttribute('data-value',hand[i].value);
    card_img.setAttribute('onClick', 'stageCard(this)');
    card_col.appendChild(card_img);
    hand_element.appendChild(card_col);
  }
});
