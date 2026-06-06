"""P5-B Feedback Statistics Analyzer for override examples.

Aggregates override feedback using the reduced taxonomy in
``docs/feedback_override_taxonomy.md``. Does not modify recommendation logic.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from tools.analyze_override_patterns import (
    classify_gap_type,
    classify_primary_pattern,
    example_status,
    is_no_candidate_recommendation,
    normalize_visual,
    parse_final_visual_parts,
)

DEFAULT_INPUT = Path("data/override_examples.json")
DEFAULT_TOP_N = 10

TAXONOMY_CATEGORIES = (
    "no_candidate",
    "workflow_mismatch",
    "visual_mismatch",
    "boundary_ambiguity",
    "channel_vs_object",
    "action_vs_object",
    "object_vs_status",
    "personal_preference",
    "uncategorized",
)

SOURCE_TYPES = (
    "CANDIDATE_ABSENT",
    "CANDIDATE_WRONG_TOP",
    "CANDIDATE_NEAR_TIE",
    "PIPELINE_SKIP",
    "PHILOSOPHY_MISMATCH",
)

INFERRED_GAP_TYPES = (
    "inferred_workflow_boundary",
    "inferred_channel_object",
    "inferred_action_object",
    "inferred_document_channel",
    "inferred_meeting_meal",
    "inferred_no_candidate",
    "inferred_ambiguous_channel",
)

WORKFLOW_FIELD_CANDIDATES = (
    "workflow",
    "resolved_workflow",
    "system_workflow",
    "expected_workflow",
    "selected_workflow",
)

SYSTEM_VISUAL_FIELDS = (
    "system_recommended_visual",
    "recommended_visual",
    "recommended_visual",
    "top_candidate",
)

USER_VISUAL_FIELDS = (
    "user_selected_visual",
    "final_visual",
    "override_visual",
    "selected_visual",
)

_PERSONAL_HINTS = ("선호", "색", "orange", "파란", "갈색", "연상", "회상", "이미지")
_BOUNDARY_HINTS = ("맥락", "경계", "일 수 있", "일수있", "모두 가능", "ambiguous", "애매")
_MEETING_MEAL_HINTS = ("회의", "오찬", "식사", "다과", "점심", "저녁")
_STATUS_HINTS = ("현황", "상태", "마감", "일정", "확인 대상")
_CHANNEL_HINTS = ("메일", "전화", "카톡", "이메일", "메신저", "📧", "📞", "💬")
_ACTION_HINTS = ("실제 행동", "행위", "행동", "등록", "예약", "픽업", "참석", "제작")
_OBJECT_HINTS = ("대상", "중점", "보도자료", "영상", "배너", "포스터", "물품", "매트리스")


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(hint in text or hint.lower() in lowered for hint in hints)


def _first_nested(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    taxonomy = item.get("taxonomy")
    if isinstance(taxonomy, dict):
        for key in keys:
            if key in taxonomy and taxonomy[key] not in (None, ""):
                return taxonomy[key]
    override_analysis = item.get("override_analysis")
    if isinstance(override_analysis, dict):
        for key in keys:
            if key in override_analysis and override_analysis[key] not in (None, ""):
                return override_analysis[key]
    return None


def _pick_visual(item: dict[str, Any], field_names: tuple[str, ...]) -> str:
    value = _first_nested(item, *field_names)
    return normalize_visual(str(value) if value is not None else "")


def extract_workflow(item: dict[str, Any]) -> str | None:
    raw = _first_nested(item, *WORKFLOW_FIELD_CANDIDATES)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


@lru_cache(maxsize=1)
def _load_visual_candidates() -> dict[str, Any]:
    from app.data_loader import load_visual_candidates

    return load_visual_candidates()


@lru_cache(maxsize=1)
def _load_sample_cases() -> list[dict[str, Any]]:
    from app.data_loader import load_sample_cases

    return load_sample_cases()


def format_visual_display(visual: dict[str, Any] | None) -> str | None:
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


def _visual_matches_target(engine_visual: str | None, target_visual: str | None) -> bool:
    engine = normalize_visual(engine_visual)
    target = normalize_visual(target_visual)
    if not engine or not target:
        return False
    if engine == target:
        return True
    parts = parse_final_visual_parts(target_visual)
    if any(normalize_visual(part) == engine for part in parts):
        return True
    catalog = _load_visual_candidates()
    engine_ids = candidate_ids_for_visual(engine_visual, catalog)
    target_ids = candidate_ids_for_visual(target_visual, catalog)
    return bool(engine_ids and target_ids and set(engine_ids) & set(target_ids))


def _visual_part_matches(part: str, candidate_data: dict[str, Any]) -> bool:
    vis = candidate_data.get("visual") or {}
    if not isinstance(vis, dict):
        return False
    value = str(vis.get("value") or "")
    color = str(vis.get("color") or "")
    part_l = part.lower()
    val_l = value.lower()
    if part == value or part_l == val_l:
        return True
    m = re.match(r"^(.+?)\s*\(\s*(\w+)\s*\)\s*$", part)
    if m:
        name, part_color = m.group(1).strip().lower(), m.group(2).lower()
        if name == val_l:
            return not color or color.lower() == part_color
    label = f"{value} ({color})" if color else value
    if part_l == label.lower():
        return True
    return bool(val_l) and (part_l in val_l or val_l in part_l)


def candidate_ids_for_visual(visual: str | None, catalog: dict[str, Any]) -> list[str]:
    parts = parse_final_visual_parts(visual)
    if not parts:
        return []
    hits: list[str] = []
    for cid, data in catalog.items():
        if cid == "meta" or not isinstance(data, dict):
            continue
        if "workflow_priority" not in data:
            continue
        if any(_visual_part_matches(part, data) for part in parts):
            hits.append(cid)
    return hits


def resolve_engine_candidate_id(title: str, catalog: dict[str, Any]) -> str | None:
    from app.recommender import find_best_visual_candidate_match

    match = find_best_visual_candidate_match(title, catalog)
    if match is None:
        return None
    return match.candidate_id


def workflow_fit_label(candidate_id: str | None, catalog: dict[str, Any]) -> str | None:
    if not candidate_id:
        return None
    data = catalog.get(candidate_id)
    if not isinstance(data, dict):
        return candidate_id
    meta = data.get("semantic_metadata")
    if isinstance(meta, dict):
        fits = meta.get("workflow_fit")
        if isinstance(fits, list) and fits:
            return str(fits[0])
    return candidate_id


def classify_source_type(item: dict[str, Any]) -> str:
    explicit = _first_nested(
        item,
        "source_type",
        "override_source_type",
    )
    if explicit:
        return str(explicit)

    if is_no_candidate_recommendation(item):
        return "CANDIDATE_ABSENT"

    note = str(item.get("note") or "")
    confidence = item.get("confidence")
    if _contains_any(note, _PERSONAL_HINTS) and "실제 행동" not in note:
        return "PHILOSOPHY_MISMATCH"
    if isinstance(confidence, int) and confidence < 70 and _contains_any(note, _BOUNDARY_HINTS):
        return "CANDIDATE_NEAR_TIE"
    return "CANDIDATE_WRONG_TOP"


def classify_cause_type(item: dict[str, Any], primary_pattern: str) -> str | None:
    explicit = _first_nested(item, "cause_type", "semantic_cause_label", "semantic_cause")
    if explicit:
        return str(explicit)

    note = str(item.get("note") or "")
    title = str(item.get("title") or "")
    text = f"{note} {title}"

    if is_no_candidate_recommendation(item):
        return "catalog_gap"
    if primary_pattern == "channel_priority":
        return "object_vs_channel"
    if primary_pattern == "interface_priority":
        return "interface_ignored"
    if primary_pattern == "object_priority":
        return "object_priority"
    if primary_pattern == "action_priority":
        return "action_not_captured"
    if _contains_any(text, _BOUNDARY_HINTS):
        return "ontology_boundary_blur"
    if _contains_any(note, _PERSONAL_HINTS):
        return "visual_wrong_recall"
    return None


def classify_taxonomy_category(item: dict[str, Any], primary_pattern: str) -> str:
    explicit = _first_nested(item, "taxonomy_category", "cause_type")
    if explicit and str(explicit) in TAXONOMY_CATEGORIES:
        return str(explicit)

    if example_status(item) == "accepted":
        return "uncategorized"

    note = str(item.get("note") or "")
    title = str(item.get("title") or "")
    text = f"{note} {title}"

    if is_no_candidate_recommendation(item):
        return "no_candidate"
    if _contains_any(note, _PERSONAL_HINTS) and primary_pattern != "action_priority":
        return "personal_preference"
    if _contains_any(text, _BOUNDARY_HINTS) or " or " in str(item.get("final_visual") or "").lower():
        if primary_pattern in {"candidate_gap", "unknown"} or (
            isinstance(item.get("confidence"), int) and item["confidence"] < 70
        ):
            return "boundary_ambiguity"
    if _contains_any(text, _MEETING_MEAL_HINTS) and _contains_any(note, ("맥락", "실제 행동", "행위")):
        return "workflow_mismatch"
    if primary_pattern == "channel_priority":
        return "channel_vs_object"
    if primary_pattern == "action_priority":
        return "action_vs_object"
    if primary_pattern == "interface_priority":
        return "action_vs_object"
    if primary_pattern == "object_priority":
        if _contains_any(text, _STATUS_HINTS):
            return "object_vs_status"
        return "action_vs_object"
    if primary_pattern == "candidate_gap":
        return "no_candidate"

    recommended = normalize_visual(item.get("recommended_visual"))
    final = normalize_visual(item.get("final_visual"))
    if recommended and final and recommended != final:
        if _contains_any(note, ("연상", "회상", "이미지")):
            return "visual_mismatch"
        return "visual_mismatch"
    return "uncategorized"


def infer_gap_type(item: dict[str, Any], gap_type: str | None) -> str | None:
    if gap_type:
        mapping = {
            "candidate_gap": "inferred_no_candidate",
            "ambiguous_channel": "inferred_ambiguous_channel",
            "metadata_gap": "inferred_workflow_boundary",
            "keyword_gap": "inferred_no_candidate",
        }
        return mapping.get(gap_type, f"inferred_{gap_type}")

    note = str(item.get("note") or "")
    title = str(item.get("title") or "")
    text = f"{note} {title}"

    if is_no_candidate_recommendation(item):
        return "inferred_no_candidate"
    if _contains_any(text, _MEETING_MEAL_HINTS):
        return "inferred_meeting_meal"
    if _contains_any(text, _CHANNEL_HINTS) and _contains_any(text, ("공문", "문서", "보도자료", "📄")):
        return "inferred_document_channel"
    if _contains_any(text, _CHANNEL_HINTS) and _contains_any(text, _OBJECT_HINTS):
        return "inferred_channel_object"
    if _contains_any(text, _ACTION_HINTS) and _contains_any(text, _OBJECT_HINTS):
        return "inferred_action_object"
    if _contains_any(text, _BOUNDARY_HINTS):
        return "inferred_workflow_boundary"
    return None


@dataclass
class EnrichedExample:
    raw: dict[str, Any]
    status: str
    primary_pattern: str
    gap_type: str | None
    source_type: str
    cause_type: str | None
    taxonomy_category: str
    inferred_gap_type: str | None
    system_visual: str
    user_visual: str
    system_workflow: str | None
    user_workflow: str | None
    engine_candidate_id: str | None
    user_candidate_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.raw,
            "status": self.status,
            "primary_pattern": self.primary_pattern,
            "gap_type": self.gap_type,
            "source_type": self.source_type,
            "cause_type": self.cause_type,
            "taxonomy_category": self.taxonomy_category,
            "inferred_gap_type": self.inferred_gap_type,
            "system_visual": self.system_visual,
            "user_visual": self.user_visual,
            "system_workflow": self.system_workflow,
            "user_workflow": self.user_workflow,
            "engine_candidate_id": self.engine_candidate_id,
            "user_candidate_ids": self.user_candidate_ids,
        }


def enrich_example(item: dict[str, Any], catalog: dict[str, Any]) -> EnrichedExample:
    status = example_status(item)
    primary_pattern = classify_primary_pattern(item) if status == "override" else "accepted"
    gap_type = classify_gap_type(item, catalog) if status == "override" else None
    source_type = classify_source_type(item) if status == "override" else "accepted"
    cause_type = classify_cause_type(item, primary_pattern) if status == "override" else None
    taxonomy_category = (
        classify_taxonomy_category(item, primary_pattern) if status == "override" else "accepted"
    )
    inferred = infer_gap_type(item, gap_type) if status == "override" else None

    system_visual = _pick_visual(item, SYSTEM_VISUAL_FIELDS)
    user_visual = _pick_visual(item, USER_VISUAL_FIELDS)

    title = str(item.get("title") or "")
    engine_candidate_id = resolve_engine_candidate_id(title, catalog) if title else None
    user_candidate_ids = candidate_ids_for_visual(user_visual, catalog)

    explicit_workflow = extract_workflow(item)
    system_workflow = explicit_workflow or workflow_fit_label(engine_candidate_id, catalog)
    user_workflow = explicit_workflow or workflow_fit_label(
        user_candidate_ids[0] if user_candidate_ids else None,
        catalog,
    )

    return EnrichedExample(
        raw=item,
        status=status,
        primary_pattern=primary_pattern,
        gap_type=gap_type,
        source_type=source_type,
        cause_type=cause_type,
        taxonomy_category=taxonomy_category,
        inferred_gap_type=inferred,
        system_visual=system_visual,
        user_visual=user_visual,
        system_workflow=system_workflow,
        user_workflow=user_workflow,
        engine_candidate_id=engine_candidate_id,
        user_candidate_ids=user_candidate_ids,
    )


def load_examples(path: Path, catalog: dict[str, Any] | None = None) -> list[EnrichedExample]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must be a JSON array")
    catalog = catalog if catalog is not None else _load_visual_candidates()
    rows = [row for row in raw if isinstance(row, dict)]
    return [enrich_example(row, catalog) for row in rows]


def _ratio(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total * 100, 1)


def _counter_rows(counter: Counter[str], total: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, count in counter.most_common():
        rows.append({"key": key, "count": count, "ratio_pct": _ratio(count, total)})
    return rows


def _suggested_review_targets(
    overrides: list[EnrichedExample],
    taxonomy_counts: Counter[str],
    workflow_counts: Counter[str],
    transition_counts: Counter[str],
    inferred_counts: Counter[str],
) -> list[str]:
    suggestions: list[str] = []
    total = len(overrides) or 1

    top_taxonomy = taxonomy_counts.most_common(1)
    if top_taxonomy:
        key, count = top_taxonomy[0]
        suggestions.append(
            f"Top override taxonomy `{key}` ({count}/{total}, {_ratio(count, total)}%) — "
            "review boundary or catalog policy for this cluster first."
        )

    top_workflow = workflow_counts.most_common(3)
    if top_workflow:
        labels = ", ".join(f"`{wf}` ({cnt})" for wf, cnt in top_workflow)
        suggestions.append(f"Highest override workflows: {labels}.")

    top_transition = transition_counts.most_common(3)
    if top_transition:
        labels = ", ".join(f"{pair} ({cnt})" for pair, cnt in top_transition)
        suggestions.append(f"Common visual transitions: {labels}.")

    no_candidate = taxonomy_counts.get("no_candidate", 0)
    if no_candidate:
        suggestions.append(
            f"`no_candidate` overrides: {no_candidate} — catalog_gap / keyword_gap candidates."
        )

    boundary = taxonomy_counts.get("boundary_ambiguity", 0) + inferred_counts.get(
        "inferred_workflow_boundary", 0
    )
    if boundary:
        suggestions.append(
            f"Boundary / ambiguity signals: {boundary} — run semantic boundary workflow before scoring tweaks."
        )

    if len(suggestions) < 3:
        suggestions.append(
            "Cross-check `resolved_by_current_engine` after catalog patches using snapshot diff tooling."
        )
    return suggestions[:5]


def analyze(examples: list[EnrichedExample], top_n: int = DEFAULT_TOP_N) -> dict[str, Any]:
    accepted = [row for row in examples if row.status == "accepted"]
    overrides = [row for row in examples if row.status == "override"]
    no_candidate = [row for row in examples if is_no_candidate_recommendation(row.raw)]
    uncategorized = [row for row in overrides if row.taxonomy_category == "uncategorized"]

    taxonomy_counts = Counter(row.taxonomy_category for row in overrides)
    source_counts = Counter(row.source_type for row in overrides)
    cause_counts = Counter(row.cause_type for row in overrides if row.cause_type)
    inferred_counts = Counter(
        row.inferred_gap_type for row in overrides if row.inferred_gap_type
    )
    gap_type_counts = Counter(row.gap_type for row in overrides if row.gap_type)

    workflow_override_counts: Counter[str] = Counter()
    workflow_total_counts: Counter[str] = Counter()
    for row in examples:
        wf = row.system_workflow or row.engine_candidate_id or "unknown"
        workflow_total_counts[wf] += 1
        if row.status == "override":
            workflow_override_counts[wf] += 1

    workflow_rows: list[dict[str, Any]] = []
    for wf in workflow_override_counts:
        override_cnt = workflow_override_counts[wf]
        total_cnt = workflow_total_counts.get(wf, override_cnt)
        workflow_rows.append(
            {
                "workflow": wf,
                "override_count": override_cnt,
                "total_count": total_cnt,
                "override_ratio_pct": _ratio(override_cnt, total_cnt),
            }
        )
    workflow_rows.sort(key=lambda r: (-r["override_count"], r["workflow"]))

    system_visual_counts = Counter(row.system_visual for row in overrides if row.system_visual)
    user_visual_counts = Counter(row.user_visual for row in overrides if row.user_visual)
    transition_counts: Counter[str] = Counter()
    for row in overrides:
        if row.system_visual and row.user_visual and row.system_visual != row.user_visual:
            transition_counts[f"{row.system_visual} -> {row.user_visual}"] += 1

    return {
        "overall": {
            "total_examples": len(examples),
            "accepted_count": len(accepted),
            "override_count": len(overrides),
            "no_candidate_count": len(no_candidate),
            "uncategorized_count": len(uncategorized),
            "unknown_count": len(uncategorized),
        },
        "taxonomy_distribution": _counter_rows(taxonomy_counts, len(overrides)),
        "source_type_distribution": _counter_rows(source_counts, len(overrides)),
        "cause_type_distribution": _counter_rows(cause_counts, len(overrides)),
        "workflow_distribution": workflow_rows[:top_n],
        "visual_distribution": {
            "system_recommended": _counter_rows(system_visual_counts, len(overrides))[:top_n],
            "user_selected": _counter_rows(user_visual_counts, len(overrides))[:top_n],
        },
        "visual_transitions": _counter_rows(transition_counts, len(overrides))[:top_n],
        "gap_type_distribution": {
            "engine_gap_type": _counter_rows(gap_type_counts, len(overrides)),
            "inferred_gap_type": _counter_rows(inferred_counts, len(overrides)),
        },
        "suggested_review_targets": _suggested_review_targets(
            overrides,
            taxonomy_counts,
            workflow_override_counts,
            transition_counts,
            inferred_counts,
        ),
    }


def format_markdown_report(summary: dict[str, Any]) -> str:
    overall = summary["overall"]
    lines: list[str] = [
        "# P5-B Feedback Statistics Summary",
        "",
        "> Override taxonomy follows `docs/feedback_override_taxonomy.md`. "
        "Engine `gap_type` uses the current catalog; inferred gap types are keyword-based.",
        "",
        "## 1. Overall",
        f"- Total examples: {overall['total_examples']}",
        f"- Overrides: {overall['override_count']}",
        f"- Accepted: {overall['accepted_count']}",
        f"- No candidate: {overall['no_candidate_count']}",
        f"- Uncategorized: {overall['uncategorized_count']}",
        "",
        "## 2. Override Taxonomy Distribution",
        "",
        "| taxonomy | count | ratio |",
        "| --- | ---: | ---: |",
    ]
    for row in summary["taxonomy_distribution"]:
        lines.append(f"| {row['key']} | {row['count']} | {row['ratio_pct']}% |")

    lines.extend(["", "## 3. Workflow Override Ranking", ""])
    if summary["workflow_distribution"]:
        lines.extend(
            [
                "| workflow | overrides | total | override ratio |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for row in summary["workflow_distribution"]:
            lines.append(
                f"| {row['workflow']} | {row['override_count']} | {row['total_count']} | "
                f"{row['override_ratio_pct']}% |"
            )
    else:
        lines.append("- (no workflow field resolved)")

    lines.extend(["", "## 4. Visual Transition Ranking", ""])
    if summary["visual_transitions"]:
        lines.extend(["| transition | count | ratio |", "| --- | ---: | ---: |"])
        for row in summary["visual_transitions"]:
            lines.append(f"| {row['key']} | {row['count']} | {row['ratio_pct']}% |")
    else:
        lines.append("- (no visual transitions)")

    lines.extend(["", "## 5. Ambiguity / Gap Type Summary", ""])
    lines.append("### Engine gap_type (current catalog)")
    lines.append("")
    engine_rows = summary["gap_type_distribution"]["engine_gap_type"]
    if engine_rows:
        lines.extend(["| gap_type | count | ratio |", "| --- | ---: | ---: |"])
        for row in engine_rows:
            lines.append(f"| {row['key']} | {row['count']} | {row['ratio_pct']}% |")
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("### Inferred gap type (keyword-based)")
    lines.append("")
    inferred_rows = summary["gap_type_distribution"]["inferred_gap_type"]
    if inferred_rows:
        lines.extend(["| inferred_gap_type | count | ratio |", "| --- | ---: | ---: |"])
        for row in inferred_rows:
            lines.append(f"| {row['key']} | {row['count']} | {row['ratio_pct']}% |")
    else:
        lines.append("- (none)")

    lines.extend(["", "## 6. Suggested Next Review Targets", ""])
    for index, target in enumerate(summary["suggested_review_targets"], start=1):
        lines.append(f"{index}. {target}")

    if "current_engine_recheck" in summary:
        lines.extend(format_current_engine_recheck_markdown(summary))

    return "\n".join(lines).rstrip() + "\n"


def analyze_to_json(summary: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "overall": summary["overall"],
        "taxonomy_distribution": {
            row["key"]: {"count": row["count"], "ratio_pct": row["ratio_pct"]}
            for row in summary["taxonomy_distribution"]
        },
        "source_type_distribution": {
            row["key"]: {"count": row["count"], "ratio_pct": row["ratio_pct"]}
            for row in summary.get("source_type_distribution", [])
        },
        "cause_type_distribution": {
            row["key"]: {"count": row["count"], "ratio_pct": row["ratio_pct"]}
            for row in summary.get("cause_type_distribution", [])
        },
        "workflow_distribution": summary["workflow_distribution"],
        "visual_distribution": summary["visual_distribution"],
        "visual_transitions": {
            row["key"]: {"count": row["count"], "ratio_pct": row["ratio_pct"]}
            for row in summary["visual_transitions"]
        },
        "gap_type_distribution": summary["gap_type_distribution"],
        "suggested_review_targets": summary["suggested_review_targets"],
    }
    if "current_engine_recheck" in summary:
        payload["current_engine_recheck"] = summary["current_engine_recheck"]
    if "current_engine_examples" in summary:
        payload["current_engine_examples"] = summary["current_engine_examples"]
    return payload


def _resolve_current_engine_for_title(
    title: str,
    catalog: dict[str, Any],
    sample_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    from app.recommender import find_best_visual_candidate_match, find_exact_title_match

    result: dict[str, Any] = {
        "current_engine_candidate_id": None,
        "current_engine_visual": None,
        "current_engine_workflow": None,
        "matches_final_visual": False,
        "matches_final_candidate_id": False,
        "resolved_by_current_engine": False,
        "active_gap": False,
        "still_no_candidate": False,
        "partial_match": False,
        "engine_error": False,
        "engine_error_message": None,
        "used_sample_case": False,
    }
    try:
        case = find_exact_title_match(title, sample_cases)
        if case is not None:
            visual = case.get("visual")
            if isinstance(visual, dict):
                result["current_engine_visual"] = format_visual_display(visual)
                result["used_sample_case"] = True
                cid = case.get("candidate_id")
                if isinstance(cid, str) and cid.strip():
                    result["current_engine_candidate_id"] = cid.strip()

        if result["current_engine_candidate_id"] is None:
            match = find_best_visual_candidate_match(title, catalog)
            if match is None:
                result["still_no_candidate"] = True
                return result
            result["current_engine_candidate_id"] = match.candidate_id
            if result["current_engine_visual"] is None:
                vis = match.data.get("visual")
                if isinstance(vis, dict):
                    result["current_engine_visual"] = format_visual_display(vis)

        cid = result["current_engine_candidate_id"]
        result["current_engine_workflow"] = workflow_fit_label(cid, catalog)
        return result
    except Exception as exc:
        result["engine_error"] = True
        result["engine_error_message"] = str(exc)
        return result


def recheck_current_engine(
    examples: list[EnrichedExample],
    catalog: dict[str, Any] | None = None,
    sample_cases: list[dict[str, Any]] | None = None,
    *,
    active_gap_top_n: int = 10,
) -> dict[str, Any]:
    catalog = catalog if catalog is not None else _load_visual_candidates()
    sample_cases = sample_cases if sample_cases is not None else _load_sample_cases()

    per_example: list[dict[str, Any]] = []
    resolved = 0
    active_gap = 0
    still_no_candidate = 0
    partial_match = 0
    engine_errors = 0

    for row in examples:
        title = str(row.raw.get("title") or "")
        engine = _resolve_current_engine_for_title(title, catalog, sample_cases)
        final_visual = row.user_visual
        user_candidate_ids = row.user_candidate_ids

        if engine.get("engine_error"):
            engine_errors += 1
        elif engine.get("still_no_candidate"):
            still_no_candidate += 1

        matches_visual = _visual_matches_target(engine.get("current_engine_visual"), final_visual)
        matches_candidate = bool(
            engine.get("current_engine_candidate_id")
            and user_candidate_ids
            and engine["current_engine_candidate_id"] in user_candidate_ids
        )
        engine["matches_final_visual"] = matches_visual
        engine["matches_final_candidate_id"] = matches_candidate
        engine["resolved_by_current_engine"] = matches_visual

        is_override = row.status == "override"
        engine["active_gap"] = is_override and not matches_visual and not engine.get("engine_error")

        partial = False
        if is_override and not matches_visual and not engine.get("engine_error"):
            same_workflow = (
                engine.get("current_engine_workflow")
                and row.user_workflow
                and engine["current_engine_workflow"] == row.user_workflow
            )
            partial = matches_candidate or bool(same_workflow)
        engine["partial_match"] = partial

        if engine.get("resolved_by_current_engine"):
            resolved += 1
        if engine.get("active_gap"):
            active_gap += 1
        if engine.get("partial_match"):
            partial_match += 1

        per_example.append(
            {
                "id": row.raw.get("id"),
                "title": title,
                "status": row.status,
                "previous_recommended": row.system_visual,
                "final_visual": final_visual,
                "inferred_gap_type": row.inferred_gap_type,
                "taxonomy_category": row.taxonomy_category,
                **engine,
            }
        )

    active_examples = [
        ex
        for ex in per_example
        if ex.get("active_gap") and not ex.get("engine_error")
    ]
    active_examples.sort(
        key=lambda ex: (
            0 if ex.get("still_no_candidate") else 1,
            str(ex.get("title") or ""),
        )
    )

    return {
        "current_engine_recheck": {
            "resolved_by_current_engine": resolved,
            "active_gap": active_gap,
            "still_no_candidate": still_no_candidate,
            "partial_match": partial_match,
            "engine_errors": engine_errors,
            "override_total": sum(1 for row in examples if row.status == "override"),
        },
        "current_engine_examples": per_example,
        "active_gap_top_examples": active_examples[:active_gap_top_n],
    }


def _md_cell(text: str | None) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ")


LABELING_MD_HEADER = """# P5-B Override Manual Labeling Sheet

## Purpose
이 파일은 자동 taxonomy 결과를 사람이 검토하여, override 원인을 수동 라벨링하기 위한 작업 파일입니다.

## Labeling Guide
- `source_type_manual`: override가 발생한 1차 원인
- `cause_type_manual`: 구체적 원인
- `action_hint_manual`: 이후 조치 방향
- `generalizable_manual`: 다른 유사 업무에도 적용 가능한지 여부

## Allowed source_type_manual values
- workflow_mismatch
- visual_mismatch
- boundary_ambiguity
- candidate_gap
- metadata_gap
- personal_preference
- no_candidate
- unclear

## Allowed action_hint_manual values
- add_candidate
- update_metadata
- adjust_boundary
- adjust_scoring
- suppress_overfit
- keep_as_preference
- needs_more_data
"""

LABELING_MD_LEGACY_TABLE = """## Labeling Table
| id | title | recommended_visual | final_visual | current_taxonomy | inferred_gap_type | source_type_manual | cause_type_manual | action_hint_manual | generalizable_manual | note |
|---|---|---|---|---|---|---|---|---|---|---|
"""

LABELING_CSV_COLUMNS = (
    "id",
    "title",
    "recommended_visual",
    "final_visual",
    "current_taxonomy",
    "inferred_gap_type",
    "inferred_source_type",
    "inferred_cause_type",
    "current_engine_visual",
    "current_engine_candidate_id",
    "current_engine_workflow",
    "resolved_by_current_engine",
    "active_gap",
    "still_no_candidate",
    "engine_error",
    "source_type_manual",
    "cause_type_manual",
    "action_hint_manual",
    "generalizable_manual",
    "note",
)

LABELING_MD_TABLE_HEADER = (
    "| id | title | recommended_visual | final_visual | current_engine_visual | "
    "current_engine_workflow | current_taxonomy | inferred_gap_type | "
    "source_type_manual | cause_type_manual | action_hint_manual | "
    "generalizable_manual | note |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
)

LABELING_MD_TABLE_HEADER_LEGACY = (
    "| id | title | recommended_visual | final_visual | current_taxonomy | inferred_gap_type | "
    "source_type_manual | cause_type_manual | action_hint_manual | generalizable_manual | note |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|\n"
)


def _engine_by_id(recheck: dict[str, Any] | None) -> dict[Any, dict[str, Any]]:
    if not recheck:
        return {}
    return {
        ex.get("id"): ex
        for ex in recheck.get("current_engine_examples") or []
        if ex.get("id") is not None
    }


def _bool_str(value: bool | None) -> str:
    if value is None:
        return ""
    return "true" if value else "false"


def _labeling_row_dict(row: EnrichedExample, engine_ex: dict[str, Any] | None) -> dict[str, Any]:
    raw = row.raw
    engine = engine_ex or {}
    return {
        "id": raw.get("id", ""),
        "title": raw.get("title", ""),
        "recommended_visual": row.system_visual,
        "final_visual": row.user_visual,
        "current_taxonomy": row.taxonomy_category,
        "inferred_gap_type": row.inferred_gap_type or "",
        "inferred_source_type": row.source_type,
        "inferred_cause_type": row.cause_type or "",
        "current_engine_visual": engine.get("current_engine_visual") or "",
        "current_engine_candidate_id": engine.get("current_engine_candidate_id") or "",
        "current_engine_workflow": engine.get("current_engine_workflow") or "",
        "resolved_by_current_engine": _bool_str(engine.get("resolved_by_current_engine")),
        "active_gap": _bool_str(engine.get("active_gap")),
        "still_no_candidate": _bool_str(engine.get("still_no_candidate")),
        "engine_error": _bool_str(engine.get("engine_error")),
        "source_type_manual": "",
        "cause_type_manual": "",
        "action_hint_manual": "",
        "generalizable_manual": "",
        "note": raw.get("note", ""),
        "_engine_ex": engine,
    }


def _classify_labeling_bucket(row: dict[str, Any]) -> str:
    engine = row.get("_engine_ex") or {}
    if engine.get("engine_error"):
        return "engine_error"
    if engine.get("still_no_candidate"):
        return "still_no_candidate"
    if engine.get("active_gap"):
        return "active_gap"
    if engine.get("resolved_by_current_engine"):
        return "resolved_stale"
    return "other"


def _labeling_rows_for_export(
    examples: list[EnrichedExample],
    recheck: dict[str, Any] | None,
    *,
    only_active_gaps: bool,
) -> list[dict[str, Any]]:
    engine_map = _engine_by_id(recheck)
    rows: list[dict[str, Any]] = []
    for ex in examples:
        if ex.status != "override":
            continue
        row = _labeling_row_dict(ex, engine_map.get(ex.raw.get("id")))
        rows.append(row)

    if not only_active_gaps:
        return rows

    filtered: list[dict[str, Any]] = []
    for row in rows:
        engine = row.get("_engine_ex") or {}
        if engine.get("resolved_by_current_engine"):
            continue
        if engine.get("engine_error") or engine.get("active_gap") or engine.get("still_no_candidate"):
            filtered.append(row)
    return filtered


def _format_labeling_md_row(row: dict[str, Any], *, with_engine: bool) -> str:
    if with_engine:
        return (
            "| {id} | {title} | {rec} | {fin} | {cur_vis} | {cur_wf} | {tax} | {gap} | "
            " |  |  |  | {note} |"
        ).format(
            id=_md_cell(str(row.get("id", ""))),
            title=_md_cell(str(row.get("title", ""))),
            rec=_md_cell(str(row.get("recommended_visual", ""))),
            fin=_md_cell(str(row.get("final_visual", ""))),
            cur_vis=_md_cell(str(row.get("current_engine_visual", ""))),
            cur_wf=_md_cell(str(row.get("current_engine_workflow", ""))),
            tax=_md_cell(str(row.get("current_taxonomy", ""))),
            gap=_md_cell(str(row.get("inferred_gap_type", ""))),
            note=_md_cell(str(row.get("note", ""))),
        )
    return (
        "| {id} | {title} | {rec} | {fin} | {tax} | {gap} |  |  |  |  | {note} |"
    ).format(
        id=_md_cell(str(row.get("id", ""))),
        title=_md_cell(str(row.get("title", ""))),
        rec=_md_cell(str(row.get("recommended_visual", ""))),
        fin=_md_cell(str(row.get("final_visual", ""))),
        tax=_md_cell(str(row.get("current_taxonomy", ""))),
        gap=_md_cell(str(row.get("inferred_gap_type", ""))),
        note=_md_cell(str(row.get("note", ""))),
    )


def export_labeling_markdown(
    examples: list[EnrichedExample],
    path: Path,
    *,
    recheck: dict[str, Any] | None = None,
    only_active_gaps: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with_engine = recheck is not None
    rows = _labeling_rows_for_export(examples, recheck, only_active_gaps=only_active_gaps)

    lines = [LABELING_MD_HEADER.rstrip()]
    if with_engine:
        lines.extend(
            [
                "",
                "> Current-engine recheck fields included. "
                "Label **Active Gaps** and **Still No Candidate** first; skip resolved stale overrides.",
                "",
            ]
        )

    if with_engine:
        buckets: dict[str, list[dict[str, Any]]] = {
            "active_gap": [],
            "still_no_candidate": [],
            "engine_error": [],
            "resolved_stale": [],
            "other": [],
        }
        for row in rows:
            buckets[_classify_labeling_bucket(row)].append(row)

        def _section(title: str, description: str, bucket_key: str) -> None:
            lines.extend(["", f"## {title}", "", description, ""])
            lines.append(LABELING_MD_TABLE_HEADER.rstrip())
            bucket_rows = buckets[bucket_key]
            if bucket_rows:
                for row in bucket_rows:
                    lines.append(_format_labeling_md_row(row, with_engine=True))
            else:
                lines.append("| — | (none) | | | | | | | | | | | |")

        if only_active_gaps:
            _section(
                "Active Gaps for Manual Labeling",
                "현재 엔진에서도 여전히 사용자 최종 선택과 맞지 않는 사례입니다.",
                "active_gap",
            )
            _section(
                "Still No Candidate",
                "현재 엔진도 후보를 찾지 못한 사례입니다.",
                "still_no_candidate",
            )
            _section(
                "Engine Error / Needs Review",
                "현재 엔진 재검증에 실패한 사례입니다.",
                "engine_error",
            )
        else:
            _section(
                "Active Gaps for Manual Labeling",
                "현재 엔진에서도 여전히 사용자 최종 선택과 맞지 않는 사례입니다.",
                "active_gap",
            )
            _section(
                "Still No Candidate",
                "현재 엔진도 후보를 찾지 못한 사례입니다.",
                "still_no_candidate",
            )
            _section(
                "Engine Error / Needs Review",
                "현재 엔진 재검증에 실패한 사례입니다.",
                "engine_error",
            )
            lines.extend(
                [
                    "",
                    "## Resolved (Stale — Skip Labeling)",
                    "",
                    "현재 엔진이 사용자 final visual과 일치합니다. boundary 수정 대상에서 제외하세요.",
                    "",
                    LABELING_MD_TABLE_HEADER.rstrip(),
                ]
            )
            if buckets["resolved_stale"]:
                for row in buckets["resolved_stale"]:
                    lines.append(_format_labeling_md_row(row, with_engine=True))
            else:
                lines.append("| — | (none) | | | | | | | | | | | |")
            if buckets["other"]:
                lines.extend(
                    [
                        "",
                        "## Other Overrides (Reference)",
                        "",
                        LABELING_MD_TABLE_HEADER.rstrip(),
                    ]
                )
                for row in buckets["other"]:
                    lines.append(_format_labeling_md_row(row, with_engine=True))
    else:
        lines.extend(["", LABELING_MD_LEGACY_TABLE.rstrip()])
        for row in rows:
            lines.append(_format_labeling_md_row(row, with_engine=False))

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def export_labeling_csv(
    examples: list[EnrichedExample],
    path: Path,
    *,
    recheck: dict[str, Any] | None = None,
    only_active_gaps: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = _labeling_rows_for_export(examples, recheck, only_active_gaps=only_active_gaps)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LABELING_CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in LABELING_CSV_COLUMNS})


def format_current_engine_recheck_markdown(recheck: dict[str, Any]) -> list[str]:
    summary = recheck["current_engine_recheck"]
    lines = [
        "",
        "## Current Engine Recheck",
        "",
        f"- Resolved by current engine: {summary['resolved_by_current_engine']}",
        f"- Active gaps: {summary['active_gap']}",
        f"- Still no candidate: {summary['still_no_candidate']}",
        f"- Partial matches: {summary['partial_match']}",
    ]
    if summary.get("engine_errors"):
        lines.append(f"- Engine errors (non-fatal): {summary['engine_errors']}")

    lines.extend(
        [
            "",
            "## Active Gap Top Examples",
            "",
            "| id | title | previous_recommended | final_visual | current_engine_visual | current_engine_workflow | inferred_gap_type |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for ex in recheck.get("active_gap_top_examples") or []:
        lines.append(
            "| {id} | {title} | {prev} | {fin} | {cur} | {wf} | {gap} |".format(
                id=_md_cell(str(ex.get("id", ""))),
                title=_md_cell(str(ex.get("title", ""))),
                prev=_md_cell(str(ex.get("previous_recommended", ""))),
                fin=_md_cell(str(ex.get("final_visual", ""))),
                cur=_md_cell(str(ex.get("current_engine_visual") or "")),
                wf=_md_cell(str(ex.get("current_engine_workflow") or "")),
                gap=_md_cell(str(ex.get("inferred_gap_type") or "")),
            )
        )
    if not recheck.get("active_gap_top_examples"):
        lines.append("| — | (none) | | | | | |")
    return lines


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description="P5-B feedback override statistics from Notion examples."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Override examples JSON (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print analysis result as JSON instead of markdown",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"Top N rows for ranking sections (default: {DEFAULT_TOP_N})",
    )
    parser.add_argument(
        "--export-labeling-md",
        type=Path,
        metavar="PATH",
        help="Write manual labeling sheet as Markdown (e.g. reports/p5b_active_gap_labeling.md)",
    )
    parser.add_argument(
        "--export-labeling-csv",
        type=Path,
        metavar="PATH",
        help="Write manual labeling sheet as CSV (e.g. reports/p5b_active_gap_labeling.csv)",
    )
    parser.add_argument(
        "--check-current-engine",
        action="store_true",
        help="Re-run titles through the current recommendation engine and split stale vs active gaps",
    )
    parser.add_argument(
        "--only-active-gaps",
        action="store_true",
        help="With --check-current-engine: export only active_gap, still_no_candidate, and engine_error rows",
    )
    args = parser.parse_args()

    if args.only_active_gaps and not args.check_current_engine:
        parser.error("--only-active-gaps requires --check-current-engine")

    examples = load_examples(args.input)
    summary = analyze(examples, top_n=args.top)

    recheck: dict[str, Any] | None = None
    if args.check_current_engine:
        recheck = recheck_current_engine(examples, active_gap_top_n=args.top)
        summary.update(recheck)

    export_kwargs = {
        "recheck": recheck,
        "only_active_gaps": args.only_active_gaps,
    }
    if args.export_labeling_md:
        export_labeling_markdown(examples, args.export_labeling_md, **export_kwargs)
    if args.export_labeling_csv:
        export_labeling_csv(examples, args.export_labeling_csv, **export_kwargs)

    if args.json:
        print(json.dumps(analyze_to_json(summary), ensure_ascii=False, indent=2))
    elif args.export_labeling_md or args.export_labeling_csv:
        if args.check_current_engine:
            print(format_markdown_report(summary), end="")
    else:
        print(format_markdown_report(summary), end="")


if __name__ == "__main__":
    main()
