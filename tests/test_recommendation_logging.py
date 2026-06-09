"""P3 recommendation observation log (JSONL) contract tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.data_loader import load_visual_candidates
from app.main import get_sample_cases, get_visual_candidates, recommend_icon
from app.models import RecommendRequest
from app.recommendation_logging import (
    REQUIRED_LOG_FIELDS,
    append_recommendation_log,
    build_recommendation_log_entry,
    log_recommendation_execution,
    _new_recommendation_id,
)
from app.recommendation_response import run_recommendation
from app.recommender import find_best_visual_candidate_match


class RecommendationLoggingTests(unittest.TestCase):
    """Observation log at logs/recommendation_log.jsonl must not change recommendations."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmpdir.name) / "recommendation_log.jsonl"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _read_lines(self) -> list[dict]:
        if not self.log_path.is_file():
            return []
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def _recommend(self, title: str):
        return run_recommendation(
            title,
            sample_cases=get_sample_cases(),
            visual_candidates=get_visual_candidates(),
            log_path=self.log_path,
        )

    def test_log_file_created_on_recommendation(self) -> None:
        self._recommend("점심 카톡 확인")
        self.assertTrue(self.log_path.is_file())

    def test_one_line_appended_per_execution(self) -> None:
        self._recommend("점심 카톡 확인")
        self._recommend("보고서 확인")
        self.assertEqual(len(self._read_lines()), 2)

    def test_required_fields_present(self) -> None:
        self._recommend("보고서 확인")
        row = self._read_lines()[0]
        for field in REQUIRED_LOG_FIELDS:
            self.assertIn(field, row, msg=field)

    def test_recommendation_unchanged_when_logging_enabled(self) -> None:
        title = "보고서 확인"
        with patch("app.recommendation_response.append_recommendation_log"):
            baseline = recommend_icon(RecommendRequest(title=title))
        logged = self._recommend(title)
        baseline_dump = baseline.model_dump()
        logged_dump = logged.model_dump()
        baseline_dump.pop("recommendation_id", None)
        logged_dump.pop("recommendation_id", None)
        self.assertEqual(baseline_dump, logged_dump)

    def test_fallback_exact_match_logged(self) -> None:
        self._recommend("점심 카톡 확인")
        row = self._read_lines()[0]
        self.assertTrue(row["fallback_used"])
        self.assertFalse(row["no_candidate"])
        self.assertEqual(row["recommendation_path"], "sample_cases_exact_match")
        self.assertIsNone(row["top_candidate"])
        vis = row["recommended_visual"]
        self.assertIsInstance(vis, dict)
        self.assertEqual(vis["type"], "emoji")
        self.assertEqual(vis["value"], "💬")

    def test_recommendation_ids_are_unique(self) -> None:
        r1 = self._recommend("점심 카톡 확인")
        r2 = self._recommend("보고서 확인")
        self.assertNotEqual(r1.recommendation_id, r2.recommendation_id)
        ids = [row["recommendation_id"] for row in self._read_lines()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_logging_failure_does_not_break_recommendation(self) -> None:
        with patch(
            "app.recommendation_response.append_recommendation_log",
            side_effect=OSError("disk full"),
        ):
            res = recommend_icon(RecommendRequest(title="보고서 확인"))
        self.assertEqual(res.visual.value, "📄")

    def test_no_candidate_logged_with_200_response(self) -> None:
        title = "교육자료 정리"
        res = self._recommend(title)
        self.assertTrue(res.no_candidate)
        self.assertIsNone(res.visual)
        self.assertEqual(res.recommendation_path, "no_candidate")
        row = self._read_lines()[0]
        self.assertTrue(row["no_candidate"])
        self.assertFalse(row["fallback_used"])
        self.assertIsNone(row["top_candidate"])
        self.assertEqual(row["recommendation_path"], "no_candidate")
        self.assertIsNone(row["recommended_visual"])

    def test_catalog_path_includes_top_three_candidates_with_scores(self) -> None:
        cands = load_visual_candidates()
        entry = build_recommendation_log_entry(
            "보고서 확인",
            recommendation_id=_new_recommendation_id(),
            catalog_match=find_best_visual_candidate_match("보고서 확인", cands),
            candidates=cands,
        )
        self.assertEqual(len(entry["candidates"]), 3)
        for item in entry["candidates"]:
            self.assertIn("candidate_id", item)
            self.assertIn("score", item)
            self.assertIsInstance(item["score"], float)

    def test_append_creates_parent_directory(self) -> None:
        nested = Path(self._tmpdir.name) / "nested" / "log.jsonl"
        append_recommendation_log({"timestamp": "2026-01-01T00:00:00Z", "probe": True}, log_path=nested)
        self.assertTrue(nested.is_file())

    def test_log_recommendation_execution_still_works(self) -> None:
        rec_id = log_recommendation_execution(
            "보고서 확인",
            catalog_match=find_best_visual_candidate_match("보고서 확인", load_visual_candidates()),
            candidates=load_visual_candidates(),
            log_path=self.log_path,
        )
        self.assertIsNotNone(rec_id)
        self.assertEqual(len(self._read_lines()), 1)


if __name__ == "__main__":
    unittest.main()
