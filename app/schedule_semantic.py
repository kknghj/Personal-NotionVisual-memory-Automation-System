"""Schedule/date verification vs generic document review (Metadata Pilot M2-A)."""

from __future__ import annotations

from typing import Any

from app.workflow_resolution import _canonical_title_text

WORK_CALENDAR_ORGANIZATION_ID = "work_calendar_organization"
DEADLINE_MANAGEMENT_ID = "deadline_management"
SCHEDULE_CANDIDATE_IDS = frozenset(
    {
        WORK_CALENDAR_ORGANIZATION_ID,
        DEADLINE_MANAGEMENT_ID,
    }
)
GENERIC_REVIEW_CANDIDATE_IDS = frozenset(
    {
        "document_review",
        "slide_deck_final_review",
    }
)

DATE_VERIFICATION_TERMS: frozenset[str] = frozenset(
    {
        "종료일",
        "할인종료일",
        "마감일",
        "신청마감일",
        "제작시기",
        "시기",
        "기간",
    }
)
DEADLINE_VERIFICATION_TERMS: frozenset[str] = frozenset(
    {
        "마감일",
        "신청마감일",
        "혜택마감",
    }
)
DOCUMENT_OBJECT_BLOCKER_TERMS: frozenset[str] = frozenset(
    {
        "공문",
        "문서",
        "자료",
        "신청서",
        "결과보고",
        "보고서",
    }
)
CONFIRM_ACTION_TERM = "확인"

SCHEDULE_SOFT_BONUS = 12
GENERIC_REVIEW_PENALTY = 8


def schedule_date_verification_anchor_active(title: str) -> bool:
    """True when a date/deadline term and 확인 co-occur without a document object anchor."""
    canonical = _canonical_title_text(title)
    if CONFIRM_ACTION_TERM not in canonical:
        return False
    if not any(term in canonical for term in DATE_VERIFICATION_TERMS):
        return False
    return not any(term in canonical for term in DOCUMENT_OBJECT_BLOCKER_TERMS)


def _schedule_intent_value(canonical: str) -> str:
    if any(term in canonical for term in DEADLINE_VERIFICATION_TERMS):
        return "deadline_verification"
    return "date_verification"


def refine_schedule_title_signals(
    canonical: str,
    signals: dict[str, set[str]],
) -> None:
    """Add schedule verification signals and suppress generic document-review cues."""
    if not schedule_date_verification_anchor_active_from_canonical(canonical):
        return

    intent = _schedule_intent_value(canonical)
    signals["primary_object"] = {"date_time"}
    signals["workflow_fit"] = {"time_scheduling"}
    signals["schedule_intent"] = {intent}
    if intent == "deadline_verification":
        signals["object_type"] = {"deadline_date"}
        signals["interaction_mode"] = {"check_deadline"}
    else:
        signals["object_type"] = {"calendar_date"}
        signals["interaction_mode"] = {"check_schedule"}

    signals.get("document_flow_stage", set()).discard("review")
    signals.get("interaction_mode", set()).discard("review_confirm")
    signals.get("interaction_mode", set()).discard("status_monitor")


def schedule_date_verification_anchor_active_from_canonical(canonical: str) -> bool:
    if CONFIRM_ACTION_TERM not in canonical:
        return False
    if not any(term in canonical for term in DATE_VERIFICATION_TERMS):
        return False
    return not any(term in canonical for term in DOCUMENT_OBJECT_BLOCKER_TERMS)


def schedule_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    if not candidate_id or not schedule_date_verification_anchor_active(title):
        return score, reasons, fields

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if candidate_id in SCHEDULE_CANDIDATE_IDS:
        bonus += SCHEDULE_SOFT_BONUS
        adj_reasons.append("schedule date verification soft boost")
    elif candidate_id in GENERIC_REVIEW_CANDIDATE_IDS:
        penalty += GENERIC_REVIEW_PENALTY
        adj_reasons.append("schedule date verification generic review soft penalty")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)


def withhold_schedule_review_boost(title: str) -> bool:
    """Whether reporting/review soft boosts should not apply to generic review rows."""
    return schedule_date_verification_anchor_active(title)
