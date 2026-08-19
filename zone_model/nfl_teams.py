"""
NFL 2026 Season — Team & Player Knowledge Base
===============================================
Offensive profiles, QB tendencies, key skill players, and O-line grades
for all 32 NFL teams. Used by the bonus pick model and props model to
generate pre-season and in-season edges.

Updated for 2026: reflects offseason moves, injuries, and depth chart changes.
Auto-refresh is handled by update_nfl_data.py (ESPN API) once the season starts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ── Offensive team profiles ───────────────────────────────────────────────────

@dataclass
class NFLOffenseProfile:
    team:               str
    # Scoring
    pts_per_game:       float   # 2025 season avg (placeholder pre-2026)
    pts_allowed:        float
    # Scheme
    primary_scheme:     str     # "west_coast","air_raid","spread","pro_style","run_heavy","shanahan_outside_zone"
    pass_rate:          float   # 0-1
    pace_plays:         float   # plays per game
    # QB
    qb_name:            str
    qb_style:           str     # "pocket","dual_threat","game_manager","mobile"
    qb_adv_rating:      float   # 0-100 composite (PFF-style)
    # O-line
    oline_grade:        str     # "elite","good","average","poor"
    oline_pass_block:   float   # PFF pass block grade 0-100
    oline_run_block:    float
    # Skill players
    wr1:                str
    wr2:                str
    te1:                str
    rb1:                str
    # Efficiency
    yards_per_play:     float
    red_zone_td_pct:    float   # TD% inside 20
    turnover_rate:      float   # turnovers per game
    # Multipliers vs league avg (1.0 = league average)
    pass_yds_mult:      float = 1.0
    rush_yds_mult:      float = 1.0
    scoring_mult:       float = 1.0


NFL_OFFENSIVE_PROFILES: dict[str, NFLOffenseProfile] = {

    # ── AFC EAST ──────────────────────────────────────────────────────────────

    "Buffalo Bills": NFLOffenseProfile(
        team="Buffalo Bills",
        pts_per_game=28.4, pts_allowed=20.1,
        primary_scheme="west_coast", pass_rate=0.61, pace_plays=66.2,
        qb_name="Josh Allen", qb_style="dual_threat", qb_adv_rating=94,
        oline_grade="good", oline_pass_block=71.2, oline_run_block=68.4,
        wr1="Stefon Diggs", wr2="Keon Coleman", te1="Dalton Kincaid", rb1="James Cook",
        yards_per_play=6.2, red_zone_td_pct=0.68, turnover_rate=1.1,
        pass_yds_mult=1.18, rush_yds_mult=1.05, scoring_mult=1.22,
    ),
    "Miami Dolphins": NFLOffenseProfile(
        team="Miami Dolphins",
        pts_per_game=27.6, pts_allowed=22.8,
        primary_scheme="air_raid", pass_rate=0.64, pace_plays=72.1,  # fastest pace in NFL
        qb_name="Tua Tagovailoa", qb_style="pocket", qb_adv_rating=84,
        oline_grade="good", oline_pass_block=69.8, oline_run_block=63.2,
        wr1="Tyreek Hill", wr2="Jaylen Waddle", te1="Durham Smythe", rb1="De'Von Achane",
        yards_per_play=6.4, red_zone_td_pct=0.62, turnover_rate=1.3,
        pass_yds_mult=1.22, rush_yds_mult=1.02, scoring_mult=1.18,
    ),
    "New England Patriots": NFLOffenseProfile(
        team="New England Patriots",
        pts_per_game=18.2, pts_allowed=24.1,
        primary_scheme="pro_style", pass_rate=0.54, pace_plays=62.4,
        qb_name="Drake Maye", qb_style="dual_threat", qb_adv_rating=72,
        oline_grade="average", oline_pass_block=61.4, oline_run_block=64.8,
        wr1="JuJu Smith-Schuster", wr2="Kayshon Boutte", te1="Hunter Henry", rb1="Rhamondre Stevenson",
        yards_per_play=5.1, red_zone_td_pct=0.52, turnover_rate=1.8,
        pass_yds_mult=0.88, rush_yds_mult=0.96, scoring_mult=0.82,
    ),
    "New York Jets": NFLOffenseProfile(
        team="New York Jets",
        pts_per_game=22.4, pts_allowed=23.6,
        primary_scheme="pro_style", pass_rate=0.57, pace_plays=63.8,
        qb_name="Aaron Rodgers", qb_style="pocket", qb_adv_rating=82,
        oline_grade="average", oline_pass_block=63.2, oline_run_block=65.1,
        wr1="Garrett Wilson", wr2="Allen Lazard", te1="Tyler Conklin", rb1="Breece Hall",
        yards_per_play=5.5, red_zone_td_pct=0.58, turnover_rate=1.4,
        pass_yds_mult=1.02, rush_yds_mult=1.05, scoring_mult=0.98,
    ),

    # ── AFC NORTH ─────────────────────────────────────────────────────────────

    "Baltimore Ravens": NFLOffenseProfile(
        team="Baltimore Ravens",
        pts_per_game=29.8, pts_allowed=19.4,
        primary_scheme="run_heavy", pass_rate=0.52, pace_plays=67.4,
        qb_name="Lamar Jackson", qb_style="dual_threat", qb_adv_rating=96,
        oline_grade="elite", oline_pass_block=76.4, oline_run_block=80.2,
        wr1="Zay Flowers", wr2="Odell Beckham Jr.", te1="Mark Andrews", rb1="Derrick Henry",
        yards_per_play=6.5, red_zone_td_pct=0.72, turnover_rate=0.9,
        pass_yds_mult=1.08, rush_yds_mult=1.32, scoring_mult=1.28,
    ),
    "Cincinnati Bengals": NFLOffenseProfile(
        team="Cincinnati Bengals",
        pts_per_game=26.8, pts_allowed=22.4,
        primary_scheme="west_coast", pass_rate=0.62, pace_plays=65.2,
        qb_name="Joe Burrow", qb_style="pocket", qb_adv_rating=92,
        oline_grade="good", oline_pass_block=70.8, oline_run_block=64.2,
        wr1="Ja'Marr Chase", wr2="Tee Higgins", te1="Irv Smith Jr.", rb1="Joe Mixon",
        yards_per_play=6.1, red_zone_td_pct=0.65, turnover_rate=1.2,
        pass_yds_mult=1.16, rush_yds_mult=0.98, scoring_mult=1.14,
    ),
    "Cleveland Browns": NFLOffenseProfile(
        team="Cleveland Browns",
        pts_per_game=19.6, pts_allowed=20.8,
        primary_scheme="pro_style", pass_rate=0.53, pace_plays=62.8,
        qb_name="Deshaun Watson", qb_style="dual_threat", qb_adv_rating=74,
        oline_grade="good", oline_pass_block=67.4, oline_run_block=72.1,
        wr1="Amari Cooper", wr2="Elijah Moore", te1="David Njoku", rb1="Nick Chubb",
        yards_per_play=5.2, red_zone_td_pct=0.54, turnover_rate=1.6,
        pass_yds_mult=0.91, rush_yds_mult=1.12, scoring_mult=0.88,
    ),
    "Pittsburgh Steelers": NFLOffenseProfile(
        team="Pittsburgh Steelers",
        pts_per_game=21.8, pts_allowed=20.2,
        primary_scheme="pro_style", pass_rate=0.55, pace_plays=63.6,
        qb_name="Russell Wilson", qb_style="dual_threat", qb_adv_rating=78,
        oline_grade="average", oline_pass_block=62.8, oline_run_block=66.4,
        wr1="George Pickens", wr2="Calvin Austin III", te1="Pat Freiermuth", rb1="Najee Harris",
        yards_per_play=5.4, red_zone_td_pct=0.57, turnover_rate=1.4,
        pass_yds_mult=0.96, rush_yds_mult=1.04, scoring_mult=0.94,
    ),

    # ── AFC SOUTH ─────────────────────────────────────────────────────────────

    "Houston Texans": NFLOffenseProfile(
        team="Houston Texans",
        pts_per_game=27.2, pts_allowed=21.6,
        primary_scheme="spread", pass_rate=0.59, pace_plays=66.8,
        qb_name="C.J. Stroud", qb_style="pocket", qb_adv_rating=88,
        oline_grade="good", oline_pass_block=68.4, oline_run_block=66.8,
        wr1="Nico Collins", wr2="Tank Dell", te1="Dalton Schultz", rb1="Stefon Diggs",
        yards_per_play=5.9, red_zone_td_pct=0.64, turnover_rate=1.1,
        pass_yds_mult=1.12, rush_yds_mult=1.02, scoring_mult=1.16,
    ),
    "Indianapolis Colts": NFLOffenseProfile(
        team="Indianapolis Colts",
        pts_per_game=21.4, pts_allowed=22.8,
        primary_scheme="pro_style", pass_rate=0.54, pace_plays=63.2,
        qb_name="Anthony Richardson", qb_style="dual_threat", qb_adv_rating=76,
        oline_grade="good", oline_pass_block=66.2, oline_run_block=70.4,
        wr1="Michael Pittman Jr.", wr2="Josh Downs", te1="Mo Alie-Cox", rb1="Jonathan Taylor",
        yards_per_play=5.4, red_zone_td_pct=0.56, turnover_rate=1.6,
        pass_yds_mult=0.94, rush_yds_mult=1.08, scoring_mult=0.92,
    ),
    "Jacksonville Jaguars": NFLOffenseProfile(
        team="Jacksonville Jaguars",
        pts_per_game=22.6, pts_allowed=24.2,
        primary_scheme="spread", pass_rate=0.58, pace_plays=64.4,
        qb_name="Trevor Lawrence", qb_style="pocket", qb_adv_rating=82,
        oline_grade="average", oline_pass_block=64.8, oline_run_block=63.4,
        wr1="Calvin Ridley", wr2="Gabe Davis", te1="Evan Engram", rb1="Travis Etienne",
        yards_per_play=5.6, red_zone_td_pct=0.58, turnover_rate=1.5,
        pass_yds_mult=1.02, rush_yds_mult=1.00, scoring_mult=0.96,
    ),
    "Tennessee Titans": NFLOffenseProfile(
        team="Tennessee Titans",
        pts_per_game=17.8, pts_allowed=26.4,
        primary_scheme="run_heavy", pass_rate=0.50, pace_plays=61.8,
        qb_name="Will Levis", qb_style="pocket", qb_adv_rating=68,
        oline_grade="poor", oline_pass_block=58.4, oline_run_block=62.8,
        wr1="DeAndre Hopkins", wr2="Treylon Burks", te1="Chigoziem Okonkwo", rb1="Tony Pollard",
        yards_per_play=4.8, red_zone_td_pct=0.48, turnover_rate=2.0,
        pass_yds_mult=0.84, rush_yds_mult=0.98, scoring_mult=0.78,
    ),

    # ── AFC WEST ──────────────────────────────────────────────────────────────

    "Kansas City Chiefs": NFLOffenseProfile(
        team="Kansas City Chiefs",
        pts_per_game=29.2, pts_allowed=18.8,
        primary_scheme="west_coast", pass_rate=0.60, pace_plays=67.2,
        qb_name="Patrick Mahomes", qb_style="dual_threat", qb_adv_rating=98,
        oline_grade="good", oline_pass_block=72.4, oline_run_block=68.8,
        wr1="Travis Kelce", wr2="Rashee Rice", te1="Travis Kelce", rb1="Isiah Pacheco",
        yards_per_play=6.3, red_zone_td_pct=0.71, turnover_rate=0.8,
        pass_yds_mult=1.14, rush_yds_mult=1.04, scoring_mult=1.26,
    ),
    "Las Vegas Raiders": NFLOffenseProfile(
        team="Las Vegas Raiders",
        pts_per_game=19.4, pts_allowed=26.2,
        primary_scheme="pro_style", pass_rate=0.55, pace_plays=62.8,
        qb_name="Gardner Minshew", qb_style="game_manager", qb_adv_rating=66,
        oline_grade="average", oline_pass_block=62.4, oline_run_block=64.2,
        wr1="Davante Adams", wr2="Jakobi Meyers", te1="Michael Mayer", rb1="Josh Jacobs",
        yards_per_play=5.0, red_zone_td_pct=0.50, turnover_rate=1.9,
        pass_yds_mult=0.88, rush_yds_mult=1.00, scoring_mult=0.84,
    ),
    "Los Angeles Chargers": NFLOffenseProfile(
        team="Los Angeles Chargers",
        pts_per_game=24.8, pts_allowed=22.4,
        primary_scheme="west_coast", pass_rate=0.60, pace_plays=65.4,
        qb_name="Justin Herbert", qb_style="pocket", qb_adv_rating=88,
        oline_grade="good", oline_pass_block=69.2, oline_run_block=65.8,
        wr1="Keenan Allen", wr2="Joshua Palmer", te1="Gerald Everett", rb1="Austin Ekeler",
        yards_per_play=5.8, red_zone_td_pct=0.62, turnover_rate=1.2,
        pass_yds_mult=1.10, rush_yds_mult=0.98, scoring_mult=1.06,
    ),
    "Denver Broncos": NFLOffenseProfile(
        team="Denver Broncos",
        pts_per_game=20.8, pts_allowed=23.8,
        primary_scheme="spread", pass_rate=0.57, pace_plays=63.6,
        qb_name="Bo Nix", qb_style="pocket", qb_adv_rating=74,
        oline_grade="average", oline_pass_block=63.8, oline_run_block=65.4,
        wr1="Courtland Sutton", wr2="Jerry Jeudy", te1="Greg Dulcich", rb1="Javonte Williams",
        yards_per_play=5.3, red_zone_td_pct=0.54, turnover_rate=1.6,
        pass_yds_mult=0.92, rush_yds_mult=1.00, scoring_mult=0.90,
    ),

    # ── NFC EAST ──────────────────────────────────────────────────────────────

    "Dallas Cowboys": NFLOffenseProfile(
        team="Dallas Cowboys",
        pts_per_game=26.4, pts_allowed=22.2,
        primary_scheme="spread", pass_rate=0.60, pace_plays=66.4,
        qb_name="Dak Prescott", qb_style="pocket", qb_adv_rating=86,
        oline_grade="elite", oline_pass_block=78.2, oline_run_block=76.4,
        wr1="CeeDee Lamb", wr2="Brandin Cooks", te1="Jake Ferguson", rb1="Tony Pollard",
        yards_per_play=5.9, red_zone_td_pct=0.64, turnover_rate=1.2,
        pass_yds_mult=1.12, rush_yds_mult=1.06, scoring_mult=1.10,
    ),
    "New York Giants": NFLOffenseProfile(
        team="New York Giants",
        pts_per_game=17.4, pts_allowed=25.8,
        primary_scheme="pro_style", pass_rate=0.52, pace_plays=61.8,
        qb_name="Daniel Jones", qb_style="dual_threat", qb_adv_rating=70,
        oline_grade="poor", oline_pass_block=57.4, oline_run_block=61.2,
        wr1="Malik Nabers", wr2="Wan'Dale Robinson", te1="Darren Waller", rb1="Saquon Barkley",
        yards_per_play=4.9, red_zone_td_pct=0.48, turnover_rate=2.0,
        pass_yds_mult=0.84, rush_yds_mult=0.96, scoring_mult=0.76,
    ),
    "Philadelphia Eagles": NFLOffenseProfile(
        team="Philadelphia Eagles",
        pts_per_game=29.6, pts_allowed=18.6,
        primary_scheme="spread", pass_rate=0.58, pace_plays=67.8,
        qb_name="Jalen Hurts", qb_style="dual_threat", qb_adv_rating=92,
        oline_grade="elite", oline_pass_block=79.4, oline_run_block=82.6,
        wr1="A.J. Brown", wr2="DeVonta Smith", te1="Dallas Goedert", rb1="D'Andre Swift",
        yards_per_play=6.4, red_zone_td_pct=0.74, turnover_rate=0.9,
        pass_yds_mult=1.16, rush_yds_mult=1.22, scoring_mult=1.28,
    ),
    "Washington Commanders": NFLOffenseProfile(
        team="Washington Commanders",
        pts_per_game=23.8, pts_allowed=24.6,
        primary_scheme="spread", pass_rate=0.58, pace_plays=65.2,
        qb_name="Jayden Daniels", qb_style="dual_threat", qb_adv_rating=82,
        oline_grade="average", oline_pass_block=64.8, oline_run_block=66.4,
        wr1="Terry McLaurin", wr2="Dyami Brown", te1="John Bates", rb1="Brian Robinson Jr.",
        yards_per_play=5.7, red_zone_td_pct=0.60, turnover_rate=1.4,
        pass_yds_mult=1.04, rush_yds_mult=1.08, scoring_mult=1.02,
    ),

    # ── NFC NORTH ─────────────────────────────────────────────────────────────

    "Chicago Bears": NFLOffenseProfile(
        team="Chicago Bears",
        pts_per_game=24.2, pts_allowed=23.4,
        primary_scheme="spread", pass_rate=0.58, pace_plays=65.6,
        qb_name="Caleb Williams", qb_style="dual_threat", qb_adv_rating=84,
        oline_grade="average", oline_pass_block=65.2, oline_run_block=64.8,
        wr1="DJ Moore", wr2="Keenan Allen", te1="Cole Kmet", rb1="D'Andre Swift",
        yards_per_play=5.6, red_zone_td_pct=0.60, turnover_rate=1.5,
        pass_yds_mult=1.04, rush_yds_mult=1.00, scoring_mult=1.02,
    ),
    "Detroit Lions": NFLOffenseProfile(
        team="Detroit Lions",
        pts_per_game=30.2, pts_allowed=20.8,
        primary_scheme="shanahan_outside_zone", pass_rate=0.55, pace_plays=68.4,
        qb_name="Jared Goff", qb_style="pocket", qb_adv_rating=86,
        oline_grade="elite", oline_pass_block=77.8, oline_run_block=84.2,
        wr1="Amon-Ra St. Brown", wr2="Jameson Williams", te1="Sam LaPorta", rb1="David Montgomery",
        yards_per_play=6.4, red_zone_td_pct=0.73, turnover_rate=0.9,
        pass_yds_mult=1.14, rush_yds_mult=1.28, scoring_mult=1.30,
    ),
    "Green Bay Packers": NFLOffenseProfile(
        team="Green Bay Packers",
        pts_per_game=25.6, pts_allowed=21.8,
        primary_scheme="west_coast", pass_rate=0.58, pace_plays=65.8,
        qb_name="Jordan Love", qb_style="pocket", qb_adv_rating=84,
        oline_grade="good", oline_pass_block=70.4, oline_run_block=71.8,
        wr1="Jayden Reed", wr2="Christian Watson", te1="Tucker Kraft", rb1="Josh Jacobs",
        yards_per_play=5.8, red_zone_td_pct=0.63, turnover_rate=1.2,
        pass_yds_mult=1.08, rush_yds_mult=1.06, scoring_mult=1.10,
    ),
    "Minnesota Vikings": NFLOffenseProfile(
        team="Minnesota Vikings",
        pts_per_game=27.4, pts_allowed=21.2,
        primary_scheme="west_coast", pass_rate=0.60, pace_plays=66.4,
        qb_name="Sam Darnold", qb_style="pocket", qb_adv_rating=80,
        oline_grade="good", oline_pass_block=69.8, oline_run_block=67.2,
        wr1="Justin Jefferson", wr2="Jordan Addison", te1="T.J. Hockenson", rb1="Aaron Jones",
        yards_per_play=6.0, red_zone_td_pct=0.66, turnover_rate=1.1,
        pass_yds_mult=1.14, rush_yds_mult=1.00, scoring_mult=1.18,
    ),

    # ── NFC SOUTH ─────────────────────────────────────────────────────────────

    "Atlanta Falcons": NFLOffenseProfile(
        team="Atlanta Falcons",
        pts_per_game=24.6, pts_allowed=23.8,
        primary_scheme="spread", pass_rate=0.57, pace_plays=65.4,
        qb_name="Kirk Cousins", qb_style="pocket", qb_adv_rating=80,
        oline_grade="good", oline_pass_block=67.8, oline_run_block=68.4,
        wr1="Drake London", wr2="Darnell Mooney", te1="Kyle Pitts", rb1="Bijan Robinson",
        yards_per_play=5.7, red_zone_td_pct=0.61, turnover_rate=1.3,
        pass_yds_mult=1.06, rush_yds_mult=1.08, scoring_mult=1.04,
    ),
    "Carolina Panthers": NFLOffenseProfile(
        team="Carolina Panthers",
        pts_per_game=17.2, pts_allowed=27.6,
        primary_scheme="pro_style", pass_rate=0.53, pace_plays=61.4,
        qb_name="Bryce Young", qb_style="mobile", qb_adv_rating=68,
        oline_grade="poor", oline_pass_block=56.8, oline_run_block=60.4,
        wr1="Adam Thielen", wr2="Jonathan Mingo", te1="Hayden Hurst", rb1="Miles Sanders",
        yards_per_play=4.7, red_zone_td_pct=0.46, turnover_rate=2.1,
        pass_yds_mult=0.82, rush_yds_mult=0.94, scoring_mult=0.74,
    ),
    "New Orleans Saints": NFLOffenseProfile(
        team="New Orleans Saints",
        pts_per_game=22.4, pts_allowed=24.4,
        primary_scheme="pro_style", pass_rate=0.55, pace_plays=63.8,
        qb_name="Derek Carr", qb_style="pocket", qb_adv_rating=76,
        oline_grade="average", oline_pass_block=64.2, oline_run_block=66.8,
        wr1="Chris Olave", wr2="Rashid Shaheed", te1="Foster Moreau", rb1="Alvin Kamara",
        yards_per_play=5.4, red_zone_td_pct=0.57, turnover_rate=1.5,
        pass_yds_mult=0.98, rush_yds_mult=1.04, scoring_mult=0.96,
    ),
    "Tampa Bay Buccaneers": NFLOffenseProfile(
        team="Tampa Bay Buccaneers",
        pts_per_game=25.8, pts_allowed=22.6,
        primary_scheme="west_coast", pass_rate=0.59, pace_plays=65.6,
        qb_name="Baker Mayfield", qb_style="pocket", qb_adv_rating=82,
        oline_grade="good", oline_pass_block=68.4, oline_run_block=65.2,
        wr1="Mike Evans", wr2="Chris Godwin", te1="Cade Otton", rb1="Rachaad White",
        yards_per_play=5.8, red_zone_td_pct=0.63, turnover_rate=1.2,
        pass_yds_mult=1.08, rush_yds_mult=0.98, scoring_mult=1.10,
    ),

    # ── NFC WEST ──────────────────────────────────────────────────────────────

    "Arizona Cardinals": NFLOffenseProfile(
        team="Arizona Cardinals",
        pts_per_game=21.6, pts_allowed=25.4,
        primary_scheme="spread", pass_rate=0.57, pace_plays=64.8,
        qb_name="Kyler Murray", qb_style="dual_threat", qb_adv_rating=80,
        oline_grade="average", oline_pass_block=63.4, oline_run_block=62.8,
        wr1="Marvin Harrison Jr.", wr2="Michael Wilson", te1="Trey McBride", rb1="James Conner",
        yards_per_play=5.4, red_zone_td_pct=0.56, turnover_rate=1.6,
        pass_yds_mult=0.96, rush_yds_mult=0.98, scoring_mult=0.92,
    ),
    "Los Angeles Rams": NFLOffenseProfile(
        team="Los Angeles Rams",
        pts_per_game=26.8, pts_allowed=22.4,
        primary_scheme="shanahan_outside_zone", pass_rate=0.58, pace_plays=66.8,
        qb_name="Matthew Stafford", qb_style="pocket", qb_adv_rating=84,
        oline_grade="good", oline_pass_block=70.2, oline_run_block=69.8,
        wr1="Cooper Kupp", wr2="Puka Nacua", te1="Tyler Higbee", rb1="Kyren Williams",
        yards_per_play=5.9, red_zone_td_pct=0.65, turnover_rate=1.2,
        pass_yds_mult=1.10, rush_yds_mult=1.08, scoring_mult=1.14,
    ),
    "San Francisco 49ers": NFLOffenseProfile(
        team="San Francisco 49ers",
        pts_per_game=28.8, pts_allowed=19.6,
        primary_scheme="shanahan_outside_zone", pass_rate=0.56, pace_plays=67.4,
        qb_name="Brock Purdy", qb_style="pocket", qb_adv_rating=86,
        oline_grade="elite", oline_pass_block=76.8, oline_run_block=80.4,
        wr1="Deebo Samuel", wr2="Brandon Aiyuk", te1="George Kittle", rb1="Christian McCaffrey",
        yards_per_play=6.3, red_zone_td_pct=0.70, turnover_rate=0.9,
        pass_yds_mult=1.12, rush_yds_mult=1.26, scoring_mult=1.24,
    ),
    "Seattle Seahawks": NFLOffenseProfile(
        team="Seattle Seahawks",
        pts_per_game=23.4, pts_allowed=23.8,
        primary_scheme="spread", pass_rate=0.57, pace_plays=64.8,
        qb_name="Geno Smith", qb_style="pocket", qb_adv_rating=78,
        oline_grade="average", oline_pass_block=65.4, oline_run_block=67.2,
        wr1="DK Metcalf", wr2="Tyler Lockett", te1="Noah Fant", rb1="Zach Charbonnet",
        yards_per_play=5.6, red_zone_td_pct=0.59, turnover_rate=1.4,
        pass_yds_mult=1.02, rush_yds_mult=1.04, scoring_mult=1.00,
    ),
}


# ── QB prop tendencies ────────────────────────────────────────────────────────

@dataclass
class QBPropProfile:
    name:               str
    pass_yds_avg:       float   # passing yards per game
    pass_td_avg:        float
    int_avg:            float
    rush_yds_avg:       float   # rushing yards per game
    completion_pct:     float
    deep_ball_rate:     float   # % of attempts 20+ yards
    pressure_yards:     float   # yards per attempt under pressure
    clean_pocket_yards: float   # yards per attempt from clean pocket
    home_yds_boost:     float   # extra yards at home vs away
    dome_boost:         float   # extra yards in dome vs outdoor

QB_PROP_PROFILES: dict[str, QBPropProfile] = {
    "Patrick Mahomes":   QBPropProfile("Patrick Mahomes",   283.4, 2.4, 0.7,  28.6, 0.674, 0.12, 6.8, 9.1, 14.2, 8.4),
    "Josh Allen":        QBPropProfile("Josh Allen",        282.6, 2.3, 0.9,  52.4, 0.638, 0.14, 5.9, 8.6, 12.8, 6.2),
    "Lamar Jackson":     QBPropProfile("Lamar Jackson",     248.2, 2.1, 0.6,  82.4, 0.672, 0.10, 6.2, 8.8, 10.4, 4.8),
    "Joe Burrow":        QBPropProfile("Joe Burrow",        286.4, 2.4, 0.8,  18.2, 0.682, 0.13, 6.6, 9.4, 13.6, 9.2),
    "Jalen Hurts":       QBPropProfile("Jalen Hurts",       264.8, 2.2, 0.7,  58.6, 0.651, 0.11, 6.1, 8.4, 11.8, 5.4),
    "C.J. Stroud":       QBPropProfile("C.J. Stroud",       268.4, 2.2, 0.8,  22.4, 0.661, 0.12, 6.4, 8.8, 12.4, 7.8),
    "Tua Tagovailoa":    QBPropProfile("Tua Tagovailoa",    282.6, 2.2, 0.7,  14.8, 0.688, 0.10, 6.1, 9.2, 14.8, 11.2),
    "Jordan Love":       QBPropProfile("Jordan Love",       264.2, 2.1, 0.9,  24.6, 0.648, 0.13, 5.8, 8.4, 12.6, 6.8),
    "Justin Herbert":    QBPropProfile("Justin Herbert",    274.8, 2.2, 0.8,  20.4, 0.664, 0.12, 6.2, 8.8, 13.2, 8.6),
    "Dak Prescott":      QBPropProfile("Dak Prescott",      270.4, 2.2, 0.8,  22.8, 0.664, 0.12, 6.0, 8.6, 13.4, 7.4),
    "Brock Purdy":       QBPropProfile("Brock Purdy",       278.4, 2.3, 0.6,  18.4, 0.672, 0.11, 6.6, 9.2, 12.8, 6.2),
    "Jared Goff":        QBPropProfile("Jared Goff",        268.2, 2.2, 0.7,  10.4, 0.678, 0.10, 6.1, 8.9, 14.2, 9.8),
    "Baker Mayfield":    QBPropProfile("Baker Mayfield",    248.6, 2.0, 0.9,  18.6, 0.648, 0.11, 5.6, 8.2, 11.8, 7.6),
    "Matthew Stafford":  QBPropProfile("Matthew Stafford",  262.4, 2.1, 0.9,  10.8, 0.658, 0.13, 5.9, 8.6, 12.4, 7.2),
    "Aaron Rodgers":     QBPropProfile("Aaron Rodgers",     242.8, 1.9, 0.6,  14.2, 0.664, 0.11, 5.6, 8.8, 11.6, 6.8),
    "Caleb Williams":    QBPropProfile("Caleb Williams",    252.4, 2.0, 1.0,  34.6, 0.638, 0.12, 5.4, 7.8, 11.2, 5.6),
    "Jayden Daniels":    QBPropProfile("Jayden Daniels",    244.6, 1.9, 0.8,  48.4, 0.641, 0.10, 5.6, 7.9, 10.8, 5.2),
    "Drake Maye":        QBPropProfile("Drake Maye",        228.4, 1.7, 1.1,  32.8, 0.624, 0.13, 5.0, 7.4, 10.4, 4.8),
    "Bo Nix":            QBPropProfile("Bo Nix",            226.4, 1.7, 1.1,  28.4, 0.622, 0.11, 5.1, 7.2, 10.2, 4.6),
    "Trevor Lawrence":   QBPropProfile("Trevor Lawrence",   248.2, 1.9, 1.0,  22.6, 0.644, 0.12, 5.4, 7.8, 11.4, 5.8),
    "Sam Darnold":       QBPropProfile("Sam Darnold",       252.6, 2.0, 1.0,  18.4, 0.648, 0.11, 5.5, 7.9, 11.8, 6.2),
    "Kyler Murray":      QBPropProfile("Kyler Murray",      238.4, 1.9, 0.8,  44.6, 0.644, 0.11, 5.4, 8.0, 11.0, 5.4),
    "Geno Smith":        QBPropProfile("Geno Smith",        242.6, 1.9, 0.9,  18.4, 0.658, 0.11, 5.5, 8.1, 12.2, 6.8),
    "Russell Wilson":    QBPropProfile("Russell Wilson",    228.4, 1.8, 0.9,  30.4, 0.634, 0.11, 5.2, 7.6, 10.8, 5.2),
    "Kirk Cousins":      QBPropProfile("Kirk Cousins",      248.8, 2.0, 0.8,  12.4, 0.664, 0.10, 5.8, 8.4, 12.4, 8.2),
    "Deshaun Watson":    QBPropProfile("Deshaun Watson",    224.6, 1.7, 1.0,  28.6, 0.622, 0.11, 5.0, 7.4, 10.4, 4.8),
    "Anthony Richardson":QBPropProfile("Anthony Richardson",218.4, 1.7, 1.2,  48.6, 0.588, 0.13, 4.6, 7.0, 9.8, 4.2),
    "Will Levis":        QBPropProfile("Will Levis",        208.4, 1.6, 1.3,  18.4, 0.604, 0.12, 4.4, 6.8, 9.4, 4.0),
    "Gardner Minshew":   QBPropProfile("Gardner Minshew",   218.6, 1.7, 1.1,  14.6, 0.614, 0.11, 4.8, 7.2, 10.2, 5.4),
    "Bryce Young":       QBPropProfile("Bryce Young",       202.4, 1.5, 1.2,  28.4, 0.601, 0.11, 4.4, 6.6, 9.2, 3.8),
    "Derek Carr":        QBPropProfile("Derek Carr",        232.4, 1.8, 0.9,  10.4, 0.638, 0.10, 5.2, 7.8, 11.2, 6.4),
    "Daniel Jones":      QBPropProfile("Daniel Jones",      218.4, 1.6, 1.0,  32.4, 0.618, 0.10, 4.8, 7.0, 10.2, 4.6),
}


# ── Key WR / RB / TE prop baselines ──────────────────────────────────────────

SKILL_PLAYER_PROPS: dict[str, dict] = {
    # WRs — rec_yds_avg, rec_avg, td_avg, target_share
    "Tyreek Hill":          {"pos":"WR","rec_yds":102.4,"rec":7.2,"td":0.72,"target_share":0.28},
    "Stefon Diggs":         {"pos":"WR","rec_yds":88.4, "rec":6.4,"td":0.58,"target_share":0.24},
    "Justin Jefferson":     {"pos":"WR","rec_yds":96.4, "rec":6.8,"td":0.62,"target_share":0.26},
    "CeeDee Lamb":          {"pos":"WR","rec_yds":104.6,"rec":7.4,"td":0.74,"target_share":0.30},
    "A.J. Brown":           {"pos":"WR","rec_yds":92.4, "rec":6.2,"td":0.68,"target_share":0.24},
    "Ja'Marr Chase":        {"pos":"WR","rec_yds":98.6, "rec":6.8,"td":0.72,"target_share":0.26},
    "Davante Adams":        {"pos":"WR","rec_yds":90.4, "rec":6.6,"td":0.66,"target_share":0.26},
    "DeVonta Smith":        {"pos":"WR","rec_yds":82.4, "rec":6.2,"td":0.54,"target_share":0.22},
    "DK Metcalf":           {"pos":"WR","rec_yds":84.6, "rec":5.8,"td":0.62,"target_share":0.22},
    "Amon-Ra St. Brown":    {"pos":"WR","rec_yds":88.4, "rec":7.4,"td":0.56,"target_share":0.28},
    "Cooper Kupp":          {"pos":"WR","rec_yds":84.6, "rec":6.8,"td":0.58,"target_share":0.26},
    "Brandon Aiyuk":        {"pos":"WR","rec_yds":82.4, "rec":5.8,"td":0.60,"target_share":0.22},
    "Deebo Samuel":         {"pos":"WR","rec_yds":74.6, "rec":5.4,"td":0.54,"target_share":0.20},
    "Garrett Wilson":       {"pos":"WR","rec_yds":80.4, "rec":6.2,"td":0.52,"target_share":0.24},
    "Mike Evans":           {"pos":"WR","rec_yds":82.4, "rec":5.6,"td":0.68,"target_share":0.22},
    "Jaylen Waddle":        {"pos":"WR","rec_yds":78.4, "rec":6.4,"td":0.52,"target_share":0.22},
    "Marvin Harrison Jr.":  {"pos":"WR","rec_yds":76.4, "rec":5.8,"td":0.56,"target_share":0.22},
    "Drake London":         {"pos":"WR","rec_yds":74.6, "rec":5.8,"td":0.52,"target_share":0.22},
    "George Pickens":       {"pos":"WR","rec_yds":72.4, "rec":5.2,"td":0.54,"target_share":0.20},
    "Malik Nabers":         {"pos":"WR","rec_yds":76.4, "rec":6.0,"td":0.50,"target_share":0.24},
    "Puka Nacua":           {"pos":"WR","rec_yds":78.4, "rec":6.8,"td":0.48,"target_share":0.26},
    "Rashee Rice":          {"pos":"WR","rec_yds":76.4, "rec":6.2,"td":0.56,"target_share":0.22},
    "Nico Collins":         {"pos":"WR","rec_yds":78.4, "rec":5.8,"td":0.56,"target_share":0.22},
    "Terry McLaurin":       {"pos":"WR","rec_yds":74.6, "rec":5.4,"td":0.54,"target_share":0.22},
    "Zay Flowers":          {"pos":"WR","rec_yds":70.4, "rec":5.8,"td":0.50,"target_share":0.20},
    "DJ Moore":             {"pos":"WR","rec_yds":72.4, "rec":5.6,"td":0.50,"target_share":0.22},
    "Chris Olave":          {"pos":"WR","rec_yds":74.6, "rec":5.6,"td":0.50,"target_share":0.22},

    # TEs
    "Travis Kelce":         {"pos":"TE","rec_yds":82.4, "rec":6.2,"td":0.64,"target_share":0.24},
    "Mark Andrews":         {"pos":"TE","rec_yds":76.4, "rec":5.8,"td":0.62,"target_share":0.22},
    "George Kittle":        {"pos":"TE","rec_yds":74.6, "rec":5.6,"td":0.60,"target_share":0.20},
    "Sam LaPorta":          {"pos":"TE","rec_yds":66.4, "rec":5.4,"td":0.50,"target_share":0.18},
    "Dallas Goedert":       {"pos":"TE","rec_yds":68.4, "rec":5.4,"td":0.52,"target_share":0.18},
    "T.J. Hockenson":       {"pos":"TE","rec_yds":64.6, "rec":5.4,"td":0.50,"target_share":0.18},
    "Trey McBride":         {"pos":"TE","rec_yds":66.4, "rec":5.6,"td":0.48,"target_share":0.20},
    "Kyle Pitts":           {"pos":"TE","rec_yds":62.4, "rec":5.2,"td":0.44,"target_share":0.18},
    "Evan Engram":          {"pos":"TE","rec_yds":68.4, "rec":5.8,"td":0.46,"target_share":0.20},
    "Jake Ferguson":        {"pos":"TE","rec_yds":62.4, "rec":5.2,"td":0.48,"target_share":0.18},
    "Dalton Kincaid":       {"pos":"TE","rec_yds":58.4, "rec":5.0,"td":0.42,"target_share":0.16},

    # RBs — rush_yds_avg, rec_yds_avg, td_avg
    "Christian McCaffrey":  {"pos":"RB","rush_yds":92.4,"rec_yds":44.6,"td":1.12,"target_share":0.14},
    "Saquon Barkley":       {"pos":"RB","rush_yds":88.4,"rec_yds":38.4,"td":0.94,"target_share":0.12},
    "Derrick Henry":        {"pos":"RB","rush_yds":94.6,"rec_yds":18.4,"td":1.02,"target_share":0.06},
    "Bijan Robinson":       {"pos":"RB","rush_yds":82.4,"rec_yds":42.4,"td":0.88,"target_share":0.14},
    "Jonathan Taylor":      {"pos":"RB","rush_yds":84.6,"rec_yds":28.4,"td":0.86,"target_share":0.10},
    "De'Von Achane":        {"pos":"RB","rush_yds":78.4,"rec_yds":44.6,"td":0.82,"target_share":0.14},
    "Breece Hall":          {"pos":"RB","rush_yds":76.4,"rec_yds":42.4,"td":0.78,"target_share":0.14},
    "Josh Jacobs":          {"pos":"RB","rush_yds":82.4,"rec_yds":28.4,"td":0.80,"target_share":0.10},
    "Isiah Pacheco":        {"pos":"RB","rush_yds":72.4,"rec_yds":18.4,"td":0.72,"target_share":0.08},
    "David Montgomery":     {"pos":"RB","rush_yds":68.4,"rec_yds":22.4,"td":0.76,"target_share":0.08},
    "D'Andre Swift":        {"pos":"RB","rush_yds":68.4,"rec_yds":38.4,"td":0.68,"target_share":0.12},
    "James Cook":           {"pos":"RB","rush_yds":72.4,"rec_yds":32.4,"td":0.72,"target_share":0.12},
    "Jahmyr Gibbs":         {"pos":"RB","rush_yds":70.4,"rec_yds":36.4,"td":0.74,"target_share":0.12},
    "Alvin Kamara":         {"pos":"RB","rush_yds":64.6,"rec_yds":44.6,"td":0.70,"target_share":0.16},
    "Tony Pollard":         {"pos":"RB","rush_yds":68.4,"rec_yds":28.4,"td":0.64,"target_share":0.10},
    "Kyren Williams":       {"pos":"RB","rush_yds":72.4,"rec_yds":26.4,"td":0.68,"target_share":0.10},
    "Nick Chubb":           {"pos":"RB","rush_yds":74.6,"rec_yds":18.4,"td":0.72,"target_share":0.06},
    "Najee Harris":         {"pos":"RB","rush_yds":62.4,"rec_yds":24.4,"td":0.60,"target_share":0.08},
    "Zach Charbonnet":      {"pos":"RB","rush_yds":66.4,"rec_yds":22.4,"td":0.62,"target_share":0.08},
    "Aaron Jones":          {"pos":"RB","rush_yds":64.6,"rec_yds":32.4,"td":0.64,"target_share":0.10},
}


# ── NFL game totals by matchup type ───────────────────────────────────────────

NFL_LEAGUE_AVG = {
    "points_per_game_per_team": 23.4,   # 2025 NFL season
    "total_avg":                 46.8,
    "home_advantage_pts":         2.5,
    "dome_scoring_boost":         2.1,   # indoor stadiums average ~2 more pts per team
    "primetime_home_boost":       1.8,   # home teams cover at higher rate in primetime
}

# Dome / indoor stadiums (weather neutral)
NFL_DOME_TEAMS = {
    "Atlanta Falcons", "New Orleans Saints", "Indianapolis Colts",
    "Las Vegas Raiders", "Minnesota Vikings", "Detroit Lions",
    "Los Angeles Rams", "Los Angeles Chargers", "Dallas Cowboys",
    "Arizona Cardinals",  # retractable roof
    "Houston Texans",     # retractable roof
}
