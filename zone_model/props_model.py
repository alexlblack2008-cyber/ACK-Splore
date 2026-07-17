"""
Player & Game Props Model
=========================
Identifies edges across ANY prop market where statistical value exists.
Not limited to mainstream lines — corners, cards, anytime scorer, alternate
totals, rushing attempts, first baskets, and more are all fair game.

Season-aware priority:
  NFL in season (Sep–Jan)  → NFL props + NBA + MLB
  NBA in season (Oct–Jun)  → NBA props + NFL (if active) + MLB
  MLB only (Jul–Aug break) → MLB + Soccer + MMA

Methodology:
  1. Fetch player/team game log from ESPN (last 10 where available)
  2. Compute rolling average and population std dev
  3. Compare to market line → z-score conviction
  4. Opponent adjustment: how generous is the defense/team at allowing this stat
  5. Edge = (adj_avg - line) / std → |z| >= 0.4 triggers a pick
  6. Confidence capped at 85%: 50% + |z| * 12%

Output: list of PropPick objects, sorted by |z| descending
"""
from __future__ import annotations
import json
import math
import os
import urllib.request
import urllib.error
import urllib.parse
import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
ODDS_BASE = "https://api.the-odds-api.com/v4"


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class PropPick:
    sport:          str
    player:         str           # player name or "TEAM" for team props
    team:           str
    prop_type:      str           # human-readable: "corners", "passing_yards", etc.
    line:           float
    recommendation: str           # "OVER" or "UNDER"
    player_avg:     float
    player_std:     float
    z_score:        float
    confidence:     float         # 0–1
    rationale:      list[str]
    matchup_note:   str = ""
    last_n_games:   list[float] = field(default_factory=list)
    market_key:     str = ""      # raw Odds API market key


# ── Season detection ───────────────────────────────────────────────────────────

def _active_seasons(today: date | None = None) -> dict[str, bool]:
    """Returns which major leagues are currently in season."""
    d = today or date.today()
    m = d.month
    return {
        "nfl":    m in (9, 10, 11, 12, 1),           # Sep–Jan
        "nba":    m in (10, 11, 12, 1, 2, 3, 4, 5, 6),# Oct–Jun
        "mlb":    m in (4, 5, 6, 7, 8, 9, 10),        # Apr–Oct (rough)
        "nhl":    m in (10, 11, 12, 1, 2, 3, 4, 5, 6),
        "soccer": True,                                # year-round leagues
        "mma":    True,
    }


def _sport_priority(today: date | None = None) -> list[tuple[str, list[str]]]:
    """
    Returns ordered list of (sport_key, [market_keys]) based on which
    leagues are currently most active.
    NFL and NBA take top priority in season; MLB drops to background Jul-Aug.
    """
    seasons = _active_seasons(today)

    priority: list[tuple[str, list[str]]] = []

    # NFL in season → leads
    if seasons["nfl"]:
        priority.append(("americanfootball_nfl", NFL_PROP_MARKETS))

    # NBA in season → second
    if seasons["nba"]:
        priority.append(("basketball_nba", NBA_PROP_MARKETS))

    # MLB (lower priority Jun–Aug, back up in playoff chase Sep–Oct)
    if seasons["mlb"]:
        priority.append(("baseball_mlb", MLB_PROP_MARKETS))

    # NHL
    if seasons["nhl"]:
        priority.append(("icehockey_nhl", NHL_PROP_MARKETS))

    # Soccer — high-profile competitions only (World Cup, CL, PL, major cups)
    for sk in SOCCER_SPORT_KEYS:
        priority.append((sk, SOCCER_PROP_MARKETS))
    # Skip lower-tier domestic leagues (La Liga, Bundesliga, MLS, etc.)

    # MMA — fighter props
    priority.append(("mma_mixed_martial_arts", MMA_PROP_MARKETS))

    return priority


# ── Market definitions ─────────────────────────────────────────────────────────

MLB_PROP_MARKETS = [
    # Pitcher
    "pitcher_strikeouts",
    "pitcher_outs",
    "pitcher_hits_allowed",
    "pitcher_walks",
    "pitcher_earned_runs",
    # Batter
    "batter_hits",
    "batter_total_bases",
    "batter_home_runs",
    "batter_runs_scored",
    "batter_rbis",
    "batter_stolen_bases",
    "batter_singles",
    "batter_doubles",
    # Team props
    "team_total_hits",
    "team_first_5_innings_runs",
    "alternate_strikeouts",        # alternate K lines (often juicier)
]

NFL_PROP_MARKETS = [
    # QB
    "player_pass_yds",
    "player_pass_attempts",
    "player_pass_tds",
    "player_pass_completions",
    "player_pass_interceptions",
    "player_pass_longest_completion",
    # RB
    "player_rush_yds",
    "player_rush_attempts",
    "player_rush_longest",
    "player_rush_tds",
    # WR/TE
    "player_reception_yds",
    "player_receptions",
    "player_receiving_tds",
    "player_receiving_longest",
    # Kicker
    "player_field_goals",
    "player_kicking_points",
    # First TD scorer
    "player_anytime_td",
    "player_first_td",
    # Defense
    "player_sacks",
    "player_solo_tackles",
    "player_tackles_assists",
    # Alternate lines (wider range, can find mispriced spots)
    "alternate_player_rush_yds",
    "alternate_player_reception_yds",
    "alternate_player_pass_yds",
]

NBA_PROP_MARKETS = [
    "player_points",
    "player_rebounds",
    "player_assists",
    "player_blocks",
    "player_steals",
    "player_turnovers",
    "player_threes",
    "player_points_rebounds_assists",
    "player_points_rebounds",
    "player_points_assists",
    "player_rebounds_assists",
    "player_blocks_steals",
    "player_double_double",
    "player_first_basket",
    # Alternate lines
    "alternate_player_points",
    "alternate_player_rebounds",
    "alternate_player_assists",
]

NHL_PROP_MARKETS = [
    "player_points",
    "player_goals",
    "player_assists",
    "player_shots_on_goal",
    "player_blocks",
    "player_saves",          # goalies
    "player_power_play_points",
    "player_anytime_goalscorer",
    "player_first_goalscorer",
]

# Soccer: corners, cards, shots are where the sharpest props live
SOCCER_PROP_MARKETS = [
    "btts",                  # both teams to score
    "team_corners",          # corner kick lines
    "player_shots_on_target",
    "player_shots",
    "player_assists",
    "player_anytime_goalscorer",
    "player_first_goalscorer",
    "player_to_receive_card",
    "team_total_corners",    # alternate phrasing
    "alternate_spreads",
    "alternate_totals",
]

MMA_PROP_MARKETS = [
    "fight_result",
    "fight_total_rounds",
    "method_of_victory",
    "fighter_to_win_by_ko",
    "fighter_to_win_by_submission",
    "fighter_to_win_by_decision",
]

# Soccer leagues to scan — high-profile competitions only
SOCCER_SPORT_KEYS = [
    "soccer_fifa_world_cup",              # World Cup (top priority)
    "soccer_uefa_champs_league",          # Champions League
    "soccer_uefa_europa_league",          # Europa League
    "soccer_epl",                         # Premier League
    "soccer_england_efl_cup",            # EFL Cup (Carabao)
    "soccer_fa_cup",                      # FA Cup
    "soccer_conmebol_copa_libertadores",  # Copa Libertadores
    "soccer_conmebol_copa_america",       # Copa América / international
    "soccer_uefa_euro",                   # European Championship
    "soccer_concacaf_gold_cup",           # CONCACAF Gold Cup
]


# ── Opponent adjustment tables ─────────────────────────────────────────────────

# NBA: how much each team allows relative to league average
NBA_DEF_ALLOWED = {
    "points": {
        "Golden State Warriors": 1.08, "Phoenix Suns": 1.12, "Brooklyn Nets": 1.14,
        "Charlotte Hornets": 1.15, "Washington Wizards": 1.18, "Atlanta Hawks": 1.10,
        "Boston Celtics": 0.88, "Oklahoma City Thunder": 0.90,
        "Minnesota Timberwolves": 0.91, "Cleveland Cavaliers": 0.92,
        "New York Knicks": 0.93, "Indiana Pacers": 1.07, "Sacramento Kings": 1.06,
        "Dallas Mavericks": 0.95, "Denver Nuggets": 0.97,
        "__default__": 1.0,
    },
    "rebounds":  {"__default__": 1.0},
    "assists":   {"__default__": 1.0},
    "threes":    {
        "Dallas Mavericks": 0.92, "Memphis Grizzlies": 0.94,
        "Golden State Warriors": 1.09, "Indiana Pacers": 1.07,
        "__default__": 1.0,
    },
    "blocks": {"__default__": 1.0},
}

# NFL: pace of play / defensive tendencies affecting passing / rushing
NFL_DEF_ALLOWED = {
    "passing_yards": {
        "Detroit Lions": 1.12, "Dallas Cowboys": 1.10, "Indianapolis Colts": 1.09,
        "Washington Commanders": 1.08, "Chicago Bears": 1.11,
        "San Francisco 49ers": 0.88, "Baltimore Ravens": 0.90,
        "Cleveland Browns": 0.91, "Pittsburgh Steelers": 0.92,
        "__default__": 1.0,
    },
    "rushing_yards": {
        "New Orleans Saints": 1.10, "Chicago Bears": 1.08,
        "San Francisco 49ers": 0.85, "Baltimore Ravens": 0.87,
        "__default__": 1.0,
    },
    "receiving_yards": {
        "Detroit Lions": 1.10, "Washington Commanders": 1.09,
        "San Francisco 49ers": 0.89, "Pittsburgh Steelers": 0.91,
        "__default__": 1.0,
    },
    "receptions": {"__default__": 1.0},
}

# MLB: pitcher opponent stats by team (how much does the opposing lineup hit)
MLB_LINEUP_STRENGTH = {
    # Above-average offenses (opposing pitchers face tougher lineups → more K opportunity)
    "Los Angeles Dodgers": 1.06, "Atlanta Braves": 1.05, "New York Yankees": 1.04,
    "Houston Astros": 1.03, "Philadelphia Phillies": 1.02,
    # Below-average offenses (easier to K, lower hit/TB totals)
    "Oakland Athletics": 0.92, "Kansas City Royals": 0.94, "Colorado Rockies": 0.93,
    "Chicago White Sox": 0.91, "Washington Nationals": 0.93,
    "__default__": 1.0,
}

# Soccer: which teams give up more corners / shots
SOCCER_CORNERS_ALLOWED = {
    "Manchester City": 1.12,     # high-press → lots of corners
    "Liverpool": 1.10,
    "Arsenal": 1.08,
    "Burnley": 1.15,             # low-block → concede corners
    "Crystal Palace": 1.13,
    "Tottenham Hotspur": 1.05,
    "__default__": 1.0,
}


def _opp_adjustment(prop_type: str, opponent: str, sport: str) -> float:
    """Returns a multiplier: 1.08 = opponent allows 8% more of this stat."""
    clean = prop_type.replace("alternate_", "").replace("player_", "")

    if sport == "nba":
        for key in (clean, prop_type):
            if key in NBA_DEF_ALLOWED:
                t = NBA_DEF_ALLOWED[key]
                return t.get(opponent, t["__default__"])

    elif sport == "nfl":
        for key in (clean, prop_type):
            if key in NFL_DEF_ALLOWED:
                t = NFL_DEF_ALLOWED[key]
                return t.get(opponent, t["__default__"])

    elif sport == "mlb":
        if clean in ("strikeouts", "hits", "total_bases", "home_runs"):
            return MLB_LINEUP_STRENGTH.get(opponent,
                   MLB_LINEUP_STRENGTH["__default__"])

    elif "soccer" in sport:
        if "corner" in clean:
            return SOCCER_CORNERS_ALLOWED.get(opponent,
                   SOCCER_CORNERS_ALLOWED["__default__"])

    return 1.0


# ── ESPN helpers ───────────────────────────────────────────────────────────────

def _espn_get(sport_path: str, endpoint: str) -> dict:
    url = f"{ESPN_BASE}/{sport_path}/{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _find_player_id(sport_path: str, player_name: str) -> Optional[str]:
    try:
        data = _espn_get(sport_path,
            f"athletes?limit=1000&search={urllib.parse.quote(player_name)}")
        items = data.get("items", []) or data.get("athletes", [])
        if items:
            return str(items[0].get("id") or
                       items[0].get("$ref", "").split("/")[-1])
    except Exception:
        pass
    return None


def _get_player_game_log(sport_path: str, player_id: str,
                          stat_key: str, n: int = 10) -> list[float]:
    """Fetch last n game values for a stat from ESPN game log."""
    try:
        data   = _espn_get(sport_path, f"athletes/{player_id}/gamelog")
        events = data.get("events", {})
        labels = data.get("labels", [])

        if stat_key not in labels:
            stat_key = next(
                (l for l in labels if l.lower() == stat_key.lower()), None)
            if not stat_key:
                return []

        idx    = labels.index(stat_key)
        values = []
        for _gid, stats_list in list(events.items())[-n:]:
            if isinstance(stats_list, list) and idx < len(stats_list):
                try:
                    values.append(float(stats_list[idx]))
                except (ValueError, TypeError):
                    pass
        return values[-n:]
    except Exception:
        return []


# ── ESPN stat key lookup ───────────────────────────────────────────────────────

# Maps our prop_type string → ESPN game log column label
ESPN_STAT_KEY_MAP: dict[str, str] = {
    # MLB pitcher
    "strikeouts":      "SO",
    "outs_recorded":   "IP",    # innings pitched used as proxy
    "hits_allowed":    "H",
    "walks":           "BB",
    "earned_runs":     "ER",
    # MLB batter
    "hits":            "H",
    "total_bases":     "TB",
    "home_runs":       "HR",
    "runs":            "R",
    "rbis":            "RBI",
    "stolen_bases":    "SB",
    # NFL
    "passing_yards":   "YDS",
    "pass_attempts":   "ATT",
    "pass_tds":        "TD",
    "pass_completions":"CMP",
    "rushing_yards":   "YDS",
    "rush_attempts":   "ATT",
    "receiving_yards": "YDS",
    "receptions":      "REC",
    # NBA
    "points":          "PTS",
    "rebounds":        "REB",
    "assists":         "AST",
    "blocks":          "BLK",
    "steals":          "STL",
    "turnovers":       "TO",
    "threes":          "3PM",
    # NHL
    "shots_on_goal":   "SOG",
    "saves":           "SV",
}

ESPN_SPORT_PATHS = {
    "baseball_mlb":         "baseball/mlb",
    "americanfootball_nfl": "football/nfl",
    "basketball_nba":       "basketball/nba",
    "icehockey_nhl":        "hockey/nhl",
}


# ── Odds API helpers ───────────────────────────────────────────────────────────

def _get_player_props(sport_key: str, event_id: str,
                       markets: list[str], api_key: str) -> dict:
    try:
        qs = urllib.parse.urlencode({
            "apiKey":     api_key,
            "regions":    "us",
            "markets":    ",".join(markets),
            "oddsFormat": "american",
        })
        url = f"{ODDS_BASE}/sports/{sport_key}/events/{event_id}/odds?{qs}"
        req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return {}


def _get_events(sport_key: str, api_key: str, game_date: str) -> list[dict]:
    try:
        qs = urllib.parse.urlencode({
            "apiKey":     api_key,
            "dateFormat": "iso",
            "oddsFormat": "american",
        })
        url = f"{ODDS_BASE}/sports/{sport_key}/odds?{qs}"
        req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            events = json.loads(r.read())
        return [e for e in events if game_date in e.get("commence_time", "")]
    except Exception:
        return []


# ── Core prop analyser ─────────────────────────────────────────────────────────

def analyse_prop(
    player_name:   str,
    team:          str,
    opponent:      str,
    sport:         str,      # short: "mlb", "nfl", "nba", "nhl", "soccer"
    sport_key:     str,      # full Odds API key e.g. "americanfootball_nfl"
    prop_type:     str,      # e.g. "strikeouts", "points", "corners"
    line:          float,
    last_n:        list[float] | None = None,
    espn_stat_key: str | None = None,
) -> Optional[PropPick]:
    """
    Analyses a single player (or team) prop.
    Returns PropPick if there's an edge, None if the line is fair.
    """
    # Get game log
    values = list(last_n) if last_n else []

    if not values and espn_stat_key:
        sp_path = ESPN_SPORT_PATHS.get(sport_key)
        if sp_path:
            try:
                pid = _find_player_id(sp_path, player_name)
                if pid:
                    values = _get_player_game_log(sp_path, pid, espn_stat_key, n=10)
            except Exception:
                pass

    if len(values) < 3:
        return None

    avg = sum(values) / len(values)
    variance = sum((v - avg) ** 2 for v in values) / len(values)
    std = math.sqrt(variance) if variance > 0 else max(0.5, avg * 0.15)

    # Opponent adjustment
    opp_mult = _opp_adjustment(prop_type, opponent, sport)
    adj_avg  = avg * opp_mult

    z = (adj_avg - line) / std
    confidence = min(0.85, 0.50 + abs(z) * 0.12)

    if abs(z) < 0.4:
        return None

    rec   = "OVER" if z > 0 else "UNDER"
    last5 = values[:5]

    hits_over  = sum(1 for v in values if v > line)
    hit_rate   = hits_over / len(values)

    rationale = [
        f"Last {len(values)}G avg: {avg:.1f}  (line: {line})  hit rate: {hit_rate:.0%} OVER",
        f"Std dev: {std:.2f}  →  z-score: {z:+.2f}",
        f"Opp ({opponent}) allows {opp_mult:.2f}x avg {prop_type}  →  adj avg: {adj_avg:.1f}",
        f"Last 5: {[round(v, 1) for v in last5]}",
    ]

    return PropPick(
        sport          = sport,
        player         = player_name,
        team           = team,
        prop_type      = prop_type,
        line           = line,
        recommendation = rec,
        player_avg     = round(avg, 2),
        player_std     = round(std, 2),
        z_score        = round(z, 3),
        confidence     = round(confidence, 3),
        rationale      = rationale,
        matchup_note   = f"opp mult {opp_mult:.2f}x",
        last_n_games   = values,
        market_key     = prop_type,
    )


# ── Batch scanner ──────────────────────────────────────────────────────────────

def _clean_prop_type(market_key: str) -> str:
    """Converts raw Odds API market key to readable prop_type label."""
    return (market_key
            .replace("player_", "")
            .replace("alternate_player_", "")
            .replace("alternate_", "")
            .replace("_", " "))


def scan_sport_props(sport_key: str, markets: list[str],
                     api_key: str, game_date: str) -> list[PropPick]:
    """Scans all player props for one sport on game_date. Returns edge picks."""
    sport_map = {
        "baseball_mlb":         "mlb",
        "americanfootball_nfl": "nfl",
        "basketball_nba":       "nba",
        "icehockey_nhl":        "nhl",
        "mma_mixed_martial_arts": "mma",
    }
    # Soccer keys all map to "soccer"
    sport = sport_map.get(sport_key, "soccer")

    events = _get_events(sport_key, api_key, game_date)
    if not events:
        return []

    picks: list[PropPick] = []

    for event in events:
        home     = event.get("home_team", "")
        away     = event.get("away_team", "")
        event_id = event.get("id", "")

        # Batch market requests in chunks of 10 (Odds API limit per call)
        for i in range(0, len(markets), 10):
            batch = markets[i:i + 10]
            props_data = _get_player_props(sport_key, event_id, batch, api_key)
            if not props_data:
                continue

            for bm in props_data.get("bookmakers", [])[:3]:
                for market in bm.get("markets", []):
                    mkey     = market.get("key", "")
                    prop_str = _clean_prop_type(mkey)

                    for outcome in market.get("outcomes", []):
                        player  = outcome.get("description") or outcome.get("name", "")
                        line    = outcome.get("point")
                        rec_raw = outcome.get("name", "").lower()

                        if line is None or rec_raw not in ("over", "under"):
                            continue

                        # Rough team assignment: player on home team if name contains
                        # home team keyword; otherwise mark as away
                        team     = home
                        opponent = away

                        # Try ESPN game log lookup
                        espn_key = ESPN_STAT_KEY_MAP.get(
                            prop_str.replace(" ", "_"), None)

                        pick = analyse_prop(
                            player_name   = player,
                            team          = team,
                            opponent      = opponent,
                            sport         = sport,
                            sport_key     = sport_key,
                            prop_type     = prop_str,
                            line          = float(line),
                            espn_stat_key = espn_key,
                        )
                        if pick:
                            picks.append(pick)

    # Deduplicate by player + prop, keep best z-score
    seen: dict[str, PropPick] = {}
    for p in picks:
        key = f"{p.player}:{p.prop_type}"
        if key not in seen or abs(p.z_score) > abs(seen[key].z_score):
            seen[key] = p

    return list(seen.values())


def scan_all_props(api_key: str, game_date: str,
                   max_picks: int = 8,
                   today: date | None = None) -> list[PropPick]:
    """
    Season-aware scan across all sports.
    NFL/NBA dominate when in season. Returns top max_picks by |z_score|.
    """
    priority = _sport_priority(today)
    all_picks: list[PropPick] = []

    for sport_key, markets in priority:
        try:
            picks = scan_sport_props(sport_key, markets, api_key, game_date)
            all_picks.extend(picks)
        except Exception:
            continue

    # Sort by |z| descending, then deduplicate across sports
    all_picks.sort(key=lambda p: abs(p.z_score), reverse=True)
    seen: dict[str, PropPick] = {}
    for p in all_picks:
        key = f"{p.player}:{p.prop_type}"
        if key not in seen:
            seen[key] = p

    return list(seen.values())[:max_picks]


# Legacy entry point kept for cron_entry.py compatibility
def scan_props_from_odds_api(sport_key: str, api_key: str,
                              game_date: str) -> list[PropPick]:
    """Scan a single sport. For multi-sport use scan_all_props()."""
    sport_markets = {
        "baseball_mlb":         MLB_PROP_MARKETS,
        "americanfootball_nfl": NFL_PROP_MARKETS,
        "basketball_nba":       NBA_PROP_MARKETS,
        "icehockey_nhl":        NHL_PROP_MARKETS,
        "mma_mixed_martial_arts": MMA_PROP_MARKETS,
    }
    markets = sport_markets.get(sport_key, SOCCER_PROP_MARKETS)
    return scan_sport_props(sport_key, markets, api_key, game_date)


# ── Formatting ─────────────────────────────────────────────────────────────────

def format_prop_pick(pick: PropPick) -> str:
    """Formats a PropPick for the daily report."""
    sym      = "▲" if pick.recommendation == "OVER" else "▼"
    bar_fill = round(pick.confidence * 10)
    conf_bar = "█" * bar_fill + "░" * (10 - bar_fill)
    sport_tag = pick.sport.upper()

    lines = [
        f"  ⬡ PROP [{sport_tag}]: {pick.player} ({pick.team})"
        f"  {sym} {pick.recommendation} {pick.line}"
        f" {pick.prop_type.upper()}",
        f"    Avg:{pick.player_avg:.1f}  Std:{pick.player_std:.2f}"
        f"  z={pick.z_score:+.2f}  Conf:{pick.confidence:.0%}  [{conf_bar}]",
    ]
    for r in pick.rationale:
        lines.append(f"    • {r}")
    lines.append(
        f"  **PROP PICK: {pick.recommendation} {pick.line}"
        f" {pick.player} {pick.prop_type}**"
    )
    return "\n".join(lines)
