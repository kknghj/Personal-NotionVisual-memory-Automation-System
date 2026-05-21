from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.workflow_resolution import _canonical_title_text

TITLE_SIGNAL_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("interaction_mode", "send_share", ("공유",)),
    ("interaction_mode", "publish_distribute", ("배포", "배부", "송부", "전송", "발송")),
    ("interaction_mode", "publish_post", ("게시", "공고", "등록")),
    ("interaction_mode", "report_brief", ("보고", "브리핑", "상신")),
    ("interaction_mode", "request_delegate", ("요청", "협조요청", "지급요청")),
    ("interaction_mode", "request_approval", ("승인요청", "결재요청", "승인요청", "결재받기")),
    ("interaction_mode", "review_request", ("검토요청", "확인요청")),
    ("interaction_mode", "submission_request", ("제출요청", "제출")),
    ("workflow_fit", "communication", ("메일", "카카오톡", "카톡", "슬랙", "채팅")),
    ("workflow_fit", "document", ("문서", "자료", "공문", "계획", "보고", "결과", "안내문", "승인요청", "결재요청")),
    ("workflow_fit", "broadcast_notice", ("공지", "공고", "안내", "게시")),
    ("workflow_fit", "web_publication", ("게시", "공개", "공고")),
    ("workflow_fit", "tracking", ("현황", "진행상황", "집계", "점검결과", "추진실적")),
    ("object_type", "document", ("문서", "자료", "공문", "계획", "결과서", "보고서", "안내문", "승인요청", "결재요청")),
    ("object_type", "notice", ("공지", "공고", "게시", "안내")),
    ("object_type", "message", ("메일", "카카오톡", "카톡", "슬랙", "채팅")),
    ("visibility", "public", ("게시", "공개", "공고", "공지사항")),
    ("visibility", "internal", ("공유", "전달", "송부", "전송", "보고", "결재", "승인요청")),
    ("tone", "formal", ("공문", "결재", "승인", "보고", "공고", "게시")),
    ("tone", "neutral", ("공유", "안내", "전달")),
    ("publish_distribute", "distribution", ("배포", "배부", "송부", "전송", "발송")),
    ("publish_distribute", "posting", ("게시", "공고", "등록", "공개")),
    ("send_share", "mail", ("메일공유", "메일로공유")),
    ("send_share", "document", ("문서공유", "자료공유", "파일공유", "운영계획공유", "결과서공유")),
    ("request_approval", "approval_request", ("승인요청", "결재요청", "게시승인요청")),
    ("request_approval", "review_request", ("검토요청", "확인요청")),
    ("request_approval", "submission_request", ("제출요청", "자료제출")),
    ("request_approval", "action_request", ("지급요청", "협조요청", "요청")),
)

FIELD_WEIGHTS: dict[str, int] = {
    "interaction_mode": 3,
    "workflow_fit": 2,
    "publish_distribute": 2,
    "send_share": 2,
    "request_approval": 2,
    "object_type": 1,
    "visibility": 1,
    "tone": 1,
}


def _as_values(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    if isinstance(value, bool):
        return {str(value).lower()}
    return set()


def infer_title_semantic_signals(title: str) -> dict[str, set[str]]:
    canonical = _canonical_title_text(title)
    signals: dict[str, set[str]] = {}
    for field, value, terms in TITLE_SIGNAL_RULES:
        if any(term in canonical for term in terms):
            signals.setdefault(field, set()).add(value)
    return signals


def semantic_compatibility(
    title: str,
    semantic_metadata: dict[str, Any] | None,
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    if not semantic_metadata:
        return 0, (), ()

    signals = infer_title_semantic_signals(title)
    score = 0
    reasons: list[str] = []
    fields: list[str] = []

    for field in sorted(signals):
        title_values = signals[field]
        candidate_values = _as_values(semantic_metadata.get(field))
        matched = sorted(title_values & candidate_values)
        if not matched:
            continue
        score += FIELD_WEIGHTS.get(field, 1)
        fields.append(field)
        reasons.append(f"{field} matched {', '.join(matched)}")

    return score, tuple(reasons), tuple(fields)


def semantic_metadata_with_updates(
    metadata: dict[str, Any] | None,
    **updates: Any,
) -> dict[str, Any]:
    merged: dict[str, Any] = dict(metadata or {})
    for key, value in updates.items():
        if isinstance(value, Iterable) and not isinstance(value, str | bytes | dict):
            merged[key] = list(value)
        else:
            merged[key] = value
    return merged
