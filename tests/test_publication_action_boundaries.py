"""Publication action vs document/review boundary (Boundary Backlog 4)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

PUBLICATION_IDS = frozenset(
    {
        "public_posting",
        "publication_posting",
        "notice_posting",
        "publication_announcement",
    }
)
GENERIC_REVIEW_ID = "document_review"


class PublicationActionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_object_plus_post_prefers_publication(self) -> None:
        cases = (
            "정책자료 게시",
            "공지사항 게시",
            "안내문 게시",
        )
        for title in cases:
            with self.subTest(title=title):
                self.assertIn(self._cid(title), PUBLICATION_IDS)

    def test_noun_false_positive_stays_review(self) -> None:
        cases = (
            "게시판 확인",
            "공고번호 확인",
        )
        for title in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), GENERIC_REVIEW_ID)

    def test_review_not_publication(self) -> None:
        self.assertEqual(self._cid("자료 검토"), GENERIC_REVIEW_ID)
        self.assertEqual(self._cid("정책자료 검토"), GENERIC_REVIEW_ID)


if __name__ == "__main__":
    unittest.main()
