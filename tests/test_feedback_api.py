"""Feedback UI API tests (Phase 6-B)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.feedback_api import get_feedback_recent, get_visuals_catalog, post_feedback
from app.feedback_export import feedback_entry_to_override_example
from app.main import recommend_icon
from app.models import FeedbackRequest, RecommendRequest


class FeedbackApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.feedback_path = Path(self._tmpdir.name) / "feedback_log.jsonl"
        self._patches = [
            patch("app.feedback_logging.DEFAULT_LOG_PATH", self.feedback_path),
            patch("app.feedback_read.DEFAULT_LOG_PATH", self.feedback_path),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._tmpdir.cleanup()

    def _read_feedback(self) -> list[dict]:
        if not self.feedback_path.is_file():
            return []
        return [json.loads(line) for line in self.feedback_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_recommend_extended_response(self) -> None:
        with patch("app.recommendation_response.append_recommendation_log"):
            res = recommend_icon(RecommendRequest(title="보고서 확인"))
        self.assertFalse(res.no_candidate)
        self.assertEqual(res.recommendation_path, "visual_candidates")
        self.assertTrue(res.recommendation_id)
        self.assertIsInstance(res.candidates, list)
        if res.candidates:
            first = res.candidates[0]
            self.assertTrue(first.label)
            self.assertTrue(first.summary_reason)
            self.assertIsInstance(first.score, float)

    def test_no_candidate_returns_200(self) -> None:
        with patch("app.recommendation_response.append_recommendation_log"):
            res = recommend_icon(RecommendRequest(title="교육자료 정리"))
        self.assertTrue(res.no_candidate)
        self.assertIsNone(res.visual)
        self.assertEqual(res.recommendation_path, "no_candidate")
        self.assertEqual(res.candidates, [])
        self.assertTrue(res.recommendation_id)

    def test_post_feedback_accepted(self) -> None:
        res = post_feedback(
            FeedbackRequest(
                recommendation_id="rec-1",
                input_title="보고서 확인",
                feedback_type="accepted",
                system_recommended_visual={"type": "emoji", "value": "📄"},
                final_selected_visual={"type": "emoji", "value": "📄"},
            )
        )
        self.assertEqual(res.feedback_type, "accepted")
        rows = self._read_feedback()
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["accepted_system_recommendation"])

    def test_post_feedback_override_requires_reason(self) -> None:
        from fastapi import HTTPException

        with self.assertRaises(HTTPException) as ctx:
            post_feedback(
                FeedbackRequest(
                    input_title="점심 카톡 확인",
                    feedback_type="override",
                    system_recommended_visual={"type": "emoji", "value": "💬"},
                    final_selected_visual={"type": "emoji", "value": "📱"},
                )
            )
        self.assertEqual(ctx.exception.status_code, 422)

    def test_post_feedback_override_manual_visual(self) -> None:
        res = post_feedback(
            FeedbackRequest(
                input_title="신규 업무",
                feedback_type="override",
                system_recommended_visual=None,
                final_selected_visual={"type": "notion_icon", "value": "airplane", "color": "blue"},
                override_reason="catalog_gap",
                user_note="catalog에 없는 icon 직접 선택",
            )
        )
        self.assertEqual(res.feedback_type, "manual_without_recommendation")
        row = self._read_feedback()[0]
        self.assertEqual(row["final_selected_visual"]["value"], "airplane")

    def test_post_feedback_no_candidate(self) -> None:
        res = post_feedback(
            FeedbackRequest(
                recommendation_id="rec-nc",
                input_title="교육자료 정리",
                feedback_type="no_candidate",
            )
        )
        self.assertEqual(res.feedback_type, "no_candidate_selected")

    def test_feedback_recent(self) -> None:
        post_feedback(FeedbackRequest(input_title="A", feedback_type="no_candidate"))
        rows = get_feedback_recent(limit=5)
        self.assertEqual(len(rows), 1)

    def test_visuals_catalog(self) -> None:
        res = get_visuals_catalog()
        self.assertGreater(len(res.items), 0)
        self.assertTrue(res.items[0].candidate_id)
        self.assertTrue(res.items[0].label)

    def test_export_override_example_shape(self) -> None:
        entry = {
            "timestamp": "2026-06-09T00:00:00Z",
            "recommendation_id": "r1",
            "input_title": "교육자료 정리",
            "system_recommended_visual": None,
            "final_selected_visual": None,
            "feedback_type": "no_candidate_selected",
            "override_reason": "catalog_gap",
            "user_note": "적합 후보 없음",
        }
        ex = feedback_entry_to_override_example(entry)
        self.assertEqual(ex["recommended_visual"], "없음")
        self.assertEqual(ex["source"], "feedback_ui")
        self.assertIn("catalog_gap", ex["note"])


if __name__ == "__main__":
    unittest.main()
