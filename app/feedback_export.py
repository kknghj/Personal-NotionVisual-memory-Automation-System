"""P5-B-compatible export helpers for UI feedback JSONL."""

from __future__ import annotations

from typing import Any


def format_visual_display(visual: dict[str, Any] | None) -> str | None:
    """Convert structured visual to override_examples display string."""
    if not visual or not isinstance(visual, dict):
        return None
    value = str(visual.get("value") or "").strip()
    if not value:
        return None
    if visual.get("type") == "emoji":
        return value
    color = str(visual.get("color") or "").strip()
    if color:
        return f"{value} ({color})"
    return value


def feedback_entry_to_override_example(entry: dict[str, Any]) -> dict[str, Any]:
    """Map one ``data/feedback_log.jsonl`` line to override_examples shape."""
    system = format_visual_display(entry.get("system_recommended_visual"))
    final = format_visual_display(entry.get("final_selected_visual"))
    feedback_type = str(entry.get("feedback_type") or "")

    if feedback_type == "no_candidate_selected" or (
        feedback_type == "accepted" and system is None and final is None
    ):
        system = "없음"

    note_parts: list[str] = []
    override_reason = entry.get("override_reason")
    if isinstance(override_reason, str) and override_reason.strip():
        note_parts.append(f"override_reason={override_reason.strip()}")
    user_note = entry.get("user_note")
    if isinstance(user_note, str) and user_note.strip():
        note_parts.append(user_note.strip())

    return {
        "title": str(entry.get("input_title") or ""),
        "recommended_visual": system or "없음",
        "final_visual": final or "",
        "confidence": None,
        "note": " | ".join(note_parts),
        "source": "feedback_ui",
        "recommendation_id": entry.get("recommendation_id"),
        "feedback_type": feedback_type,
        "recorded_at": entry.get("timestamp"),
    }


def load_feedback_jsonl_lines(path) -> list[dict[str, Any]]:
    import json
    from pathlib import Path

    log_path = Path(path)
    if not log_path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows
