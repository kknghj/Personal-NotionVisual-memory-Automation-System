"""Export scoring-log rows into feedback_log-shaped entries."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data_loader import append_feedback_log_entry, feedback_log_path
from app.feedback_event import build_ambiguity_scoring_event, normalize_feedback_event


def _scoring_row_to_feedback_entry(row: dict[str, Any], recorded_at: str) -> dict[str, Any]:
    top = row.get("top_candidate")
    normalized = normalize_feedback_event(row)
    workflow_stage = normalized.get("observations", {}).get("workflow_stage", {})
    workflow_stage = {
        "inferred_workflow_stage": workflow_stage.get("inferred_workflow_stage"),
        "matched_workflow_stage": workflow_stage.get("matched_workflow_stage") or [],
        "user_confirmed_workflow_stage": workflow_stage.get("user_confirmed_workflow_stage") or "",
        "workflow_stage_confidence": workflow_stage.get("workflow_stage_confidence", 0.0),
        "workflow_stage_source": workflow_stage.get("workflow_stage_source") or "",
        "workflow_stage_ambiguous": workflow_stage.get("workflow_stage_ambiguous", False),
        "workflow_stage_mismatch": workflow_stage.get("workflow_stage_mismatch", False),
        "inferred_workflow_stages_all": workflow_stage.get("inferred_workflow_stages_all") or [],
    }
    return build_ambiguity_scoring_event(
        recorded_at=recorded_at,
        title=str(row.get("title", "")),
        recommended_candidate_id=top if isinstance(top, str) else "",
        user_selected_candidate_id="",
        workflow_stage=workflow_stage,
    )


def export_from_scoring_log(
    scoring_log: Path,
    *,
    output: Path | None = None,
    append: bool = False,
) -> list[dict[str, Any]]:
    rows = json.loads(scoring_log.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"{scoring_log} must be a JSON array")

    recorded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized = normalize_feedback_event(row)
        workflow_stage = normalized.get("observations", {}).get("workflow_stage", {})
        if (
            "inferred_workflow_stage" not in workflow_stage
            and "workflow_stage_ambiguous" not in workflow_stage
        ):
            continue
        entry = _scoring_row_to_feedback_entry(row, recorded_at)
        entries.append(entry)
        if append:
            append_feedback_log_entry(entry)

    if output and not append:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Export workflow_stage observations to feedback_log shape.")
    parser.add_argument("--scoring-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=feedback_log_path())
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append each entry to data/feedback_log.json instead of overwriting --output",
    )
    args = parser.parse_args()
    entries = export_from_scoring_log(args.scoring_log, output=args.output, append=args.append)
    print(json.dumps({"exported_count": len(entries), "output": str(args.output)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
