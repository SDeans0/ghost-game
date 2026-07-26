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
  return `player_token_ranwords_${room}`;
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
      document.getElementById('scratchpad').value = '';
    }
    if (event.type === 'begin_game') {
      alert('The game has started');
    }
    if (event.type === 'message') {
      document.getElementById('scratchpad').value += event.payload.msg + '\n';
    }
  });
}

async function start() {
  await postJson(`/api/rooms/${room}/start`, { player_token: playerToken });
}

window.addEventListener('load', async function () {
  await joinRoom();
  setInterval(poll, 2000);

  const form = document.getElementById('entry');
  form.addEventListener('submit', async function (event) {
    event.preventDefault(event);
    const FD = new FormData(form);
    const formFields = FD.entries();
    const username = formFields.next().value[1];
    const message = username + ': ' + formFields.next().value[1];

    await postJson(`/api/rooms/${room}/actions`, {
      action: 'message',
      player_token: playerToken,
      payload: { msg: message }
    });

    form.reset();
    document.getElementById('user').defaultValue = username;
  });
});
