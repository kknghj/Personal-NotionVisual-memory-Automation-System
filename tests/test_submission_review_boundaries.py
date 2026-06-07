"""Submission vs submission-review boundary (Boundary Backlog 6)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match


class SubmissionReviewBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_submission_action_titles(self) -> None:
        cases = (
            "자료 제출",
            "결과자료 제출",
        )
        for title in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "document_submission")

    def test_submission_review_compounds(self) -> None:
        cases = (
            "자료 제출 검토",
            "제출자료 검토",
            "자료제출검토",
        )
        for title in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "approval_review")

    def test_submission_request_and_confirm(self) -> None:
        self.assertEqual(self._cid("자료 제출 요청"), "submission_request")
        self.assertEqual(self._cid("제출 확인"), "document_review")


if __name__ == "__main__":
    unittest.main()
