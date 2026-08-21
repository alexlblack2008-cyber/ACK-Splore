"""
NBA Head Coach Profiles
=======================
Captures coaching tendencies that affect pace, total points, and defensive style.

Key factors modeled:
  - pace_tendency: possessions per 48 min vs league avg (~99.5)
  - three_point_emphasis: how heavily they build around 3-pointers (affects variance)
  - defensive_intensity: 0=soft, 1=elite lockdown
  - bench_rotation_depth: how much bench minutes affect starters' efficiency
  - clutch_management: how well they manage late-game scoring situations
  - pts_per_game_adj: net points above/below league avg (115 ppg) from scheme alone
  - pace_adj: possessions above/below league avg (positive = faster)
  - total_pts_adj: net impact on game total vs league average
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class NBACoachProfile:
    name:                   str
    team:                   str
    # Offense
    pace_tendency:          float = 99.5   # possessions per 48 min; league avg
    three_point_emphasis:   float = 0.38   # 3PA rate; league avg
    motion_offense:         bool  = False  # ball-movement heavy = more open looks
    iso_heavy:              bool  = False  # isolation = lower scoring efficiency
    pts_per_game_adj:       float = 0.0    # offensive pts above league avg from scheme
    # Defense
    defensive_intensity:    float = 0.50   # 0=soft, 1=elite
    defensive_style:        str   = "hybrid"  # "zone" | "man" | "switch" | "hybrid"
    blitz_pick_roll:        bool  = False  # trapping PnR slows elite guards
    # Game management
    bench_rotation_depth:   float = 0.50   # 0=ride starters, 1=deep rotation
    clutch_management:      float = 0.50   # ability to score in final 5 min
    # Net total impact
    pace_adj:               float = 0.0    # possessions above/below avg
    total_pts_adj:          float = 0.0    # net pts on game total vs league avg
    notes:                  str   = ""


# ── NBA Head Coach Profiles (2024-25 season) ──────────────────────────────────

NBA_COACH_PROFILES: dict[str, NBACoachProfile] = {

    # ── Atlantic Division ─────────────────────────────────────────────────────
    "Boston Celtics": NBACoachProfile(
        name="Joe Mazzulla", team="Boston Celtics",
        pace_tendency=100.2,
        three_point_emphasis=0.46,
        motion_offense=True,
        pts_per_game_adj=3.5,
        defensive_intensity=0.90,
        defensive_style="switch",
        bench_rotation_depth=0.55,
        clutch_management=0.85,
        pace_adj=0.7,
        total_pts_adj=3.0,
        notes="NBA champion scheme; Tatum/Brown/White 3-pt barrage; elite switch defense",
    ),
    "Philadelphia 76ers": NBACoachProfile(
        name="Nick Nurse", team="Philadelphia 76ers",
        pace_tendency=98.5,
        three_point_emphasis=0.38,
        motion_offense=False,
        iso_heavy=True,
        pts_per_game_adj=1.0,
        defensive_intensity=0.60,
        defensive_style="hybrid",
        blitz_pick_roll=True,
        bench_rotation_depth=0.40,
        clutch_management=0.70,
        pace_adj=-1.0,
        total_pts_adj=0.5,
        notes="Embiid-dependent; Nurse's varied D schemes; pace slows around big man",
    ),
    "New York Knicks": NBACoachProfile(
        name="Tom Thibodeau", team="New York Knicks",
        pace_tendency=97.5,
        three_point_emphasis=0.36,
        motion_offense=False,
        pts_per_game_adj=0.5,
        defensive_intensity=0.82,
        defensive_style="man",
        bench_rotation_depth=0.25,
        clutch_management=0.72,
        pace_adj=-2.0,
        total_pts_adj=-2.5,
        notes="Slowest pace in NBA; grind-it-out D; rides starters 40+ min; unders lean",
    ),
    "Brooklyn Nets": NBACoachProfile(
        name="Jordi Fernandez", team="Brooklyn Nets",
        pace_tendency=100.5,
        three_point_emphasis=0.40,
        motion_offense=True,
        pts_per_game_adj=-2.0,
        defensive_intensity=0.30,
        defensive_style="zone",
        bench_rotation_depth=0.70,
        clutch_management=0.35,
        pace_adj=1.0,
        total_pts_adj=-3.0,
        notes="Rebuilding; plays fast but allows a ton; young roster = high variance",
    ),
    "Toronto Raptors": NBACoachProfile(
        name="Darko Rajakovic", team="Toronto Raptors",
        pace_tendency=101.0,
        three_point_emphasis=0.41,
        motion_offense=True,
        pts_per_game_adj=-1.5,
        defensive_intensity=0.50,
        defensive_style="hybrid",
        bench_rotation_depth=0.65,
        clutch_management=0.45,
        pace_adj=1.5,
        total_pts_adj=-1.5,
        notes="Fast pace, but lacks top scoring talent; defensive identity still developing",
    ),

    # ── Central Division ──────────────────────────────────────────────────────
    "Milwaukee Bucks": NBACoachProfile(
        name="Doc Rivers", team="Milwaukee Bucks",
        pace_tendency=99.0,
        three_point_emphasis=0.37,
        motion_offense=False,
        iso_heavy=True,
        pts_per_game_adj=1.5,
        defensive_intensity=0.58,
        defensive_style="switch",
        bench_rotation_depth=0.45,
        clutch_management=0.65,
        pace_adj=-0.5,
        total_pts_adj=1.0,
        notes="Giannis iso-heavy; Doc has elite offensive history but inconsistent D",
    ),
    "Indiana Pacers": NBACoachProfile(
        name="Rick Carlisle", team="Indiana Pacers",
        pace_tendency=103.5,
        three_point_emphasis=0.43,
        motion_offense=True,
        pts_per_game_adj=2.5,
        defensive_intensity=0.42,
        defensive_style="hybrid",
        bench_rotation_depth=0.60,
        clutch_management=0.60,
        pace_adj=4.0,
        total_pts_adj=5.0,
        notes="Fastest pace in NBA; Carlisle's motion system; overs hit at enormous rate",
    ),
    "Chicago Bulls": NBACoachProfile(
        name="Billy Donovan", team="Chicago Bulls",
        pace_tendency=99.0,
        three_point_emphasis=0.37,
        motion_offense=False,
        pts_per_game_adj=0.0,
        defensive_intensity=0.55,
        defensive_style="hybrid",
        bench_rotation_depth=0.55,
        clutch_management=0.55,
        pace_adj=-0.5,
        total_pts_adj=-1.0,
        notes="Average-everything team; DeRozan-era offense winds down; transitional",
    ),
    "Cleveland Cavaliers": NBACoachProfile(
        name="Kenny Atkinson", team="Cleveland Cavaliers",
        pace_tendency=99.5,
        three_point_emphasis=0.39,
        motion_offense=True,
        pts_per_game_adj=1.5,
        defensive_intensity=0.78,
        defensive_style="switch",
        bench_rotation_depth=0.55,
        clutch_management=0.70,
        pace_adj=0.0,
        total_pts_adj=1.5,
        notes="Mitchell + Mobley elite duo; strong D; balanced scoring tendency",
    ),
    "Detroit Pistons": NBACoachProfile(
        name="JB Bickerstaff", team="Detroit Pistons",
        pace_tendency=100.5,
        three_point_emphasis=0.38,
        motion_offense=False,
        pts_per_game_adj=-2.0,
        defensive_intensity=0.38,
        defensive_style="zone",
        bench_rotation_depth=0.65,
        clutch_management=0.40,
        pace_adj=1.0,
        total_pts_adj=-2.5,
        notes="Young rebuilding team; Cade developing; allows too many points defensively",
    ),

    # ── Southeast Division ─────────────────────────────────────────────────────
    "Miami Heat": NBACoachProfile(
        name="Erik Spoelstra", team="Miami Heat",
        pace_tendency=97.8,
        three_point_emphasis=0.38,
        motion_offense=True,
        pts_per_game_adj=1.0,
        defensive_intensity=0.85,
        defensive_style="man",
        blitz_pick_roll=True,
        bench_rotation_depth=0.70,
        clutch_management=0.88,
        pace_adj=-1.7,
        total_pts_adj=-2.0,
        notes="Spo's culture = elite D; slow pace; unders lean; best coach in NBA",
    ),
    "Atlanta Hawks": NBACoachProfile(
        name="Quin Snyder", team="Atlanta Hawks",
        pace_tendency=101.0,
        three_point_emphasis=0.42,
        motion_offense=True,
        pts_per_game_adj=1.5,
        defensive_intensity=0.40,
        defensive_style="hybrid",
        bench_rotation_depth=0.55,
        clutch_management=0.55,
        pace_adj=1.5,
        total_pts_adj=2.0,
        notes="Fast pace; Trae Young live-or-die offense; poor D = high totals",
    ),
    "Charlotte Hornets": NBACoachProfile(
        name="Charles Lee", team="Charlotte Hornets",
        pace_tendency=101.5,
        three_point_emphasis=0.41,
        motion_offense=True,
        pts_per_game_adj=-2.5,
        defensive_intensity=0.32,
        defensive_style="zone",
        bench_rotation_depth=0.65,
        clutch_management=0.38,
        pace_adj=2.0,
        total_pts_adj=-2.0,
        notes="Rebuilding; LaMelo live-or-die; allows tons; fast but not efficient",
    ),
    "Orlando Magic": NBACoachProfile(
        name="Jamahl Mosley", team="Orlando Magic",
        pace_tendency=98.5,
        three_point_emphasis=0.36,
        motion_offense=True,
        pts_per_game_adj=0.5,
        defensive_intensity=0.75,
        defensive_style="man",
        bench_rotation_depth=0.60,
        clutch_management=0.60,
        pace_adj=-1.0,
        total_pts_adj=-1.5,
        notes="Strong young D with Paolo/Suggs/Wagner; half-court offense; unders lean",
    ),
    "Washington Wizards": NBACoachProfile(
        name="Brian Keefe", team="Washington Wizards",
        pace_tendency=101.5,
        three_point_emphasis=0.39,
        motion_offense=False,
        pts_per_game_adj=-3.5,
        defensive_intensity=0.25,
        defensive_style="zone",
        bench_rotation_depth=0.70,
        clutch_management=0.30,
        pace_adj=2.0,
        total_pts_adj=-2.5,
        notes="Full rebuild; worst D in NBA; fast pace but no offensive identity",
    ),

    # ── Northwest Division ─────────────────────────────────────────────────────
    "Denver Nuggets": NBACoachProfile(
        name="Michael Malone", team="Denver Nuggets",
        pace_tendency=98.0,
        three_point_emphasis=0.35,
        motion_offense=True,
        pts_per_game_adj=2.0,
        defensive_intensity=0.72,
        defensive_style="hybrid",
        bench_rotation_depth=0.40,
        clutch_management=0.90,
        pace_adj=-1.5,
        total_pts_adj=1.0,
        notes="Jokic makes everything work; elite half-court; deliberate pace; championship IQ",
    ),
    "Minnesota Timberwolves": NBACoachProfile(
        name="Chris Finch", team="Minnesota Timberwolves",
        pace_tendency=98.5,
        three_point_emphasis=0.38,
        motion_offense=False,
        pts_per_game_adj=0.5,
        defensive_intensity=0.85,
        defensive_style="switch",
        bench_rotation_depth=0.50,
        clutch_management=0.68,
        pace_adj=-1.0,
        total_pts_adj=-1.5,
        notes="Gobert/KAT/Edwards; elite D when locked in; half-court offense = unders",
    ),
    "Oklahoma City Thunder": NBACoachProfile(
        name="Mark Daigneault", team="Oklahoma City Thunder",
        pace_tendency=101.5,
        three_point_emphasis=0.43,
        motion_offense=True,
        pts_per_game_adj=2.0,
        defensive_intensity=0.80,
        defensive_style="switch",
        bench_rotation_depth=0.70,
        clutch_management=0.72,
        pace_adj=2.0,
        total_pts_adj=3.5,
        notes="SGA + deep young roster; fast 3-pt motion offense; excellent D; overs lean",
    ),
    "Utah Jazz": NBACoachProfile(
        name="Will Hardy", team="Utah Jazz",
        pace_tendency=100.5,
        three_point_emphasis=0.40,
        motion_offense=True,
        pts_per_game_adj=-2.5,
        defensive_intensity=0.35,
        defensive_style="zone",
        bench_rotation_depth=0.75,
        clutch_management=0.40,
        pace_adj=1.0,
        total_pts_adj=-3.0,
        notes="Full rebuild; Lauri top piece; D is a work in progress; low totals",
    ),
    "Portland Trail Blazers": NBACoachProfile(
        name="Chauncey Billups", team="Portland Trail Blazers",
        pace_tendency=100.0,
        three_point_emphasis=0.38,
        motion_offense=False,
        pts_per_game_adj=-1.5,
        defensive_intensity=0.42,
        defensive_style="hybrid",
        bench_rotation_depth=0.60,
        clutch_management=0.45,
        pace_adj=0.5,
        total_pts_adj=-2.0,
        notes="Scoot Henderson developing; rebuilding; below avg on both ends",
    ),

    # ── Pacific Division ───────────────────────────────────────────────────────
    "Golden State Warriors": NBACoachProfile(
        name="Steve Kerr", team="Golden State Warriors",
        pace_tendency=100.5,
        three_point_emphasis=0.48,
        motion_offense=True,
        pts_per_game_adj=2.5,
        defensive_intensity=0.68,
        defensive_style="switch",
        bench_rotation_depth=0.60,
        clutch_management=0.82,
        pace_adj=1.0,
        total_pts_adj=3.0,
        notes="Curry 3-pt system is a franchise; ball movement best in NBA; overs lean",
    ),
    "Los Angeles Lakers": NBACoachProfile(
        name="JJ Redick", team="Los Angeles Lakers",
        pace_tendency=100.0,
        three_point_emphasis=0.38,
        motion_offense=False,
        iso_heavy=True,
        pts_per_game_adj=1.5,
        defensive_intensity=0.60,
        defensive_style="hybrid",
        bench_rotation_depth=0.40,
        clutch_management=0.78,
        pace_adj=0.5,
        total_pts_adj=1.0,
        notes="LeBron/AD carry; new HC adapting; iso-heavy offense; AD anchors D",
    ),
    "Los Angeles Clippers": NBACoachProfile(
        name="Tyronn Lue", team="Los Angeles Clippers",
        pace_tendency=99.5,
        three_point_emphasis=0.40,
        motion_offense=False,
        pts_per_game_adj=1.0,
        defensive_intensity=0.68,
        defensive_style="switch",
        bench_rotation_depth=0.60,
        clutch_management=0.75,
        pace_adj=0.0,
        total_pts_adj=0.5,
        notes="Lue gets most from roster; Kawhi/PG health-dependent; solid scheme",
    ),
    "Phoenix Suns": NBACoachProfile(
        name="Mike Budenholzer", team="Phoenix Suns",
        pace_tendency=100.0,
        three_point_emphasis=0.42,
        motion_offense=True,
        pts_per_game_adj=1.5,
        defensive_intensity=0.65,
        defensive_style="switch",
        bench_rotation_depth=0.50,
        clutch_management=0.68,
        pace_adj=0.5,
        total_pts_adj=1.5,
        notes="Bud's motion offense fits Durant/Booker perfectly; switch D credentialed",
    ),
    "Sacramento Kings": NBACoachProfile(
        name="Doug Christie", team="Sacramento Kings",
        pace_tendency=101.5,
        three_point_emphasis=0.41,
        motion_offense=False,
        pts_per_game_adj=0.5,
        defensive_intensity=0.48,
        defensive_style="hybrid",
        bench_rotation_depth=0.55,
        clutch_management=0.52,
        pace_adj=2.0,
        total_pts_adj=1.0,
        notes="Fast pace; Sabonis passing hub; Fox speed; D below avg",
    ),

    # ── Southwest Division ─────────────────────────────────────────────────────
    "San Antonio Spurs": NBACoachProfile(
        name="Gregg Popovich", team="San Antonio Spurs",
        pace_tendency=99.5,
        three_point_emphasis=0.38,
        motion_offense=True,
        pts_per_game_adj=-1.5,
        defensive_intensity=0.55,
        defensive_style="hybrid",
        bench_rotation_depth=0.75,
        clutch_management=0.65,
        pace_adj=0.0,
        total_pts_adj=-2.0,
        notes="Pop developing Wembanyama; patient system; D teaching phase",
    ),
    "Dallas Mavericks": NBACoachProfile(
        name="Jason Kidd", team="Dallas Mavericks",
        pace_tendency=100.0,
        three_point_emphasis=0.43,
        motion_offense=False,
        iso_heavy=True,
        pts_per_game_adj=2.5,
        defensive_intensity=0.62,
        defensive_style="switch",
        bench_rotation_depth=0.40,
        clutch_management=0.80,
        pace_adj=0.5,
        total_pts_adj=2.5,
        notes="Doncic iso-heaven; Kyrie off-ball; elite clutch performances; overs lean",
    ),
    "Houston Rockets": NBACoachProfile(
        name="Ime Udoka", team="Houston Rockets",
        pace_tendency=100.5,
        three_point_emphasis=0.41,
        motion_offense=True,
        pts_per_game_adj=0.5,
        defensive_intensity=0.75,
        defensive_style="man",
        bench_rotation_depth=0.65,
        clutch_management=0.60,
        pace_adj=1.0,
        total_pts_adj=0.5,
        notes="Strong young D culture; Alperen/Jalen Green ascending; competitive",
    ),
    "Memphis Grizzlies": NBACoachProfile(
        name="Taylor Jenkins", team="Memphis Grizzlies",
        pace_tendency=101.0,
        three_point_emphasis=0.38,
        motion_offense=True,
        pts_per_game_adj=0.5,
        defensive_intensity=0.65,
        defensive_style="man",
        bench_rotation_depth=0.65,
        clutch_management=0.58,
        pace_adj=1.5,
        total_pts_adj=0.5,
        notes="Morant-led pace; gritty D; physical style; health is always the variable",
    ),
    "New Orleans Pelicans": NBACoachProfile(
        name="Willie Green", team="New Orleans Pelicans",
        pace_tendency=99.0,
        three_point_emphasis=0.37,
        motion_offense=True,
        pts_per_game_adj=0.5,
        defensive_intensity=0.68,
        defensive_style="man",
        bench_rotation_depth=0.55,
        clutch_management=0.60,
        pace_adj=-0.5,
        total_pts_adj=0.0,
        notes="Zion health defines ceiling; solid team D when healthy; mid-range identity",
    ),
}


def get_coach(team_name: str) -> NBACoachProfile:
    """Return coach profile for a team, or default league-avg profile."""
    profile = NBA_COACH_PROFILES.get(team_name)
    if profile:
        return profile
    for key, prof in NBA_COACH_PROFILES.items():
        if team_name.lower() in key.lower() or key.lower() in team_name.lower():
            return prof
    return NBACoachProfile(name="Unknown", team=team_name)
