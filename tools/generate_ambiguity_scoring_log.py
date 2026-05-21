from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from app.candidate_row import CandidateRow
from app.data_loader import load_visual_candidates
from app.recommender import _pos_key_row, _row_sort_key, rank_visual_candidate_rows
from app.workflow_resolution import title_contains_interface_anchor

DEFAULT_TEST_SET = Path("tests/ambiguity/ambiguity_test_set.json")
DEFAULT_OUTPUT_DIR = Path("tests/ambiguity/ambiguity_results")
TOP_N = 5
HIGH_AMBIGUITY_THRESHOLD = 0.05
RANK_DIMENSIONS = 7


def _load_titles(path: Path) -> list[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must be a JSON array")

    titles: list[str] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"{path}: item {index} must be an object")
        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"{path}: item {index} must have a non-empty title")
        titles.append(title.strip())
    return titles


def _dedupe_rows(rows: Sequence[CandidateRow]) -> list[CandidateRow]:
    seen: set[str] = set()
    unique: list[CandidateRow] = []
    for row in rows:
        if row.candidate_id in seen:
            continue
        seen.add(row.candidate_id)
        unique.append(row)
    return unique


def _component_scores(rows: Sequence[CandidateRow], title_has_ui: bool) -> list[list[int]]:
    keys = [_row_sort_key(row, title_has_ui) for row in rows]
    columns = list(zip(*keys, strict=True))
    components: list[list[int]] = [[] for _ in rows]

    for column in columns:
        ranks = {value: index for index, value in enumerate(sorted(set(column)))}
        max_rank = max(ranks.values(), default=0)
        for row_index, value in enumerate(column):
            components[row_index].append(max_rank - ranks[value])

    return components


def _final_scores(rows: Sequence[CandidateRow], title_has_ui: bool) -> dict[str, float]:
    if not rows:
        return {}
    components = _component_scores(rows, title_has_ui)
    base = len(rows) + 1
    max_score = sum((base - 1) * base**power for power in range(RANK_DIMENSIONS))
    scores: dict[str, float] = {}
    for row, row_components in zip(rows, components, strict=True):
        weighted = sum(
            component * base**power
            for component, power in zip(
                row_components,
                reversed(range(RANK_DIMENSIONS)),
                strict=True,
            )
        )
        scores[row.candidate_id] = round(0.5 + (weighted / max_score / 2), 3)
    return scores


def _matched_rules(row: CandidateRow, title_has_ui: bool) -> list[str]:
    is_pair = row.rule_tier > 0
    rules: list[str] = []

    if row.matched:
        rules.append("token_match")
    if row.rule_tier:
        rules.append("pair_rule_tier")

    secondary_rule = "pair_rule.sort_secondary_wp" if is_pair else "workflow_priority"
    ordered_rules = (
        [
            "interface_dominance_effective",
            "keyword_workflow_resolution",
            secondary_rule,
        ]
        if title_has_ui
        else [
            secondary_rule,
            "interface_dominance_effective",
            "keyword_workflow_resolution",
        ]
    )
    for rule in ordered_rules:
        if rule == "interface_dominance_effective" and row.interface_dominance_effective:
            rules.append(rule)
        elif rule == "keyword_workflow_resolution" and row.keyword_workflow_resolution:
            rules.append(rule)
        elif rule == secondary_rule and row.sort_secondary_wp:
            rules.append(rule)

    rules.append("rank_tiebreak.match_position")
    rules.append("rank_tiebreak.matched_keyword_length")
    return rules


def _why_scored(row: CandidateRow, title_has_ui: bool) -> list[str]:
    is_pair = row.rule_tier > 0
    reasons: list[str] = []
    source = "pair rule" if is_pair else "visual_candidates meaning"

    if row.matched:
        reasons.append(f"'{row.matched}' matched from {source}")
    if is_pair:
        reasons.append("pair rule tier placed this row above meaning-only rows")
        reasons.append(f"pair sort_secondary_wp={row.sort_secondary_wp} applied")
    else:
        reasons.append(f"workflow_priority={row.sort_secondary_wp} used as secondary rank")

    if row.interface_dominance_effective:
        reasons.append(
            f"interface_dominance_effective={row.interface_dominance_effective} "
            "boosted UI/channel relevance"
        )
    if row.keyword_workflow_resolution:
        reasons.append(
            f"keyword_workflow_resolution={row.keyword_workflow_resolution} "
            "contributed to workflow specificity"
        )
    if title_has_ui:
        reasons.append("title has interface anchor, so dominance/resolution rank before secondary rank")

    reasons.append(f"match_position={_pos_key_row(row)} used as deterministic tie-break")
    reasons.append(f"matched_keyword_length={row.matched_keyword_length} used as tie-break")
    return reasons or ["fallback semantic similarity"]


def _no_candidate_entry(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "top_candidate": None,
        "ambiguity_gap": None,
        "high_ambiguity": False,
        "rankings": [
            {
                "rank": None,
                "candidate": None,
                "final_score": None,
                "ambiguity_gap": None,
                "why_scored": [
                    "no candidate row generated from pair rules or meaning token matches"
                ],
                "matched_rules": [],
            }
        ],
    }


def _title_log(title: str, candidates: dict[str, Any]) -> dict[str, Any]:
    rows = _dedupe_rows(rank_visual_candidate_rows(title, candidates))
    if not rows:
        return _no_candidate_entry(title)

    title_has_ui = title_contains_interface_anchor(title)
    scores = _final_scores(rows, title_has_ui)
    top_rows = rows[:TOP_N]
    rank1 = scores[top_rows[0].candidate_id]
    rank2 = scores[top_rows[1].candidate_id] if len(top_rows) > 1 else None
    gap = round(rank1 - rank2, 3) if rank2 is not None else None
    high_ambiguity = gap is not None and gap <= HIGH_AMBIGUITY_THRESHOLD

    rankings: list[dict[str, Any]] = []
    for rank, row in enumerate(top_rows, start=1):
        rankings.append(
            {
                "rank": rank,
                "candidate": row.candidate_id,
                "final_score": scores[row.candidate_id],
                "ambiguity_gap": gap,
                "why_scored": _why_scored(row, title_has_ui),
                "matched_rules": _matched_rules(row, title_has_ui),
            }
        )

    return {
        "title": title,
        "top_candidate": top_rows[0].candidate_id,
        "ambiguity_gap": gap,
        "high_ambiguity": high_ambiguity,
        "rankings": rankings,
    }


def _summary(logs: Sequence[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    gaps = [
        item["ambiguity_gap"]
        for item in logs
        if isinstance(item.get("ambiguity_gap"), int | float)
    ]
    lowest = sorted(
        (item for item in logs if isinstance(item.get("ambiguity_gap"), int | float)),
        key=lambda item: (item["ambiguity_gap"], item["title"]),
    )[:10]
    close = [
        item for item in logs if item.get("high_ambiguity") and item.get("ambiguity_gap") is not None
    ]

    return {
        "total_titles_tested": len(logs),
        "scoring_log_file_path": str(output_path),
        "average_ambiguity_gap": round(sum(gaps) / len(gaps), 3) if gaps else None,
        "lowest_ambiguity_gap_top_10": [
            {
                "title": item["title"],
                "top_candidate": item["top_candidate"],
                "ambiguity_gap": item["ambiguity_gap"],
            }
            for item in lowest
        ],
        "close_top1_top2_cases": [
            {
                "title": item["title"],
                "top_candidate": item["top_candidate"],
                "second_candidate": item["rankings"][1]["candidate"],
                "ambiguity_gap": item["ambiguity_gap"],
            }
            for item in close
            if len(item["rankings"]) > 1
        ],
    }


def _default_output_path(output_dir: Path, now: datetime) -> Path:
    return output_dir / f"{now:%Y-%m-%d_%H%M}_scoring_log.json"


def generate_log(test_set: Path, output_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    titles = _load_titles(test_set)
    candidates = load_visual_candidates()
    logs = [_title_log(title, candidates) for title in titles]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(logs, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return logs, _summary(logs, output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate ambiguity scoring logs.")
    parser.add_argument("--test-set", type=Path, default=DEFAULT_TEST_SET)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = args.output or _default_output_path(DEFAULT_OUTPUT_DIR, datetime.now())
    _logs, summary = generate_log(args.test_set, output_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
