"""
Sunday NFL Parlay Builder
=========================
Every Sunday during the NFL season generates three tiered parlays from that
day's NFL picks: Safe (2-leg), Moderate (3-leg), and Risky (4-5-leg).

Parlay math:
  - Each leg is priced at -110 unless a spread/total line differs.
  - Parlay payout = product of each leg's decimal odds.
  - American -110  → decimal 1.909
  - We estimate true win probability for each leg from the model's confidence,
    then compute the parlay's combined probability and expected value.

Risk tiers:
  SAFE     — 2 legs, both ≥ 0.58 confidence (implied ~72% parlay hit rate)
  MODERATE — 3 legs, all  ≥ 0.52 confidence (implied ~56% parlay hit rate)
  RISKY    — 4-5 legs, all ≥ 0.45 confidence (implied ~40-50% parlay hit rate)

If we don't have enough legs in a tier we drop down gracefully: e.g., if only
2 qualifying picks exist, we output Safe and Moderate but skip Risky.
"""

from __future__ import annotations
import math
from typing import Optional
from dataclasses import dataclass

from bonus_pick import BonusPickOutput


# Decimal odds for a standard -110 line
_DEC_110 = 1.0 / 1.1 + 1.0   # ≈ 1.9091


@dataclass
class ParlayLeg:
    description:  str     # e.g. "Kansas City Chiefs -3.5"
    team_or_side: str     # short label
    lean:         str
    confidence:   float   # model's win probability estimate for this leg
    decimal_odds: float   # payout multiplier (1.909 for -110)


@dataclass
class Parlay:
    tier:          str          # "SAFE", "MODERATE", "RISKY"
    legs:          list[ParlayLeg]
    combined_prob: float        # product of individual win probs
    payout_odds:   float        # decimal parlay payout (e.g. 3.64x for 2-leg -110)
    ev:            float        # expected value per $100 bet
    recommendation: str         # "BET" or "SKIP"


# Confidence floor per tier
_TIER_CONF = {
    "SAFE":     0.58,
    "MODERATE": 0.52,
    "RISKY":    0.45,
}

_TIER_LEGS = {
    "SAFE":     2,
    "MODERATE": 3,
    "RISKY":    (4, 5),   # range
}


def _leg_from_pick(pick: BonusPickOutput) -> ParlayLeg:
    ev = pick.event
    spread = ev.best_spread_home

    if pick.lean in ("HOME", "AWAY"):
        if pick.lean == "HOME" and spread is not None:
            side = ev.home_team
            line = f"{ev.home_team} {spread:+.1f}"
        elif pick.lean == "AWAY" and spread is not None:
            away_spread = -spread if spread else None
            side = ev.away_team
            line = f"{ev.away_team} {away_spread:+.1f}" if away_spread is not None else ev.away_team
        else:
            side = ev.home_team if pick.lean == "HOME" else ev.away_team
            line = side
    else:
        total = ev.best_total or 47.0
        side = f"{pick.lean} {total}"
        line = f"{pick.lean} {total}"

    return ParlayLeg(
        description  = line,
        team_or_side = side,
        lean         = pick.lean,
        confidence   = pick.confidence,
        decimal_odds = _DEC_110,
    )


def _build_parlay(legs: list[ParlayLeg], tier: str) -> Parlay:
    combined_prob = math.prod(leg.confidence for leg in legs)
    payout_odds   = math.prod(leg.decimal_odds for leg in legs)
    # EV = P(win) × profit − P(lose) × stake (per $100)
    ev = combined_prob * (payout_odds - 1) * 100 - (1 - combined_prob) * 100

    recommendation = "BET" if ev > 0 and combined_prob >= 0.35 else "SKIP"

    return Parlay(
        tier           = tier,
        legs           = legs,
        combined_prob  = round(combined_prob, 3),
        payout_odds    = round(payout_odds, 3),
        ev             = round(ev, 2),
        recommendation = recommendation,
    )


def build_sunday_parlays(nfl_picks: list[BonusPickOutput]) -> list[Parlay]:
    """
    Given today's NFL picks (already scored, sorted by confidence desc),
    constructs up to three tiered parlays. Returns only parlays with enough
    qualifying legs — never pads with low-confidence legs.
    """
    parlays: list[Parlay] = []

    # Convert picks to legs once
    all_legs = [_leg_from_pick(p) for p in nfl_picks]

    for tier, min_conf in _TIER_CONF.items():
        qualifying = [l for l in all_legs if l.confidence >= min_conf]

        if tier == "RISKY":
            target_min, target_max = _TIER_LEGS["RISKY"]
            if len(qualifying) < target_min:
                continue
            legs = qualifying[:target_max]
        else:
            target = _TIER_LEGS[tier]
            if len(qualifying) < target:
                continue
            legs = qualifying[:target]

        parlays.append(_build_parlay(legs, tier))

    return parlays


def format_sunday_parlays(parlays: list[Parlay]) -> str:
    """Returns a formatted string for the Sunday parlay section."""
    sep = "=" * 56
    lines = [
        "",
        sep,
        "  🏈  SUNDAY NFL PARLAYS  —  3 TIERS",
        sep,
        "  Model builds these from today's highest-confidence NFL legs.",
        "  Pick the risk level that fits your bankroll.",
        "",
    ]

    if not parlays:
        lines += [
            "  Not enough qualifying NFL picks today to build parlays.",
            "  (Need at least 2 legs at 45%+ confidence.)",
            sep,
        ]
        return "\n".join(lines)

    tier_emoji = {"SAFE": "🟢", "MODERATE": "🟡", "RISKY": "🔴"}

    for p in parlays:
        emoji = tier_emoji.get(p.tier, "")
        lines += [
            f"  {emoji}  {p.tier} PARLAY  ({len(p.legs)}-leg)",
            f"  {'─' * 50}",
        ]
        for i, leg in enumerate(p.legs, 1):
            conf_pct = f"{leg.confidence:.0%}"
            lines.append(f"    Leg {i}: {leg.description:<30s}  ({conf_pct} conf)")
        lines += [
            f"",
            f"  Combined hit prob: {p.combined_prob:.0%}",
            f"  Payout:  {p.payout_odds:.2f}x  (${p.payout_odds * 100:.0f} on $100)",
            f"  EV:      {'+' if p.ev >= 0 else ''}{p.ev:.2f} per $100",
            f"  → {p.recommendation}",
            "",
        ]

    lines.append(sep)
    lines += [
        "  PARLAY NOTES:",
        "  • SAFE: lower payout, highest probability — best for steady bankroll",
        "  • MODERATE: balanced risk/reward — the main Sunday play",
        "  • RISKY: lottery ticket; only if you're comfortable losing the stake",
        "  • Never bet more than 2-3% of bankroll on any single parlay",
        sep,
    ]
    return "\n".join(lines)
