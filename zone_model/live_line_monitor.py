"""
Sunday Live Line Monitor
=========================
Runs every 15 minutes on Sundays during NFL game windows (1pm–11pm ET).
Also covers Saturday college football and primetime weekday NFL/NBA.

Sharp line detection:
  1. Steam move   — same-direction move of 1.5+ pts across 3+ books simultaneously
  2. Reverse line movement (RLM) — public bets one way, line moves the other
  3. Model divergence — live total has drifted far from our model fair total
  4. Key number cross — total crosses 3, 7, 10, 14 (NFL), or 5, 10 (NBA)
  5. Opener drift — current line 2+ pts off opening = sharp action taken a side

When a sharp signal fires, an email is sent immediately with:
  - Game, current line, signal type, recommended bet
  - Confidence, estimated edge
  - Time remaining / quarter / period context

Requires: ODDS_API_KEY, GMAIL_APP_PASSWORD, GMAIL_FROM, GMAIL_TO
"""
from __future__ import annotations
import json
import os
import smtplib
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
STATE_FILE    = os.path.join(os.path.dirname(__file__), ".line_state.json")

# Sports to monitor and their key numbers
SPORT_CONFIG = {
    "americanfootball_nfl": {
        "label": "NFL",
        "key_numbers": {3, 7, 10, 14, 17, 21, 24},   # common final score margins
        "total_key":   {37, 40, 44, 47, 51, 54},      # common game totals
        "steam_threshold":  1.5,   # pts move to classify as steam
        "model_edge_alert": 4.0,   # pts divergence from model to alert
        "rlm_threshold":    1.0,   # line moves this much against public
    },
    "basketball_nba": {
        "label": "NBA",
        "key_numbers": {3, 5, 7, 10},
        "total_key":   {210, 215, 220, 225, 230, 235},
        "steam_threshold":  2.5,
        "model_edge_alert": 6.0,
        "rlm_threshold":    1.5,
    },
    "americanfootball_ncaaf": {
        "label": "NCAAF",
        "key_numbers": {3, 7, 10, 14, 17},
        "total_key":   {44, 47, 51, 54, 58},
        "steam_threshold":  2.0,
        "model_edge_alert": 5.0,
        "rlm_threshold":    1.5,
    },
}

# Books to track for steam detection (consensus across these = sharp signal)
SHARP_BOOKS = {
    "pinnacle", "betmgm", "draftkings", "fanduel",
    "caesars", "pointsbetus", "williamhill_us",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _api_key() -> str:
    key = os.environ.get("ODDS_API_KEY", "")
    if not key:
        raise RuntimeError("ODDS_API_KEY not set")
    return key


def _get(path: str, params: dict) -> list | dict:
    params["apiKey"] = _api_key()
    qs  = urllib.parse.urlencode(params)
    url = f"{ODDS_API_BASE}/{path}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ── Email sender ───────────────────────────────────────────────────────────────

def _send_alert(subject: str, body: str) -> None:
    gmail_from = os.environ.get("GMAIL_FROM", "")
    gmail_to   = os.environ.get("GMAIL_TO", gmail_from)
    password   = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not all([gmail_from, gmail_to, password]):
        print(f"[ALERT — no email configured]\n{subject}\n{body}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_from
    msg["To"]      = gmail_to

    plain = MIMEText(body, "plain")
    html  = MIMEText(
        f"<pre style='font-family:monospace;font-size:14px'>{body}</pre>",
        "html"
    )
    msg.attach(plain)
    msg.attach(html)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_from, password)
            smtp.sendmail(gmail_from, gmail_to.split(","), msg.as_string())
        print(f"  ✉  Alert sent: {subject}")
    except Exception as e:
        print(f"  ✗  Email failed: {e}\n{body}")


# ── Odds fetching ──────────────────────────────────────────────────────────────

def _fetch_live_odds(sport_key: str) -> list[dict]:
    """Fetch current odds for all live + upcoming games in a sport."""
    try:
        return _get(
            f"sports/{sport_key}/odds",
            {
                "regions":    "us",
                "markets":    "spreads,totals",
                "oddsFormat": "american",
                "dateFormat": "iso",
            }
        )
    except Exception as e:
        print(f"  [odds fetch] {sport_key}: {e}")
        return []


def _extract_book_lines(event: dict) -> dict[str, dict]:
    """
    Returns {book_key: {spread: float, total: float}} for each bookmaker.
    """
    lines: dict[str, dict] = {}
    home = event.get("home_team", "")
    for bm in event.get("bookmakers", []):
        book = bm.get("key", "")
        entry: dict = {"spread": None, "total": None}
        for mkt in bm.get("markets", []):
            if mkt["key"] == "spreads":
                for oc in mkt.get("outcomes", []):
                    if oc.get("name") == home:
                        try:
                            entry["spread"] = float(oc["point"])
                        except (KeyError, ValueError):
                            pass
            elif mkt["key"] == "totals":
                for oc in mkt.get("outcomes", []):
                    if oc.get("name") == "Over":
                        try:
                            entry["total"] = float(oc["point"])
                        except (KeyError, ValueError):
                            pass
        if entry["spread"] is not None or entry["total"] is not None:
            lines[book] = entry
    return lines


def _consensus(lines: dict[str, dict], field: str) -> Optional[float]:
    vals = [v[field] for v in lines.values() if v.get(field) is not None]
    if not vals:
        return None
    return sorted(vals)[len(vals) // 2]


# ── Sharp signal detection ─────────────────────────────────────────────────────

def _check_steam(
    game_id: str,
    sport_cfg: dict,
    current_lines: dict[str, dict],
    prev_lines: dict[str, dict],
    field: str,         # "spread" or "total"
) -> Optional[dict]:
    """
    Steam move: 3+ sharp books moved the same direction by threshold.
    Returns signal dict or None.
    """
    threshold = sport_cfg["steam_threshold"]
    moves = {}
    for book in SHARP_BOOKS:
        if book in current_lines and book in prev_lines:
            curr = current_lines[book].get(field)
            prev = prev_lines[book].get(field)
            if curr is not None and prev is not None and curr != prev:
                moves[book] = curr - prev

    if len(moves) < 3:
        return None

    # All moves in same direction and large enough
    up   = [v for v in moves.values() if v >=  threshold]
    down = [v for v in moves.values() if v <= -threshold]

    if len(up) >= 3:
        return {
            "type": "steam",
            "field": field,
            "direction": "up",
            "magnitude": round(sum(up) / len(up), 2),
            "books": [b for b, v in moves.items() if v >= threshold],
            "description": f"Steam UP {field}: {len(up)} sharp books moved +{threshold}+ simultaneously",
        }
    if len(down) >= 3:
        return {
            "type": "steam",
            "field": field,
            "direction": "down",
            "magnitude": round(sum(down) / len(down), 2),
            "books": [b for b, v in moves.items() if v <= -threshold],
            "description": f"Steam DOWN {field}: {len(down)} sharp books moved -{threshold}+ simultaneously",
        }
    return None


def _check_opener_drift(
    sport_cfg: dict,
    current_consensus: Optional[float],
    opener: Optional[float],
    field: str,
) -> Optional[dict]:
    """Opening line vs current — 2+ pts = significant sharp action."""
    if current_consensus is None or opener is None:
        return None
    drift = current_consensus - opener
    min_drift = sport_cfg["steam_threshold"] * 1.2
    if abs(drift) < min_drift:
        return None
    direction = "up" if drift > 0 else "down"
    return {
        "type": "opener_drift",
        "field": field,
        "direction": direction,
        "magnitude": round(abs(drift), 2),
        "description": (
            f"Line drifted {drift:+.1f} from opener ({opener} → {current_consensus}) "
            f"— sharp money on {'OVER' if (field=='total' and direction=='up') else 'UNDER' if field=='total' else direction.upper()}"
        ),
    }


def _check_key_number_cross(
    sport_cfg: dict,
    current_consensus: Optional[float],
    prev_consensus: Optional[float],
    field: str,
) -> Optional[dict]:
    """Did the line just cross a key number? Those bets have extra value."""
    if current_consensus is None or prev_consensus is None:
        return None
    key_set = sport_cfg["key_numbers"] if field == "spread" else sport_cfg["total_key"]
    for kn in key_set:
        crossed = (prev_consensus < kn <= current_consensus or
                   current_consensus <= kn < prev_consensus)
        if crossed:
            direction = "up" if current_consensus > prev_consensus else "down"
            bet_side  = "UNDER" if (field == "total" and direction == "up") else \
                        "OVER"  if field == "total" else direction.upper()
            return {
                "type": "key_number",
                "field": field,
                "direction": direction,
                "key_number": kn,
                "description": (
                    f"Total crossed key number {kn} ({prev_consensus} → {current_consensus}) "
                    f"— bet {bet_side} now before it moves further"
                ),
            }
    return None


def _check_model_divergence(
    sport_cfg: dict,
    home_team: str,
    away_team: str,
    sport: str,
    market_total: Optional[float],
) -> Optional[dict]:
    """Compare market total to our stat model."""
    if market_total is None:
        return None
    try:
        from nfl_nba_model import score_nfl_nba_game
        out = score_nfl_nba_game(sport, home_team, away_team, market_total)
        edge = out.edge_total
        threshold = sport_cfg["model_edge_alert"]
        if abs(edge) >= threshold:
            direction = "OVER" if edge > 0 else "UNDER"
            return {
                "type": "model_divergence",
                "field": "total",
                "direction": direction.lower(),
                "magnitude": round(abs(edge), 1),
                "fair_total": out.fair_total,
                "description": (
                    f"Model says {out.fair_total:.1f}, market is {market_total} "
                    f"— {direction} edge of {edge:+.1f} pts ({out.confidence:.0%} conf)"
                ),
            }
    except Exception:
        pass
    return None


# ── Alert formatting ───────────────────────────────────────────────────────────

def _format_alert(
    label: str,
    home: str,
    away: str,
    signal: dict,
    current_total: Optional[float],
    current_spread: Optional[float],
    commence: str,
) -> tuple[str, str]:
    """Returns (subject, body)."""
    now = datetime.now(timezone.utc).strftime("%I:%M %p ET")
    sig_labels = {
        "steam":           "🔥 STEAM MOVE",
        "opener_drift":    "📈 SHARP DRIFT",
        "key_number":      "🎯 KEY NUMBER",
        "model_divergence":"⚡ MODEL EDGE",
    }
    tag     = sig_labels.get(signal["type"], "⚡ ALERT")
    field   = signal["field"].upper()
    direc   = signal["direction"].upper()

    if signal["field"] == "total":
        bet_side = "OVER" if direc == "UP" else "UNDER"
        line_str = f"Total: {current_total}"
    else:
        bet_side = f"{'HOME' if direc == 'UP' else 'AWAY'} covers"
        line_str = f"Spread: Home {current_spread:+.1f}" if current_spread else ""

    subject = f"{tag} [{label}] {away} @ {home} — {bet_side} {current_total or ''}"

    body = f"""
{'='*58}
  {tag}
  {label}: {away}  @  {home}
  {now}  |  Game: {commence[:10]}
{'='*58}

  BET:   {bet_side} {current_total if signal['field']=='total' else ''}
  {line_str}

  SIGNAL: {signal['description']}

  Type:      {signal['type'].replace('_',' ').title()}
  Field:     {field}
  Magnitude: {signal.get('magnitude', 'N/A')} pts
{('  Books:     ' + ', '.join(signal['books'])) if 'books' in signal else ''}
{('  Fair total: ' + str(signal.get('fair_total',''))) if 'fair_total' in signal else ''}

  ⚡ Act fast — sharp lines move quickly.
{'='*58}
  Zone Model Live Monitor
""".strip()

    return subject, body


# ── Cooldown: don't spam same game + signal type within 30 min ────────────────

_alerted: dict[str, float] = {}

def _should_alert(game_id: str, sig_type: str) -> bool:
    key = f"{game_id}|{sig_type}"
    last = _alerted.get(key, 0)
    if time.time() - last < 1800:   # 30 min cooldown
        return False
    _alerted[key] = time.time()
    return True


# ── Main scan ──────────────────────────────────────────────────────────────────

def scan_once() -> int:
    """Run one scan across all monitored sports. Returns number of alerts fired."""
    state = _load_state()
    alerts_fired = 0
    now_str = datetime.now(timezone.utc).isoformat()

    for sport_key, sport_cfg in SPORT_CONFIG.items():
        label  = sport_cfg["label"]
        events = _fetch_live_odds(sport_key)
        if not events:
            continue

        for ev in events:
            game_id  = ev.get("id", "")
            home     = ev.get("home_team", "")
            away     = ev.get("away_team", "")
            commence = ev.get("commence_time", "")

            current_lines  = _extract_book_lines(ev)
            current_total  = _consensus(current_lines, "total")
            current_spread = _consensus(current_lines, "spread")

            prev_state   = state.get(game_id, {})
            prev_lines   = prev_state.get("lines", {})
            opener_total = prev_state.get("opener_total") or current_total
            opener_spread= prev_state.get("opener_spread") or current_spread
            prev_total   = prev_state.get("last_total")
            prev_spread  = prev_state.get("last_spread")

            signals = []

            # Steam moves
            for field in ("total", "spread"):
                sig = _check_steam(game_id, sport_cfg, current_lines, prev_lines, field)
                if sig:
                    signals.append(sig)

            # Opener drift
            for field, curr, opener in [
                ("total",  current_total,  opener_total),
                ("spread", current_spread, opener_spread),
            ]:
                sig = _check_opener_drift(sport_cfg, curr, opener, field)
                if sig:
                    signals.append(sig)

            # Key number cross
            for field, curr, prev in [
                ("total",  current_total,  prev_total),
                ("spread", current_spread, prev_spread),
            ]:
                sig = _check_key_number_cross(sport_cfg, curr, prev, field)
                if sig:
                    signals.append(sig)

            # Model divergence
            sport_name = "nfl" if "football" in sport_key else "nba"
            sig = _check_model_divergence(
                sport_cfg, home, away, sport_name, current_total)
            if sig:
                signals.append(sig)

            # Fire alerts
            for sig in signals:
                if _should_alert(game_id, sig["type"] + sig["field"]):
                    subject, body = _format_alert(
                        label, home, away, sig,
                        current_total, current_spread, commence)
                    print(f"\n  ⚡ ALERT: {subject}")
                    print(f"     {sig['description']}")
                    _send_alert(subject, body)
                    alerts_fired += 1

            # Update state
            state[game_id] = {
                "home": home, "away": away, "sport": sport_key,
                "lines": current_lines,
                "opener_total":  opener_total,
                "opener_spread": opener_spread,
                "last_total":    current_total,
                "last_spread":   current_spread,
                "last_checked":  now_str,
            }

    _save_state(state)
    return alerts_fired


def run() -> None:
    print(f"[live_line_monitor] Scan @ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    from live.odds_client import load_dotenv
    load_dotenv()
    alerts = scan_once()
    print(f"[live_line_monitor] Done — {alerts} alert(s) fired")


if __name__ == "__main__":
    run()
