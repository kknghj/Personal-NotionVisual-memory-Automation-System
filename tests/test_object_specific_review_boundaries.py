"""Object-specific review vs generic document.review boundary (Boundary Pilot 1)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

GENERIC_REVIEW_ID = "document_review"
OBJECT_SPECIFIC_REVIEW_IDS = frozenset(
    {
        "press_release_review",
        "tax_invoice_review",
    }
)


class ObjectSpecificReviewBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_object_specific_review_titles(self) -> None:
        cases = (
            ("식생활교육 보도자료 확인", "press_release_review"),
            ("세금계산서 검토", "tax_invoice_review"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)

    def test_generic_review_titles_unchanged(self) -> None:
        cases = (
            "보고서 검토",
            "운영계획 검토",
            "공문 확인",
            "자료 확인",
            "사업계획서 검토",
            "행사자료 검토",
        )
        for title in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), GENERIC_REVIEW_ID)

    def test_review_request_not_object_specific_review(self) -> None:
        self.assertEqual(self._cid("보도자료 확인 요청"), "review_request")
        self.assertNotIn(self._cid("보도자료 확인 요청"), OBJECT_SPECIFIC_REVIEW_IDS)


if __name__ == "__main__":
    unittest.main()
