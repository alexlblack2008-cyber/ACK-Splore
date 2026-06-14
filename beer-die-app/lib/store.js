const fs = require("fs");
const path = require("path");

// On Render (or similar hosts with ephemeral filesystems), set
// BEERDIE_DATA_DIR to a mounted persistent disk so data survives deploys.
const DATA_DIR = process.env.BEERDIE_DATA_DIR || path.join(__dirname, "..", "data");
const DATA_FILE = path.join(DATA_DIR, "beerdie.json");

function readData() {
  try {
    const raw = fs.readFileSync(DATA_FILE, "utf8");
    return JSON.parse(raw);
  } catch (err) {
    return { nextPlayerId: 1, nextGameId: 1, players: [], games: [] };
  }
}

function writeData(data) {
  fs.mkdirSync(path.dirname(DATA_FILE), { recursive: true });
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

function getPlayers() {
  return readData().players;
}

function addPlayer(name) {
  const data = readData();
  const player = { id: String(data.nextPlayerId), name };
  data.players.push(player);
  data.nextPlayerId += 1;
  writeData(data);
  return player;
}

function getGames() {
  return readData().games;
}

function addGame(game) {
  const data = readData();
  const entry = { id: String(data.nextGameId), ...game };
  data.games.push(entry);
  data.nextGameId += 1;
  writeData(data);
  return entry;
}

module.exports = { getPlayers, addPlayer, getGames, addGame };
