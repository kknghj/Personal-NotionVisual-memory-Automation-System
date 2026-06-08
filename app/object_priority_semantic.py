"""Physical object priority vs generic document review (Metadata Pilot M1)."""

from __future__ import annotations

from typing import Any

from app.workflow_resolution import _canonical_title_text

PHYSICAL_ITEM_INSPECTION_ID = "physical_item_inspection"
PHYSICAL_OBJECT_TERMS: frozenset[str] = frozenset({"매트리스", "침대"})
PHYSICAL_STATUS_TERMS: frozenset[str] = frozenset({"상태확인", "현황확인"})
GENERIC_REVIEW_CANDIDATE_IDS = frozenset(
    {
        "document_review",
        "slide_deck_final_review",
    }
)
PHYSICAL_ITEM_SOFT_BONUS = 12
GENERIC_REVIEW_PENALTY = 8


def physical_item_inspection_anchor_active(title: str) -> bool:
    """True when whitelisted physical noun and status-check terms co-occur."""
    canonical = _canonical_title_text(title)
    has_physical = any(term in canonical for term in PHYSICAL_OBJECT_TERMS)
    has_status = any(term in canonical for term in PHYSICAL_STATUS_TERMS)
    return has_physical and has_status


def refine_object_priority_title_signals(
    canonical: str,
    signals: dict[str, set[str]],
) -> None:
    """Add physical-item metadata signals and suppress generic document-review cues."""
    if not any(term in canonical for term in PHYSICAL_OBJECT_TERMS):
        return
    if not any(term in canonical for term in PHYSICAL_STATUS_TERMS):
        return

    signals["primary_object"] = {"physical_item"}
    signals["object_type"] = {"equipment_asset"}
    signals["interaction_mode"] = {"inspect_verify"}

    signals.get("document_flow_stage", set()).discard("review")
    signals.get("interaction_mode", set()).discard("review_confirm")
    signals.get("interaction_mode", set()).discard("status_monitor")


def object_priority_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    if not candidate_id or not physical_item_inspection_anchor_active(title):
        return score, reasons, fields

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if candidate_id == PHYSICAL_ITEM_INSPECTION_ID:
        bonus += PHYSICAL_ITEM_SOFT_BONUS
        adj_reasons.append("object_priority physical_item_inspection soft boost")
    elif candidate_id in GENERIC_REVIEW_CANDIDATE_IDS:
        penalty += GENERIC_REVIEW_PENALTY
        adj_reasons.append("object_priority generic review soft penalty")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)


def withhold_generic_review_boost(title: str) -> bool:
    """Whether reporting/review soft boosts should not apply to generic review rows."""
    return physical_item_inspection_anchor_active(title)
