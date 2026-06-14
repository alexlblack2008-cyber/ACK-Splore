(function () {
  const STAT_FIELDS = [
    { key: "throws", label: "Throws" },
    { key: "hits", label: "Hits" },
    { key: "dinks", label: "Dinks (2pt)" },
    { key: "sinks", label: "Sinks (5pt)" },
    { key: "catches", label: "Catches" },
    { key: "drops", label: "Drops" },
    { key: "fifaSuccesses", label: "FIFA successes" },
    { key: "fifaHighestLevel", label: "FIFA highest level reached" },
    { key: "dungeons", label: "Dungeons (short throws)" },
    { key: "heightCalls", label: "Height calls" },
    { key: "heightWarnings", label: "Height warnings" },
    { key: "overTableCalls", label: "Over-the-table calls" },
    { key: "overTableWarnings", label: "Over-the-table warnings" },
  ];

  let players = [];

  function setToast(el, message, type) {
    el.textContent = message;
    el.className = "toast show";
    if (type === "success") el.classList.add("success");
    if (type === "danger") el.classList.add("danger");
  }

  // ----- Tabs -----
  document.querySelectorAll(".bd-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".bd-tab").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".bd-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("bd-" + btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab === "leaderboard") loadLeaderboard();
      if (btn.dataset.tab === "players") loadPlayers();
      if (btn.dataset.tab === "loggame") loadPlayers();
    });
  });

  // ----- Players -----
  async function loadPlayers() {
    const res = await fetch("/api/players");
    players = await res.json();
    renderPlayerList();
    renderTeamSetup();
  }

  function renderPlayerList() {
    const el = document.getElementById("bd-player-list");
    if (!players.length) {
      el.innerHTML = '<div class="note">No players yet. Add your friends above.</div>';
      return;
    }
    el.innerHTML = players
      .map((p) => `<div class="row" style="padding: 6px 0">${p.name}</div>`)
      .join("");
  }

  document.getElementById("bd-add-player").addEventListener("click", async () => {
    const input = document.getElementById("bd-player-name");
    const toast = document.getElementById("bd-player-toast");
    const name = input.value.trim();
    if (!name) {
      setToast(toast, "Enter a name first.", "danger");
      return;
    }
    const res = await fetch("/api/players", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (res.ok) {
      input.value = "";
      setToast(toast, "Player added.", "success");
      loadPlayers();
    } else {
      const err = await res.json().catch(() => ({}));
      setToast(toast, err.error || "Could not add player.", "danger");
    }
  });

  // ----- Leaderboard -----
  async function loadLeaderboard() {
    const res = await fetch("/api/rankings");
    const data = await res.json();

    document.getElementById("bd-mingames").textContent = data.minGames;
    document.getElementById("bd-weights").textContent = Object.entries(data.weights)
      .map(([key, value]) => `${key} ${Math.round(value * 100)}%`)
      .join(", ");

    const el = document.getElementById("bd-leaderboard-table");
    if (!data.players.length) {
      el.innerHTML =
        '<div class="note">No rankings yet — players need at least ' +
        data.minGames +
        " logged games.</div>";
      return;
    }

    const rows = data.players
      .map(
        (p, i) => `
        <tr>
          <td>${i + 1}</td>
          <td>${p.name}</td>
          <td>${p.rating.toFixed(1)}</td>
          <td>${p.gamesPlayed}</td>
          <td>${Math.round(p.winPct * 100)}%</td>
          <td>${Math.round(p.hitPct * 100)}%</td>
          <td>${Math.round(p.catchPct * 100)}%</td>
          <td>${p.offensePerGame.toFixed(1)}</td>
          <td>${p.fifaPerGame.toFixed(1)}</td>
          <td>${Math.round(p.dungeonPct * 100)}%</td>
          <td>${p.heightFoulsPerGame.toFixed(1)}</td>
          <td>${p.overTableFoulsPerGame.toFixed(1)}</td>
        </tr>`
      )
      .join("");

    el.innerHTML = `
      <div style="overflow-x: auto">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; white-space: nowrap">
          <thead>
            <tr style="text-align: left; color: var(--muted2)">
              <th style="padding: 4px 8px">#</th>
              <th style="padding: 4px 8px">Player</th>
              <th style="padding: 4px 8px">Rating</th>
              <th style="padding: 4px 8px">Games</th>
              <th style="padding: 4px 8px">Win%</th>
              <th style="padding: 4px 8px">Hit%</th>
              <th style="padding: 4px 8px">Catch%</th>
              <th style="padding: 4px 8px">Offense/G</th>
              <th style="padding: 4px 8px">FIFA/G</th>
              <th style="padding: 4px 8px">Dungeon%</th>
              <th style="padding: 4px 8px">Height fouls/G</th>
              <th style="padding: 4px 8px">Over-table fouls/G</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  // ----- Log game: team setup -----
  function renderTeamSetup() {
    const el = document.getElementById("bd-team-setup");
    if (!el) return;

    const numTeams = parseInt(document.getElementById("bd-num-teams").value, 10);
    const teamSize = parseInt(document.getElementById("bd-team-size").value, 10);

    const options = players.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");

    let html = "";
    for (let t = 0; t < numTeams; t++) {
      html += `<div class="field"><label>Team ${t + 1}</label>`;
      for (let s = 0; s < teamSize; s++) {
        html += `<select class="bd-player-select" data-team="${t}" data-slot="${s}">
          <option value="">Select player…</option>
          ${options}
        </select>`;
      }
      html += `</div>`;
    }
    el.innerHTML = html;

    renderWinnerSetup(numTeams);
    resetStatEntry();
  }

  function renderWinnerSetup(numTeams) {
    const el = document.getElementById("bd-winner-setup");
    if (!el) return;

    let html = "<label>Winning team</label>";
    for (let t = 0; t < numTeams; t++) {
      html += `<label style="display: flex; align-items: center; gap: 8px; font-size: 13px; margin-top: 6px; font-weight: 400">
        <input type="radio" name="bd-winner" value="${t}" ${t === 0 ? "checked" : ""}/> Team ${t + 1}
      </label>`;
    }
    el.innerHTML = html;
  }

  function resetStatEntry() {
    const statEntry = document.getElementById("bd-stat-entry");
    statEntry.innerHTML = "";
    statEntry.style.display = "none";
    document.getElementById("bd-submit-game").style.display = "none";
  }

  document.getElementById("bd-num-teams").addEventListener("change", renderTeamSetup);
  document.getElementById("bd-team-size").addEventListener("change", renderTeamSetup);

  // ----- Log game: stat entry -----
  document.getElementById("bd-generate-stats").addEventListener("click", () => {
    const toast = document.getElementById("bd-loggame-toast");
    const selects = Array.from(document.querySelectorAll(".bd-player-select"));
    const ids = selects.map((s) => s.value);

    if (ids.some((id) => !id)) {
      setToast(toast, "Assign a player to every slot.", "danger");
      return;
    }
    if (new Set(ids).size !== ids.length) {
      setToast(toast, "Each player can only appear once in a game.", "danger");
      return;
    }
    toast.className = "toast";

    const el = document.getElementById("bd-stat-entry");
    el.innerHTML = ids
      .map((id) => {
        const player = players.find((p) => p.id === id);
        return `
          <div class="panel" style="margin-top: 10px">
            <div style="font-weight: 800; margin-bottom: 6px">${player.name}</div>
            <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 8px">
              ${STAT_FIELDS.map(
                (f) => `
                <div class="field" style="margin-top: 0">
                  <label>${f.label}</label>
                  <input type="number" min="0" step="1" value="0" class="bd-stat" data-player="${id}" data-field="${f.key}" />
                </div>`
              ).join("")}
            </div>
          </div>`;
      })
      .join("");

    el.style.display = "block";
    document.getElementById("bd-submit-game").style.display = "inline-block";
  });

  document.getElementById("bd-submit-game").addEventListener("click", async () => {
    const toast = document.getElementById("bd-loggame-toast");
    const numTeams = parseInt(document.getElementById("bd-num-teams").value, 10);
    const teamSize = parseInt(document.getElementById("bd-team-size").value, 10);
    const date = document.getElementById("bd-game-date").value || undefined;
    const winnerInput = document.querySelector('input[name="bd-winner"]:checked');
    const winningTeamIndex = winnerInput ? parseInt(winnerInput.value, 10) : 0;

    const teams = [];
    for (let t = 0; t < numTeams; t++) {
      const team = [];
      for (let s = 0; s < teamSize; s++) {
        const sel = document.querySelector(`.bd-player-select[data-team="${t}"][data-slot="${s}"]`);
        team.push(sel.value);
      }
      teams.push(team);
    }

    const playerStats = {};
    document.querySelectorAll(".bd-stat").forEach((input) => {
      const id = input.dataset.player;
      const field = input.dataset.field;
      if (!playerStats[id]) playerStats[id] = {};
      playerStats[id][field] = parseInt(input.value, 10) || 0;
    });

    const res = await fetch("/api/games", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date, teams, winningTeamIndex, playerStats }),
    });

    if (res.ok) {
      setToast(toast, "Game logged!", "success");
      resetStatEntry();
      renderTeamSetup();
      loadLeaderboard();
    } else {
      const err = await res.json().catch(() => ({}));
      setToast(toast, err.error || "Could not log game.", "danger");
    }
  });

  // ----- Initial load -----
  loadLeaderboard();
  loadPlayers();
})();
