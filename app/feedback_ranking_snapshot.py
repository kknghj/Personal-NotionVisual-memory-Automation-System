"""Ranking snapshot helpers for feedback_log denormalization (schema v2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.feedback_export import format_visual_display
from app.recommendation_logging import DEFAULT_LOG_PATH as DEFAULT_RECOMMENDATION_PATH

MARGIN_STABLE_THRESHOLD = 0.03
MARGIN_HIGH_THRESHOLD = 0.07
LOW_CONFIDENCE_THRESHOLD = 0.03

ACCEPT_QUALITIES: frozenset[str] = frozenset({"stable", "unstable", "unsure"})
RANKING_CONFIDENCES: frozenset[str] = frozenset({"low", "medium", "high", "unknown"})

RANKING_SNAPSHOT_FIELDS: frozenset[str] = frozenset(
    {
        "top1_candidate_id",
        "top1_visual",
        "top1_score",
        "top2_candidate_id",
        "top2_visual",
        "top2_score",
        "top1_top2_margin",
        "ranking_confidence",
    }
)


def compute_margin(top1_score: Any, top2_score: Any) -> float | None:
    if not isinstance(top1_score, (int, float)) or not isinstance(top2_score, (int, float)):
        return None
    return round(float(top1_score) - float(top2_score), 3)


def infer_ranking_confidence(margin: float | None) -> str:
    if margin is None:
        return "unknown"
    if margin < MARGIN_STABLE_THRESHOLD:
        return "low"
    if margin < MARGIN_HIGH_THRESHOLD:
        return "medium"
    return "high"


def infer_default_accept_quality(margin: float | None) -> str:
    if margin is None:
        return "unsure"
    if margin >= MARGIN_STABLE_THRESHOLD:
        return "stable"
    return "unstable"


def is_low_confidence_margin(margin: float | None) -> bool:
    return margin is not None and margin < LOW_CONFIDENCE_THRESHOLD


def _visual_display_from_payload(visual: Any) -> str | None:
    if isinstance(visual, dict):
        return format_visual_display(visual)
    if isinstance(visual, str) and visual.strip():
        return visual.strip()
    return None


def build_snapshot_from_candidate_rows(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Build snapshot dict from API ``RankedCandidate``-like rows or log candidates."""
    if not candidates:
        return {}

    ordered = sorted(candidates, key=lambda row: int(row.get("rank") or 999))
    top1 = ordered[0]
    top2 = ordered[1] if len(ordered) > 1 else None

    top1_score = top1.get("score")
    top2_score = top2.get("score") if top2 else None
    margin = compute_margin(top1_score, top2_score)

    snapshot: dict[str, Any] = {
        "top1_candidate_id": top1.get("candidate_id"),
        "top1_visual": _visual_display_from_payload(top1.get("visual")),
        "top1_score": top1_score,
        "top2_candidate_id": top2.get("candidate_id") if top2 else None,
        "top2_visual": _visual_display_from_payload(top2.get("visual")) if top2 else None,
        "top2_score": top2_score,
        "top1_top2_margin": margin,
        "ranking_confidence": infer_ranking_confidence(margin),
    }
    return snapshot


def build_snapshot_from_recommendation_log(recommendation: dict[str, Any] | None) -> dict[str, Any]:
    if not recommendation:
        return {}
    candidates = recommendation.get("candidates") or []
    if not isinstance(candidates, list) or not candidates:
        gap = recommendation.get("ambiguity_gap")
        top_candidate = recommendation.get("top_candidate")
        if gap is None and not top_candidate:
            return {}
        margin = float(gap) if isinstance(gap, (int, float)) else None
        snapshot: dict[str, Any] = {
            "top1_candidate_id": top_candidate,
            "top1_visual": _visual_display_from_payload(recommendation.get("recommended_visual")),
            "top1_score": None,
            "top2_candidate_id": None,
            "top2_visual": None,
            "top2_score": None,
            "top1_top2_margin": margin,
            "ranking_confidence": infer_ranking_confidence(margin),
        }
        return snapshot
    return build_snapshot_from_candidate_rows(candidates)


def extract_margin_from_entry(
    entry: dict[str, Any] | None,
    recommendation: dict[str, Any] | None = None,
) -> float | None:
    if entry:
        stored = entry.get("top1_top2_margin")
        if isinstance(stored, (int, float)):
            return float(stored)
    if recommendation:
        gap = recommendation.get("ambiguity_gap")
        if isinstance(gap, (int, float)):
            return float(gap)
        candidates = recommendation.get("candidates") or []
        if len(candidates) >= 2:
            return compute_margin(
                candidates[0].get("score"),
                candidates[1].get("score"),
            )
    return None


def normalize_accept_quality(value: str | None, *, margin: float | None) -> str:
    if isinstance(value, str) and value.strip() in ACCEPT_QUALITIES:
        return value.strip()
    return infer_default_accept_quality(margin)


def merge_ranking_snapshot(
    *,
    client_snapshot: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prefer explicit client snapshot fields; fill gaps from recommendation log."""
    merged: dict[str, Any] = {}
    if client_snapshot:
        for key in RANKING_SNAPSHOT_FIELDS:
            value = client_snapshot.get(key)
            if value is not None:
                merged[key] = value

    log_snapshot = build_snapshot_from_recommendation_log(recommendation)
    for key, value in log_snapshot.items():
        if key not in merged or merged[key] is None:
            merged[key] = value

    margin = merged.get("top1_top2_margin")
    if margin is None and merged.get("top1_score") is not None and merged.get("top2_score") is not None:
        margin = compute_margin(merged.get("top1_score"), merged.get("top2_score"))
        merged["top1_top2_margin"] = margin

    if "ranking_confidence" not in merged or merged.get("ranking_confidence") is None:
        merged["ranking_confidence"] = infer_ranking_confidence(
            merged.get("top1_top2_margin") if isinstance(merged.get("top1_top2_margin"), (int, float)) else None
        )

    return {key: merged[key] for key in RANKING_SNAPSHOT_FIELDS if key in merged}


def load_recommendation_index(path: Path | None = None) -> dict[str, dict[str, Any]]:
    log_path = path or DEFAULT_RECOMMENDATION_PATH
    index: dict[str, dict[str, Any]] = {}
    if not log_path.is_file():
        return index
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        rid = row.get("recommendation_id")
        if isinstance(rid, str) and rid:
            index[rid] = row
    return index
