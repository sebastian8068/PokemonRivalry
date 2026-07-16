(function () {
  let ws = null;
  let playerTeam = null;
  let opponentTeam = null;
  let opponentUsername = '';
  let currentSlot = 1;
  let battleEnded = false;
  let waitingForOpponent = false;
  let myTurn = false;
  let needSwitch = false;

  const urlParams = new URLSearchParams(window.location.search);
  const roomId = urlParams.get('room');

  function log(msg, className = 'log-action') {
    const content = document.getElementById('logContent');
    const entry = document.createElement('div');
    entry.className = `log-entry ${className}`;
    entry.textContent = msg;
    content.appendChild(entry);
    content.scrollTop = content.scrollHeight;
  }

  function getActivePokemon() {
    if (!playerTeam) return null;
    return playerTeam.members.find(m => m.slot === currentSlot) || playerTeam.members[0];
  }

  function renderHpBar(fillEl, textEl, current, max) {
    const pct = max > 0 ? Math.round((current / max) * 100) : 0;
    fillEl.style.width = pct + '%';
    textEl.textContent = pct + '%';
    if (pct > 50) fillEl.style.background = 'var(--nord14)';
    else if (pct > 25) fillEl.style.background = 'var(--nord12)';
    else fillEl.style.background = 'var(--nord11)';
  }

  function renderOpponent(pokemon) {
    if (!pokemon) return;
    document.getElementById('opponentSprite').src = `/static/${pokemon.frontSpriteGIF}`;
    document.getElementById('opponentName').textContent = pokemon.pokemonName;
    renderHpBar(
      document.getElementById('opponentHpFill'),
      document.getElementById('opponentHpText'),
      pokemon.hp,
      pokemon.hp
    );
  }

  function renderBattleField() {
    const player = getActivePokemon();
    if (!player) return;
    document.getElementById('playerSprite').src = `/static/${player.backSpriteGIF}`;
    document.getElementById('playerName').textContent = player.pokemonName;
    renderHpBar(
      document.getElementById('playerHpFill'),
      document.getElementById('playerHpText'),
      player.hp,
      player.hp
    );
  }

  function setControlsEnabled(enabled) {
    document.querySelectorAll('.move-btn').forEach(b => b.disabled = !enabled);
  }

  function renderMoves() {
    const player = getActivePokemon();
    const container = document.getElementById('moveSelector');
    container.innerHTML = player.moves.map(m => {
      const typeIcon = `/static/sprites/types/${m.typeName.toLowerCase()}.png`;
      return `
        <button class="move-btn" data-move-id="${m.moveId}" ${waitingForOpponent || needSwitch ? 'disabled' : ''}>
          <span class="move-name">${m.name}</span>
          <div class="move-type-row">
            <img class="move-type-icon" src="${typeIcon}" alt="${m.typeName}" width="48" height="18">
          </div>
          <div class="move-detail">
            <span>PP ${m.pp}</span>
            <span>${m.power ? 'Power ' + m.power : 'Power \u2014'}</span>
            <span>${m.accuracy ? 'Acc ' + m.accuracy : 'Acc \u2014'}</span>
            <span class="move-category ${(m.category || '').toLowerCase()}">${m.category || ''}</span>
          </div>
          <div class="move-effect">${m.effect || ''}</div>
        </button>
      `;
    }).join('');

    container.querySelectorAll('.move-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (battleEnded || waitingForOpponent || needSwitch) return;
        const player = getActivePokemon();
        const move = player.moves.find(m => m.moveId === parseInt(btn.dataset.moveId));
        if (move && ws && ws.readyState === WebSocket.OPEN) {
          btn.classList.add('selected');
          setControlsEnabled(false);
          waitingForOpponent = true;
          log(`You selected ${move.name}. Waiting for opponent...`, 'log-system');
          ws.send(JSON.stringify({type: 'move_action', moveId: move.moveId}));
        }
      });
    });
  }

  function renderPartyBar() {
    const container = document.getElementById('partyBar');
    container.innerHTML = playerTeam.members.map(m => {
      const isActive = m.slot === currentSlot;
      const alive = m.hp > 0;
      return `
        <div class="party-member ${isActive ? 'active' : ''} ${!alive ? 'fainted' : ''}" data-slot="${m.slot}">
          <img src="/static/${m.frontSpritePNG}" alt="${m.pokemonName}" loading="lazy">
          <span class="party-name">${m.pokemonName}</span>
        </div>
      `;
    }).join('');

    container.querySelectorAll('.party-member').forEach(el => {
      el.addEventListener('click', () => {
        if (battleEnded) return;
        const newSlot = parseInt(el.dataset.slot);
        if (newSlot === currentSlot) return;

        if (needSwitch) {
          const mon = playerTeam.members.find(m => m.slot === newSlot);
          if (!mon || mon.hp <= 0) return;
          needSwitch = false;
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({type: 'switch_action', slot: newSlot}));
          }
          return;
        }

        if (waitingForOpponent) return;

        if (ws && ws.readyState === WebSocket.OPEN) {
          setControlsEnabled(false);
          waitingForOpponent = true;
          log(`Selecting ${el.querySelector('.party-name').textContent}... Waiting for opponent...`, 'log-system');
          ws.send(JSON.stringify({type: 'switch_action', slot: newSlot}));
        }
      });
    });
  }

  function updatePlayerHp(hp, maxHp) {
    const mon = playerTeam.members.find(m => m.slot === currentSlot);
    if (mon) {
      mon.hp = hp;
    }
    renderHpBar(
      document.getElementById('playerHpFill'),
      document.getElementById('playerHpText'),
      hp, maxHp
    );
  }

  function updateOpponentHp(hp, maxHp) {
    const mon = opponentTeam.members.find(m => m.slot === currentSlot);
    if (mon) {
      mon.hp = hp;
    }
    renderHpBar(
      document.getElementById('opponentHpFill'),
      document.getElementById('opponentHpText'),
      hp, maxHp
    );
  }

  function connectWebSocket() {
    const token = sessionStorage.getItem('token');
    if (!token || !roomId) return;
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws?token=${token}`);

    ws.onopen = () => {
      ws.send(JSON.stringify({type: 'join_room', room_id: roomId}));
    };

    ws.onmessage = (event) => {
      let data;
      try { data = JSON.parse(event.data); } catch { return; }

      switch (data.type) {
        case 'battle_start':
          opponentUsername = data.opponent || 'Unknown';
          opponentTeam = data.opponent_team;
          if (data.your_team) {
            playerTeam = data.your_team;
            currentSlot = playerTeam.members[0].slot;
          }
          document.getElementById('vsOpponentName').innerHTML =
            `<i class="fas fa-user"></i> ${opponentUsername}`;
          if (opponentTeam && opponentTeam.members && opponentTeam.members.length > 0) {
            const first = opponentTeam.members[0];
            first.hp = first.hp;
            renderOpponent(first);
          }
          renderBattleField();
          renderMoves();
          renderPartyBar();
          log('Battle started!', 'log-system');
          break;

        case 'action_confirmed':
          log('Action registered. Waiting for opponent...', 'log-system');
          break;

        case 'opponent_ready':
          log('Opponent has chosen!', 'log-system');
          break;

        case 'turn_result':
          waitingForOpponent = false;
          needSwitch = false;

          if (data.events) {
            data.events.forEach(ev => {
              if (ev.type === 'move') {
                const isMyAction = playerTeam && ev.actor === document.querySelector('.vs-player-name')?.textContent?.trim();
                const logClass = isMyAction ? 'log-action' : 'log-enemy';
                let msg = `${ev.actor} used ${ev.moveName}!`;
                if (ev.damage > 0) {
                  msg += ` (${ev.damage} damage)`;
                }
                log(msg, logClass);
                if (ev.effectiveness) {
                  log(ev.effectiveness, 'log-system');
                }
                if (ev.crit) {
                  log('Critical hit!', 'log-system');
                }
                if (ev.fainted) {
                  log(`${ev.actor}'s opponent's Pokémon fainted!`, 'log-system');
                }
              } else if (ev.type === 'switch') {
                const isMySwitch = playerTeam && ev.actor === document.querySelector('.vs-player-name')?.textContent?.trim();
                if (isMySwitch) {
                  currentSlot = ev.slot;
                }
                log(`${ev.actor} switched Pokémon!`, 'log-system');
              } else if (ev.type === 'critical') {
                log(ev.text, 'log-system');
              } else if (ev.type === 'status_damage') {
                log(`${ev.actor} took ${ev.damage} damage from ${ev.status.toLowerCase()}!`, 'log-system');
                if (ev.fainted) {
                  log(`${ev.actor}'s Pokémon fainted!`, 'log-system');
                }
              } else if (ev.type === 'log') {
                log(ev.text, 'log-system');
              }
            });
          }

          if (data.yourActiveSlot !== undefined) {
            currentSlot = data.yourActiveSlot;
          }
          if (data.yourActiveHp !== undefined) {
            updatePlayerHp(data.yourActiveHp, data.yourActiveMaxHp);
          }
          if (data.opponentActiveHp !== undefined) {
            updateOpponentHp(data.opponentActiveHp, data.opponentActiveMaxHp);
          }
          if (data.yourActiveName) {
            const playerNameEl = document.getElementById('playerName');
            if (playerNameEl) playerNameEl.textContent = data.yourActiveName;
          }
          if (data.opponentActiveName) {
            const oppNameEl = document.getElementById('opponentName');
            if (oppNameEl) oppNameEl.textContent = data.opponentActiveName;
            const oppMon = opponentTeam && opponentTeam.members.find(m => m.slot === data.opponentActiveSlot);
            if (oppMon) {
              document.getElementById('opponentSprite').src = `/static/${oppMon.frontSpriteGIF}`;
            }
          }

          renderMoves();
          renderPartyBar();
          break;

        case 'request_switch':
          needSwitch = true;
          waitingForOpponent = false;
          log('Your Pokémon fainted! Select a replacement from the party.', 'log-system');
          renderPartyBar();
          break;

        case 'switch_done':
          currentSlot = data.slot;
          const newMon = playerTeam.members.find(m => m.slot === data.slot);
          if (newMon) {
            log(`Go, ${newMon.pokemonName}!`, 'log-system');
          }
          renderBattleField();
          break;

        case 'opponent_switch':
          log(`Opponent switched to a new Pokémon!`, 'log-system');
          break;

        case 'new_turn':
          waitingForOpponent = false;
          setControlsEnabled(true);
          renderMoves();
          renderPartyBar();
          break;

        case 'battle_over':
          battleEnded = true;
          waitingForOpponent = false;
          setControlsEnabled(false);
          if (data.result === 'win') {
            log(`You won! +${data.score_change} score (Total: ${data.new_score})`, 'log-system');
          } else {
            log(`You lost! -${data.score_change} score (Total: ${data.new_score})`, 'log-system');
          }
          setTimeout(() => { window.location.href = '/home'; }, 4000);
          break;

        case 'opponent_disconnected':
          log('Opponent disconnected', 'log-system');
          break;

        case 'battle_result':
          battleEnded = true;
          if (data.result === 'win') {
            log(`You won! +${data.score_change} score (Total: ${data.new_score})`, 'log-system');
          } else {
            log(`You lost! -${data.score_change} score (Total: ${data.new_score})`, 'log-system');
          }
          setTimeout(() => { window.location.href = '/home'; }, 4000);
          break;

        case 'error':
          log(`Error: ${data.message}`, 'log-system');
          break;
      }
    };

    ws.onclose = () => {};
    ws.onerror = () => {};
  }

  function sendChat() {
    if (battleEnded) return;
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({type: 'chat_message', message: msg}));
    }
    input.value = '';
  }

  async function init() {
    const token = sessionStorage.getItem('token');
    if (!token) {
      window.location.href = '/';
      return;
    }

    if (!roomId) {
      log('No room specified', 'log-system');
      return;
    }

    try {
      const meRes = await fetch('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (meRes.ok) {
        const me = await meRes.json();
        document.getElementById('battleUsername').innerHTML =
          `<i class="fas fa-user"></i> ${me.username}`;
        document.getElementById('vsPlayerName').innerHTML =
          `<i class="fas fa-user"></i> ${me.username}`;
      }
    } catch {}

    connectWebSocket();
  }

  window.updatePlayerHp = updatePlayerHp;
  window.updateOpponentHp = updateOpponentHp;

  document.getElementById('forfeitBtn').addEventListener('click', () => {
    if (battleEnded) return;
    if (confirm('Are you sure you want to forfeit?')) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({type: 'forfeit'}));
      }
    }
  });

  document.getElementById('chatSendBtn').addEventListener('click', sendChat);
  document.getElementById('chatInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendChat();
  });

  init();
})();
