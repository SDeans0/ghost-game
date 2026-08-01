async function createRoom(game) {
  const response = await fetch('/api/rooms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game })
  });

  if (!response.ok) {
    alert('Failed to create room');
    return;
  }

  const data = await response.json();
  window.location = data.url;
}

function newGhost() {
  createRoom('ghost');
}

function newRanwords() {
  createRoom('ranwords');
}

function newBlackmaria() {
  createRoom('blackmaria');
}
