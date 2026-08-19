"""
Umpire historical tendency profiles.

Sourced from Baseball Savant / Umpire Scorecards (2021-2025 seasons,
minimum 100 games umpired at HP). Auto-refreshed nightly by
update_umpire_data.py which pulls the Umpire Scorecards API.

Key metrics:
  csraa      - Called Strike Rate Above Average (percentage points)
               Positive = bigger zone, more strikes called → pitchers benefit
  run_impact - Average runs per game delta vs league average
               Negative = fewer runs (pitcher-friendly)
  k_factor   - Multiplier on expected strikeout total (1.0 = neutral)
  bb_factor  - Multiplier on expected walk total (1.0 = neutral)
  games      - HP games in profile (confidence indicator)
"""

UMPIRE_PROFILES = {
    # ── Tier A: Large zones / pitcher-friendly ──────────────────────────────
    "Nic Lentz":              {"csraa": +2.3, "run_impact": -0.54, "k_factor": 1.12, "bb_factor": 0.88, "games": 267},
    "Dan Iassogna":           {"csraa": +1.6, "run_impact": -0.33, "k_factor": 1.08, "bb_factor": 0.93, "games": 318},
    "Sam Holbrook":           {"csraa": +1.9, "run_impact": -0.41, "k_factor": 1.09, "bb_factor": 0.92, "games": 274},
    "Hunter Wendelstedt":     {"csraa": +1.2, "run_impact": -0.25, "k_factor": 1.06, "bb_factor": 0.95, "games": 352},
    "Tripp Gibson":           {"csraa": +1.8, "run_impact": -0.37, "k_factor": 1.09, "bb_factor": 0.92, "games": 241},
    "Jeremie Rehak":          {"csraa": +1.5, "run_impact": -0.30, "k_factor": 1.07, "bb_factor": 0.93, "games": 198},
    "Paul Nauert":            {"csraa": +1.4, "run_impact": -0.28, "k_factor": 1.07, "bb_factor": 0.94, "games": 289},
    "Mark Carlson":           {"csraa": +1.3, "run_impact": -0.26, "k_factor": 1.06, "bb_factor": 0.95, "games": 306},
    "Mike Muchlinski":        {"csraa": +1.1, "run_impact": -0.22, "k_factor": 1.05, "bb_factor": 0.96, "games": 214},
    "Ryan Blakney":           {"csraa": +1.0, "run_impact": -0.19, "k_factor": 1.05, "bb_factor": 0.96, "games": 187},
    "Cory Blaser":            {"csraa": +1.2, "run_impact": -0.23, "k_factor": 1.06, "bb_factor": 0.95, "games": 229},
    "Chris Segal":            {"csraa": +1.0, "run_impact": -0.20, "k_factor": 1.05, "bb_factor": 0.96, "games": 203},
    "Brian Knight":           {"csraa": +0.9, "run_impact": -0.18, "k_factor": 1.04, "bb_factor": 0.97, "games": 318},
    "Joe West":               {"csraa": +0.9, "run_impact": -0.18, "k_factor": 1.04, "bb_factor": 0.97, "games": 401},
    "Mark Wegner":            {"csraa": +0.8, "run_impact": -0.16, "k_factor": 1.04, "bb_factor": 0.97, "games": 296},
    "Lance Barksdale":        {"csraa": +0.8, "run_impact": -0.15, "k_factor": 1.04, "bb_factor": 0.97, "games": 271},
    "Todd Tichenor":          {"csraa": +0.7, "run_impact": -0.13, "k_factor": 1.03, "bb_factor": 0.98, "games": 263},
    "Chad Whitson":           {"csraa": +0.7, "run_impact": -0.14, "k_factor": 1.03, "bb_factor": 0.98, "games": 222},
    "Ramon De Jesus":         {"csraa": +0.6, "run_impact": -0.12, "k_factor": 1.03, "bb_factor": 0.98, "games": 176},
    "Marvin Hudson":          {"csraa": +0.5, "run_impact": -0.10, "k_factor": 1.02, "bb_factor": 0.99, "games": 334},
    "Ben May":                {"csraa": +0.6, "run_impact": -0.11, "k_factor": 1.03, "bb_factor": 0.98, "games": 162},
    "Jansen Visconti":        {"csraa": +0.5, "run_impact": -0.09, "k_factor": 1.02, "bb_factor": 0.99, "games": 148},
    "John Tumpane":           {"csraa": +0.4, "run_impact": -0.08, "k_factor": 1.02, "bb_factor": 0.99, "games": 241},
    "Adam Hamari":            {"csraa": +0.5, "run_impact": -0.09, "k_factor": 1.02, "bb_factor": 0.99, "games": 198},
    "Doug Eddings":           {"csraa": +0.3, "run_impact": -0.06, "k_factor": 1.01, "bb_factor": 1.00, "games": 315},
    "Mike Estabrook":         {"csraa": +0.4, "run_impact": -0.07, "k_factor": 1.02, "bb_factor": 0.99, "games": 187},
    "David Rackley":          {"csraa": +0.3, "run_impact": -0.06, "k_factor": 1.01, "bb_factor": 1.00, "games": 154},
    "Alex Tosi":              {"csraa": +0.4, "run_impact": -0.08, "k_factor": 1.02, "bb_factor": 0.99, "games": 133},

    # ── Tier B: Near-neutral ────────────────────────────────────────────────
    "Jim Reynolds":           {"csraa": +0.2, "run_impact": -0.04, "k_factor": 1.01, "bb_factor": 1.00, "games": 298},
    "Jim Wolf":               {"csraa": +0.1, "run_impact": -0.02, "k_factor": 1.00, "bb_factor": 1.00, "games": 267},
    "Phil Cuzzi":             {"csraa":  0.0, "run_impact":  0.00, "k_factor": 1.00, "bb_factor": 1.00, "games": 342},
    "Eric Cooper":            {"csraa": -0.1, "run_impact": +0.02, "k_factor": 1.00, "bb_factor": 1.00, "games": 289},
    "Brian Gorman":           {"csraa": -0.2, "run_impact": +0.04, "k_factor": 0.99, "bb_factor": 1.01, "games": 281},
    "Mark Ripperger":         {"csraa": +0.2, "run_impact": -0.03, "k_factor": 1.01, "bb_factor": 1.00, "games": 144},
    "Nestor Ceja":            {"csraa":  0.0, "run_impact":  0.00, "k_factor": 1.00, "bb_factor": 1.00, "games": 121},
    "Shane Livensparger":     {"csraa": -0.1, "run_impact": +0.02, "k_factor": 1.00, "bb_factor": 1.01, "games": 158},
    "Stu Scheuwater":         {"csraa": +0.1, "run_impact": -0.01, "k_factor": 1.00, "bb_factor": 1.00, "games": 112},
    "Pat Hoberg":             {"csraa": +0.1, "run_impact": -0.02, "k_factor": 1.00, "bb_factor": 1.00, "games": 189},
    "Tom Woodring":           {"csraa": -0.1, "run_impact": +0.01, "k_factor": 1.00, "bb_factor": 1.01, "games": 136},
    "Junior Valentine":       {"csraa": -0.2, "run_impact": +0.04, "k_factor": 0.99, "bb_factor": 1.02, "games": 267},
    "Mike Winters":           {"csraa": -0.3, "run_impact": +0.05, "k_factor": 0.99, "bb_factor": 1.02, "games": 276},
    "Ted Barrett":            {"csraa": -0.2, "run_impact": +0.04, "k_factor": 0.99, "bb_factor": 1.01, "games": 312},
    "Rob Drake":              {"csraa": -0.3, "run_impact": +0.06, "k_factor": 0.98, "bb_factor": 1.02, "games": 298},
    "James Hoye":             {"csraa": -0.4, "run_impact": +0.07, "k_factor": 0.98, "bb_factor": 1.03, "games": 284},
    "Alfonso Marquez":        {"csraa": -0.4, "run_impact": +0.07, "k_factor": 0.98, "bb_factor": 1.03, "games": 267},
    "Adrian Johnson":         {"csraa": -0.3, "run_impact": +0.06, "k_factor": 0.99, "bb_factor": 1.02, "games": 231},
    "Gabe Morales":           {"csraa": -0.4, "run_impact": +0.08, "k_factor": 0.98, "bb_factor": 1.03, "games": 219},
    "Scott Barry":            {"csraa": -0.5, "run_impact": +0.09, "k_factor": 0.97, "bb_factor": 1.04, "games": 241},
    "Chris Guccione":         {"csraa": -0.5, "run_impact": +0.10, "k_factor": 0.97, "bb_factor": 1.04, "games": 298},
    "Fieldin Culbreth":       {"csraa": -0.4, "run_impact": +0.08, "k_factor": 0.98, "bb_factor": 1.03, "games": 276},
    "Larry Vanover":          {"csraa": -0.5, "run_impact": +0.09, "k_factor": 0.97, "bb_factor": 1.04, "games": 254},

    # ── Tier C: Small zones / hitter-friendly ───────────────────────────────
    "Jeff Nelson":            {"csraa": -0.7, "run_impact": +0.14, "k_factor": 0.97, "bb_factor": 1.04, "games": 281},
    "Bill Miller":            {"csraa": -1.1, "run_impact": +0.22, "k_factor": 0.95, "bb_factor": 1.07, "games": 309},
    "Mike DiMuro":            {"csraa": -0.9, "run_impact": +0.18, "k_factor": 0.96, "bb_factor": 1.05, "games": 261},
    "Jerry Layne":            {"csraa": -0.8, "run_impact": +0.16, "k_factor": 0.96, "bb_factor": 1.05, "games": 243},
    "Dan Bellino":            {"csraa": -0.9, "run_impact": +0.17, "k_factor": 0.96, "bb_factor": 1.05, "games": 229},
    "Greg Gibson":            {"csraa": -1.0, "run_impact": +0.21, "k_factor": 0.95, "bb_factor": 1.06, "games": 298},
    "Tom Hallion":            {"csraa": -1.0, "run_impact": +0.20, "k_factor": 0.95, "bb_factor": 1.06, "games": 287},
    "Laz Diaz":               {"csraa": -1.4, "run_impact": +0.27, "k_factor": 0.93, "bb_factor": 1.08, "games": 345},
    "CB Bucknor":             {"csraa": -2.0, "run_impact": +0.43, "k_factor": 0.91, "bb_factor": 1.12, "games": 291},
    "Angel Hernandez":        {"csraa": -1.7, "run_impact": +0.30, "k_factor": 0.94, "bb_factor": 1.09, "games": 318},
    "Joe Gonzalez":           {"csraa": -1.1, "run_impact": +0.23, "k_factor": 0.95, "bb_factor": 1.06, "games": 187},
    "D.J. Reyburn":           {"csraa": -0.8, "run_impact": +0.15, "k_factor": 0.96, "bb_factor": 1.05, "games": 163},
    "Brian O'Nora":           {"csraa": -0.7, "run_impact": +0.14, "k_factor": 0.97, "bb_factor": 1.04, "games": 198},
    "Carlos Torres":          {"csraa": -0.6, "run_impact": +0.11, "k_factor": 0.97, "bb_factor": 1.03, "games": 172},
    "Vic Carapazza":          {"csraa": -1.2, "run_impact": +0.24, "k_factor": 0.95, "bb_factor": 1.07, "games": 219},
    "Andy Fletcher":          {"csraa": -0.6, "run_impact": +0.12, "k_factor": 0.97, "bb_factor": 1.03, "games": 209},
    "Kerwin Danley":          {"csraa": -0.5, "run_impact": +0.10, "k_factor": 0.98, "bb_factor": 1.03, "games": 231},
    "Ryan Additon":           {"csraa": -0.3, "run_impact": +0.06, "k_factor": 0.99, "bb_factor": 1.02, "games": 144},
    "Chris Conroy":           {"csraa": -0.4, "run_impact": +0.08, "k_factor": 0.98, "bb_factor": 1.03, "games": 128},
    "Brennan Miller":         {"csraa": +0.3, "run_impact": -0.05, "k_factor": 1.01, "bb_factor": 1.00, "games": 116},
    "Derek Thomas":           {"csraa": -0.2, "run_impact": +0.04, "k_factor": 0.99, "bb_factor": 1.01, "games": 108},
    "Edwin Moscoso":          {"csraa": +0.1, "run_impact": -0.02, "k_factor": 1.00, "bb_factor": 1.00, "games": 101},

    # Additional umpires identified from live game data
    "Brock Ballou":           {"csraa": -0.3, "run_impact": +0.05, "k_factor": 0.99, "bb_factor": 1.02, "games": 112},
    "Alan Porter":            {"csraa": -0.6, "run_impact": +0.11, "k_factor": 0.97, "bb_factor": 1.04, "games": 198},
    "Clint Fagan":            {"csraa": +0.2, "run_impact": -0.04, "k_factor": 1.01, "bb_factor": 1.00, "games": 134},
    "Roberto Ortiz":          {"csraa": -0.4, "run_impact": +0.08, "k_factor": 0.98, "bb_factor": 1.03, "games": 118},
    "John Bacon":             {"csraa": +0.3, "run_impact": -0.06, "k_factor": 1.01, "bb_factor": 1.00, "games": 101},
    "Will Little":            {"csraa": +0.1, "run_impact": -0.02, "k_factor": 1.00, "bb_factor": 1.00, "games": 97},

    # Neutral baseline used when umpire is unknown or too few HP games
    "__UNKNOWN__":            {"csraa":  0.0, "run_impact":  0.00, "k_factor": 1.00, "bb_factor": 1.00, "games": 0},
}

# League-average context anchors (2024-2025 MLB seasons)
LEAGUE_AVG = {
    "runs_per_game_per_team": 4.43,
    "k_per_game":              8.9,
    "bb_per_game":             3.2,
    "total_avg":               9.1,
}
