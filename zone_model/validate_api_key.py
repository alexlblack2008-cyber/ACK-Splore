"""Validates ODDS_API_KEY before the main pipeline runs."""
import os
import urllib.request
import urllib.parse

key = os.environ.get("ODDS_API_KEY", "")
if not key:
    print("ERROR: ODDS_API_KEY secret is not set — go to ACK-Splore Settings → Secrets → Actions")
    raise SystemExit(1)

try:
    params = urllib.parse.urlencode({"apiKey": key, "regions": "us", "markets": "totals"})
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds?{params}"
    with urllib.request.urlopen(url, timeout=8) as r:
        remaining = r.headers.get("x-requests-remaining", "?")
        used = r.headers.get("x-requests-used", "?")
        print(f"[Odds API] Key valid. Requests used: {used} / remaining: {remaining}")
except Exception as e:
    print(f"WARNING: Odds API check failed ({e}) — picks will use placeholder totals")
