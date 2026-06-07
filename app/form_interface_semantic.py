"""Form interface vs document submission/receipt boundary."""

from __future__ import annotations

from typing import Any

from app.workflow_resolution import _canonical_title_text

FORM_INTERFACE_ANCHOR_TERMS: frozenset[str] = frozenset(
    {
        "네이버폼",
        "구글폼",
        "구글설문",
        "서베이몽키",
        "typeform",
    }
)
FORM_INTERFACE_CANDIDATE_IDS: frozenset[str] = frozenset({"survey_form"})
DOCUMENT_RECEIPT_CANDIDATE_IDS: frozenset[str] = frozenset(
    {
        "document_submission",
        "response_tracking",
        "allocation_tracking",
    }
)
FORM_INTERFACE_SOFT_BONUS = 4
FORM_INTERFACE_GENERIC_RECEIPT_PENALTY = 4


def _title_has_form_interface_anchor(canonical: str) -> bool:
    return any(term in canonical for term in FORM_INTERFACE_ANCHOR_TERMS)


def _title_has_document_receipt_flow(canonical: str) -> bool:
    if _title_has_form_interface_anchor(canonical):
        return False
    if "접수현황" in canonical or "현황확인" in canonical:
        return False
    return "접수" in canonical or ("신청" in canonical and "서" in canonical)


def form_interface_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    """Form anchor titles prefer survey_form; bare receipt flow demotes generic form match."""
    if not candidate_id or not semantic_metadata:
        return score, reasons, fields

    canonical = _canonical_title_text(title)
    has_form_anchor = _title_has_form_interface_anchor(canonical)
    has_document_receipt = _title_has_document_receipt_flow(canonical)

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if has_form_anchor and candidate_id in FORM_INTERFACE_CANDIDATE_IDS:
        bonus += FORM_INTERFACE_SOFT_BONUS
        adj_reasons.append("form_interface anchor soft boost survey_form")

    if has_document_receipt:
        if candidate_id in DOCUMENT_RECEIPT_CANDIDATE_IDS:
            bonus += FORM_INTERFACE_SOFT_BONUS
            adj_reasons.append("form_interface document receipt soft boost")
        if candidate_id in FORM_INTERFACE_CANDIDATE_IDS:
            penalty += FORM_INTERFACE_GENERIC_RECEIPT_PENALTY
            adj_reasons.append("form_interface document receipt demotes survey_form")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)
