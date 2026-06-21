"""P5-B Feedback Statistics Analyzer — live UI feedback + recommendation logs.

Measures cognitive stability, semantic ambiguity, ranking confidence, and boundary
weakness — not raw accuracy alone. See ``docs/workflow_philosophy.md`` and
``docs/workflows/semantic_boundary_workflow.md``.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.feedback_export import format_visual_display
from app.feedback_logging import DEFAULT_LOG_PATH as DEFAULT_FEEDBACK_PATH
from app.feedback_ranking_snapshot import extract_margin_from_entry, load_recommendation_index
from app.recommendation_logging import DEFAULT_LOG_PATH as DEFAULT_RECOMMENDATION_PATH

DEFAULT_MARGIN_THRESHOLD = 0.03
AMBIGUITY_THRESHOLDS = (0.01, 0.03, 0.05)

OverrideTaxonomy = Literal[
    "wrong_recommendation",
    "boundary_disagreement",
    "ranking_instability",
    "metadata_gap",
]
AcceptTaxonomy = Literal["stable_accept", "unstable_accept", "unsure_accept"]

BOUNDARY_PATTERNS: dict[str, tuple[str, ...]] = {
    "action_vs_object": ("이동", "자료", "준비", "정리", "수정", "작성"),
    "channel_vs_document": ("전달", "보고", "송부", "제출", "공지"),
    "interface_vs_semantic": ("드라이브", "이동", "엑셀", "카톡", "메일"),
    "status_vs_workflow": ("현황", "상태", "마감", "확인", "작성"),
}

KNOWN_BOUNDARY_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("folder", "taxi_service", "folder vs taxi (object transfer vs commute)"),
    ("messenger_notice", "document_reporting", "messenger vs document"),
    ("meeting", "meal_planning", "meeting vs meal"),
    ("urgent_notice", "document_reporting", "notice vs report"),
)

_RANKING_INSTABILITY_HINTS = (
    "동점",
    "ranking",
    "안정",
    "margin",
    "score 차이",
    "거의",
    "맞음",
    "추천은 맞",
    "틀리지",
)
_METADATA_GAP_HINTS = ("metadata", "부족", "boost", "penalty", "근거")
_BOUNDARY_HINTS = ("맥락", "경계", "둘 다", "preference", "선호", "유의사항")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_recommendation_index(path: Path | None = None) -> dict[str, dict[str, Any]]:
    from app.feedback_ranking_snapshot import load_recommendation_index as _load_index

    return _load_index(path)


def _visuals_equal(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    if left is None or right is None:
        return left is right
    return left == right


def _feedback_bucket(feedback_type: str) -> str:
    if feedback_type == "accepted":
        return "accepted"
    if feedback_type == "override":
        return "override"
    if feedback_type in ("no_candidate_selected", "no_candidate", "manual_without_recommendation"):
        return "no_candidate"
    return "other"


def compute_top_margin(
    entry: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
) -> float | None:
    return extract_margin_from_entry(entry, recommendation)


def _entry_top_candidates(entry: dict[str, Any]) -> list[dict[str, Any]]:
    top1 = entry.get("top1_candidate_id")
    if not isinstance(top1, str) or not top1.strip():
        return []
    rows: list[dict[str, Any]] = [
        {
            "candidate_id": top1.strip(),
            "score": entry.get("top1_score"),
        }
    ]
    top2 = entry.get("top2_candidate_id")
    if isinstance(top2, str) and top2.strip():
        rows.append(
            {
                "candidate_id": top2.strip(),
                "score": entry.get("top2_score"),
            }
        )
    return rows


def is_ambiguous_margin(margin: float | None, threshold: float) -> bool:
    return margin is not None and margin <= threshold


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(hint in text or hint.lower() in lowered for hint in hints)


def _top_candidates(
    entry: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if entry:
        from_entry = _entry_top_candidates(entry)
        if from_entry:
            return from_entry
    if not recommendation:
        return []
    raw = recommendation.get("candidates") or []
    return [row for row in raw if isinstance(row, dict)]


def _workflow_key(
    entry: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
) -> str:
    if entry:
        top1 = entry.get("top1_candidate_id")
        if isinstance(top1, str) and top1.strip():
            return top1.strip()
    if not recommendation:
        return "unknown"
    top = recommendation.get("top_candidate")
    if isinstance(top, str) and top.strip():
        return top.strip()
    path = recommendation.get("recommendation_path")
    if isinstance(path, str) and path.strip():
        return path.strip()
    wf = recommendation.get("resolved_workflow")
    if wf is not None:
        return f"workflow_level_{wf}"
    return "unknown"


def _visual_key(visual: dict[str, Any] | None) -> str:
    display = format_visual_display(visual)
    return display or "none"


def _semantic_bonus_weak(
    entry: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
) -> bool:
    tops = _top_candidates(entry, recommendation)[:2]
    if len(tops) < 2:
        return False
    bonus1 = int(tops[0].get("semantic_bonus") or 0)
    bonus2 = int(tops[1].get("semantic_bonus") or 0)
    margin = compute_top_margin(entry, recommendation)
    return bonus1 == 0 and bonus2 == 0 and is_ambiguous_margin(margin, DEFAULT_MARGIN_THRESHOLD)


def classify_accepted(
    entry: dict[str, Any],
    recommendation: dict[str, Any] | None,
    *,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
) -> AcceptTaxonomy:
    explicit = entry.get("accept_quality")
    if explicit == "stable":
        return "stable_accept"
    if explicit == "unstable":
        return "unstable_accept"
    if explicit == "unsure":
        return "unsure_accept"

    margin = compute_top_margin(entry, recommendation)
    if margin is None:
        return "unsure_accept"
    if margin >= margin_threshold:
        return "stable_accept"
    return "unstable_accept"


def classify_override(
    entry: dict[str, Any],
    recommendation: dict[str, Any] | None,
    *,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
) -> OverrideTaxonomy:
    system_visual = entry.get("system_recommended_visual")
    final_visual = entry.get("final_selected_visual")
    visuals_match = _visuals_equal(system_visual, final_visual)
    override_reason = str(entry.get("override_reason") or "").strip()
    user_note = str(entry.get("user_note") or "")
    note_text = f"{override_reason} {user_note}"
    margin = compute_top_margin(entry, recommendation)

    if visuals_match:
        if _contains_any(user_note, _RANKING_INSTABILITY_HINTS) or (
            override_reason == "wrong_top_candidate"
            and is_ambiguous_margin(margin, margin_threshold)
        ):
            return "ranking_instability"
        if _semantic_bonus_weak(entry, recommendation) or _contains_any(note_text, _METADATA_GAP_HINTS):
            return "metadata_gap"
        if is_ambiguous_margin(margin, margin_threshold):
            return "ranking_instability"
        return "metadata_gap"

    if override_reason in {"channel_vs_object", "boundary_ambiguity", "document_vs_status"}:
        return "boundary_disagreement"
    if override_reason == "action_vs_object" and _contains_any(user_note, _BOUNDARY_HINTS):
        return "boundary_disagreement"
    if override_reason == "personal_preference":
        return "boundary_disagreement"
    if override_reason == "wrong_top_candidate":
        return "wrong_recommendation"
    if override_reason == "action_vs_object":
        return "wrong_recommendation"
    if override_reason == "other" and _contains_any(note_text, _BOUNDARY_HINTS):
        return "boundary_disagreement"
    return "wrong_recommendation"


@dataclass
class AnalyzedFeedbackRow:
    entry: dict[str, Any]
    recommendation: dict[str, Any] | None
    bucket: str
    accept_class: AcceptTaxonomy | None = None
    override_class: OverrideTaxonomy | None = None
    margin: float | None = None
    workflow: str = "unknown"
    system_visual: str = "none"
    final_visual: str = "none"
    is_ambiguous: bool = False
    boundary_hits: list[str] = field(default_factory=list)


def detect_boundary_patterns(
    title: str,
    entry: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
) -> list[str]:
    hits: list[str] = []
    text = title.strip()
    for pattern_name, keywords in BOUNDARY_PATTERNS.items():
        if sum(1 for kw in keywords if kw in text) >= 2:
            hits.append(pattern_name)

    tops = _top_candidates(entry, recommendation)
    if len(tops) >= 2:
        id1 = str(tops[0].get("candidate_id") or "")
        id2 = str(tops[1].get("candidate_id") or "")
        for left, right, label in KNOWN_BOUNDARY_PAIRS:
            pair = {left, right}
            if {id1, id2} == pair:
                hits.append(label)

    margin = compute_top_margin(entry, recommendation)
    if is_ambiguous_margin(margin, DEFAULT_MARGIN_THRESHOLD) and hits:
        return hits
    if is_ambiguous_margin(margin, DEFAULT_MARGIN_THRESHOLD) and len(tops) >= 2:
        hits.append("low_margin_top2_collision")
    return sorted(set(hits))


def enrich_feedback_row(
    entry: dict[str, Any],
    recommendation_index: dict[str, dict[str, Any]],
    *,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
) -> AnalyzedFeedbackRow:
    rid = entry.get("recommendation_id")
    recommendation = recommendation_index.get(rid) if isinstance(rid, str) else None
    bucket = _feedback_bucket(str(entry.get("feedback_type") or ""))
    margin = compute_top_margin(entry, recommendation)
    row = AnalyzedFeedbackRow(
        entry=entry,
        recommendation=recommendation,
        bucket=bucket,
        margin=margin,
        workflow=_workflow_key(entry, recommendation),
        system_visual=_visual_key(entry.get("system_recommended_visual")),
        final_visual=_visual_key(entry.get("final_selected_visual")),
        is_ambiguous=is_ambiguous_margin(margin, margin_threshold),
        boundary_hits=detect_boundary_patterns(
            str(entry.get("input_title") or ""),
            entry,
            recommendation,
        ),
    )
    if bucket == "accepted":
        row.accept_class = classify_accepted(
            entry, recommendation, margin_threshold=margin_threshold
        )
    elif bucket == "override":
        row.override_class = classify_override(
            entry, recommendation, margin_threshold=margin_threshold
        )
    return row


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct / 100.0
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[int(rank)]
    weight = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _ratio(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total * 100, 1)


def analyze_feedback_rows(
    rows: list[AnalyzedFeedbackRow],
    *,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
) -> dict[str, Any]:
    total = len(rows)
    accepted_rows = [row for row in rows if row.bucket == "accepted"]
    override_rows = [row for row in rows if row.bucket == "override"]
    no_candidate_rows = [row for row in rows if row.bucket == "no_candidate"]

    stable = sum(1 for row in accepted_rows if row.accept_class == "stable_accept")
    unstable = sum(1 for row in accepted_rows if row.accept_class == "unstable_accept")
    unsure = sum(1 for row in accepted_rows if row.accept_class == "unsure_accept")

    override_classes = Counter(row.override_class for row in override_rows if row.override_class)
    override_total = len(override_rows) or 1

    margins = [row.margin for row in rows if row.margin is not None]
    ranking_metrics = {
        "count_with_margin": len(margins),
        "p50": round(_percentile(margins, 50) or 0, 3) if margins else None,
        "p75": round(_percentile(margins, 75) or 0, 3) if margins else None,
        "p90": round(_percentile(margins, 90) or 0, 3) if margins else None,
        "minimum": round(min(margins), 3) if margins else None,
        "maximum": round(max(margins), 3) if margins else None,
        "mean": round(statistics.mean(margins), 3) if margins else None,
    }

    ambiguity_metrics: dict[str, Any] = {"thresholds": {}}
    for threshold in AMBIGUITY_THRESHOLDS:
        ambiguous_rows = [row for row in rows if is_ambiguous_margin(row.margin, threshold)]
        ambiguity_metrics["thresholds"][str(threshold)] = {
            "count": len(ambiguous_rows),
            "ratio_pct": _ratio(len(ambiguous_rows), total),
            "by_workflow": dict(
                Counter(row.workflow for row in ambiguous_rows).most_common(10)
            ),
            "by_visual": dict(
                Counter(row.system_visual for row in ambiguous_rows).most_common(10)
            ),
        }
    ambiguity_metrics["overall_ambiguity_rate_pct"] = ambiguity_metrics["thresholds"][
        str(margin_threshold)
    ]["ratio_pct"]

    workflow_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "accepted": 0,
            "override": 0,
            "unstable_accept": 0,
            "ranking_instability": 0,
            "ambiguous": 0,
        }
    )
    for row in rows:
        stats = workflow_stats[row.workflow]
        stats["count"] += 1
        if row.bucket == "accepted":
            stats["accepted"] += 1
            if row.accept_class == "unstable_accept":
                stats["unstable_accept"] += 1
        elif row.bucket == "override":
            stats["override"] += 1
            if row.override_class == "ranking_instability":
                stats["ranking_instability"] += 1
        if row.is_ambiguous:
            stats["ambiguous"] += 1

    workflow_risk_rows: list[dict[str, Any]] = []
    for workflow, stats in workflow_stats.items():
        count = stats["count"]
        workflow_risk_rows.append(
            {
                "workflow": workflow,
                "count": count,
                "accepted": stats["accepted"],
                "override": stats["override"],
                "unstable_accept": stats["unstable_accept"],
                "ranking_instability": stats["ranking_instability"],
                "override_rate_pct": _ratio(stats["override"], count),
                "ambiguity_rate_pct": _ratio(stats["ambiguous"], count),
            }
        )
    workflow_risk_rows.sort(
        key=lambda item: (-item["override_rate_pct"], -item["ambiguity_rate_pct"], item["workflow"])
    )

    visual_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "recommended_count": 0,
            "override_count": 0,
            "unstable_accept_count": 0,
            "margins": [],
        }
    )
    for row in rows:
        if row.bucket == "no_candidate":
            continue
        stats = visual_stats[row.system_visual]
        stats["recommended_count"] += 1
        if row.bucket == "override":
            stats["override_count"] += 1
        if row.accept_class == "unstable_accept":
            stats["unstable_accept_count"] += 1
        if row.margin is not None:
            stats["margins"].append(row.margin)

    visual_risk_rows: list[dict[str, Any]] = []
    for visual, stats in visual_stats.items():
        margins_for_visual = stats["margins"]
        visual_risk_rows.append(
            {
                "visual": visual,
                "recommended_count": stats["recommended_count"],
                "override_count": stats["override_count"],
                "unstable_accept_count": stats["unstable_accept_count"],
                "avg_margin": round(statistics.mean(margins_for_visual), 3)
                if margins_for_visual
                else None,
                "min_margin": round(min(margins_for_visual), 3) if margins_for_visual else None,
                "override_rate_pct": _ratio(stats["override_count"], stats["recommended_count"]),
            }
        )
    visual_risk_rows.sort(
        key=lambda item: (-item["override_rate_pct"], item["avg_margin"] or 0, item["visual"])
    )

    boundary_counter: Counter[str] = Counter()
    for row in rows:
        boundary_counter.update(row.boundary_hits)

    return {
        "overall": {
            "total_logs": total,
            "accepted_count": len(accepted_rows),
            "override_count": len(override_rows),
            "no_candidate_count": len(no_candidate_rows),
            "override_rate_pct": _ratio(len(override_rows), total),
        },
        "acceptance_metrics": {
            "stable_accept_count": stable,
            "unstable_accept_count": unstable,
            "unsure_accept_count": unsure,
            "stable_accept_pct": _ratio(stable, len(accepted_rows) or 1),
            "unstable_accept_pct": _ratio(unstable, len(accepted_rows) or 1),
            "unsure_accept_pct": _ratio(unsure, len(accepted_rows) or 1),
            "margin_threshold": margin_threshold,
        },
        "override_metrics": {
            taxonomy: {
                "count": override_classes.get(taxonomy, 0),
                "ratio_pct": _ratio(override_classes.get(taxonomy, 0), override_total),
            }
            for taxonomy in (
                "wrong_recommendation",
                "boundary_disagreement",
                "ranking_instability",
                "metadata_gap",
            )
        },
        "ranking_metrics": ranking_metrics,
        "ambiguity_metrics": ambiguity_metrics,
        "workflow_risk_metrics": workflow_risk_rows,
        "visual_risk_metrics": visual_risk_rows,
        "boundary_discovery": {
            "pattern_counts": dict(boundary_counter.most_common()),
            "known_pairs_observed": [
                label
                for label in boundary_counter
                if " vs " in label or label in {
                    "action_vs_object",
                    "channel_vs_document",
                    "interface_vs_semantic",
                    "status_vs_workflow",
                }
            ],
        },
        "rows": rows,
    }


def analyze_logs(
    feedback_path: Path | None = None,
    recommendation_path: Path | None = None,
    *,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
) -> dict[str, Any]:
    feedback_rows = _load_jsonl(feedback_path or DEFAULT_FEEDBACK_PATH)
    recommendation_index = load_recommendation_index(recommendation_path)
    enriched = [
        enrich_feedback_row(
            entry,
            recommendation_index,
            margin_threshold=margin_threshold,
        )
        for entry in feedback_rows
    ]
    return analyze_feedback_rows(enriched, margin_threshold=margin_threshold)


def format_statistics_report(summary: dict[str, Any]) -> str:
    overall = summary["overall"]
    acceptance = summary["acceptance_metrics"]
    override = summary["override_metrics"]
    ambiguity = summary["ambiguity_metrics"]
    ranking = summary["ranking_metrics"]
    margin_threshold = acceptance["margin_threshold"]

    lines = [
        "# P5-B Feedback Statistics",
        "",
        "> Visual workflow indexing system observability — cognitive stability over raw accuracy.",
        "",
        "## Executive Summary",
        "",
        f"- **Total logs:** {overall['total_logs']}",
        f"- **Override rate:** {overall['override_rate_pct']}% ({overall['override_count']}/{overall['total_logs']})",
        f"- **Unstable accept rate:** {acceptance['unstable_accept_pct']}% "
        f"({acceptance['unstable_accept_count']}/{overall['accepted_count']} accepted)",
        f"- **Unsure accept rate:** {acceptance.get('unsure_accept_pct', 0)}% "
        f"({acceptance.get('unsure_accept_count', 0)} accepted)",
        f"- **Ambiguity rate (margin ≤ {margin_threshold}):** "
        f"{ambiguity['overall_ambiguity_rate_pct']}%",
        "",
        "## Overall Metrics",
        "",
        "| metric | count |",
        "| --- | ---: |",
        f"| total logs | {overall['total_logs']} |",
        f"| accepted | {overall['accepted_count']} |",
        f"| override | {overall['override_count']} |",
        f"| no_candidate | {overall['no_candidate_count']} |",
        "",
        "## Acceptance Metrics",
        "",
        f"- stable_accept: **{acceptance['stable_accept_pct']}%** "
        f"({acceptance['stable_accept_count']})",
        f"- unstable_accept: **{acceptance['unstable_accept_pct']}%** "
        f"({acceptance['unstable_accept_count']})",
        f"- unsure_accept: **{acceptance.get('unsure_accept_pct', 0)}%** "
        f"({acceptance.get('unsure_accept_count', 0)})",
        f"- margin threshold: `{margin_threshold}`",
        "",
        "## Override Metrics",
        "",
        "| taxonomy | count | ratio |",
        "| --- | ---: | ---: |",
    ]
    for taxonomy, payload in override.items():
        lines.append(f"| {taxonomy} | {payload['count']} | {payload['ratio_pct']}% |")

    lines.extend(
        [
            "",
            "## Ranking Metrics (top1 − top2 margin)",
            "",
            f"- count with margin: {ranking['count_with_margin']}",
            f"- p50: {ranking['p50']}",
            f"- p75: {ranking['p75']}",
            f"- p90: {ranking['p90']}",
            f"- minimum: {ranking['minimum']}",
            f"- maximum: {ranking['maximum']}",
            f"- mean: {ranking['mean']}",
            "",
            "## Ambiguity Metrics",
            "",
        ]
    )
    for threshold, payload in ambiguity["thresholds"].items():
        lines.append(
            f"### margin ≤ {threshold}: {payload['count']} cases ({payload['ratio_pct']}%)"
        )
        if payload["by_workflow"]:
            lines.append("")
            lines.append("**By workflow (top):**")
            for wf, cnt in payload["by_workflow"].items():
                lines.append(f"- `{wf}`: {cnt}")
        if payload["by_visual"]:
            lines.append("")
            lines.append("**By visual (top):**")
            for vis, cnt in payload["by_visual"].items():
                lines.append(f"- `{vis}`: {cnt}")
        lines.append("")

    lines.extend(["## Top Risk Workflows", ""])
    lines.extend(
        [
            "| workflow | count | override_rate | ambiguity_rate | unstable_accept | ranking_instability |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["workflow_risk_metrics"][:10]:
        lines.append(
            f"| {row['workflow']} | {row['count']} | {row['override_rate_pct']}% | "
            f"{row['ambiguity_rate_pct']}% | {row['unstable_accept']} | {row['ranking_instability']} |"
        )

    lines.extend(["", "## Top Risk Visuals", ""])
    lines.extend(
        [
            "| visual | count | avg_margin | override_rate | unstable_accept |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["visual_risk_metrics"][:10]:
        avg = row["avg_margin"] if row["avg_margin"] is not None else "—"
        lines.append(
            f"| {row['visual']} | {row['recommended_count']} | {avg} | "
            f"{row['override_rate_pct']}% | {row['unstable_accept_count']} |"
        )

    lines.extend(["", "## Boundary Candidates", ""])
    patterns = summary["boundary_discovery"]["pattern_counts"]
    if patterns:
        for label, count in sorted(patterns.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {label} ({count})")
    else:
        lines.append("- (none detected)")

    lines.extend(["", "## Recommended Next Actions", "", "### Immediate", ""])
    immediate: list[str] = []
    if acceptance["unstable_accept_pct"] >= 20:
        immediate.append(
            "Review margin threshold / tie-break policy — unstable accepts exceed 20%."
        )
    if override["ranking_instability"]["count"]:
        immediate.append(
            "Add metadata boost/penalty for near-tie pairs flagged as ranking_instability."
        )
    if overall["no_candidate_count"]:
        immediate.append(
            f"Catalog gap backlog: {overall['no_candidate_count']} no_candidate events."
        )
    if not immediate:
        immediate.append("Continue observation; no critical immediate threshold change flagged.")
    lines.extend(f"- {item}" for item in immediate)

    lines.extend(["", "### Medium", ""])
    lines.extend(
        [
            "- Run semantic boundary workflow pilots on top ambiguous workflow pairs.",
            "- Extend candidate ontology for recurring boundary_disagreement clusters.",
            "",
            "### Long Term",
            "",
            "- Introduce ranking confidence score in API/UI.",
            "- Add accepted memo / quality signal in feedback schema.",
            "- Surface ranking explanation (top2 + margin) in feedback UI.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def format_insights_report(summary: dict[str, Any]) -> str:
    overall = summary["overall"]
    acceptance = summary["acceptance_metrics"]
    override = summary["override_metrics"]
    rows: list[AnalyzedFeedbackRow] = summary["rows"]

    duplicate_recommendations = Counter(
        row.entry.get("recommendation_id")
        for row in rows
        if row.entry.get("recommendation_id")
    )
    multi_feedback = [rid for rid, count in duplicate_recommendations.items() if count > 1]

    override_with_correct_visual = [
        row
        for row in rows
        if row.bucket == "override"
        and row.override_class in {"ranking_instability", "metadata_gap"}
    ]
    unstable_without_signal = [
        row
        for row in rows
        if row.accept_class == "unstable_accept" and not row.entry.get("user_note")
    ]

    lines = [
        "# P5-B Feedback Insights",
        "",
        "## Philosophy Check",
        "",
        "This analyzer treats **workflow recall speed** and **cognitive stability** as primary",
        "signals. Override is not always failure; accepted is not always high confidence.",
        "",
        "## Taxonomy Sufficiency",
        "",
    ]

    override_total = overall["override_count"] or 1
    wrong_pct = override["wrong_recommendation"]["ratio_pct"]
    boundary_pct = override["boundary_disagreement"]["ratio_pct"]
    ranking_pct = override["ranking_instability"]["ratio_pct"]
    metadata_pct = override["metadata_gap"]["ratio_pct"]

    lines.extend(
        [
            f"- **wrong_recommendation:** {wrong_pct}% of overrides — true top1 errors.",
            f"- **boundary_disagreement:** {boundary_pct}% — both candidates semantically plausible.",
            f"- **ranking_instability:** {ranking_pct}% — correct visual, low margin.",
            f"- **metadata_gap:** {metadata_pct}% — weak scoring differentiation.",
            "",
        ]
    )

    if ranking_pct > 0 or metadata_pct > 0:
        lines.append(
            "The four-class override taxonomy **captures live UI behavior** better than legacy "
            "accepted/override ratios alone. `wrong_top_candidate` UI reason still mixes true "
            "errors with ranking-instability memos — keep analyzer reclassification."
        )
    else:
        lines.append(
            "Current sample is small; taxonomy classes may shift as more ranking-instability "
            "memos accumulate."
        )

    lines.extend(["", "## Gaps Observed", ""])
    if multi_feedback:
        lines.append(
            f"- **Duplicate feedback on same recommendation_id:** {len(multi_feedback)} case(s). "
            "Users re-filed override memos when accepted lacked a note field "
            "(e.g. folder vs taxi at margin 0.001)."
        )
    lines.append(
        f"- **Unstable accepts without user note:** {len(unstable_without_signal)}/"
        f"{acceptance['unstable_accept_count']} — silent low-confidence accepts."
    )
    lines.append(
        f"- **Override used as ranking memo:** {len(override_with_correct_visual)} override(s) "
        "where system visual matched final selection."
    )

    lines.extend(["", "## Accepted Memo Feature", ""])
    lines.extend(
        [
            "**Status: implemented (schema v2).** UI accepts `accept_quality` + "
            "`ranking_confidence_note` on Accept; see `reports/p5b_feedback_schema_v2_plan.md`.",
            "",
        ]
    )
    if unstable_without_signal or multi_feedback:
        lines.extend(
            [
                "**Recommendation: yes — pilot accepted memo / quality flag.**",
                "",
                "Proposed schema extension:",
                "",
                "```json",
                "{",
                '  "accept_quality": "stable | unstable | unsure",',
                '  "ranking_confidence_note": "optional string",',
                '  "top2_candidate_id": "optional correlation field"',
                "}",
                "```",
                "",
                "UI: optional collapsible note on Accept when margin ≤ threshold.",
            ]
        )
    else:
        lines.append("Not yet critical at current volume; revisit after ~50 accepted events.")

    lines.extend(["", "## Feedback Schema Extensions", ""])
    lines.extend(
        [
            "| field | purpose |",
            "| --- | --- |",
            "| `accept_quality` | stable vs unstable accept without fake override |",
            "| `analyzer_override_class` | persisted post-hoc taxonomy for dashboards |",
            "| `top1_top2_margin` | snapshot at feedback time (denormalized from rec log) |",
            "| `top2_candidate_id` | boundary review / ontology work |",
            "| `semantic_boundary_tags[]` | action/object, channel/document, etc. |",
            "",
            "Keep observation-first: analyzer computes classes today; persist only after policy review.",
            "",
            "## Boundary Backlog Signals",
            "",
        ]
    )
    for label, count in summary["boundary_discovery"]["pattern_counts"].items():
        lines.append(f"- `{label}` — {count} hit(s)")

    lines.extend(["", "## Next Experiments", ""])
    experiments: list[str] = []
    if any(row.workflow == "folder" for row in rows):
        experiments.append("folder vs taxi_service: object-transfer metadata + commute penalty pilot")
    if boundary_pct >= 20:
        experiments.append("channel_vs_document boundary tests for reporting/전달 titles")
    if acceptance["unstable_accept_pct"] >= 25:
        experiments.append("raise tie-break weight or semantic bonus floor for unstable accepts")
    if not experiments:
        experiments.append("accumulate 50+ feedback rows before next ontology sprint")
    lines.extend(f"- {item}" for item in experiments)

    lines.extend(
        [
            "",
            "## Human Review Queue",
            "",
            "| title | feedback | class | margin | note |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    review_rows = sorted(
        [
            row
            for row in rows
            if row.bucket in {"accepted", "override"}
            and (row.is_ambiguous or row.override_class == "ranking_instability")
        ],
        key=lambda row: (row.margin if row.margin is not None else 999),
    )[:8]
    for row in review_rows:
        note = str(row.entry.get("user_note") or "")[:60].replace("|", "/")
        cls = row.override_class or row.accept_class or "—"
        margin = row.margin if row.margin is not None else "—"
        title = str(row.entry.get("input_title") or "").replace("|", "/")
        lines.append(
            f"| {title} | {row.bucket} | {cls} | {margin} | {note or '—'} |"
        )

    return "\n".join(lines).rstrip() + "\n"


def analyze_to_json(summary: dict[str, Any]) -> dict[str, Any]:
    payload = {
        key: value
        for key, value in summary.items()
        if key != "rows"
    }
    payload["analyzed_rows"] = [
        {
            "input_title": row.entry.get("input_title"),
            "recommendation_id": row.entry.get("recommendation_id"),
            "feedback_type": row.entry.get("feedback_type"),
            "bucket": row.bucket,
            "accept_class": row.accept_class,
            "override_class": row.override_class,
            "margin": row.margin,
            "workflow": row.workflow,
            "system_visual": row.system_visual,
            "final_visual": row.final_visual,
            "is_ambiguous": row.is_ambiguous,
            "boundary_hits": row.boundary_hits,
        }
        for row in summary["rows"]
    ]
    return payload


def write_reports(
    summary: dict[str, Any],
    *,
    statistics_path: Path,
    insights_path: Path,
) -> None:
    statistics_path.parent.mkdir(parents=True, exist_ok=True)
    statistics_path.write_text(format_statistics_report(summary), encoding="utf-8")
    insights_path.write_text(format_insights_report(summary), encoding="utf-8")


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description="P5-B feedback statistics analyzer (UI JSONL + recommendation log)."
    )
    parser.add_argument(
        "--feedback",
        type=Path,
        default=DEFAULT_FEEDBACK_PATH,
        help=f"Feedback JSONL (default: {DEFAULT_FEEDBACK_PATH})",
    )
    parser.add_argument(
        "--recommendation-log",
        type=Path,
        default=DEFAULT_RECOMMENDATION_PATH,
        help=f"Recommendation JSONL (default: {DEFAULT_RECOMMENDATION_PATH})",
    )
    parser.add_argument(
        "--margin-threshold",
        type=float,
        default=DEFAULT_MARGIN_THRESHOLD,
        help=f"Stable accept / ambiguity threshold (default: {DEFAULT_MARGIN_THRESHOLD})",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary to stdout")
    parser.add_argument(
        "--write-reports",
        action="store_true",
        help="Write reports/p5b_feedback_statistics.md and reports/p5b_feedback_insights.md",
    )
    parser.add_argument(
        "--statistics-report",
        type=Path,
        default=Path("reports/p5b_feedback_statistics.md"),
    )
    parser.add_argument(
        "--insights-report",
        type=Path,
        default=Path("reports/p5b_feedback_insights.md"),
    )
    args = parser.parse_args()

    summary = analyze_logs(
        args.feedback,
        args.recommendation_log,
        margin_threshold=args.margin_threshold,
    )

    if args.write_reports:
        write_reports(
            summary,
            statistics_path=args.statistics_report,
            insights_path=args.insights_report,
        )

    if args.json:
        print(json.dumps(analyze_to_json(summary), ensure_ascii=False, indent=2))
    elif not args.write_reports:
        print(format_statistics_report(summary), end="")


if __name__ == "__main__":
    main()
