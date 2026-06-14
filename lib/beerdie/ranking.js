// Starting weights for the Beer Die Rating (BDR). Tune these as the group
// plays more games and we see how the rankings feel.
const WEIGHTS = {
  winPct: 0.3,
  offensePerGame: 0.25,
  hitPct: 0.15,
  catchPct: 0.15,
  fifaPerGame: 0.15,
};

// A player needs at least this many logged games before they show up
// on the leaderboard, so a hot/cold first game doesn't dominate.
const MIN_GAMES = 3;

// FIFA is a ladder: reaching level N means you've cleared 1..N, so a
// run that tops out at level N is worth the triangular number 1+2+...+N.
function fifaPoints(highestLevel) {
  const n = Math.max(0, Math.floor(highestLevel) || 0);
  return (n * (n + 1)) / 2;
}

function computeRankings(players, games) {
  const stats = {};
  for (const p of players) {
    stats[p.id] = {
      playerId: p.id,
      name: p.name,
      gamesPlayed: 0,
      wins: 0,
      throws: 0,
      hits: 0,
      dinks: 0,
      sinks: 0,
      catches: 0,
      drops: 0,
      fifaPoints: 0,
    };
  }

  for (const game of games) {
    const winningTeam = game.teams[game.winningTeamIndex] || [];
    for (const team of game.teams) {
      for (const playerId of team) {
        const s = stats[playerId];
        if (!s) continue;
        const ps = (game.playerStats && game.playerStats[playerId]) || {};
        s.gamesPlayed += 1;
        if (winningTeam.includes(playerId)) s.wins += 1;
        s.throws += ps.throws || 0;
        s.hits += ps.hits || 0;
        s.dinks += ps.dinks || 0;
        s.sinks += ps.sinks || 0;
        s.catches += ps.catches || 0;
        s.drops += ps.drops || 0;
        s.fifaPoints += fifaPoints(ps.fifaHighestLevel);
      }
    }
  }

  const rows = Object.values(stats)
    .filter((s) => s.gamesPlayed >= MIN_GAMES)
    .map((s) => ({
      ...s,
      winPct: s.wins / s.gamesPlayed,
      hitPct: s.throws > 0 ? s.hits / s.throws : 0,
      catchPct: s.catches + s.drops > 0 ? s.catches / (s.catches + s.drops) : 0,
      offensePerGame: (s.dinks * 2 + s.sinks * 5) / s.gamesPlayed,
      fifaPerGame: s.fifaPoints / s.gamesPlayed,
    }));

  // Min-max normalize each metric to 0-100 across eligible players so the
  // weights below combine comparable scales.
  const metrics = Object.keys(WEIGHTS);
  const ranges = {};
  for (const m of metrics) {
    const values = rows.map((r) => r[m]);
    ranges[m] = { min: Math.min(...values), max: Math.max(...values) };
  }

  function normalize(value, m) {
    const { min, max } = ranges[m];
    if (max === min) return 50;
    return ((value - min) / (max - min)) * 100;
  }

  for (const row of rows) {
    const normalized = {};
    let rating = 0;
    for (const m of metrics) {
      normalized[m] = normalize(row[m], m);
      rating += normalized[m] * WEIGHTS[m];
    }
    row.normalized = normalized;
    row.rating = Math.round(rating * 10) / 10;
  }

  rows.sort((a, b) => b.rating - a.rating);
  return { weights: WEIGHTS, minGames: MIN_GAMES, players: rows };
}

module.exports = { computeRankings, WEIGHTS, MIN_GAMES, fifaPoints };
