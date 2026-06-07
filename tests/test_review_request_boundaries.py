"""Review request vs object-specific review boundary (Boundary Backlog 5)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

OBJECT_SPECIFIC_REVIEW_IDS = frozenset({"press_release_review", "tax_invoice_review"})


class ReviewRequestBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_object_review_without_request_stays_object_specific(self) -> None:
        self.assertEqual(self._cid("보도자료 검토"), "press_release_review")

    def test_review_request_compound_prefers_request_workflow(self) -> None:
        cases = (
            ("보도자료 검토 요청", "review_request"),
            ("자료 검토 요청", "review_request"),
            ("계획서 검토 요청", "review_request"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)
                self.assertNotIn(self._cid(title), OBJECT_SPECIFIC_REVIEW_IDS)

    def test_review_request_regressions(self) -> None:
        self.assertEqual(self._cid("보도자료 확인"), "press_release_review")
        self.assertEqual(self._cid("세금계산서 확인 요청"), "review_request")


if __name__ == "__main__":
    unittest.main()
