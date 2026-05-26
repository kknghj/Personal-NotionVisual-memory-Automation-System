"""notification_ops vs communication semantic adjustments (§8.5)."""

from __future__ import annotations

from typing import Any

from app.workflow_resolution import _canonical_title_text

def _status_work_blocks_communication_boost(title: str, canonical: str) -> bool:
    if "현황" not in canonical:
        return False
    from app.semantic_scoring import detect_status_work_action

    return detect_status_work_action(title) is not None


NOTIFICATION_OPS_CANDIDATE_IDS = frozenset(
    {
        "notification_cleanup",
        "urgent_notice",
    }
)
ONE_WAY_NOTICE_CANDIDATE_IDS = frozenset(
    {
        "notification_cleanup",
        "urgent_notice",
        "notice_posting",
        "mail_distribution",
    }
)
COMMUNICATION_CANDIDATE_IDS = frozenset(
    {
        "phone_call",
        "messenger_chat",
        "mail_action",
        "mail_request",
        "verbal_request",
    }
)
NOTIFICATION_COMMUNICATION_SOFT_BONUS = 5
NOTIFICATION_COMMUNICATION_PENALTY = 6


def _title_has_two_way_communication(canonical: str) -> bool:
    """Two-way intent; bare ``협의`` without channel (e.g. 교육 협의) is excluded."""
    if any(term in canonical for term in ("회신", "문의", "연락", "대화")):
        return True
    has_channel = any(
        term in canonical for term in ("카톡", "카카오톡", "메신저", "메일", "이메일", "전화", "통화")
    )
    if has_channel and any(term in canonical for term in ("협의", "확인", "문의", "연락")):
        return True
    return False


def _title_has_notification_alert(canonical: str) -> bool:
    return "알림" in canonical


def _title_has_one_way_guidance(canonical: str) -> bool:
    if not any(term in canonical for term in ("안내", "공지", "알림")):
        return False
    return not _title_has_two_way_communication(canonical)


def notification_communication_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    """Soft bonus/penalty for notification_ops vs communication."""
    if not candidate_id or not semantic_metadata:
        return score, reasons, fields

    canonical = _canonical_title_text(title)
    has_alert = _title_has_notification_alert(canonical)
    has_two_way = _title_has_two_way_communication(canonical)
    has_one_way_guidance = _title_has_one_way_guidance(canonical)
    has_messenger_channel = any(term in canonical for term in ("카톡", "카카오톡", "메신저", "채팅"))
    has_mail_channel = any(term in canonical for term in ("메일", "이메일", "아웃룩"))
    has_publish_post = "게시" in canonical or "등록" in canonical or "고정" in canonical

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if has_alert and not has_two_way:
        if candidate_id in NOTIFICATION_OPS_CANDIDATE_IDS:
            bonus += NOTIFICATION_COMMUNICATION_SOFT_BONUS
            adj_reasons.append("notification_ops alert soft boost")
        if candidate_id == "messenger_chat" and has_messenger_channel:
            penalty += NOTIFICATION_COMMUNICATION_PENALTY
            adj_reasons.append("notification_ops demotes messenger on alert title")

    if "회신" in canonical:
        if candidate_id == "mail_action":
            bonus += NOTIFICATION_COMMUNICATION_SOFT_BONUS
            adj_reasons.append("communication reply soft boost mail_action")
        if candidate_id in ONE_WAY_NOTICE_CANDIDATE_IDS or candidate_id == "mail_distribution":
            penalty += NOTIFICATION_COMMUNICATION_PENALTY
            adj_reasons.append("communication reply demotes one-way notice")

    if (
        has_two_way
        and candidate_id in COMMUNICATION_CANDIDATE_IDS
        and not _status_work_blocks_communication_boost(title, canonical)
    ):
        bonus += NOTIFICATION_COMMUNICATION_SOFT_BONUS
        adj_reasons.append("communication two-way soft boost")

    if candidate_id == "mail_action" and has_messenger_channel:
        penalty += NOTIFICATION_COMMUNICATION_SOFT_BONUS
        adj_reasons.append("messenger channel demotes mail_action")

    if candidate_id == "mail_action" and "작성" in canonical and "안내문" in canonical:
        penalty += NOTIFICATION_COMMUNICATION_SOFT_BONUS
        adj_reasons.append("document writing demotes mail_action")

    if (
        candidate_id == "messenger_chat"
        and has_messenger_channel
        and ("공유" in canonical or has_two_way)
    ):
        bonus += NOTIFICATION_COMMUNICATION_SOFT_BONUS
        adj_reasons.append("messenger channel surface soft boost")

    if has_one_way_guidance and not has_publish_post and "작성" not in canonical:
        if candidate_id in ONE_WAY_NOTICE_CANDIDATE_IDS:
            bonus += NOTIFICATION_COMMUNICATION_SOFT_BONUS
            adj_reasons.append("one-way guidance notice soft boost")
        if candidate_id == "mail_action" and has_mail_channel and "발송" in canonical:
            bonus += NOTIFICATION_COMMUNICATION_SOFT_BONUS
            adj_reasons.append("one-way guidance mail dispatch soft boost")
        if (
            candidate_id == "messenger_chat"
            and not has_two_way
            and "공유" not in canonical
            and "전달" not in canonical
        ):
            penalty += NOTIFICATION_COMMUNICATION_PENALTY
            adj_reasons.append("one-way guidance demotes messenger conversation")
        if candidate_id == "work_calendar_organization" and "정리" not in canonical:
            penalty += NOTIFICATION_COMMUNICATION_PENALTY
            adj_reasons.append("one-way guidance demotes calendar on 안내 title")

    if has_publish_post and candidate_id == "urgent_notice":
        penalty += NOTIFICATION_COMMUNICATION_SOFT_BONUS
        adj_reasons.append("publication post demotes urgent_notice")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)
