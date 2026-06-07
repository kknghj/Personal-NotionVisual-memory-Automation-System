"""document.reporting vs document.review semantic adjustments (§8.6)."""

from __future__ import annotations

from typing import Any

from app.workflow_resolution import _canonical_title_text

OBJECT_BOUND_TRANSFER_OBJECT_TERMS: frozenset[str] = frozenset(
    {
        "공문",
        "자료",
        "회의자료",
        "검토자료",
        "결과자료",
        "파일",
        "서류",
    },
)
EXPLICIT_CHANNEL_TERMS: frozenset[str] = frozenset(
    {"메일", "이메일", "아웃룩", "카카오톡", "카톡", "슬랙", "채팅", "메신저"},
)


def _title_has_object_bound_transfer(canonical: str) -> bool:
    if "전달" not in canonical or any(term in canonical for term in EXPLICIT_CHANNEL_TERMS):
        return False
    return any(
        f"{obj}전달" in canonical
        for obj in sorted(OBJECT_BOUND_TRANSFER_OBJECT_TERMS, key=len, reverse=True)
    )

REVIEW_CANDIDATE_IDS = frozenset(
    {
        "document_review",
        "slide_deck_final_review",
        "approval_review",
        "promotional_material_review",
    }
)
GENERIC_DOCUMENT_REVIEW_ID = "document_review"
OBJECT_SPECIFIC_REVIEW_CANDIDATE_IDS = frozenset(
    {
        "press_release_review",
        "tax_invoice_review",
    }
)
OBJECT_SPECIFIC_REVIEW_OBJECT_TERMS: frozenset[str] = frozenset(
    {
        "보도자료",
        "세금계산서",
        "영수증",
        "계산서",
    }
)
REPORTING_CANDIDATE_IDS = frozenset(
    {
        "document_reporting",
        "result_reporting",
    }
)
REPORTING_REVIEW_SOFT_BONUS = 5
REPORTING_REVIEW_PENALTY = 6

REPORTING_BRIEF_COMPOUND_TERMS: tuple[str, ...] = (
    "결과보고",
    "결과자료보고",
    "집계결과보고",
    "운영결과보고",
    "정산결과보고",
    "교육결과보고",
    "최종결과보고",
    "최종보고",
    "진행상황보고",
    "진행보고",
    "추진현황보고",
    "중간보고",
    "검토결과보고",
)

DOCUMENT_OBJECT_REVIEW_ACTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("보고서", ("검토", "확인", "열람", "작성", "수정")),
    ("보고자료", ("검토", "확인", "열람", "작성", "수정")),
    ("회의자료", ("검토", "확인", "열람")),
    ("검토자료", ("검토", "확인", "열람")),
    ("발표자료", ("검토", "확인", "열람")),
)

COMPOSE_ACTION_TERMS: frozenset[str] = frozenset({"작성", "기안", "편집", "기입"})
REPORTING_DELIVERY_TERMS: frozenset[str] = frozenset(
    {"전달", "송부", "상신", "브리핑", "제출"},
)
REVIEW_OBJECT_NOUN_TERMS: frozenset[str] = frozenset(
    {"검토자료", "검토안", "검토본", "검토표"},
)


def _title_has_review_keyword(canonical: str) -> bool:
    """``검토`` as review action — not when it only appears inside ``검토자료`` object nouns."""
    if "검토요청" in canonical:
        return False
    if "검토" not in canonical:
        return False
    stripped = canonical
    for noun in REVIEW_OBJECT_NOUN_TERMS:
        stripped = stripped.replace(noun, "")
    return "검토" in stripped


def _title_has_document_object_review(canonical: str) -> bool:
    return any(
        f"{obj}{action}" in canonical
        for obj, actions in DOCUMENT_OBJECT_REVIEW_ACTIONS
        for action in actions
    )


def _title_has_reporting_brief(canonical: str) -> bool:
    if any(term in canonical for term in REPORTING_BRIEF_COMPOUND_TERMS):
        return True
    if any(term in canonical for term in ("브리핑", "상신")):
        return True
    if _title_has_document_object_review(canonical):
        return False
    if "보고" in canonical:
        if any(term in canonical for term in COMPOSE_ACTION_TERMS):
            return False
        if "검토" in canonical and not canonical.endswith("보고"):
            return False
        if "요청" in canonical:
            return False
        return True
    return False


def _title_has_object_specific_review_compound(canonical: str) -> bool:
    """Object noun + 검토/확인 in title — maps to object-specific review catalog entries."""
    return any(
        obj in canonical and any(f"{obj}{action}" in canonical for action in ("검토", "확인"))
        for obj in OBJECT_SPECIFIC_REVIEW_OBJECT_TERMS
    )


def _title_has_review_action(canonical: str) -> bool:
    if any(term in canonical for term in ("검토요청", "확인요청")):
        return False
    if _title_has_reporting_brief(canonical):
        return False
    if _title_has_review_keyword(canonical):
        return True
    if "확인" in canonical and "요청" not in canonical and "현황" not in canonical:
        return True
    if "열람" in canonical:
        return True
    return False


def _title_is_report_compose(canonical: str) -> bool:
    if not any(term in canonical for term in COMPOSE_ACTION_TERMS):
        return False
    if not any(term in canonical for term in ("보고", "보고서", "결과")):
        return False
    return not any(term in canonical for term in REPORTING_DELIVERY_TERMS)


def refine_reporting_review_title_signals(
    canonical: str,
    signals: dict[str, set[str]],
) -> None:
    """Remove false ``report_brief`` when ``보고서``/``보고자료`` carry review/compose action."""
    if _title_has_document_object_review(canonical) or _title_is_report_compose(canonical):
        signals.get("interaction_mode", set()).discard("report_brief")
    if _title_has_reporting_brief(canonical):
        signals.setdefault("interaction_mode", set()).add("report_brief")
    if _title_has_review_action(canonical):
        signals.setdefault("interaction_mode", set()).add("review_confirm")
    if _title_has_object_bound_transfer(canonical) and not _title_has_review_action(canonical):
        signals.get("interaction_mode", set()).discard("review_confirm")
        signals.get("document_flow_stage", set()).discard("review")


def reporting_review_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    """Soft bonus/penalty for reporting vs review boundary."""
    if not candidate_id or not semantic_metadata:
        return score, reasons, fields

    canonical = _canonical_title_text(title)
    has_reporting = _title_has_reporting_brief(canonical)
    has_review = _title_has_review_action(canonical)
    has_compose = _title_is_report_compose(canonical)
    has_transfer = "전달" in canonical

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if has_compose:
        if candidate_id == "document_edit":
            bonus += REPORTING_REVIEW_SOFT_BONUS
            adj_reasons.append("reporting_review report compose soft boost document_edit")
        if candidate_id in REPORTING_CANDIDATE_IDS:
            penalty += REPORTING_REVIEW_PENALTY
            adj_reasons.append("reporting_review report compose demotes reporting brief")

    if has_reporting and not has_review:
        if candidate_id in REPORTING_CANDIDATE_IDS:
            bonus += REPORTING_REVIEW_SOFT_BONUS
            adj_reasons.append("reporting_review reporting brief soft boost")
        if candidate_id in REVIEW_CANDIDATE_IDS:
            penalty += REPORTING_REVIEW_PENALTY
            adj_reasons.append("reporting_review reporting brief demotes review")
        if has_transfer and candidate_id == "document_review":
            penalty += REPORTING_REVIEW_SOFT_BONUS
            adj_reasons.append("reporting_review reporting transfer demotes generic review")

    if has_review and not has_reporting:
        has_object_review = _title_has_object_specific_review_compound(canonical)
        if candidate_id in REVIEW_CANDIDATE_IDS:
            if has_object_review and candidate_id == GENERIC_DOCUMENT_REVIEW_ID:
                adj_reasons.append(
                    "object_specific_review compound withholds generic document_review boost"
                )
            else:
                bonus += REPORTING_REVIEW_SOFT_BONUS
                adj_reasons.append("reporting_review review action soft boost")
        elif has_object_review and candidate_id in OBJECT_SPECIFIC_REVIEW_CANDIDATE_IDS:
            bonus += REPORTING_REVIEW_SOFT_BONUS
            adj_reasons.append("object_specific_review compound soft boost")
        if candidate_id in REPORTING_CANDIDATE_IDS:
            penalty += REPORTING_REVIEW_PENALTY
            adj_reasons.append("reporting_review review action demotes reporting")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)
