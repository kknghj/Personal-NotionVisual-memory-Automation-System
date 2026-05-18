"""sample_cases.json 과 visual_candidates.json 의 visual 목록을 비교한다.

사용법 (프로젝트 루트에서)::

    python -m tools.compare_visuals
    python -m tools.compare_visuals --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.data_loader import DATA_DIR


def _visual_key(visual: dict[str, Any] | None) -> tuple[str, str] | None:
    if not isinstance(visual, dict):
        return None
    t = visual.get("type")
    v = visual.get("value")
    if t is None or v is None:
        return None
    return (str(t), str(v))


def _load_sample_visuals(path: Path) -> dict[tuple[str, str], list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise TypeError(f"{path} 는 배열 JSON 이어야 합니다.")
    by_visual: dict[tuple[str, str], list[str]] = defaultdict(list)
    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        title = row.get("title")
        vk = _visual_key(row.get("visual"))
        if vk is None:
            label = f"(행 {i}, title 없음)"
            by_visual[("__missing__", "__missing__")].append(
                str(title) if title is not None else label
            )
            continue
        by_visual[vk].append(str(title))
    return dict(by_visual)


def _load_candidate_visuals(path: Path) -> dict[tuple[str, str], list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path} 는 객체 JSON 이어야 합니다.")
    by_visual: dict[tuple[str, str], list[str]] = defaultdict(list)
    for cid, block in raw.items():
        if cid == "meta":
            continue
        if not isinstance(block, dict):
            continue
        vk = _visual_key(block.get("visual"))
        if vk is None:
            continue
        by_visual[vk].append(cid)
    return dict(by_visual)


def build_report(
    sample_path: Path,
    candidates_path: Path,
) -> dict[str, Any]:
    sample_map = _load_sample_visuals(sample_path)
    cand_map = _load_candidate_visuals(candidates_path)

    sample_keys = {k for k in sample_map if k != ("__missing__", "__missing__")}
    cand_keys = set(cand_map)

    only_in_samples = sorted(sample_keys - cand_keys)
    only_in_candidates = sorted(cand_keys - sample_keys)
    in_both = sorted(sample_keys & cand_keys)

    missing_rows = sample_map.get(("__missing__", "__missing__"), [])

    return {
        "sample_cases_path": str(sample_path),
        "visual_candidates_path": str(candidates_path),
        "counts": {
            "unique_visuals_in_sample_cases": len(sample_keys),
            "unique_visuals_in_visual_candidates": len(cand_keys),
            "in_both": len(in_both),
            "only_in_sample_cases": len(only_in_samples),
            "only_in_visual_candidates": len(only_in_candidates),
            "sample_rows_without_visual": len(missing_rows),
        },
        "only_in_sample_cases": [
            {"type": t, "value": v, "titles": sample_map[(t, v)]}
            for t, v in only_in_samples
        ],
        "only_in_visual_candidates": [
            {"type": t, "value": v, "candidate_ids": cand_map[(t, v)]}
            for t, v in only_in_candidates
        ],
        "in_both": [
            {
                "type": t,
                "value": v,
                "titles": sample_map[(t, v)],
                "candidate_ids": cand_map[(t, v)],
            }
            for t, v in in_both
        ],
        "sample_rows_missing_visual_field": missing_rows,
    }


def _print_human(report: dict[str, Any]) -> None:
    c = report["counts"]
    print("=== visual 비교 요약 ===")
    print(f"  sample_cases 고유 visual 수: {c['unique_visuals_in_sample_cases']}")
    print(f"  visual_candidates 고유 visual 수: {c['unique_visuals_in_visual_candidates']}")
    print(f"  양쪽 모두에 있음: {c['in_both']}")
    print(f"  sample 에만 있음 (candidates 미포함): {c['only_in_sample_cases']}")
    print(f"  candidates 에만 있음 (sample 미사용): {c['only_in_visual_candidates']}")
    if c["sample_rows_without_visual"]:
        print(f"  visual 필드 없는 sample 행: {c['sample_rows_without_visual']}")
    print()

    def line(t: str, v: str) -> str:
        return f"  {t}: {v!r}"

    if report["only_in_sample_cases"]:
        print("--- sample_cases 에만 있는 visual (추가 후보) ---")
        for item in report["only_in_sample_cases"]:
            print(line(item["type"], item["value"]))
            for title in item["titles"]:
                print(f"      · {title}")
        print()

    if report["only_in_visual_candidates"]:
        print("--- visual_candidates 에만 있는 visual ---")
        for item in report["only_in_visual_candidates"]:
            print(line(item["type"], item["value"]))
            for cid in item["candidate_ids"]:
                print(f"      · {cid}")
        print()

    print("--- 양쪽에 모두 있는 visual (일부) ---")
    for item in report["in_both"]:
        print(line(item["type"], item["value"]))
        print(f"      candidates: {', '.join(item['candidate_ids'])}")
        print(f"      sample 건수: {len(item['titles'])}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample",
        type=Path,
        default=DATA_DIR / "sample_cases.json",
        help="sample_cases.json 경로",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DATA_DIR / "visual_candidates.json",
        help="visual_candidates.json 경로",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 한 덩어리로 출력",
    )
    args = parser.parse_args()

    report = build_report(args.sample, args.candidates)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human(report)


if __name__ == "__main__":
    main()
