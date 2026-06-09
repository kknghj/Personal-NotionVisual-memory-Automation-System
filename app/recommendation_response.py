"""Build extended recommend-icon API responses (UI + logging correlation)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.models import RankedCandidate, RecommendResponse, Visual
from app.recommendation_logging import (
    TOP_CANDIDATES,
    _dedupe_rows,
    _new_recommendation_id,
    _observation_calibration_scores,
    _title_has_ui_anchor,
    _utc_timestamp,
    append_recommendation_log,
    build_recommendation_log_entry,
)
from app.recommender import find_best_visual_candidate_match, find_exact_title_match
from app.recommender import rank_visual_candidate_rows

logger = logging.getLogger(__name__)


NO_CANDIDATE_REASON = "적합한 후보를 찾지 못했습니다."


def _candidate_label(candidate_id: str, data: dict[str, Any]) -> str:
    usage = data.get("usage_context")
    if isinstance(usage, list):
        for item in usage:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return candidate_id.replace("_", " ")


def _candidate_summary_reason(row: Any) -> str:
    matched = getattr(row, "matched", "") or ""
    base = f"제목에「{matched}」가 포함됨" if matched else "제목 의미와 후보가 연결됨"
    reasons = getattr(row, "semantic_match_reason", ()) or ()
    if reasons:
        return f"{base}. {' · '.join(reasons[:2])}"
    return base


def _visual_from_data(data: dict[str, Any]) -> Visual | None:
    visual = data.get("visual")
    if not isinstance(visual, dict):
        return None
    vtype = visual.get("type")
    value = visual.get("value")
    if vtype not in ("emoji", "notion_icon") or not isinstance(value, str) or not value.strip():
        return None
    color = visual.get("color")
    return Visual(
        type=vtype,
        value=value,
        color=color if isinstance(color, str) and color.strip() else None,
    )


def build_ranked_candidates(
    title: str,
    candidates: dict[str, Any],
    *,
    limit: int = TOP_CANDIDATES,
) -> list[RankedCandidate]:
    key_title = title.strip()
    rows = _dedupe_rows(rank_visual_candidate_rows(key_title, candidates))
    if not rows:
        return []

    title_has_ui = _title_has_ui_anchor(key_title)
    calibration = _observation_calibration_scores(rows, title_has_ui)
    ranked: list[RankedCandidate] = []
    for rank, row in enumerate(rows[:limit], start=1):
        visual = _visual_from_data(row.data)
        if visual is None:
            continue
        ranked.append(
            RankedCandidate(
                rank=rank,
                candidate_id=row.candidate_id,
                visual=visual,
                score=calibration[row.candidate_id],
                label=_candidate_label(row.candidate_id, row.data),
                summary_reason=_candidate_summary_reason(row),
            )
        )
    return ranked


def _append_log(title: str, *, log_path: Path | None = None, **kwargs: Any) -> str:
    recommendation_id = _new_recommendation_id()
    try:
        body = build_recommendation_log_entry(
            title,
            recommendation_id=recommendation_id,
            **kwargs,
        )
        body["timestamp"] = _utc_timestamp()
        append_recommendation_log(body, log_path=log_path)
    except Exception:
        logger.warning(
            "recommendation log append failed (recommendation_id=%s)",
            recommendation_id,
            exc_info=True,
        )
    return recommendation_id


def run_recommendation(
    title: str,
    *,
    sample_cases: list[dict[str, Any]],
    visual_candidates: dict[str, Any],
    log_path: Path | None = None,
) -> RecommendResponse:
    """Execute recommendation, append observation log, return extended API response."""
    case = find_exact_title_match(title, sample_cases)
    if case is not None:
        visual = case.get("visual")
        if not visual or not isinstance(visual, dict):
            raise ValueError("일치하는 케이스에 visual 필드가 없습니다.")
        raw_reason = case.get("reason")
        reason = (
            raw_reason.strip()
            if isinstance(raw_reason, str) and raw_reason.strip()
            else "data/sample_cases.json의 제목과 정확히 일치하는 사례의 visual을 사용합니다."
        )
        wfs = case.get("workflow_resolution")
        if isinstance(wfs, int):
            reason = f"{reason} (기록된 workflow_resolution={wfs})"
        response_visual = Visual(**visual)
        recommendation_id = _append_log(
            title,
            log_path=log_path,
            case=case,
            recommended_visual=response_visual.model_dump(exclude_none=True),
        )
        return RecommendResponse(
            recommendation_id=recommendation_id,
            visual=response_visual,
            reason=reason,
            no_candidate=False,
            recommendation_path="sample_cases_exact_match",
            candidates=[],
        )

    cand = find_best_visual_candidate_match(title, visual_candidates)
    if cand is None:
        recommendation_id = _append_log(
            title,
            log_path=log_path,
            candidates=visual_candidates,
            recommended_visual=None,
        )
        return RecommendResponse(
            recommendation_id=recommendation_id,
            visual=None,
            reason=NO_CANDIDATE_REASON,
            no_candidate=True,
            recommendation_path="no_candidate",
            candidates=[],
        )

    data, cid, matched, wp, kres, idom = cand
    visual_raw = data.get("visual")
    if not visual_raw or not isinstance(visual_raw, dict):
        raise ValueError("선택된 data/visual_candidates 항목에 visual 필드가 없습니다.")
    reason = (
        "data/sample_cases에 같은 제목이 없어 data/visual_candidates로 매칭했습니다. "
        f"제목에 meaning「{matched}」가 포함되어 후보「{cid}」를 선택했습니다 "
        f"(정렬: interface_dominance={idom}, keyword_workflow_resolution={kres}, workflow_priority={wp})."
    )
    response_visual = Visual(**visual_raw)
    recommendation_id = _append_log(
        title,
        log_path=log_path,
        catalog_match=cand,
        candidates=visual_candidates,
        recommended_visual=response_visual.model_dump(exclude_none=True),
    )
    return RecommendResponse(
        recommendation_id=recommendation_id,
        visual=response_visual,
        reason=reason,
        no_candidate=False,
        recommendation_path="visual_candidates",
        candidates=build_ranked_candidates(title, visual_candidates),
    )
