"""Feedback log event validation, normalization, and builders (observation log, not training)."""

from __future__ import annotations

from typing import Any

# Layer B workflow_stage slice — flat export keys (see docs/feedback_observations/workflow_stage.md).
WORKFLOW_STAGE_FLAT_KEYS: frozenset[str] = frozenset(
    {
        "inferred_workflow_stage",
        "matched_workflow_stage",
        "user_confirmed_workflow_stage",
        "workflow_stage_confidence",
        "workflow_stage_source",
        "workflow_stage_ambiguous",
        "workflow_stage_mismatch",
        "inferred_workflow_stages_all",
    }
)

_CORE_REQUIRED = ("event_type", "recorded_at")

# Layer A string fields: if present on the event, must be JSON strings.
_OPTIONAL_STRING_FIELDS = frozenset(
    {
        "title",
        "recommended_candidate_id",
        "user_selected_candidate_id",
        "source_surface",
        "user_confirmed_workflow_stage",
        "workflow_stage_source",
    }
)


def validate_feedback_event(event: object) -> None:
    """Validate core feedback event requirements. Unknown fields are allowed."""
    if not isinstance(event, dict):
        raise ValueError(
            f"feedback event must be a JSON object, got {type(event).__name__}."
        )
    for field in _CORE_REQUIRED:
        if field not in event:
            raise ValueError(f'feedback event missing required field "{field}".')
    event_type = event["event_type"]
    if not isinstance(event_type, str) or not event_type.strip():
        raise ValueError('feedback event "event_type" must be a non-empty string.')
    recorded_at = event["recorded_at"]
    if not isinstance(recorded_at, str) or not recorded_at.strip():
        raise ValueError('feedback event "recorded_at" must be a non-empty string.')
    for field in _OPTIONAL_STRING_FIELDS:
        if field in event and event[field] is not None and not isinstance(event[field], str):
            raise ValueError(
                f'feedback event "{field}" must be a string when present, '
                f"got {type(event[field]).__name__}."
            )


def normalize_feedback_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with flat workflow_stage fields also under observations.workflow_stage.

    Does not remove top-level flat fields (backward compatible for readers).
    """
    normalized = dict(event)
    flat_slice = {
        key: event[key] for key in WORKFLOW_STAGE_FLAT_KEYS if key in event
    }
    if not flat_slice:
        return normalized

    observations = normalized.get("observations")
    if not isinstance(observations, dict):
        observations = {}
    else:
        observations = dict(observations)

    existing = observations.get("workflow_stage")
    if isinstance(existing, dict):
        merged = {**flat_slice, **existing}
    else:
        merged = dict(flat_slice)

    observations["workflow_stage"] = merged
    normalized["observations"] = observations
    return normalized


def build_ambiguity_scoring_event(
    *,
    recorded_at: str,
    title: str = "",
    recommended_candidate_id: str = "",
    user_selected_candidate_id: str = "",
    workflow_stage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an ambiguity_scoring feedback event from scoring-log export fields."""
    event: dict[str, Any] = {
        "schema_version": 1,
        "source_surface": "ambiguity_scoring_log",
        "event_type": "ambiguity_scoring",
        "recorded_at": recorded_at,
        "title": title,
        "recommended_candidate_id": recommended_candidate_id,
        "user_selected_candidate_id": user_selected_candidate_id,
    }
    if workflow_stage:
        for key in WORKFLOW_STAGE_FLAT_KEYS:
            if key in workflow_stage:
                event[key] = workflow_stage[key]
    return event
