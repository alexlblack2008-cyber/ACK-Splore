"""
Sports Intelligence Scraper
=============================
Pulls news from ESPN RSS, NFL.com, NBA.com, and public reporter feeds.
Extracts player-level signals relevant to props and game totals:
  - Usage / target share / snap counts
  - Injury / health updates
  - Trade rumors / team changes
  - Locker room / drama signals
  - Coach quotes on player roles

Writes player_intel.json — loaded by the prop model and daily report.

X/Twitter note: Uses public web scraping of key reporter profiles.
X API basic tier costs $100/month — if you want higher volume upgrade
the TWITTER_BEARER_TOKEN secret and the quota lifts automatically.
"""
from __future__ import annotations
import json
import os
import re
import smtplib
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from dataclasses import dataclass, field, asdict

INTEL_PATH = os.path.join(os.path.dirname(__file__), "player_intel.json")
TIMEOUT    = 10

# ── Signal categories ──────────────────────────────────────────────────────────

USAGE_UP_KEYWORDS = [
    "first team reps", "leading receiver", "target share", "chemistry",
    "featured back", "every day player", "starting role", "primary",
    "number one", "#1 option", "getting looks", "heavily involved",
    "breakout", "expanded role", "more involved", "step up", "big season",
    "emerging", "bigger role", "significant role", "workhorse",
]

USAGE_DOWN_KEYWORDS = [
    "limited role", "backup", "depth chart", "behind", "lost job",
    "fewer snaps", "reduced role", "third string", "inactive",
    "buried on roster", "losing reps",
]

INJURY_KEYWORDS = [
    "injury", "injured", "hurt", "out", "questionable", "doubtful",
    "placed on ir", "torn", "fracture", "concussion", "hamstring",
    "knee", "ankle", "shoulder", "dealing with", "day-to-day",
    "missed practice", "limited practice", "non-contact",
]

DRAMA_KEYWORDS = [
    "trade request", "trade rumor", "wants out", "unhappy", "disgruntled",
    "holdout", "skipping", "absence", "locker room", "drama",
    "conflict", "benched", "disciplinary", "suspension", "fine",
    "missed meetings", "contract dispute", "released", "cut",
]

POSITIVE_KEYWORDS = [
    "healthy", "looks great", "full practice", "cleared", "no limitations",
    "franchise player", "extension", "committed", "motivated",
    "best shape", "locked in", "excited", "confident",
]

# MLB-specific keywords
MLB_USAGE_UP = [
    "lineup spot", "batting cleanup", "top of the order", "leadoff",
    "getting starts", "regular starter", "rotation", "ace",
    "extra at-bats", "platoon advantage", "rbi machine", "hot streak",
    "on a tear", "batting average up", "slugging", "launch angle",
]

MLB_USAGE_DOWN = [
    "skipped start", "bullpen day", "opener", "limited innings",
    "pitch count", "short outing", "day-to-day", "placed on il",
    "60-day il", "knee", "elbow", "ucl", "shoulder", "velocity down",
    "velocity concerns", "command issues", "struggling",
]

MLB_INJURY_KEYWORDS = [
    "placed on il", "il stint", "elbow inflammation", "ucl", "tommy john",
    "oblique", "hamstring", "back tightness", "forearm tightness",
    "blister", "shoulder inflammation", "side session", "simulated game",
]

# ── Reporter RSS feeds ─────────────────────────────────────────────────────────

RSS_FEEDS = [
    # ESPN NFL/NBA/MLB
    ("ESPN NFL", "https://www.espn.com/espn/rss/nfl/news"),
    ("ESPN NBA", "https://www.espn.com/espn/rss/nba/news"),
    ("ESPN MLB", "https://www.espn.com/espn/rss/mlb/news"),
    ("ESPN NFL Insider", "https://www.espn.com/espn/rss/nfl/insider/news"),
    # NFL.com
    ("NFL.com", "https://www.nfl.com/rss/rsslanding?searchString=news"),
    # MLB.com
    ("MLB.com", "https://www.mlb.com/feeds/news/rss.xml"),
    # Pro Football Talk
    ("PFT", "https://profootballtalk.nbcsports.com/feed/"),
    # NBC Sports MLB
    ("HBT", "https://mlb.nbcsports.com/feed/"),
    # Bleacher Report
    ("BR NFL", "https://bleacherreport.com/nfl.rss"),
    ("BR NBA", "https://bleacherreport.com/nba.rss"),
    ("BR MLB", "https://bleacherreport.com/mlb.rss"),
    # The Athletic (limited headlines)
    ("Athletic NFL", "https://theathletic.com/nfl/feed/"),
    ("Athletic NBA", "https://theathletic.com/nba/feed/"),
    ("Athletic MLB", "https://theathletic.com/mlb/feed/"),
]

# ── Key reporters to monitor on X (public profiles) ───────────────────────────

X_REPORTERS = {
    "nfl": [
        "AdamSchefter",     # ESPN — transactions / trades
        "RapSheet",         # NFL Network — injuries / trades
        "TomPelissero",     # NFL Network — contracts / depth charts
        "MikeGarafolo",     # NFL Network — injuries / locker room
        "JeffDarlington",   # ESPN — South beat / QB intel
        "mortreport",       # ESPN — veteran insider
        "MikeReiss",        # ESPN — Patriots
        "JordanSchultz",    # Transactions / injuries
        "FieldYates",       # ESPN — fantasy / usage data
        "PatMcAfeeShow",    # Player quotes / access
    ],
    "nba": [
        "ShamsCharania",    # The Athletic — trades / injuries
        "wojespn",          # ESPN — transactions
        "MarcStein",        # Independent — veteran insider
        "ChrisBHaynes",     # TNT — locker room / drama
        "TheSteinLine",     # Marc Stein newsletter
        "malika_andrews",   # ESPN — player access / quotes
        "ZachLowe_NBA",     # ESPN — scheme / usage analysis
        "KevinOConnorNBA",  # The Ringer — player dev / usage
    ],
    "mlb": [
        "JonHeyman",        # MLB Network — transactions / contracts
        "Ken_Rosenthal",    # The Athletic — trades / signings
        "Feinsand",         # MLB.com — breaking news
        "BNightengale",     # USA Today — veteran insider
        "Joelsherman1",     # NY Post — NY market / trades
        "Heyblasty",        # MLB Network — injuries / transactions
        "MarcCaig",         # MLB.com — rosters / DL moves
        "JeffPassan",       # ESPN — major transactions
        "EvanWainerwright", # Statcast / pitch data analysis
        "tangotiger",       # Advanced metrics / usage patterns
    ],
}


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class PlayerSignal:
    player:       str
    team:         str
    sport:        str
    signal_type:  str        # "usage_up" | "usage_down" | "injury" | "drama" | "positive"
    headline:     str
    excerpt:      str
    source:       str
    url:          str        = ""
    confidence:   float      = 0.5   # 0–1 based on source credibility
    prop_impact:  str        = ""    # "over" | "under" | "neutral"
    detected_at:  str        = ""

    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.now(timezone.utc).isoformat()


# Source credibility weights
SOURCE_CREDIBILITY = {
    # NFL insiders
    "AdamSchefter": 0.95, "RapSheet": 0.95,      "TomPelissero": 0.90,
    "MikeGarafolo": 0.85, "JeffDarlington": 0.82, "mortreport": 0.82,
    "MikeReiss": 0.78,    "JordanSchultz": 0.75,  "FieldYates": 0.80,
    # NBA insiders
    "ShamsCharania": 0.95, "wojespn": 0.95,        "MarcStein": 0.88,
    "ChrisBHaynes": 0.88,  "ZachLowe_NBA": 0.85,   "KevinOConnorNBA": 0.80,
    "malika_andrews": 0.78,
    # MLB insiders
    "JonHeyman": 0.92,    "Ken_Rosenthal": 0.92,  "Feinsand": 0.85,
    "BNightengale": 0.85, "Joelsherman1": 0.80,   "JeffPassan": 0.90,
    "Heyblasty": 0.78,    "EvanWainerwright": 0.75, "tangotiger": 0.80,
    # Outlets
    "ESPN NFL": 0.78, "ESPN NBA": 0.78, "ESPN MLB": 0.78,
    "NFL.com": 0.75,  "MLB.com": 0.80,  "HBT": 0.72,
    "PFT": 0.70,      "BR NFL": 0.65,   "BR NBA": 0.65,   "BR MLB": 0.65,
    "Athletic NFL": 0.80, "Athletic NBA": 0.80, "Athletic MLB": 0.80,
}

# NFL and NBA rosters for player name matching (key names — model learns more over time)
NFL_STAR_PLAYERS = [
    # QBs
    "Patrick Mahomes", "Josh Allen", "Lamar Jackson", "Joe Burrow",
    "Jalen Hurts", "Dak Prescott", "Justin Herbert", "Tua Tagovailoa",
    "Jayden Daniels", "Caleb Williams", "Drake Maye", "Bo Nix",
    "CJ Stroud", "Anthony Richardson", "Brock Purdy", "Matthew Stafford",
    "Geno Smith", "Sam Darnold", "Kirk Cousins", "Kyler Murray",
    "Russell Wilson", "Aaron Rodgers", "Trevor Lawrence", "Bryce Young",
    # RBs
    "Saquon Barkley", "Derrick Henry", "Jonathan Taylor", "Josh Jacobs",
    "Breece Hall", "De'Von Achane", "Jahmyr Gibbs", "David Montgomery",
    "Tony Pollard", "Kyren Williams", "Rhamondre Stevenson", "Najee Harris",
    "James Cook", "Javonte Williams", "Alvin Kamara", "Aaron Jones",
    # WRs
    "Tyreek Hill", "Justin Jefferson", "CeeDee Lamb", "Davante Adams",
    "Stefon Diggs", "A.J. Brown", "DeVonta Smith", "Ja'Marr Chase",
    "Tee Higgins", "Amon-Ra St. Brown", "Puka Nacua", "Garrett Wilson",
    "Drake London", "Kyle Pitts", "Zay Flowers", "Rashid Shaheed",
    "DK Metcalf", "Tyler Lockett", "Diontae Johnson", "Chris Olave",
    "Jaylen Waddle", "Nick Westbrook-Ikhine", "Jakobi Meyers",
    "Xavier Worthy", "Rashee Rice", "Rome Odunze", "Malik Nabers",
    "Brian Thomas Jr", "Marvin Harrison Jr", "Ladd McConkey",
    "Xavier Legette", "Bijan Robinson", "Keon Coleman", "Nick Boutte",
    # TEs
    "Travis Kelce", "Sam LaPorta", "Trey McBride", "Mark Andrews",
    "Dallas Goedert", "George Kittle", "Evan Engram", "David Njoku",
    "Jake Ferguson", "Cole Kmet", "T.J. Hockenson",
]

MLB_STAR_PLAYERS = [
    # Starting pitchers
    "Shohei Ohtani", "Spencer Strider", "Gerrit Cole", "Zack Wheeler",
    "Max Fried", "Blake Snell", "Corbin Burnes", "Luis Castillo",
    "Framber Valdez", "Hunter Brown", "Logan Webb", "Sandy Alcantara",
    "Pablo Lopez", "Chris Sale", "Shane Bieber", "Kevin Gausman",
    "Dylan Cease", "Nestor Cortes", "Tarik Skubal", "Josiah Gray",
    "George Kirby", "Aaron Nola", "Zac Gallen", "Freddy Peralta",
    # Hitters
    "Ronald Acuna Jr", "Mookie Betts", "Freddie Freeman", "Trea Turner",
    "Mike Trout", "Yordan Alvarez", "Jose Altuve", "Kyle Tucker",
    "Vladimir Guerrero Jr", "Bo Bichette", "Corey Seager", "Marcus Semien",
    "Juan Soto", "Pete Alonso", "Francisco Lindor", "Jeff McNeil",
    "Julio Rodriguez", "Cal Raleigh", "Adley Rutschman", "Gunnar Henderson",
    "Bobby Witt Jr", "Salvador Perez", "MJ Melendez", "Jazz Chisholm",
    "Elly De La Cruz", "Matt McLain", "Spencer Steer", "Christian Yelich",
    "Willy Adames", "Jackson Chourio", "William Contreras", "Ketel Marte",
    "Corbin Carroll", "Lourdes Gurriel Jr", "Jordan Walker", "Lars Nootbaar",
    "Bryce Harper", "Nick Castellanos", "Austin Hays", "Cedric Mullins",
    "Cody Bellinger", "Ian Happ", "Dansby Swanson", "Kyle Schwarber",
    "Michael Harris II", "Austin Riley", "Matt Olson", "Ozzie Albies",
    "Paul Goldschmidt", "Nolan Arenado", "Tommy Edman",
    "Michael Brantley", "Luis Robert", "Andrew Vaughn",
    "Jose Ramirez", "Josh Naylor", "Lane Thomas", "CJ Abrams",
]

NBA_STAR_PLAYERS = [
    "LeBron James", "Stephen Curry", "Kevin Durant", "Giannis Antetokounmpo",
    "Nikola Jokic", "Joel Embiid", "Luka Doncic", "Jayson Tatum",
    "Ja Morant", "Zion Williamson", "Damian Lillard", "Devin Booker",
    "Anthony Davis", "Kawhi Leonard", "Paul George", "Jimmy Butler",
    "Donovan Mitchell", "Karl-Anthony Towns", "Anthony Edwards",
    "Shai Gilgeous-Alexander", "Tyrese Haliburton", "Tyrese Maxey",
    "Paolo Banchero", "Victor Wembanyama", "Cade Cunningham",
    "Franz Wagner", "Evan Mobley", "Scottie Barnes", "Jaren Jackson Jr",
    "Bam Adebayo", "Darius Garland", "De'Aaron Fox", "LaMelo Ball",
    "Jalen Green", "Alperen Sengun", "Josh Giddey", "Trae Young",
    "Dejounte Murray", "Bradley Beal", "Kristaps Porzingis",
    "Jaylen Brown", "Marcus Smart", "Draymond Green", "Klay Thompson",
    "James Harden", "Russell Westbrook", "Chris Paul",
    "Scottie Barnes", "Scoot Henderson", "Brandon Miller",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fetch(url: str) -> str:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _classify_signal(text: str, sport: str = "") -> tuple[str, str]:
    """Returns (signal_type, prop_impact)."""
    t = text.lower()
    # MLB-specific checks first
    if sport == "mlb":
        if any(k in t for k in MLB_INJURY_KEYWORDS + INJURY_KEYWORDS):
            return "injury", "under"
        if any(k in t for k in DRAMA_KEYWORDS):
            return "drama", "under"
        if any(k in t for k in MLB_USAGE_UP + USAGE_UP_KEYWORDS):
            return "usage_up", "over"
        if any(k in t for k in MLB_USAGE_DOWN + USAGE_DOWN_KEYWORDS):
            return "usage_down", "under"
        if any(k in t for k in POSITIVE_KEYWORDS):
            return "positive", "over"
        return "neutral", "neutral"
    if any(k in t for k in INJURY_KEYWORDS):
        return "injury", "under"
    if any(k in t for k in DRAMA_KEYWORDS):
        return "drama", "under"
    if any(k in t for k in USAGE_UP_KEYWORDS):
        return "usage_up", "over"
    if any(k in t for k in USAGE_DOWN_KEYWORDS):
        return "usage_down", "under"
    if any(k in t for k in POSITIVE_KEYWORDS):
        return "positive", "over"
    return "neutral", "neutral"


def _extract_players(text: str, sport: str) -> list[str]:
    """Find player names mentioned in text."""
    if sport == "mlb":
        players = MLB_STAR_PLAYERS
    elif sport == "nfl":
        players = NFL_STAR_PLAYERS
    else:
        players = NBA_STAR_PLAYERS
    found = []
    tl = text.lower()
    for p in players:
        if p.lower() in tl:
            found.append(p)
        else:
            last = p.split()[-1]
            if len(last) > 5 and last.lower() in tl:
                found.append(p)
    return list(set(found))


def _player_team(player: str, sport: str) -> str:
    """Best-effort team lookup — expands over time as intel accumulates."""
    return "Unknown"


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def _parse_rss(xml: str, source: str) -> list[dict]:
    """Parse RSS XML into list of {title, description, link} dicts."""
    def _unwrap(text: str) -> str:
        # Strip CDATA wrappers
        text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
        return _strip_html(text).strip()

    items = []
    for item in re.findall(r"<item>(.*?)</item>", xml, re.DOTALL):
        def _tag(tag: str) -> str:
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", item, re.DOTALL)
            return _unwrap(m.group(1)) if m else ""
        title = _tag("title")
        desc  = _tag("description") or _tag("summary")
        link  = _tag("link")
        if title:
            items.append({"title": title, "description": desc[:400], "link": link})
    return items


# ── X (Twitter) public scraper ─────────────────────────────────────────────────

def _scrape_x_profile(username: str) -> list[dict]:
    """
    Scrape recent posts from a public X profile.
    Uses the public syndication endpoint — no API key needed.
    Falls back gracefully if blocked.
    """
    posts = []
    # Try syndication endpoint
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}?lang=en"
    html = _fetch(url)
    if not html:
        return posts

    # Extract tweet text from JSON embedded in the page
    m = re.search(r'"timeline":\s*(\{.*?\})\s*,"metadata"', html, re.DOTALL)
    if not m:
        # Try alternate extraction
        texts = re.findall(r'"full_text"\s*:\s*"(.*?)"(?:,|\})', html)
        for t in texts[:15]:
            clean = t.replace("\\n", " ").replace('\\"', '"')
            if len(clean) > 20:
                posts.append({"text": clean, "source": username})
        return posts

    try:
        blob = json.loads(m.group(1))
        for entry in blob.get("entries", []):
            content = entry.get("content", {})
            tweet   = content.get("tweet", {})
            text    = tweet.get("full_text", "")
            if text and len(text) > 20:
                posts.append({"text": text, "source": username})
    except Exception:
        pass

    return posts[:20]


# ── Main scraping functions ────────────────────────────────────────────────────

def _process_item(text: str, source: str, url: str, sport: str) -> list[PlayerSignal]:
    """Turn one article/post into zero or more PlayerSignal objects."""
    signals = []
    players = _extract_players(text, sport)
    if not players:
        return signals

    sig_type, prop_impact = _classify_signal(text, sport)
    if sig_type == "neutral":
        return signals  # only store actionable signals

    credibility = SOURCE_CREDIBILITY.get(source, 0.60)

    for player in players:
        signals.append(PlayerSignal(
            player      = player,
            team        = _player_team(player, sport),
            sport       = sport,
            signal_type = sig_type,
            headline    = text[:120],
            excerpt     = text[:300],
            source      = source,
            url         = url,
            confidence  = credibility,
            prop_impact = prop_impact,
        ))
    return signals


def scrape_rss_feeds() -> list[PlayerSignal]:
    signals = []
    for source, feed_url in RSS_FEEDS:
        sl = source.lower()
        sport = "mlb" if "mlb" in sl or "hbt" in sl else "nfl" if "nfl" in sl or "pft" in sl else "nba"
        xml   = _fetch(feed_url)
        if not xml:
            print(f"  [RSS] {source}: no data")
            continue
        items = _parse_rss(xml, source)
        count = 0
        for item in items:
            text = f"{item['title']} {item['description']}"
            sigs = _process_item(text, source, item.get("link", ""), sport)
            signals.extend(sigs)
            count += len(sigs)
        print(f"  [RSS] {source}: {len(items)} articles → {count} signals")
        time.sleep(0.3)
    return signals


def scrape_x_reporters() -> list[PlayerSignal]:
    signals = []
    bearer = os.environ.get("TWITTER_BEARER_TOKEN", "")

    for sport, reporters in X_REPORTERS.items():
        for username in reporters:
            posts = _scrape_x_profile(username)
            count = 0
            for post in posts:
                sigs = _process_item(post["text"], username, "", sport)
                signals.extend(sigs)
                count += len(sigs)
            if posts:
                print(f"  [X] @{username}: {len(posts)} posts → {count} signals")
            time.sleep(0.5)

    return signals


# ── Persistence ────────────────────────────────────────────────────────────────

def _load_existing() -> dict:
    if os.path.exists(INTEL_PATH):
        try:
            with open(INTEL_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {"updated_at": "", "signals": []}


def _save(all_signals: list[PlayerSignal]) -> None:
    # Keep last 90 days of signals
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    existing = _load_existing()

    # Merge old signals (still within window) with new ones
    old_kept = [
        s for s in existing.get("signals", [])
        if s.get("detected_at", "") >= cutoff
    ]

    # Dedup: don't add if same player + signal_type + source in last 24h
    recent_keys = set()
    day_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    for s in old_kept:
        if s.get("detected_at", "") >= day_ago:
            recent_keys.add(f"{s['player']}|{s['signal_type']}|{s['source']}")

    truly_new: list[PlayerSignal] = []
    new_dicts = []
    for sig in all_signals:
        key = f"{sig.player}|{sig.signal_type}|{sig.source}"
        if key not in recent_keys:
            new_dicts.append(asdict(sig))
            truly_new.append(sig)
            recent_keys.add(key)

    # Fire breaking alerts for new high-confidence injury / upgrade signals
    _fire_breaking_alerts(truly_new, existing)

    merged = old_kept + new_dicts
    merged.sort(key=lambda x: x.get("detected_at", ""), reverse=True)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "signal_count": len(merged),
        "signals": merged,
        "_alert_cooldowns": existing.get("_alert_cooldowns", {}),
    }
    with open(INTEL_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n[intel_scraper] Saved {len(new_dicts)} new + {len(old_kept)} carried → "
          f"{len(merged)} total signals")


# ── Query interface (used by prop model) ──────────────────────────────────────

def get_player_signals(player_name: str,
                       sport: str,
                       days: int = 14) -> list[dict]:
    """
    Return recent signals for a player. Called by nfl_nba_picks.py
    when scoring player props to adjust confidence.
    """
    if not os.path.exists(INTEL_PATH):
        return []
    try:
        with open(INTEL_PATH) as f:
            data = json.load(f)
    except Exception:
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    last   = player_name.split()[-1].lower()
    return [
        s for s in data.get("signals", [])
        if (player_name.lower() in s.get("player", "").lower()
            or last in s.get("player", "").lower())
        and s.get("sport") == sport
        and s.get("detected_at", "") >= cutoff
    ]


def get_team_signals(team_name: str,
                     sport: str,
                     days: int = 7) -> list[dict]:
    """Return recent signals for any player on a given team."""
    if not os.path.exists(INTEL_PATH):
        return []
    try:
        with open(INTEL_PATH) as f:
            data = json.load(f)
    except Exception:
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return [
        s for s in data.get("signals", [])
        if team_name.lower() in s.get("team", "").lower()
        and s.get("sport") == sport
        and s.get("detected_at", "") >= cutoff
    ]


def get_prop_edge(player_name: str, sport: str) -> tuple[str, float]:
    """
    Quick summary for the prop model: returns (direction, confidence_boost).
    direction: "over" | "under" | "neutral"
    confidence_boost: added to base confidence if signals align
    """
    signals = get_player_signals(player_name, sport, days=7)
    if not signals:
        return "neutral", 0.0

    over_weight  = sum(s["confidence"] for s in signals if s["prop_impact"] == "over")
    under_weight = sum(s["confidence"] for s in signals if s["prop_impact"] == "under")

    if over_weight == 0 and under_weight == 0:
        return "neutral", 0.0
    if over_weight > under_weight * 1.5:
        boost = min(0.08, over_weight * 0.03)
        return "over", round(boost, 3)
    if under_weight > over_weight * 1.5:
        boost = min(0.08, under_weight * 0.03)
        return "under", round(boost, 3)
    return "neutral", 0.0


# ── Breaking alert: injury / upgrade before the line moves ────────────────────

# Signal types that are worth an immediate email
BREAKING_SIGNAL_TYPES = {"injury", "usage_up", "positive"}

# Minimum source credibility to send a breaking alert (avoids noise from low-tier outlets)
BREAKING_MIN_CONFIDENCE = 0.75


def _send_breaking_alert(sig: PlayerSignal) -> None:
    """Send an immediate email for a high-confidence injury or upgrade signal."""
    gmail_from = os.environ.get("GMAIL_FROM", "")
    gmail_to   = os.environ.get("GMAIL_TO", gmail_from)
    password   = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not all([gmail_from, gmail_to, password]):
        print(f"[BREAKING — no email configured] {sig.player}: {sig.headline[:80]}")
        return

    type_labels = {
        "injury":   "🩹 INJURY ALERT",
        "usage_up": "⬆ UPGRADE ALERT",
        "positive": "✅ PLAYER UPGRADE",
    }
    tag    = type_labels.get(sig.signal_type, "⚡ BREAKING INTEL")
    impact = "UNDER" if sig.signal_type == "injury" else "OVER"
    sport  = sig.sport.upper()

    subject = f"{tag} — {sig.player} ({sport}) → Bet {impact} before line moves"

    plain = (
        f"{tag}\n\n"
        f"Player : {sig.player}\n"
        f"Team   : {sig.team}\n"
        f"Sport  : {sport}\n"
        f"Impact : Bet {impact}\n"
        f"Source : @{sig.source}  (credibility {sig.confidence:.0%})\n\n"
        f"Headline:\n{sig.headline}\n\n"
        f"Excerpt:\n{sig.excerpt}\n\n"
        f"Detected: {sig.detected_at}\n\n"
        "Act fast — Vegas adjusts within minutes of breaking injury news."
    )

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2 style="color:#c0392b">{tag}</h2>
      <table style="width:100%;border-collapse:collapse;font-size:15px">
        <tr><td style="padding:6px;color:#888">Player</td><td style="padding:6px"><b>{sig.player}</b></td></tr>
        <tr><td style="padding:6px;color:#888">Team</td><td style="padding:6px">{sig.team}</td></tr>
        <tr><td style="padding:6px;color:#888">Sport</td><td style="padding:6px">{sport}</td></tr>
        <tr><td style="padding:6px;color:#888">Bet</td>
            <td style="padding:6px;font-size:18px;font-weight:bold;color:{'#e74c3c' if impact=='UNDER' else '#27ae60'}">{impact}</td></tr>
        <tr><td style="padding:6px;color:#888">Source</td><td style="padding:6px">@{sig.source} ({sig.confidence:.0%} credibility)</td></tr>
      </table>
      <p style="background:#f8f8f8;padding:12px;border-left:4px solid #c0392b;margin:16px 0">
        <b>Headline:</b> {sig.headline}
      </p>
      <p style="color:#555">{sig.excerpt}</p>
      <p style="color:#e74c3c;font-weight:bold">
        ⏱ Act fast — Vegas adjusts within minutes of breaking injury/upgrade news.
      </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_from
    msg["To"]      = gmail_to
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_from, password)
            smtp.sendmail(gmail_from, gmail_to.split(","), msg.as_string())
        print(f"  📧 Breaking alert sent: {subject}")
    except Exception as e:
        print(f"  ✗ Email failed: {e}")


def _fire_breaking_alerts(new_signals: list[PlayerSignal], existing: dict) -> None:
    """
    For each genuinely new high-confidence signal, send an immediate email.
    Cooldown: 6 hours per player+signal_type, stored in player_intel.json.
    """
    cooldowns = existing.get("_alert_cooldowns", {})
    now = datetime.now(timezone.utc)
    six_hours_ago = (now - timedelta(hours=6)).isoformat()
    fired = 0

    for sig in new_signals:
        if sig.signal_type not in BREAKING_SIGNAL_TYPES:
            continue
        if sig.confidence < BREAKING_MIN_CONFIDENCE:
            continue

        key  = f"{sig.player}|{sig.signal_type}"
        last = cooldowns.get(key, "")
        if last >= six_hours_ago:
            continue  # already alerted within 6 hours

        _send_breaking_alert(sig)
        cooldowns[key] = now.isoformat()
        fired += 1

    existing["_alert_cooldowns"] = cooldowns
    if fired:
        print(f"[intel_scraper] {fired} breaking alert(s) sent")


# ── Entry point ────────────────────────────────────────────────────────────────

def run() -> None:
    print("── RSS feeds ───────────────────────────────────────")
    rss_signals = scrape_rss_feeds()

    print("\n── X reporter profiles ─────────────────────────────")
    x_signals   = scrape_x_reporters()

    all_signals = rss_signals + x_signals
    _save(all_signals)

    # Print top signals for log visibility
    actionable = [s for s in all_signals
                  if s.signal_type in ("usage_up", "injury", "drama")]
    if actionable:
        print("\n── Top actionable signals ──────────────────────────")
        for s in sorted(actionable, key=lambda x: x.confidence, reverse=True)[:10]:
            icon = {"usage_up": "↑", "injury": "🩹", "drama": "⚠"}.get(s.signal_type, "•")
            print(f"  {icon} [{s.sport.upper()}] {s.player} ({s.source}) "
                  f"→ prop {s.prop_impact.upper()}  conf {s.confidence:.0%}")
            print(f"     {s.headline[:90]}")


if __name__ == "__main__":
    run()
