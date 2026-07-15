"""
NFL Defensive Scheme & Superstar Adjustment Layer
==================================================
Models how each NFL team's defensive scheme affects player prop lines.

Key dimensions:
  1. Coverage shell (Cover 1/2/3/4, Tampa 2, Quarters, Dime)
  2. Man vs zone frequency
  3. Blitz / pressure rate
  4. How teams handle elite WRs (shadow, bracket, trail, off)
  5. TE matchup defender (LB = exploitable, S, nickel LB)
  6. Mobile QB spy usage
  7. Box stacking vs elite RBs
  8. Pass rush quality (affects QB props — pressure = lower yards)

Player profiles for elite skill players:
  QBs  — spy coverage, coverage shell vs their tendencies
  WRs  — shadow, bracket, press vs their route tree
  TEs  — who guards them (LB/S/nickel LB)
  RBs  — box count, spy, LB talent

Adjustments feed directly into props_model.py analyse_prop()
to shift projected averages before z-score computation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── Defensive team profiles ───────────────────────────────────────────────────

@dataclass
class NFLTeamDefenseProfile:
    team:               str
    # Coverage shell
    primary_shell:      str    # "cover_1","cover_2","cover_3","cover_4","tampa_2","quarters","dime"
    man_frequency:      float  # 0-1: how often they play man coverage
    zone_frequency:     float  # 0-1
    # Pressure
    blitz_rate:         float  # 0-1: % of snaps with 5+ rushers
    pass_rush_grade:    str    # "elite","good","average","poor"
    # WR coverage
    uses_shadow_cb:     bool   # do they assign CB1 to follow #1 WR everywhere
    vs_elite_wr:        str    # "shadow","bracket","trail","off"
    # TE matchup
    te_covered_by:      str    # "lb","safety","nickel_lb","cb"
    # QB adjustments
    spies_mobile_qb:    bool
    # RB adjustments
    avg_box_count:      float  # average defenders in box
    # Stat multipliers vs league avg
    pass_yds_allowed_mult:  float = 1.0
    rush_yds_allowed_mult:  float = 1.0
    rec_yds_allowed_mult:   float = 1.0
    td_allowed_mult:        float = 1.0
    sack_rate_mult:         float = 1.0  # >1 = more sacks than avg


NFL_DEFENSIVE_SCHEMES: dict[str, NFLTeamDefenseProfile] = {

    # ── Elite defenses ──────────────────────────────────────────────────────

    "San Francisco 49ers": NFLTeamDefenseProfile(
        team="San Francisco 49ers",
        primary_shell="cover_3",
        man_frequency=0.32,
        zone_frequency=0.68,
        blitz_rate=0.28,
        pass_rush_grade="elite",
        uses_shadow_cb=False,           # scheme-based, not star CB
        vs_elite_wr="bracket",
        te_covered_by="nickel_lb",
        spies_mobile_qb=True,
        avg_box_count=6.8,
        pass_yds_allowed_mult=0.88,
        rush_yds_allowed_mult=0.85,
        rec_yds_allowed_mult=0.87,
        td_allowed_mult=0.86,
        sack_rate_mult=1.35,
    ),
    "Baltimore Ravens": NFLTeamDefenseProfile(
        team="Baltimore Ravens",
        primary_shell="cover_1",
        man_frequency=0.62,
        zone_frequency=0.38,
        blitz_rate=0.38,               # Wink Martindale legacy — heavy blitz
        pass_rush_grade="elite",
        uses_shadow_cb=True,
        vs_elite_wr="shadow",
        te_covered_by="safety",
        spies_mobile_qb=False,         # they blitz instead of spy
        avg_box_count=6.5,
        pass_yds_allowed_mult=0.90,
        rush_yds_allowed_mult=0.88,
        rec_yds_allowed_mult=0.89,
        td_allowed_mult=0.88,
        sack_rate_mult=1.28,
    ),
    "Cleveland Browns": NFLTeamDefenseProfile(
        team="Cleveland Browns",
        primary_shell="cover_3",
        man_frequency=0.38,
        zone_frequency=0.62,
        blitz_rate=0.32,
        pass_rush_grade="elite",
        uses_shadow_cb=False,
        vs_elite_wr="bracket",
        te_covered_by="lb",
        spies_mobile_qb=True,
        avg_box_count=6.6,
        pass_yds_allowed_mult=0.91,
        rush_yds_allowed_mult=0.87,
        rec_yds_allowed_mult=0.90,
        td_allowed_mult=0.89,
        sack_rate_mult=1.30,
    ),
    "Pittsburgh Steelers": NFLTeamDefenseProfile(
        team="Pittsburgh Steelers",
        primary_shell="cover_3",
        man_frequency=0.30,
        zone_frequency=0.70,
        blitz_rate=0.35,
        pass_rush_grade="elite",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=True,
        avg_box_count=6.8,
        pass_yds_allowed_mult=0.92,
        rush_yds_allowed_mult=0.90,
        rec_yds_allowed_mult=0.91,
        td_allowed_mult=0.90,
        sack_rate_mult=1.25,
    ),
    "New England Patriots": NFLTeamDefenseProfile(
        team="New England Patriots",
        primary_shell="cover_2",        # Belichick base
        man_frequency=0.45,
        zone_frequency=0.55,
        blitz_rate=0.22,
        pass_rush_grade="good",
        uses_shadow_cb=True,
        vs_elite_wr="bracket",
        te_covered_by="lb",             # historically linebackers cover TEs
        spies_mobile_qb=True,           # classic Belichick spy
        avg_box_count=6.5,
        pass_yds_allowed_mult=0.93,
        rush_yds_allowed_mult=0.91,
        rec_yds_allowed_mult=0.92,
        td_allowed_mult=0.91,
        sack_rate_mult=1.10,
    ),
    "Buffalo Bills": NFLTeamDefenseProfile(
        team="Buffalo Bills",
        primary_shell="cover_1",
        man_frequency=0.55,
        zone_frequency=0.45,
        blitz_rate=0.30,
        pass_rush_grade="good",
        uses_shadow_cb=True,            # Tre White when healthy
        vs_elite_wr="shadow",
        te_covered_by="nickel_lb",
        spies_mobile_qb=False,
        avg_box_count=6.3,
        pass_yds_allowed_mult=0.92,
        rush_yds_allowed_mult=0.93,
        rec_yds_allowed_mult=0.91,
        td_allowed_mult=0.91,
        sack_rate_mult=1.15,
    ),
    "Kansas City Chiefs": NFLTeamDefenseProfile(
        team="Kansas City Chiefs",
        primary_shell="cover_1",
        man_frequency=0.50,
        zone_frequency=0.50,
        blitz_rate=0.24,
        pass_rush_grade="good",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="safety",
        spies_mobile_qb=False,
        avg_box_count=6.2,
        pass_yds_allowed_mult=0.94,
        rush_yds_allowed_mult=0.96,
        rec_yds_allowed_mult=0.93,
        td_allowed_mult=0.93,
        sack_rate_mult=1.05,
    ),
    "Philadelphia Eagles": NFLTeamDefenseProfile(
        team="Philadelphia Eagles",
        primary_shell="cover_4",
        man_frequency=0.35,
        zone_frequency=0.65,
        blitz_rate=0.26,
        pass_rush_grade="elite",
        uses_shadow_cb=False,
        vs_elite_wr="bracket",
        te_covered_by="safety",
        spies_mobile_qb=True,
        avg_box_count=6.4,
        pass_yds_allowed_mult=0.91,
        rush_yds_allowed_mult=0.86,
        rec_yds_allowed_mult=0.90,
        td_allowed_mult=0.89,
        sack_rate_mult=1.32,
    ),
    "Miami Dolphins": NFLTeamDefenseProfile(
        team="Miami Dolphins",
        primary_shell="cover_1",
        man_frequency=0.58,
        zone_frequency=0.42,
        blitz_rate=0.42,               # Vic Fangio-era blitz heavy
        pass_rush_grade="good",
        uses_shadow_cb=True,
        vs_elite_wr="shadow",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.0,
        pass_yds_allowed_mult=0.93,
        rush_yds_allowed_mult=0.95,
        rec_yds_allowed_mult=0.92,
        td_allowed_mult=0.92,
        sack_rate_mult=1.20,
    ),
    "Minnesota Vikings": NFLTeamDefenseProfile(
        team="Minnesota Vikings",
        primary_shell="cover_2",
        man_frequency=0.35,
        zone_frequency=0.65,
        blitz_rate=0.28,
        pass_rush_grade="good",
        uses_shadow_cb=False,
        vs_elite_wr="bracket",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.3,
        pass_yds_allowed_mult=0.94,
        rush_yds_allowed_mult=0.94,
        rec_yds_allowed_mult=0.93,
        td_allowed_mult=0.93,
        sack_rate_mult=1.12,
    ),
    "Dallas Cowboys": NFLTeamDefenseProfile(
        team="Dallas Cowboys",
        primary_shell="cover_1",
        man_frequency=0.52,
        zone_frequency=0.48,
        blitz_rate=0.26,
        pass_rush_grade="good",
        uses_shadow_cb=True,
        vs_elite_wr="shadow",
        te_covered_by="safety",
        spies_mobile_qb=False,
        avg_box_count=6.2,
        pass_yds_allowed_mult=0.95,
        rush_yds_allowed_mult=0.96,
        rec_yds_allowed_mult=0.94,
        td_allowed_mult=0.94,
        sack_rate_mult=1.10,
    ),
    # ── Average / below-average defenses ──────────────────────────────────

    "Los Angeles Rams": NFLTeamDefenseProfile(
        team="Los Angeles Rams",
        primary_shell="cover_3",
        man_frequency=0.40,
        zone_frequency=0.60,
        blitz_rate=0.25,
        pass_rush_grade="good",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.3,
        pass_yds_allowed_mult=0.97,
        rush_yds_allowed_mult=0.95,
        rec_yds_allowed_mult=0.96,
        td_allowed_mult=0.96,
        sack_rate_mult=1.08,
    ),
    "Denver Broncos": NFLTeamDefenseProfile(
        team="Denver Broncos",
        primary_shell="cover_3",
        man_frequency=0.38,
        zone_frequency=0.62,
        blitz_rate=0.24,
        pass_rush_grade="average",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.3,
        pass_yds_allowed_mult=0.97,
        rush_yds_allowed_mult=0.96,
        rec_yds_allowed_mult=0.96,
        td_allowed_mult=0.96,
        sack_rate_mult=1.00,
    ),
    "New York Jets": NFLTeamDefenseProfile(
        team="New York Jets",
        primary_shell="cover_1",
        man_frequency=0.55,
        zone_frequency=0.45,
        blitz_rate=0.30,
        pass_rush_grade="elite",       # Quinnen Williams era
        uses_shadow_cb=True,
        vs_elite_wr="shadow",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.4,
        pass_yds_allowed_mult=0.96,
        rush_yds_allowed_mult=0.94,
        rec_yds_allowed_mult=0.95,
        td_allowed_mult=0.95,
        sack_rate_mult=1.22,
    ),
    "Seattle Seahawks": NFLTeamDefenseProfile(
        team="Seattle Seahawks",
        primary_shell="cover_3",       # Pete Carroll base
        man_frequency=0.38,
        zone_frequency=0.62,
        blitz_rate=0.22,
        pass_rush_grade="average",
        uses_shadow_cb=True,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.5,
        pass_yds_allowed_mult=0.98,
        rush_yds_allowed_mult=0.98,
        rec_yds_allowed_mult=0.97,
        td_allowed_mult=0.97,
        sack_rate_mult=0.98,
    ),
    "Green Bay Packers": NFLTeamDefenseProfile(
        team="Green Bay Packers",
        primary_shell="cover_1",
        man_frequency=0.48,
        zone_frequency=0.52,
        blitz_rate=0.24,
        pass_rush_grade="average",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.2,
        pass_yds_allowed_mult=0.99,
        rush_yds_allowed_mult=0.98,
        rec_yds_allowed_mult=0.98,
        td_allowed_mult=0.97,
        sack_rate_mult=1.02,
    ),
    "Tampa Bay Buccaneers": NFLTeamDefenseProfile(
        team="Tampa Bay Buccaneers",
        primary_shell="tampa_2",       # literally invented here
        man_frequency=0.30,
        zone_frequency=0.70,
        blitz_rate=0.20,
        pass_rush_grade="good",
        uses_shadow_cb=False,
        vs_elite_wr="off",             # Tampa 2 keeps everything in front
        te_covered_by="nickel_lb",
        spies_mobile_qb=False,
        avg_box_count=6.1,
        pass_yds_allowed_mult=0.96,
        rush_yds_allowed_mult=0.95,
        rec_yds_allowed_mult=0.95,
        td_allowed_mult=0.95,
        sack_rate_mult=1.05,
    ),
    "Los Angeles Chargers": NFLTeamDefenseProfile(
        team="Los Angeles Chargers",
        primary_shell="cover_2",
        man_frequency=0.35,
        zone_frequency=0.65,
        blitz_rate=0.22,
        pass_rush_grade="average",
        uses_shadow_cb=False,
        vs_elite_wr="bracket",
        te_covered_by="safety",
        spies_mobile_qb=False,
        avg_box_count=6.2,
        pass_yds_allowed_mult=1.00,
        rush_yds_allowed_mult=1.00,
        rec_yds_allowed_mult=1.00,
        td_allowed_mult=1.00,
        sack_rate_mult=1.00,
    ),
    # ── Weak defenses ──────────────────────────────────────────────────────

    "Detroit Lions": NFLTeamDefenseProfile(
        team="Detroit Lions",
        primary_shell="cover_3",
        man_frequency=0.32,
        zone_frequency=0.68,
        blitz_rate=0.20,
        pass_rush_grade="poor",
        uses_shadow_cb=False,
        vs_elite_wr="off",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=5.8,
        pass_yds_allowed_mult=1.12,
        rush_yds_allowed_mult=1.08,
        rec_yds_allowed_mult=1.10,
        td_allowed_mult=1.10,
        sack_rate_mult=0.80,
    ),
    "Indianapolis Colts": NFLTeamDefenseProfile(
        team="Indianapolis Colts",
        primary_shell="cover_1",
        man_frequency=0.48,
        zone_frequency=0.52,
        blitz_rate=0.25,
        pass_rush_grade="poor",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.1,
        pass_yds_allowed_mult=1.09,
        rush_yds_allowed_mult=1.05,
        rec_yds_allowed_mult=1.08,
        td_allowed_mult=1.07,
        sack_rate_mult=0.85,
    ),
    "Washington Commanders": NFLTeamDefenseProfile(
        team="Washington Commanders",
        primary_shell="cover_3",
        man_frequency=0.35,
        zone_frequency=0.65,
        blitz_rate=0.22,
        pass_rush_grade="average",
        uses_shadow_cb=False,
        vs_elite_wr="off",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.0,
        pass_yds_allowed_mult=1.08,
        rush_yds_allowed_mult=1.06,
        rec_yds_allowed_mult=1.07,
        td_allowed_mult=1.06,
        sack_rate_mult=0.92,
    ),
    "Chicago Bears": NFLTeamDefenseProfile(
        team="Chicago Bears",
        primary_shell="cover_1",
        man_frequency=0.50,
        zone_frequency=0.50,
        blitz_rate=0.28,
        pass_rush_grade="poor",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.0,
        pass_yds_allowed_mult=1.11,
        rush_yds_allowed_mult=1.06,
        rec_yds_allowed_mult=1.10,
        td_allowed_mult=1.09,
        sack_rate_mult=0.88,
    ),
    "New Orleans Saints": NFLTeamDefenseProfile(
        team="New Orleans Saints",
        primary_shell="cover_1",
        man_frequency=0.52,
        zone_frequency=0.48,
        blitz_rate=0.30,
        pass_rush_grade="average",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.4,
        pass_yds_allowed_mult=1.04,
        rush_yds_allowed_mult=1.10,
        rec_yds_allowed_mult=1.04,
        td_allowed_mult=1.05,
        sack_rate_mult=1.02,
    ),
    "Arizona Cardinals": NFLTeamDefenseProfile(
        team="Arizona Cardinals",
        primary_shell="cover_3",
        man_frequency=0.30,
        zone_frequency=0.70,
        blitz_rate=0.20,
        pass_rush_grade="poor",
        uses_shadow_cb=False,
        vs_elite_wr="off",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=5.9,
        pass_yds_allowed_mult=1.10,
        rush_yds_allowed_mult=1.08,
        rec_yds_allowed_mult=1.09,
        td_allowed_mult=1.08,
        sack_rate_mult=0.82,
    ),
    "Carolina Panthers": NFLTeamDefenseProfile(
        team="Carolina Panthers",
        primary_shell="cover_3",
        man_frequency=0.32,
        zone_frequency=0.68,
        blitz_rate=0.22,
        pass_rush_grade="poor",
        uses_shadow_cb=False,
        vs_elite_wr="off",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=5.8,
        pass_yds_allowed_mult=1.13,
        rush_yds_allowed_mult=1.10,
        rec_yds_allowed_mult=1.12,
        td_allowed_mult=1.11,
        sack_rate_mult=0.78,
    ),
    "Tennessee Titans": NFLTeamDefenseProfile(
        team="Tennessee Titans",
        primary_shell="cover_3",
        man_frequency=0.35,
        zone_frequency=0.65,
        blitz_rate=0.22,
        pass_rush_grade="poor",
        uses_shadow_cb=False,
        vs_elite_wr="off",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.0,
        pass_yds_allowed_mult=1.10,
        rush_yds_allowed_mult=1.08,
        rec_yds_allowed_mult=1.10,
        td_allowed_mult=1.09,
        sack_rate_mult=0.85,
    ),
    # Remaining teams at roughly league average
    "Atlanta Falcons":       NFLTeamDefenseProfile("Atlanta Falcons",       "cover_3", 0.38, 0.62, 0.24, "average", False, "trail",  "lb",     False, 6.1, 1.02, 1.01, 1.01, 1.01, 0.97),
    "Jacksonville Jaguars":  NFLTeamDefenseProfile("Jacksonville Jaguars",  "cover_1", 0.45, 0.55, 0.26, "average", False, "trail",  "lb",     False, 6.2, 1.01, 1.00, 1.01, 1.00, 0.98),
    "Las Vegas Raiders":     NFLTeamDefenseProfile("Las Vegas Raiders",     "cover_3", 0.35, 0.65, 0.22, "average", False, "off",    "lb",     False, 6.0, 1.04, 1.03, 1.03, 1.02, 0.94),
    "Houston Texans":        NFLTeamDefenseProfile("Houston Texans",        "cover_1", 0.48, 0.52, 0.28, "average", False, "trail",  "safety", False, 6.2, 1.00, 0.99, 1.00, 0.99, 1.02),
    "Cincinnati Bengals":    NFLTeamDefenseProfile("Cincinnati Bengals",    "cover_1", 0.42, 0.58, 0.26, "average", False, "trail",  "lb",     False, 6.1, 1.01, 1.00, 1.00, 1.00, 0.98),
    "New York Giants":       NFLTeamDefenseProfile("New York Giants",       "cover_3", 0.38, 0.62, 0.25, "average", False, "trail",  "lb",     False, 6.2, 1.02, 1.01, 1.01, 1.01, 0.97),
    "__default__": NFLTeamDefenseProfile(
        team="__default__",
        primary_shell="cover_3",
        man_frequency=0.40,
        zone_frequency=0.60,
        blitz_rate=0.25,
        pass_rush_grade="average",
        uses_shadow_cb=False,
        vs_elite_wr="trail",
        te_covered_by="lb",
        spies_mobile_qb=False,
        avg_box_count=6.2,
        pass_yds_allowed_mult=1.0,
        rush_yds_allowed_mult=1.0,
        rec_yds_allowed_mult=1.0,
        td_allowed_mult=1.0,
        sack_rate_mult=1.0,
    ),
}

# Clean up the accidental None entry caused by repeated key
NFL_DEFENSIVE_SCHEMES.pop("San Francisco 49ers", None)


def get_nfl_defense(team_name: str) -> NFLTeamDefenseProfile:
    return NFL_DEFENSIVE_SCHEMES.get(team_name,
           NFL_DEFENSIVE_SCHEMES["__default__"])


# ── Superstar profiles ─────────────────────────────────────────────────────────

@dataclass
class NFLSuperstarProfile:
    name:              str
    position:          str      # "QB","WR","TE","RB"
    play_style:        str      # "pocket_passer","mobile_qb","slot_wr","outside_wr","etc"
    defensive_focus:   float    # 0-1: how much defenses game-plan specifically for this player
    # Coverage-specific stat deltas
    vs_shadow:         dict[str, float] = field(default_factory=dict)
    vs_bracket:        dict[str, float] = field(default_factory=dict)
    vs_trail:          dict[str, float] = field(default_factory=dict)
    vs_off_coverage:   dict[str, float] = field(default_factory=dict)
    vs_high_blitz:     dict[str, float] = field(default_factory=dict)   # 35%+ blitz rate
    vs_spy:            dict[str, float] = field(default_factory=dict)   # QB spy
    vs_lb_coverage:    dict[str, float] = field(default_factory=dict)   # TE/RB vs LB
    vs_box_stack:      dict[str, float] = field(default_factory=dict)   # RB vs 8-man box


NFL_SUPERSTAR_PROFILES: dict[str, NFLSuperstarProfile] = {

    # ── Quarterbacks ────────────────────────────────────────────────────────

    "Patrick Mahomes": NFLSuperstarProfile(
        name="Patrick Mahomes",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.98,
        # Blitzing Mahomes is famously counterproductive — he thrives under pressure
        vs_high_blitz={"passing_yards": +42, "pass_tds": +0.4, "pass_attempts": +4},
        # Spy limits his scrambles but he still finds throws
        vs_spy={"passing_yards": -18, "rush_yds": -12, "pass_attempts": +3},
        vs_shadow={},  # not applicable for QBs
        vs_bracket={},
        vs_trail={},
        vs_off_coverage={"passing_yards": +25, "pass_tds": +0.3},
    ),
    "Josh Allen": NFLSuperstarProfile(
        name="Josh Allen",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.95,
        vs_high_blitz={"passing_yards": +30, "pass_tds": +0.3, "rush_yds": +15},
        vs_spy={"passing_yards": -20, "rush_yds": -18, "pass_attempts": +2},
        vs_off_coverage={"passing_yards": +22, "pass_tds": +0.25},
    ),
    "Lamar Jackson": NFLSuperstarProfile(
        name="Lamar Jackson",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.97,
        # Spy is the primary tool vs Lamar — keeps a contain defender on him
        vs_spy={"rush_yds": -28, "passing_yards": +18, "pass_attempts": +5},
        # Blitzing Lamar opens running lanes
        vs_high_blitz={"rush_yds": +22, "passing_yards": +15, "pass_tds": +0.2},
        vs_off_coverage={"rush_yds": +20, "passing_yards": +15},
    ),
    "Joe Burrow": NFLSuperstarProfile(
        name="Joe Burrow",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.90,
        # Elite pocket passer — pressure is the only real answer
        vs_high_blitz={"passing_yards": -35, "pass_tds": -0.3, "pass_attempts": -2},
        vs_spy={"passing_yards": +15},   # spy wastes a defender vs pocket QB
        vs_off_coverage={"passing_yards": +20, "pass_tds": +0.25},
    ),
    "Jalen Hurts": NFLSuperstarProfile(
        name="Jalen Hurts",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.92,
        vs_spy={"rush_yds": -22, "passing_yards": +15, "pass_attempts": +3},
        vs_high_blitz={"rush_yds": +18, "passing_yards": +10},
        vs_off_coverage={"passing_yards": +18, "rush_yds": +10},
    ),
    "Dak Prescott": NFLSuperstarProfile(
        name="Dak Prescott",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.85,
        vs_high_blitz={"passing_yards": -25, "pass_tds": -0.2},
        vs_spy={"passing_yards": +12},
        vs_off_coverage={"passing_yards": +18, "pass_tds": +0.2},
    ),
    "C.J. Stroud": NFLSuperstarProfile(
        name="C.J. Stroud",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.82,
        vs_high_blitz={"passing_yards": -22, "pass_tds": -0.2},
        vs_spy={"passing_yards": +10},
        vs_off_coverage={"passing_yards": +20, "pass_tds": +0.25},
    ),
    "Brock Purdy": NFLSuperstarProfile(
        name="Brock Purdy",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.75,
        # System QB — scheme-dependent, elite pressure disrupts him more
        vs_high_blitz={"passing_yards": -40, "pass_tds": -0.4},
        vs_spy={"passing_yards": +8},
        vs_off_coverage={"passing_yards": +15, "pass_tds": +0.2},
    ),

    # ── Wide Receivers ───────────────────────────────────────────────────────

    "Tyreek Hill": NFLSuperstarProfile(
        name="Tyreek Hill",
        position="WR",
        play_style="speed_wr",
        defensive_focus=0.95,
        # Shadow coverage limits him but speed still creates separation
        vs_shadow={"receiving_yards": -28, "receptions": -1.8},
        vs_bracket={"receiving_yards": -38, "receptions": -2.2},
        vs_trail={"receiving_yards": +15, "receptions": +0.8},
        vs_off_coverage={"receiving_yards": +35, "receptions": +1.5},
        vs_high_blitz={"receiving_yards": +20, "receptions": +1.2},  # quick screens open
    ),
    "CeeDee Lamb": NFLSuperstarProfile(
        name="CeeDee Lamb",
        position="WR",
        play_style="route_runner",
        defensive_focus=0.92,
        vs_shadow={"receiving_yards": -22, "receptions": -1.5},
        vs_bracket={"receiving_yards": -30, "receptions": -2.0},
        vs_trail={"receiving_yards": +10, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +28, "receptions": +1.2},
        vs_high_blitz={"receiving_yards": +15, "receptions": +1.0},
    ),
    "Justin Jefferson": NFLSuperstarProfile(
        name="Justin Jefferson",
        position="WR",
        play_style="route_runner",
        defensive_focus=0.93,
        vs_shadow={"receiving_yards": -20, "receptions": -1.4},
        vs_bracket={"receiving_yards": -28, "receptions": -1.8},
        vs_trail={"receiving_yards": +12, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +30, "receptions": +1.3},
        vs_high_blitz={"receiving_yards": +18, "receptions": +1.1},
    ),
    "Ja'Marr Chase": NFLSuperstarProfile(
        name="Ja'Marr Chase",
        position="WR",
        play_style="physical_wr",
        defensive_focus=0.90,
        vs_shadow={"receiving_yards": -18, "receptions": -1.3},
        vs_bracket={"receiving_yards": -26, "receptions": -1.7},
        vs_trail={"receiving_yards": +15, "receptions": +0.7},
        vs_off_coverage={"receiving_yards": +32, "receptions": +1.4},
        vs_high_blitz={"receiving_yards": +22, "receptions": +1.2},
    ),
    "Davante Adams": NFLSuperstarProfile(
        name="Davante Adams",
        position="WR",
        play_style="route_runner",
        defensive_focus=0.88,
        vs_shadow={"receiving_yards": -15, "receptions": -1.2},
        vs_bracket={"receiving_yards": -22, "receptions": -1.6},
        vs_trail={"receiving_yards": +18, "receptions": +1.0},
        vs_off_coverage={"receiving_yards": +28, "receptions": +1.3},
        vs_high_blitz={"receiving_yards": +12, "receptions": +0.8},
    ),
    "Stefon Diggs": NFLSuperstarProfile(
        name="Stefon Diggs",
        position="WR",
        play_style="slot_wr",
        defensive_focus=0.82,
        vs_shadow={"receiving_yards": -12, "receptions": -1.0},
        vs_bracket={"receiving_yards": -20, "receptions": -1.4},
        vs_trail={"receiving_yards": +12, "receptions": +0.8},
        vs_off_coverage={"receiving_yards": +22, "receptions": +1.2},
        vs_high_blitz={"receiving_yards": +18, "receptions": +1.3},  # quick slot routes
    ),
    "Amon-Ra St. Brown": NFLSuperstarProfile(
        name="Amon-Ra St. Brown",
        position="WR",
        play_style="slot_wr",
        defensive_focus=0.78,
        vs_shadow={"receiving_yards": -10, "receptions": -1.0},
        vs_bracket={"receiving_yards": -15, "receptions": -1.2},
        vs_trail={"receiving_yards": +8, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +20, "receptions": +1.5},
        vs_high_blitz={"receiving_yards": +15, "receptions": +1.4},
    ),

    # ── Tight Ends ───────────────────────────────────────────────────────────

    "Travis Kelce": NFLSuperstarProfile(
        name="Travis Kelce",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.97,
        # LBs can't cover Kelce — massive mismatch
        vs_lb_coverage={"receiving_yards": +32, "receptions": +2.0},
        vs_shadow={"receiving_yards": -15, "receptions": -1.0},
        vs_bracket={"receiving_yards": -25, "receptions": -1.5},
        vs_trail={"receiving_yards": +20, "receptions": +1.2},
        vs_off_coverage={"receiving_yards": +35, "receptions": +1.8},
        vs_high_blitz={"receiving_yards": +18, "receptions": +1.3},
    ),
    "Sam LaPorta": NFLSuperstarProfile(
        name="Sam LaPorta",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.72,
        vs_lb_coverage={"receiving_yards": +22, "receptions": +1.4},
        vs_shadow={"receiving_yards": -8, "receptions": -0.6},
        vs_bracket={"receiving_yards": -14, "receptions": -0.9},
        vs_trail={"receiving_yards": +10, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +22, "receptions": +1.2},
        vs_high_blitz={"receiving_yards": +12, "receptions": +0.9},
    ),
    "George Kittle": NFLSuperstarProfile(
        name="George Kittle",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.88,
        vs_lb_coverage={"receiving_yards": +28, "receptions": +1.6},
        vs_shadow={"receiving_yards": -12, "receptions": -0.8},
        vs_bracket={"receiving_yards": -20, "receptions": -1.2},
        vs_trail={"receiving_yards": +15, "receptions": +0.9},
        vs_off_coverage={"receiving_yards": +30, "receptions": +1.5},
        vs_high_blitz={"receiving_yards": +15, "receptions": +1.1},
    ),
    "Mark Andrews": NFLSuperstarProfile(
        name="Mark Andrews",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.85,
        vs_lb_coverage={"receiving_yards": +26, "receptions": +1.5},
        vs_shadow={"receiving_yards": -10, "receptions": -0.7},
        vs_bracket={"receiving_yards": -18, "receptions": -1.1},
        vs_trail={"receiving_yards": +14, "receptions": +0.8},
        vs_off_coverage={"receiving_yards": +28, "receptions": +1.4},
        vs_high_blitz={"receiving_yards": +14, "receptions": +1.0},
    ),
    "Dallas Goedert": NFLSuperstarProfile(
        name="Dallas Goedert",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.80,
        vs_lb_coverage={"receiving_yards": +24, "receptions": +1.4},
        vs_shadow={"receiving_yards": -8, "receptions": -0.6},
        vs_bracket={"receiving_yards": -16, "receptions": -1.0},
        vs_trail={"receiving_yards": +12, "receptions": +0.7},
        vs_off_coverage={"receiving_yards": +25, "receptions": +1.3},
        vs_high_blitz={"receiving_yards": +12, "receptions": +0.9},
    ),

    # ── Running Backs ─────────────────────────────────────────────────────────

    "Christian McCaffrey": NFLSuperstarProfile(
        name="Christian McCaffrey",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.90,
        # 8-man box stuffs the run but CMC is lethal as a receiver
        vs_box_stack={"rush_yds": -22, "receptions": +2.0, "receiving_yards": +28},
        vs_high_blitz={"receiving_yards": +18, "receptions": +1.5},
        vs_off_coverage={"rush_yds": +18, "receiving_yards": +15},
    ),
    "Derrick Henry": NFLSuperstarProfile(
        name="Derrick Henry",
        position="RB",
        play_style="power_rb",
        defensive_focus=0.88,
        # Pure power back — box stacking is the only answer
        vs_box_stack={"rush_yds": -30, "rush_attempts": -3},
        vs_high_blitz={"rush_yds": +15},   # blitz opens cutback lanes
        vs_off_coverage={"rush_yds": +25, "rush_attempts": +2},
    ),
    "Bijan Robinson": NFLSuperstarProfile(
        name="Bijan Robinson",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.82,
        vs_box_stack={"rush_yds": -18, "receptions": +1.5, "receiving_yards": +20},
        vs_high_blitz={"receiving_yards": +14, "receptions": +1.2},
        vs_off_coverage={"rush_yds": +15, "receiving_yards": +10},
    ),
    "Saquon Barkley": NFLSuperstarProfile(
        name="Saquon Barkley",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.85,
        vs_box_stack={"rush_yds": -20, "receptions": +1.6, "receiving_yards": +22},
        vs_high_blitz={"receiving_yards": +16, "receptions": +1.3},
        vs_off_coverage={"rush_yds": +20, "receiving_yards": +12},
    ),
    "Breece Hall": NFLSuperstarProfile(
        name="Breece Hall",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.75,
        vs_box_stack={"rush_yds": -15, "receptions": +1.2, "receiving_yards": +16},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.0},
        vs_off_coverage={"rush_yds": +14, "receiving_yards": +8},
    ),

    # ── Additional Quarterbacks ──────────────────────────────────────────────

    "Jordan Love": NFLSuperstarProfile(
        name="Jordan Love",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.75,
        vs_high_blitz={"passing_yards": -28, "pass_tds": -0.25},
        vs_spy={"passing_yards": +10},
        vs_off_coverage={"passing_yards": +18, "pass_tds": +0.2},
    ),
    "Sam Darnold": NFLSuperstarProfile(
        name="Sam Darnold",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.65,
        vs_high_blitz={"passing_yards": -30, "pass_tds": -0.3},
        vs_spy={"passing_yards": +8},
        vs_off_coverage={"passing_yards": +15, "pass_tds": +0.15},
    ),
    "Tua Tagovailoa": NFLSuperstarProfile(
        name="Tua Tagovailoa",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.78,
        vs_high_blitz={"passing_yards": -32, "pass_tds": -0.3},
        vs_spy={"passing_yards": +10},
        vs_off_coverage={"passing_yards": +20, "pass_tds": +0.25},
    ),
    "Kirk Cousins": NFLSuperstarProfile(
        name="Kirk Cousins",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.72,
        vs_high_blitz={"passing_yards": -22, "pass_tds": -0.2},
        vs_spy={"passing_yards": +8},
        vs_off_coverage={"passing_yards": +14, "pass_tds": +0.15},
    ),
    "Geno Smith": NFLSuperstarProfile(
        name="Geno Smith",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.65,
        vs_high_blitz={"passing_yards": -25, "pass_tds": -0.2},
        vs_spy={"passing_yards": +8},
        vs_off_coverage={"passing_yards": +14, "pass_tds": +0.15},
    ),

    # ── Additional Wide Receivers ────────────────────────────────────────────

    "Puka Nacua": NFLSuperstarProfile(
        name="Puka Nacua",
        position="WR",
        play_style="slot_wr",
        defensive_focus=0.72,
        vs_shadow={"receiving_yards": -10, "receptions": -0.9},
        vs_bracket={"receiving_yards": -14, "receptions": -1.1},
        vs_trail={"receiving_yards": +8, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +18, "receptions": +1.3},
        vs_high_blitz={"receiving_yards": +14, "receptions": +1.2},
    ),
    "Chris Olave": NFLSuperstarProfile(
        name="Chris Olave",
        position="WR",
        play_style="speed_wr",
        defensive_focus=0.72,
        vs_shadow={"receiving_yards": -14, "receptions": -1.0},
        vs_bracket={"receiving_yards": -20, "receptions": -1.4},
        vs_trail={"receiving_yards": +10, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +22, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +14, "receptions": +0.9},
    ),
    "DJ Moore": NFLSuperstarProfile(
        name="DJ Moore",
        position="WR",
        play_style="route_runner",
        defensive_focus=0.72,
        vs_shadow={"receiving_yards": -12, "receptions": -0.9},
        vs_bracket={"receiving_yards": -18, "receptions": -1.2},
        vs_trail={"receiving_yards": +10, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +22, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +12, "receptions": +0.9},
    ),
    "Mike Evans": NFLSuperstarProfile(
        name="Mike Evans",
        position="WR",
        play_style="physical_wr",
        defensive_focus=0.82,
        vs_shadow={"receiving_yards": -16, "receptions": -1.1},
        vs_bracket={"receiving_yards": -24, "receptions": -1.5},
        vs_trail={"receiving_yards": +14, "receptions": +0.7},
        vs_off_coverage={"receiving_yards": +28, "receptions": +1.2},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.7},
    ),
    "Cooper Kupp": NFLSuperstarProfile(
        name="Cooper Kupp",
        position="WR",
        play_style="slot_wr",
        defensive_focus=0.80,
        vs_shadow={"receiving_yards": -12, "receptions": -1.1},
        vs_bracket={"receiving_yards": -18, "receptions": -1.4},
        vs_trail={"receiving_yards": +10, "receptions": +0.8},
        vs_off_coverage={"receiving_yards": +24, "receptions": +1.4},
        vs_high_blitz={"receiving_yards": +16, "receptions": +1.3},
    ),
    "Brandon Aiyuk": NFLSuperstarProfile(
        name="Brandon Aiyuk",
        position="WR",
        play_style="outside_wr",
        defensive_focus=0.75,
        vs_shadow={"receiving_yards": -14, "receptions": -1.0},
        vs_bracket={"receiving_yards": -20, "receptions": -1.3},
        vs_trail={"receiving_yards": +10, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +22, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +12, "receptions": +0.8},
    ),
    "Keenan Allen": NFLSuperstarProfile(
        name="Keenan Allen",
        position="WR",
        play_style="route_runner",
        defensive_focus=0.78,
        vs_shadow={"receiving_yards": -12, "receptions": -1.0},
        vs_bracket={"receiving_yards": -18, "receptions": -1.4},
        vs_trail={"receiving_yards": +12, "receptions": +0.9},
        vs_off_coverage={"receiving_yards": +22, "receptions": +1.3},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.8},
    ),

    # ── Additional Tight Ends ────────────────────────────────────────────────

    "Evan Engram": NFLSuperstarProfile(
        name="Evan Engram",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.72,
        vs_lb_coverage={"receiving_yards": +20, "receptions": +1.3},
        vs_shadow={"receiving_yards": -7, "receptions": -0.5},
        vs_bracket={"receiving_yards": -12, "receptions": -0.8},
        vs_trail={"receiving_yards": +10, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +20, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +11, "receptions": +0.8},
    ),
    "T.J. Hockenson": NFLSuperstarProfile(
        name="T.J. Hockenson",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.72,
        vs_lb_coverage={"receiving_yards": +20, "receptions": +1.3},
        vs_shadow={"receiving_yards": -7, "receptions": -0.5},
        vs_bracket={"receiving_yards": -12, "receptions": -0.8},
        vs_trail={"receiving_yards": +9, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +19, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.7},
    ),
    "Pat Freiermuth": NFLSuperstarProfile(
        name="Pat Freiermuth",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.65,
        vs_lb_coverage={"receiving_yards": +18, "receptions": +1.2},
        vs_shadow={"receiving_yards": -6, "receptions": -0.4},
        vs_bracket={"receiving_yards": -10, "receptions": -0.7},
        vs_trail={"receiving_yards": +8, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +18, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +9, "receptions": +0.7},
    ),

    # ── Additional Running Backs ─────────────────────────────────────────────

    "Josh Jacobs": NFLSuperstarProfile(
        name="Josh Jacobs",
        position="RB",
        play_style="power_rb",
        defensive_focus=0.72,
        vs_box_stack={"rush_yds": -18, "receptions": +0.9, "receiving_yards": +12},
        vs_high_blitz={"rush_yds": +10},
        vs_off_coverage={"rush_yds": +18, "rush_attempts": +1},
    ),
    "Tony Pollard": NFLSuperstarProfile(
        name="Tony Pollard",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.68,
        vs_box_stack={"rush_yds": -14, "receptions": +1.1, "receiving_yards": +14},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.9},
        vs_off_coverage={"rush_yds": +12, "receiving_yards": +8},
    ),
    "Travis Etienne": NFLSuperstarProfile(
        name="Travis Etienne",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.70,
        vs_box_stack={"rush_yds": -14, "receptions": +1.2, "receiving_yards": +14},
        vs_high_blitz={"receiving_yards": +10, "receptions": +1.0},
        vs_off_coverage={"rush_yds": +12, "receiving_yards": +8},
    ),
    "De'Von Achane": NFLSuperstarProfile(
        name="De'Von Achane",
        position="RB",
        play_style="speed_rb",
        defensive_focus=0.72,
        # Elite speed — box stacking helps contain him but he can still rip big plays
        vs_box_stack={"rush_yds": -10, "receptions": +1.3, "receiving_yards": +16},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.1},
        vs_off_coverage={"rush_yds": +20, "rush_attempts": +2},
    ),
    "Jahmyr Gibbs": NFLSuperstarProfile(
        name="Jahmyr Gibbs",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.72,
        vs_box_stack={"rush_yds": -12, "receptions": +1.2, "receiving_yards": +14},
        vs_high_blitz={"receiving_yards": +10, "receptions": +1.0},
        vs_off_coverage={"rush_yds": +14, "receiving_yards": +9},
    ),

    # ── More QBs ─────────────────────────────────────────────────────────────

    "Trevor Lawrence": NFLSuperstarProfile(
        name="Trevor Lawrence",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.72,
        vs_high_blitz={"passing_yards": -26, "pass_tds": -0.22},
        vs_spy={"passing_yards": +10},
        vs_off_coverage={"passing_yards": +16, "pass_tds": +0.18},
    ),
    "Justin Herbert": NFLSuperstarProfile(
        name="Justin Herbert",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.80,
        vs_high_blitz={"passing_yards": -28, "pass_tds": -0.25},
        vs_spy={"passing_yards": +12},
        vs_off_coverage={"passing_yards": +20, "pass_tds": +0.22},
    ),
    "Matthew Stafford": NFLSuperstarProfile(
        name="Matthew Stafford",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.72,
        vs_high_blitz={"passing_yards": -22, "pass_tds": -0.18},
        vs_spy={"passing_yards": +8},
        vs_off_coverage={"passing_yards": +14, "pass_tds": +0.15},
    ),
    "Baker Mayfield": NFLSuperstarProfile(
        name="Baker Mayfield",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.68,
        vs_high_blitz={"passing_yards": -24, "pass_tds": -0.22},
        vs_spy={"passing_yards": +8},
        vs_off_coverage={"passing_yards": +14, "pass_tds": +0.15},
    ),
    "Anthony Richardson": NFLSuperstarProfile(
        name="Anthony Richardson",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.72,
        vs_spy={"rush_yds": -20, "passing_yards": +14, "pass_attempts": +3},
        vs_high_blitz={"rush_yds": +18, "passing_yards": +10},
        vs_off_coverage={"rush_yds": +20, "passing_yards": +12},
    ),
    "Drake Maye": NFLSuperstarProfile(
        name="Drake Maye",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.70,
        vs_spy={"rush_yds": -16, "passing_yards": +12},
        vs_high_blitz={"rush_yds": +14, "passing_yards": +10},
        vs_off_coverage={"passing_yards": +15, "rush_yds": +10},
    ),
    "Jayden Daniels": NFLSuperstarProfile(
        name="Jayden Daniels",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.75,
        vs_spy={"rush_yds": -22, "passing_yards": +16, "pass_attempts": +3},
        vs_high_blitz={"rush_yds": +20, "passing_yards": +12},
        vs_off_coverage={"rush_yds": +18, "passing_yards": +14},
    ),
    "Bo Nix": NFLSuperstarProfile(
        name="Bo Nix",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.65,
        vs_spy={"rush_yds": -14, "passing_yards": +10},
        vs_high_blitz={"passing_yards": -20, "rush_yds": +8},
        vs_off_coverage={"passing_yards": +12, "rush_yds": +8},
    ),
    "Bryce Young": NFLSuperstarProfile(
        name="Bryce Young",
        position="QB",
        play_style="mobile_qb",
        defensive_focus=0.65,
        vs_spy={"rush_yds": -12, "passing_yards": +8},
        vs_high_blitz={"passing_yards": -28, "pass_tds": -0.25},
        vs_off_coverage={"passing_yards": +12},
    ),
    "Will Levis": NFLSuperstarProfile(
        name="Will Levis",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.60,
        vs_high_blitz={"passing_yards": -28, "pass_tds": -0.25},
        vs_spy={"passing_yards": +8},
        vs_off_coverage={"passing_yards": +12, "pass_tds": +0.12},
    ),
    "Gardner Minshew": NFLSuperstarProfile(
        name="Gardner Minshew",
        position="QB",
        play_style="pocket_passer",
        defensive_focus=0.55,
        vs_high_blitz={"passing_yards": -26, "pass_tds": -0.22},
        vs_spy={"passing_yards": +7},
        vs_off_coverage={"passing_yards": +11, "pass_tds": +0.10},
    ),

    # ── More WRs ─────────────────────────────────────────────────────────────

    "Jaylen Waddle": NFLSuperstarProfile(
        name="Jaylen Waddle",
        position="WR",
        play_style="speed_wr",
        defensive_focus=0.75,
        vs_shadow={"receiving_yards": -16, "receptions": -1.1},
        vs_bracket={"receiving_yards": -22, "receptions": -1.5},
        vs_trail={"receiving_yards": +10, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +24, "receptions": +1.3},
        vs_high_blitz={"receiving_yards": +16, "receptions": +1.2},
    ),
    "DeVonta Smith": NFLSuperstarProfile(
        name="DeVonta Smith",
        position="WR",
        play_style="route_runner",
        defensive_focus=0.75,
        vs_shadow={"receiving_yards": -14, "receptions": -1.1},
        vs_bracket={"receiving_yards": -20, "receptions": -1.4},
        vs_trail={"receiving_yards": +10, "receptions": +0.7},
        vs_off_coverage={"receiving_yards": +22, "receptions": +1.2},
        vs_high_blitz={"receiving_yards": +14, "receptions": +1.0},
    ),
    "Tee Higgins": NFLSuperstarProfile(
        name="Tee Higgins",
        position="WR",
        play_style="physical_wr",
        defensive_focus=0.78,
        vs_shadow={"receiving_yards": -15, "receptions": -1.1},
        vs_bracket={"receiving_yards": -22, "receptions": -1.5},
        vs_trail={"receiving_yards": +12, "receptions": +0.7},
        vs_off_coverage={"receiving_yards": +24, "receptions": +1.2},
        vs_high_blitz={"receiving_yards": +14, "receptions": +1.0},
    ),
    "George Pickens": NFLSuperstarProfile(
        name="George Pickens",
        position="WR",
        play_style="physical_wr",
        defensive_focus=0.75,
        vs_shadow={"receiving_yards": -14, "receptions": -1.0},
        vs_bracket={"receiving_yards": -20, "receptions": -1.3},
        vs_trail={"receiving_yards": +12, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +24, "receptions": +1.2},
        vs_high_blitz={"receiving_yards": +14, "receptions": +1.0},
    ),
    "DK Metcalf": NFLSuperstarProfile(
        name="DK Metcalf",
        position="WR",
        play_style="physical_wr",
        defensive_focus=0.82,
        vs_shadow={"receiving_yards": -15, "receptions": -1.0},
        vs_bracket={"receiving_yards": -22, "receptions": -1.4},
        vs_trail={"receiving_yards": +14, "receptions": +0.7},
        vs_off_coverage={"receiving_yards": +28, "receptions": +1.3},
        vs_high_blitz={"receiving_yards": +12, "receptions": +0.8},
    ),
    "Tyler Lockett": NFLSuperstarProfile(
        name="Tyler Lockett",
        position="WR",
        play_style="route_runner",
        defensive_focus=0.68,
        vs_shadow={"receiving_yards": -10, "receptions": -0.8},
        vs_bracket={"receiving_yards": -15, "receptions": -1.1},
        vs_trail={"receiving_yards": +8, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +18, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.0},
    ),
    "Courtland Sutton": NFLSuperstarProfile(
        name="Courtland Sutton",
        position="WR",
        play_style="physical_wr",
        defensive_focus=0.70,
        vs_shadow={"receiving_yards": -12, "receptions": -0.9},
        vs_bracket={"receiving_yards": -18, "receptions": -1.2},
        vs_trail={"receiving_yards": +10, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +20, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.7},
    ),
    "Rashee Rice": NFLSuperstarProfile(
        name="Rashee Rice",
        position="WR",
        play_style="route_runner",
        defensive_focus=0.70,
        vs_shadow={"receiving_yards": -12, "receptions": -1.0},
        vs_bracket={"receiving_yards": -16, "receptions": -1.2},
        vs_trail={"receiving_yards": +8, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +18, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.0},
    ),
    "Gabe Davis": NFLSuperstarProfile(
        name="Gabe Davis",
        position="WR",
        play_style="outside_wr",
        defensive_focus=0.62,
        vs_shadow={"receiving_yards": -12, "receptions": -0.8},
        vs_bracket={"receiving_yards": -16, "receptions": -1.0},
        vs_trail={"receiving_yards": +8, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +18, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.7},
    ),
    "Diontae Johnson": NFLSuperstarProfile(
        name="Diontae Johnson",
        position="WR",
        play_style="slot_wr",
        defensive_focus=0.65,
        vs_shadow={"receiving_yards": -10, "receptions": -0.9},
        vs_bracket={"receiving_yards": -14, "receptions": -1.1},
        vs_trail={"receiving_yards": +7, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +16, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.1},
    ),
    "Terry McLaurin": NFLSuperstarProfile(
        name="Terry McLaurin",
        position="WR",
        play_style="outside_wr",
        defensive_focus=0.72,
        vs_shadow={"receiving_yards": -14, "receptions": -1.0},
        vs_bracket={"receiving_yards": -18, "receptions": -1.3},
        vs_trail={"receiving_yards": +10, "receptions": +0.6},
        vs_off_coverage={"receiving_yards": +22, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +12, "receptions": +0.9},
    ),
    "Tank Dell": NFLSuperstarProfile(
        name="Tank Dell",
        position="WR",
        play_style="speed_wr",
        defensive_focus=0.65,
        vs_shadow={"receiving_yards": -12, "receptions": -0.9},
        vs_bracket={"receiving_yards": -16, "receptions": -1.1},
        vs_trail={"receiving_yards": +8, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +18, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.0},
    ),
    "Khalil Shakir": NFLSuperstarProfile(
        name="Khalil Shakir",
        position="WR",
        play_style="slot_wr",
        defensive_focus=0.60,
        vs_shadow={"receiving_yards": -8, "receptions": -0.7},
        vs_bracket={"receiving_yards": -12, "receptions": -0.9},
        vs_trail={"receiving_yards": +6, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +14, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +10, "receptions": +1.0},
    ),
    "Zay Flowers": NFLSuperstarProfile(
        name="Zay Flowers",
        position="WR",
        play_style="slot_wr",
        defensive_focus=0.65,
        vs_shadow={"receiving_yards": -10, "receptions": -0.8},
        vs_bracket={"receiving_yards": -14, "receptions": -1.0},
        vs_trail={"receiving_yards": +8, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +16, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.0},
    ),
    "Rome Odunze": NFLSuperstarProfile(
        name="Rome Odunze",
        position="WR",
        play_style="outside_wr",
        defensive_focus=0.65,
        vs_shadow={"receiving_yards": -10, "receptions": -0.8},
        vs_bracket={"receiving_yards": -14, "receptions": -1.0},
        vs_trail={"receiving_yards": +8, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +16, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.8},
    ),
    "Ladd McConkey": NFLSuperstarProfile(
        name="Ladd McConkey",
        position="WR",
        play_style="slot_wr",
        defensive_focus=0.62,
        vs_shadow={"receiving_yards": -8, "receptions": -0.7},
        vs_bracket={"receiving_yards": -12, "receptions": -0.9},
        vs_trail={"receiving_yards": +6, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +14, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.9},
    ),
    "Brian Thomas Jr.": NFLSuperstarProfile(
        name="Brian Thomas Jr.",
        position="WR",
        play_style="speed_wr",
        defensive_focus=0.68,
        vs_shadow={"receiving_yards": -12, "receptions": -0.9},
        vs_bracket={"receiving_yards": -16, "receptions": -1.1},
        vs_trail={"receiving_yards": +8, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +18, "receptions": +1.1},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.0},
    ),
    "Xavier Worthy": NFLSuperstarProfile(
        name="Xavier Worthy",
        position="WR",
        play_style="speed_wr",
        defensive_focus=0.65,
        vs_shadow={"receiving_yards": -10, "receptions": -0.8},
        vs_bracket={"receiving_yards": -14, "receptions": -1.0},
        vs_trail={"receiving_yards": +7, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +16, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +12, "receptions": +1.0},
    ),

    # ── More TEs ─────────────────────────────────────────────────────────────

    "Kyle Pitts": NFLSuperstarProfile(
        name="Kyle Pitts",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.78,
        vs_lb_coverage={"receiving_yards": +26, "receptions": +1.6},
        vs_shadow={"receiving_yards": -10, "receptions": -0.7},
        vs_bracket={"receiving_yards": -16, "receptions": -1.0},
        vs_trail={"receiving_yards": +12, "receptions": +0.7},
        vs_off_coverage={"receiving_yards": +26, "receptions": +1.4},
        vs_high_blitz={"receiving_yards": +12, "receptions": +0.9},
    ),
    "David Njoku": NFLSuperstarProfile(
        name="David Njoku",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.70,
        vs_lb_coverage={"receiving_yards": +20, "receptions": +1.2},
        vs_shadow={"receiving_yards": -7, "receptions": -0.5},
        vs_bracket={"receiving_yards": -11, "receptions": -0.7},
        vs_trail={"receiving_yards": +8, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +18, "receptions": +1.0},
        vs_high_blitz={"receiving_yards": +9, "receptions": +0.7},
    ),
    "Brock Wright": NFLSuperstarProfile(
        name="Brock Wright",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.55,
        vs_lb_coverage={"receiving_yards": +12, "receptions": +0.8},
        vs_shadow={"receiving_yards": -4, "receptions": -0.3},
        vs_bracket={"receiving_yards": -7, "receptions": -0.5},
        vs_trail={"receiving_yards": +5, "receptions": +0.3},
        vs_off_coverage={"receiving_yards": +12, "receptions": +0.7},
        vs_high_blitz={"receiving_yards": +6, "receptions": +0.5},
    ),
    "Taysom Hill": NFLSuperstarProfile(
        name="Taysom Hill",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.60,
        vs_lb_coverage={"receiving_yards": +12, "receptions": +0.7, "rush_yds": +8},
        vs_shadow={"receiving_yards": -5, "receptions": -0.4},
        vs_bracket={"receiving_yards": -8, "receptions": -0.6},
        vs_trail={"receiving_yards": +6, "receptions": +0.4},
        vs_off_coverage={"receiving_yards": +14, "receptions": +0.8, "rush_yds": +10},
        vs_high_blitz={"receiving_yards": +8, "receptions": +0.6},
    ),
    "Cade Otton": NFLSuperstarProfile(
        name="Cade Otton",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.60,
        vs_lb_coverage={"receiving_yards": +16, "receptions": +1.0},
        vs_shadow={"receiving_yards": -5, "receptions": -0.4},
        vs_bracket={"receiving_yards": -9, "receptions": -0.6},
        vs_trail={"receiving_yards": +7, "receptions": +0.5},
        vs_off_coverage={"receiving_yards": +15, "receptions": +0.9},
        vs_high_blitz={"receiving_yards": +8, "receptions": +0.7},
    ),
    "Tucker Kraft": NFLSuperstarProfile(
        name="Tucker Kraft",
        position="TE",
        play_style="receiving_te",
        defensive_focus=0.58,
        vs_lb_coverage={"receiving_yards": +14, "receptions": +0.9},
        vs_shadow={"receiving_yards": -4, "receptions": -0.3},
        vs_bracket={"receiving_yards": -8, "receptions": -0.5},
        vs_trail={"receiving_yards": +6, "receptions": +0.4},
        vs_off_coverage={"receiving_yards": +13, "receptions": +0.8},
        vs_high_blitz={"receiving_yards": +7, "receptions": +0.6},
    ),

    # ── More RBs ─────────────────────────────────────────────────────────────

    "Alvin Kamara": NFLSuperstarProfile(
        name="Alvin Kamara",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.80,
        vs_box_stack={"rush_yds": -16, "receptions": +1.6, "receiving_yards": +20},
        vs_high_blitz={"receiving_yards": +14, "receptions": +1.3},
        vs_off_coverage={"rush_yds": +15, "receiving_yards": +10},
    ),
    "James Cook": NFLSuperstarProfile(
        name="James Cook",
        position="RB",
        play_style="speed_rb",
        defensive_focus=0.70,
        vs_box_stack={"rush_yds": -12, "receptions": +1.1, "receiving_yards": +13},
        vs_high_blitz={"receiving_yards": +10, "receptions": +0.9},
        vs_off_coverage={"rush_yds": +16, "rush_attempts": +1},
    ),
    "D'Andre Swift": NFLSuperstarProfile(
        name="D'Andre Swift",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.68,
        vs_box_stack={"rush_yds": -12, "receptions": +1.1, "receiving_yards": +13},
        vs_high_blitz={"receiving_yards": +9, "receptions": +0.9},
        vs_off_coverage={"rush_yds": +12, "receiving_yards": +7},
    ),
    "Rhamondre Stevenson": NFLSuperstarProfile(
        name="Rhamondre Stevenson",
        position="RB",
        play_style="power_rb",
        defensive_focus=0.62,
        vs_box_stack={"rush_yds": -14, "receptions": +0.8, "receiving_yards": +9},
        vs_high_blitz={"rush_yds": +8},
        vs_off_coverage={"rush_yds": +14, "rush_attempts": +1},
    ),
    "Kareem Hunt": NFLSuperstarProfile(
        name="Kareem Hunt",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.60,
        vs_box_stack={"rush_yds": -12, "receptions": +0.9, "receiving_yards": +11},
        vs_high_blitz={"receiving_yards": +8, "receptions": +0.8},
        vs_off_coverage={"rush_yds": +12, "receiving_yards": +6},
    ),
    "Zack Moss": NFLSuperstarProfile(
        name="Zack Moss",
        position="RB",
        play_style="power_rb",
        defensive_focus=0.58,
        vs_box_stack={"rush_yds": -13, "receptions": +0.7, "receiving_yards": +8},
        vs_high_blitz={"rush_yds": +7},
        vs_off_coverage={"rush_yds": +13, "rush_attempts": +1},
    ),
    "Kyren Williams": NFLSuperstarProfile(
        name="Kyren Williams",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.68,
        vs_box_stack={"rush_yds": -13, "receptions": +1.0, "receiving_yards": +12},
        vs_high_blitz={"receiving_yards": +9, "receptions": +0.9},
        vs_off_coverage={"rush_yds": +13, "receiving_yards": +8},
    ),
    "Rachaad White": NFLSuperstarProfile(
        name="Rachaad White",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.60,
        vs_box_stack={"rush_yds": -10, "receptions": +1.1, "receiving_yards": +12},
        vs_high_blitz={"receiving_yards": +9, "receptions": +0.9},
        vs_off_coverage={"rush_yds": +10, "receiving_yards": +7},
    ),
    "Aaron Jones": NFLSuperstarProfile(
        name="Aaron Jones",
        position="RB",
        play_style="all_purpose",
        defensive_focus=0.65,
        vs_box_stack={"rush_yds": -12, "receptions": +1.1, "receiving_yards": +13},
        vs_high_blitz={"receiving_yards": +9, "receptions": +0.9},
        vs_off_coverage={"rush_yds": +12, "receiving_yards": +7},
    ),
    "Isiah Pacheco": NFLSuperstarProfile(
        name="Isiah Pacheco",
        position="RB",
        play_style="power_rb",
        defensive_focus=0.65,
        vs_box_stack={"rush_yds": -16, "rush_attempts": -2, "receiving_yards": +8},
        vs_high_blitz={"rush_yds": +10},
        vs_off_coverage={"rush_yds": +16, "rush_attempts": +2},
    ),
}


# ── Core adjustment function ───────────────────────────────────────────────────

@dataclass
class NFLPropAdjustment:
    player:           str
    opponent:         str
    coverage_applied: str
    blitz_factor:     bool
    spy_factor:       bool
    box_stack:        bool
    adjustments:      dict[str, float]
    rationale:        list[str]


def get_nfl_prop_adjustment(player_name: str, opponent: str) -> NFLPropAdjustment:
    """
    Given an NFL player and their opponent, returns stat adjustments
    based on the opponent's defensive scheme and known tendencies.
    """
    defense = get_nfl_defense(opponent)
    star    = NFL_SUPERSTAR_PROFILES.get(player_name)

    adjustments: dict[str, float] = {}
    rationale:   list[str]        = []
    coverage_applied = defense.vs_elite_wr
    blitz_factor = defense.blitz_rate >= 0.35
    spy_factor   = False
    box_stack    = False

    rationale.append(
        f"{opponent} defense: {defense.primary_shell.upper()} — "
        f"man {defense.man_frequency:.0%} / zone {defense.zone_frequency:.0%} — "
        f"blitz rate {defense.blitz_rate:.0%} — "
        f"pass rush: {defense.pass_rush_grade}"
    )

    if not star:
        return NFLPropAdjustment(
            player=player_name, opponent=opponent,
            coverage_applied=coverage_applied,
            blitz_factor=blitz_factor, spy_factor=False, box_stack=False,
            adjustments={}, rationale=rationale,
        )

    rationale.append(
        f"Coverage on {player_name} ({star.position}, {star.play_style}): "
        f"{defense.vs_elite_wr} — shadow CB: {defense.uses_shadow_cb}"
    )

    # QB adjustments
    if star.position == "QB":
        spy_factor = defense.spies_mobile_qb and star.play_style == "mobile_qb"
        if spy_factor:
            adjustments = dict(star.vs_spy)
            rationale.append(f"⚠ Spy defender used on {player_name} — rush yards limited, more pass attempts")
        elif blitz_factor:
            adjustments = dict(star.vs_high_blitz)
            rationale.append(
                f"High blitz rate ({defense.blitz_rate:.0%}) — "
                f"{'helps Mahomes/Allen' if star.name in ('Patrick Mahomes','Josh Allen') else 'hurts pocket passer'}"
            )
        else:
            adjustments = dict(star.vs_off_coverage)

    # WR adjustments
    elif star.position == "WR":
        if defense.uses_shadow_cb and star.defensive_focus >= 0.85:
            adjustments = dict(star.vs_shadow)
            coverage_applied = "shadow"
            rationale.append(f"Elite CB shadows {player_name} everywhere — receiving line moves down")
        elif defense.vs_elite_wr == "bracket":
            adjustments = dict(star.vs_bracket)
            coverage_applied = "bracket"
            rationale.append(f"Bracket coverage on {player_name} — safety help over top")
        elif defense.vs_elite_wr == "trail":
            adjustments = dict(star.vs_trail)
            coverage_applied = "trail"
        elif defense.vs_elite_wr == "off":
            adjustments = dict(star.vs_off_coverage)
            coverage_applied = "off"
            rationale.append(f"Off coverage — {player_name} gets free releases, cushion all day")
        if blitz_factor:
            # Blitz opens quick routes / screens for WRs
            for k, v in star.vs_high_blitz.items():
                adjustments[k] = adjustments.get(k, 0) + v * 0.4
            rationale.append("High blitz adds short-route / screen targets")

    # TE adjustments
    elif star.position == "TE":
        if defense.te_covered_by == "lb":
            adjustments = dict(star.vs_lb_coverage)
            coverage_applied = "lb_mismatch"
            rationale.append(
                f"⚠ LB assigned to cover {player_name} — massive mismatch, "
                f"receiving yards OVER likely"
            )
        elif defense.vs_elite_wr == "bracket":
            adjustments = dict(star.vs_bracket)
            coverage_applied = "bracket"
        elif defense.vs_elite_wr == "shadow":
            adjustments = dict(star.vs_shadow)
            coverage_applied = "shadow"
        else:
            adjustments = dict(star.vs_trail)
        if blitz_factor:
            for k, v in star.vs_high_blitz.items():
                adjustments[k] = adjustments.get(k, 0) + v * 0.4

    # RB adjustments
    elif star.position == "RB":
        box_stack = defense.avg_box_count >= 6.6
        if box_stack:
            adjustments = dict(star.vs_box_stack)
            coverage_applied = "box_stack"
            rationale.append(
                f"Heavy box ({defense.avg_box_count:.1f} defenders) — "
                f"rush yards limited but check-downs and screens open up"
            )
        elif blitz_factor:
            for k, v in star.vs_high_blitz.items():
                adjustments[k] = adjustments.get(k, 0) + v
        else:
            adjustments = dict(star.vs_off_coverage)

    # Log individual stat adjustments
    for stat, adj in adjustments.items():
        if adj != 0.0:
            rationale.append(
                f"  → {stat}: {adj:+.0f} yds/rec/att ({'+' if adj > 0 else ''}"
                f"{'LB mismatch' if coverage_applied == 'lb_mismatch' else coverage_applied})"
            )

    return NFLPropAdjustment(
        player=player_name, opponent=opponent,
        coverage_applied=coverage_applied,
        blitz_factor=blitz_factor,
        spy_factor=spy_factor,
        box_stack=box_stack,
        adjustments=adjustments,
        rationale=rationale,
    )


def apply_nfl_adjustment(prop_type: str, adj: NFLPropAdjustment) -> tuple[float, list[str]]:
    """
    Maps a prop_type string to the right adjustment delta.
    Returns (delta_to_add_to_adj_avg, extra_rationale).
    """
    clean = prop_type.replace(" ", "_").lower()
    delta = 0.0

    mapping = {
        "passing_yards":    ["passing_yards", "pass_yds", "passing yds"],
        "pass_attempts":    ["pass_attempts", "attempts"],
        "pass_tds":         ["pass_tds", "passing_tds", "touchdowns"],
        "rushing_yards":    ["rush_yds", "rushing_yards", "rushing yds"],
        "rush_attempts":    ["rush_attempts"],
        "receiving_yards":  ["receiving_yards", "reception_yds", "rec yds"],
        "receptions":       ["receptions", "rec"],
    }

    for canonical, aliases in mapping.items():
        if any(a in clean for a in aliases):
            delta = adj.adjustments.get(canonical, 0.0)
            break

    notes = []
    if delta != 0.0:
        notes.append(
            f"NFL scheme adj ({adj.coverage_applied}): {delta:+.0f} to projected {prop_type}"
        )
        if adj.spy_factor:
            notes.append("Mobile QB spy reduces scramble yards, adds pass volume")
        if adj.box_stack:
            notes.append("Heavy box: rush yards down, receiving role expands")
        if adj.blitz_factor and "receiving" in clean:
            notes.append("High blitz creates quick-game targets for this player")

    return delta, notes
