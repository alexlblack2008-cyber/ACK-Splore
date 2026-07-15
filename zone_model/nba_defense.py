"""
NBA Defensive Scheme & Superstar Adjustment Layer
==================================================
Models how each NBA team's defensive scheme affects player prop lines.

Key dimensions:
  1. Primary coverage type (man, zone, switch-everything, match-up zone)
  2. Pick-and-roll coverage (drop, hedge, switch, ice)
  3. How teams guard elite players (double, chase, ice, switch)
  4. Perimeter vs paint defensive strength
  5. Transition defense quality
  6. Blitz/double-team frequency

Superstar adjustments:
  When a team double-teams a superstar, his scoring prop goes DOWN
  but his assists prop goes UP (he becomes a passer out of doubles).
  When a team plays zone, bigs struggle more, guards find more gaps.
  When a team switches everything, isolation scorers thrive but
  pick-and-roll dependent players lose their advantage.

This feeds directly into props_model.py to adjust individual player
prop lines based on the specific matchup they're facing tonight.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── Defensive scheme profiles ─────────────────────────────────────────────────

@dataclass
class TeamDefenseProfile:
    team:               str
    primary_coverage:   str    # "man", "zone", "switch_everything", "matchup_zone"
    vs_pick_roll:       str    # "drop", "hedge", "switch", "ice"
    zone_frequency:     float  # 0-1: how often they play zone
    blitz_frequency:    float  # 0-1: how often they double a star
    vs_superstar:       str    # "double", "ice", "chase", "switch", "help_and_recover"
    perimeter_defense:  str    # "elite", "good", "average", "poor"
    paint_defense:      str    # "elite", "good", "average", "poor"
    transition_defense: str    # "elite", "good", "average", "poor"
    # Stat multipliers vs league average (1.0 = average)
    pts_allowed_mult:   float = 1.0
    three_allowed_mult: float = 1.0
    paint_pts_mult:     float = 1.0
    ast_allowed_mult:   float = 1.0


NBA_DEFENSIVE_SCHEMES: dict[str, TeamDefenseProfile] = {
    # ── Elite defenses ──
    "Boston Celtics": TeamDefenseProfile(
        team="Boston Celtics",
        primary_coverage="switch_everything",
        vs_pick_roll="switch",
        zone_frequency=0.10,
        blitz_frequency=0.06,
        vs_superstar="switch",          # trust their defender 1-on-1
        perimeter_defense="elite",
        paint_defense="elite",
        transition_defense="good",
        pts_allowed_mult=0.88,
        three_allowed_mult=0.91,
        paint_pts_mult=0.90,
        ast_allowed_mult=0.95,
    ),
    "Oklahoma City Thunder": TeamDefenseProfile(
        team="Oklahoma City Thunder",
        primary_coverage="man",
        vs_pick_roll="hedge",
        zone_frequency=0.08,
        blitz_frequency=0.10,
        vs_superstar="help_and_recover",
        perimeter_defense="elite",
        paint_defense="good",
        transition_defense="elite",
        pts_allowed_mult=0.90,
        three_allowed_mult=0.93,
        paint_pts_mult=0.92,
        ast_allowed_mult=0.97,
    ),
    "Minnesota Timberwolves": TeamDefenseProfile(
        team="Minnesota Timberwolves",
        primary_coverage="man",
        vs_pick_roll="drop",            # Gobert sits in the paint
        zone_frequency=0.06,
        blitz_frequency=0.08,
        vs_superstar="double",          # send help at elite scorers
        perimeter_defense="good",
        paint_defense="elite",
        transition_defense="good",
        pts_allowed_mult=0.91,
        three_allowed_mult=0.89,        # guards stars off the three
        paint_pts_mult=0.80,            # Gobert dominates the paint
        ast_allowed_mult=1.05,          # doubles create kick-outs
    ),
    "Cleveland Cavaliers": TeamDefenseProfile(
        team="Cleveland Cavaliers",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.12,
        blitz_frequency=0.07,
        vs_superstar="help_and_recover",
        perimeter_defense="good",
        paint_defense="elite",
        transition_defense="good",
        pts_allowed_mult=0.92,
        three_allowed_mult=0.95,
        paint_pts_mult=0.85,
        ast_allowed_mult=1.02,
    ),
    "New York Knicks": TeamDefenseProfile(
        team="New York Knicks",
        primary_coverage="man",
        vs_pick_roll="hedge",
        zone_frequency=0.15,
        blitz_frequency=0.12,
        vs_superstar="double",
        perimeter_defense="good",
        paint_defense="good",
        transition_defense="good",
        pts_allowed_mult=0.93,
        three_allowed_mult=0.96,
        paint_pts_mult=0.92,
        ast_allowed_mult=1.06,
    ),
    "Dallas Mavericks": TeamDefenseProfile(
        team="Dallas Mavericks",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.10,
        blitz_frequency=0.08,
        vs_superstar="chase",
        perimeter_defense="good",
        paint_defense="good",
        transition_defense="average",
        pts_allowed_mult=0.95,
        three_allowed_mult=0.92,
        paint_pts_mult=0.94,
        ast_allowed_mult=1.00,
    ),
    "Denver Nuggets": TeamDefenseProfile(
        team="Denver Nuggets",
        primary_coverage="man",
        vs_pick_roll="drop",            # Murray/KCP chase, Jokic drops
        zone_frequency=0.07,
        blitz_frequency=0.06,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="good",
        transition_defense="average",
        pts_allowed_mult=0.97,
        three_allowed_mult=1.02,
        paint_pts_mult=0.96,
        ast_allowed_mult=1.00,
    ),
    # ── Average defenses ──
    "Los Angeles Lakers": TeamDefenseProfile(
        team="Los Angeles Lakers",
        primary_coverage="man",
        vs_pick_roll="switch",
        zone_frequency=0.08,
        blitz_frequency=0.10,
        vs_superstar="switch",
        perimeter_defense="average",
        paint_defense="good",
        transition_defense="average",
        pts_allowed_mult=1.00,
        three_allowed_mult=1.00,
        paint_pts_mult=0.98,
        ast_allowed_mult=1.00,
    ),
    "Miami Heat": TeamDefenseProfile(
        team="Miami Heat",
        primary_coverage="man",
        vs_pick_roll="hedge",
        zone_frequency=0.20,            # Spoelstra loves zone
        blitz_frequency=0.15,
        vs_superstar="double",
        perimeter_defense="good",
        paint_defense="average",
        transition_defense="good",
        pts_allowed_mult=0.97,
        three_allowed_mult=1.00,
        paint_pts_mult=1.00,
        ast_allowed_mult=1.08,          # doubles force extra passes
    ),
    "Indiana Pacers": TeamDefenseProfile(
        team="Indiana Pacers",
        primary_coverage="man",
        vs_pick_roll="hedge",
        zone_frequency=0.10,
        blitz_frequency=0.06,
        vs_superstar="ice",
        perimeter_defense="average",
        paint_defense="average",
        transition_defense="average",
        pts_allowed_mult=1.07,
        three_allowed_mult=1.05,
        paint_pts_mult=1.05,
        ast_allowed_mult=1.02,
    ),
    "Sacramento Kings": TeamDefenseProfile(
        team="Sacramento Kings",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.08,
        blitz_frequency=0.05,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="average",
        transition_defense="poor",
        pts_allowed_mult=1.06,
        three_allowed_mult=1.03,
        paint_pts_mult=1.04,
        ast_allowed_mult=1.01,
    ),
    # ── Weak defenses ──
    "Phoenix Suns": TeamDefenseProfile(
        team="Phoenix Suns",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.08,
        blitz_frequency=0.05,
        vs_superstar="ice",
        perimeter_defense="poor",
        paint_defense="average",
        transition_defense="poor",
        pts_allowed_mult=1.12,
        three_allowed_mult=1.08,
        paint_pts_mult=1.06,
        ast_allowed_mult=1.00,
    ),
    "Washington Wizards": TeamDefenseProfile(
        team="Washington Wizards",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.10,
        blitz_frequency=0.04,
        vs_superstar="help_and_recover",
        perimeter_defense="poor",
        paint_defense="poor",
        transition_defense="poor",
        pts_allowed_mult=1.18,
        three_allowed_mult=1.10,
        paint_pts_mult=1.15,
        ast_allowed_mult=1.02,
    ),
    "Charlotte Hornets": TeamDefenseProfile(
        team="Charlotte Hornets",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.12,
        blitz_frequency=0.05,
        vs_superstar="help_and_recover",
        perimeter_defense="poor",
        paint_defense="poor",
        transition_defense="average",
        pts_allowed_mult=1.15,
        three_allowed_mult=1.09,
        paint_pts_mult=1.12,
        ast_allowed_mult=1.03,
    ),
    "Brooklyn Nets": TeamDefenseProfile(
        team="Brooklyn Nets",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.08,
        blitz_frequency=0.05,
        vs_superstar="ice",
        perimeter_defense="poor",
        paint_defense="average",
        transition_defense="poor",
        pts_allowed_mult=1.14,
        three_allowed_mult=1.07,
        paint_pts_mult=1.10,
        ast_allowed_mult=1.01,
    ),
    "Atlanta Hawks": TeamDefenseProfile(
        team="Atlanta Hawks",
        primary_coverage="man",
        vs_pick_roll="hedge",
        zone_frequency=0.08,
        blitz_frequency=0.06,
        vs_superstar="help_and_recover",
        perimeter_defense="poor",
        paint_defense="average",
        transition_defense="poor",
        pts_allowed_mult=1.10,
        three_allowed_mult=1.06,
        paint_pts_mult=1.08,
        ast_allowed_mult=1.02,
    ),
    "Golden State Warriors": TeamDefenseProfile(
        team="Golden State Warriors",
        primary_coverage="switch_everything",
        vs_pick_roll="switch",
        zone_frequency=0.10,
        blitz_frequency=0.06,
        vs_superstar="switch",
        perimeter_defense="average",
        paint_defense="average",
        transition_defense="good",
        pts_allowed_mult=1.08,
        three_allowed_mult=1.05,
        paint_pts_mult=1.06,
        ast_allowed_mult=0.98,
    ),
    "San Antonio Spurs": TeamDefenseProfile(
        team="San Antonio Spurs",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.15,
        blitz_frequency=0.18,
        vs_superstar="double",
        perimeter_defense="average",
        paint_defense="good",
        transition_defense="average",
        pts_allowed_mult=1.02,
        three_allowed_mult=1.04,
        paint_pts_mult=0.82,
        ast_allowed_mult=1.10,
    ),
    "Memphis Grizzlies": TeamDefenseProfile(
        team="Memphis Grizzlies",
        primary_coverage="man",
        vs_pick_roll="hedge",
        zone_frequency=0.10,
        blitz_frequency=0.10,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="good",
        transition_defense="good",
        pts_allowed_mult=1.00,
        three_allowed_mult=1.00,
        paint_pts_mult=0.95,
        ast_allowed_mult=1.00,
    ),
    "Toronto Raptors": TeamDefenseProfile(
        team="Toronto Raptors",
        primary_coverage="switch_everything",
        vs_pick_roll="switch",
        zone_frequency=0.12,
        blitz_frequency=0.08,
        vs_superstar="switch",
        perimeter_defense="good",
        paint_defense="average",
        transition_defense="good",
        pts_allowed_mult=0.98,
        three_allowed_mult=0.97,
        paint_pts_mult=1.02,
        ast_allowed_mult=0.98,
    ),
    "Milwaukee Bucks": TeamDefenseProfile(
        team="Milwaukee Bucks",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.08,
        blitz_frequency=0.08,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="elite",
        transition_defense="average",
        pts_allowed_mult=0.96,
        three_allowed_mult=0.98,
        paint_pts_mult=0.88,
        ast_allowed_mult=1.02,
    ),
    "Chicago Bulls": TeamDefenseProfile(
        team="Chicago Bulls",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.08,
        blitz_frequency=0.06,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="average",
        transition_defense="average",
        pts_allowed_mult=1.05,
        three_allowed_mult=1.04,
        paint_pts_mult=1.03,
        ast_allowed_mult=1.01,
    ),
    "Utah Jazz": TeamDefenseProfile(
        team="Utah Jazz",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.10,
        blitz_frequency=0.05,
        vs_superstar="ice",
        perimeter_defense="poor",
        paint_defense="average",
        transition_defense="average",
        pts_allowed_mult=1.10,
        three_allowed_mult=1.07,
        paint_pts_mult=1.06,
        ast_allowed_mult=1.01,
    ),
    "Orlando Magic": TeamDefenseProfile(
        team="Orlando Magic",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.08,
        blitz_frequency=0.07,
        vs_superstar="help_and_recover",
        perimeter_defense="good",
        paint_defense="elite",
        transition_defense="good",
        pts_allowed_mult=0.92,
        three_allowed_mult=0.93,
        paint_pts_mult=0.84,
        ast_allowed_mult=1.00,
    ),
    "Detroit Pistons": TeamDefenseProfile(
        team="Detroit Pistons",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.10,
        blitz_frequency=0.05,
        vs_superstar="help_and_recover",
        perimeter_defense="poor",
        paint_defense="average",
        transition_defense="poor",
        pts_allowed_mult=1.12,
        three_allowed_mult=1.08,
        paint_pts_mult=1.10,
        ast_allowed_mult=1.02,
    ),
    "Houston Rockets": TeamDefenseProfile(
        team="Houston Rockets",
        primary_coverage="man",
        vs_pick_roll="hedge",
        zone_frequency=0.10,
        blitz_frequency=0.08,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="good",
        transition_defense="good",
        pts_allowed_mult=0.96,
        three_allowed_mult=0.97,
        paint_pts_mult=0.94,
        ast_allowed_mult=1.00,
    ),
    "Portland Trail Blazers": TeamDefenseProfile(
        team="Portland Trail Blazers",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.08,
        blitz_frequency=0.05,
        vs_superstar="ice",
        perimeter_defense="poor",
        paint_defense="poor",
        transition_defense="poor",
        pts_allowed_mult=1.13,
        three_allowed_mult=1.09,
        paint_pts_mult=1.11,
        ast_allowed_mult=1.02,
    ),
    "Los Angeles Clippers": TeamDefenseProfile(
        team="Los Angeles Clippers",
        primary_coverage="man",
        vs_pick_roll="hedge",
        zone_frequency=0.10,
        blitz_frequency=0.08,
        vs_superstar="double",
        perimeter_defense="good",
        paint_defense="average",
        transition_defense="average",
        pts_allowed_mult=1.00,
        three_allowed_mult=0.99,
        paint_pts_mult=1.00,
        ast_allowed_mult=1.03,
    ),
    "New Orleans Pelicans": TeamDefenseProfile(
        team="New Orleans Pelicans",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.10,
        blitz_frequency=0.08,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="good",
        transition_defense="average",
        pts_allowed_mult=0.98,
        three_allowed_mult=0.97,
        paint_pts_mult=0.93,
        ast_allowed_mult=1.00,
    ),
    "Philadelphia 76ers": TeamDefenseProfile(
        team="Philadelphia 76ers",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.08,
        blitz_frequency=0.07,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="good",
        transition_defense="average",
        pts_allowed_mult=1.02,
        three_allowed_mult=1.01,
        paint_pts_mult=0.96,
        ast_allowed_mult=1.00,
    ),
    "__default__": TeamDefenseProfile(
        team="__default__",
        primary_coverage="man",
        vs_pick_roll="drop",
        zone_frequency=0.10,
        blitz_frequency=0.07,
        vs_superstar="help_and_recover",
        perimeter_defense="average",
        paint_defense="average",
        transition_defense="average",
        pts_allowed_mult=1.0,
        three_allowed_mult=1.0,
        paint_pts_mult=1.0,
        ast_allowed_mult=1.0,
    ),
}


def get_defense(team_name: str) -> TeamDefenseProfile:
    """Returns defensive profile, falling back to default."""
    return NBA_DEFENSIVE_SCHEMES.get(team_name,
           NBA_DEFENSIVE_SCHEMES["__default__"])


# ── Superstar profiles ─────────────────────────────────────────────────────────

@dataclass
class SuperstarProfile:
    name:               str
    primary_threat:     str      # "scoring", "playmaking", "shooting", "post"
    attack_style:       str      # "iso", "pick_roll", "post", "off_ball", "all_around"
    # How stat lines shift vs different coverages (delta from baseline)
    vs_double: dict[str, float] = field(default_factory=dict)
    vs_zone:   dict[str, float] = field(default_factory=dict)
    vs_switch: dict[str, float] = field(default_factory=dict)
    vs_ice:    dict[str, float] = field(default_factory=dict)
    vs_chase:  dict[str, float] = field(default_factory=dict)
    # How often opponents game-plan specifically for this player
    defensive_focus: float = 0.5   # 0-1: 1.0 = every team builds a scheme for them


SUPERSTAR_PROFILES: dict[str, SuperstarProfile] = {

    "Victor Wembanyama": SuperstarProfile(
        name="Victor Wembanyama",
        primary_threat="scoring",
        attack_style="all_around",
        defensive_focus=0.95,
        # Teams double him in the post: scoring down, dimes up
        vs_double={"points": -4.5, "assists": +2.8, "rebounds": +0.5, "blocks": +0.3},
        # Zone keeps him off the block: less efficient scoring but more movement
        vs_zone={"points": -2.5, "assists": +1.5, "rebounds": +1.0},
        # Switching exposes mismatches — Wemby can shoot over anyone
        vs_switch={"points": +2.5, "assists": -0.5},
        # Ice pushes him baseline — less comfortable spot
        vs_ice={"points": -1.5, "assists": +0.8},
        # Chasing him off screens — gets clean looks
        vs_chase={"points": +1.5, "assists": +0.3},
    ),

    "Nikola Jokic": SuperstarProfile(
        name="Nikola Jokic",
        primary_threat="playmaking",
        attack_style="post",
        defensive_focus=0.95,
        # Jokic LOVES doubles — he's the best passer in the league out of them
        vs_double={"points": -2.5, "assists": +4.0, "rebounds": +0.8},
        # Zone gives him wide lanes to see passes — thrives
        vs_zone={"points": +1.5, "assists": +2.5, "rebounds": +1.0},
        # Switching puts a guard on him in the post — exploit
        vs_switch={"points": +3.5, "assists": +1.0, "rebounds": +0.5},
        # Drop coverage — he can shoot the mid-range freely
        vs_ice={"points": +1.0, "assists": +0.5},
        vs_chase={"points": +0.5, "assists": +0.5},
    ),

    "Giannis Antetokounmpo": SuperstarProfile(
        name="Giannis Antetokounmpo",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.95,
        # Teams drop to take away his drive — he has to shoot mid/three (weakness)
        vs_double={"points": -3.0, "assists": +2.5, "rebounds": +0.5},
        vs_zone={"points": -2.0, "assists": +1.5, "rebounds": +1.0},
        vs_switch={"points": +2.0, "assists": +0.5},
        vs_ice={"points": -1.5, "assists": +1.0},
        vs_chase={"points": +1.0, "assists": +0.0},
    ),

    "Stephen Curry": SuperstarProfile(
        name="Stephen Curry",
        primary_threat="shooting",
        attack_style="off_ball",
        defensive_focus=0.95,
        # Doubling Curry is nearly impossible — he moves without the ball
        vs_double={"points": -1.5, "assists": +2.0, "threes": -0.5},
        vs_zone={"points": -2.0, "assists": +1.5, "threes": -0.8},
        # Switching — Curry destroys guards and bigs alike off movement
        vs_switch={"points": +2.0, "threes": +0.7},
        # Ice forces him sideline — limits pull-up threes
        vs_ice={"points": -1.5, "threes": -0.6},
        vs_chase={"points": +1.5, "threes": +0.5},
    ),

    "LeBron James": SuperstarProfile(
        name="LeBron James",
        primary_threat="playmaking",
        attack_style="all_around",
        defensive_focus=0.90,
        vs_double={"points": -2.0, "assists": +3.5, "rebounds": +0.5},
        vs_zone={"points": -1.0, "assists": +2.0, "rebounds": +0.5},
        vs_switch={"points": +2.0, "assists": +0.5},
        vs_ice={"points": -1.0, "assists": +1.0},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),

    "Kevin Durant": SuperstarProfile(
        name="Kevin Durant",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.92,
        # KD is virtually unguardable 1-on-1 — doubles help more
        vs_double={"points": -3.5, "assists": +2.0},
        vs_zone={"points": -1.5, "assists": +1.5},
        vs_switch={"points": +3.0},   # can score over any mismatch
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.5},
    ),

    "Joel Embiid": SuperstarProfile(
        name="Joel Embiid",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.93,
        vs_double={"points": -4.0, "assists": +2.5, "rebounds": +0.8},
        vs_zone={"points": -2.0, "assists": +1.5, "rebounds": +1.0},
        vs_switch={"points": +3.5, "rebounds": +0.5},
        vs_ice={"points": -1.0, "assists": +0.8},
        vs_chase={"points": +1.0},
    ),

    "Luka Doncic": SuperstarProfile(
        name="Luka Doncic",
        primary_threat="playmaking",
        attack_style="pick_roll",
        defensive_focus=0.93,
        vs_double={"points": -2.5, "assists": +3.5},
        vs_zone={"points": -1.5, "assists": +2.5},
        vs_switch={"points": +2.0, "assists": +0.5},
        vs_ice={"points": -2.0, "assists": +1.5},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),

    "Jayson Tatum": SuperstarProfile(
        name="Jayson Tatum",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.88,
        vs_double={"points": -3.0, "assists": +2.0},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.5},
    ),

    "Shai Gilgeous-Alexander": SuperstarProfile(
        name="Shai Gilgeous-Alexander",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.88,
        vs_double={"points": -3.0, "assists": +2.5},
        vs_zone={"points": -1.5, "assists": +1.5},
        vs_switch={"points": +2.5},
        vs_ice={"points": -2.0, "assists": +1.0},
        vs_chase={"points": +1.5},
    ),

    "Devin Booker": SuperstarProfile(
        name="Devin Booker",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.82,
        vs_double={"points": -2.5, "assists": +2.0},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.5, "assists": +1.0},
        vs_chase={"points": +1.5},
    ),

    "Anthony Davis": SuperstarProfile(
        name="Anthony Davis",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.88,
        vs_double={"points": -3.5, "assists": +2.0, "rebounds": +1.0},
        vs_zone={"points": -1.5, "rebounds": +1.5},
        vs_switch={"points": +3.0, "rebounds": +0.5},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),

    "Tyrese Haliburton": SuperstarProfile(
        name="Tyrese Haliburton",
        primary_threat="playmaking",
        attack_style="pick_roll",
        defensive_focus=0.78,
        vs_double={"points": -1.5, "assists": +3.0},
        vs_zone={"points": -1.0, "assists": +2.0},
        vs_switch={"points": +1.5, "assists": +0.5},
        vs_ice={"points": -2.0, "assists": +1.5},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),

    "Donovan Mitchell": SuperstarProfile(
        name="Donovan Mitchell",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.82,
        vs_double={"points": -3.0, "assists": +2.0},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.5},
        vs_chase={"points": +1.5},
    ),

    # ── Additional guards / wings ──────────────────────────────────────────

    "Damian Lillard": SuperstarProfile(
        name="Damian Lillard",
        primary_threat="scoring",
        attack_style="pick_roll",
        defensive_focus=0.85,
        # Ice coverage — pushed sideline, limits his pull-up three
        vs_ice={"points": -2.5, "threes": -0.7, "assists": +1.0},
        vs_double={"points": -2.5, "assists": +2.5},
        vs_zone={"points": -1.5, "assists": +1.5},
        vs_switch={"points": +2.0, "threes": +0.5},
        vs_chase={"points": +1.5, "threes": +0.4},
    ),

    "Jalen Brunson": SuperstarProfile(
        name="Jalen Brunson",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.82,
        vs_double={"points": -2.0, "assists": +2.5},
        vs_zone={"points": -1.5, "assists": +1.5},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.5, "assists": +1.0},
        vs_chase={"points": +1.5},
    ),

    "De'Aaron Fox": SuperstarProfile(
        name="De'Aaron Fox",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.78,
        vs_double={"points": -2.5, "assists": +2.0},
        vs_zone={"points": -1.0, "assists": +1.5},
        vs_switch={"points": +2.0},
        vs_ice={"points": -2.0, "assists": +1.0},
        vs_chase={"points": +1.5},
    ),

    "Trae Young": SuperstarProfile(
        name="Trae Young",
        primary_threat="playmaking",
        attack_style="pick_roll",
        defensive_focus=0.85,
        # Ice is the blueprint vs Trae — pushes him off the arc
        vs_ice={"points": -3.0, "threes": -0.8, "assists": +1.5},
        vs_double={"points": -2.0, "assists": +4.0},
        vs_zone={"points": -2.5, "assists": +2.5},
        vs_switch={"points": +2.0, "assists": +0.5},
        vs_chase={"points": +1.5, "assists": +0.5},
    ),

    "Cade Cunningham": SuperstarProfile(
        name="Cade Cunningham",
        primary_threat="playmaking",
        attack_style="pick_roll",
        defensive_focus=0.78,
        vs_double={"points": -2.0, "assists": +2.5},
        vs_zone={"points": -1.5, "assists": +1.5},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.5, "assists": +1.0},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),

    "Ja Morant": SuperstarProfile(
        name="Ja Morant",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.85,
        vs_double={"points": -2.5, "assists": +2.5},
        vs_zone={"points": -1.5, "assists": +1.5},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.5, "assists": +1.0},
        vs_chase={"points": +1.5},
    ),

    "Paolo Banchero": SuperstarProfile(
        name="Paolo Banchero",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.78,
        vs_double={"points": -2.5, "assists": +2.0, "rebounds": +0.5},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.5},
    ),

    "Franz Wagner": SuperstarProfile(
        name="Franz Wagner",
        primary_threat="scoring",
        attack_style="all_around",
        defensive_focus=0.72,
        vs_double={"points": -1.5, "assists": +1.5},
        vs_zone={"points": -1.0, "assists": +1.0},
        vs_switch={"points": +1.5},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),

    "Zach LaVine": SuperstarProfile(
        name="Zach LaVine",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.78,
        vs_double={"points": -2.5, "assists": +1.5},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.5},
        vs_chase={"points": +2.0},
    ),

    "Darius Garland": SuperstarProfile(
        name="Darius Garland",
        primary_threat="playmaking",
        attack_style="pick_roll",
        defensive_focus=0.75,
        vs_ice={"points": -2.0, "assists": +1.5, "threes": -0.5},
        vs_double={"points": -1.5, "assists": +2.5},
        vs_zone={"points": -1.0, "assists": +2.0},
        vs_switch={"points": +1.5, "assists": +0.5},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),

    "Tyrese Maxey": SuperstarProfile(
        name="Tyrese Maxey",
        primary_threat="scoring",
        attack_style="off_ball",
        defensive_focus=0.78,
        vs_double={"points": -1.5, "assists": +1.5},
        vs_zone={"points": -1.0, "assists": +1.0},
        vs_switch={"points": +2.0, "threes": +0.5},
        vs_ice={"points": -1.5},
        vs_chase={"points": +1.5, "threes": +0.4},
    ),

    "Anthony Edwards": SuperstarProfile(
        name="Anthony Edwards",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.85,
        vs_double={"points": -2.5, "assists": +2.0},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.5},
        vs_chase={"points": +2.0},
    ),

    "Kawhi Leonard": SuperstarProfile(
        name="Kawhi Leonard",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.88,
        vs_double={"points": -2.0, "assists": +1.5},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.5},
    ),

    "Paul George": SuperstarProfile(
        name="Paul George",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.80,
        vs_double={"points": -2.0, "assists": +1.5},
        vs_zone={"points": -1.0, "assists": +1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.5},
    ),

    # ── Bigs / forwards ─────────────────────────────────────────────────────

    "Karl-Anthony Towns": SuperstarProfile(
        name="Karl-Anthony Towns",
        primary_threat="scoring",
        attack_style="pick_roll",
        defensive_focus=0.82,
        # Drop coverage invites him to shoot — he's an elite stretch big
        vs_double={"points": -2.5, "assists": +1.5, "rebounds": +0.8},
        vs_zone={"points": -1.5, "rebounds": +1.0},
        vs_switch={"points": +3.0, "threes": +0.6},
        vs_ice={"points": +1.0, "threes": +0.4},
        vs_chase={"points": +1.5, "threes": +0.3},
    ),

    "Domantas Sabonis": SuperstarProfile(
        name="Domantas Sabonis",
        primary_threat="playmaking",
        attack_style="post",
        defensive_focus=0.78,
        vs_double={"points": -2.0, "assists": +3.5, "rebounds": +1.0},
        vs_zone={"points": -1.0, "assists": +2.0, "rebounds": +1.5},
        vs_switch={"points": +2.0, "rebounds": +0.5},
        vs_ice={"points": +0.5, "rebounds": +0.5},
        vs_chase={"points": +0.5, "assists": +0.5},
    ),

    "Bam Adebayo": SuperstarProfile(
        name="Bam Adebayo",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.78,
        vs_double={"points": -2.0, "assists": +2.0, "rebounds": +1.0},
        vs_zone={"points": -1.5, "rebounds": +1.5},
        vs_switch={"points": +2.0, "rebounds": +0.5},
        vs_ice={"points": -0.5, "rebounds": +0.5},
        vs_chase={"points": +0.5},
    ),

    "Evan Mobley": SuperstarProfile(
        name="Evan Mobley",
        primary_threat="scoring",
        attack_style="all_around",
        defensive_focus=0.72,
        vs_double={"points": -1.5, "assists": +1.5, "rebounds": +1.0},
        vs_zone={"points": -1.0, "rebounds": +1.0},
        vs_switch={"points": +2.0, "rebounds": +0.5},
        vs_ice={"points": -0.5},
        vs_chase={"points": +0.5},
    ),

    "Jaren Jackson Jr.": SuperstarProfile(
        name="Jaren Jackson Jr.",
        primary_threat="scoring",
        attack_style="pick_roll",
        defensive_focus=0.75,
        vs_double={"points": -1.5, "assists": +1.0, "rebounds": +0.5},
        vs_zone={"points": -1.0, "rebounds": +0.5},
        vs_switch={"points": +2.5, "threes": +0.5},
        vs_ice={"points": +0.5},
        vs_chase={"points": +1.0, "threes": +0.3},
    ),

    "Rudy Gobert": SuperstarProfile(
        name="Rudy Gobert",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.70,
        # Gobert can only score inside — zone and drop both neutralize him
        vs_double={"points": -1.5, "rebounds": +1.0},
        vs_zone={"points": -2.0, "rebounds": +1.5},
        vs_switch={"points": +1.5, "rebounds": +0.5},
        vs_ice={"points": -0.5, "rebounds": +0.5},
        vs_chase={"points": +0.5},
    ),

    "Alperen Sengun": SuperstarProfile(
        name="Alperen Sengun",
        primary_threat="playmaking",
        attack_style="post",
        defensive_focus=0.75,
        vs_double={"points": -2.0, "assists": +3.0, "rebounds": +0.8},
        vs_zone={"points": -1.0, "assists": +1.5, "rebounds": +1.0},
        vs_switch={"points": +2.5, "rebounds": +0.5},
        vs_ice={"points": +0.5},
        vs_chase={"points": +0.5, "assists": +0.5},
    ),

    "Jaylen Brown": SuperstarProfile(
        name="Jaylen Brown",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.80,
        vs_double={"points": -2.5, "assists": +1.5},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.5},
    ),

    "Jimmy Butler": SuperstarProfile(
        name="Jimmy Butler",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.82,
        vs_double={"points": -2.0, "assists": +2.5},
        vs_zone={"points": -1.5, "assists": +1.5},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0, "assists": +1.0},
        vs_chase={"points": +1.0},
    ),

    "Pascal Siakam": SuperstarProfile(
        name="Pascal Siakam",
        primary_threat="scoring",
        attack_style="all_around",
        defensive_focus=0.75,
        vs_double={"points": -2.0, "assists": +1.5, "rebounds": +0.5},
        vs_zone={"points": -1.0, "rebounds": +0.8},
        vs_switch={"points": +2.0},
        vs_ice={"points": -0.5},
        vs_chase={"points": +1.0},
    ),

    # ── Remaining guards ─────────────────────────────────────────────────────

    "Jalen Williams": SuperstarProfile(
        name="Jalen Williams",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.80,
        vs_double={"points": -2.5, "assists": +2.0},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.5},
        vs_chase={"points": +1.5},
    ),
    "Luguentz Dort": SuperstarProfile(
        name="Luguentz Dort",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.55,
        vs_double={"points": -1.5, "assists": +0.8},
        vs_zone={"points": -1.0},
        vs_switch={"points": +1.5},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Isaiah Hartenstein": SuperstarProfile(
        name="Isaiah Hartenstein",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.60,
        vs_double={"points": -1.5, "assists": +1.5, "rebounds": +1.0},
        vs_zone={"points": -1.0, "rebounds": +1.0},
        vs_switch={"points": +1.5},
        vs_ice={"points": -0.5},
        vs_chase={"points": +0.5},
    ),
    "Malik Monk": SuperstarProfile(
        name="Malik Monk",
        primary_threat="scoring",
        attack_style="off_ball",
        defensive_focus=0.60,
        vs_double={"points": -1.5, "assists": +1.0},
        vs_zone={"points": -1.0},
        vs_switch={"points": +1.5, "threes": +0.4},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0, "threes": +0.3},
    ),
    "Keegan Murray": SuperstarProfile(
        name="Keegan Murray",
        primary_threat="scoring",
        attack_style="off_ball",
        defensive_focus=0.60,
        vs_double={"points": -1.5, "assists": +0.8},
        vs_zone={"points": -1.0, "threes": -0.3},
        vs_switch={"points": +1.5, "threes": +0.3},
        vs_ice={"points": -0.5},
        vs_chase={"points": +1.0, "threes": +0.3},
    ),
    "Josh Giddey": SuperstarProfile(
        name="Josh Giddey",
        primary_threat="playmaking",
        attack_style="all_around",
        defensive_focus=0.65,
        vs_double={"points": -1.0, "assists": +2.0, "rebounds": +0.8},
        vs_zone={"points": -0.5, "assists": +1.5},
        vs_switch={"points": +1.5, "rebounds": +0.5},
        vs_ice={"points": -1.0, "assists": +1.0},
        vs_chase={"points": +0.5, "assists": +0.5},
    ),
    "Scoot Henderson": SuperstarProfile(
        name="Scoot Henderson",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.62,
        vs_double={"points": -2.0, "assists": +2.0},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -2.0, "assists": +1.0},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),
    "Anfernee Simons": SuperstarProfile(
        name="Anfernee Simons",
        primary_threat="scoring",
        attack_style="off_ball",
        defensive_focus=0.65,
        vs_double={"points": -2.0, "assists": +1.5},
        vs_zone={"points": -1.5, "threes": -0.4},
        vs_switch={"points": +2.5, "threes": +0.6},
        vs_ice={"points": -1.5},
        vs_chase={"points": +1.5, "threes": +0.4},
    ),
    "Jalen Green": SuperstarProfile(
        name="Jalen Green",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.72,
        vs_double={"points": -2.5, "assists": +1.5},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.5},
        vs_chase={"points": +2.0},
    ),
    "RJ Barrett": SuperstarProfile(
        name="RJ Barrett",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.68,
        vs_double={"points": -2.0, "assists": +1.5},
        vs_zone={"points": -1.0, "assists": +1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Immanuel Quickley": SuperstarProfile(
        name="Immanuel Quickley",
        primary_threat="scoring",
        attack_style="pick_roll",
        defensive_focus=0.62,
        vs_double={"points": -1.5, "assists": +2.0},
        vs_zone={"points": -1.0, "assists": +1.5},
        vs_switch={"points": +1.5},
        vs_ice={"points": -2.0, "assists": +1.0},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),
    "Jordan Poole": SuperstarProfile(
        name="Jordan Poole",
        primary_threat="scoring",
        attack_style="off_ball",
        defensive_focus=0.60,
        vs_double={"points": -2.0, "assists": +1.0},
        vs_zone={"points": -1.5, "threes": -0.4},
        vs_switch={"points": +2.5, "threes": +0.5},
        vs_ice={"points": -1.5},
        vs_chase={"points": +1.5, "threes": +0.4},
    ),
    "Klay Thompson": SuperstarProfile(
        name="Klay Thompson",
        primary_threat="shooting",
        attack_style="off_ball",
        defensive_focus=0.75,
        vs_double={"points": -1.5, "threes": -0.5},
        vs_zone={"points": -2.0, "threes": -0.7},
        vs_switch={"points": +2.0, "threes": +0.6},
        vs_ice={"points": -1.0, "threes": -0.3},
        vs_chase={"points": +1.5, "threes": +0.5},
    ),
    "Fred VanVleet": SuperstarProfile(
        name="Fred VanVleet",
        primary_threat="playmaking",
        attack_style="pick_roll",
        defensive_focus=0.65,
        vs_double={"points": -1.5, "assists": +2.5},
        vs_zone={"points": -1.0, "assists": +1.5},
        vs_switch={"points": +1.5, "threes": +0.3},
        vs_ice={"points": -2.0, "assists": +1.5},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),
    "Chris Paul": SuperstarProfile(
        name="Chris Paul",
        primary_threat="playmaking",
        attack_style="pick_roll",
        defensive_focus=0.72,
        vs_double={"points": -1.5, "assists": +3.5},
        vs_zone={"points": -1.0, "assists": +2.5},
        vs_switch={"points": +1.5, "assists": +0.5},
        vs_ice={"points": -2.0, "assists": +2.0},
        vs_chase={"points": +0.5, "assists": +1.0},
    ),

    # ── Remaining bigs / forwards ────────────────────────────────────────────

    "Nic Claxton": SuperstarProfile(
        name="Nic Claxton",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.62,
        vs_double={"points": -1.5, "rebounds": +1.0, "assists": +1.0},
        vs_zone={"points": -1.0, "rebounds": +1.5},
        vs_switch={"points": +2.0, "rebounds": +0.5},
        vs_ice={"points": -0.5},
        vs_chase={"points": +0.5},
    ),
    "Brook Lopez": SuperstarProfile(
        name="Brook Lopez",
        primary_threat="scoring",
        attack_style="pick_roll",
        defensive_focus=0.62,
        vs_double={"points": -1.5, "rebounds": +0.8},
        vs_zone={"points": -2.0, "rebounds": +1.0},
        vs_switch={"points": +2.5, "threes": +0.5},
        vs_ice={"points": +0.5},
        vs_chase={"points": +1.0, "threes": +0.3},
    ),
    "Daniel Gafford": SuperstarProfile(
        name="Daniel Gafford",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.58,
        vs_double={"points": -1.5, "rebounds": +1.0},
        vs_zone={"points": -1.5, "rebounds": +1.5},
        vs_switch={"points": +2.0},
        vs_ice={"points": -0.5},
        vs_chase={"points": +0.5},
    ),
    "Myles Turner": SuperstarProfile(
        name="Myles Turner",
        primary_threat="scoring",
        attack_style="pick_roll",
        defensive_focus=0.65,
        vs_double={"points": -1.5, "rebounds": +0.8},
        vs_zone={"points": -1.5, "rebounds": +1.0},
        vs_switch={"points": +2.5, "threes": +0.5},
        vs_ice={"points": +0.5},
        vs_chase={"points": +1.0},
    ),
    "Bobby Portis": SuperstarProfile(
        name="Bobby Portis",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.58,
        vs_double={"points": -2.0, "rebounds": +1.5},
        vs_zone={"points": -1.0, "rebounds": +1.5},
        vs_switch={"points": +2.0},
        vs_ice={"points": -0.5},
        vs_chase={"points": +0.5},
    ),
    "Zion Williamson": SuperstarProfile(
        name="Zion Williamson",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.88,
        vs_double={"points": -3.5, "assists": +2.0, "rebounds": +0.8},
        vs_zone={"points": -2.0, "rebounds": +1.5},
        vs_switch={"points": +3.5},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Brandon Ingram": SuperstarProfile(
        name="Brandon Ingram",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.75,
        vs_double={"points": -2.5, "assists": +1.5},
        vs_zone={"points": -1.5, "assists": +1.0},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.5},
    ),
    "Herbert Jones": SuperstarProfile(
        name="Herbert Jones",
        primary_threat="scoring",
        attack_style="all_around",
        defensive_focus=0.50,
        vs_double={"points": -0.5, "rebounds": +0.5},
        vs_zone={"points": -0.5},
        vs_switch={"points": +1.0},
        vs_ice={"points": -0.5},
        vs_chase={"points": +0.5},
    ),
    "OG Anunoby": SuperstarProfile(
        name="OG Anunoby",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.70,
        vs_double={"points": -2.0, "assists": +1.0},
        vs_zone={"points": -1.5, "threes": -0.3},
        vs_switch={"points": +2.0, "threes": +0.4},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Miles Bridges": SuperstarProfile(
        name="Miles Bridges",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.65,
        vs_double={"points": -2.0, "assists": +1.0, "rebounds": +0.5},
        vs_zone={"points": -1.0, "rebounds": +0.5},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Jonathan Kuminga": SuperstarProfile(
        name="Jonathan Kuminga",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.65,
        vs_double={"points": -2.0, "assists": +1.0},
        vs_zone={"points": -1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Julius Randle": SuperstarProfile(
        name="Julius Randle",
        primary_threat="scoring",
        attack_style="post",
        defensive_focus=0.75,
        vs_double={"points": -3.0, "assists": +2.5, "rebounds": +0.8},
        vs_zone={"points": -2.0, "rebounds": +1.5},
        vs_switch={"points": +2.5},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Kristaps Porzingis": SuperstarProfile(
        name="Kristaps Porzingis",
        primary_threat="scoring",
        attack_style="pick_roll",
        defensive_focus=0.78,
        vs_double={"points": -2.0, "assists": +1.5, "rebounds": +0.8},
        vs_zone={"points": -1.5, "rebounds": +1.0},
        vs_switch={"points": +3.0, "threes": +0.5},
        vs_ice={"points": +0.5, "threes": +0.3},
        vs_chase={"points": +1.5, "threes": +0.4},
    ),
    "Amen Thompson": SuperstarProfile(
        name="Amen Thompson",
        primary_threat="scoring",
        attack_style="all_around",
        defensive_focus=0.65,
        vs_double={"points": -1.5, "assists": +1.5, "rebounds": +0.8},
        vs_zone={"points": -1.0, "rebounds": +1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Scottie Barnes": SuperstarProfile(
        name="Scottie Barnes",
        primary_threat="playmaking",
        attack_style="all_around",
        defensive_focus=0.72,
        vs_double={"points": -2.0, "assists": +2.0, "rebounds": +0.8},
        vs_zone={"points": -1.0, "assists": +1.5, "rebounds": +1.0},
        vs_switch={"points": +2.0, "rebounds": +0.5},
        vs_ice={"points": -1.0, "assists": +1.0},
        vs_chase={"points": +1.0, "assists": +0.5},
    ),
    "Jabari Smith Jr.": SuperstarProfile(
        name="Jabari Smith Jr.",
        primary_threat="scoring",
        attack_style="pick_roll",
        defensive_focus=0.62,
        vs_double={"points": -1.5, "rebounds": +0.8},
        vs_zone={"points": -1.0, "rebounds": +0.5},
        vs_switch={"points": +2.0, "threes": +0.4},
        vs_ice={"points": +0.5},
        vs_chase={"points": +1.0, "threes": +0.3},
    ),
    "Andrew Wiggins": SuperstarProfile(
        name="Andrew Wiggins",
        primary_threat="scoring",
        attack_style="iso",
        defensive_focus=0.62,
        vs_double={"points": -1.5, "assists": +1.0},
        vs_zone={"points": -1.0},
        vs_switch={"points": +2.0},
        vs_ice={"points": -1.0},
        vs_chase={"points": +1.0},
    ),
    "Mike Conley": SuperstarProfile(
        name="Mike Conley",
        primary_threat="playmaking",
        attack_style="pick_roll",
        defensive_focus=0.60,
        vs_double={"points": -1.0, "assists": +2.5},
        vs_zone={"points": -0.5, "assists": +1.5},
        vs_switch={"points": +1.5, "assists": +0.5},
        vs_ice={"points": -1.5, "assists": +1.5},
        vs_chase={"points": +0.5, "assists": +0.5},
    ),
}


# ── Core adjustment function ───────────────────────────────────────────────────

@dataclass
class PropAdjustment:
    """Stat adjustments to apply to a player's prop line given the matchup."""
    player:         str
    opponent:       str
    coverage_type:  str
    blitz_likely:   bool
    adjustments:    dict[str, float]   # stat → delta (e.g. {"points": -3.5, "assists": +2.0})
    rationale:      list[str]


def get_prop_adjustment(player_name: str, opponent: str) -> PropAdjustment:
    """
    Given a player and opponent, returns stat adjustments based on
    the opponent's defensive scheme and whether they'll double this player.
    """
    defense  = get_defense(opponent)
    star     = SUPERSTAR_PROFILES.get(player_name)

    adjustments: dict[str, float] = {}
    rationale:   list[str]        = []

    # Apply general opponent multipliers (affects all players, not just stars)
    # These are already handled in the props_model via _opp_adjustment —
    # here we layer on scheme-specific adjustments for known superstars

    if not star:
        # Non-superstar: just return scheme context for rationale
        rationale.append(
            f"{opponent} runs {defense.primary_coverage} "
            f"(zone {defense.zone_frequency:.0%} of possessions)"
        )
        return PropAdjustment(
            player=player_name, opponent=opponent,
            coverage_type=defense.primary_coverage,
            blitz_likely=False,
            adjustments={},
            rationale=rationale,
        )

    # Determine likely coverage vs this specific superstar
    blitz_likely = (defense.blitz_frequency >= 0.12 or
                    defense.vs_superstar == "double") and \
                   star.defensive_focus >= 0.80

    if blitz_likely:
        coverage = "vs_double"
        cov_label = "double-team"
        delta = star.vs_double
    elif defense.vs_superstar == "switch":
        coverage = "vs_switch"
        cov_label = "switch-everything"
        delta = star.vs_switch
    elif defense.vs_superstar == "ice":
        coverage = "vs_ice"
        cov_label = "ice coverage (push sideline)"
        delta = star.vs_ice
    elif defense.vs_superstar == "chase":
        coverage = "vs_chase"
        cov_label = "chase off screens"
        delta = star.vs_chase
    elif defense.zone_frequency >= 0.18:
        coverage = "vs_zone"
        cov_label = f"zone ({defense.zone_frequency:.0%} rate)"
        delta = star.vs_zone
    else:
        coverage = "vs_chase"
        cov_label = "help-and-recover"
        delta = star.vs_chase

    adjustments = dict(delta)

    rationale += [
        f"{opponent} defensive scheme: {defense.primary_coverage} — "
        f"{defense.perimeter_defense} perimeter / {defense.paint_defense} paint",
        f"Expected coverage on {player_name}: {cov_label}",
    ]

    for stat, adj in adjustments.items():
        direction = "up" if adj > 0 else "down"
        rationale.append(
            f"  → {stat}: {adj:+.1f} pts ({direction}) — "
            f"{'doubles create kick-outs' if stat == 'assists' and adj > 0 else 'reduced touches' if stat == 'points' and adj < 0 else 'scheme effect'}"
        )

    if blitz_likely:
        rationale.append(
            f"  ★ BOOK NOTE: If {player_name}'s assists line is available, "
            f"OVER is likely underpriced — doubles inflate assist numbers"
        )

    return PropAdjustment(
        player=player_name,
        opponent=opponent,
        coverage_type=coverage,
        blitz_likely=blitz_likely,
        adjustments=adjustments,
        rationale=rationale,
    )


def apply_adjustment_to_prop(prop_type: str, line: float,
                               adj: PropAdjustment) -> tuple[float, list[str]]:
    """
    Applies a PropAdjustment to a specific prop line.
    Returns (adjusted_line_for_analysis, extra_rationale).
    The adjusted line is what we compare against — if the delta pushes
    the player's expected output further from the book line, edge grows.
    """
    clean = prop_type.replace(" ", "_").lower()
    delta = 0.0

    # Match stat name to adjustment key
    for key, val in adj.adjustments.items():
        if key in clean or clean in key:
            delta = val
            break

    if delta == 0.0:
        return line, []

    # We don't move the line — we shift the player's projected average
    # The caller adds delta to adj_avg before computing z-score
    notes = [f"Scheme adj ({adj.coverage_type}): {delta:+.1f} to projected {prop_type}"]
    if adj.blitz_likely:
        notes.append(f"Double-team likely → {prop_type} shift confirmed")

    return delta, notes
