"""Analyze why users overrode recommendations (P5-A Override Pattern Analyzer).

See ``docs/p5_override_pattern_analysis.md`` for how ``primary_pattern`` and
``gap_type`` differ (historical feedback vs current engine replay).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

PATTERNS = (
    "candidate_gap",
    "channel_priority",
    "interface_priority",
    "object_priority",
    "action_priority",
    "unknown",
)

GAP_TYPES = (
    "candidate_gap",
    "keyword_gap",
    "metadata_gap",
    "ambiguous_channel",
)

DEFAULT_INPUT = Path("data/override_examples.json")

ANALYSIS_BASIS: dict[str, str] = {
    "primary_pattern": "historical_feedback",
    "gap_type": "current_engine",
}

_CANDIDATE_GAP_NOTE_HINTS = ("후보 없음", "workflow 없음", "적절한 후보 없음")
_CHANNEL_HINTS = ("메일", "전화", "카톡", "이메일", "전달", "요청", "연락")
_INTERFACE_HINTS = ("시스템", "화면", "ui", "행정 내부 시스템", "등록", "예약", "결재")
_OBJECT_HINTS = (
    "대상",
    "중점",
    "보도자료",
    "영상",
    "포스터",
    "배너",
    "홍보물",
    "과일",
    "간식",
    "시각매체",
    "매트리스",
    "물품",
    "수신자",
)
_ACTION_HINTS = (
    "실제 행동",
    "행위",
    "선정",
    "정하기",
    "등록",
    "예약",
    "처리",
    "싣기",
    "제작",
    "픽업",
    "참석",
)
_CHANNEL_FINAL_MARKERS = ("📧", "📞", "💬", "mail", "email", "phone", "메일", "전화")
_DOCUMENT_FINAL_MARKERS = ("📄", "📝", "document", "paper", "문서")
_SYSTEM_FINAL_MARKERS = ("💻", "system", "computer", "window", "행정")
_AMBIGUOUS_NOTE_HINTS = ("일 수 있", "일수있", "다른 이모지", "모두 가능", "에 따라")


def normalize_visual(value: str | None) -> str:
    return (value or "").strip()


def example_status(item: dict[str, Any]) -> str:
    if normalize_visual(item.get("recommended_visual")) == normalize_visual(item.get("final_visual")):
        return "accepted"
    return "override"


def is_no_candidate_recommendation(item: dict[str, Any]) -> bool:
    return normalize_visual(item.get("recommended_visual")) == "없음"


def confidence_tier(confidence: int | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence >= 90:
        return "strong"
    if confidence >= 70:
        return "medium"
    return "weak"


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(hint in text or hint.lower() in lowered for hint in hints)


def _is_channel_or_system_final(final_visual: str) -> bool:
    final = final_visual.lower()
    if _contains_any(final_visual, _CHANNEL_FINAL_MARKERS):
        return True
    return _contains_any(final, _SYSTEM_FINAL_MARKERS)


def _matches_candidate_gap(item: dict[str, Any]) -> bool:
    if normalize_visual(item.get("recommended_visual")) == "없음":
        return True
    note = str(item.get("note") or "")
    return _contains_any(note, _CANDIDATE_GAP_NOTE_HINTS)


def _matches_channel(item: dict[str, Any]) -> bool:
    note = str(item.get("note") or "")
    final = str(item.get("final_visual") or "")
    return _contains_any(f"{note} {final}", _CHANNEL_HINTS) or _contains_any(
        final, _CHANNEL_FINAL_MARKERS
    )


def _matches_interface(item: dict[str, Any]) -> bool:
    note = str(item.get("note") or "")
    return _contains_any(note, _INTERFACE_HINTS)


def _matches_object(item: dict[str, Any]) -> bool:
    note = str(item.get("note") or "")
    return _contains_any(note, _OBJECT_HINTS)


def _matches_action(item: dict[str, Any]) -> bool:
    note = str(item.get("note") or "")
    title = str(item.get("title") or "")
    return _contains_any(f"{note} {title}", _ACTION_HINTS)


def parse_final_visual_parts(final_visual: str | None) -> list[str]:
    raw = normalize_visual(final_visual)
    if not raw:
        return []
    return [normalize_visual(part) for part in re.split(r"\s+or\s+", raw, flags=re.IGNORECASE) if part.strip()]


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
    m = re.match(r"^(.+?)\s*\((\w+)\)\s*$", part)
    if m:
        name, part_color = m.group(1).strip().lower(), m.group(2).lower()
        if name == val_l:
            return not color or color.lower() == part_color
    label = f"{value} ({color})" if color else value
    if part_l == label.lower():
        return True
    return bool(val_l) and (part_l in val_l or val_l in part_l)


def catalog_candidate_ids_for_final(
    final_visual: str | None, catalog: dict[str, Any]
) -> list[str]:
    parts = parse_final_visual_parts(final_visual)
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


def _channel_kinds_in_text(text: str) -> set[str]:
    kinds: set[str] = set()
    if _contains_any(text, ("📧", "mail", "email", "메일")):
        kinds.add("email")
    if _contains_any(text, ("📞", "phone", "전화")):
        kinds.add("phone")
    if _contains_any(text, ("💬", "카톡", "메신저")):
        kinds.add("messenger")
    if _contains_any(text, _DOCUMENT_FINAL_MARKERS):
        kinds.add("document")
    if _contains_any(text, _SYSTEM_FINAL_MARKERS):
        kinds.add("system")
    return kinds


def _is_ambiguous_channel(item: dict[str, Any]) -> bool:
    final = str(item.get("final_visual") or "")
    note = str(item.get("note") or "")
    parts = parse_final_visual_parts(final)
    if len(parts) >= 2:
        kinds: set[str] = set()
        for part in parts:
            kinds |= _channel_kinds_in_text(part)
        if len(kinds) >= 2:
            return True
    if " or " in final.lower() and len(_channel_kinds_in_text(final)) >= 2:
        return True
    if "민원" in note and len(_channel_kinds_in_text(note)) >= 2:
        return True
    if _contains_any(note, _AMBIGUOUS_NOTE_HINTS) and len(_channel_kinds_in_text(f"{note} {final}")) >= 2:
        return True
    return False


def _engine_aligns_with_final(
    candidate_id: str,
    candidate_data: dict[str, Any],
    final_parts: list[str],
    catalog_ids_for_final: list[str],
) -> bool:
    if candidate_id in catalog_ids_for_final:
        return True
    return any(_visual_part_matches(part, candidate_data) for part in final_parts)


@lru_cache(maxsize=1)
def _load_visual_candidates() -> dict[str, Any]:
    from app.data_loader import load_visual_candidates

    return load_visual_candidates()


def classify_gap_type(
    item: dict[str, Any],
    catalog: dict[str, Any] | None = None,
) -> str | None:
    """Classify catalog/engine gap (orthogonal to ``primary_pattern``).

    Returns ``None`` when the example is accepted or no catalog/engine gap is detected.
    """
    if example_status(item) == "accepted":
        return None
    if _is_ambiguous_channel(item):
        return "ambiguous_channel"

    catalog = catalog if catalog is not None else _load_visual_candidates()
    final_parts = parse_final_visual_parts(str(item.get("final_visual") or ""))
    catalog_ids = catalog_candidate_ids_for_final(str(item.get("final_visual") or ""), catalog)
    if not catalog_ids:
        return "candidate_gap"

    from app.recommender import find_best_visual_candidate_match

    title = str(item.get("title") or "")
    engine_match = find_best_visual_candidate_match(title, catalog)
    if engine_match is None:
        return "keyword_gap"

    if _engine_aligns_with_final(
        engine_match.candidate_id,
        engine_match.data,
        final_parts,
        catalog_ids,
    ):
        return None
    return "metadata_gap"


def classify_primary_pattern(item: dict[str, Any]) -> str:
    note = str(item.get("note") or "")
    final = str(item.get("final_visual") or "")

    if "실제 행동" in note and not _is_channel_or_system_final(final):
        return "action_priority"

    checks: tuple[tuple[str, Any], ...] = (
        ("candidate_gap", _matches_candidate_gap),
        ("channel_priority", _matches_channel),
        ("interface_priority", _matches_interface),
        ("object_priority", _matches_object),
        ("action_priority", _matches_action),
    )
    for pattern, matcher in checks:
        if matcher(item):
            return pattern
    return "unknown"


def _enriched_case(item: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        **item,
        "status": example_status(item),
        "primary_pattern": classify_primary_pattern(item),
        "gap_type": classify_gap_type(item, catalog),
        "confidence_tier": confidence_tier(item.get("confidence")),
    }


def load_examples(path: Path, catalog: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} must be a JSON array")
    rows = [row for row in raw if isinstance(row, dict)]
    catalog = catalog if catalog is not None else _load_visual_candidates()
    return [_enriched_case(row, catalog) for row in rows]


def analyze(examples: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in examples if row["status"] == "accepted"]
    overrides = [row for row in examples if row["status"] == "override"]
    no_candidate = [row for row in examples if is_no_candidate_recommendation(row)]

    confidence_dist = Counter(row["confidence_tier"] for row in overrides)
    pattern_counts = Counter(row["primary_pattern"] for row in overrides)
    gap_type_counts = Counter(
        row["gap_type"] for row in overrides if row.get("gap_type") is not None
    )
    by_pattern: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_gap_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in overrides:
        by_pattern[row["primary_pattern"]].append(row)
        gap_type = row.get("gap_type")
        if gap_type:
            by_gap_type[gap_type].append(row)

    def sort_key(row: dict[str, Any]) -> tuple[int, int]:
        confidence = row.get("confidence")
        return (-(confidence if isinstance(confidence, int) else -1), row.get("id", 0))

    representative: dict[str, list[dict[str, Any]]] = {}
    for pattern in PATTERNS:
        cases = sorted(by_pattern.get(pattern, []), key=sort_key)
        representative[pattern] = cases[:3]

    strong_signals = [
        row
        for row in sorted(overrides, key=sort_key)
        if row["confidence_tier"] == "strong"
    ]
    weak_signals = [
        row
        for row in sorted(overrides, key=lambda r: (r.get("confidence") or 101, r.get("id", 0)))
        if row["confidence_tier"] == "weak"
    ]

    improvement_candidates: list[dict[str, str]] = []
    for pattern in PATTERNS:
        strong_in_pattern = [r for r in by_pattern.get(pattern, []) if r["confidence_tier"] == "strong"]
        if not strong_in_pattern:
            continue
        titles = ", ".join(r["title"] for r in strong_in_pattern[:3])
        improvement_candidates.append(
            {
                "pattern": pattern,
                "count": str(len(strong_in_pattern)),
                "titles": titles,
            }
        )

    return {
        "total_examples": len(examples),
        "accepted_count": len(accepted),
        "no_candidate_count": len(no_candidate),
        "override_count": len(overrides),
        "confidence_distribution": {
            tier: confidence_dist.get(tier, 0) for tier in ("strong", "medium", "weak", "unknown")
        },
        "pattern_summary": {pattern: pattern_counts.get(pattern, 0) for pattern in PATTERNS},
        "gap_type_summary": {gap: gap_type_counts.get(gap, 0) for gap in GAP_TYPES},
        "representative_gap_cases": {
            gap: sorted(by_gap_type.get(gap, []), key=sort_key)[:3] for gap in GAP_TYPES
        },
        "representative_cases": representative,
        "strong_signals": strong_signals,
        "weak_signals": weak_signals,
        "improvement_candidates": improvement_candidates,
        "overrides": overrides,
    }


def interpretation_markdown_lines() -> list[str]:
    """Human-readable rules for reading ``primary_pattern`` vs ``gap_type``."""
    return [
        "## primary_pattern vs gap_type",
        "",
        "> **Note:** `primary_pattern` is computed from **historical manual feedback** "
        "(`recommended_visual` → `final_visual` at review time). "
        "`gap_type` is recomputed from the **current** `visual_candidates` catalog "
        "and recommendation engine.",
        "",
        "| Field | Basis | Question answered |",
        "| --- | --- | --- |",
        "| `primary_pattern` | Historical feedback | Why did the user change the recommendation? |",
        "| `gap_type` | Current catalog + engine | Why can the engine not match this case *now*? |",
        "",
        "Therefore **`primary_pattern=candidate_gap` with `gap_type=null` is not a bug**. "
        "It usually means the case was a gap when feedback was recorded, but a later "
        "catalog/engine patch already resolves it.",
        "",
        "### Example: 인사 상담",
        "",
        "- **At feedback time:** `recommended_visual=없음`, `final_visual=👥` "
        "→ `primary_pattern=candidate_gap` (no suggestion; user picked 👥).",
        "- **After adding `hr_consultation`:** engine can recommend `인사 상담` → 👥 "
        "→ `gap_type=null` (no remaining engine/catalog gap).",
        "",
        "Other `gap_type` values (override only):",
        "",
        "- `candidate_gap` — no catalog candidate for the user's final visual.",
        "- `keyword_gap` — candidates exist, but title keywords do not match.",
        "- `metadata_gap` — engine matches, but visual/metadata disagrees with final choice.",
        "- `ambiguous_channel` — phone/document/system (or similar) are all plausible.",
        "",
        "Full reference: `docs/p5_override_pattern_analysis.md`.",
        "",
    ]


def format_markdown_report(summary: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Override Pattern Analysis",
        "",
        *interpretation_markdown_lines(),
        f"Total examples: {summary['total_examples']}",
        f"Override cases: {summary['override_count']}",
        f"Accepted cases (excluded from pattern analysis): {summary['accepted_count']}",
        f"No-candidate recommendations (`없음`): {summary['no_candidate_count']}",
        "",
        "## Confidence Distribution (override only)",
        "",
    ]
    dist = summary["confidence_distribution"]
    for tier, label in (
        ("strong", "strong (>= 90)"),
        ("medium", "medium (70-89)"),
        ("weak", "weak (< 70)"),
        ("unknown", "unknown (null)"),
    ):
        lines.append(f"- {label}: {dist[tier]}")
    lines.extend(["", "## Pattern Summary", "", "| Pattern | Count |", "| --- | ---: |"])
    for pattern in PATTERNS:
        lines.append(f"| {pattern} | {summary['pattern_summary'][pattern]} |")

    lines.extend(["", "## Gap Type Summary (override only)", "", "| Gap type | Count |", "| --- | ---: |"])
    for gap in GAP_TYPES:
        lines.append(f"| {gap} | {summary['gap_type_summary'][gap]} |")

    lines.extend(["", "## Representative Gap Cases", ""])
    for gap in GAP_TYPES:
        cases = summary["representative_gap_cases"].get(gap) or []
        if not cases:
            continue
        lines.append(f"### {gap}")
        lines.append("")
        for case in cases:
            confidence = case.get("confidence")
            conf_display = confidence if confidence is not None else "null"
            lines.append(f"- {case['title']}")
            lines.append(f"  - primary_pattern: {case['primary_pattern']}")
            lines.append(f"  - recommended: {case['recommended_visual']}")
            lines.append(f"  - final: {case['final_visual']}")
            lines.append(f"  - confidence: {conf_display}")
        lines.append("")

    lines.extend(["", "## Representative Cases", ""])
    for pattern in PATTERNS:
        cases = summary["representative_cases"].get(pattern) or []
        if not cases:
            continue
        lines.append(f"### {pattern}")
        lines.append("")
        for case in cases:
            confidence = case.get("confidence")
            conf_display = confidence if confidence is not None else "null"
            lines.append(f"- {case['title']}")
            lines.append(f"  - recommended: {case['recommended_visual']}")
            lines.append(f"  - final: {case['final_visual']}")
            lines.append(f"  - confidence: {conf_display}")
            note = str(case.get("note") or "").strip()
            if note:
                lines.append(f"  - note: {note}")
        lines.append("")

    lines.extend(["## Strong Signals", ""])
    if summary["strong_signals"]:
        for case in summary["strong_signals"][:12]:
            gap = case.get("gap_type")
            gap_label = f" gap={gap}" if gap else ""
            lines.append(
                f"- [{case['primary_pattern']}{gap_label}] {case['title']} "
                f"({case['recommended_visual']} -> {case['final_visual']}, "
                f"confidence {case.get('confidence')})"
            )
    else:
        lines.append("- (none)")
    lines.extend(["", "## Weak Signals", ""])
    if summary["weak_signals"]:
        for case in summary["weak_signals"][:12]:
            gap = case.get("gap_type")
            gap_label = f" gap={gap}" if gap else ""
            lines.append(
                f"- [{case['primary_pattern']}{gap_label}] {case['title']} "
                f"({case['recommended_visual']} -> {case['final_visual']}, "
                f"confidence {case.get('confidence')})"
            )
    else:
        lines.append("- (none)")

    lines.extend(["", "## Improvement Candidates (strong override signals)", ""])
    if summary["improvement_candidates"]:
        for row in summary["improvement_candidates"]:
            lines.append(
                f"- **{row['pattern']}** ({row['count']} strong): {row['titles']}"
            )
    else:
        lines.append("- (none)")

    return "\n".join(lines).rstrip() + "\n"


def analyze_to_json(summary: dict[str, Any]) -> dict[str, Any]:
    def slim_case(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row.get("id"),
            "title": row.get("title"),
            "recommended_visual": row.get("recommended_visual"),
            "final_visual": row.get("final_visual"),
            "confidence": row.get("confidence"),
            "note": row.get("note"),
            "source": row.get("source"),
            "primary_pattern": row.get("primary_pattern"),
            "gap_type": row.get("gap_type"),
            "confidence_tier": row.get("confidence_tier"),
        }

    return {
        "analysis_basis": dict(ANALYSIS_BASIS),
        "interpretation_note": (
            "primary_pattern reflects historical feedback; gap_type reflects the "
            "current catalog and engine. primary_pattern=candidate_gap with "
            "gap_type=null often means a resolved case after a catalog patch."
        ),
        "total_examples": summary["total_examples"],
        "accepted_count": summary["accepted_count"],
        "no_candidate_count": summary["no_candidate_count"],
        "override_count": summary["override_count"],
        "confidence_distribution": summary["confidence_distribution"],
        "pattern_summary": summary["pattern_summary"],
        "gap_type_summary": summary["gap_type_summary"],
        "representative_gap_cases": {
            gap: [slim_case(case) for case in cases]
            for gap, cases in summary["representative_gap_cases"].items()
        },
        "representative_cases": {
            pattern: [slim_case(case) for case in cases]
            for pattern, cases in summary["representative_cases"].items()
        },
        "strong_signals": [slim_case(case) for case in summary["strong_signals"]],
        "weak_signals": [slim_case(case) for case in summary["weak_signals"]],
        "improvement_candidates": summary["improvement_candidates"],
    }


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description="Analyze override patterns from Notion feedback examples."
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
    args = parser.parse_args()

    summary = analyze(load_examples(args.input))
    if args.json:
        print(json.dumps(analyze_to_json(summary), ensure_ascii=False, indent=2))
    else:
        print(format_markdown_report(summary), end="")


if __name__ == "__main__":
    main()
