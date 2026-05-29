"""Aggregate workflow_stage observations for calibration analytics."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.feedback_event import normalize_feedback_event


def _load_rows(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must be a JSON array")
    return [row for row in raw if isinstance(row, dict)]


def _has_stage_fields(workflow_stage: dict[str, Any]) -> bool:
    return (
        "inferred_workflow_stage" in workflow_stage
        or "workflow_stage_ambiguous" in workflow_stage
    )


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for row in rows:
        normalized = normalize_feedback_event(row)
        workflow_stage = normalized.get("observations", {}).get("workflow_stage", {})
        if _has_stage_fields(workflow_stage):
            stage_pairs.append((row, workflow_stage))
    reporting_pairs = [
        (row, ws)
        for row, ws in stage_pairs
        if row.get("recommended_candidate_id") in {"document_reporting", "result_reporting"}
        or row.get("top_candidate") in {"document_reporting", "result_reporting"}
    ]

    confusion: Counter[tuple[str | None, str]] = Counter()
    for row, ws in reporting_pairs:
        inferred = ws.get("inferred_workflow_stage")
        top = row.get("recommended_candidate_id") or row.get("top_candidate") or ""
        if isinstance(top, str):
            confusion[(inferred, top)] += 1

    progress_result_confusion = sum(
        count
        for (inferred, top), count in confusion.items()
        if inferred == "progress" and top == "result_reporting"
        or inferred == "result" and top == "document_reporting"
    )

    ambiguous_sources: Counter[str] = Counter()
    hyeonhwang_titles = 0
    ambiguous_count = 0
    mismatch_count = 0
    confidence_buckets: Counter[str] = Counter()

    for row, ws in stage_pairs:
        if ws.get("workflow_stage_ambiguous"):
            ambiguous_count += 1
        if ws.get("workflow_stage_mismatch"):
            mismatch_count += 1
        title = str(row.get("title", ""))
        if "현황" in title.replace(" ", ""):
            hyeonhwang_titles += 1
        source = str(ws.get("workflow_stage_source") or "")
        if source.startswith("ambiguous:") or source.startswith("contextual:"):
            ambiguous_sources[source] += 1
        conf = float(ws.get("workflow_stage_confidence") or 0.0)
        if conf <= 0.2:
            confidence_buckets["0.0-0.2"] += 1
        elif conf <= 0.65:
            confidence_buckets["0.21-0.65"] += 1
        elif conf <= 0.75:
            confidence_buckets["0.66-0.75"] += 1
        else:
            confidence_buckets["0.76-1.0"] += 1

    confirmed = [
        (row, ws)
        for row, ws in stage_pairs
        if isinstance(ws.get("user_confirmed_workflow_stage"), str)
        and str(ws.get("user_confirmed_workflow_stage", "")).strip()
    ]
    calibration: dict[str, Any] = {"labeled_count": len(confirmed), "accuracy_by_bucket": {}}
    if confirmed:
        bucket_hits: dict[str, list[bool]] = defaultdict(list)
        for row, ws in confirmed:
            conf = float(ws.get("workflow_stage_confidence") or 0.0)
            bucket = (
                "0.0-0.2"
                if conf <= 0.2
                else "0.21-0.65"
                if conf <= 0.65
                else "0.66-0.75"
                if conf <= 0.75
                else "0.76-1.0"
            )
            confirmed_stage = str(ws["user_confirmed_workflow_stage"]).strip()
            inferred = ws.get("inferred_workflow_stage")
            bucket_hits[bucket].append(inferred == confirmed_stage)
        calibration["accuracy_by_bucket"] = {
            bucket: round(sum(hits) / len(hits), 3) for bucket, hits in bucket_hits.items()
        }

    return {
        "total_rows": len(rows),
        "stage_observation_rows": len(stage_pairs),
        "reporting_subset_rows": len(reporting_pairs),
        "workflow_stage_confusion_matrix": {
            f"inferred={inferred or 'null'} -> top={top}": count
            for (inferred, top), count in sorted(
                confusion.items(),
                key=lambda item: (str(item[0][0]), str(item[0][1])),
            )
        },
        "progress_result_cross_confusion": progress_result_confusion,
        "ambiguous_token_frequency": dict(ambiguous_sources),
        "hyeonhwang_title_count": hyeonhwang_titles,
        "ambiguous_stage_count": ambiguous_count,
        "stage_mismatch_count": mismatch_count,
        "stage_mismatch_rate": round(mismatch_count / len(stage_pairs), 3) if stage_pairs else None,
        "confidence_distribution": dict(confidence_buckets),
        "confidence_calibration": calibration,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze workflow_stage observations in a log file.")
    parser.add_argument("log_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = analyze(_load_rows(args.log_path))
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
