"""Append-only recommendation observation logs (JSONL). Does not alter ranking.

``candidates[].score`` and ``ambiguity_gap`` are **ranking observation calibration**
values (same weighted lexicographic projection as offline ambiguity scoring logs).
They are **not** P6 ``_row_sort_key`` tuple scores and do not drive which candidate wins.

Use ``recommendation_id`` to correlate a later ``feedback_log`` event with this run.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.candidate_row import CandidateRow
from app.recommender import BestVisualCandidateMatch, _row_sort_key, rank_visual_candidate_rows
from app.workflow_resolution import infer_workflow_resolution

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = Path("logs/recommendation_log.jsonl")
TOP_CANDIDATES = 3
HIGH_AMBIGUITY_THRESHOLD = 0.05

REQUIRED_LOG_FIELDS: frozenset[str] = frozenset(
    {
        "recommendation_id",
        "timestamp",
        "input_title",
        "resolved_workflow",
        "workflow_resolution",
        "top_candidate",
        "candidates",
        "ambiguity_gap",
        "is_ambiguous",
        "fallback_used",
        "no_candidate",
        "semantic_bonus_applied",
        "top_semantic_bonus",
        "recommendation_path",
        "recommended_visual",
    }
)


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _new_recommendation_id() -> str:
    return str(uuid.uuid4())


def _recommended_visual_payload(visual: Any) -> dict[str, Any] | None:
    """Minimal visual slice returned to the client (for later feedback comparison)."""
    if not isinstance(visual, dict):
        return None
    vtype = visual.get("type")
    value = visual.get("value")
    if not isinstance(vtype, str) or not isinstance(value, str):
        return None
    out: dict[str, Any] = {"type": vtype, "value": value}
    color = visual.get("color")
    if isinstance(color, str) and color.strip():
        out["color"] = color
    return out


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


def _observation_calibration_scores(
    rows: Sequence[CandidateRow],
    title_has_ui: bool,
) -> dict[str, float]:
    """Map candidate_id → calibration score in (0.5, 1.0] for log ambiguity analysis only."""
    if not rows:
        return {}
    components = _component_scores(rows, title_has_ui)
    base = len(rows) + 1
    rank_dimensions = len(components[0])
    max_score = sum((base - 1) * base**power for power in range(rank_dimensions))
    scores: dict[str, float] = {}
    for row, row_components in zip(rows, components, strict=True):
        weighted = sum(
            component * base**power
            for component, power in zip(
                row_components,
                reversed(range(rank_dimensions)),
                strict=True,
            )
        )
        scores[row.candidate_id] = round(0.5 + (weighted / max_score / 2), 3)
    return scores


def _title_has_ui_anchor(title: str) -> bool:
    from app.workflow_resolution import title_contains_interface_anchor

    return title_contains_interface_anchor(title)


def _catalog_ranking_snapshot(
    title: str,
    candidates: dict[str, Any],
) -> dict[str, Any]:
    """Observation-only ranking summary; mirrors offline ambiguity log scoring."""
    key_title = title.strip()
    rows = _dedupe_rows(rank_visual_candidate_rows(key_title, candidates))
    if not rows:
        return {
            "top_candidate": None,
            "candidates": [],
            "ambiguity_gap": None,
            "is_ambiguous": False,
            "no_candidate": True,
            "semantic_bonus_applied": False,
            "top_semantic_bonus": 0,
        }

    title_has_ui = _title_has_ui_anchor(key_title)
    calibration = _observation_calibration_scores(rows, title_has_ui)
    top_rows = rows[:TOP_CANDIDATES]
    rank1 = calibration[top_rows[0].candidate_id]
    rank2 = calibration[top_rows[1].candidate_id] if len(top_rows) > 1 else None
    # Gap between top-1 and top-2 calibration scores (not P6 tuple distance).
    gap = round(rank1 - rank2, 3) if rank2 is not None else None
    is_ambiguous = gap is not None and gap <= HIGH_AMBIGUITY_THRESHOLD

    candidate_entries: list[dict[str, Any]] = []
    for rank, row in enumerate(top_rows, start=1):
        candidate_entries.append(
            {
                "rank": rank,
                "candidate_id": row.candidate_id,
                # calibration score for ranking observation / ambiguity tooling
                "score": calibration[row.candidate_id],
                "semantic_bonus": row.semantic_bonus,
                "semantic_match_reason": list(row.semantic_match_reason),
                "semantic_metadata_fields_matched": list(row.semantic_metadata_fields_matched),
            }
        )

    top_row = top_rows[0]
    return {
        "top_candidate": top_row.candidate_id,
        "candidates": candidate_entries,
        "ambiguity_gap": gap,
        "is_ambiguous": is_ambiguous,
        "no_candidate": False,
        "semantic_bonus_applied": top_row.semantic_bonus > 0,
        "top_semantic_bonus": top_row.semantic_bonus,
    }


def _workflow_resolution_payload(
    title: str,
    *,
    case: dict[str, Any] | None = None,
    catalog_match: BestVisualCandidateMatch | None = None,
) -> dict[str, Any]:
    title_level = infer_workflow_resolution(title.strip())
    if case is not None:
        stored = case.get("workflow_resolution")
        if isinstance(stored, int):
            title_level = stored
    payload: dict[str, Any] = {"title_level": title_level}
    if catalog_match is not None:
        payload["winning_keyword_workflow_resolution"] = catalog_match.keyword_workflow_resolution
        payload["winning_interface_dominance"] = catalog_match.interface_dominance_effective
    return payload


def build_recommendation_log_entry(
    title: str,
    *,
    recommendation_id: str,
    case: dict[str, Any] | None = None,
    catalog_match: BestVisualCandidateMatch | None = None,
    candidates: dict[str, Any] | None = None,
    recommended_visual: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one JSON object for a recommendation execution (without timestamp)."""
    key_title = title.strip()
    entry: dict[str, Any] = {
        "recommendation_id": recommendation_id,
        "input_title": key_title,
        "resolved_workflow": infer_workflow_resolution(key_title),
        "fallback_used": False,
        "no_candidate": False,
        "recommended_visual": recommended_visual,
    }

    if case is not None:
        entry["recommendation_path"] = "sample_cases_exact_match"
        entry["fallback_used"] = True
        entry["top_candidate"] = None
        entry["candidates"] = []
        entry["ambiguity_gap"] = None
        entry["is_ambiguous"] = False
        entry["semantic_bonus_applied"] = False
        entry["top_semantic_bonus"] = 0
        entry["workflow_resolution"] = _workflow_resolution_payload(key_title, case=case)
        stored = case.get("workflow_resolution")
        if isinstance(stored, int):
            entry["resolved_workflow"] = stored
        if recommended_visual is None:
            entry["recommended_visual"] = _recommended_visual_payload(case.get("visual"))
        return entry

    assert candidates is not None
    snapshot = _catalog_ranking_snapshot(key_title, candidates)
    entry.update(snapshot)
    entry["recommendation_path"] = (
        "no_candidate" if snapshot.get("no_candidate") else "visual_candidates"
    )
    entry["workflow_resolution"] = _workflow_resolution_payload(
        key_title,
        catalog_match=catalog_match,
    )
    if catalog_match is not None:
        entry["top_candidate"] = catalog_match.candidate_id
        if recommended_visual is None:
            entry["recommended_visual"] = _recommended_visual_payload(catalog_match.data.get("visual"))
    return entry


def append_recommendation_log(
    entry: dict[str, Any],
    *,
    log_path: Path | None = None,
) -> None:
    """Append one observation line; creates ``logs/`` and file when missing."""
    path = log_path or DEFAULT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as newline:
        newline.write(line + "\n")


def log_recommendation_execution(
    title: str,
    *,
    case: dict[str, Any] | None = None,
    catalog_match: BestVisualCandidateMatch | None = None,
    candidates: dict[str, Any] | None = None,
    recommended_visual: dict[str, Any] | None = None,
    log_path: Path | None = None,
) -> str | None:
    """Record one recommendation run immediately before returning the API result.

    Logging failures are logged as warnings and do not propagate (recommendation API
    stability over strict log durability at this stage).

    Returns ``recommendation_id`` when the log line was written, else ``None``.
    """
    recommendation_id = _new_recommendation_id()
    try:
        body = build_recommendation_log_entry(
            title,
            recommendation_id=recommendation_id,
            case=case,
            catalog_match=catalog_match,
            candidates=candidates,
            recommended_visual=recommended_visual,
        )
        body["timestamp"] = _utc_timestamp()
        append_recommendation_log(body, log_path=log_path)
    except Exception:
        logger.warning(
            "recommendation log append failed (recommendation_id=%s)",
            recommendation_id,
            exc_info=True,
        )
        return None
    return recommendation_id

