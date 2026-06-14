# Beer Die Rankings

A small web app for tracking Beer Die stats for your group and ranking
players with a composite "Beer Die Rating" (BDR), GHIN-style.

## Features

- **Players** — add everyone in your group.
- **Log Game** — pick the number of teams (2-4) and players per team (1-4),
  assign players to teams, mark the winner, and enter per-player stats:
  throws, hits, dinks, sinks, catches, drops, FIFA ladder results, dungeons,
  height calls/warnings, and over-the-table calls/warnings.
- **Leaderboard** — a 0-100 rating per player combining win %, hit %, catch %,
  offense per game, FIFA points per game, and penalties for dungeons, height
  fouls, and over-the-table fouls.

Players need at least 3 logged games before they appear on the leaderboard.

## Tuning the rating formula

All weights live in `lib/ranking.js` (`WEIGHTS` constant) along with the
minimum-games threshold and the "warning vs. call" weighting. Edit those
values and redeploy to retune the rankings as you collect more data.

## Running locally

```bash
npm install
npm start
```

The app runs on port 4243 by default (or `PORT` if set). Open
`http://localhost:4243`.

## Deploying to Render

1. Push this repo to GitHub.
2. In Render, click **New > Blueprint** and point it at this repo — it will
   pick up `render.yaml` automatically (free web service + 1GB persistent
   disk mounted at `/data` for the stats database).
3. Alternatively, create a **New > Web Service** manually:
   - Build command: `npm install`
   - Start command: `npm start`
   - Add a disk mounted at `/data` and set the env var
     `BEERDIE_DATA_DIR=/data` so your data survives redeploys (without a
     disk, Render's filesystem is wiped on every deploy).
4. Once deployed, Render gives you a public URL — share that with your group.

## Data storage

Stats are stored in a simple JSON file (`data/beerdie.json` locally, or
`$BEERDIE_DATA_DIR/beerdie.json` if that env var is set). No database setup
required.
