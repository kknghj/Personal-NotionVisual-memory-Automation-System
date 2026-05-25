"""Compare before/after ranking snapshots and emit a markdown change summary."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT = Path("tests/ambiguity/ranking_snapshots/snapshot_diff_summary.md")

STABLE_ANCHOR_CANDIDATES = frozenset(
    {
        "mail_action",
        "document_sharing",
        "credential_sharing",
        "mail_sharing",
        "result_reporting",
        "document_reporting",
        "document_distribution",
        "mail_distribution",
    }
)
REPORTING_CANDIDATES = frozenset({"result_reporting", "document_reporting"})
DISTRIBUTION_CANDIDATES = frozenset({"document_distribution", "mail_distribution"})
SHARING_CANDIDATES = frozenset({"document_sharing", "credential_sharing", "mail_sharing"})


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_cases(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict) and item.get("title")]
    if isinstance(raw, dict):
        cases = raw.get("cases")
        if isinstance(cases, list):
            return [item for item in cases if isinstance(item, dict) and item.get("title")]
    raise ValueError("Unsupported snapshot format: expected a list of cases or {cases: [...]}")


def _ranking_rows(case: dict[str, Any]) -> list[dict[str, Any]]:
    rows = case.get("top3") or case.get("rankings") or []
    return [row for row in rows if isinstance(row, dict) and row.get("candidate")]


def _semantic_bonus(row: dict[str, Any]) -> int:
    return int(row.get("semantic_bonus") or 0)


def _bonus_for_candidate(rows: list[dict[str, Any]], candidate: str | None) -> int:
    if candidate is None:
        return 0
    for row in rows:
        if row.get("candidate") == candidate:
            return _semantic_bonus(row)
    return 0


def _normalize_case(case: dict[str, Any]) -> dict[str, Any]:
    rows = _ranking_rows(case)
    top = case.get("top_candidate")
    if top is None and rows:
        top = rows[0]["candidate"]

    top_bonus = _bonus_for_candidate(rows, top)
    second_bonus = _semantic_bonus(rows[1]) if len(rows) >= 2 else None
    gap = case.get("ambiguity_gap")
    if not isinstance(gap, int | float):
        gap = None

    bonus_gap_proxy = (top_bonus - second_bonus) if second_bonus is not None else None
    is_tie = len(rows) >= 2 and top_bonus == second_bonus

    return {
        "title": case["title"],
        "top_candidate": top,
        "top3": rows,
        "ambiguity_gap": gap,
        "bonus_gap_proxy": bonus_gap_proxy,
        "is_tie": is_tie,
        "top_semantic_bonus": top_bonus,
        "ranking_depth": len(rows),
    }


def _index_snapshot(path: Path) -> dict[str, dict[str, Any]]:
    return {case["title"]: case for case in (_normalize_case(item) for item in _extract_cases(_load_json(path)))}


def _movement_key(before_top: str | None, after_top: str | None) -> str:
    return f"{before_top or 'none'} -> {after_top or 'none'}"


def _regression_reasons(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    before_top = before["top_candidate"]
    after_top = after["top_candidate"]
    if before_top == after_top:
        return []

    reasons: list[str] = []
    if before_top in STABLE_ANCHOR_CANDIDATES:
        reasons.append(f"stable anchor `{before_top}` moved to `{after_top}`")

    if before_top == "mail_action" and after_top != "mail_action":
        reasons.append(f"mail_action displaced by `{after_top}`")

    if before_top in REPORTING_CANDIDATES and after_top in DISTRIBUTION_CANDIDATES:
        reasons.append(f"reporting `{before_top}` moved to distribution `{after_top}`")

    if before_top in SHARING_CANDIDATES and after_top not in SHARING_CANDIDATES:
        reasons.append(f"sharing `{before_top}` moved to `{after_top}`")

    if before_top is not None and after_top is None:
        reasons.append("top candidate lost (retrieval regression)")

    if before["top_semantic_bonus"] > 0 and after["top_semantic_bonus"] < before["top_semantic_bonus"]:
        reasons.append(
            "top semantic bonus decreased "
            f"({before['top_semantic_bonus']} -> {after['top_semantic_bonus']})"
        )

    return reasons


def _semantic_improvement_note(before: dict[str, Any], after: dict[str, Any]) -> str | None:
    before_bonus = before["top_semantic_bonus"]
    after_bonus = after["top_semantic_bonus"]
    before_top = before["top_candidate"]
    after_top = after["top_candidate"]

    if before_bonus == after_bonus:
        return None

    if before_top != after_top and after_bonus > before_bonus:
        return f"semantic_bonus: {before_bonus} -> {after_bonus}"
    if before_top == after_top and after_bonus > before_bonus:
        return f"semantic_bonus: {before_bonus} -> {after_bonus}"
    return None


def _gap_label(case: dict[str, Any]) -> str:
    if isinstance(case["ambiguity_gap"], int | float):
        return f"ambiguity_gap={case['ambiguity_gap']:.4f}"
    if case["bonus_gap_proxy"] is not None:
        return f"bonus_gap_proxy={case['bonus_gap_proxy']}"
    if case["is_tie"]:
        return "tie=yes"
    return "gap=n/a"


def _gap_delta_note(before: dict[str, Any], after: dict[str, Any]) -> str | None:
    before_gap = before["ambiguity_gap"]
    after_gap = after["ambiguity_gap"]
    if isinstance(before_gap, int | float) and isinstance(after_gap, int | float):
        delta = after_gap - before_gap
        direction = "widened" if delta > 0 else "narrowed" if delta < 0 else "unchanged"
        return f"ambiguity_gap: {before_gap:.4f} -> {after_gap:.4f} ({direction})"

    before_proxy = before["bonus_gap_proxy"]
    after_proxy = after["bonus_gap_proxy"]
    if before_proxy is not None and after_proxy is not None and before_proxy != after_proxy:
        return f"bonus_gap_proxy: {before_proxy} -> {after_proxy}"

    if before["is_tie"] != after["is_tie"]:
        before_state = "tie" if before["is_tie"] else "no tie"
        after_state = "tie" if after["is_tie"] else "no tie"
        return f"tie status: {before_state} -> {after_state}"

    return None


def analyze_snapshot_diff(before_path: Path, after_path: Path) -> dict[str, Any]:
    before_index = _index_snapshot(before_path)
    after_index = _index_snapshot(after_path)
    titles = sorted(before_index.keys() | after_index.keys())

    changed_top1: list[dict[str, Any]] = []
    semantic_improvements: list[dict[str, Any]] = []
    regression_candidates: list[dict[str, Any]] = []
    ambiguity_changes: list[dict[str, Any]] = []
    movement_clusters: Counter[str] = Counter()

    ties_before = 0
    ties_after = 0

    for title in titles:
        before = before_index.get(title)
        after = after_index.get(title)
        if before is None or after is None:
            regression_candidates.append(
                {
                    "title": title,
                    "reasons": [f"missing in {'before' if before is None else 'after'} snapshot"],
                }
            )
            continue

        if before["is_tie"]:
            ties_before += 1
        if after["is_tie"]:
            ties_after += 1

        before_top = before["top_candidate"]
        after_top = after["top_candidate"]
        if before_top != after_top:
            changed_top1.append(
                {
                    "title": title,
                    "movement": _movement_key(before_top, after_top),
                    "semantic_bonus": f"{before['top_semantic_bonus']} -> {after['top_semantic_bonus']}",
                }
            )
            movement_clusters[_movement_key(before_top, after_top)] += 1

        improvement = _semantic_improvement_note(before, after)
        if improvement:
            semantic_improvements.append({"title": title, "note": improvement})

        reasons = _regression_reasons(before, after)
        if reasons:
            regression_candidates.append({"title": title, "reasons": reasons})

        gap_note = _gap_delta_note(before, after)
        if gap_note or before["is_tie"] != after["is_tie"]:
            ambiguity_changes.append(
                {
                    "title": title,
                    "before": _gap_label(before),
                    "after": _gap_label(after),
                    "note": gap_note or "tie status changed",
                }
            )

    return {
        "before_path": str(before_path),
        "after_path": str(after_path),
        "compared_titles": len(titles),
        "changed_top1": changed_top1,
        "semantic_improvements": semantic_improvements,
        "regression_candidates": regression_candidates,
        "ambiguity_changes": ambiguity_changes,
        "movement_clusters": movement_clusters,
        "tie_counts": {
            "before": ties_before,
            "after": ties_after,
            "delta": ties_after - ties_before,
        },
    }


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Snapshot Diff Summary",
        "",
        f"- before: `{result['before_path']}`",
        f"- after: `{result['after_path']}`",
        f"- compared titles: {result['compared_titles']}",
        "",
        "## changed top1",
        "",
    ]

    if result["changed_top1"]:
        for item in result["changed_top1"]:
            lines.append(f"- {item['title']}")
            lines.append(f"  {item['movement']}")
            if item.get("semantic_bonus"):
                lines.append(f"  semantic_bonus: {item['semantic_bonus']}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## semantic improvements", ""])
    if result["semantic_improvements"]:
        for item in result["semantic_improvements"]:
            lines.append(f"- {item['title']}: {item['note']}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## regression candidates", ""])
    if result["regression_candidates"]:
        for item in result["regression_candidates"]:
            lines.append(f"- {item['title']}")
            for reason in item["reasons"]:
                lines.append(f"  - {reason}")
    else:
        lines.append("- (none)")

    tie_counts = result["tie_counts"]
    lines.extend(
        [
            "",
            "## ambiguity changes",
            "",
            f"- tie count: {tie_counts['before']} -> {tie_counts['after']} (delta {tie_counts['delta']:+d})",
            "",
        ]
    )
    if result["ambiguity_changes"]:
        for item in result["ambiguity_changes"]:
            lines.append(f"- {item['title']}: {item['before']} -> {item['after']}")
            lines.append(f"  - {item['note']}")
    else:
        lines.append("- (no per-title ambiguity deltas detected)")

    lines.extend(["", "## movement clusters", ""])
    if result["movement_clusters"]:
        for movement, count in result["movement_clusters"].most_common():
            lines.append(f"- {movement}: {count}")
    else:
        lines.append("- (none)")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare before/after ranking snapshots and write a markdown summary."
    )
    parser.add_argument("--before", type=Path, required=True, help="Before snapshot JSON")
    parser.add_argument("--after", type=Path, required=True, help="After snapshot JSON")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Markdown output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    result = analyze_snapshot_diff(args.before, args.after)
    markdown = _render_markdown(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
