"""tracking/status_work vs document.reporting semantic adjustments (§8.7)."""

from __future__ import annotations

from typing import Any

from app.reporting_review_semantic import (
    REPORTING_CANDIDATE_IDS,
    REVIEW_CANDIDATE_IDS,
    _title_has_reporting_brief,
)
from app.workflow_resolution import _canonical_title_text

TRACKING_STATUS_CANDIDATE_IDS = frozenset(
    {
        "status_check",
        "progress_monitoring",
        "allocation_tracking",
        "response_tracking",
        "budget_tracking",
        "status_summary",
        "status_sharing",
        "status_update",
    }
)

STATUS_REPORTING_SOFT_BONUS = 5
STATUS_REPORTING_PENALTY = 6

STATUS_MONITOR_ACTION_TERMS: frozenset[str] = frozenset({"확인", "체크", "점검", "모니터링"})
STATUS_WORK_ACTION_TERMS: frozenset[str] = frozenset(
    {"공유", "정리", "업데이트", "작성", "제출"},
)
FORMAL_STATUS_DOCUMENT_TERMS: frozenset[str] = frozenset(
    {"보고서", "공고문", "제출서류", "안내문"},
)


def _title_has_status_material_compose(canonical: str) -> bool:
    """Internal status material writing — not formal document compose."""
    if "현황" not in canonical or "작성" not in canonical:
        return False
    return not any(term in canonical for term in FORMAL_STATUS_DOCUMENT_TERMS)


def _title_has_status_monitor_pattern(canonical: str) -> bool:
    """``현황`` + 확인/체크 — monitoring, not hierarchy brief or document review."""
    if "현황" not in canonical:
        return False
    if "요청" in canonical:
        return False
    if not any(term in canonical for term in STATUS_MONITOR_ACTION_TERMS):
        return False
    return not _title_has_reporting_brief(canonical)


def _title_has_bare_status_visibility(canonical: str) -> bool:
    """``현황``-only titles — intentionally soft; no hard reporting/review routing."""
    if "현황" not in canonical:
        return False
    if "결과" in canonical:
        return False
    if any(term in canonical for term in STATUS_MONITOR_ACTION_TERMS):
        return False
    if any(term in canonical for term in STATUS_WORK_ACTION_TERMS):
        return False
    if _title_has_reporting_brief(canonical):
        return False
    return True


def _title_has_status_reporting_compound(canonical: str) -> bool:
    """``현황`` appears alongside hierarchy reporting brief."""
    return "현황" in canonical and _title_has_reporting_brief(canonical)


def refine_status_reporting_title_signals(
    canonical: str,
    signals: dict[str, set[str]],
) -> None:
    """Strip false review/reporting signals on status monitoring titles."""
    if _title_has_status_monitor_pattern(canonical) or _title_has_bare_status_visibility(
        canonical
    ):
        signals.get("interaction_mode", set()).discard("report_brief")
        signals.get("interaction_mode", set()).discard("review_confirm")
        signals.setdefault("operational_state", set()).add("monitoring")
    if _title_has_status_reporting_compound(canonical):
        signals.setdefault("operational_state", set()).add("briefing")


def status_reporting_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    """Soft bonus/penalty for tracking/status vs reporting boundary."""
    if not candidate_id or not semantic_metadata:
        return score, reasons, fields

    from app.semantic_scoring import detect_status_work_action, is_result_status_reporting_compound

    canonical = _canonical_title_text(title)
    has_monitor = _title_has_status_monitor_pattern(canonical)
    has_bare_status = _title_has_bare_status_visibility(canonical)
    has_status_reporting = _title_has_status_reporting_compound(canonical)
    has_status_material = _title_has_status_material_compose(canonical)
    has_status_work = detect_status_work_action(title) is not None
    has_result_compound = is_result_status_reporting_compound(title)

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if has_monitor or has_bare_status:
        if candidate_id in TRACKING_STATUS_CANDIDATE_IDS:
            bonus += STATUS_REPORTING_SOFT_BONUS
            adj_reasons.append("status_reporting monitoring soft boost")
        if candidate_id in REPORTING_CANDIDATE_IDS:
            penalty += STATUS_REPORTING_PENALTY
            adj_reasons.append("status_reporting monitoring demotes reporting")
        if candidate_id in REVIEW_CANDIDATE_IDS:
            penalty += STATUS_REPORTING_PENALTY
            adj_reasons.append("status_reporting monitoring demotes review")

    if has_status_reporting and not has_result_compound:
        if candidate_id in REPORTING_CANDIDATE_IDS:
            bonus += STATUS_REPORTING_SOFT_BONUS
            adj_reasons.append("status_reporting 현황+보고 soft boost reporting")
        if (
            candidate_id in TRACKING_STATUS_CANDIDATE_IDS
            and not has_status_work
            and candidate_id != "status_summary"
        ):
            penalty += STATUS_REPORTING_SOFT_BONUS
            adj_reasons.append("status_reporting 현황+보고 demotes tracking")

    if has_status_work or has_status_material:
        if candidate_id == "status_summary":
            bonus += STATUS_REPORTING_SOFT_BONUS
            adj_reasons.append("status_reporting status material soft boost status_summary")
        if candidate_id in {"progress_monitoring", "status_check"}:
            penalty += STATUS_REPORTING_PENALTY
            adj_reasons.append("status_reporting status_work demotes bare tracking")
        if candidate_id in REPORTING_CANDIDATE_IDS:
            penalty += STATUS_REPORTING_SOFT_BONUS
            adj_reasons.append("status_reporting status_work demotes reporting")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)
