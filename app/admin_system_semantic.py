"""Admin system interface vs object/document/salary semantic boundary (Pilot A)."""

from __future__ import annotations

from typing import Any

from app.workflow_resolution import _canonical_title_text

SYSTEM_WORK_ID = "system_work"
ADMIN_SYSTEM_COMPETING_IDS = frozenset(
    {
        "salary_system",
        "room_cleanup",
        "document_review",
    }
)
SALARY_SYSTEM_GUARD_COMPOUNDS: tuple[str, ...] = (
    "월급여입력",
    "급여반영",
    "급여지급",
    "월급계산",
)
TRAVEL_RESERVATION_TERMS: frozenset[str] = frozenset(
    {"숙소", "호텔", "기차", "ktx", "비행기", "항공", "식당", "숙박"},
)
ADMIN_SYSTEM_SOFT_BONUS = 12
ADMIN_SYSTEM_COMPETING_PENALTY = 8


def _canonical(title: str) -> str:
    return _canonical_title_text(title)


def title_has_salary_system_guard(title: str) -> bool:
    canonical = _canonical(title)
    return any(compound in canonical for compound in SALARY_SYSTEM_GUARD_COMPOUNDS)


def title_has_admin_interface_action(title: str) -> bool:
    """Detect admin-interface action compounds without travel/document-salary false positives."""
    canonical = _canonical(title)
    if "예약" in canonical:
        if not any(term in canonical for term in TRAVEL_RESERVATION_TERMS):
            if "회의실" in canonical or "시설" in canonical:
                return True
    if "등록" in canonical and any(term in canonical for term in ("여비", "출장", "경비")):
        return True
    if "접수" in canonical and "확인" in canonical and "문서" not in canonical:
        return True
    if (
        "지급" in canonical
        and any(term in canonical for term in ("수당", "위원회"))
        and "신청" not in canonical
    ):
        return True
    if "결재" in canonical and any(
        term in canonical for term in ("전산", "시스템", "행정", "초과근무", "초근")
    ):
        return True
    return False


def admin_system_boundary_active(title: str) -> bool:
    return title_has_admin_interface_action(title) and not title_has_salary_system_guard(title)


def admin_system_injection_match(title: str) -> tuple[str, int, int]:
    """Return synthetic match span for injected ``system_work`` row."""
    canonical = _canonical(title)
    patterns = (
        "회의실예약",
        "여비등록",
        "출장여비등록",
        "접수확인",
        "수당지급",
        "전산결재",
        "행정시스템등록",
        "등록",
        "예약",
        "지급",
        "결재",
    )
    for pattern in patterns:
        pos = canonical.find(pattern)
        if pos >= 0:
            return pattern, pos, len(pattern)
    return "시스템", 0, 2


def admin_system_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    if not candidate_id:
        return score, reasons, fields
    if not admin_system_boundary_active(title):
        return score, reasons, fields

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if candidate_id == SYSTEM_WORK_ID:
        bonus += ADMIN_SYSTEM_SOFT_BONUS
        adj_reasons.append("admin_system interface action soft boost system_work")
    if candidate_id in ADMIN_SYSTEM_COMPETING_IDS:
        penalty += ADMIN_SYSTEM_COMPETING_PENALTY
        adj_reasons.append(f"admin_system interface action demotes {candidate_id}")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)
