"""Analyze reporting_current_state experiment against manifest expectations."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path("tests/ambiguity/reporting_current_state_manifest.json")


def _load_manifest() -> dict[str, list[dict[str, Any]]]:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict[str, Any]]] = {}
    for key in (
        "reporting_stage_cases",
        "status_ambiguity_cases",
        "result_lifecycle_cases",
        "intentionally_ambiguous_cases",
    ):
        grouped[key] = [item for item in raw.get(key, []) if isinstance(item, dict)]
    return grouped


def _index_log(path: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {row["title"]: row for row in rows if isinstance(row, dict) and row.get("title")}


def _near_reporting_tie(row: dict[str, Any]) -> bool:
    rankings = row.get("rankings") or []
    if len(rankings) < 2:
        return False
    first = rankings[0].get("candidate")
    second = rankings[1].get("candidate")
    gap = row.get("ambiguity_gap")
    return (
        first in {"document_reporting", "result_reporting"}
        and second in {"document_reporting", "result_reporting"}
        and isinstance(gap, int | float)
        and gap <= 0.005
    )


def analyze(log_path: Path) -> dict[str, Any]:
    log = _index_log(log_path)
    manifest = _load_manifest()
    by_group: dict[str, Any] = {}
    all_cases: list[tuple[str, dict[str, Any]]] = []

    for group, cases in manifest.items():
        group_stats: list[dict[str, Any]] = []
        for case in cases:
            title = case["title"]
            row = log.get(title, {})
            actual_top = row.get("top_candidate")
            inferred = row.get("inferred_workflow_stage")
            ambiguous = row.get("workflow_stage_ambiguous")
            conf = float(row.get("workflow_stage_confidence") or 0.0)
            expected = case.get("expected_workflow_stage_behavior", "")
            expected_ok = True
            if expected in {"null", "ambiguous_or_null"}:
                expected_ok = inferred is None or ambiguous
            elif expected == "progress":
                expected_ok = inferred in {None, "progress"} or ambiguous
            elif expected == "result":
                expected_ok = inferred in {"result", "final"} or actual_top == "result_reporting"
            elif expected == "interim":
                expected_ok = inferred in {"interim", "progress", None} or actual_top == "document_reporting"

            likely = set(case.get("likely_competing_candidates") or [])
            top_in_likely = actual_top in likely if actual_top else False

            group_stats.append(
                {
                    "title": title,
                    "expected_ambiguity_level": case.get("expected_ambiguity_level"),
                    "actual_top_candidate": actual_top,
                    "inferred_workflow_stage": inferred,
                    "workflow_stage_ambiguous": ambiguous,
                    "workflow_stage_confidence": conf,
                    "workflow_stage_mismatch": row.get("workflow_stage_mismatch"),
                    "near_reporting_tie": _near_reporting_tie(row),
                    "expected_behavior_ok": expected_ok,
                    "top_in_likely_competitors": top_in_likely,
                    "top5": [r.get("candidate") for r in (row.get("rankings") or [])[:5]],
                }
            )
            all_cases.append((group, case))

        by_group[group] = {
            "count": len(group_stats),
            "expected_behavior_ok_rate": round(
                sum(1 for item in group_stats if item["expected_behavior_ok"]) / len(group_stats),
                3,
            )
            if group_stats
            else None,
            "near_reporting_tie_count": sum(1 for item in group_stats if item["near_reporting_tie"]),
            "cases": group_stats,
        }

    false_certainty = [
        item
        for group_data in by_group.values()
        for item in group_data["cases"]
        if float(item.get("workflow_stage_confidence") or 0) >= 0.8
        and (
            item.get("workflow_stage_ambiguous")
            or (
                item.get("inferred_workflow_stage")
                and "현황" in item["title"].replace(" ", "")
                and item.get("expected_ambiguity_level") == "high"
            )
        )
    ]

    overfit_keywords = Counter()
    for group_data in by_group.values():
        for item in group_data["cases"]:
            title = item["title"]
            top = item.get("actual_top_candidate")
            if top not in {"document_reporting", "result_reporting"}:
                continue
            for kw in ("제출", "공유", "정리"):
                if kw in title:
                    overfit_keywords[kw] += 1

    return {
        "log_path": str(log_path),
        "manifest_path": str(MANIFEST_PATH),
        "group_summaries": by_group,
        "false_certainty_cases": false_certainty,
        "false_certainty_count": len(false_certainty),
        "keyword_overfit_to_reporting": dict(overfit_keywords),
        "required_case_checklist": {
            title: log.get(title, {}).get("top_candidate")
            for title in [
                "전국 식생활교육 현황 보고",
                "사업 운영 결과 현황 보고",
                "부서별 현황 자료 공유",
                "주요사업 추진현황 주간회의 자료 작성",
                "보험 가입현황 제출",
                "비상소집 응소자 현황 제출",
            ]
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = analyze(args.log_path)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
