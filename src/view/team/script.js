(function () {
  const API = '/api';

  let currentTeamId = null;
  let currentSlot = null;
  let pokemonCatalog = [];
  let itemsCatalog = [];
  let abilitiesCatalog = [];
  let movesCatalog = [];
  let naturesCatalog = [];
  let slots = Array(6).fill(null);
  let pickerResolve = null;  // callback for generic picker modal

  const STAT_ABBR = { attackEvs: 'Atk', defenseEvs: 'Def', spAtkEvs: 'SpA', spDefEvs: 'SpD', speedEvs: 'Spe' };

  function parseStatChanged(str) {
    const m = str && str.match(/\(-(\w+),\s*\+(\w+)\)/);
    return m ? { dec: m[1], inc: m[2] } : { dec: null, inc: null };
  }

  // ──── Auth ────
  async function checkAuth() {
    const token = sessionStorage.getItem('token');
    if (!token) { window.location.href = '/'; return null; }
    try {
      const res = await fetch('/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) { sessionStorage.removeItem('token'); window.location.href = '/'; return null; }
      return await res.json();
    } catch { sessionStorage.removeItem('token'); window.location.href = '/'; return null; }
  }

  function authHeaders() {
    const token = sessionStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  }

  // ──── Views ────
  function showTeamListView() {
    document.getElementById('teamListView').style.display = 'block';
    document.getElementById('teamEditorView').style.display = 'none';
    document.getElementById('detailPanel').style.display = 'none';
    document.getElementById('pokemonModal').style.display = 'none';
    document.getElementById('pickerModal').style.display = 'none';
  }

  function showEditorView() {
    document.getElementById('teamListView').style.display = 'none';
    document.getElementById('teamEditorView').style.display = 'block';
  }

  // ──── Load Catalogs ────
  async function loadCatalogs() {
    const [pokemon, items, abilities, moves, natures] = await Promise.all([
      fetch(`${API}/pokemon`, { headers: authHeaders() }).then(r => r.json()),
      fetch(`${API}/items`, { headers: authHeaders() }).then(r => r.json()),
      fetch(`${API}/abilities`, { headers: authHeaders() }).then(r => r.json()),
      fetch(`${API}/moves`, { headers: authHeaders() }).then(r => r.json()),
      fetch(`${API}/natures`, { headers: authHeaders() }).then(r => r.json()),
    ]);
    pokemonCatalog = pokemon;
    itemsCatalog = items;
    abilitiesCatalog = abilities;
    movesCatalog = moves;
    naturesCatalog = natures;
  }

  const TYPE_COLORS = {
    normal: '#A8A77A', fire: '#EE8130', water: '#6390F0', electric: '#F7D02C',
    grass: '#7AC74C', ice: '#96D9D6', fighting: '#C22E28', poison: '#A33EA1',
    ground: '#E2BF65', flying: '#A98FF3', psychic: '#F95587', bug: '#A6B91A',
    rock: '#B6A136', ghost: '#735797', dragon: '#6F35FC', dark: '#705746',
    steel: '#B7B7CE', fairy: '#D685AD',
  };

  // ──── Team List ────
  function renderTeamSprites(members) {
    const sprites = [];
    for (let i = 1; i <= 6; i++) {
      const m = (members || []).find(me => me.slot === i);
      if (m) {
        sprites.push(`<img class="mini-sprite" src="/static/${m.frontSprite}" alt="" loading="lazy">`);
      } else {
        sprites.push(`<span class="empty-slot"></span>`);
      }
    }
    return sprites.join('');
  }

  async function loadTeams() {
    const container = document.getElementById('teamListContainer');
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
    try {
      const teams = await fetch(`${API}/teams`, { headers: authHeaders() }).then(r => r.json());
      if (teams.length === 0) {
        container.innerHTML = '';
        return;
      }
      container.innerHTML = teams.map(t => `
        <div class="team-card" data-team-id="${t.teamId}">
          <div class="team-card-header">
            <span class="team-card-name">${t.name}</span>
            <div class="team-card-actions">
              ${t.isActive
                ? `<span class="active-radio" title="Active"><i class="fas fa-circle-check"></i></span>`
                : `<span class="inactive-radio activate-team-btn" data-team-id="${t.teamId}" title="Set as active"><i class="fas fa-circle"></i></span>`}
              <button class="ghost-btn edit-team-btn" data-team-id="${t.teamId}" title="Edit">
                <i class="fas fa-pen-to-square"></i>
              </button>
              <button class="danger-btn delete-team-btn" data-team-id="${t.teamId}" title="Delete">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
          <div class="team-card-sprites">
            ${renderTeamSprites(t.members)}
          </div>
        </div>
      `).join('');

      container.querySelectorAll('.team-card').forEach(card => {
        card.addEventListener('click', e => {
          if (e.target.closest('button, .activate-team-btn')) return;
          openTeamEditor(parseInt(card.dataset.teamId));
        });
      });
      container.querySelectorAll('.edit-team-btn').forEach(btn => {
        btn.addEventListener('click', e => { e.stopPropagation(); openTeamEditor(parseInt(btn.dataset.teamId)); });
      });
      container.querySelectorAll('.activate-team-btn').forEach(el => {
        el.addEventListener('click', async e => {
          e.stopPropagation();
          await activateTeam(parseInt(el.dataset.teamId));
        });
      });
      container.querySelectorAll('.delete-team-btn').forEach(btn => {
        btn.addEventListener('click', async e => {
          e.stopPropagation();
          await deleteTeam(parseInt(btn.dataset.teamId));
        });
      });
    } catch {
      container.innerHTML = '<div class="loading-spinner" style="color:var(--nord11);">Error loading teams</div>';
    }
  }

  async function deleteTeam(teamId) {
    if (!confirm('Delete this team?')) return;
    await fetch(`${API}/teams/${teamId}`, { method: 'DELETE', headers: authHeaders() });
    loadTeams();
  }

  async function activateTeam(teamId) {
    await fetch(`${API}/teams/${teamId}/activate`, { method: 'POST', headers: authHeaders() });
    loadTeams();
  }

  // ──── New Team ────
  function showNewTeamModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'newTeamModal';
    overlay.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h3><i class="fas fa-plus-circle"></i> New Team</h3>
          <button class="modal-close" id="newTeamModalClose">&times;</button>
        </div>
        <input type="text" id="newTeamNameInput" class="modal-input" placeholder="Enter team name..." maxlength="50" autofocus>
        <div class="modal-actions">
          <button class="ghost-btn" id="newTeamCancelBtn">Cancel</button>
          <button class="primary-btn" id="newTeamConfirmBtn"><i class="fas fa-check"></i> Create</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const close = () => overlay.remove();
    overlay.querySelector('#newTeamModalClose').onclick = close;
    overlay.querySelector('#newTeamCancelBtn').onclick = close;
    overlay.querySelector('#newTeamConfirmBtn').onclick = async () => {
      const name = overlay.querySelector('#newTeamNameInput').value.trim();
      if (!name) return;
      try {
        const res = await fetch(`${API}/teams`, { method: 'POST', headers: authHeaders(), body: JSON.stringify({ name }) });
        const data = await res.json();
        overlay.remove();
        openTeamEditor(data.teamId);
      } catch { alert('Error creating team'); }
    };
    overlay.querySelector('#newTeamNameInput').addEventListener('keydown', e => {
      if (e.key === 'Enter') overlay.querySelector('#newTeamConfirmBtn').click();
      if (e.key === 'Escape') close();
    });
    setTimeout(() => overlay.querySelector('#newTeamNameInput').focus(), 100);
  }

  // ──── Team Editor ────
  async function openTeamEditor(teamId) {
    showEditorView();
    currentSlot = null;
    document.getElementById('detailPanel').style.display = 'none';
    try {
      const team = await fetch(`${API}/teams/${teamId}`, { headers: authHeaders() }).then(r => r.json());
      currentTeamId = team.teamId;
      document.getElementById('teamNameInput').value = team.name;
      slots = Array(6).fill(null);
      for (const m of team.members || []) {
        slots[m.slot - 1] = m;
      }
      renderSlots();
    } catch { alert('Error loading team'); showTeamListView(); }
  }

  function renderSlots() {
    const container = document.getElementById('pokemonSlots');
    container.innerHTML = slots.map((data, idx) => {
      const slotNum = idx + 1;
      if (!data) {
        return `
          <div class="pokemon-slot" data-slot="${slotNum}">
            <span class="slot-number">#${slotNum}</span>
            <i class="fas fa-plus slot-empty-icon"></i>
            <span class="slot-empty-text">Add Pokémon</span>
          </div>
        `;
      }
      const sprite = data.frontSprite || '';
      const pokemonData = pokemonCatalog.find(p => p.pokemonId === data.pokemonId);
      const types = (pokemonData && pokemonData.types) || [];
      const typesHtml = types.map(t =>
        `<img class="type-icon" src="/static/sprites/types/${t.toLowerCase()}.png" alt="${t}" title="${t}">`
      ).join('');
      return `
        <div class="pokemon-slot filled" data-slot="${slotNum}">
          <span class="slot-number">#${slotNum}</span>
          <img class="slot-sprite" src="/static/${sprite}" alt="${data.pokemonName || ''}" loading="lazy">
          <span class="slot-name">${data.pokemonName || 'Pokémon'}</span>
          <div class="slot-types">${typesHtml}</div>
        </div>
      `;
    }).join('');

    container.querySelectorAll('.pokemon-slot').forEach(el => {
      el.addEventListener('click', () => {
        const slotNum = parseInt(el.dataset.slot);
        if (slots[slotNum - 1]) {
          openDetailPanel(slotNum);
        } else {
          openPokemonSelector(slotNum);
        }
      });
    });
    updateSaveButton();
  }

  // ──── Pokémon Selector (modal) ────
  function openPokemonSelector(slotNum) {
    currentSlot = slotNum;
    const modal = document.getElementById('pokemonModal');
    modal.style.display = 'flex';
    const grid = document.getElementById('pokemonGrid');
    const search = document.getElementById('pokemonSearch');
    search.value = '';
    renderPokemonGrid(grid, pokemonCatalog);
    search.focus();
    search.oninput = () => {
      const q = search.value.toLowerCase();
      renderPokemonGrid(grid, pokemonCatalog.filter(p => p.name.toLowerCase().includes(q)));
    };
  }

  function renderPokemonGrid(container, list) {
    container.innerHTML = list.map(p => {
      const typesHtml = (p.types || []).map(t =>
        `<img class="type-icon" src="/static/sprites/types/${t.toLowerCase()}.png" alt="${t}" title="${t}">`
      ).join('');
      return `
        <div class="option-card" data-id="${p.pokemonId}">
          <img src="/static/${p.frontSprite}" alt="${p.name}" loading="lazy">
          <div class="option-name">${p.name}</div>
          <div class="pokemon-option-types">${typesHtml || ''}</div>
        </div>
      `;
    }).join('');
    container.querySelectorAll('.option-card').forEach(el => {
      el.addEventListener('click', () => {
        const pokemonId = parseInt(el.dataset.id);
        const pokemon = pokemonCatalog.find(p => p.pokemonId === pokemonId);
        if (!pokemon) return;
        slots[currentSlot - 1] = {
          slot: currentSlot, pokemonId: pokemon.pokemonId, pokemonName: pokemon.name,
          frontSprite: pokemon.frontSprite, itemId: null, abilityId: null, natureId: null,
          hpEvs: 0, attackEvs: 0, defenseEvs: 0, spAtkEvs: 0, spDefEvs: 0, speedEvs: 0,
          move1Id: null, move2Id: null, move3Id: null, move4Id: null,
        };
        document.getElementById('pokemonModal').style.display = 'none';
        renderSlots();
        openDetailPanel(currentSlot);
      });
    });
  }

  // ──── Generic Picker Modal ────
  function openPicker(title, searchPlaceholder, items, renderFn) {
    return new Promise(resolve => {
      pickerResolve = resolve;
      const modal = document.getElementById('pickerModal');
      const titleEl = document.getElementById('pickerTitle');
      const search = document.getElementById('pickerSearch');
      const grid = document.getElementById('pickerGrid');
      titleEl.textContent = title;
      search.placeholder = searchPlaceholder || 'Search...';
      search.value = '';
      renderPickerGrid(grid, items, renderFn);
      modal.style.display = 'flex';
      search.focus();
      search.oninput = () => {
        const q = search.value.toLowerCase();
        const filtered = items.filter(item =>
          (item.name || '').toLowerCase().includes(q) ||
          (item.statChanged || '').toLowerCase().includes(q) ||
          (item.description || '').toLowerCase().includes(q)
        );
        renderPickerGrid(grid, filtered, renderFn);
      };
    });
  }

  function renderPickerGrid(container, items, renderFn) {
    container.innerHTML = items.map(renderFn).join('');
    container.querySelectorAll('.option-card').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.dataset.idx);
        document.getElementById('pickerModal').style.display = 'none';
        if (pickerResolve) {
          pickerResolve(items[idx]);
          pickerResolve = null;
        }
      });
    });
  }

  // ──── Render functions for each picker type ────
  function renderItemOption(item, idx) {
    return `
      <div class="option-card" data-idx="${idx}">
        <div class="option-name">${item.name}</div>
        <div class="option-desc">${item.description || ''}</div>
      </div>
    `;
  }

  function renderAbilityOption(ability, idx) {
    return `
      <div class="option-card" data-idx="${idx}">
        <div class="option-name">${ability.name}</div>
        <div class="option-desc">${ability.description || ''}</div>
      </div>
    `;
  }

  function renderMoveOption(move, idx) {
    const typeName = (move.typeName || '').toLowerCase();
    return `
      <div class="option-card move-card" data-idx="${idx}">
        <div class="move-header">
          <span class="option-name">${move.name}</span>
          <img class="type-icon-sm" src="/static/sprites/types/${typeName}.png" alt="${move.typeName || ''}" title="${move.typeName || ''}">
          <span class="move-category">${move.category || '—'}</span>
        </div>
        <div class="move-details">
          <span>Power: ${move.power ?? '—'}</span>
          <span>Acc: ${move.accuracy != null ? move.accuracy + '%' : '—'}</span>
          <span>PP: ${move.pp}</span>
        </div>
        <div class="option-desc">${move.effect || ''}</div>
      </div>
    `;
  }

  function renderNatureOption(nature, idx) {
    return `
      <div class="option-card" data-idx="${idx}">
        <div class="option-name">${nature.name}</div>
        <div class="nature-stat">${nature.statChanged}</div>
      </div>
    `;
  }

  // ──── Detail Panel ────
  async function openDetailPanel(slotNum) {
    currentSlot = slotNum;
    const data = slots[slotNum - 1];
    if (!data) return;

    const panel = document.getElementById('detailPanel');
    panel.style.display = 'block';
    document.getElementById('detailPokemonName').textContent = data.pokemonName || 'Pokémon';
    document.getElementById('detailSlotLabel').textContent = `Slot ${slotNum}`;

    const body = document.getElementById('detailBody');
    const [slotAbilities, slotMoves] = await Promise.all([
      fetch(`${API}/pokemon/${data.pokemonId}/abilities`, { headers: authHeaders() }).then(r => r.json()).catch(() => []),
      fetch(`${API}/pokemon/${data.pokemonId}/moves`, { headers: authHeaders() }).then(r => r.json()).catch(() => []),
    ]);

    const namedItem = data.itemId ? itemsCatalog.find(i => i.itemId === data.itemId) : null;
    const namedAbility = data.abilityId ? slotAbilities.find(a => a.abilityId === data.abilityId) || abilitiesCatalog.find(a => a.abilityId === data.abilityId) : null;
    const namedNature = data.natureId ? naturesCatalog.find(n => n.natureId === data.natureId) : null;
    const natureMod = namedNature ? namedNature.statChanged : null;
    const namedMoves = [1,2,3,4].map(i => {
      const id = data[`move${i}Id`];
      return id ? slotMoves.find(m => m.moveId === id) || movesCatalog.find(m => m.moveId === id) : null;
    });

    const pokemon = pokemonCatalog.find(p => p.pokemonId === data.pokemonId);
    const base = pokemon || {};
    const evSum = data.hpEvs + data.attackEvs + data.defenseEvs + data.spAtkEvs + data.spDefEvs + data.speedEvs;
    const remaining = 508 - evSum;

    body.innerHTML = `
      <div class="detail-section">
        <label>Held Item</label>
        <button class="selection-btn" id="pickItemBtn">
          <span class="${namedItem ? 'sel-value' : 'sel-placeholder'}">${namedItem ? namedItem.name : 'Click to select'}</span>
          <i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--nord3)"></i>
        </button>
      </div>
      <div class="detail-section">
        <label>Ability</label>
        <button class="selection-btn" id="pickAbilityBtn">
          <span class="${namedAbility ? 'sel-value' : 'sel-placeholder'}">${namedAbility ? namedAbility.name : 'Click to select'}</span>
          <i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--nord3)"></i>
        </button>
      </div>
      <div class="detail-section">
        <label>Move 1</label>
        <button class="selection-btn" id="pickMove1Btn">
          <span class="${namedMoves[0] ? 'sel-value' : 'sel-placeholder'}">${namedMoves[0] ? namedMoves[0].name : 'Click to select'}</span>
          <i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--nord3)"></i>
        </button>
      </div>
      <div class="detail-section">
        <label>Move 2</label>
        <button class="selection-btn" id="pickMove2Btn">
          <span class="${namedMoves[1] ? 'sel-value' : 'sel-placeholder'}">${namedMoves[1] ? namedMoves[1].name : 'Click to select'}</span>
          <i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--nord3)"></i>
        </button>
      </div>
      <div class="detail-section">
        <label>Move 3</label>
        <button class="selection-btn" id="pickMove3Btn">
          <span class="${namedMoves[2] ? 'sel-value' : 'sel-placeholder'}">${namedMoves[2] ? namedMoves[2].name : 'Click to select'}</span>
          <i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--nord3)"></i>
        </button>
      </div>
      <div class="detail-section">
        <label>Move 4</label>
        <button class="selection-btn" id="pickMove4Btn">
          <span class="${namedMoves[3] ? 'sel-value' : 'sel-placeholder'}">${namedMoves[3] ? namedMoves[3].name : 'Click to select'}</span>
          <i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--nord3)"></i>
        </button>
      </div>
      <div class="detail-section">
        <label>Nature</label>
        <button class="selection-btn" id="pickNatureBtn">
          <span class="${namedNature ? 'sel-value' : 'sel-placeholder'}">${namedNature ? namedNature.name + ' ' + namedNature.statChanged : 'Click to select'}</span>
          <i class="fas fa-chevron-right" style="font-size:0.7rem;color:var(--nord3)"></i>
        </button>
      </div>
      <div class="detail-section ev-container full-width">
        <label>EVs</label>
        <div class="ev-table" id="evGrid">
          <div class="ev-header">
            <span>Stat</span><span>Base</span><span>EVs</span><span></span><span>Total</span>
          </div>
          ${makeEvRow('hpEvs', 'HP', base.hp, data.hpEvs, natureMod)}
          ${makeEvRow('attackEvs', 'Attack', base.attack, data.attackEvs, natureMod)}
          ${makeEvRow('defenseEvs', 'Defense', base.defense, data.defenseEvs, natureMod)}
          ${makeEvRow('spAtkEvs', 'Sp. Atk', base.spAtk, data.spAtkEvs, natureMod)}
          ${makeEvRow('spDefEvs', 'Sp. Def', base.spDef, data.spDefEvs, natureMod)}
          ${makeEvRow('speedEvs', 'Speed', base.speed, data.speedEvs, natureMod)}
        </div>
        <div class="ev-total">
          <span class="remaining-ok" id="evRemainingDisplay">remaining: ${remaining}</span>
        </div>
      </div>
    `;

    // Wire picker buttons
    document.getElementById('pickItemBtn').addEventListener('click', async () => {
      const result = await openPicker('Select Item', 'Search items...', itemsCatalog, renderItemOption);
      if (result) {
        data.itemId = result.itemId;
        openDetailPanel(slotNum);
        updateSaveButton();
      }
    });
    document.getElementById('pickAbilityBtn').addEventListener('click', async () => {
      const result = await openPicker('Select Ability', 'Search abilities...', slotAbilities, renderAbilityOption);
      if (result) {
        data.abilityId = result.abilityId;
        openDetailPanel(slotNum);
        updateSaveButton();
      }
    });
    for (let i = 1; i <= 4; i++) {
      const btn = document.getElementById(`pickMove${i}Btn`);
      btn.addEventListener('click', async () => {
        const result = await openPicker(`Select Move ${i}`, 'Search moves...', slotMoves, renderMoveOption);
        if (result) {
          data[`move${i}Id`] = result.moveId;
          openDetailPanel(slotNum);
          updateSaveButton();
        }
      });
    }
    document.getElementById('pickNatureBtn').addEventListener('click', async () => {
      const result = await openPicker('Select Nature', 'Search natures...', naturesCatalog, renderNatureOption);
      if (result) {
        data.natureId = result.natureId;
        openDetailPanel(slotNum);
        updateSaveButton();
      }
    });

    // EV sliders
    const statNames = { hpEvs: 'hp', attackEvs: 'attack', defenseEvs: 'defense', spAtkEvs: 'spAtk', spDefEvs: 'spDef', speedEvs: 'speed' };
    const evNames = Object.keys(statNames);
    evNames.forEach(name => {
      const slider = document.getElementById(`slider-${name}`);
      const valSpan = document.getElementById(`val-${name}`);
      if (!slider) return;

      const updateAll = () => recalcEvMaxs(slotNum);

      slider.addEventListener('input', () => {
        const val = parseInt(slider.value);
        valSpan.textContent = val;
        data[name] = val;
        const baseStat = base[statNames[name]] || 0;
        const totalEl = document.getElementById(`total-${name}`);
        if (totalEl) totalEl.textContent = calcTotalStat(name, baseStat, val, natureMod);
        updateAll();
        updateEvDisplay(slotNum);
        updateSaveButton();
      });
    });

    recalcEvMaxs(slotNum);
    updateEvDisplay(slotNum);
    updateSaveButton();

    document.getElementById('removePokemonBtn').onclick = () => {
      slots[slotNum - 1] = null;
      panel.style.display = 'none';
      renderSlots();
    };
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function calcTotalStat(evName, baseStat, evValue, statChanged) {
    let total;
    if (evName === 'hpEvs') {
      total = (baseStat * 2) + 141 + Math.floor(evValue / 4);
    } else {
      total = (baseStat * 2) + 36 + Math.floor(evValue / 4);
    }
    if (statChanged && evName !== 'hpEvs') {
      const mods = parseStatChanged(statChanged);
      const abbr = STAT_ABBR[evName];
      if (abbr === mods.inc) {
        total = Math.floor(total * 1.1);
      } else if (abbr === mods.dec) {
        total = Math.floor(total * 0.9);
      }
    }
    return total;
  }

  function makeEvRow(evName, label, baseStat, value, statChanged) {
    const clamped = Math.min(value, 252);
    const total = calcTotalStat(evName, baseStat || 0, clamped, statChanged);
    return `
      <div class="ev-row">
        <span class="ev-label">${label}</span>
        <span class="ev-base">${baseStat ?? '—'}</span>
        <input type="range" id="slider-${evName}" min="0" max="252" value="${clamped}">
        <span class="ev-value" id="val-${evName}">${clamped}</span>
        <span class="ev-total-stat" id="total-${evName}">${total}</span>
      </div>
    `;
  }

  function recalcEvMaxs(slotNum) {
    const data = slots[slotNum - 1];
    if (!data) return;
    const evNames = ['hpEvs', 'attackEvs', 'defenseEvs', 'spAtkEvs', 'spDefEvs', 'speedEvs'];
    const current = {};
    evNames.forEach(n => { current[n] = parseInt(document.getElementById(`slider-${n}`)?.value) || 0; });

    evNames.forEach(name => {
      const slider = document.getElementById(`slider-${name}`);
      if (!slider) return;
      const othersSum = evNames
        .filter(n => n !== name)
        .reduce((sum, n) => sum + current[n], 0);
      const maxAllowed = Math.max(0, Math.min(252, 508 - othersSum));
      const currentVal = parseInt(slider.value);
      if (currentVal > maxAllowed) {
        slider.value = maxAllowed;
        current[name] = maxAllowed;
        data[name] = maxAllowed;
        document.getElementById(`val-${name}`).textContent = maxAllowed;
      }
      slider.max = maxAllowed;
    });
  }

  function updateEvDisplay(slotNum) {
    const data = slots[slotNum - 1];
    if (!data) return;
    const total = data.hpEvs + data.attackEvs + data.defenseEvs + data.spAtkEvs + data.spDefEvs + data.speedEvs;
    const remaining = 508 - total;
    const rd = document.getElementById('evRemainingDisplay');
    if (rd) {
      rd.textContent = `remaining: ${remaining}`;
      rd.className = 'remaining-ok';
    }
  }

  // ──── Save ────
  function updateSaveButton() {
    const btn = document.getElementById('saveTeamBtn');
    const hasPokemon = slots.some(s => s !== null);
    const valid = hasPokemon && slots.every(s => {
      if (!s) return true;
      const total = s.hpEvs + s.attackEvs + s.defenseEvs + s.spAtkEvs + s.spDefEvs + s.speedEvs;
      return total <= 508 && s.hpEvs <= 252 && s.attackEvs <= 252 && s.defenseEvs <= 252 &&
             s.spAtkEvs <= 252 && s.spDefEvs <= 252 && s.speedEvs <= 252 && s.abilityId && s.natureId;
    });
    btn.disabled = !valid;
  }

  async function saveTeam() {
    if (!currentTeamId) return;
    const name = document.getElementById('teamNameInput').value.trim();
    if (!name) return;
    const members = slots.filter(s => s !== null).map(s => ({
      slot: s.slot, pokemonId: s.pokemonId, itemId: s.itemId || null, abilityId: s.abilityId,
      natureId: s.natureId, hpEvs: s.hpEvs, attackEvs: s.attackEvs, defenseEvs: s.defenseEvs,
      spAtkEvs: s.spAtkEvs, spDefEvs: s.spDefEvs, speedEvs: s.speedEvs,
      move1Id: s.move1Id || null, move2Id: s.move2Id || null, move3Id: s.move3Id || null, move4Id: s.move4Id || null,
    }));
    try {
      const btn = document.getElementById('saveTeamBtn');
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
      await fetch(`${API}/teams/${currentTeamId}`, {
        method: 'PUT', headers: authHeaders(),
        body: JSON.stringify({ name, isActive: false, members }),
      });
      btn.innerHTML = '<i class="fas fa-check"></i> Saved!';
      setTimeout(() => {
        btn.innerHTML = '<i class="fas fa-floppy-disk"></i> Save';
        btn.disabled = false;
        updateSaveButton();
      }, 1500);
    } catch { alert('Error saving team'); updateSaveButton(); }
  }

  // ──── Init ────
  async function init() {
    const user = await checkAuth();
    if (!user) return;
    document.querySelector('.username').textContent = user.username;
    document.querySelector('.score-badge').innerHTML = `<i class="fas fa-star"></i> ${user.score}`;

    await loadCatalogs();
    await loadTeams();
    showTeamListView();

    document.getElementById('newTeamBtn').addEventListener('click', showNewTeamModal);
    document.getElementById('backToTeamsBtn').addEventListener('click', () => {
      document.getElementById('detailPanel').style.display = 'none';
      showTeamListView();
      loadTeams();
    });
    document.getElementById('saveTeamBtn').addEventListener('click', saveTeam);
    document.getElementById('modalCloseBtn').addEventListener('click', () => {
      document.getElementById('pokemonModal').style.display = 'none';
    });
    document.getElementById('pickerModalClose').addEventListener('click', () => {
      document.getElementById('pickerModal').style.display = 'none';
      if (pickerResolve) { pickerResolve(null); pickerResolve = null; }
    });
    document.getElementById('pokemonModal').addEventListener('click', e => {
      if (e.target === e.currentTarget) document.getElementById('pokemonModal').style.display = 'none';
    });
    document.getElementById('pickerModal').addEventListener('click', e => {
      if (e.target === e.currentTarget) {
        document.getElementById('pickerModal').style.display = 'none';
        if (pickerResolve) { pickerResolve(null); pickerResolve = null; }
      }
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
