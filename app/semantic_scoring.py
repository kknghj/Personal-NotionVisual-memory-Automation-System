from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from app.workflow_resolution import _canonical_title_text

TITLE_SIGNAL_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("interaction_mode", "create_edit", ("작성", "기안", "수정", "편집", "기입")),
    ("interaction_mode", "send_share", ("공유", "전달")),
    ("interaction_mode", "publish_distribute", ("배포", "배부", "송부", "전송", "발송")),
    ("interaction_mode", "publish_post", ("게시", "공고", "등록")),
    ("interaction_mode", "report_brief", ("보고", "브리핑", "상신")),
    ("interaction_mode", "request_delegate", ("요청", "협조요청", "지급요청")),
    ("interaction_mode", "request_approval", ("승인요청", "결재요청", "승인요청", "결재받기")),
    ("interaction_mode", "review_request", ("검토요청", "확인요청")),
    (
        "interaction_mode",
        "submission_request",
        (
            "제출요청",
            "자료제출요청",
            "서류제출요청",
            "참가폼제출요청",
            "보완자료제출요청",
            "보완요청",
            "수정요청",
        ),
    ),
    (
        "interaction_mode",
        "submit",
        (
            "자료제출",
            "실적자료제출",
            "추진현황제출",
            "활동결과제출",
            "참가폼제출",
        ),
    ),
    ("interaction_mode", "review_confirm", ("검토",)),
    (
        "interaction_mode",
        "approve_signoff",
        ("승인하기", "결재하기", "최종승인", "최종결재", "신청승인"),
    ),
    ("workflow_fit", "communication", ("메일", "카카오톡", "카톡", "슬랙", "채팅")),
    ("workflow_fit", "document", ("문서", "자료", "공문", "계획", "보고", "결과", "안내문", "승인요청", "결재요청")),
    ("workflow_fit", "broadcast_notice", ("공지", "공고", "안내", "게시")),
    ("workflow_fit", "web_publication", ("게시", "공개", "공고", "홈페이지", "배너")),
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
    ("request_approval", "submission_request", ("제출요청", "자료제출요청", "서류제출요청", "참가폼제출요청", "보완자료제출요청")),
    ("request_approval", "revision_request", ("보완요청", "수정요청", "자료제출보완요청")),
    ("request_approval", "action_request", ("지급요청", "협조요청", "요청")),
)

FIELD_WEIGHTS: dict[str, int] = {
    "interaction_mode": 3,
    "document_flow_stage": 3,
    "workflow_fit": 2,
    "workflow_stage": 2,
    "publish_distribute": 2,
    "send_share": 2,
    "request_approval": 2,
    "object_type": 1,
    "visibility": 1,
    "tone": 1,
}

DOCUMENT_FLOW_STAGE_COMPOUND_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "complete",
        (
            "최종승인",
            "최종결재",
            "승인완료",
            "결재완료",
            "신청승인",
        ),
    ),
    (
        "request",
        (
            "자료제출보완요청",
            "제출보완요청",
            "보완자료제출요청",
            "자료제출요청",
            "서류제출요청",
            "참가폼제출요청",
            "제출요청",
            "검토요청",
            "확인요청",
            "승인요청",
            "결재요청",
            "보완요청",
            "수정요청",
            "신청내용확인요청",
        ),
    ),
    (
        "approve",
        ("자료제출승인", "제출승인", "제출후승인", "자료제출후승인", "결재하기", "승인하기"),
    ),
    (
        "review",
        ("자료제출검토", "제출검토", "제출자료검토", "결재검토", "승인검토"),
    ),
    ("reject_or_return", ("반려", "회송", "반송")),
    (
        "submit",
        (
            "자료제출",
            "실적자료제출",
            "추진현황제출",
            "활동결과제출",
            "참가폼제출",
            "현황제출",
            "가입현황제출",
        ),
    ),
)

# Longer phrases first so e.g. ``최종결과`` wins over bare ``결과``.
WORKFLOW_STAGE_AMBIGUOUS_TERMS: frozenset[str] = frozenset({"현황"})
WORKFLOW_STAGE_CONTEXTUAL_TERMS: tuple[tuple[str, str], ...] = (
    ("contextual:운영현황", "운영현황"),
    ("contextual:신청현황", "신청현황"),
    ("contextual:배정현황", "배정현황"),
)
WORKFLOW_STAGE_PRIMARY_ORDER: tuple[str, ...] = ("final", "result", "interim", "progress")

RESULT_STATUS_REPORTING_ACTION_TERMS: frozenset[str] = frozenset(
    {"보고", "정리", "공유", "자료", "제출"},
)
PROGRESS_STRONG_TERMS: frozenset[str] = frozenset({"진행상황", "추진상황"})
PROGRESS_MODERATE_TERMS: frozenset[str] = frozenset({"진행현황", "추진현황", "진행상태"})
RESULT_STATUS_REPORTING_SOFT_BONUS = 1
RESULT_STATUS_COMPOUND_CONFIDENCE = 0.68
STATUS_WORK_SOFT_BONUS = 1
STATUS_WORK_ACTION_UPDATE = "update_status"
STATUS_WORK_ACTION_SHARE = "share_status"
STATUS_WORK_ACTION_SUMMARIZE = "organize_summarize"


TRANSFER_INTERACTION_MODES: frozenset[str] = frozenset({"publish_distribute", "send_share"})

EXPLICIT_CHANNEL_TERMS: frozenset[str] = frozenset(
    {"메일", "이메일", "아웃룩", "카카오톡", "카톡", "슬랙", "채팅", "메신저"},
)
GENERIC_TRANSFER_TERMS: frozenset[str] = frozenset({"전달"})
FORMAL_DISPATCH_TERMS: frozenset[str] = frozenset({"송부", "배부", "배포", "전송", "발송"})
ACCESS_SHARE_OBJECT_TERMS: frozenset[str] = frozenset(
    {"암호", "비밀번호", "패스워드", "권한", "계정"},
)
DOCUMENT_TRANSFER_OBJECT_TERMS: frozenset[str] = frozenset(
    {
        "문서",
        "자료",
        "공문",
        "계획",
        "보고",
        "결과",
        "안내문",
        "검토자료",
        "정산서류",
        "파일",
        "링크",
        "서류",
    },
)
MAIL_CHANNEL_CANDIDATE_IDS: frozenset[str] = frozenset(
    {"mail_action", "mail_sharing", "mail_distribution"},
)
TRANSFER_SHARING_SOFT_BONUS = 2
GENERIC_TRANSFER_MAIL_PENALTY = 2


def _title_has_explicit_channel(canonical: str) -> bool:
    return any(term in canonical for term in EXPLICIT_CHANNEL_TERMS)


def _title_has_formal_dispatch(canonical: str) -> bool:
    return any(term in canonical for term in FORMAL_DISPATCH_TERMS)


def _title_has_generic_transfer_only(canonical: str) -> bool:
    return (
        any(term in canonical for term in GENERIC_TRANSFER_TERMS)
        and not _title_has_explicit_channel(canonical)
        and not _title_has_formal_dispatch(canonical)
    )


def _title_has_access_share_object(canonical: str) -> bool:
    return any(term in canonical for term in ACCESS_SHARE_OBJECT_TERMS)


def _title_has_document_transfer_object(canonical: str) -> bool:
    return any(term in canonical for term in DOCUMENT_TRANSFER_OBJECT_TERMS)


def transfer_sharing_semantic_adjustment(
    title: str,
    candidate_id: str | None,
    semantic_metadata: dict[str, Any] | None,
    score: int,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    """Soft bonus/penalty for 전달/송부/공유 policy (channel > object > action > generic)."""
    if not candidate_id or not semantic_metadata:
        return score, reasons, fields

    canonical = _canonical_title_text(title)
    has_channel = _title_has_explicit_channel(canonical)
    has_dispatch = _title_has_formal_dispatch(canonical)
    has_sharing = "공유" in canonical
    has_generic_transfer = _title_has_generic_transfer_only(canonical)
    has_access_object = _title_has_access_share_object(canonical)
    has_document_object = _title_has_document_transfer_object(canonical)

    bonus = 0
    penalty = 0
    adj_reasons = list(reasons)
    adj_fields = list(fields)

    if has_channel and candidate_id in MAIL_CHANNEL_CANDIDATE_IDS:
        if has_generic_transfer or has_dispatch or has_sharing:
            bonus += TRANSFER_SHARING_SOFT_BONUS
            adj_reasons.append("transfer_sharing explicit channel soft boost")

    if "송부" in canonical and candidate_id == "document_distribution":
        bonus += TRANSFER_SHARING_SOFT_BONUS
        adj_reasons.append("transfer_sharing formal dispatch document_distribution soft boost")

    if has_sharing and candidate_id == "document_sharing":
        if has_document_object and not has_access_object:
            bonus += TRANSFER_SHARING_SOFT_BONUS
            adj_reasons.append("transfer_sharing document object sharing soft boost")

    if has_sharing and candidate_id == "credential_sharing" and has_access_object:
        bonus += TRANSFER_SHARING_SOFT_BONUS
        adj_reasons.append("transfer_sharing access/key sharing soft boost")

    if has_sharing and has_access_object and candidate_id == "document_sharing":
        penalty += TRANSFER_SHARING_SOFT_BONUS
        adj_reasons.append("transfer_sharing access object demotes document_sharing")

    if has_generic_transfer and not has_channel and candidate_id in MAIL_CHANNEL_CANDIDATE_IDS:
        penalty += GENERIC_TRANSFER_MAIL_PENALTY
        adj_reasons.append("transfer_sharing generic transfer demotes mail channel")

    adjusted = max(0, score + bonus - penalty)
    return adjusted, tuple(adj_reasons), tuple(adj_fields)


def title_has_transfer_without_compose(signals: dict[str, set[str]]) -> bool:
    """Transfer/distribute/share verbs without compose — do not boost create_edit."""
    modes = signals.get("interaction_mode", set())
    has_transfer = bool(modes & TRANSFER_INTERACTION_MODES)
    has_compose = "create_edit" in modes
    return has_transfer and not has_compose

WORKFLOW_STAGE_TITLE_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("final", ("최종결과보고", "최종결과", "최종보고", "최종안", "종료보고", "마감보고")),
    ("result", (
        "결과보고",
        "결과자료보고",
        "집계결과보고",
        "운영결과보고",
        "정산결과보고",
        "교육결과보고",
        "출장결과",
        "현장결과",
        "활동결과",
        "행사결과",
        "회의결과",
        "검토결과",
        "점검결과",
        "운영결과",
        "교육결과",
        "정산결과",
        "집계결과",
    )),
    ("interim", ("중간보고", "중간점검", "중간결과", "중간")),
    ("progress", (
        "진행상황",
        "진행현황",
        "진행상태",
        "추진현황",
        "추진상황",
        "진행보고",
        "추진실적",
    )),
)


def _as_values(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    if isinstance(value, bool):
        return {str(value).lower()}
    return set()


def _title_has_spaced_progress_status(title: str) -> bool:
    return bool(re.search(r"진행\s+현황", title) or re.search(r"추진\s+현황", title))


def detect_result_status_reporting_compound(title: str) -> dict[str, str] | None:
    """결과+현황+reporting/document action without overfitting bare 현황 or 결과 alone."""
    canonical = _canonical_title_text(title)
    if "결과" not in canonical or "현황" not in canonical:
        return None
    action = next(
        (term for term in RESULT_STATUS_REPORTING_ACTION_TERMS if term in canonical),
        None,
    )
    if not action:
        return None
    return {"action": action, "source": f"compound:결과+현황+{action}"}


def is_result_status_reporting_compound(title: str) -> bool:
    return detect_result_status_reporting_compound(title) is not None


def detect_status_work_action(title: str) -> str | None:
    """현황+정리/공유/업데이트 without 결과+현황 reporting compound."""
    if is_result_status_reporting_compound(title):
        return None
    canonical = _canonical_title_text(title)
    if "현황" not in canonical:
        return None
    if "업데이트" in canonical:
        return STATUS_WORK_ACTION_UPDATE
    if "공유" in canonical:
        return STATUS_WORK_ACTION_SHARE
    if any(term in canonical for term in ("정리", "작성")):
        return STATUS_WORK_ACTION_SUMMARIZE
    return None


def _workflow_stage_term_hits(canonical: str) -> list[tuple[str, str, int]]:
    """Return (stage, matched_term, term_length) for each rule hit."""
    hits: list[tuple[str, str, int]] = []
    for stage, terms in WORKFLOW_STAGE_TITLE_TERMS:
        for term in terms:
            if term and term in canonical:
                hits.append((stage, term, len(term)))
    return hits


def infer_title_workflow_stages(title: str) -> set[str]:
    """Infer reporting lifecycle stages from title text.

    ``현황`` alone is intentionally omitted (ambiguous across progress/result/tracking).
    """
    stages = {stage for stage, _term, _ln in _workflow_stage_term_hits(_canonical_title_text(title))}
    if detect_result_status_reporting_compound(title):
        stages.add("result")
    return stages


def _pick_primary_workflow_stage(stages: set[str]) -> str | None:
    for stage in WORKFLOW_STAGE_PRIMARY_ORDER:
        if stage in stages:
            return stage
    return None


def _calibrate_progress_confidence(
    title: str,
    best_term: str,
    base_confidence: float,
) -> tuple[float, str]:
    if best_term in PROGRESS_STRONG_TERMS:
        return base_confidence, f"keyword:{best_term}"
    if best_term in PROGRESS_MODERATE_TERMS:
        source = (
            "compound:진행+현황"
            if _title_has_spaced_progress_status(title)
            else f"contextual:{best_term}"
        )
        return 0.55, source
    return base_confidence, f"keyword:{best_term}"


def infer_workflow_stage_detail(title: str) -> dict[str, Any]:
    """Lightweight stage inference for feedback_log / calibration (not a hard rule)."""
    canonical = _canonical_title_text(title)
    compound = detect_result_status_reporting_compound(title)
    hits = _workflow_stage_term_hits(canonical)
    stages = {stage for stage, _term, _ln in hits}
    if compound:
        stages.add("result")

    ambiguous_token: str | None = None
    if not stages:
        for token in WORKFLOW_STAGE_AMBIGUOUS_TERMS:
            if token in canonical:
                ambiguous_token = token
                break

    if compound and "result" in stages:
        confidence = RESULT_STATUS_COMPOUND_CONFIDENCE
        if len(stages) > 1:
            confidence = min(confidence, 0.72)
        return {
            "inferred_workflow_stage": "result",
            "inferred_workflow_stages_all": sorted(stages),
            "workflow_stage_confidence": confidence,
            "workflow_stage_source": compound["source"],
            "workflow_stage_ambiguous": False,
        }

    if ambiguous_token and not stages:
        contextual_source = ""
        for source, phrase in WORKFLOW_STAGE_CONTEXTUAL_TERMS:
            if phrase in canonical:
                contextual_source = source
                break
        return {
            "inferred_workflow_stage": None,
            "inferred_workflow_stages_all": [],
            "workflow_stage_confidence": 0.2,
            "workflow_stage_source": contextual_source or f"ambiguous:{ambiguous_token}",
            "workflow_stage_ambiguous": True,
        }

    if not stages:
        return {
            "inferred_workflow_stage": None,
            "inferred_workflow_stages_all": [],
            "workflow_stage_confidence": 0.0,
            "workflow_stage_source": "",
            "workflow_stage_ambiguous": False,
        }

    best_hit = max(hits, key=lambda item: item[2])
    stage, best_term, best_len = best_hit
    confidence = 0.85 if best_len >= 4 else 0.65
    source = f"keyword:{best_term}"
    if stage == "progress":
        confidence, source = _calibrate_progress_confidence(title, best_term, confidence)
    if len(stages) > 1:
        confidence = min(confidence, 0.75)
    return {
        "inferred_workflow_stage": _pick_primary_workflow_stage(stages),
        "inferred_workflow_stages_all": sorted(stages),
        "workflow_stage_confidence": confidence,
        "workflow_stage_source": source,
        "workflow_stage_ambiguous": False,
    }


DOCUMENT_FLOW_STAGE_FALLBACK_PRIORITY: tuple[str, ...] = (
    "complete",
    "request",
    "approve",
    "review",
    "reject_or_return",
    "submit",
)

# ``완료`` alone is not document_flow complete — only approval/decision-flow compounds qualify.
DOCUMENT_FLOW_NON_APPROVAL_COMPLETE_TERMS: frozenset[str] = frozenset(
    {
        "교육완료",
        "작업완료",
        "보고완료",
        "정리완료",
        "진행완료",
        "행사완료",
        "회의완료",
    }
)


def infer_document_flow_stages(title: str) -> set[str]:
    """Infer document lifecycle stage from title (soft signal, not a hard filter)."""
    canonical = _canonical_title_text(title)

    best_stage: str | None = None
    best_len = 0
    for stage, terms in DOCUMENT_FLOW_STAGE_COMPOUND_TERMS:
        for term in terms:
            if term in canonical and len(term) > best_len:
                best_len = len(term)
                best_stage = stage

    if best_stage:
        return {best_stage}

    if canonical in DOCUMENT_FLOW_NON_APPROVAL_COMPLETE_TERMS:
        return set()

    fallback: set[str] = set()
    if "요청" in canonical and any(
        marker in canonical
        for marker in ("검토", "확인", "승인", "결재", "보완", "수정", "제출", "협조", "지급")
    ):
        fallback.add("request")
    if "제출" in canonical and "요청" not in canonical:
        fallback.add("submit")
    if "검토" in canonical or (
        "확인" in canonical and "요청" not in canonical and "현황" not in canonical
    ):
        fallback.add("review")
    if ("승인" in canonical or "결재" in canonical) and "검토" not in canonical:
        fallback.add("approve")
    if any(term in canonical for term in ("반려", "회송", "반송")):
        fallback.add("reject_or_return")

    for stage in DOCUMENT_FLOW_STAGE_FALLBACK_PRIORITY:
        if stage in fallback:
            return {stage}
    return fallback


def _apply_document_flow_stage_signals(
    title: str,
    signals: dict[str, set[str]],
) -> None:
    stages = infer_document_flow_stages(title)
    if not stages:
        return

    signals["document_flow_stage"] = stages
    canonical = _canonical_title_text(title)

    if "request" in stages:
        if any(
            term in canonical
            for term in ("보완요청", "수정요청", "자료제출보완요청", "제출보완요청")
        ):
            signals.setdefault("interaction_mode", set()).add("request_delegate")
            signals.setdefault("request_approval", set()).add("revision_request")
        elif any(term in canonical for term in ("검토요청", "확인요청", "신청내용확인요청")):
            signals.setdefault("interaction_mode", set()).add("review_request")
        elif any(term in canonical for term in ("승인요청", "결재요청", "게시승인요청")):
            signals.setdefault("interaction_mode", set()).add("request_approval")
        elif any(
            term in canonical
            for term in (
                "제출요청",
                "자료제출요청",
                "서류제출요청",
                "참가폼제출요청",
                "보완자료제출요청",
            )
        ):
            signals.setdefault("interaction_mode", set()).add("submission_request")
        elif "요청" in canonical:
            signals.setdefault("interaction_mode", set()).add("request_delegate")
    elif "submit" in stages:
        signals.setdefault("interaction_mode", set()).add("submit")
    elif "review" in stages:
        signals.setdefault("interaction_mode", set()).add("review_confirm")
    elif "approve" in stages or "complete" in stages:
        signals.setdefault("interaction_mode", set()).add("approve_signoff")


def infer_title_semantic_signals(title: str) -> dict[str, set[str]]:
    canonical = _canonical_title_text(title)
    signals: dict[str, set[str]] = {}
    for field, value, terms in TITLE_SIGNAL_RULES:
        if any(term in canonical for term in terms):
            signals.setdefault(field, set()).add(value)
    stages = infer_title_workflow_stages(title)
    if stages:
        signals["workflow_stage"] = stages
    _apply_document_flow_stage_signals(title, signals)
    return signals


def semantic_compatibility(
    title: str,
    semantic_metadata: dict[str, Any] | None,
    candidate_id: str | None = None,
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    if not semantic_metadata:
        return 0, (), ()

    signals = infer_title_semantic_signals(title)
    score = 0
    reasons: list[str] = []
    fields: list[str] = []

    if is_result_status_reporting_compound(title):
        for field in sorted(signals):
            title_values = signals[field]
            candidate_values = _as_values(semantic_metadata.get(field))
            matched = sorted(title_values & candidate_values)
            if not matched:
                continue
            score += FIELD_WEIGHTS.get(field, 1)
            fields.append(field)
            reasons.append(f"{field} matched {', '.join(matched)}")
        stage_values = _as_values(semantic_metadata.get("workflow_stage"))
        if "result" in stage_values or "final" in stage_values:
            score += RESULT_STATUS_REPORTING_SOFT_BONUS
            if "workflow_stage" not in fields:
                fields.append("workflow_stage")
            reasons.append("workflow_stage compound result+현황 soft boost")
        return score, tuple(reasons), tuple(fields)

    status_action = detect_status_work_action(title)

    if title_has_transfer_without_compose(signals):
        if "create_edit" in _as_values(semantic_metadata.get("interaction_mode")):
            return 0, (), ()

    for field in sorted(signals):
        title_values = signals[field]
        if status_action and field == "interaction_mode" and "create_edit" in title_values:
            continue
        candidate_values = _as_values(semantic_metadata.get(field))
        matched = sorted(title_values & candidate_values)
        if not matched:
            continue
        score += FIELD_WEIGHTS.get(field, 1)
        fields.append(field)
        reasons.append(f"{field} matched {', '.join(matched)}")

    if status_action == STATUS_WORK_ACTION_SUMMARIZE:
        if "create_edit" in _as_values(semantic_metadata.get("interaction_mode")):
            score = 0
            reasons = []
            fields = []

    if status_action:
        action_values = _as_values(semantic_metadata.get("action"))
        if status_action in action_values:
            score += STATUS_WORK_SOFT_BONUS
            if "action" not in fields:
                fields.append("action")
            reasons.append(f"action status_work {status_action} soft boost")

    return transfer_sharing_semantic_adjustment(
        title,
        candidate_id,
        semantic_metadata,
        score,
        tuple(reasons),
        tuple(fields),
    )


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
