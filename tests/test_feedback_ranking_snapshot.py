"""Tests for feedback ranking snapshot helpers."""

from __future__ import annotations

import unittest

from app.feedback_ranking_snapshot import (
    build_snapshot_from_candidate_rows,
    infer_default_accept_quality,
    infer_ranking_confidence,
    merge_ranking_snapshot,
    normalize_accept_quality,
)


class FeedbackRankingSnapshotTests(unittest.TestCase):
    def test_ranking_confidence_thresholds(self) -> None:
        self.assertEqual(infer_ranking_confidence(0.001), "low")
        self.assertEqual(infer_ranking_confidence(0.029), "low")
        self.assertEqual(infer_ranking_confidence(0.03), "medium")
        self.assertEqual(infer_ranking_confidence(0.05), "medium")
        self.assertEqual(infer_ranking_confidence(0.07), "high")
        self.assertEqual(infer_ranking_confidence(0.31), "high")
        self.assertEqual(infer_ranking_confidence(None), "unknown")

    def test_default_accept_quality(self) -> None:
        self.assertEqual(infer_default_accept_quality(0.31), "stable")
        self.assertEqual(infer_default_accept_quality(0.001), "unstable")
        self.assertEqual(infer_default_accept_quality(None), "unsure")

    def test_build_snapshot_from_candidates(self) -> None:
        snapshot = build_snapshot_from_candidate_rows(
            [
                {
                    "rank": 1,
                    "candidate_id": "folder_organization",
                    "visual": {"type": "emoji", "value": "📁"},
                    "score": 0.761,
                },
                {
                    "rank": 2,
                    "candidate_id": "taxi_service",
                    "visual": {"type": "emoji", "value": "🚕"},
                    "score": 0.76,
                },
            ]
        )
        self.assertEqual(snapshot["top1_candidate_id"], "folder_organization")
        self.assertEqual(snapshot["top1_top2_margin"], 0.001)
        self.assertEqual(snapshot["ranking_confidence"], "low")

    def test_merge_prefers_client_margin(self) -> None:
        merged = merge_ranking_snapshot(
            client_snapshot={"top1_top2_margin": 0.001, "top1_candidate_id": "folder_organization"},
            recommendation={
                "candidates": [
                    {"rank": 1, "candidate_id": "folder_organization", "score": 0.9},
                    {"rank": 2, "candidate_id": "taxi_service", "score": 0.5},
                ],
                "ambiguity_gap": 0.4,
            },
        )
        self.assertEqual(merged["top1_top2_margin"], 0.001)
        self.assertEqual(normalize_accept_quality(None, margin=0.001), "unstable")


if __name__ == "__main__":
    unittest.main()
