from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

LATEST_LOG = Path("tests/ambiguity/ambiguity_results/2026-05-21_workflow_stage_scoring_log.json")
RESULTS_DIR = Path("tests/ambiguity/ambiguity_results")
SNAPSHOT_DIR = Path("tests/ambiguity/ranking_snapshots")

WORKFLOW_CANDIDATES = frozenset(
    {
        "document_distribution",
        "document_sharing",
        "mail_distribution",
        "mail_sharing",
        "document_reporting",
        "result_reporting",
        "notice_posting",
        "public_posting",
        "publication_posting",
        "publication_announcement",
        "approval_request",
        "review_request",
        "submission_request",
        "document_submission",
        "document_request",
    }
)

GENERIC_NOISE_CANDIDATES = frozenset(
    {"room_cleaning", "event_preparation", "education_fieldwork", "mail_action", "document_edit"}
)

INTERFACE_TERMS = ("메일", "카카오톡", "카톡", "슬랙", "채팅", "QR", "엑셀", "네이버폼", "줌", "화상회의")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _previous_log_path(latest: Path) -> Path:
    logs = sorted(RESULTS_DIR.glob("*_scoring_log.json"))
    previous = [path for path in logs if path.name < latest.name]
    if not previous:
        raise FileNotFoundError(f"No previous scoring log found before {latest}")
    return previous[-1]


def _ranking_rows(item: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in item.get("rankings", []) if row.get("candidate") is not None]


def _top_candidate(item: dict[str, Any]) -> str | None:
    value = item.get("top_candidate")
    return value if isinstance(value, str) else None


def _gap(item: dict[str, Any]) -> float | None:
    value = item.get("ambiguity_gap")
    return value if isinstance(value, int | float) else None


def _ranking_depth(item: dict[str, Any]) -> int:
    return len(_ranking_rows(item))


def _top_row(item: dict[str, Any]) -> dict[str, Any]:
    rows = _ranking_rows(item)
    return rows[0] if rows else {}


def _semantic_bonus_total(item: dict[str, Any]) -> int:
    return sum(int(row.get("semantic_bonus") or 0) for row in _ranking_rows(item))


def _top_semantic_bonus(item: dict[str, Any]) -> int:
    return int(_top_row(item).get("semantic_bonus") or 0)


def _suppression_applied(item: dict[str, Any]) -> bool:
    return any(
        "generic_token_suppression_applied" in (row.get("matched_rules") or [])
        for row in _ranking_rows(item)
    )


def _candidate_list(item: dict[str, Any]) -> list[str]:
    return [row["candidate"] for row in _ranking_rows(item)]


def _classify_change(
    title: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> tuple[str, list[str], list[str]]:
    before_top = _top_candidate(before)
    after_top = _top_candidate(after)
    notes: list[str] = []
    labels: list[str] = []

    if before_top is None and after_top is not None:
        labels.append("retrieval_improvement")
        notes.append("candidate retrieval coverage recovered")

    if _suppression_applied(after) and (before_top in GENERIC_NOISE_CANDIDATES or before_top != after_top):
        labels.append("generic_noise_reduction")
        notes.append("generic token leakage reduced")

    if after_top in WORKFLOW_CANDIDATES and _top_semantic_bonus(after) > _top_semantic_bonus(before):
        labels.append("semantic_improvement")
        notes.append("workflow semantic candidate won or gained stronger evidence")

    if any(term in title for term in INTERFACE_TERMS) and after_top != before_top:
        labels.append("interface_anchor_recovery")
        notes.append("interface/channel anchor affected ranking movement")

    if before_top != after_top and after_top in WORKFLOW_CANDIDATES:
        labels.append("workflow_boundary_improvement")
        notes.append("ranking moved toward explicit workflow boundary")

    if not labels and before_top == after_top:
        labels.append("stable")
        notes.append("top candidate remained stable")
    elif not labels:
        labels.append("ranking_shift")
        notes.append("top candidate changed without a clear semantic improvement signal")

    primary = next((label for label in labels if label != "stable"), labels[0])
    return primary, labels, notes


def _regression_risks(
    snapshot: dict[str, Any],
    before: dict[str, Any],
    after: dict[str, Any],
) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    before_gap = _gap(before)
    after_gap = _gap(after)
    before_top = _top_candidate(before)
    after_top = _top_candidate(after)
    after_candidates = _candidate_list(after)

    def add(kind: str, severity: str, reason: str) -> None:
        risks.append(
            {
                "title": snapshot["title"],
                "before": before_top,
                "after": after_top,
                "regression_type": kind,
                "severity": severity,
                "reason": reason,
                "before_ambiguity_gap": before_gap,
                "after_ambiguity_gap": after_gap,
            }
        )

    if before_top is not None and after_top is None:
        add("retrieval_loss", "high", "candidate retrieval disappeared after semantic ranking changes")

    if isinstance(before_gap, float | int) and isinstance(after_gap, float | int):
        if after_gap + 0.02 < before_gap:
            add("ambiguity_worsened", "medium", "top1/top2 gap narrowed materially")
        elif before_gap > 0.05 and after_gap <= 0.005:
            add("candidate_overlap_increase", "low", "candidate competition became nearly tied")

    if (
        before_top is not None
        and before_top != after_top
        and _top_semantic_bonus(after) > 0
        and isinstance(after_gap, float | int)
        and after_gap <= 0.005
    ):
        add("semantic_bonus_overreach_risk", "medium", "semantic bonus changed top1 but rank gap is near-zero")

    if len(after_candidates) >= 2 and after_candidates[0] in WORKFLOW_CANDIDATES and after_candidates[1] in WORKFLOW_CANDIDATES:
        if isinstance(after_gap, float | int) and after_gap <= 0.005:
            add("ontology_overlap_hotspot", "low", "neighbor workflow candidates are almost tied")

    return risks


def _improvement_score(snapshot: dict[str, Any]) -> int:
    score = 0
    labels = set(snapshot["change_labels"])
    score += 5 if "retrieval_improvement" in labels else 0
    score += 4 if "generic_noise_reduction" in labels else 0
    score += 3 if "semantic_improvement" in labels else 0
    score += 2 if "workflow_boundary_improvement" in labels else 0
    score += 1 if snapshot["ranking_change"]["ranking_depth_delta"] > 0 else 0
    return score


def _reporting_pair_snapshots(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    """Metrics focused on document_reporting vs result_reporting disambiguation."""
    reporting_keywords = ("보고", "진행상황", "현황", "결과", "추진")
    subset = [
        item
        for item in snapshots
        if any(kw in item["title"] for kw in reporting_keywords)
        and (
            "document_reporting" in item["before"]["top5_candidates"]
            or "result_reporting" in item["before"]["top5_candidates"]
            or "document_reporting" in item["after"]["top5_candidates"]
            or "result_reporting" in item["after"]["top5_candidates"]
        )
    ]
    confusion_before = 0
    confusion_after = 0
    separated_after = 0
    for item in subset:
        before_top5 = item["before"]["top5_candidates"][:2]
        after_top5 = item["after"]["top5_candidates"][:2]
        before_pair = (
            len(before_top5) >= 2
            and before_top5[0] in {"document_reporting", "result_reporting"}
            and before_top5[1] in {"document_reporting", "result_reporting"}
            and isinstance(item["before"]["ambiguity_gap"], int | float)
            and item["before"]["ambiguity_gap"] <= 0.005
        )
        after_pair = (
            len(after_top5) >= 2
            and after_top5[0] in {"document_reporting", "result_reporting"}
            and after_top5[1] in {"document_reporting", "result_reporting"}
            and isinstance(item["after"]["ambiguity_gap"], int | float)
            and item["after"]["ambiguity_gap"] <= 0.005
        )
        if before_pair:
            confusion_before += 1
        if after_pair:
            confusion_after += 1
        if before_pair and not after_pair:
            separated_after += 1
    return {
        "titles_in_reporting_focus_set": len(subset),
        "near_tied_reporting_pair_before": confusion_before,
        "near_tied_reporting_pair_after": confusion_after,
        "near_tied_pairs_resolved": separated_after,
        "top_candidate_flips_between_reporting_pair": sum(
            1
            for item in subset
            if item["changed"]
            and {item["before"]["top_candidate"], item["after"]["top_candidate"]}
            == {"document_reporting", "result_reporting"}
        ),
    }


def _summarize(snapshots: list[dict[str, Any]], regressions: list[dict[str, Any]]) -> dict[str, Any]:
    before_gaps = [item["before"]["ambiguity_gap"] for item in snapshots if isinstance(item["before"]["ambiguity_gap"], int | float)]
    after_gaps = [item["after"]["ambiguity_gap"] for item in snapshots if isinstance(item["after"]["ambiguity_gap"], int | float)]
    before_no_candidate = sum(1 for item in snapshots if item["before"]["top_candidate"] is None)
    after_no_candidate = sum(1 for item in snapshots if item["after"]["top_candidate"] is None)
    before_depth = [item["before"]["ranking_depth"] for item in snapshots]
    after_depth = [item["after"]["ranking_depth"] for item in snapshots]
    before_high = sum(1 for item in snapshots if item["before"]["high_ambiguity"])
    after_high = sum(1 for item in snapshots if item["after"]["high_ambiguity"])
    semantic_before = sum(item["before"]["semantic_bonus_total"] for item in snapshots)
    semantic_after = sum(item["after"]["semantic_bonus_total"] for item in snapshots)
    semantic_row_before = sum(
        1 for item in snapshots for value in (item["before"]["top_semantic_bonus"],) if value > 0
    )
    semantic_row_after = sum(
        1 for item in snapshots for value in (item["after"]["top_semantic_bonus"],) if value > 0
    )
    suppression_before = sum(1 for item in snapshots if item["before"]["suppression_applied"])
    suppression_after = sum(1 for item in snapshots if item["after"]["suppression_applied"])
    comparable_gaps = [
        (item["before"]["ambiguity_gap"], item["after"]["ambiguity_gap"])
        for item in snapshots
        if isinstance(item["before"]["ambiguity_gap"], int | float)
        and isinstance(item["after"]["ambiguity_gap"], int | float)
    ]

    label_counts: dict[str, int] = {}
    for item in snapshots:
        for label in item["change_labels"]:
            label_counts[label] = label_counts.get(label, 0) + 1

    after_top_counts: dict[str, int] = {}
    for item in snapshots:
        top = item["after"]["top_candidate"] or "none"
        after_top_counts[top] = after_top_counts.get(top, 0) + 1

    improvement_top = sorted(
        snapshots,
        key=lambda item: (-_improvement_score(item), item["title"]),
    )[:10]

    risky_top = sorted(
        regressions,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item["severity"], 3),
            item["after_ambiguity_gap"] if isinstance(item["after_ambiguity_gap"], int | float) else 99,
            item["title"],
        ),
    )[:10]

    return {
        "source_logs": {
            "before": "",
            "after": str(LATEST_LOG),
        },
        "movement_metrics": {
            "total_titles": len(snapshots),
            "top_candidate_changed_count": sum(1 for item in snapshots if item["changed"]),
            "no_candidate_before": before_no_candidate,
            "no_candidate_after": after_no_candidate,
            "no_candidate_decrease": before_no_candidate - after_no_candidate,
            "semantic_bonus_total_before": semantic_before,
            "semantic_bonus_total_after": semantic_after,
            "semantic_bonus_total_delta": semantic_after - semantic_before,
            "top_semantic_bonus_applied_before_count": semantic_row_before,
            "top_semantic_bonus_applied_after_count": semantic_row_after,
            "top_semantic_bonus_applied_delta": semantic_row_after - semantic_row_before,
            "suppression_applied_before_count": suppression_before,
            "suppression_applied_after_count": suppression_after,
            "high_ambiguity_before": before_high,
            "high_ambiguity_after": after_high,
            "high_ambiguity_delta": after_high - before_high,
            "average_ambiguity_gap_before": round(mean(before_gaps), 3) if before_gaps else None,
            "average_ambiguity_gap_after": round(mean(after_gaps), 3) if after_gaps else None,
            "average_ranking_depth_before": round(mean(before_depth), 3),
            "average_ranking_depth_after": round(mean(after_depth), 3),
            "ranking_depth_delta": round(mean(after_depth) - mean(before_depth), 3),
            "titles_with_depth_increase": sum(
                1 for item in snapshots if item["ranking_change"]["ranking_depth_delta"] > 0
            ),
            "titles_with_top2_competition_before": sum(1 for depth in before_depth if depth >= 2),
            "titles_with_top2_competition_after": sum(1 for depth in after_depth if depth >= 2),
            "ambiguity_gap_improved_count": sum(1 for before, after in comparable_gaps if after > before),
            "ambiguity_gap_worsened_count": sum(1 for before, after in comparable_gaps if after < before),
            "ambiguity_gap_unchanged_count": sum(1 for before, after in comparable_gaps if after == before),
        },
        "change_label_counts": dict(sorted(label_counts.items())),
        "top_candidate_distribution_after": dict(sorted(after_top_counts.items())),
        "most_improved_top_10": [
            {
                "title": item["title"],
                "change_type": item["change_type"],
                "before": item["before"]["top_candidate"],
                "after": item["after"]["top_candidate"],
                "notes": item["notes"],
            }
            for item in improvement_top
        ],
        "most_risky_regression_top_10": risky_top,
        "semantic_recommender_assessment": {
            "semantic_rows_increased": semantic_after > semantic_before,
            "retrieval_coverage_improved": after_no_candidate < before_no_candidate,
            "candidate_competition_increased": mean(after_depth) > mean(before_depth),
            "summary": (
                "semantic workflow competition increased: more titles have candidate rows, "
                "semantic metadata contributes to ranking, and generic token rows are explicitly dampened"
            ),
        },
        "keyword_dominance_remaining_areas": [
            item["title"]
            for item in snapshots
            if item["after"]["semantic_bonus_total"] == 0 and item["after"]["top_candidate"] is not None
        ][:20],
        "ontology_overlap_hotspots": [
            item["title"]
            for item in snapshots
            if any(risk["title"] == item["title"] and risk["regression_type"] == "ontology_overlap_hotspot" for risk in regressions)
        ][:20],
        "next_tuning_priorities": [
            "tune ambiguous 현황-only titles with feedback labels before hard stage rules",
            "add semantic metadata to legacy candidates still relying on raw token rank",
            "review near-zero gap publication/request overlaps before turning snapshots into hard regression gates",
        ],
        "workflow_stage_ambiguity_analysis": _reporting_pair_snapshots(snapshots),
    }


def generate_snapshots(latest_log: Path = LATEST_LOG) -> dict[str, Any]:
    previous_log = _previous_log_path(latest_log)
    before_items = {item["title"]: item for item in _load_json(previous_log)}
    after_items = {item["title"]: item for item in _load_json(latest_log)}
    titles = sorted(before_items.keys() | after_items.keys())

    snapshots: list[dict[str, Any]] = []
    improvements: list[dict[str, Any]] = []
    regressions: list[dict[str, Any]] = []

    for title in titles:
        before = before_items.get(title, {"title": title, "top_candidate": None, "rankings": []})
        after = after_items.get(title, {"title": title, "top_candidate": None, "rankings": []})
        change_type, labels, notes = _classify_change(title, before, after)
        before_candidates = _candidate_list(before)
        after_candidates = _candidate_list(after)
        snapshot = {
            "title": title,
            "before": {
                "top_candidate": _top_candidate(before),
                "ambiguity_gap": _gap(before),
                "high_ambiguity": bool(before.get("high_ambiguity")),
                "ranking_depth": _ranking_depth(before),
                "top5_candidates": before_candidates[:5],
                "top_semantic_bonus": _top_semantic_bonus(before),
                "semantic_bonus_total": _semantic_bonus_total(before),
                "suppression_applied": _suppression_applied(before),
            },
            "after": {
                "top_candidate": _top_candidate(after),
                "ambiguity_gap": _gap(after),
                "high_ambiguity": bool(after.get("high_ambiguity")),
                "ranking_depth": _ranking_depth(after),
                "top5_candidates": after_candidates[:5],
                "top_semantic_bonus": _top_semantic_bonus(after),
                "semantic_bonus_total": _semantic_bonus_total(after),
                "suppression_applied": _suppression_applied(after),
            },
            "changed": _top_candidate(before) != _top_candidate(after),
            "change_type": change_type,
            "change_labels": labels,
            "ranking_change": {
                "top_candidate_changed": _top_candidate(before) != _top_candidate(after),
                "ranking_depth_delta": _ranking_depth(after) - _ranking_depth(before),
                "entered_top5": sorted(set(after_candidates[:5]) - set(before_candidates[:5])),
                "exited_top5": sorted(set(before_candidates[:5]) - set(after_candidates[:5])),
            },
            "semantic_bonus_change": {
                "top_delta": _top_semantic_bonus(after) - _top_semantic_bonus(before),
                "total_delta": _semantic_bonus_total(after) - _semantic_bonus_total(before),
            },
            "suppression_change": {
                "before": _suppression_applied(before),
                "after": _suppression_applied(after),
                "changed": _suppression_applied(before) != _suppression_applied(after),
            },
            "notes": notes,
        }
        snapshots.append(snapshot)

        if any(label in labels for label in (
            "semantic_improvement",
            "retrieval_improvement",
            "generic_noise_reduction",
            "interface_anchor_recovery",
            "workflow_boundary_improvement",
        )):
            improvements.append(
                {
                    "title": title,
                    "improvement_type": change_type,
                    "improvement_labels": labels,
                    "before": snapshot["before"],
                    "after": snapshot["after"],
                    "notes": notes,
                }
            )

        regressions.extend(_regression_risks(snapshot, before, after))

    summary = _summarize(snapshots, regressions)
    summary["source_logs"]["before"] = str(previous_log)

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(SNAPSHOT_DIR / "before_vs_after_snapshot.json", snapshots)
    _write_json(SNAPSHOT_DIR / "ranking_movement_summary.json", summary)
    _write_json(SNAPSHOT_DIR / "semantic_improvement_cases.json", improvements)
    _write_json(SNAPSHOT_DIR / "regression_cases.json", regressions)
    return summary


def main() -> None:
    summary = generate_snapshots()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
