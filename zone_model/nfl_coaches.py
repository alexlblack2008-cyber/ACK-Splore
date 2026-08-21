"""
NFL Head Coach + Offensive Coordinator Profiles
================================================
Captures coaching tendencies that directly affect scoring totals and game pace.

Key factors modeled:
  - pass_rate_tendency: how aggressively they pass vs league avg (0.575)
  - fourth_down_aggression: 0=conservative, 1=very aggressive (league avg ~0.55)
  - hurry_up_freq: how often they use no-huddle / uptempo (affects pace)
  - red_zone_aggression: 0=kick FGs, 1=always go for TD
  - two_minute_efficiency: how well they manage end-of-half drives
  - pts_per_drive_adj: adjustment vs league avg pts per drive (~2.1)
  - defensive_style: "zone" | "man" | "hybrid"
  - blitz_rate: how often they bring extra rushers (league avg ~0.22)
  - cover_2_rate: classic tampa-2 bend-don't-break
  - aggressive_defense: forces more turnovers but gives up big plays

These are applied as modifiers on top of ESPN team stats when scoring games.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class NFLCoachProfile:
    name:                   str
    team:                   str
    role:                   str            # "HC" | "OC" | "DC"
    # Offense tendencies
    pass_rate_tendency:     float = 0.575  # league avg
    fourth_down_aggression: float = 0.55   # 0–1 scale
    hurry_up_freq:          float = 0.10   # fraction of plays no-huddle
    red_zone_aggression:    float = 0.575  # TD% in red zone tendency
    two_minute_efficiency:  float = 1.00   # multiplier on end-of-half drives
    pts_per_drive_adj:      float = 0.0    # vs league avg 2.1 pts/drive
    # Defense tendencies
    defensive_style:        str   = "hybrid"
    blitz_rate:             float = 0.22   # league avg
    cover_2_rate:           float = 0.20
    aggressive_defense:     bool  = False  # forces TOs but allows big plays
    # Total scoring impact
    total_pts_adj:          float = 0.0    # net pts above/below avg for this coaching staff
    notes:                  str   = ""


# ── NFL Head Coach Profiles (2026 season) ─────────────────────────────────────
# Total pts adj = net expected points above league avg per game for this HC's offense + defense combo

NFL_COACH_PROFILES: dict[str, NFLCoachProfile] = {

    # ── NFC East ──────────────────────────────────────────────────────────────
    "Philadelphia Eagles": NFLCoachProfile(
        name="Nick Sirianni", team="Philadelphia Eagles", role="HC",
        pass_rate_tendency=0.58,
        fourth_down_aggression=0.70,
        hurry_up_freq=0.14,
        red_zone_aggression=0.63,
        pts_per_drive_adj=0.25,
        defensive_style="man",
        blitz_rate=0.25,
        aggressive_defense=True,
        total_pts_adj=2.5,
        notes="Aggressive 4th down philosophy; Hurts extends plays; elite D forces TOs",
    ),
    "Dallas Cowboys": NFLCoachProfile(
        name="Mike McCarthy", team="Dallas Cowboys", role="HC",
        pass_rate_tendency=0.60,
        fourth_down_aggression=0.50,
        hurry_up_freq=0.12,
        red_zone_aggression=0.58,
        pts_per_drive_adj=0.10,
        defensive_style="hybrid",
        blitz_rate=0.28,
        aggressive_defense=False,
        total_pts_adj=1.5,
        notes="Pass-heavy with Dak; blitz-heavy D; can be conservative late",
    ),
    "New York Giants": NFLCoachProfile(
        name="Brian Daboll", team="New York Giants", role="HC",
        pass_rate_tendency=0.54,
        fourth_down_aggression=0.60,
        hurry_up_freq=0.10,
        red_zone_aggression=0.55,
        pts_per_drive_adj=-0.15,
        defensive_style="zone",
        blitz_rate=0.20,
        aggressive_defense=False,
        total_pts_adj=-1.0,
        notes="Balanced but limited by roster; defense bends often",
    ),
    "Washington Commanders": NFLCoachProfile(
        name="Dan Quinn", team="Washington Commanders", role="HC",
        pass_rate_tendency=0.57,
        fourth_down_aggression=0.58,
        hurry_up_freq=0.11,
        red_zone_aggression=0.58,
        pts_per_drive_adj=0.05,
        defensive_style="man",
        blitz_rate=0.30,
        aggressive_defense=True,
        total_pts_adj=0.5,
        notes="Quinn runs Seattle-style Cover-3 with heavy man; Daniels on the rise",
    ),

    # ── NFC North ─────────────────────────────────────────────────────────────
    "Green Bay Packers": NFLCoachProfile(
        name="Matt LaFleur", team="Green Bay Packers", role="HC",
        pass_rate_tendency=0.59,
        fourth_down_aggression=0.62,
        hurry_up_freq=0.13,
        red_zone_aggression=0.60,
        pts_per_drive_adj=0.20,
        defensive_style="zone",
        blitz_rate=0.19,
        aggressive_defense=False,
        total_pts_adj=2.0,
        notes="McVay disciple; motion-heavy offense; Love ascending; low-blitz D",
    ),
    "Minnesota Vikings": NFLCoachProfile(
        name="Kevin O'Connell", team="Minnesota Vikings", role="HC",
        pass_rate_tendency=0.61,
        fourth_down_aggression=0.65,
        hurry_up_freq=0.15,
        red_zone_aggression=0.62,
        pts_per_drive_adj=0.30,
        defensive_style="hybrid",
        blitz_rate=0.26,
        aggressive_defense=False,
        total_pts_adj=3.0,
        notes="Pass-first spread offense; JJ McCarthy; strong YAC scheme; high-scoring tendency",
    ),
    "Chicago Bears": NFLCoachProfile(
        name="Ben Johnson", team="Chicago Bears", role="HC",
        pass_rate_tendency=0.62,
        fourth_down_aggression=0.68,
        hurry_up_freq=0.18,
        red_zone_aggression=0.64,
        pts_per_drive_adj=0.40,
        defensive_style="hybrid",
        blitz_rate=0.23,
        aggressive_defense=False,
        total_pts_adj=3.5,
        notes="Elite OC turned HC; Caleb Williams + uptempo scheme = high-scoring ceiling",
    ),
    "Detroit Lions": NFLCoachProfile(
        name="Dan Campbell", team="Detroit Lions", role="HC",
        pass_rate_tendency=0.55,
        fourth_down_aggression=0.90,
        hurry_up_freq=0.12,
        red_zone_aggression=0.70,
        pts_per_drive_adj=0.35,
        defensive_style="man",
        blitz_rate=0.30,
        aggressive_defense=True,
        total_pts_adj=4.0,
        notes="Most aggressive 4th-down team in NFL; physical run game sets up PA; D forces TOs",
    ),

    # ── NFC South ─────────────────────────────────────────────────────────────
    "Atlanta Falcons": NFLCoachProfile(
        name="Raheem Morris", team="Atlanta Falcons", role="HC",
        pass_rate_tendency=0.55,
        fourth_down_aggression=0.55,
        hurry_up_freq=0.09,
        red_zone_aggression=0.57,
        pts_per_drive_adj=0.05,
        defensive_style="man",
        blitz_rate=0.24,
        aggressive_defense=False,
        total_pts_adj=0.5,
        notes="Balanced scheme; Penix era beginning; D improving",
    ),
    "New Orleans Saints": NFLCoachProfile(
        name="Kellen Moore", team="New Orleans Saints", role="HC",
        pass_rate_tendency=0.59,
        fourth_down_aggression=0.60,
        hurry_up_freq=0.12,
        red_zone_aggression=0.59,
        pts_per_drive_adj=0.15,
        defensive_style="hybrid",
        blitz_rate=0.22,
        aggressive_defense=False,
        total_pts_adj=1.0,
        notes="Pass-first OC background; Derek Carr health-dependent",
    ),
    "Tampa Bay Buccaneers": NFLCoachProfile(
        name="Todd Bowles", team="Tampa Bay Buccaneers", role="HC",
        pass_rate_tendency=0.58,
        fourth_down_aggression=0.52,
        hurry_up_freq=0.10,
        red_zone_aggression=0.57,
        pts_per_drive_adj=0.10,
        defensive_style="zone",
        blitz_rate=0.28,
        aggressive_defense=True,
        total_pts_adj=1.0,
        notes="Bowles is a defensive HC; Tampa-2 roots; Baker steady with Licht's WR depth",
    ),
    "Carolina Panthers": NFLCoachProfile(
        name="Dave Canales", team="Carolina Panthers", role="HC",
        pass_rate_tendency=0.57,
        fourth_down_aggression=0.55,
        hurry_up_freq=0.11,
        red_zone_aggression=0.54,
        pts_per_drive_adj=-0.25,
        defensive_style="zone",
        blitz_rate=0.20,
        aggressive_defense=False,
        total_pts_adj=-2.0,
        notes="Rebuilding; roster limitations cap ceiling; Bryce Young proving himself",
    ),

    # ── NFC West ──────────────────────────────────────────────────────────────
    "Los Angeles Rams": NFLCoachProfile(
        name="Sean McVay", team="Los Angeles Rams", role="HC",
        pass_rate_tendency=0.60,
        fourth_down_aggression=0.72,
        hurry_up_freq=0.16,
        red_zone_aggression=0.65,
        pts_per_drive_adj=0.35,
        defensive_style="hybrid",
        blitz_rate=0.25,
        aggressive_defense=False,
        total_pts_adj=3.5,
        notes="Best OC mind in NFL; motion pre-snap; Stafford IQ exploits every D",
    ),
    "San Francisco 49ers": NFLCoachProfile(
        name="Kyle Shanahan", team="San Francisco 49ers", role="HC",
        pass_rate_tendency=0.54,
        fourth_down_aggression=0.65,
        hurry_up_freq=0.11,
        red_zone_aggression=0.65,
        pts_per_drive_adj=0.30,
        defensive_style="man",
        blitz_rate=0.22,
        aggressive_defense=True,
        total_pts_adj=3.0,
        notes="Run-first scheme opens everything; Brock Purdy smart; elite D unit",
    ),
    "Seattle Seahawks": NFLCoachProfile(
        name="Mike Macdonald", team="Seattle Seahawks", role="HC",
        pass_rate_tendency=0.56,
        fourth_down_aggression=0.58,
        hurry_up_freq=0.10,
        red_zone_aggression=0.58,
        pts_per_drive_adj=0.10,
        defensive_style="man",
        blitz_rate=0.32,
        aggressive_defense=True,
        total_pts_adj=1.0,
        notes="Ravens D coordinator background; heavy man-press; Geno steady",
    ),
    "Arizona Cardinals": NFLCoachProfile(
        name="Jonathan Gannon", team="Arizona Cardinals", role="HC",
        pass_rate_tendency=0.57,
        fourth_down_aggression=0.55,
        hurry_up_freq=0.10,
        red_zone_aggression=0.55,
        pts_per_drive_adj=-0.10,
        defensive_style="zone",
        blitz_rate=0.20,
        aggressive_defense=False,
        total_pts_adj=-0.5,
        notes="Defensive HC; Kyler Murray health key; young team trending up",
    ),

    # ── AFC East ──────────────────────────────────────────────────────────────
    "Buffalo Bills": NFLCoachProfile(
        name="Sean McDermott", team="Buffalo Bills", role="HC",
        pass_rate_tendency=0.62,
        fourth_down_aggression=0.60,
        hurry_up_freq=0.15,
        red_zone_aggression=0.60,
        pts_per_drive_adj=0.25,
        defensive_style="man",
        blitz_rate=0.26,
        aggressive_defense=False,
        total_pts_adj=3.0,
        notes="Josh Allen carries offense; spread-and-run; defensive intelligence",
    ),
    "Miami Dolphins": NFLCoachProfile(
        name="Mike McDaniel", team="Miami Dolphins", role="HC",
        pass_rate_tendency=0.62,
        fourth_down_aggression=0.60,
        hurry_up_freq=0.18,
        red_zone_aggression=0.60,
        pts_per_drive_adj=0.30,
        defensive_style="hybrid",
        blitz_rate=0.22,
        aggressive_defense=False,
        total_pts_adj=3.0,
        notes="Speed-in-space offense; Tua + Tyreek; fastest tempo in NFL",
    ),
    "New England Patriots": NFLCoachProfile(
        name="Jerod Mayo", team="New England Patriots", role="HC",
        pass_rate_tendency=0.55,
        fourth_down_aggression=0.50,
        hurry_up_freq=0.09,
        red_zone_aggression=0.54,
        pts_per_drive_adj=-0.20,
        defensive_style="zone",
        blitz_rate=0.18,
        aggressive_defense=False,
        total_pts_adj=-1.5,
        notes="Post-Belichick rebuild; conservative game management; Maye developing",
    ),
    "New York Jets": NFLCoachProfile(
        name="Jeff Ulbrich", team="New York Jets", role="HC",
        pass_rate_tendency=0.57,
        fourth_down_aggression=0.55,
        hurry_up_freq=0.10,
        red_zone_aggression=0.56,
        pts_per_drive_adj=0.05,
        defensive_style="man",
        blitz_rate=0.28,
        aggressive_defense=True,
        total_pts_adj=0.0,
        notes="Rodgers health = everything; elite D limits opponent scoring",
    ),

    # ── AFC North ─────────────────────────────────────────────────────────────
    "Baltimore Ravens": NFLCoachProfile(
        name="John Harbaugh", team="Baltimore Ravens", role="HC",
        pass_rate_tendency=0.54,
        fourth_down_aggression=0.75,
        hurry_up_freq=0.12,
        red_zone_aggression=0.68,
        pts_per_drive_adj=0.40,
        defensive_style="hybrid",
        blitz_rate=0.30,
        aggressive_defense=True,
        total_pts_adj=4.5,
        notes="Lamar Jackson MVP-level; one of most aggressive 4th-down coaches; elite overall",
    ),
    "Cincinnati Bengals": NFLCoachProfile(
        name="Zac Taylor", team="Cincinnati Bengals", role="HC",
        pass_rate_tendency=0.63,
        fourth_down_aggression=0.58,
        hurry_up_freq=0.14,
        red_zone_aggression=0.61,
        pts_per_drive_adj=0.25,
        defensive_style="zone",
        blitz_rate=0.22,
        aggressive_defense=False,
        total_pts_adj=2.5,
        notes="Burrow + Chase = elite passing game; McPherson FG reliability caps some drives",
    ),
    "Cleveland Browns": NFLCoachProfile(
        name="Kevin Stefanski", team="Cleveland Browns", role="HC",
        pass_rate_tendency=0.52,
        fourth_down_aggression=0.55,
        hurry_up_freq=0.09,
        red_zone_aggression=0.56,
        pts_per_drive_adj=-0.05,
        defensive_style="hybrid",
        blitz_rate=0.24,
        aggressive_defense=False,
        total_pts_adj=0.0,
        notes="Run-heavy; QB health determines ceiling; solid mid-range coaching",
    ),
    "Pittsburgh Steelers": NFLCoachProfile(
        name="Mike Tomlin", team="Pittsburgh Steelers", role="HC",
        pass_rate_tendency=0.55,
        fourth_down_aggression=0.58,
        hurry_up_freq=0.10,
        red_zone_aggression=0.58,
        pts_per_drive_adj=0.10,
        defensive_style="man",
        blitz_rate=0.32,
        aggressive_defense=True,
        total_pts_adj=1.5,
        notes="Never had a losing season; run-first; Watt-less D still above avg",
    ),

    # ── AFC South ─────────────────────────────────────────────────────────────
    "Houston Texans": NFLCoachProfile(
        name="DeMeco Ryans", team="Houston Texans", role="HC",
        pass_rate_tendency=0.58,
        fourth_down_aggression=0.60,
        hurry_up_freq=0.12,
        red_zone_aggression=0.60,
        pts_per_drive_adj=0.20,
        defensive_style="man",
        blitz_rate=0.28,
        aggressive_defense=True,
        total_pts_adj=2.0,
        notes="49ers D pedigree; CJ Stroud efficient; offense and D both ascending",
    ),
    "Indianapolis Colts": NFLCoachProfile(
        name="Shane Steichen", team="Indianapolis Colts", role="HC",
        pass_rate_tendency=0.57,
        fourth_down_aggression=0.60,
        hurry_up_freq=0.12,
        red_zone_aggression=0.58,
        pts_per_drive_adj=0.10,
        defensive_style="hybrid",
        blitz_rate=0.22,
        aggressive_defense=False,
        total_pts_adj=1.0,
        notes="Helped Hurts develop; Anthony Richardson upside; balanced scheme",
    ),
    "Jacksonville Jaguars": NFLCoachProfile(
        name="Liam Coen", team="Jacksonville Jaguars", role="HC",
        pass_rate_tendency=0.59,
        fourth_down_aggression=0.58,
        hurry_up_freq=0.12,
        red_zone_aggression=0.57,
        pts_per_drive_adj=0.05,
        defensive_style="zone",
        blitz_rate=0.20,
        aggressive_defense=False,
        total_pts_adj=0.5,
        notes="New HC; Trevor Lawrence bounce-back candidate; uncertain D",
    ),
    "Tennessee Titans": NFLCoachProfile(
        name="Brian Callahan", team="Tennessee Titans", role="HC",
        pass_rate_tendency=0.54,
        fourth_down_aggression=0.52,
        hurry_up_freq=0.09,
        red_zone_aggression=0.54,
        pts_per_drive_adj=-0.20,
        defensive_style="zone",
        blitz_rate=0.19,
        aggressive_defense=False,
        total_pts_adj=-1.5,
        notes="Rebuilding year; conservative scheme; low expected scoring",
    ),

    # ── AFC West ──────────────────────────────────────────────────────────────
    "Kansas City Chiefs": NFLCoachProfile(
        name="Andy Reid", team="Kansas City Chiefs", role="HC",
        pass_rate_tendency=0.61,
        fourth_down_aggression=0.65,
        hurry_up_freq=0.15,
        red_zone_aggression=0.65,
        pts_per_drive_adj=0.45,
        defensive_style="hybrid",
        blitz_rate=0.22,
        aggressive_defense=False,
        total_pts_adj=5.0,
        notes="Greatest OC mind in NFL history; Mahomes; D scheme by Spagnuolo; 3-peat window",
    ),
    "Denver Broncos": NFLCoachProfile(
        name="Sean Payton", team="Denver Broncos", role="HC",
        pass_rate_tendency=0.60,
        fourth_down_aggression=0.60,
        hurry_up_freq=0.13,
        red_zone_aggression=0.60,
        pts_per_drive_adj=0.20,
        defensive_style="hybrid",
        blitz_rate=0.24,
        aggressive_defense=False,
        total_pts_adj=2.0,
        notes="Payton offense with Bo Nix maturing; D improved dramatically in year 2",
    ),
    "Las Vegas Raiders": NFLCoachProfile(
        name="Pete Carroll", team="Las Vegas Raiders", role="HC",
        pass_rate_tendency=0.52,
        fourth_down_aggression=0.50,
        hurry_up_freq=0.09,
        red_zone_aggression=0.55,
        pts_per_drive_adj=-0.10,
        defensive_style="man",
        blitz_rate=0.20,
        aggressive_defense=False,
        total_pts_adj=-0.5,
        notes="Run-heavy Carroll ball; Cover-3 D; conservative game management",
    ),
    "Los Angeles Chargers": NFLCoachProfile(
        name="Jim Harbaugh", team="Los Angeles Chargers", role="HC",
        pass_rate_tendency=0.56,
        fourth_down_aggression=0.65,
        hurry_up_freq=0.11,
        red_zone_aggression=0.63,
        pts_per_drive_adj=0.25,
        defensive_style="hybrid",
        blitz_rate=0.26,
        aggressive_defense=True,
        total_pts_adj=2.5,
        notes="Michigan-style physicality; Herbert elite; Harbaugh wins culture immediately",
    ),
}


def get_coach(team_name: str) -> NFLCoachProfile:
    """Return coach profile for a team, or default league-avg profile."""
    profile = NFL_COACH_PROFILES.get(team_name)
    if profile:
        return profile
    # Try partial match
    for key, prof in NFL_COACH_PROFILES.items():
        if team_name.lower() in key.lower() or key.lower() in team_name.lower():
            return prof
    return NFLCoachProfile(name="Unknown", team=team_name, role="HC")
