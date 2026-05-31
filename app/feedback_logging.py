"""Append-only user feedback / override observation logs (JSONL).

Records what the system recommended, what the user changed, and the final selection.
Does not alter ranking, scoring, or ontology — observation only.

Correlate with a recommendation run via ``recommendation_id`` (same UUID as
``logs/recommendation_log.jsonl``).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = Path("data/feedback_log.jsonl")

FeedbackType = Literal[
    "accepted",
    "override",
    "manual_without_recommendation",
    "no_candidate_selected",
]

FEEDBACK_TYPES: frozenset[str] = frozenset(
    {
        "accepted",
        "override",
        "manual_without_recommendation",
        "no_candidate_selected",
    }
)

REQUIRED_LOG_FIELDS: frozenset[str] = frozenset(
    {
        "timestamp",
        "recommendation_id",
        "input_title",
        "system_recommended_visual",
        "final_selected_visual",
        "feedback_type",
        "override_reason",
        "user_note",
        "accepted_system_recommendation",
    }
)


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _visual_payload(visual: Any) -> dict[str, Any] | None:
    """Minimal visual slice for feedback comparison (type, value, optional color)."""
    if not isinstance(visual, dict):
        return None
    vtype = visual.get("type")
    value = visual.get("value")
    if not isinstance(vtype, str) or not isinstance(value, str):
        return None
    out: dict[str, Any] = {"type": vtype, "value": value}
    color = visual.get("color")
    if isinstance(color, str) and color.strip():
        out["color"] = color
    return out


def _visuals_equal(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
) -> bool:
    if left is None or right is None:
        return left is right
    return left == right


def compute_accepted_system_recommendation(
    feedback_type: str,
    *,
    system_recommended_visual: dict[str, Any] | None,
    final_selected_visual: dict[str, Any] | None,
) -> bool:
    """Derive whether the user kept the system recommendation."""
    if feedback_type == "accepted":
        return True
    if feedback_type in ("override", "manual_without_recommendation", "no_candidate_selected"):
        return False
    return _visuals_equal(system_recommended_visual, final_selected_visual)


def build_feedback_log_entry(
    input_title: str,
    *,
    feedback_type: FeedbackType | str,
    recommendation_id: str | None = None,
    system_recommended_visual: Any = None,
    final_selected_visual: Any = None,
    override_reason: str | None = None,
    user_note: str | None = None,
    accepted_system_recommendation: bool | None = None,
) -> dict[str, Any]:
    """Build one JSON object for a user feedback event (without timestamp)."""
    if feedback_type not in FEEDBACK_TYPES:
        raise ValueError(
            f"feedback_type must be one of {sorted(FEEDBACK_TYPES)}, got {feedback_type!r}."
        )

    system_visual = _visual_payload(system_recommended_visual)
    final_visual = _visual_payload(final_selected_visual)

    if accepted_system_recommendation is None:
        accepted = compute_accepted_system_recommendation(
            feedback_type,
            system_recommended_visual=system_visual,
            final_selected_visual=final_visual,
        )
    else:
        accepted = accepted_system_recommendation

    return {
        "recommendation_id": recommendation_id,
        "input_title": input_title.strip(),
        "system_recommended_visual": system_visual,
        "final_selected_visual": final_visual,
        "feedback_type": feedback_type,
        "override_reason": override_reason if override_reason else None,
        "user_note": user_note if user_note else None,
        "accepted_system_recommendation": accepted,
    }


def append_feedback_log(
    entry: dict[str, Any],
    *,
    log_path: Path | None = None,
) -> None:
    """Append one observation line; creates parent directory when missing."""
    path = log_path or DEFAULT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def log_user_feedback(
    input_title: str,
    *,
    feedback_type: FeedbackType | str,
    recommendation_id: str | None = None,
    system_recommended_visual: Any = None,
    final_selected_visual: Any = None,
    override_reason: str | None = None,
    user_note: str | None = None,
    accepted_system_recommendation: bool | None = None,
    log_path: Path | None = None,
) -> bool:
    """Record one user feedback event.

    Logging failures are logged as warnings and do not propagate.

    Returns ``True`` when the log line was written, else ``False``.
    """
    try:
        body = build_feedback_log_entry(
            input_title,
            feedback_type=feedback_type,
            recommendation_id=recommendation_id,
            system_recommended_visual=system_recommended_visual,
            final_selected_visual=final_selected_visual,
            override_reason=override_reason,
            user_note=user_note,
            accepted_system_recommendation=accepted_system_recommendation,
        )
        body["timestamp"] = _utc_timestamp()
        append_feedback_log(body, log_path=log_path)
    except Exception:
        logger.warning(
            "feedback log append failed (recommendation_id=%s, feedback_type=%s)",
            recommendation_id,
            feedback_type,
            exc_info=True,
        )
        return False
    return True
