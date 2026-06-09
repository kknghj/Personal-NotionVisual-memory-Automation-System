"""Feedback UI API routes (POST /feedback, GET /feedback/recent, GET /visuals/catalog)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.data_loader import load_visual_candidates
from app.feedback_logging import log_user_feedback
from app.feedback_read import read_recent_feedback
from app.models import (
    OVERRIDE_REASONS,
    FeedbackRequest,
    FeedbackResponse,
    VisualCatalogItem,
    VisualCatalogResponse,
)
from app.recommendation_response import _candidate_label, _visual_from_data

router = APIRouter(tags=["feedback"])

_visual_candidates: dict | None = None


def get_visual_candidates() -> dict:
    global _visual_candidates
    if _visual_candidates is None:
        _visual_candidates = load_visual_candidates()
    return _visual_candidates


def _normalize_feedback_type(feedback_type: str) -> str:
    if feedback_type == "no_candidate":
        return "no_candidate_selected"
    return feedback_type


def _resolve_storage_feedback_type(body: FeedbackRequest) -> str:
    normalized = _normalize_feedback_type(body.feedback_type)
    if normalized == "no_candidate_selected":
        return normalized
    if body.system_recommended_visual is None and body.final_selected_visual is not None:
        return "manual_without_recommendation"
    return normalized


@router.post("/feedback", response_model=FeedbackResponse)
def post_feedback(body: FeedbackRequest) -> FeedbackResponse:
    storage_type = _resolve_storage_feedback_type(body)

    if storage_type == "override":
        if body.final_selected_visual is None:
            raise HTTPException(status_code=422, detail="override requires final_selected_visual.")
        reason = (body.override_reason or "").strip()
        if not reason or reason not in OVERRIDE_REASONS:
            raise HTTPException(
                status_code=422,
                detail=f"override requires override_reason in {sorted(OVERRIDE_REASONS)}.",
            )

    if storage_type == "manual_without_recommendation":
        if body.final_selected_visual is None:
            raise HTTPException(
                status_code=422,
                detail="manual selection requires final_selected_visual.",
            )
        reason = (body.override_reason or "").strip()
        if not reason or reason not in OVERRIDE_REASONS:
            raise HTTPException(
                status_code=422,
                detail=f"manual override requires override_reason in {sorted(OVERRIDE_REASONS)}.",
            )

    if storage_type == "accepted":
        if body.system_recommended_visual is None:
            raise HTTPException(status_code=422, detail="accepted requires system_recommended_visual.")
        final = body.final_selected_visual or body.system_recommended_visual
    elif storage_type == "no_candidate_selected":
        final = body.final_selected_visual
    else:
        final = body.final_selected_visual

    system_payload: dict[str, Any] | None = (
        body.system_recommended_visual.model_dump(exclude_none=True)
        if body.system_recommended_visual
        else None
    )
    final_payload: dict[str, Any] | None = (
        final.model_dump(exclude_none=True) if final else None
    )

    ok = log_user_feedback(
        body.input_title,
        feedback_type=storage_type,
        recommendation_id=body.recommendation_id,
        system_recommended_visual=system_payload,
        final_selected_visual=final_payload,
        override_reason=body.override_reason,
        user_note=body.user_note,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="feedback log write failed.")
    return FeedbackResponse(feedback_type=storage_type)


@router.get("/feedback/recent")
def get_feedback_recent(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    return read_recent_feedback(limit=limit)


@router.get("/visuals/catalog", response_model=VisualCatalogResponse)
def get_visuals_catalog() -> VisualCatalogResponse:
    catalog = get_visual_candidates()
    items: list[VisualCatalogItem] = []
    for candidate_id, data in sorted(catalog.items()):
        if candidate_id == "meta" or not isinstance(data, dict):
            continue
        if "workflow_priority" not in data:
            continue
        visual = _visual_from_data(data)
        if visual is None:
            continue
        items.append(
            VisualCatalogItem(
                candidate_id=candidate_id,
                visual=visual,
                label=_candidate_label(candidate_id, data),
            )
        )
    return VisualCatalogResponse(items=items)
