"""
College Football 2026 — Team Knowledge Base
============================================
Offensive/defensive profiles for the top 64 FBS programs.
Stats from 2025 season; updated at season start via ESPN API.

Used by cfb_picks.py to score totals and sides when live odds are unavailable.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class CFBTeamProfile:
    team: str
    conference: str
    pts_per_game: float       # 2025 season offense
    pts_allowed: float        # 2025 season defense
    yards_per_play: float
    pass_rate: float          # 0-1
    pace_plays: float         # plays per game
    home_field_boost: float   # extra pts at home (big stadiums = +3 to +5)
    # Coaching
    coach: str
    coach_style: str          # "air_raid","spread","pro_style","option","run_heavy"
    # Composite ratings (0-100)
    off_rating: float
    def_rating: float         # lower = better defense


CFB_TEAM_PROFILES: dict[str, CFBTeamProfile] = {

    # ── SEC ──────────────────────────────────────────────────────────────────

    "Georgia Bulldogs": CFBTeamProfile(
        team="Georgia Bulldogs", conference="SEC",
        pts_per_game=36.2, pts_allowed=12.8, yards_per_play=6.8,
        pass_rate=0.52, pace_plays=68.4, home_field_boost=3.5,
        coach="Kirby Smart", coach_style="pro_style",
        off_rating=88, def_rating=18,
    ),
    "Alabama Crimson Tide": CFBTeamProfile(
        team="Alabama Crimson Tide", conference="SEC",
        pts_per_game=38.4, pts_allowed=16.2, yards_per_play=7.1,
        pass_rate=0.57, pace_plays=70.2, home_field_boost=4.0,
        coach="Kalen DeBoer", coach_style="spread",
        off_rating=90, def_rating=22,
    ),
    "Texas Longhorns": CFBTeamProfile(
        team="Texas Longhorns", conference="SEC",
        pts_per_game=37.8, pts_allowed=18.4, yards_per_play=6.9,
        pass_rate=0.55, pace_plays=71.0, home_field_boost=4.5,
        coach="Steve Sarkisian", coach_style="spread",
        off_rating=89, def_rating=25,
    ),
    "LSU Tigers": CFBTeamProfile(
        team="LSU Tigers", conference="SEC",
        pts_per_game=34.6, pts_allowed=21.8, yards_per_play=6.5,
        pass_rate=0.60, pace_plays=72.4, home_field_boost=5.0,
        coach="Brian Kelly", coach_style="pro_style",
        off_rating=84, def_rating=30,
    ),
    "Tennessee Volunteers": CFBTeamProfile(
        team="Tennessee Volunteers", conference="SEC",
        pts_per_game=36.8, pts_allowed=22.4, yards_per_play=6.9,
        pass_rate=0.62, pace_plays=73.8, home_field_boost=4.5,
        coach="Josh Heupel", coach_style="air_raid",
        off_rating=87, def_rating=32,
    ),
    "Ole Miss Rebels": CFBTeamProfile(
        team="Ole Miss Rebels", conference="SEC",
        pts_per_game=35.2, pts_allowed=24.6, yards_per_play=6.7,
        pass_rate=0.64, pace_plays=75.2, home_field_boost=3.5,
        coach="Lane Kiffin", coach_style="air_raid",
        off_rating=85, def_rating=35,
    ),
    "Auburn Tigers": CFBTeamProfile(
        team="Auburn Tigers", conference="SEC",
        pts_per_game=28.4, pts_allowed=24.2, yards_per_play=5.8,
        pass_rate=0.54, pace_plays=67.8, home_field_boost=4.0,
        coach="Hugh Freeze", coach_style="spread",
        off_rating=72, def_rating=33,
    ),
    "Florida Gators": CFBTeamProfile(
        team="Florida Gators", conference="SEC",
        pts_per_game=30.2, pts_allowed=26.4, yards_per_play=6.0,
        pass_rate=0.58, pace_plays=70.4, home_field_boost=4.0,
        coach="Billy Napier", coach_style="spread",
        off_rating=75, def_rating=38,
    ),
    "Arkansas Razorbacks": CFBTeamProfile(
        team="Arkansas Razorbacks", conference="SEC",
        pts_per_game=26.8, pts_allowed=25.6, yards_per_play=5.6,
        pass_rate=0.52, pace_plays=66.2, home_field_boost=3.5,
        coach="Sam Pittman", coach_style="pro_style",
        off_rating=68, def_rating=36,
    ),
    "South Carolina Gamecocks": CFBTeamProfile(
        team="South Carolina Gamecocks", conference="SEC",
        pts_per_game=27.6, pts_allowed=27.2, yards_per_play=5.7,
        pass_rate=0.55, pace_plays=68.0, home_field_boost=3.0,
        coach="Shane Beamer", coach_style="spread",
        off_rating=70, def_rating=40,
    ),
    "Mississippi State Bulldogs": CFBTeamProfile(
        team="Mississippi State Bulldogs", conference="SEC",
        pts_per_game=24.2, pts_allowed=28.4, yards_per_play=5.2,
        pass_rate=0.68, pace_plays=76.0, home_field_boost=3.0,
        coach="Jeff Lebby", coach_style="air_raid",
        off_rating=62, def_rating=42,
    ),
    "Kentucky Wildcats": CFBTeamProfile(
        team="Kentucky Wildcats", conference="SEC",
        pts_per_game=26.4, pts_allowed=24.8, yards_per_play=5.5,
        pass_rate=0.50, pace_plays=65.4, home_field_boost=3.0,
        coach="Mark Stoops", coach_style="run_heavy",
        off_rating=66, def_rating=35,
    ),
    "Missouri Tigers": CFBTeamProfile(
        team="Missouri Tigers", conference="SEC",
        pts_per_game=29.8, pts_allowed=26.2, yards_per_play=6.0,
        pass_rate=0.56, pace_plays=69.2, home_field_boost=3.0,
        coach="Eli Drinkwitz", coach_style="spread",
        off_rating=74, def_rating=38,
    ),
    "Vanderbilt Commodores": CFBTeamProfile(
        team="Vanderbilt Commodores", conference="SEC",
        pts_per_game=22.4, pts_allowed=32.8, yards_per_play=5.0,
        pass_rate=0.58, pace_plays=68.4, home_field_boost=2.0,
        coach="Clark Lea", coach_style="pro_style",
        off_rating=55, def_rating=52,
    ),

    # ── Big Ten ───────────────────────────────────────────────────────────────

    "Michigan Wolverines": CFBTeamProfile(
        team="Michigan Wolverines", conference="Big Ten",
        pts_per_game=34.2, pts_allowed=14.6, yards_per_play=6.4,
        pass_rate=0.48, pace_plays=65.8, home_field_boost=4.0,
        coach="Sherrone Moore", coach_style="run_heavy",
        off_rating=83, def_rating=20,
    ),
    "Ohio State Buckeyes": CFBTeamProfile(
        team="Ohio State Buckeyes", conference="Big Ten",
        pts_per_game=42.8, pts_allowed=16.4, yards_per_play=7.4,
        pass_rate=0.60, pace_plays=72.0, home_field_boost=4.5,
        coach="Ryan Day", coach_style="spread",
        off_rating=94, def_rating=23,
    ),
    "Penn State Nittany Lions": CFBTeamProfile(
        team="Penn State Nittany Lions", conference="Big Ten",
        pts_per_game=33.6, pts_allowed=18.2, yards_per_play=6.4,
        pass_rate=0.55, pace_plays=68.6, home_field_boost=4.5,
        coach="James Franklin", coach_style="pro_style",
        off_rating=82, def_rating=26,
    ),
    "Oregon Ducks": CFBTeamProfile(
        team="Oregon Ducks", conference="Big Ten",
        pts_per_game=39.4, pts_allowed=19.8, yards_per_play=7.0,
        pass_rate=0.58, pace_plays=73.4, home_field_boost=4.0,
        coach="Dan Lanning", coach_style="spread",
        off_rating=91, def_rating=28,
    ),
    "Washington Huskies": CFBTeamProfile(
        team="Washington Huskies", conference="Big Ten",
        pts_per_game=36.2, pts_allowed=22.6, yards_per_play=6.8,
        pass_rate=0.64, pace_plays=74.8, home_field_boost=3.5,
        coach="Jedd Fisch", coach_style="air_raid",
        off_rating=86, def_rating=32,
    ),
    "USC Trojans": CFBTeamProfile(
        team="USC Trojans", conference="Big Ten",
        pts_per_game=34.8, pts_allowed=26.4, yards_per_play=6.6,
        pass_rate=0.62, pace_plays=73.0, home_field_boost=3.0,
        coach="Lincoln Riley", coach_style="air_raid",
        off_rating=84, def_rating=38,
    ),
    "UCLA Bruins": CFBTeamProfile(
        team="UCLA Bruins", conference="Big Ten",
        pts_per_game=30.4, pts_allowed=24.8, yards_per_play=6.0,
        pass_rate=0.60, pace_plays=71.4, home_field_boost=3.0,
        coach="DeShaun Foster", coach_style="spread",
        off_rating=75, def_rating=36,
    ),
    "Iowa Hawkeyes": CFBTeamProfile(
        team="Iowa Hawkeyes", conference="Big Ten",
        pts_per_game=22.8, pts_allowed=18.6, yards_per_play=5.0,
        pass_rate=0.50, pace_plays=62.4, home_field_boost=4.0,
        coach="Kirk Ferentz", coach_style="pro_style",
        off_rating=56, def_rating=24,
    ),
    "Wisconsin Badgers": CFBTeamProfile(
        team="Wisconsin Badgers", conference="Big Ten",
        pts_per_game=26.4, pts_allowed=20.4, yards_per_play=5.4,
        pass_rate=0.46, pace_plays=63.8, home_field_boost=3.5,
        coach="Luke Fickell", coach_style="run_heavy",
        off_rating=64, def_rating=28,
    ),
    "Michigan State Spartans": CFBTeamProfile(
        team="Michigan State Spartans", conference="Big Ten",
        pts_per_game=24.6, pts_allowed=28.4, yards_per_play=5.2,
        pass_rate=0.55, pace_plays=67.2, home_field_boost=3.0,
        coach="Jonathan Smith", coach_style="spread",
        off_rating=60, def_rating=42,
    ),
    "Minnesota Golden Gophers": CFBTeamProfile(
        team="Minnesota Golden Gophers", conference="Big Ten",
        pts_per_game=26.2, pts_allowed=22.8, yards_per_play=5.4,
        pass_rate=0.50, pace_plays=65.6, home_field_boost=3.0,
        coach="P.J. Fleck", coach_style="run_heavy",
        off_rating=64, def_rating=32,
    ),
    "Nebraska Cornhuskers": CFBTeamProfile(
        team="Nebraska Cornhuskers", conference="Big Ten",
        pts_per_game=27.8, pts_allowed=25.4, yards_per_play=5.6,
        pass_rate=0.54, pace_plays=68.4, home_field_boost=4.5,
        coach="Matt Rhule", coach_style="pro_style",
        off_rating=68, def_rating=37,
    ),
    "Indiana Hoosiers": CFBTeamProfile(
        team="Indiana Hoosiers", conference="Big Ten",
        pts_per_game=32.4, pts_allowed=24.6, yards_per_play=6.2,
        pass_rate=0.58, pace_plays=70.8, home_field_boost=3.0,
        coach="Curt Cignetti", coach_style="spread",
        off_rating=78, def_rating=36,
    ),

    # ── Big 12 ────────────────────────────────────────────────────────────────

    "Texas Tech Red Raiders": CFBTeamProfile(
        team="Texas Tech Red Raiders", conference="Big 12",
        pts_per_game=34.4, pts_allowed=28.4, yards_per_play=6.5,
        pass_rate=0.66, pace_plays=76.4, home_field_boost=3.5,
        coach="Joey McGuire", coach_style="air_raid",
        off_rating=83, def_rating=42,
    ),
    "Kansas State Wildcats": CFBTeamProfile(
        team="Kansas State Wildcats", conference="Big 12",
        pts_per_game=30.8, pts_allowed=22.4, yards_per_play=5.9,
        pass_rate=0.55, pace_plays=67.6, home_field_boost=4.0,
        coach="Chris Klieman", coach_style="pro_style",
        off_rating=76, def_rating=31,
    ),
    "Oklahoma State Cowboys": CFBTeamProfile(
        team="Oklahoma State Cowboys", conference="Big 12",
        pts_per_game=32.6, pts_allowed=24.8, yards_per_play=6.2,
        pass_rate=0.58, pace_plays=70.4, home_field_boost=4.0,
        coach="Mike Gundy", coach_style="spread",
        off_rating=79, def_rating=36,
    ),
    "Iowa State Cyclones": CFBTeamProfile(
        team="Iowa State Cyclones", conference="Big 12",
        pts_per_game=28.6, pts_allowed=22.6, yards_per_play=5.6,
        pass_rate=0.54, pace_plays=66.8, home_field_boost=3.5,
        coach="Matt Campbell", coach_style="pro_style",
        off_rating=70, def_rating=32,
    ),
    "TCU Horned Frogs": CFBTeamProfile(
        team="TCU Horned Frogs", conference="Big 12",
        pts_per_game=33.4, pts_allowed=26.8, yards_per_play=6.4,
        pass_rate=0.62, pace_plays=73.2, home_field_boost=3.5,
        coach="Sonny Dykes", coach_style="air_raid",
        off_rating=81, def_rating=39,
    ),
    "Baylor Bears": CFBTeamProfile(
        team="Baylor Bears", conference="Big 12",
        pts_per_game=28.4, pts_allowed=26.4, yards_per_play=5.7,
        pass_rate=0.55, pace_plays=68.2, home_field_boost=3.0,
        coach="Dave Aranda", coach_style="pro_style",
        off_rating=70, def_rating=38,
    ),
    "West Virginia Mountaineers": CFBTeamProfile(
        team="West Virginia Mountaineers", conference="Big 12",
        pts_per_game=26.8, pts_allowed=27.6, yards_per_play=5.5,
        pass_rate=0.57, pace_plays=69.4, home_field_boost=4.0,
        coach="Neal Brown", coach_style="spread",
        off_rating=66, def_rating=41,
    ),
    "Colorado Buffaloes": CFBTeamProfile(
        team="Colorado Buffaloes", conference="Big 12",
        pts_per_game=36.4, pts_allowed=30.8, yards_per_play=6.6,
        pass_rate=0.63, pace_plays=74.0, home_field_boost=3.5,
        coach="Deion Sanders", coach_style="spread",
        off_rating=85, def_rating=46,
    ),
    "Utah Utes": CFBTeamProfile(
        team="Utah Utes", conference="Big 12",
        pts_per_game=32.8, pts_allowed=20.4, yards_per_play=6.1,
        pass_rate=0.52, pace_plays=67.0, home_field_boost=3.5,
        coach="Kyle Whittingham", coach_style="run_heavy",
        off_rating=79, def_rating=28,
    ),
    "Arizona Wildcats": CFBTeamProfile(
        team="Arizona Wildcats", conference="Big 12",
        pts_per_game=34.2, pts_allowed=28.6, yards_per_play=6.4,
        pass_rate=0.60, pace_plays=72.6, home_field_boost=3.0,
        coach="Brent Brennan", coach_style="spread",
        off_rating=82, def_rating=43,
    ),
    "Arizona State Sun Devils": CFBTeamProfile(
        team="Arizona State Sun Devils", conference="Big 12",
        pts_per_game=28.6, pts_allowed=24.2, yards_per_play=5.7,
        pass_rate=0.55, pace_plays=68.8, home_field_boost=3.0,
        coach="Kenny Dillingham", coach_style="spread",
        off_rating=70, def_rating=34,
    ),

    # ── ACC ───────────────────────────────────────────────────────────────────

    "Florida State Seminoles": CFBTeamProfile(
        team="Florida State Seminoles", conference="ACC",
        pts_per_game=32.4, pts_allowed=20.6, yards_per_play=6.2,
        pass_rate=0.57, pace_plays=69.4, home_field_boost=4.0,
        coach="Mike Norvell", coach_style="spread",
        off_rating=79, def_rating=29,
    ),
    "Clemson Tigers": CFBTeamProfile(
        team="Clemson Tigers", conference="ACC",
        pts_per_game=30.8, pts_allowed=18.4, yards_per_play=6.0,
        pass_rate=0.54, pace_plays=67.4, home_field_boost=4.5,
        coach="Dabo Swinney", coach_style="pro_style",
        off_rating=76, def_rating=25,
    ),
    "Miami Hurricanes": CFBTeamProfile(
        team="Miami Hurricanes", conference="ACC",
        pts_per_game=36.8, pts_allowed=22.4, yards_per_play=6.8,
        pass_rate=0.61, pace_plays=72.4, home_field_boost=3.5,
        coach="Mario Cristobal", coach_style="spread",
        off_rating=87, def_rating=31,
    ),
    "North Carolina Tar Heels": CFBTeamProfile(
        team="North Carolina Tar Heels", conference="ACC",
        pts_per_game=35.4, pts_allowed=28.6, yards_per_play=6.6,
        pass_rate=0.63, pace_plays=74.2, home_field_boost=3.0,
        coach="Mack Brown", coach_style="spread",
        off_rating=84, def_rating=42,
    ),
    "NC State Wolfpack": CFBTeamProfile(
        team="NC State Wolfpack", conference="ACC",
        pts_per_game=28.4, pts_allowed=24.2, yards_per_play=5.7,
        pass_rate=0.55, pace_plays=68.6, home_field_boost=3.0,
        coach="Dave Doeren", coach_style="pro_style",
        off_rating=70, def_rating=34,
    ),
    "Louisville Cardinals": CFBTeamProfile(
        team="Louisville Cardinals", conference="ACC",
        pts_per_game=30.6, pts_allowed=24.4, yards_per_play=5.9,
        pass_rate=0.57, pace_plays=70.2, home_field_boost=3.0,
        coach="Jeff Brohm", coach_style="spread",
        off_rating=75, def_rating=35,
    ),
    "Pittsburgh Panthers": CFBTeamProfile(
        team="Pittsburgh Panthers", conference="ACC",
        pts_per_game=26.4, pts_allowed=26.8, yards_per_play=5.4,
        pass_rate=0.58, pace_plays=69.8, home_field_boost=3.0,
        coach="Pat Narduzzi", coach_style="pro_style",
        off_rating=65, def_rating=40,
    ),
    "Virginia Tech Hokies": CFBTeamProfile(
        team="Virginia Tech Hokies", conference="ACC",
        pts_per_game=26.8, pts_allowed=26.4, yards_per_play=5.5,
        pass_rate=0.56, pace_plays=68.4, home_field_boost=3.5,
        coach="Brent Pry", coach_style="pro_style",
        off_rating=66, def_rating=39,
    ),

    # ── Mountain West / Independents ─────────────────────────────────────────

    "Notre Dame Fighting Irish": CFBTeamProfile(
        team="Notre Dame Fighting Irish", conference="Independent",
        pts_per_game=34.8, pts_allowed=16.8, yards_per_play=6.5,
        pass_rate=0.54, pace_plays=68.2, home_field_boost=5.0,
        coach="Marcus Freeman", coach_style="pro_style",
        off_rating=83, def_rating=22,
    ),
    "Boise State Broncos": CFBTeamProfile(
        team="Boise State Broncos", conference="Mountain West",
        pts_per_game=36.2, pts_allowed=18.4, yards_per_play=6.7,
        pass_rate=0.60, pace_plays=72.8, home_field_boost=4.5,
        coach="Spencer Danielson", coach_style="spread",
        off_rating=86, def_rating=25,
    ),
    "UNLV Rebels": CFBTeamProfile(
        team="UNLV Rebels", conference="Mountain West",
        pts_per_game=34.8, pts_allowed=24.6, yards_per_play=6.4,
        pass_rate=0.60, pace_plays=73.0, home_field_boost=3.0,
        coach="Barry Odom", coach_style="spread",
        off_rating=83, def_rating=36,
    ),
    "SMU Mustangs": CFBTeamProfile(
        team="SMU Mustangs", conference="ACC",
        pts_per_game=38.4, pts_allowed=26.4, yards_per_play=6.9,
        pass_rate=0.64, pace_plays=75.4, home_field_boost=3.5,
        coach="Rhett Lashlee", coach_style="air_raid",
        off_rating=89, def_rating=38,
    ),
}

# League average used when a team is not in profiles
CFB_LEAGUE_AVG = {
    "pts_per_game":  30.2,
    "pts_allowed":   25.4,
    "total_avg":     55.6,   # FBS average game total (2025 season)
}
