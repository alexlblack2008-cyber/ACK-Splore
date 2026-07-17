"""
Cron entry point — called once daily by the CCR Routine trigger.

Runs the full Zone Model daily pipeline and prints the report.
The CCR trigger captures stdout and sends it as a push notification + email.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from daily_picks import run_daily
from ledger import weekly_pnl_report
from datetime import date

def _props_section(today: str) -> str:
    """
    Season-aware props scan across all sports.
    NFL/NBA lead when in season; soccer corners/cards/goals always scanned.
    """
    try:
        api_key = os.environ.get("ODDS_API_KEY", "")
        if not api_key:
            return ""
        from props_model import scan_all_props, format_prop_pick
        from datetime import date as _date
        picks = scan_all_props(api_key, today, max_picks=8)
        if not picks:
            return ""
        lines = [
            "",
            "=" * 56,
            "  PROP EDGES — ANY SPORT, ANY MARKET",
            "=" * 56,
        ]
        for p in picks:
            lines.append(format_prop_pick(p))
            lines.append("")
        return "\n".join(lines)
    except Exception:
        return ""

def _golf_section() -> str:
    """
    Fetch live DraftKings/FanDuel golf odds via The Odds API and scan for value.
    Falls back to ACTIVE_TOURNAMENTS if no API key or no live events found.
    """
    try:
        from golf_model import ACTIVE_TOURNAMENTS, scan_tournament, format_golf_pick
        bankroll = float(os.environ.get("BANKROLL", "1000"))

        # Try live odds first
        live_events = []
        api_key = os.environ.get("ODDS_API_KEY", "")
        if api_key:
            try:
                import sys
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), "live"))
                from odds_client import fetch_golf_odds
                live_events = fetch_golf_odds()
            except Exception:
                pass

        events = live_events if live_events else ACTIVE_TOURNAMENTS
        if not events:
            return ""

        lines = [
            "",
            "=" * 56,
            "  GOLF VALUE PICKS" + (" [LIVE ODDS: DK/FD]" if live_events else ""),
            "=" * 56,
        ]
        for event in events:
            course_name = event.get("course")
            player_odds = event.get("player_odds", {})
            if not course_name or not player_odds:
                continue
            picks = scan_tournament(course_name, player_odds, bankroll=bankroll)
            if picks:
                lines.append(f"\n  {event.get('tournament', event.get('name', course_name)).upper()}")
                for p in picks:
                    lines.append(format_golf_pick(p, bankroll=bankroll))
                    lines.append("")
        return "\n".join(lines) if len(lines) > 4 else ""
    except Exception:
        return ""


def main():
    today = date.today().isoformat()
    print(f"[Zone Model] Running daily picks for {today} …\n")

    report = run_daily(today, log_to_ledger=True)
    props  = _props_section(today)
    golf   = _golf_section()
    print(report + props + golf)

    # On Mondays, also print last week's full P&L
    if date.today().weekday() == 0:
        print("\n" + "=" * 56)
        print("  MONDAY WEEKLY RECAP")
        print("=" * 56)
        print(weekly_pnl_report())

if __name__ == "__main__":
    main()
