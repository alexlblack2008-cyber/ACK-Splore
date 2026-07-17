"""
Cron entry point — called once daily by the CCR Routine trigger.

Runs the full Zone Model daily pipeline, prints the report, and emails
it directly to alex.l.black.2008@gmail.com via Gmail SMTP.

Required env vars (set on Render):
  ODDS_API_KEY        — The Odds API key
  GMAIL_APP_PASSWORD  — 16-char Gmail App Password (myaccount.google.com/apppasswords)
  GMAIL_FROM          — sending address (defaults to alex.l.black.2008@gmail.com)
  GMAIL_TO            — recipient address (defaults to alex.l.black.2008@gmail.com)
  BANKROLL            — paper bankroll in dollars (default 1000)
"""

import sys
import os
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from daily_picks import run_daily
from ledger import weekly_pnl_report
from datetime import date

GMAIL_FROM = os.environ.get("GMAIL_FROM", "alex.l.black.2008@gmail.com")
GMAIL_TO   = os.environ.get("GMAIL_TO",   "alex.l.black.2008@gmail.com")


def _send_email(subject: str, body: str) -> bool:
    """Send picks report via Gmail SMTP. Returns True on success."""
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not app_password:
        print("  [Email] GMAIL_APP_PASSWORD not set — skipping email.")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_FROM
        msg["To"]      = GMAIL_TO

        # Plain text version
        msg.attach(MIMEText(body, "plain"))

        # HTML version — monospace so the bet slip formatting looks right
        html = (
            "<html><body>"
            f"<pre style='font-family:monospace;font-size:14px;line-height:1.5'>{body}</pre>"
            "</body></html>"
        )
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_FROM, app_password)
            server.sendmail(GMAIL_FROM, GMAIL_TO, msg.as_string())

        print(f"  [Email] Sent to {GMAIL_TO} ✓")
        return True
    except Exception as e:
        print(f"  [Email] Failed: {e}")
        return False


def _props_section(today: str) -> str:
    """Season-aware props scan across all sports."""
    try:
        api_key = os.environ.get("ODDS_API_KEY", "")
        if not api_key:
            return ""
        from props_model import scan_all_props, format_prop_pick
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
    """Fetch live golf odds and scan for value picks."""
    try:
        from golf_model import ACTIVE_TOURNAMENTS, scan_tournament, format_golf_pick
        bankroll = float(os.environ.get("BANKROLL", "1000"))

        live_events = []
        api_key = os.environ.get("ODDS_API_KEY", "")
        if api_key:
            try:
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
            picks = scan_tournament(
                course_name,
                player_odds,
                top5_odds  = event.get("top5_odds"),
                top10_odds = event.get("top10_odds"),
                top20_odds = event.get("top20_odds"),
                bankroll   = bankroll,
            )
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

    full_report = report + props + golf

    # Monday P&L recap
    if date.today().weekday() == 0:
        recap = (
            "\n" + "=" * 56 + "\n"
            "  MONDAY WEEKLY RECAP\n"
            + "=" * 56 + "\n"
            + weekly_pnl_report()
        )
        full_report += recap

    print(full_report)

    # Email the report directly
    subject = f"Zone Model Picks — {today}"
    _send_email(subject, full_report)


if __name__ == "__main__":
    main()
