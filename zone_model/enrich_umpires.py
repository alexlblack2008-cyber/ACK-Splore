"""
Noon second-pass: re-fetch umpire assignments for any TBD entries added today.
Runs at 12:00 UTC (8am ET) after umpire crews are posted by MLB.
Updates ledger.json umpire fields in-place for today's pending picks.
"""
from __future__ import annotations
import json
import os
import sys
from datetime import date, datetime, timezone

LEDGER_PATH = os.path.join(os.path.dirname(__file__), "ledger.json")
TARGET_DATE = date.today().isoformat()


def _get_todays_umpires() -> dict[str, str]:
    """
    Returns {game_key: umpire_name} for today's MLB games.
    game_key = "away_team vs home_team" (lowercased).
    """
    import urllib.request
    import urllib.error

    ump_map: dict[str, str] = {}
    try:
        url = (
            f"https://statsapi.mlb.com/api/v1/schedule"
            f"?sportId=1&date={TARGET_DATE}"
            f"&hydrate=officials,linescore"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ZoneModel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        for day in data.get("dates", []):
            for game in day.get("games", []):
                teams   = game.get("teams", {})
                home    = teams.get("home", {}).get("team", {}).get("name", "").lower()
                away    = teams.get("away", {}).get("team", {}).get("name", "").lower()
                key     = f"{away} vs {home}"
                officials = game.get("officials", [])
                for off in officials:
                    if off.get("officialType") == "Home Plate":
                        hp = off.get("official", {}).get("fullName", "")
                        if hp:
                            ump_map[key] = hp
                            break
    except Exception as e:
        print(f"[enrich_umpires] API fetch failed: {e}")

    return ump_map


def _fuzzy_match(away: str, home: str, ump_map: dict[str, str]) -> str:
    """Try several key variants to match a game in the umpire map."""
    # Exact key first
    key = f"{away.lower()} vs {home.lower()}"
    if key in ump_map:
        return ump_map[key]
    # Try just last word of team names (e.g. "tigers vs pirates")
    away_last = away.split()[-1].lower()
    home_last = home.split()[-1].lower()
    for k, v in ump_map.items():
        if away_last in k and home_last in k:
            return v
    return ""


def run() -> None:
    if not os.path.exists(LEDGER_PATH):
        print("[enrich_umpires] ledger.json not found — nothing to do")
        return

    with open(LEDGER_PATH) as f:
        ledger: list[dict] = json.load(f)

    # Find today's MLB pending picks with unknown umpires
    needs_update = [
        e for e in ledger
        if e.get("bet_date") == TARGET_DATE
        and e.get("sport") == "mlb"
        and e.get("outcome") == "pending"
        and e.get("umpire", "TBD") in ("TBD", "Unknown", "", None)
    ]

    if not needs_update:
        print("[enrich_umpires] No TBD umpires to update — all good")
        return

    print(f"[enrich_umpires] Found {len(needs_update)} TBD umpire(s) — fetching assignments...")
    ump_map = _get_todays_umpires()

    if not ump_map:
        print("[enrich_umpires] No umpire data returned from MLB API — try again later")
        return

    updated = 0
    for entry in ledger:
        if (entry.get("bet_date") == TARGET_DATE
                and entry.get("sport") == "mlb"
                and entry.get("outcome") == "pending"
                and entry.get("umpire", "TBD") in ("TBD", "Unknown", "", None)):
            home = entry.get("home_team", "")
            away = entry.get("away_team", "")
            ump  = _fuzzy_match(away, home, ump_map)
            if ump:
                entry["umpire"] = ump
                entry["umpire_enriched_at"] = datetime.now(timezone.utc).isoformat()
                print(f"  ✓ {away} @ {home} → {ump}")
                updated += 1
            else:
                print(f"  ✗ {away} @ {home} — still not posted")

    if updated:
        with open(LEDGER_PATH, "w") as f:
            json.dump(ledger, f, indent=2)
        print(f"[enrich_umpires] Updated {updated} entry/entries in ledger.json")
    else:
        print("[enrich_umpires] MLB hasn't posted assignments yet — will retry at next run")


if __name__ == "__main__":
    run()
