"""Metadata Pilot M1: physical object priority over generic document review."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

TARGET_TITLE = "을지훈련 매트리스 상태 확인"
TARGET_CANDIDATE = "physical_item_inspection"
TARGET_VISUAL = "🛏️"

REGRESSION_CASES: tuple[tuple[str, str], ...] = (
    ("공문 확인", "document_review"),
    ("결과보고 확인", "result_reporting"),
    ("자료 검토", "document_review"),
    ("문서 검토", "document_review"),
)


class ObjectPriorityMetadataPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _match(self, title: str) -> tuple[str, str]:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        visual = match.data.get("visual", {})
        value = visual.get("value", "")
        return match.candidate_id, value

    def test_mattress_status_check_prefers_physical_item_inspection(self) -> None:
        cid, visual = self._match(TARGET_TITLE)
        self.assertEqual(cid, TARGET_CANDIDATE)
        self.assertEqual(visual, TARGET_VISUAL)

    def test_document_review_regressions(self) -> None:
        for title, expected in REGRESSION_CASES:
            with self.subTest(title=title):
                cid, _ = self._match(title)
                self.assertEqual(cid, expected)


if __name__ == "__main__":
    unittest.main()
