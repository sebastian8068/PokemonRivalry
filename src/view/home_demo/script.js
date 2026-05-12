(function() {
  const activeTeam = [
    { name: "Pikachu", color: "#EBCB8B" },
    { name: "Charizard", color: "#D08770" },
    { name: "Greninja", color: "#88C0D0" },
    { name: "Lucario", color: "#A3BE8C" },
    { name: "Gardevoir", color: "#B48EAD" },
    { name: "Garchomp", color: "#BF616A" }
  ];

  function renderTeam() {
    const container = document.getElementById('teamCards');
    container.innerHTML = activeTeam.map(p => {
      return `
        <div class="pokemon-card" style="background: linear-gradient(135deg, ${p.color}40 0%, ${p.color}15 100%);">
          <div class="pokemon-name">${p.name}</div>
        </div>
      `;
    }).join('');
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

  document.getElementById('logoutBtn').addEventListener('click', () => {
    alert('Logout (demo)');
  });

  document.getElementById('findOpponentBtn').addEventListener('click', () => {
    alert('Searching random opponent... (demo)');
  });

  document.getElementById('challengeBtn').addEventListener('click', () => {
    const username = document.getElementById('rivalUsername').value;
    alert('Challenge sent to ' + username);
  });

  document.getElementById('teambuilderCard').addEventListener('click', () => {
    alert('Team Builder (demo) – aquí construirías tu equipo');
  });

  renderTeam();
  initModeSelector();
})();