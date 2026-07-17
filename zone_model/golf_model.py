"""
Golf Tournament Model
=====================
Identifies value bets in major golf tournaments by combining:

  1. Course DNA — what type of player the course favors
  2. Player fit score — how well a player's game matches the course
  3. Form & momentum — recent results, course history, practice intel
  4. News & prep layer — Rory-at-Augusta type edges (publicly known prep,
     equipment changes, swing coach changes, motivation narratives)
  5. Market inefficiency — public money on big names inflates prices on
     journeymen; sharp value often lives in 20-40/1 range

Covers only marquee events:
  Majors:      Masters, US Open, The Open Championship, PGA Championship
  WGC/Elite:   Players Championship, Genesis Invitational, Arnold Palmer,
               Memorial, Scottish Open, BMW Championship, Tour Championship
  Ryder Cup / Presidents Cup (matchplay model variant)

Output: ranked value picks with fit score, edge vs market odds, and rationale
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math


# ── Course profiles ────────────────────────────────────────────────────────────

@dataclass
class CourseProfile:
    name:               str
    tournament:         str
    # Terrain & setup
    course_type:        str    # "links","parkland","desert","bermuda","bentgrass"
    avg_winning_score:  int    # under par, e.g. -10
    plays_long:         bool   # >7,300 yards, rewards big hitters
    plays_short:        bool   # <7,100 yards, premium on precision
    # Key skill weights (0–1, must sum to ~1.0)
    driving_distance_weight: float   # bomb-and-gouge setups
    driving_accuracy_weight: float   # tight fairways, trees
    iron_precision_weight:   float   # approach precision matters
    short_game_weight:       float   # chipping/bunker key
    putting_weight:          float   # green speed/slope
    # Green characteristics
    green_speed:        str    # "fast","medium","slow"
    green_firmness:     str    # "firm","medium","soft"
    green_undulation:   str    # "severe","moderate","mild"
    # Weather factor
    wind_factor:        float  # 0–1: how much wind typically matters
    # Player type that wins here most
    favors:             list[str]  # e.g. ["big_hitter","ball_striker","links_specialist"]
    # Historical notes
    notes:              str = ""


COURSE_PROFILES: dict[str, CourseProfile] = {

    "Augusta National": CourseProfile(
        name="Augusta National",
        tournament="The Masters",
        course_type="parkland",
        avg_winning_score=-12,
        plays_long=True,
        plays_short=False,
        driving_distance_weight=0.25,
        driving_accuracy_weight=0.20,
        iron_precision_weight=0.25,
        short_game_weight=0.15,
        putting_weight=0.15,
        green_speed="fast",
        green_firmness="firm",
        green_undulation="severe",
        wind_factor=0.2,
        favors=["big_hitter", "ball_striker", "creative_shotmaker", "experienced"],
        notes="Amen Corner (11-13) demands controlled draws. Approach angle crucial — "
              "hitting from the correct side of fairway. Back-9 birdie opportunities "
              "reward aggressive play from those who navigated front-9 safely. "
              "Experience at Augusta matters enormously — first-timers rarely win. "
              "Soft fades struggle on holes requiring draws.",
    ),

    "Pinehurst No. 2": CourseProfile(
        name="Pinehurst No. 2",
        tournament="US Open",
        course_type="parkland",
        avg_winning_score=-2,
        plays_long=False,
        plays_short=False,
        driving_distance_weight=0.15,
        driving_accuracy_weight=0.25,
        iron_precision_weight=0.25,
        short_game_weight=0.25,
        putting_weight=0.10,
        green_speed="fast",
        green_firmness="firm",
        green_undulation="moderate",
        wind_factor=0.3,
        favors=["scrambler", "short_game_specialist", "patient_grinder"],
        notes="Turtleback greens repel everything. Missing in the wrong spot "
              "means a near-impossible up-and-down. Patience and course management "
              "beat length every time here.",
    ),

    "Royal Liverpool": CourseProfile(
        name="Royal Liverpool",
        tournament="The Open Championship",
        course_type="links",
        avg_winning_score=-16,
        plays_long=True,
        plays_short=False,
        driving_distance_weight=0.30,
        driving_accuracy_weight=0.15,
        iron_precision_weight=0.20,
        short_game_weight=0.20,
        putting_weight=0.15,
        green_speed="medium",
        green_firmness="firm",
        green_undulation="moderate",
        wind_factor=0.8,
        favors=["links_specialist", "big_hitter", "wind_player", "creative_shotmaker"],
        notes="Links conditions: bump-and-run, ground game essential. Wind direction "
              "changes everything — morning vs afternoon draw matters. Players who "
              "grew up playing links golf (European, especially Irish/Scottish) have "
              "a major edge.",
    ),

    "St Andrews Old Course": CourseProfile(
        name="St Andrews Old Course",
        tournament="The Open Championship",
        course_type="links",
        avg_winning_score=-20,
        plays_long=False,
        plays_short=False,
        driving_distance_weight=0.25,
        driving_accuracy_weight=0.20,
        iron_precision_weight=0.20,
        short_game_weight=0.20,
        putting_weight=0.15,
        green_speed="medium",
        green_firmness="firm",
        green_undulation="severe",
        wind_factor=0.7,
        favors=["links_specialist", "creative_shotmaker", "experienced", "wind_player"],
        notes="Home of golf. Double greens, hidden bunkers (Road Hole bunker). "
              "Local knowledge and course experience invaluable. Road Hole (17) "
              "can destroy a round. Low-ball flight wins in wind.",
    ),

    "Bethpage Black": CourseProfile(
        name="Bethpage Black",
        tournament="US Open / PGA Championship",
        course_type="parkland",
        avg_winning_score=-8,
        plays_long=True,
        plays_short=False,
        driving_distance_weight=0.30,
        driving_accuracy_weight=0.20,
        iron_precision_weight=0.25,
        short_game_weight=0.15,
        putting_weight=0.10,
        green_speed="fast",
        green_firmness="firm",
        green_undulation="moderate",
        wind_factor=0.4,
        favors=["big_hitter", "ball_striker", "physical_grinder"],
        notes="Monster public track. Rough is brutal — hitting fairways mandatory. "
              "Physically demanding 36-hole days. Longer hitters have an edge but "
              "must control ball flight.",
    ),

    "Valhalla": CourseProfile(
        name="Valhalla",
        tournament="PGA Championship",
        course_type="parkland",
        avg_winning_score=-14,
        plays_long=True,
        plays_short=False,
        driving_distance_weight=0.30,
        driving_accuracy_weight=0.15,
        iron_precision_weight=0.25,
        short_game_weight=0.15,
        putting_weight=0.15,
        green_speed="fast",
        green_firmness="medium",
        green_undulation="moderate",
        wind_factor=0.3,
        favors=["big_hitter", "ball_striker", "aggressive_player"],
        notes="Scoring friendly enough to reward aggression. Par 5s reachable "
              "in two for long hitters — birdie opportunities cluster on back 9.",
    ),

    "TPC Sawgrass": CourseProfile(
        name="TPC Sawgrass",
        tournament="The Players Championship",
        course_type="parkland",
        avg_winning_score=-14,
        plays_long=False,
        plays_short=True,
        driving_distance_weight=0.15,
        driving_accuracy_weight=0.30,
        iron_precision_weight=0.30,
        short_game_weight=0.15,
        putting_weight=0.10,
        green_speed="fast",
        green_firmness="medium",
        green_undulation="moderate",
        wind_factor=0.5,
        favors=["accurate_driver", "iron_specialist", "mentally_tough"],
        notes="17th island green is iconic but 18 is tougher statistically. "
              "Wind off the water changes club selection constantly. Accuracy "
              "off the tee beats distance. Bogey-free golf wins here.",
    ),

    "Riviera": CourseProfile(
        name="Riviera Country Club",
        tournament="Genesis Invitational",
        course_type="parkland",
        avg_winning_score=-15,
        plays_long=False,
        plays_short=False,
        driving_distance_weight=0.20,
        driving_accuracy_weight=0.25,
        iron_precision_weight=0.30,
        short_game_weight=0.15,
        putting_weight=0.10,
        green_speed="fast",
        green_firmness="firm",
        green_undulation="moderate",
        wind_factor=0.3,
        favors=["ball_striker", "iron_specialist", "experienced"],
        notes="Kikuyu rough is unique — grabs the hosel, players must adapt. "
              "Approach game from 150-200 yards defines the week. "
              "Classic shotmaking course — rewards traditional ball flight.",
    ),

    "Muirfield Village": CourseProfile(
        name="Muirfield Village",
        tournament="The Memorial",
        course_type="parkland",
        avg_winning_score=-16,
        plays_long=False,
        plays_short=False,
        driving_distance_weight=0.20,
        driving_accuracy_weight=0.25,
        iron_precision_weight=0.30,
        short_game_weight=0.15,
        putting_weight=0.10,
        green_speed="fast",
        green_firmness="firm",
        green_undulation="severe",
        wind_factor=0.3,
        favors=["ball_striker", "iron_specialist", "experienced"],
        notes="Jack Nicklaus design — demands total ball striking. "
              "Creek comes into play on multiple holes. Approach shots must "
              "be precise — wrong side of green = impossible putt.",
    ),

    "Royal Troon": CourseProfile(
        name="Royal Troon",
        tournament="The Open Championship",
        course_type="links",
        avg_winning_score=-15,
        plays_long=True,
        plays_short=False,
        driving_distance_weight=0.30,
        driving_accuracy_weight=0.15,
        iron_precision_weight=0.20,
        short_game_weight=0.20,
        putting_weight=0.15,
        green_speed="medium",
        green_firmness="firm",
        green_undulation="moderate",
        wind_factor=0.85,
        favors=["links_specialist", "big_hitter", "wind_player"],
        notes="Postage Stamp (8th) — tiny par 3 can destroy or create momentum. "
              "Outward nine plays downwind, inward nine into prevailing wind. "
              "Draw bias helpful throughout.",
    ),
}


# ── Player profiles ────────────────────────────────────────────────────────────

@dataclass
class GolfPlayerProfile:
    name:                   str
    world_ranking:          int      # current OWGR
    player_type:            list[str]  # ["big_hitter","ball_striker","links_specialist",etc.]
    # Key statistical strengths (percentile on tour, 0–100)
    driving_distance_pct:   float    # 80 = top 20% on tour
    driving_accuracy_pct:   float
    iron_precision_pct:     float    # strokes gained approach
    short_game_pct:         float    # strokes gained around green
    putting_pct:            float    # strokes gained putting
    # Major experience
    major_wins:             int
    major_top10s:           int
    # Course-specific history: course_name -> [best_finish, times_played, avg_score_to_par]
    course_history:         dict[str, tuple[int, int, float]] = field(default_factory=dict)
    # Recent form: last 8 events [finish positions]
    recent_form:            list[int] = field(default_factory=list)
    # Prep / news intel (manually updated before each tournament)
    prep_notes:             list[str] = field(default_factory=list)
    # Injury / fitness flags
    fitness_flag:           str = "healthy"   # "healthy","minor","doubtful","out"


PLAYER_PROFILES: dict[str, GolfPlayerProfile] = {

    "Scottie Scheffler": GolfPlayerProfile(
        name="Scottie Scheffler",
        world_ranking=1,
        player_type=["ball_striker", "iron_specialist", "accurate_driver", "mentally_tough"],
        driving_distance_pct=72,
        driving_accuracy_pct=75,
        iron_precision_pct=98,
        short_game_pct=82,
        putting_pct=70,
        major_wins=2,
        major_top10s=8,
        course_history={
            "Augusta National":       (1, 4, -9.5),
            "TPC Sawgrass":           (1, 3, -13.0),
            "Riviera Country Club":   (1, 4, -14.5),
        },
        recent_form=[1, 2, 1, 3, 1, 4, 2, 1],
    ),

    "Rory McIlroy": GolfPlayerProfile(
        name="Rory McIlroy",
        world_ranking=2,
        player_type=["big_hitter", "ball_striker", "links_specialist", "iron_specialist"],
        driving_distance_pct=95,
        driving_accuracy_pct=65,
        iron_precision_pct=92,
        short_game_pct=75,
        putting_pct=78,
        major_wins=4,
        major_top10s=15,
        course_history={
            "Augusta National":       (1, 15, -7.2),
            "St Andrews Old Course":  (2, 4, -16.0),
            "Royal Liverpool":        (1, 3, -17.0),
            "TPC Sawgrass":           (1, 10, -13.5),
            "Muirfield Village":      (3, 6, -14.0),
        },
        recent_form=[1, 4, 2, 8, 1, 3, 2, 5],
    ),

    "Xander Schauffele": GolfPlayerProfile(
        name="Xander Schauffele",
        world_ranking=3,
        player_type=["ball_striker", "accurate_driver", "mentally_tough"],
        driving_distance_pct=80,
        driving_accuracy_pct=80,
        iron_precision_pct=90,
        short_game_pct=80,
        putting_pct=82,
        major_wins=2,
        major_top10s=12,
        course_history={
            "Augusta National":       (5, 6, -8.0),
            "Valhalla":               (1, 2, -21.0),
            "TPC Sawgrass":           (4, 5, -12.0),
        },
        recent_form=[3, 1, 4, 2, 7, 1, 3, 2],
    ),

    "Jon Rahm": GolfPlayerProfile(
        name="Jon Rahm",
        world_ranking=4,
        player_type=["ball_striker", "iron_specialist", "links_specialist", "big_hitter"],
        driving_distance_pct=88,
        driving_accuracy_pct=72,
        iron_precision_pct=95,
        short_game_pct=85,
        putting_pct=80,
        major_wins=2,
        major_top10s=14,
        course_history={
            "Augusta National":       (1, 5, -10.5),
            "St Andrews Old Course":  (4, 3, -15.0),
            "Muirfield Village":      (1, 4, -18.0),
            "Riviera Country Club":   (2, 4, -15.0),
        },
        recent_form=[2, 5, 1, 3, 8, 2, 4, 1],
    ),

    "Collin Morikawa": GolfPlayerProfile(
        name="Collin Morikawa",
        world_ranking=5,
        player_type=["iron_specialist", "accurate_driver", "ball_striker"],
        driving_distance_pct=70,
        driving_accuracy_pct=85,
        iron_precision_pct=96,
        short_game_pct=72,
        putting_pct=68,
        major_wins=2,
        major_top10s=9,
        course_history={
            "Royal Liverpool":        (1, 2, -15.0),
            "TPC Sawgrass":           (6, 4, -11.0),
        },
        recent_form=[4, 8, 3, 6, 2, 9, 5, 3],
    ),

    "Viktor Hovland": GolfPlayerProfile(
        name="Viktor Hovland",
        world_ranking=6,
        player_type=["big_hitter", "ball_striker", "iron_specialist"],
        driving_distance_pct=90,
        driving_accuracy_pct=62,
        iron_precision_pct=88,
        short_game_pct=65,
        putting_pct=72,
        major_wins=0,
        major_top10s=5,
        course_history={
            "Augusta National":       (12, 4, -6.0),
            "Muirfield Village":      (1, 3, -17.0),
        },
        recent_form=[5, 3, 8, 2, 6, 4, 10, 3],
    ),

    "Ludvig Aberg": GolfPlayerProfile(
        name="Ludvig Aberg",
        world_ranking=7,
        player_type=["big_hitter", "ball_striker", "iron_specialist"],
        driving_distance_pct=92,
        driving_accuracy_pct=70,
        iron_precision_pct=88,
        short_game_pct=75,
        putting_pct=74,
        major_wins=0,
        major_top10s=3,
        course_history={
            "Augusta National":       (2, 2, -11.0),
        },
        recent_form=[3, 7, 2, 5, 4, 8, 2, 6],
    ),

    "Tommy Fleetwood": GolfPlayerProfile(
        name="Tommy Fleetwood",
        world_ranking=9,
        player_type=["links_specialist", "iron_specialist", "wind_player"],
        driving_distance_pct=78,
        driving_accuracy_pct=75,
        iron_precision_pct=90,
        short_game_pct=80,
        putting_pct=76,
        major_wins=0,
        major_top10s=8,
        course_history={
            "Royal Liverpool":        (2, 3, -15.5),
            "Pinehurst No. 2":        (2, 2, -4.0),
            "Augusta National":       (8, 5, -7.5),
        },
        recent_form=[4, 6, 3, 8, 2, 5, 7, 3],
    ),

    "Brooks Koepka": GolfPlayerProfile(
        name="Brooks Koepka",
        world_ranking=10,
        player_type=["big_hitter", "mentally_tough", "major_specialist"],
        driving_distance_pct=90,
        driving_accuracy_pct=60,
        iron_precision_pct=82,
        short_game_pct=78,
        putting_pct=75,
        major_wins=5,
        major_top10s=12,
        course_history={
            "Pinehurst No. 2":        (1, 2, -9.0),
            "Bethpage Black":         (1, 2, -8.0),
            "Valhalla":               (1, 2, -17.0),
            "Augusta National":       (2, 7, -9.0),
        },
        recent_form=[12, 5, 8, 3, 15, 7, 4, 6],
    ),

    "Justin Thomas": GolfPlayerProfile(
        name="Justin Thomas",
        world_ranking=12,
        player_type=["ball_striker", "accurate_driver", "iron_specialist"],
        driving_distance_pct=82,
        driving_accuracy_pct=72,
        iron_precision_pct=88,
        short_game_pct=82,
        putting_pct=80,
        major_wins=2,
        major_top10s=10,
        course_history={
            "Augusta National":       (4, 8, -8.5),
            "TPC Sawgrass":           (1, 6, -14.0),
            "Valhalla":               (2, 3, -15.0),
        },
        recent_form=[8, 12, 5, 9, 4, 7, 11, 6],
    ),

    "Jordan Spieth": GolfPlayerProfile(
        name="Jordan Spieth",
        world_ranking=14,
        player_type=["scrambler", "mentally_tough", "short_game_specialist", "experienced"],
        driving_distance_pct=68,
        driving_accuracy_pct=65,
        iron_precision_pct=78,
        short_game_pct=92,
        putting_pct=90,
        major_wins=3,
        major_top10s=13,
        course_history={
            "Augusta National":       (1, 10, -9.8),
            "St Andrews Old Course":  (1, 3, -19.0),
            "Royal Troon":            (1, 2, -20.0),
        },
        recent_form=[10, 6, 14, 8, 5, 12, 7, 9],
    ),

    "Patrick Cantlay": GolfPlayerProfile(
        name="Patrick Cantlay",
        world_ranking=11,
        player_type=["ball_striker", "iron_specialist", "patient_grinder"],
        driving_distance_pct=78,
        driving_accuracy_pct=78,
        iron_precision_pct=90,
        short_game_pct=82,
        putting_pct=85,
        major_wins=0,
        major_top10s=6,
        course_history={
            "Augusta National":       (6, 5, -8.0),
            "Muirfield Village":      (1, 5, -19.0),
        },
        recent_form=[6, 4, 9, 3, 7, 5, 8, 4],
    ),

    "Hideki Matsuyama": GolfPlayerProfile(
        name="Hideki Matsuyama",
        world_ranking=13,
        player_type=["ball_striker", "iron_specialist", "creative_shotmaker"],
        driving_distance_pct=82,
        driving_accuracy_pct=62,
        iron_precision_pct=88,
        short_game_pct=72,
        putting_pct=70,
        major_wins=1,
        major_top10s=8,
        course_history={
            "Augusta National":       (1, 8, -9.2),
            "TPC Sawgrass":           (5, 6, -12.0),
        },
        recent_form=[7, 5, 3, 11, 6, 4, 9, 5],
    ),

    "Max Homa": GolfPlayerProfile(
        name="Max Homa",
        world_ranking=15,
        player_type=["accurate_driver", "iron_specialist", "ball_striker"],
        driving_distance_pct=76,
        driving_accuracy_pct=82,
        iron_precision_pct=85,
        short_game_pct=78,
        putting_pct=74,
        major_wins=0,
        major_top10s=3,
        course_history={
            "Augusta National":       (14, 4, -6.0),
            "Riviera Country Club":   (1, 5, -16.0),
        },
        recent_form=[9, 5, 12, 6, 8, 4, 11, 7],
    ),

    "Shane Lowry": GolfPlayerProfile(
        name="Shane Lowry",
        world_ranking=18,
        player_type=["links_specialist", "wind_player", "scrambler", "mentally_tough"],
        driving_distance_pct=75,
        driving_accuracy_pct=70,
        iron_precision_pct=82,
        short_game_pct=85,
        putting_pct=78,
        major_wins=1,
        major_top10s=7,
        course_history={
            "Royal Portrush":         (1, 2, -15.0),
            "St Andrews Old Course":  (4, 4, -16.0),
            "Augusta National":       (10, 6, -7.0),
        },
        recent_form=[8, 4, 6, 12, 5, 9, 3, 7],
    ),
}


# ── Fit scoring engine ─────────────────────────────────────────────────────────

def score_player_course_fit(player: GolfPlayerProfile,
                             course: CourseProfile) -> tuple[float, list[str]]:
    """
    Returns (fit_score 0-100, rationale_list).
    Weights player stat percentiles against course skill weights.
    """
    rationale = []

    # Weighted skill score
    skill_score = (
        player.driving_distance_pct * course.driving_distance_weight +
        player.driving_accuracy_pct * course.driving_accuracy_weight +
        player.iron_precision_pct   * course.iron_precision_weight   +
        player.short_game_pct       * course.short_game_weight       +
        player.putting_pct          * course.putting_weight
    )

    # Player type match bonus (up to +8 pts)
    type_overlap = len(set(player.player_type) & set(course.favors))
    type_bonus = type_overlap * 4.0
    if type_overlap > 0:
        matched = set(player.player_type) & set(course.favors)
        rationale.append(f"Player type match: {', '.join(matched)} (+{type_bonus:.0f}pts)")

    # Course history bonus (up to +6 pts)
    history_bonus = 0.0
    if course.name in player.course_history:
        best_finish, times_played, avg_score = player.course_history[course.name]
        if best_finish == 1:
            history_bonus += 6.0
            rationale.append(f"Won here before (best: {best_finish}) — +6pts")
        elif best_finish <= 5:
            history_bonus += 4.0
            rationale.append(f"Top-5 history here (best: T{best_finish}) — +4pts")
        elif best_finish <= 10:
            history_bonus += 2.0
            rationale.append(f"Top-10 history here (best: T{best_finish}) — +2pts")
        if times_played >= 4:
            history_bonus += 1.0
            rationale.append(f"Course veteran ({times_played} appearances) — +1pt")

    # Major experience bonus (up to +4 pts)
    major_bonus = min(4.0, player.major_wins * 2.0 + player.major_top10s * 0.2)
    if major_bonus > 1:
        rationale.append(f"Major pedigree: {player.major_wins}W / {player.major_top10s} top-10s — +{major_bonus:.1f}pts")

    # Recent form score (last 8 events)
    form_bonus = 0.0
    if player.recent_form:
        avg_finish = sum(player.recent_form) / len(player.recent_form)
        if avg_finish <= 5:
            form_bonus = 5.0
            rationale.append(f"Red-hot form (avg finish {avg_finish:.1f}) — +5pts")
        elif avg_finish <= 10:
            form_bonus = 3.0
            rationale.append(f"Good form (avg finish {avg_finish:.1f}) — +3pts")
        elif avg_finish <= 20:
            form_bonus = 1.0

    # Fitness penalty
    fitness_penalty = 0.0
    if player.fitness_flag == "minor":
        fitness_penalty = -3.0
        rationale.append("Minor fitness concern — -3pts")
    elif player.fitness_flag == "doubtful":
        fitness_penalty = -8.0
        rationale.append("Doubtful fitness — -8pts")

    # Prep notes bonus (manually set, up to +5 pts)
    prep_bonus = 0.0
    if player.prep_notes:
        for note in player.prep_notes:
            prep_bonus += 2.5
            rationale.append(f"Prep intel: {note} — +2.5pts")
        prep_bonus = min(prep_bonus, 5.0)

    total = skill_score + type_bonus + history_bonus + major_bonus + form_bonus + fitness_penalty + prep_bonus
    total = max(0.0, min(100.0, total))

    return round(total, 1), rationale


# ── Market edge calculator ─────────────────────────────────────────────────────

def american_to_implied(odds: int) -> float:
    """Convert American odds to implied win probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def _prob_to_american(prob: float) -> int:
    """Convert a probability to American odds."""
    prob = max(0.001, min(0.999, prob))
    decimal = 1 / prob
    if decimal >= 2:
        return int((decimal - 1) * 100)
    else:
        return int(-100 / (decimal - 1))


def fit_to_finish_prob(fit_score: float, field_size: int, top_n: int) -> float:
    """
    Estimate P(finish in top N) given a player's fit score and field size.

    Logic: fit score maps to an expected finishing position.
      - fit 100 → expected position ≈ top 8% of field  (elite performer)
      - fit  80 → expected position ≈ top 20% of field
      - fit  60 → expected position ≈ top 38% of field
      - fit  40 → expected position ≈ top 58% of field (below average)

    P(top_N) = N / expected_position  (capped at 0.90)
    """
    # Map fit_score [0,100] → expected_rank percentile [0.92, 0.08]
    # Linear: fit=100 → pct=0.08, fit=0 → pct=0.92
    pct = 0.92 - (fit_score / 100) * 0.84
    expected_rank = max(1, pct * field_size)
    raw_prob = top_n / expected_rank
    return min(0.90, raw_prob)


def fit_to_fair_odds(fit_score: float, field_size: int = 156,
                     bet_type: str = "WIN") -> int:
    """
    Convert fit score + bet type to fair American odds.
    """
    top_n_map = {"WIN": 1, "TOP5": 5, "TOP10": 10, "TOP20": 20, "MAKE_CUT": field_size // 2}
    top_n = top_n_map.get(bet_type, 1)
    prob  = fit_to_finish_prob(fit_score, field_size, top_n)
    return _prob_to_american(prob)


@dataclass
class GolfPick:
    player:         str
    tournament:     str
    course:         str
    fit_score:      float
    market_odds:    int      # American odds at book
    fair_odds:      int      # model's fair value
    implied_prob:   float    # book's implied win %
    fair_prob:      float    # model's fair win %
    edge:           float    # fair_prob - implied_prob
    recommendation: str      # "WIN","TOP5","TOP10","TOP20","MAKE_CUT"
    rationale:      list[str]
    prep_notes:     list[str]
    kelly_fraction: float


def analyse_golfer(player_name: str, course_name: str,
                   market_odds: int, bet_type: str = "WIN",
                   field_size: int = 156) -> Optional[GolfPick]:
    """
    Full analysis of a player at a course vs market odds.
    Returns a GolfPick if there's value, None if not.
    """
    player = PLAYER_PROFILES.get(player_name)
    course = COURSE_PROFILES.get(course_name)

    if not player or not course:
        return None

    if player.fitness_flag == "out":
        return None

    fit_score, rationale = score_player_course_fit(player, course)

    fair_odds  = fit_to_fair_odds(fit_score, field_size, bet_type)
    fair_prob  = american_to_implied(fair_odds)
    book_prob  = american_to_implied(market_odds)
    edge       = fair_prob - book_prob

    # Only return pick if there's meaningful edge (>2%)
    if edge < 0.02:
        return None

    # Quarter-Kelly
    if market_odds > 0:
        b = market_odds / 100
    else:
        b = 100 / abs(market_odds)
    kelly = max(0.0, (b * fair_prob - (1 - fair_prob)) / b) * 0.25

    return GolfPick(
        player=player_name,
        tournament=course.tournament,
        course=course_name,
        fit_score=fit_score,
        market_odds=market_odds,
        fair_odds=fair_odds,
        implied_prob=round(book_prob, 4),
        fair_prob=round(fair_prob, 4),
        edge=round(edge, 4),
        recommendation=bet_type,
        rationale=rationale,
        prep_notes=player.prep_notes,
        kelly_fraction=round(kelly, 4),
    )


def format_golf_pick(pick: GolfPick, bankroll: float = 1000.0) -> str:
    """Formats a GolfPick as a bet slip."""
    bar_fill = min(10, round(pick.fit_score / 10))
    conf_bar = "█" * bar_fill + "░" * (10 - bar_fill)
    stake    = pick.kelly_fraction * bankroll
    odds_str = f"+{pick.market_odds}" if pick.market_odds > 0 else str(pick.market_odds)
    fair_str = f"+{pick.fair_odds}" if pick.fair_odds > 0 else str(pick.fair_odds)

    if pick.fit_score >= 80:
        tier = "⭐ STRONG VALUE"
    elif pick.fit_score >= 65:
        tier = "VALUE"
    else:
        tier = "SPECULATIVE"

    sep = "  " + "─" * 56
    lines = [
        sep,
        f"  ┌─ BET SLIP [GOLF] ─────────────────────────────────",
        f"  │  {pick.player} — {pick.recommendation}",
        f"  │  {pick.tournament} @ {pick.course}",
        f"  │  {tier}   Fit Score: {pick.fit_score}/100  [{conf_bar}]",
        f"  │",
        f"  ├─ WHY THIS BET ─────────────────────────────────────────",
    ]
    for r in pick.rationale:
        lines.append(f"  │  • {r}")
    if pick.prep_notes:
        lines.append(f"  │")
        lines.append(f"  ├─ PREP / NEWS INTEL ────────────────────────────────")
        for n in pick.prep_notes:
            lines.append(f"  │  ★ {n}")
    lines += [
        f"  │",
        f"  ├─ ODDS & EDGE ──────────────────────────────────────",
        f"  │  Market: {odds_str}  (implied {pick.implied_prob:.1%})",
        f"  │  Fair:   {fair_str}  (model   {pick.fair_prob:.1%})",
        f"  │  Edge:   +{pick.edge:.1%} in your favour",
        f"  │",
        f"  ├─ STAKE (¼-Kelly on ${bankroll:,.0f} bankroll) ─────────────",
        f"  │  Bet: ${stake:.2f}  ({pick.kelly_fraction*100:.2f}% of roll)",
        f"  │  Win: ${stake * (pick.market_odds/100 if pick.market_odds > 0 else 100/abs(pick.market_odds)):.2f} profit",
        f"  └────────────────────────────────────────────────────────",
    ]
    return "\n".join(lines)


def scan_tournament(
    course_name:  str,
    player_odds:  dict[str, int],
    top5_odds:    Optional[dict[str, int]] = None,
    top10_odds:   Optional[dict[str, int]] = None,
    top20_odds:   Optional[dict[str, int]] = None,
    bankroll:     float = 1000.0,
) -> list[GolfPick]:
    """
    Scan all players across all four bet types (WIN, TOP5, TOP10, TOP20).
    Returns all value picks sorted by edge descending.
    Pass odds dicts from fetch_golf_odds() for automatic live odds.
    """
    course = COURSE_PROFILES.get(course_name)
    if not course:
        return []

    field_size = max(len(player_odds), 70)  # major fields are typically 156
    all_picks: list[GolfPick] = []

    markets = [
        ("WIN",   player_odds),
        ("TOP5",  top5_odds  or {}),
        ("TOP10", top10_odds or {}),
        ("TOP20", top20_odds or {}),
    ]

    seen: set[tuple[str, str]] = set()  # (player, bet_type) dedup

    for bet_type, odds_dict in markets:
        for player_name, odds in odds_dict.items():
            key = (player_name, bet_type)
            if key in seen:
                continue
            seen.add(key)
            pick = analyse_golfer(player_name, course_name, odds, bet_type, field_size)
            if pick:
                all_picks.append(pick)

    all_picks.sort(key=lambda p: p.edge, reverse=True)
    return all_picks


def update_prep_notes(player_name: str, notes: list[str]) -> None:
    """Add prep/news intel to a player before a tournament."""
    if player_name in PLAYER_PROFILES:
        PLAYER_PROFILES[player_name].prep_notes = notes


# ── Active tournaments ─────────────────────────────────────────────────────────
# Populated externally (or manually) before each event.
# Each entry: {"name": str, "course": str, "player_odds": {player: american_odds}}
# The cron_entry.py _golf_section() reads this list each morning.
# Example:
#   ACTIVE_TOURNAMENTS = [
#       {
#           "name": "The Open Championship",
#           "course": "Royal Liverpool",
#           "player_odds": {
#               "Rory McIlroy": +600,
#               "Scottie Scheffler": +350,
#               ...
#           }
#       }
#   ]
ACTIVE_TOURNAMENTS: list[dict] = []
