"""
College Football Picks Engine
==============================
Scores CFB game totals and sides using:
  - Team offensive / defensive efficiency (pts/game + pts allowed)
  - Pace adjustment (high-pace = more possessions = more scoring)
  - Coaching style (air_raid / spread = higher totals; run_heavy = lower)
  - Home field advantage (varies by venue)
  - Conference-level strength adjustment

When The Odds API has CFB lines, uses live market totals.
Falls back to profile-estimated totals when API is unavailable or out of credits.

Thresholds are tighter than NFL because CFB totals have more variance:
  MIN_EDGE: 4.0 pts  (vs 2.5 for NFL)
  MIN_CONF: 0.50
"""

from __future__ import annotations
import json
import math
import urllib.request
import urllib.parse
import urllib.error
import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

from cfb_teams import CFB_TEAM_PROFILES, CFB_LEAGUE_AVG

try:
    from intel_scraper import get_team_signals
    _INTEL_AVAILABLE = True
except ImportError:
    _INTEL_AVAILABLE = False
    def get_team_signals(t, s): return []


# ── Thresholds ─────────────────────────────────────────────────────────────

CFB_MIN_EDGE_PTS = 4.0
CFB_MIN_CONF     = 0.50

# Coaching style scoring multipliers
_STYLE_MULT = {
    "air_raid":   1.12,
    "spread":     1.06,
    "pro_style":  1.00,
    "run_heavy":  0.92,
    "option":     0.90,
}

# Conference SOS adjustments (vs national average; tougher conf = lower scoring)
_CONF_ADJ = {
    "SEC":          -1.8,
    "Big Ten":      -1.4,
    "Big 12":       +0.8,
    "ACC":          -0.4,
    "Mountain West": +1.2,
    "Independent":  -0.6,
}


@dataclass
class CFBModelOutput:
    home_pts_proj: float
    away_pts_proj: float
    fair_total:    float
    edge_total:    float      # fair_total - market_total
    side_edge:     float      # home_proj - away_proj - spread (positive = fade spread)
    confidence:    float
    rationale:     list[str] = field(default_factory=list)


@dataclass
class ScoredCFBGame:
    home_team:      str
    away_team:      str
    commence:       str
    market_total:   float
    market_spread:  Optional[float]
    output:         CFBModelOutput
    recommendation: str        # "OVER", "UNDER", or "NO BET"
    side_rec:       str        # "HOME", "AWAY", or "NEUTRAL"
    score:          float
    _offline:       bool = False


def _score_game(home: str, away: str,
                market_total: float,
                spread: Optional[float]) -> CFBModelOutput:
    """Core scoring logic using team profiles."""
    hp = CFB_TEAM_PROFILES.get(home)
    ap = CFB_TEAM_PROFILES.get(away)

    avg = CFB_LEAGUE_AVG
    hp_off  = hp.pts_per_game  if hp else avg["pts_per_game"]
    hp_def  = hp.pts_allowed   if hp else avg["pts_allowed"]
    ap_off  = ap.pts_per_game  if ap else avg["pts_per_game"]
    ap_def  = ap.pts_allowed   if ap else avg["pts_allowed"]

    # Expected scoring: each team's offense vs opposing defense
    home_pts = (hp_off + ap_def) / 2
    away_pts = (ap_off + hp_def) / 2

    rationale = []

    # Pace adjustment: high-pace teams add possessions → more scoring
    if hp:
        pace_adj = (hp.pace_plays - 68.0) * 0.06
        home_pts += pace_adj / 2
        away_pts += pace_adj / 2
        if abs(pace_adj) > 0.3:
            rationale.append(f"{home} pace {hp.pace_plays:.0f} plays/gm → {pace_adj:+.1f} pts total")

    # Coaching style multiplier (air_raid inflates scoring)
    if hp:
        hm = _STYLE_MULT.get(hp.coach_style, 1.0)
        home_pts *= hm
        if hm != 1.0:
            rationale.append(f"{home} ({hp.coach_style}) style mult {hm:.2f}")
    if ap:
        am = _STYLE_MULT.get(ap.coach_style, 1.0)
        away_pts *= am
        if am != 1.0:
            rationale.append(f"{away} ({ap.coach_style}) style mult {am:.2f}")

    # Home field advantage
    hfa = hp.home_field_boost if hp else 2.5
    home_pts += hfa / 2    # HFA splits between more home pts and fewer away pts
    away_pts -= hfa / 2
    rationale.append(f"Home field ({home}): +{hfa:.1f} pts advantage")

    # Conference SOS adjustment
    if hp and ap:
        h_conf_adj = _CONF_ADJ.get(hp.conference, 0.0)
        a_conf_adj = _CONF_ADJ.get(ap.conference, 0.0)
        combined_conf_adj = (h_conf_adj + a_conf_adj) / 2
        home_pts += combined_conf_adj / 2
        away_pts += combined_conf_adj / 2
        if abs(combined_conf_adj) > 0.5:
            rationale.append(f"Conference strength adj: {combined_conf_adj:+.1f} pts total")

    fair_total = home_pts + away_pts
    edge_total = fair_total - market_total

    # Side edge: projected margin vs market spread
    proj_margin = home_pts - away_pts
    side_edge = proj_margin - (spread if spread is not None else 0.0)

    # Confidence: based on data availability + edge magnitude
    data_score = 1.0 if (hp and ap) else (0.6 if (hp or ap) else 0.3)
    edge_score = min(1.0, abs(edge_total) / 8.0)
    conf_score = min(1.0, (hp.off_rating + ap.off_rating) / 180) if (hp and ap) else 0.5
    confidence = 0.40 * data_score + 0.35 * edge_score + 0.25 * conf_score

    rationale.append(
        f"Stat model: {home} {home_pts:.1f} / {away} {away_pts:.1f} → total {fair_total:.1f} "
        f"(market {market_total:.1f}, edge {edge_total:+.1f})"
    )

    return CFBModelOutput(
        home_pts_proj=round(home_pts, 1),
        away_pts_proj=round(away_pts, 1),
        fair_total=round(fair_total, 1),
        edge_total=round(edge_total, 1),
        side_edge=round(side_edge, 1),
        confidence=round(confidence, 3),
        rationale=rationale,
    )


def _fetch_cfb_games(game_date: str) -> list[dict]:
    """Fetch CFB games from The Odds API (americanfootball_ncaaf)."""
    try:
        from live.odds_client import load_dotenv, _api_key
        load_dotenv()
        api_key = _api_key()
    except Exception:
        return []

    params = {
        "apiKey":     api_key,
        "regions":    "us",
        "markets":    "spreads,totals",
        "oddsFormat": "american",
        "dateFormat": "iso",
    }
    url = ("https://api.the-odds-api.com/v4/sports/americanfootball_ncaaf/odds?"
           + urllib.parse.urlencode(params))

    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = json.loads(r.read())
            return [ev for ev in raw if game_date in ev.get("commence_time", "")]
        except Exception:
            if attempt == 1:
                return []
            time.sleep(2)
    return []


def _parse_odds(ev: dict) -> tuple[Optional[float], Optional[float]]:
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


def _cfb_offline_events(game_date: str) -> list[dict]:
    """Generate matchups from offline profiles for days when API is unavailable."""
    import random
    rng = random.Random(int(game_date.replace("-", "")))
    teams = list(CFB_TEAM_PROFILES.keys())
    rng.shuffle(teams)

    events = []
    pairs = [(teams[i], teams[i+1]) for i in range(0, len(teams)-1, 2)]
    for home, away in pairs[:10]:
        hp = CFB_TEAM_PROFILES[home]
        ap = CFB_TEAM_PROFILES[away]
        implied_total = round(
            (hp.pts_per_game + ap.pts_allowed + ap.pts_per_game + hp.pts_allowed) / 2, 1
        )
        implied_spread = round(
            ((hp.pts_per_game - hp.pts_allowed) - (ap.pts_per_game - ap.pts_allowed)) / 2, 1
        )
        events.append({
            "home_team":      home,
            "away_team":      away,
            "commence_time":  f"{game_date}T18:00:00Z",
            "_market_total":  implied_total,
            "_market_spread": implied_spread,
            "_offline":       True,
        })
    return events


def score_cfb_games(game_date: str | None = None) -> list[ScoredCFBGame]:
    today = game_date or date.today().isoformat()
    events = _fetch_cfb_games(today)
    offline = not bool(events)
    if offline:
        # Only generate offline picks on known CFB days (Thu-Sat)
        d = date.fromisoformat(today)
        if d.weekday() not in (3, 4, 5):  # Thu=3, Fri=4, Sat=5
            return []
        events = _cfb_offline_events(today)

    results = []
    for ev in events:
        home = ev.get("home_team", "")
        away = ev.get("away_team", "")

        if ev.get("_offline"):
            total  = ev["_market_total"]
            spread = ev["_market_spread"]
        else:
            spread, total = _parse_odds(ev)
            if total is None:
                total = CFB_LEAGUE_AVG["total_avg"]

        out = _score_game(home, away, total, spread)

        # Intel boost from injury/upgrade signals
        intel_signals = get_team_signals(home, "cfb") + get_team_signals(away, "cfb")
        intel_boost = sum(
            s["confidence"] * (0.03 if s.get("prop_impact") == ("over" if out.edge_total > 0 else "under") else -0.02)
            for s in intel_signals
        )
        adj_conf = min(0.85, max(0.30, out.confidence + intel_boost))

        rec = "NO BET"
        if abs(out.edge_total) >= CFB_MIN_EDGE_PTS and adj_conf >= CFB_MIN_CONF:
            rec = "OVER" if out.edge_total > 0 else "UNDER"

        side_rec = "NEUTRAL"
        if out.side_edge >= 4.0:
            side_rec = "HOME"
        elif out.side_edge <= -4.0:
            side_rec = "AWAY"

        results.append(ScoredCFBGame(
            home_team     = home,
            away_team     = away,
            commence      = ev.get("commence_time", ""),
            market_total  = total,
            market_spread = spread,
            output        = out,
            recommendation= rec,
            side_rec      = side_rec,
            score         = abs(out.edge_total) * adj_conf,
            _offline      = offline,
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results


def format_cfb_section(picks: list[ScoredCFBGame], game_date: str) -> str:
    if not picks:
        return ""

    qualifying = [p for p in picks if p.recommendation != "NO BET"]
    if not qualifying:
        return ""

    sep = "=" * 56
    lines = ["", sep, f"  🏈 CFB PICKS  ◆  {game_date}", sep]

    if any(p._offline for p in qualifying):
        lines.append("  ⚠ Lines estimated from team profiles (odds API unavailable)")

    for i, p in enumerate(qualifying[:5], 1):
        out = p.output
        spread_str = f"{p.market_spread:+.1f}" if p.market_spread is not None else "N/A"
        lines += [
            f"\n  CFB PICK #{i}  →  {p.recommendation}  {p.market_total}",
            f"  {p.away_team}  @  {p.home_team}",
            f"  Spread:     Home {spread_str}",
            f"  Fair total: {out.fair_total:.1f}   Edge: {out.edge_total:+.1f} pts",
            f"  Proj:       {p.home_team} {out.home_pts_proj:.1f}  /  {p.away_team} {out.away_pts_proj:.1f}",
            f"  Confidence: {out.confidence:.0%}",
        ]
        if p.side_rec != "NEUTRAL":
            lines.append(f"  Side lean:  {p.side_rec}")
        lines.append("  Research:")
        for r in out.rationale[:4]:
            lines.append(f"    • {r}")
        if _INTEL_AVAILABLE:
            sigs = get_team_signals(p.home_team, "cfb") + get_team_signals(p.away_team, "cfb")
            if sigs:
                lines.append("  Intel:")
                for s in sigs[:3]:
                    icon = {"injury": "🩹", "usage_up": "↑", "positive": "✓"}.get(s["signal_type"], "•")
                    lines.append(f"    {icon} {s['player']} ({s['source']}): {s['headline'][:80]}")
        lines.append("  ·" * 28)

    lines += ["", sep]
    return "\n".join(lines)
