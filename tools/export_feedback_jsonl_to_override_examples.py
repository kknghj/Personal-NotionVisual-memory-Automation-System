#!/usr/bin/env python3
"""Export UI feedback JSONL to override_examples-compatible JSON for P5-B analyzer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.feedback_export import feedback_entry_to_override_example, load_feedback_jsonl_lines
from app.feedback_logging import DEFAULT_LOG_PATH


def export_feedback_jsonl(
    input_path: Path,
    output_path: Path,
) -> list[dict]:
    rows = load_feedback_jsonl_lines(input_path)
    exported = [feedback_entry_to_override_example(row) for row in rows]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(exported, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return exported


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export data/feedback_log.jsonl to override_examples-compatible JSON.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Source feedback JSONL (default: data/feedback_log.jsonl)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/override_examples_from_ui.json"),
        help="Output JSON array path",
    )
    args = parser.parse_args()
    exported = export_feedback_jsonl(args.input, args.output)
    print(f"Wrote {len(exported)} rows to {args.output}")


if __name__ == "__main__":
    main()
