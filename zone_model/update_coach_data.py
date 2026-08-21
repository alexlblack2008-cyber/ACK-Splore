"""
Coach / Team Season Stats Updater
===================================
Runs daily alongside update_umpire_data.py. Pulls current-season team stats
from the ESPN public API for NFL and NBA and writes coach_season_stats.json.

The static coach profiles (nfl_coaches.py / nba_coaches.py) capture coaching
philosophy and style — those don't change. This script updates the *performance*
numbers that drift week-by-week: pts_per_game, pace, pass_rate, defensive
intensity, etc.

nfl_nba_model.py loads coach_season_stats.json at runtime and merges it on top
of the static profiles so the model always uses the freshest numbers.
"""
from __future__ import annotations
import json
import os
import urllib.request
import urllib.error
from datetime import date, datetime, timezone
from typing import Optional

STATS_PATH   = os.path.join(os.path.dirname(__file__), "coach_season_stats.json")
ESPN_BASE    = "https://site.api.espn.com/apis/site/v2/sports"
TIMEOUT      = 10


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _stat_from_cats(cats: dict, cat_name: str, stat_name: str,
                    default: float = 0.0) -> float:
    cat = cats.get(cat_name, {})
    for s in cat.get("stats", []):
        if s.get("name", "").lower() == stat_name.lower():
            return _safe_float(s.get("value"), default)
    return default


# ── NFL fetcher ────────────────────────────────────────────────────────────────

NFL_TEAMS = [
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens",
    "Buffalo Bills", "Carolina Panthers", "Chicago Bears",
    "Cincinnati Bengals", "Cleveland Browns", "Dallas Cowboys",
    "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars",
    "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers",
    "Los Angeles Rams", "Miami Dolphins", "Minnesota Vikings",
    "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers",
    "San Francisco 49ers", "Seattle Seahawks", "Tampa Bay Buccaneers",
    "Tennessee Titans", "Washington Commanders",
]

NBA_TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets",
    "Indiana Pacers", "Los Angeles Clippers", "Los Angeles Lakers",
    "Memphis Grizzlies", "Miami Heat", "Milwaukee Bucks", "Minnesota Timberwolves",
    "New Orleans Pelicans", "New York Knicks", "Oklahoma City Thunder",
    "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns",
    "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs",
    "Toronto Raptors", "Utah Jazz", "Washington Wizards",
]


def _find_team_id(sport: str, league: str, team_name: str) -> Optional[str]:
    try:
        data = _get(f"{ESPN_BASE}/{sport}/{league}/teams")
        for entry in (data.get("sports", [{}])[0]
                          .get("leagues", [{}])[0]
                          .get("teams", [])):
            t    = entry.get("team", {})
            name = t.get("displayName", "")
            if (team_name.lower() in name.lower() or
                    name.lower() in team_name.lower()):
                return t.get("id")
    except Exception:
        pass
    return None


def _fetch_nfl_team(team_name: str) -> Optional[dict]:
    """Fetch live NFL season stats for one team. Returns flattened dict or None."""
    try:
        tid = _find_team_id("football", "nfl", team_name)
        if not tid:
            return None

        data = _get(f"{ESPN_BASE}/football/nfl/teams/{tid}/statistics")
        cats = {c.get("name", ""): c
                for c in data.get("results", {})
                              .get("stats", {})
                              .get("categories", [])}

        s = lambda cat, stat, d=0.0: _stat_from_cats(cats, cat, stat, d)

        pts_off  = s("scoring",    "pointsPerGame")
        pts_def  = s("defensive",  "pointsAllowed") or s("scoring", "opponentPointsPerGame")
        ypp_off  = s("passing",    "yardsPerPlay") or s("general", "yardsPerPlay")
        pass_att = s("passing",    "passAttempts")
        tot_play = s("general",    "totalPlays", 1) or 1
        pass_rate = pass_att / tot_play if pass_att > 0 and tot_play > 0 else 0.0
        tov_diff = s("turnovers",  "turnoverDifferential")
        third_pct= s("conversions","thirdDownPct")
        rz_td    = s("redZone",    "redZoneScoringPct")
        sack_rate= s("defensive",  "sacksPerGame")

        # Derive tendencies from live stats vs league averages
        league_pts_avg = 23.0
        pts_adj = round((pts_off - league_pts_avg), 2) if pts_off > 0 else 0.0
        total_pts_adj = round(pts_adj - (pts_def - league_pts_avg if pts_def > 0 else 0.0), 2)

        return {
            "pts_per_game":        round(pts_off, 2),
            "pts_allowed":         round(pts_def, 2),
            "yards_per_play":      round(ypp_off, 2),
            "pass_rate":           round(pass_rate, 3),
            "turnover_diff":       round(tov_diff, 2),
            "third_down_pct":      round(third_pct, 3),
            "red_zone_td_pct":     round(rz_td, 3),
            "sacks_per_game":      round(sack_rate, 2),
            "pts_per_game_adj":    pts_adj,
            "total_pts_adj":       total_pts_adj,
        }
    except Exception as e:
        print(f"  [NFL] {team_name}: {e}")
        return None


def _fetch_nba_team(team_name: str) -> Optional[dict]:
    """Fetch live NBA season stats for one team. Returns flattened dict or None."""
    try:
        tid = _find_team_id("basketball", "nba", team_name)
        if not tid:
            return None

        data = _get(f"{ESPN_BASE}/basketball/nba/teams/{tid}/statistics")
        cats = {c.get("name", ""): c
                for c in data.get("results", {})
                              .get("stats", {})
                              .get("categories", [])}

        s = lambda cat, stat, d=0.0: _stat_from_cats(cats, cat, stat, d)

        pts_off    = s("scoring",   "avgPoints")
        pts_def    = s("defensive", "avgPointsAllowed") or s("scoring", "opponentAvgPoints")
        off_rtg    = s("advanced",  "offensiveRating")
        def_rtg    = s("advanced",  "defensiveRating")
        pace       = s("advanced",  "pace")
        efg_pct    = s("shooting",  "effectiveFgPct")
        tov_rate   = s("turnovers", "turnoverRatio")
        oreb_rate  = s("rebounds",  "offRebPct")
        three_rate = s("shooting",  "threePointAttemptRate")
        blk_per_g  = s("defensive", "avgBlocks")

        league_pts_avg  = 115.0
        league_pace_avg = 99.5
        pts_adj  = round(pts_off - league_pts_avg, 2) if pts_off > 0 else 0.0
        pace_adj = round(pace - league_pace_avg, 2) if pace > 0 else 0.0
        # Defensive intensity proxy: lower def_rating + higher blocks = more intense
        def_intensity = 0.50
        if def_rtg > 0:
            def_intensity = round(min(0.95, max(0.20,
                0.50 + (league_pts_avg - def_rtg) / 30.0)), 2)

        return {
            "pts_per_game":        round(pts_off, 2),
            "pts_allowed":         round(pts_def, 2),
            "off_rating":          round(off_rtg, 2),
            "def_rating":          round(def_rtg, 2),
            "pace":                round(pace, 2),
            "efg_pct":             round(efg_pct, 3),
            "tov_rate":            round(tov_rate, 3),
            "oreb_rate":           round(oreb_rate, 3),
            "three_rate":          round(three_rate, 3),
            "blocks_per_game":     round(blk_per_g, 2),
            "pts_per_game_adj":    pts_adj,
            "pace_adj":            pace_adj,
            "defensive_intensity": def_intensity,
            "total_pts_adj":       round(pts_adj + pace_adj * 0.3, 2),
        }
    except Exception as e:
        print(f"  [NBA] {team_name}: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def run() -> None:
    existing: dict = {}
    if os.path.exists(STATS_PATH):
        try:
            with open(STATS_PATH) as f:
                existing = json.load(f)
        except Exception:
            pass

    stats: dict = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "season_date": date.today().isoformat(),
        "nfl": existing.get("nfl", {}),
        "nba": existing.get("nba", {}),
    }

    print("── NFL team stats ──────────────────────────────────")
    nfl_updated = 0
    for team in NFL_TEAMS:
        result = _fetch_nfl_team(team)
        if result:
            stats["nfl"][team] = result
            nfl_updated += 1
            print(f"  ✓ {team}: {result['pts_per_game']:.1f} ppg off / "
                  f"{result['pts_allowed']:.1f} allowed")
        else:
            print(f"  — {team}: no data (kept cached)")

    print(f"\n── NBA team stats ──────────────────────────────────")
    nba_updated = 0
    for team in NBA_TEAMS:
        result = _fetch_nba_team(team)
        if result:
            stats["nba"][team] = result
            nba_updated += 1
            print(f"  ✓ {team}: {result['pts_per_game']:.1f} ppg  "
                  f"pace {result['pace']:.1f}  ORtg {result['off_rating']:.1f}")
        else:
            print(f"  — {team}: no data (kept cached)")

    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n[update_coach_data] Done — "
          f"NFL {nfl_updated}/{len(NFL_TEAMS)}  "
          f"NBA {nba_updated}/{len(NBA_TEAMS)}  "
          f"→ coach_season_stats.json")


if __name__ == "__main__":
    run()
