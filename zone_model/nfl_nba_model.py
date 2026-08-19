"""
NFL / NBA Statistical Model
============================
Computes a statistically-derived fair total and side lean for NFL and NBA games.
This runs alongside the behavioral finance (Bonus Pick) layer — two independent
signals that are combined into a final recommendation.

NFL Stats Used:
  - Offensive points/yards per game
  - Defensive points/yards allowed per game
  - Turnover differential (turnovers forced vs given away)
  - Third down conversion rate (offense) / stop rate (defense)
  - Red zone TD% (offense) / red zone stop% (defense)
  - Pace: plays per game (fast pace = more possessions = more scoring)
  - Pass/rush balance (heavy pass = higher variance, more scoring upside)
  - Home field advantage (~2.5 pts in NFL)
  - Recent form (last 5 games scoring average)

NBA Stats Used:
  - Offensive rating (points per 100 possessions)
  - Defensive rating (points allowed per 100 possessions)
  - Pace (possessions per 48 minutes)
  - Effective FG% (eFG%)
  - Turnover rate
  - Offensive rebounding rate
  - Three-point attempt rate (high 3PA = more variance, boom/bust scoring)
  - Home court advantage (~3 pts in NBA)
  - Recent form

Methodology:
  1. Fetch team season stats from ESPN public API
  2. Build offensive / defensive efficiency ratings for each team
  3. Compute expected total: avg(home_off + away_off + home_def_allowed + away_def_allowed) / 2
  4. Apply pace adjustment, home field, and recent form
  5. Compare to market total → edge in runs/points
  6. Compute side lean from adjusted point differential
"""
from __future__ import annotations
import json
import math
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"

try:
    from nfl_teams import (
        NFL_OFFENSIVE_PROFILES, QB_PROP_PROFILES, SKILL_PLAYER_PROPS,
        NFL_LEAGUE_AVG as _NFL_OFF_AVG, NFL_DOME_TEAMS,
    )
    _NFL_PROFILES_AVAILABLE = True
except ImportError:
    _NFL_PROFILES_AVAILABLE = False
    NFL_DOME_TEAMS = set()


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class TeamStats:
    team_name:      str
    sport:          str
    # Scoring
    pts_per_game:   float = 0.0
    pts_allowed:    float = 0.0
    # Efficiency (NFL)
    yards_per_play_off: float = 0.0
    yards_per_play_def: float = 0.0
    turnover_diff:      float = 0.0   # positive = take more than give
    third_down_pct:     float = 0.0
    third_down_stop:    float = 0.0
    red_zone_td_pct:    float = 0.0
    red_zone_stop_pct:  float = 0.0
    pace_plays:         float = 0.0   # NFL: plays per game
    pass_rate:          float = 0.0
    # Efficiency (NBA)
    off_rating:         float = 0.0   # pts per 100 possessions
    def_rating:         float = 0.0
    pace_poss:          float = 0.0   # possessions per 48 min
    efg_pct:            float = 0.0
    tov_rate:           float = 0.0   # turnover % per possession
    oreb_rate:          float = 0.0
    three_rate:         float = 0.0   # 3PA per FGA
    # Common
    wins:           int   = 0
    losses:         int   = 0
    home_record:    str   = ""
    away_record:    str   = ""
    available:      bool  = False


@dataclass
class StatModelOutput:
    sport:          str
    home_team:      str
    away_team:      str
    market_total:   float
    fair_total:     float
    edge_total:     float          # fair - market (positive = lean OVER)
    home_pts_proj:  float
    away_pts_proj:  float
    side_edge:      float          # positive = home team favored vs spread
    confidence:     float          # 0-1
    rationale:      list[str]
    home_stats:     Optional[TeamStats] = None
    away_stats:     Optional[TeamStats] = None


# ── ESPN fetchers ──────────────────────────────────────────────────────────────

def _espn_get(sport: str, league: str, path: str) -> dict:
    url = f"{ESPN_BASE}/{sport}/{league}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read())


def _find_team_id(sport: str, league: str, team_name: str) -> Optional[str]:
    try:
        data = _espn_get(sport, league, "teams")
        for entry in (data.get("sports", [{}])[0]
                          .get("leagues", [{}])[0]
                          .get("teams", [])):
            t    = entry.get("team", {})
            name = t.get("displayName", "")
            abbr = t.get("abbreviation", "")
            if (team_name.lower() in name.lower() or
                    name.lower() in team_name.lower() or
                    team_name.upper() == abbr.upper()):
                return t.get("id")
    except Exception:
        pass
    return None


# ── NFL stats fetcher ──────────────────────────────────────────────────────────

# ESPN stat category IDs for NFL team stats
# Category 1 = passing, 2 = rushing, 3 = receiving, 17 = scoring, etc.
NFL_STAT_CATEGORIES = {
    "scoring":    "17",
    "passing":    "1",
    "rushing":    "2",
    "defense":    "4",
    "turnovers":  "8",
}

def _get_nfl_team_stats(team_name: str) -> TeamStats:
    stats = TeamStats(team_name=team_name, sport="nfl")
    try:
        tid = _find_team_id("football", "nfl", team_name)
        if not tid:
            return stats

        # ESPN team stats summary
        data = _espn_get("football", "nfl", f"teams/{tid}/statistics")
        cats = {c.get("name", ""): c
                for c in data.get("results", {})
                              .get("stats", {})
                              .get("categories", [])}

        def _stat(cat_name: str, stat_name: str, default: float = 0.0) -> float:
            cat = cats.get(cat_name, {})
            for s in cat.get("stats", []):
                if s.get("name", "").lower() == stat_name.lower():
                    try:
                        return float(s.get("value", default))
                    except (ValueError, TypeError):
                        return default
            return default

        stats.pts_per_game      = _stat("scoring",  "pointsPerGame")
        stats.pts_allowed       = _stat("defensive", "pointsAllowed") or \
                                   _stat("scoring",  "opponentPointsPerGame")
        stats.yards_per_play_off= _stat("passing",  "yardsPerPlay") or \
                                   _stat("general",  "yardsPerPlay")
        stats.turnover_diff     = _stat("turnovers", "turnoverDifferential")
        stats.third_down_pct    = _stat("conversions","thirdDownPct")
        stats.red_zone_td_pct   = _stat("redZone",   "redZoneScoringPct")
        stats.pass_rate         = _stat("passing",   "passAttempts") / max(
                                   _stat("general",  "totalPlays", 1), 1)

        # Pull record
        team_data = _espn_get("football", "nfl", f"teams/{tid}")
        record    = team_data.get("team", {}).get("record", {}).get("items", [])
        if record:
            stats.wins   = int(record[0].get("stats", [{}])[0].get("value", 0)
                               if record[0].get("stats") else 0)
            stats.losses = int(record[0].get("stats", [{}])[1].get("value", 0)
                               if len(record[0].get("stats", [])) > 1 else 0)

        stats.available = True
    except Exception:
        pass
    return stats


# ── NBA stats fetcher ──────────────────────────────────────────────────────────

def _get_nba_team_stats(team_name: str) -> TeamStats:
    stats = TeamStats(team_name=team_name, sport="nba")
    try:
        tid = _find_team_id("basketball", "nba", team_name)
        if not tid:
            return stats

        data = _espn_get("basketball", "nba", f"teams/{tid}/statistics")
        cats = {c.get("name", ""): c
                for c in data.get("results", {})
                              .get("stats", {})
                              .get("categories", [])}

        def _stat(cat_name: str, stat_name: str, default: float = 0.0) -> float:
            cat = cats.get(cat_name, {})
            for s in cat.get("stats", []):
                if s.get("name", "").lower() == stat_name.lower():
                    try:
                        return float(s.get("value", default))
                    except (ValueError, TypeError):
                        return default
            return default

        stats.pts_per_game  = _stat("scoring",  "avgPoints")
        stats.pts_allowed   = _stat("defensive", "avgPointsAllowed") or \
                               _stat("scoring",  "opponentAvgPoints")
        stats.off_rating    = _stat("advanced",  "offensiveRating")
        stats.def_rating    = _stat("advanced",  "defensiveRating")
        stats.pace_poss     = _stat("advanced",  "pace")
        stats.efg_pct       = _stat("shooting",  "effectiveFgPct")
        stats.tov_rate      = _stat("turnovers", "turnoverRatio")
        stats.oreb_rate     = _stat("rebounds",  "offRebPct")
        stats.three_rate    = _stat("shooting",  "threePointAttemptRate")

        stats.available = True
    except Exception:
        pass
    return stats


# ── League averages (2024-25 season baselines) ────────────────────────────────

NFL_LEAGUE_AVG = {
    "pts_per_game":      23.0,   # each team scores ~23 pts → ~46 total
    "yards_per_play":     5.8,
    "third_down_pct":    0.395,
    "red_zone_td_pct":   0.575,
    "turnover_diff":     0.0,
    "pass_rate":         0.575,
    "home_advantage":    2.5,    # home team scores ~2.5 more pts
}

NBA_LEAGUE_AVG = {
    "pts_per_game":    115.0,
    "off_rating":      116.0,
    "def_rating":      116.0,
    "pace_poss":        99.5,
    "efg_pct":         0.535,
    "tov_rate":        0.133,
    "oreb_rate":       0.268,
    "home_advantage":    3.0,
}


# ── NFL fair total computation ─────────────────────────────────────────────────

def _nfl_fair_total(home: TeamStats, away: TeamStats,
                     market_total: float) -> tuple[float, float, float, list[str]]:
    """
    Returns (fair_total, home_proj, away_proj, rationale_bullets).
    Uses team pts_per_game and pts_allowed to project each side's score.
    """
    avg = NFL_LEAGUE_AVG

    # Pull from offline profiles if ESPN data unavailable
    def _off_pts(ts: TeamStats) -> float:
        if ts.available and ts.pts_per_game > 0:
            return ts.pts_per_game
        if _NFL_PROFILES_AVAILABLE:
            prof = NFL_OFFENSIVE_PROFILES.get(ts.team_name)
            if prof:
                return prof.pts_per_game
        return avg["pts_per_game"]

    # Projected score = avg of (team off avg) and (opponent def allowed)
    home_off  = _off_pts(home)
    home_def  = home.pts_allowed   if home.available  else avg["pts_per_game"]
    away_off  = _off_pts(away)
    away_def  = away.pts_allowed   if away.available  else avg["pts_per_game"]

    # Each team's projected score = blend of their offense vs opponent defense
    home_proj = (home_off + away_def) / 2 + avg["home_advantage"] / 2
    away_proj = (away_off + home_def) / 2 - avg["home_advantage"] / 2

    # Pace adjustment: high-pace offenses add ~1-2 pts above average
    home_pace_adj = 0.0
    away_pace_adj = 0.0
    if home.available and home.yards_per_play_off > 0:
        home_pace_adj = (home.yards_per_play_off - avg["yards_per_play"]) * 0.8
    elif _NFL_PROFILES_AVAILABLE:
        prof = NFL_OFFENSIVE_PROFILES.get(home.team_name)
        if prof:
            home_pace_adj = (prof.yards_per_play - avg["yards_per_play"]) * 0.8
    if away.available and away.yards_per_play_off > 0:
        away_pace_adj = (away.yards_per_play_off - avg["yards_per_play"]) * 0.8
    elif _NFL_PROFILES_AVAILABLE:
        prof = NFL_OFFENSIVE_PROFILES.get(away.team_name)
        if prof:
            away_pace_adj = (prof.yards_per_play - avg["yards_per_play"]) * 0.8
    home_proj += home_pace_adj
    away_proj += away_pace_adj

    # Turnover adjustment: each turnover swing ≈ ~3.5 pts expected value
    if home.available and home.turnover_diff != 0:
        home_proj += home.turnover_diff * 0.35
    if away.available and away.turnover_diff != 0:
        away_proj += away.turnover_diff * 0.35

    # Red zone efficiency: teams that score TDs (not FGs) in red zone score more
    if home.available and home.red_zone_td_pct > 0:
        rz_adj = (home.red_zone_td_pct - avg["red_zone_td_pct"]) * 6.0
        home_proj += rz_adj
    if away.available and away.red_zone_td_pct > 0:
        rz_adj = (away.red_zone_td_pct - avg["red_zone_td_pct"]) * 6.0
        away_proj += rz_adj

    # Third down: teams that convert more 3rd downs sustain drives → more pts
    if home.available and home.third_down_pct > 0:
        td_adj = (home.third_down_pct - avg["third_down_pct"]) * 8.0
        home_proj += td_adj
    if away.available and away.third_down_pct > 0:
        td_adj = (away.third_down_pct - avg["third_down_pct"]) * 8.0
        away_proj += td_adj

    # Dome stadium scoring boost (retractable/indoor = ~2.1 pts per game total)
    if _NFL_PROFILES_AVAILABLE and home.team_name in NFL_DOME_TEAMS:
        dome_boost = _NFL_OFF_AVG.get("dome_scoring_boost", 2.1) / 2
        home_proj += dome_boost
        away_proj += dome_boost

    home_proj = round(max(10.0, home_proj), 1)
    away_proj = round(max(7.0,  away_proj), 1)
    fair_total = round(home_proj + away_proj, 1)

    rationale = []
    if home.available:
        rationale.append(
            f"{home.team_name}: {home.pts_per_game:.1f} ppg off / "
            f"{home.pts_allowed:.1f} allowed  →  proj {home_proj:.1f} pts")
    if away.available:
        rationale.append(
            f"{away.team_name}: {away.pts_per_game:.1f} ppg off / "
            f"{away.pts_allowed:.1f} allowed  →  proj {away_proj:.1f} pts")
    if home.available and home.turnover_diff != 0:
        rationale.append(
            f"{home.team_name} turnover diff: {home.turnover_diff:+.1f} "
            f"({'takes' if home.turnover_diff > 0 else 'loses'} ball more)")
    if home.available and home.red_zone_td_pct > 0:
        rationale.append(
            f"{home.team_name} red zone TD%: {home.red_zone_td_pct:.0%} "
            f"(league avg {avg['red_zone_td_pct']:.0%})")

    edge = round(fair_total - market_total, 2)
    rationale.append(
        f"Stat model fair total: {fair_total}  Market: {market_total}  "
        f"Edge: {edge:+.1f} pts  →  {'OVER' if edge > 0 else 'UNDER'}")

    return fair_total, home_proj, away_proj, rationale


# ── NBA fair total computation ─────────────────────────────────────────────────

def _nba_fair_total(home: TeamStats, away: TeamStats,
                     market_total: float) -> tuple[float, float, float, list[str]]:
    """
    Returns (fair_total, home_proj, away_proj, rationale_bullets).
    Uses offensive/defensive rating and pace to project each side's score.
    """
    avg = NBA_LEAGUE_AVG

    home_off = home.off_rating  if (home.available and home.off_rating > 0) else avg["off_rating"]
    home_def = home.def_rating  if (home.available and home.def_rating > 0) else avg["def_rating"]
    away_off = away.off_rating  if (away.available and away.off_rating > 0) else avg["off_rating"]
    away_def = away.def_rating  if (away.available and away.def_rating > 0) else avg["def_rating"]

    home_pace = home.pace_poss if (home.available and home.pace_poss > 0) else avg["pace_poss"]
    away_pace = away.pace_poss if (away.available and away.pace_poss > 0) else avg["pace_poss"]
    game_pace = (home_pace + away_pace) / 2

    # Points = (off_rating + opponent_def_rating) / 2 * pace / 100
    home_proj = ((home_off + away_def) / 2) * (game_pace / 100)
    away_proj = ((away_off + home_def) / 2) * (game_pace / 100)

    # Home court
    home_proj += avg["home_advantage"] / 2
    away_proj -= avg["home_advantage"] / 2

    # eFG% adjustment: elite shooting teams score more than rating suggests
    if home.available and home.efg_pct > 0:
        efg_adj = (home.efg_pct - avg["efg_pct"]) * 30.0
        home_proj += efg_adj
    if away.available and away.efg_pct > 0:
        efg_adj = (away.efg_pct - avg["efg_pct"]) * 30.0
        away_proj += efg_adj

    # Turnover rate: high TOV rate costs possessions → lower scoring
    if home.available and home.tov_rate > 0:
        tov_adj = -(home.tov_rate - avg["tov_rate"]) * 40.0
        home_proj += tov_adj
    if away.available and away.tov_rate > 0:
        tov_adj = -(away.tov_rate - avg["tov_rate"]) * 40.0
        away_proj += tov_adj

    # Offensive rebounding: more OReb = more second-chance pts
    if home.available and home.oreb_rate > 0:
        oreb_adj = (home.oreb_rate - avg["oreb_rate"]) * 15.0
        home_proj += oreb_adj
    if away.available and away.oreb_rate > 0:
        oreb_adj = (away.oreb_rate - avg["oreb_rate"]) * 15.0
        away_proj += oreb_adj

    home_proj = round(max(85.0, home_proj), 1)
    away_proj = round(max(85.0, away_proj), 1)
    fair_total = round(home_proj + away_proj, 1)

    rationale = []
    if home.available:
        rationale.append(
            f"{home.team_name}: ORtg {home.off_rating:.1f} / DRtg {home.def_rating:.1f} "
            f"pace {home.pace_poss:.1f}  →  proj {home_proj:.1f} pts")
    if away.available:
        rationale.append(
            f"{away.team_name}: ORtg {away.off_rating:.1f} / DRtg {away.def_rating:.1f} "
            f"pace {away.pace_poss:.1f}  →  proj {away_proj:.1f} pts")

    game_pace_dir = "fast" if game_pace > avg["pace_poss"] + 1 else \
                    "slow" if game_pace < avg["pace_poss"] - 1 else "average"
    rationale.append(
        f"Game pace: {game_pace:.1f} poss/48min ({game_pace_dir}) — "
        f"league avg {avg['pace_poss']:.1f}")

    if home.available and home.efg_pct > 0:
        rationale.append(
            f"{home.team_name} eFG%: {home.efg_pct:.1%} "
            f"(league avg {avg['efg_pct']:.1%})")

    edge = round(fair_total - market_total, 2)
    rationale.append(
        f"Stat model fair total: {fair_total}  Market: {market_total}  "
        f"Edge: {edge:+.1f} pts  →  {'OVER' if edge > 0 else 'UNDER'}")

    return fair_total, home_proj, away_proj, rationale


# ── Main entry point ───────────────────────────────────────────────────────────

def _nba_scheme_notes(home_team: str, away_team: str) -> list[str]:
    """Adds defensive scheme context to the NBA game projection."""
    notes: list[str] = []
    try:
        from nba_defense import get_defense
        hd = get_defense(home_team)
        ad = get_defense(away_team)
        notes.append(
            f"{home_team} defense: {hd.primary_coverage} — "
            f"blitz rate {hd.blitz_frequency:.0%}, zone {hd.zone_frequency:.0%}, "
            f"paint {hd.paint_defense} / perimeter {hd.perimeter_defense}"
        )
        notes.append(
            f"{away_team} defense: {ad.primary_coverage} — "
            f"blitz rate {ad.blitz_frequency:.0%}, zone {ad.zone_frequency:.0%}, "
            f"paint {ad.paint_defense} / perimeter {ad.perimeter_defense}"
        )
        # Pace-of-play interaction with scheme
        if hd.primary_coverage == "switch_everything" and ad.primary_coverage == "switch_everything":
            notes.append("Both teams switch everything — expect more isolation scoring, higher variance")
        if hd.zone_frequency >= 0.15 or ad.zone_frequency >= 0.15:
            notes.append("Zone-heavy matchup — mid-range shots increase, pace likely slows")
    except Exception:
        pass
    return notes


def score_nfl_nba_game(sport: str, home_team: str, away_team: str,
                        market_total: float,
                        market_spread: Optional[float] = None) -> StatModelOutput:
    """
    Full statistical analysis for one NFL or NBA game.
    Returns StatModelOutput with fair total, side lean, and rationale.
    sport: "nfl" or "nba"
    market_spread: home team spread (negative = home favored)
    """
    if sport == "nfl":
        home_stats = _get_nfl_team_stats(home_team)
        away_stats = _get_nfl_team_stats(away_team)
        fair, home_proj, away_proj, rat = _nfl_fair_total(
            home_stats, away_stats, market_total)
    else:
        home_stats = _get_nba_team_stats(home_team)
        away_stats = _get_nba_team_stats(away_team)
        fair, home_proj, away_proj, rat = _nba_fair_total(
            home_stats, away_stats, market_total)
        rat += _nba_scheme_notes(home_team, away_team)

    edge_total = round(fair - market_total, 2)

    # Side edge: how many pts better is home than market spread implies
    proj_margin = home_proj - away_proj
    if market_spread is not None:
        # market_spread is from home's perspective (negative = home favored)
        # If we project home wins by 7 but market says -3, home is +4 value
        side_edge = round(proj_margin - (-market_spread), 2)
    else:
        side_edge = round(proj_margin, 2)

    # Confidence: based on how far fair total deviates from market
    pts_scale  = 3.5 if sport == "nfl" else 6.0
    edge_z     = abs(edge_total) / pts_scale
    confidence = min(0.80, 0.45 + edge_z * 0.12)

    return StatModelOutput(
        sport        = sport,
        home_team    = home_team,
        away_team    = away_team,
        market_total = market_total,
        fair_total   = fair,
        edge_total   = edge_total,
        home_pts_proj= home_proj,
        away_pts_proj= away_proj,
        side_edge    = side_edge,
        confidence   = confidence,
        rationale    = rat,
        home_stats   = home_stats,
        away_stats   = away_stats,
    )


def format_stat_model(output: StatModelOutput) -> str:
    """One-paragraph summary of the stat model output for the daily report."""
    direction = "OVER" if output.edge_total > 0 else "UNDER"
    side = (f"{output.home_team} covers" if output.side_edge > 1.5 else
            f"{output.away_team} covers" if output.side_edge < -1.5 else
            "line is close statistically")
    lines = [
        f"  ◈ STAT MODEL [{output.sport.upper()}]: "
        f"{output.away_team} @ {output.home_team}",
        f"    Proj: {output.away_team} {output.away_pts_proj:.0f} — "
        f"{output.home_team} {output.home_pts_proj:.0f}  "
        f"(Fair total: {output.fair_total:.0f}  Market: {output.market_total}  "
        f"Edge: {output.edge_total:+.1f} → {direction})",
        f"    Side: {side} (proj margin {output.side_edge:+.1f} vs spread)  "
        f"Conf: {output.confidence:.0%}",
    ]
    for r in output.rationale:
        lines.append(f"    • {r}")
    return "\n".join(lines)
