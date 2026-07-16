(function() {
  const HOME = '/home';

  async function checkAuth() {
    const token = sessionStorage.getItem('token');
    if (!token) {
      window.location.href = '/';
      return null;
    }
    try {
      const res = await fetch('/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        sessionStorage.removeItem('token');
        window.location.href = '/';
        return null;
      }
      return await res.json();
    } catch {
      window.location.href = '/';
      return null;
    }
  }

  async function init() {
    const user = await checkAuth();
    if (!user) return;

    document.querySelector('.username').textContent = user.username;
    document.querySelector('.score-badge').innerHTML =
      `<i class="fas fa-star"></i> ${user.score}`;

    document.getElementById('logoutBtn').addEventListener('click', () => {
      sessionStorage.removeItem('token');
      window.location.href = '/';
    });
  }

  async function renderActiveTeam() {
    const token = sessionStorage.getItem('token');
    const container = document.getElementById('teamCards');
    const section = document.querySelector('.active-team');
    const header = document.querySelector('.active-team-header h3');
    if (!token) return;

    try {
      const res = await fetch('/api/teams', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) return;
      const teams = await res.json();
      const active = teams.find(t => t.isActive);
      if (!active) {
        section.style.display = 'none';
        return;
      }
      section.style.display = 'flex';
      header.innerHTML = `<i class="fas fa-layer-group"></i> Active Team: ${active.name}`;

      container.innerHTML = active.members.map(m => {
        const name = m.pokemonName || 'Pokémon';
        return `
          <div class="pokemon-card">
            <img class="pokemon-sprite" src="/static/${m.frontSprite}" alt="${name}">
            <div class="pokemon-name">${name}</div>
          </div>
        `;
      }).join('');
    } catch {
      section.style.display = 'none';
    }
  }

  function initModeSelector() {
    const modeButtons = document.querySelectorAll('.mode-btn');
    const randomAction = document.getElementById('randomAction');
    const challengeAction = document.getElementById('challengeAction');

    modeButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        modeButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const mode = btn.dataset.mode;
        if (mode === 'random') {
          randomAction.style.display = 'flex';
          challengeAction.classList.remove('active');
        } else {
          randomAction.style.display = 'none';
          challengeAction.classList.add('active');
        }
      });
    });

    randomAction.style.display = 'flex';
  }

  document.getElementById('findOpponentBtn').addEventListener('click', () => {
    alert('Searching random opponent... (demo)');
  });

  document.getElementById('challengeBtn').addEventListener('click', () => {
    const username = document.getElementById('rivalUsername').value;
    alert('Challenge sent to ' + username);
  });

  document.getElementById('rankedCard').addEventListener('click', async () => {
    const overlay = document.getElementById('rankedOverlay');
    const list = document.getElementById('rankedList');
    list.innerHTML = '<div class="ranked-loading">Loading...</div>';
    overlay.style.display = 'flex';
    try {
      const res = await fetch('/api/leaderboard');
      const data = await res.json();
      list.innerHTML = data.length === 0
        ? '<div class="ranked-empty">No players yet</div>'
        : data.map((p, i) => `
          <div class="ranked-entry${i < 3 ? ' top-three' : ''}">
            <span class="ranked-pos">#${i + 1}</span>
            <span class="ranked-name"><i class="fas fa-user"></i> ${p.username}</span>
            <span class="ranked-score"><i class="fas fa-star"></i> ${p.score}</span>
          </div>
        `).join('');
    } catch {
      list.innerHTML = '<div class="ranked-empty">Failed to load</div>';
    }
  });

  document.getElementById('rankedClose').addEventListener('click', () => {
    document.getElementById('rankedOverlay').style.display = 'none';
  });

  document.getElementById('rankedOverlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) {
      e.currentTarget.style.display = 'none';
    }
  });

  initModeSelector();
  init().then(() => renderActiveTeam());
})();
