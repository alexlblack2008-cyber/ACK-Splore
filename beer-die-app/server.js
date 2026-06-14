const express = require("express");
const path = require("path");

const beerDieStore = require("./lib/store");
const { computeRankings } = require("./lib/ranking");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

app.get("/api/players", (req, res) => {
  res.json(beerDieStore.getPlayers());
});

app.post("/api/players", (req, res) => {
  const name = ((req.body && req.body.name) || "").trim();
  if (!name) {
    return res.status(400).json({ error: "Name is required." });
  }
  const player = beerDieStore.addPlayer(name);
  res.status(201).json(player);
});

app.get("/api/games", (req, res) => {
  res.json(beerDieStore.getGames());
});

app.post("/api/games", (req, res) => {
  const { date, teams, winningTeamIndex, playerStats } = req.body || {};
  const players = beerDieStore.getPlayers();
  const playerIds = new Set(players.map((p) => p.id));

  if (!Array.isArray(teams) || teams.length < 2) {
    return res.status(400).json({ error: "At least two teams are required." });
  }

  const allPlayers = [];
  for (const team of teams) {
    if (!Array.isArray(team) || team.length === 0) {
      return res.status(400).json({ error: "Every team needs at least one player." });
    }
    for (const playerId of team) {
      if (!playerIds.has(String(playerId))) {
        return res.status(400).json({ error: `Unknown player id: ${playerId}` });
      }
      allPlayers.push(String(playerId));
    }
  }

  if (new Set(allPlayers).size !== allPlayers.length) {
    return res.status(400).json({ error: "A player can only appear once per game." });
  }

  const winIndex = Number(winningTeamIndex);
  if (!Number.isInteger(winIndex) || winIndex < 0 || winIndex >= teams.length) {
    return res.status(400).json({ error: "winningTeamIndex must reference one of the teams." });
  }

  const cleanStats = {};
  const numericFields = [
    "throws",
    "hits",
    "dinks",
    "sinks",
    "catches",
    "drops",
    "fifaSuccesses",
    "fifaHighestLevel",
    "dungeons",
    "heightCalls",
    "heightWarnings",
    "overTableCalls",
    "overTableWarnings",
  ];
  for (const playerId of allPlayers) {
    const raw = (playerStats && playerStats[playerId]) || {};
    const entry = {};
    for (const field of numericFields) {
      const value = Number(raw[field]);
      entry[field] = Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;
    }
    cleanStats[playerId] = entry;
  }

  const game = beerDieStore.addGame({
    date: date || new Date().toISOString().slice(0, 10),
    teams: teams.map((team) => team.map(String)),
    winningTeamIndex: winIndex,
    playerStats: cleanStats,
  });
  res.status(201).json(game);
});

app.get("/api/rankings", (req, res) => {
  const players = beerDieStore.getPlayers();
  const games = beerDieStore.getGames();
  res.json(computeRankings(players, games));
});

const PORT = process.env.PORT || 4243;
app.listen(PORT, () => console.log(`Beer Die Rankings server running on port ${PORT}`));
