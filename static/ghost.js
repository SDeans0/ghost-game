let room;
let playerToken;
let sinceId = 0;

async function postJson(url, body) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
}

function storageKey() {
  return `player_token_ghost_${room}`;
}

async function joinRoom() {
  room = window.location.pathname.split('/').pop();
  const cachedToken = window.localStorage.getItem(storageKey());
  const response = await postJson(`/api/rooms/${room}/join`, { player_token: cachedToken });
  const data = await response.json();
  playerToken = data.player_token;
  window.localStorage.setItem(storageKey(), playerToken);
}

async function poll() {
  const response = await fetch(`/api/rooms/${room}/events?since_id=${sinceId}`, { headers: { 'X-Player-Token': playerToken } });
  if (!response.ok) {
    return;
  }

  const data = await response.json();
  data.events.forEach((event) => {
    sinceId = Math.max(sinceId, event.id);
    if (event.type === 'word') {
      document.getElementById('word_placeholder').innerHTML = event.payload.word;
    }
    if (event.type === 'begin_game') {
      alert('The game has started');
    }
  });
}

async function start() {
  await postJson(`/api/rooms/${room}/start`, { player_token: playerToken });
}

window.addEventListener('load', async function () {
  await joinRoom();
  setInterval(poll, 2000);
});
