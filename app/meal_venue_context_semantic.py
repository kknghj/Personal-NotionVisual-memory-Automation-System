"""Meeting context vs embedded meal/venue action semantic boundary (Pilot B)."""

from __future__ import annotations

from typing import Any

from app.workflow_resolution import _canonical_title_text

FOOD_MEETING_ID = "food_meeting"
MEETING_ID = "meeting"
MEAL_VENUE_ACTION_TERMS: tuple[str, ...] = (
    "오찬",
    "식사",
    "식당",
    "장소정하기",
    "점심약속",
)
MEAL_VENUE_SOFT_BONUS = 6
MEETING_CONTEXT_PENALTY = 6


def _canonical(title: str) -> str:
    return _canonical_title_text(title)


def title_has_meal_venue_with_meeting_context(title: str) -> bool:
    canonical = _canonical(title)
    if "회의" not in canonical:
        return False
    return any(term in canonical for term in MEAL_VENUE_ACTION_TERMS)


def meal_venue_boundary_active(title: str) -> bool:
    return title_has_meal_venue_with_meeting_context(title)


def meal_venue_injection_match(title: str) -> tuple[str, int, int]:
    canonical = _canonical(title)
    for pattern in sorted(MEAL_VENUE_ACTION_TERMS, key=len, reverse=True):
        pos = canonical.find(pattern)
        if pos >= 0:
            return pattern, pos, len(pattern)
    return "오찬", canonical.find("회의"), 2


def meal_venue_context_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    if not candidate_id:
        return score, reasons, fields
    if not meal_venue_boundary_active(title):
        return score, reasons, fields

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if candidate_id == FOOD_MEETING_ID:
        bonus += MEAL_VENUE_SOFT_BONUS
        adj_reasons.append("meal_venue context action soft boost food_meeting")
    if candidate_id == MEETING_ID:
        penalty += MEETING_CONTEXT_PENALTY
        adj_reasons.append("meal_venue context action demotes meeting")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)
