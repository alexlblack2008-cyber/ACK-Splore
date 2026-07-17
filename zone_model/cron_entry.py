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
    Scan active major/elite golf tournaments for value picks.
    Only fires when a supported event is running or within 1 week.
    """
    try:
        from golf_model import ACTIVE_TOURNAMENTS, scan_tournament, format_golf_pick
        if not ACTIVE_TOURNAMENTS:
            return ""
        lines = [
            "",
            "=" * 56,
            "  GOLF VALUE PICKS",
            "=" * 56,
        ]
        for event in ACTIVE_TOURNAMENTS:
            course_name  = event.get("course")
            player_odds  = event.get("player_odds", {})
            bankroll     = float(os.environ.get("BANKROLL", "1000"))
            if not course_name or not player_odds:
                continue
            picks = scan_tournament(course_name, player_odds, bankroll=bankroll)
            if picks:
                lines.append(f"\n  {event.get('name', course_name).upper()}")
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
