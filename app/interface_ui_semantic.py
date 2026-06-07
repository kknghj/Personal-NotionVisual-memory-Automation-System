"""UI / screen anchor vs document_edit semantic boundary (§8 interface)."""

from __future__ import annotations

from typing import Any

from app.workflow_resolution import _canonical_title_text

UI_SCREEN_COMPOUND_ANCHORS: tuple[str, ...] = (
    "본인인증화면",
    "로그인화면",
    "신청화면",
    "인증화면",
    "로그인페이지",
    "신청페이지",
    "신청폼",
)
UI_SCREEN_EXTRA_ANCHORS: frozenset[str] = frozenset({"버튼"})
UI_INTERFACE_CANDIDATE_IDS: frozenset[str] = frozenset(
    {
        "qr_code_scan_auth",
        "qr_auth",
        "coding",
        "survey_form",
        "notion_docs_touchup",
        "spreadsheet_work",
        "terminal_work",
    }
)
DOCUMENT_EDIT_ID = "document_edit"
UI_COMPOSE_ACTION_TERMS: frozenset[str] = frozenset({"수정", "편집", "제안"})
UI_REVIEW_ACTION_TERMS: frozenset[str] = frozenset({"검토", "확인", "열람"})
UI_REQUEST_COMPOUND_TERMS: frozenset[str] = frozenset(
    {"수정요청", "확인요청", "검토요청", "제안요청"},
)
UI_SCREEN_SOFT_BONUS = 4
UI_SCREEN_DOCUMENT_EDIT_PENALTY = 4


def _title_has_ui_screen_anchor(canonical: str) -> bool:
    if any(anchor in canonical for anchor in UI_SCREEN_COMPOUND_ANCHORS):
        return True
    if "로그인" in canonical and "화면" in canonical:
        return True
    if any(term in canonical for term in UI_SCREEN_EXTRA_ANCHORS):
        return True
    if "페이지" in canonical and any(term in canonical for term in ("로그인", "신청", "인증")):
        return True
    if "폼" in canonical and "신청" in canonical:
        return True
    return False


def _title_has_ui_compose_action(canonical: str) -> bool:
    if any(term in canonical for term in UI_REQUEST_COMPOUND_TERMS):
        return False
    if any(term in canonical for term in UI_REVIEW_ACTION_TERMS):
        return False
    return any(term in canonical for term in UI_COMPOSE_ACTION_TERMS)


def interface_ui_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    """When a UI/screen anchor co-occurs with compose action, prefer interface candidates."""
    if not candidate_id or not semantic_metadata:
        return score, reasons, fields

    canonical = _canonical_title_text(title)
    has_ui_screen = _title_has_ui_screen_anchor(canonical)
    has_ui_compose = _title_has_ui_compose_action(canonical)
    if not has_ui_screen or not has_ui_compose:
        return score, reasons, fields

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if candidate_id in UI_INTERFACE_CANDIDATE_IDS:
        bonus += UI_SCREEN_SOFT_BONUS
        adj_reasons.append("interface_ui screen compose soft boost")
    if candidate_id == DOCUMENT_EDIT_ID:
        penalty += UI_SCREEN_DOCUMENT_EDIT_PENALTY
        adj_reasons.append("interface_ui screen compose demotes document_edit")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)
