"""
NFL / NBA Daily Picks Engine
=============================
Primary pick source for NFL and NBA — runs independently of the bonus_pick
market-structure engine. Uses the statistical model (ESPN live stats +
offline profiles) to find totals and side edges worth betting.

Scoring:
  - Fair total computed from offensive/defensive efficiency (nfl_nba_model.py)
  - Edge = fair_total − market_total
  - Side lean = projected margin vs market spread
  - Confidence built from edge magnitude + data availability
  - Must clear MIN_EDGE_PTS and MIN_CONFIDENCE to qualify

Returned as a list of ScoredNFLNBAGame, sorted by edge × confidence.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

from nfl_nba_model import score_nfl_nba_game, StatModelOutput


# ── Thresholds ─────────────────────────────────────────────────────────────────

NFL_MIN_EDGE_PTS  = 2.5    # minimum point edge vs market total to issue a pick
NFL_MIN_CONF      = 0.48

NBA_MIN_EDGE_PTS  = 3.5
NBA_MIN_CONF      = 0.48


@dataclass
class ScoredNFLNBAGame:
    sport:          str        # "nfl" or "nba"
    home_team:      str
    away_team:      str
    commence:       str
    market_total:   float
    market_spread:  Optional[float]
    output:         StatModelOutput
    recommendation: str        # "OVER", "UNDER", or "NO BET"
    side_rec:       str        # "HOME", "AWAY", or "NEUTRAL"
    score:          float      # |edge| × confidence (ranking key)


def _fetch_games(sport_key: str, game_date: str) -> list[dict]:
    """Pull today's games from The Odds API for a given sport."""
    import json, urllib.request, urllib.error, urllib.parse, time
    try:
        from live.odds_client import load_dotenv, _api_key
        load_dotenv()
        api_key = _api_key()
    except Exception:
        return []

    base = "https://api.the-odds-api.com/v4"
    params = {
        "apiKey":    api_key,
        "regions":   "us",
        "markets":   "spreads,totals",
        "oddsFormat": "american",
        "dateFormat": "iso",
    }
    qs  = urllib.parse.urlencode(params)
    url = f"{base}/sports/{sport_key}/odds?{qs}"

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                raw = json.loads(r.read())
            return [ev for ev in raw if game_date in ev.get("commence_time", "")]
        except Exception:
            if attempt == 2:
                return []
            time.sleep(2 ** attempt)
    return []


def _parse_odds(ev: dict) -> tuple[Optional[float], Optional[float]]:
    """Extract median spread (home) and total from bookmaker odds."""
    spreads, totals = [], []
    for bm in ev.get("bookmakers", []):
        for mkt in bm.get("markets", []):
            if mkt["key"] == "spreads":
                for oc in mkt.get("outcomes", []):
                    if oc.get("name") == ev.get("home_team"):
                        try:
                            spreads.append(float(oc["point"]))
                        except (KeyError, ValueError):
                            pass
            elif mkt["key"] == "totals":
                for oc in mkt.get("outcomes", []):
                    if oc.get("name") == "Over":
                        try:
                            totals.append(float(oc["point"]))
                        except (KeyError, ValueError):
                            pass

    def _median(vals):
        if not vals:
            return None
        s = sorted(vals)
        mid = len(s) // 2
        return s[mid] if len(s) % 2 else (s[mid-1] + s[mid]) / 2

    return _median(spreads), _median(totals)


def score_nfl_games(game_date: str | None = None) -> list[ScoredNFLNBAGame]:
    today = game_date or date.today().isoformat()
    events = _fetch_games("americanfootball_nfl", today)
    results = []

    for ev in events:
        home  = ev.get("home_team", "")
        away  = ev.get("away_team", "")
        spread, total = _parse_odds(ev)
        if total is None:
            total = 47.0   # NFL average fallback

        out = score_nfl_nba_game("nfl", home, away, total, spread)

        rec = "NO BET"
        if abs(out.edge_total) >= NFL_MIN_EDGE_PTS and out.confidence >= NFL_MIN_CONF:
            rec = "OVER" if out.edge_total > 0 else "UNDER"

        side_rec = "NEUTRAL"
        if out.side_edge >= 3.0:
            side_rec = "HOME"
        elif out.side_edge <= -3.0:
            side_rec = "AWAY"

        results.append(ScoredNFLNBAGame(
            sport         = "nfl",
            home_team     = home,
            away_team     = away,
            commence      = ev.get("commence_time", ""),
            market_total  = total,
            market_spread = spread,
            output        = out,
            recommendation= rec,
            side_rec      = side_rec,
            score         = abs(out.edge_total) * out.confidence,
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results


def score_nba_games(game_date: str | None = None) -> list[ScoredNFLNBAGame]:
    today = game_date or date.today().isoformat()
    events = _fetch_games("basketball_nba", today)
    results = []

    for ev in events:
        home  = ev.get("home_team", "")
        away  = ev.get("away_team", "")
        spread, total = _parse_odds(ev)
        if total is None:
            total = 230.0   # NBA average fallback

        out = score_nfl_nba_game("nba", home, away, total, spread)

        rec = "NO BET"
        if abs(out.edge_total) >= NBA_MIN_EDGE_PTS and out.confidence >= NBA_MIN_CONF:
            rec = "OVER" if out.edge_total > 0 else "UNDER"

        side_rec = "NEUTRAL"
        if out.side_edge >= 4.0:
            side_rec = "HOME"
        elif out.side_edge <= -4.0:
            side_rec = "AWAY"

        results.append(ScoredNFLNBAGame(
            sport         = "nba",
            home_team     = home,
            away_team     = away,
            commence      = ev.get("commence_time", ""),
            market_total  = total,
            market_spread = spread,
            output        = out,
            recommendation= rec,
            side_rec      = side_rec,
            score         = abs(out.edge_total) * out.confidence,
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results


def format_nfl_nba_section(picks: list[ScoredNFLNBAGame], game_date: str) -> str:
    if not picks:
        return ""

    sport_label = {"nfl": "🏈 NFL", "nba": "🏀 NBA"}.get(picks[0].sport, picks[0].sport.upper())
    sep = "=" * 56
    lines = [
        "",
        sep,
        f"  {sport_label} PICKS  ◆  {game_date}",
        sep,
    ]

    qualifying = [p for p in picks if p.recommendation != "NO BET"]
    if not qualifying:
        lines += [f"  No qualifying {picks[0].sport.upper()} picks today.", sep]
        return "\n".join(lines)

    for i, p in enumerate(qualifying, 1):
        out = p.output
        spread_str = f"{p.market_spread:+.1f}" if p.market_spread is not None else "N/A"
        side_str   = f"  Side lean:  {p.side_rec}" if p.side_rec != "NEUTRAL" else ""

        lines += [
            f"\n  {picks[0].sport.upper()} PICK #{i}  →  {p.recommendation}  {p.market_total}",
            f"  {p.away_team}  @  {p.home_team}",
            f"  Spread:     Home {spread_str}",
            f"  Fair total: {out.fair_total:.1f}   Edge: {out.edge_total:+.1f} pts",
            f"  Proj:       {p.home_team} {out.home_pts_proj:.1f}  /  {p.away_team} {out.away_pts_proj:.1f}",
            f"  Confidence: {out.confidence:.0%}",
        ]
        if side_str:
            lines.append(side_str)
        lines.append("  Research:")
        for r in out.rationale[:4]:
            lines.append(f"    • {r}")
        lines.append("  ·" * 28)

    lines += ["", sep]
    return "\n".join(lines)
