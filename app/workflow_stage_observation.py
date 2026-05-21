"""Build feedback_log-compatible workflow_stage observations (calibration, not hard rules)."""

from __future__ import annotations

from typing import Any

from app.semantic_scoring import infer_workflow_stage_detail
from app.workflow_resolution import _canonical_title_text

REPORTING_CANDIDATE_IDS: frozenset[str] = frozenset(
    {"document_reporting", "result_reporting"},
)

_REPORTING_TITLE_HINTS: frozenset[str] = frozenset(
    {"보고", "브리핑", "상신", "현황", "진행", "추진", "결과", "중간", "최종"},
)


def _candidate_workflow_stages(candidate_data: dict[str, Any] | None) -> list[str]:
    if not candidate_data:
        return []
    meta = candidate_data.get("semantic_metadata")
    if not isinstance(meta, dict):
        return []
    raw = meta.get("workflow_stage")
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, str) and item.strip()]
    return []


def observation_is_relevant(
    title: str,
    *,
    top_candidate_id: str | None = None,
    ranking_candidate_ids: list[str] | None = None,
) -> bool:
    """Limit logging volume: reporting-axis titles and near-reporting rankings only."""
    canonical = _canonical_title_text(title)
    if any(hint in canonical for hint in _REPORTING_TITLE_HINTS):
        return True
    if top_candidate_id in REPORTING_CANDIDATE_IDS:
        return True
    if ranking_candidate_ids:
        if REPORTING_CANDIDATE_IDS.intersection(ranking_candidate_ids):
            return True
    detail = infer_workflow_stage_detail(title)
    if detail.get("workflow_stage_ambiguous"):
        return True
    if detail.get("inferred_workflow_stage"):
        return True
    return False


def build_workflow_stage_observation(
    title: str,
    *,
    selected_candidate_id: str | None = None,
    selected_candidate_data: dict[str, Any] | None = None,
    user_confirmed_workflow_stage: str | None = None,
) -> dict[str, Any]:
    """Flat feedback_log fields for workflow_stage semantic calibration."""
    detail = infer_workflow_stage_detail(title)
    matched = _candidate_workflow_stages(selected_candidate_data)

    inferred = detail.get("inferred_workflow_stage")
    confirmed = (user_confirmed_workflow_stage or "").strip() or None

    mismatch = False
    stage_for_alignment = confirmed or inferred
    if (
        stage_for_alignment
        and matched
        and selected_candidate_id in REPORTING_CANDIDATE_IDS
        and stage_for_alignment not in matched
    ):
        mismatch = True

    return {
        "inferred_workflow_stage": inferred,
        "matched_workflow_stage": matched,
        "user_confirmed_workflow_stage": confirmed or "",
        "workflow_stage_confidence": float(detail.get("workflow_stage_confidence") or 0.0),
        "workflow_stage_source": str(detail.get("workflow_stage_source") or ""),
        "workflow_stage_ambiguous": bool(detail.get("workflow_stage_ambiguous")),
        "workflow_stage_mismatch": mismatch,
        "inferred_workflow_stages_all": list(detail.get("inferred_workflow_stages_all") or []),
    }


def attach_workflow_stage_to_log_entry(
    entry: dict[str, Any],
    candidates: dict[str, Any],
    *,
    user_confirmed_workflow_stage: str | None = None,
) -> dict[str, Any]:
    """Attach optional workflow_stage block to an ambiguity/recommendation log row."""
    title = str(entry.get("title", ""))
    top_id = entry.get("top_candidate")
    top_id = top_id if isinstance(top_id, str) else None
    ranking_ids = [
        row["candidate"]
        for row in entry.get("rankings", [])
        if isinstance(row, dict) and isinstance(row.get("candidate"), str)
    ]

    if not observation_is_relevant(
        title,
        top_candidate_id=top_id,
        ranking_candidate_ids=ranking_ids,
    ):
        return entry

    top_data = candidates.get(top_id) if top_id else None
    top_data = top_data if isinstance(top_data, dict) else None
    observation = build_workflow_stage_observation(
        title,
        selected_candidate_id=top_id,
        selected_candidate_data=top_data,
        user_confirmed_workflow_stage=user_confirmed_workflow_stage,
    )
    return {**entry, **observation}
