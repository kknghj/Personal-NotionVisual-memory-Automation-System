"""Publication false-positive guard for object/context terms vs action phrases.

``공고번호``/``게시판`` alone (with ``확인``) must not route to publication posting.
Actual publish action phrases must still reach publication candidates.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import rank_visual_candidate_rows

PUBLICATION_IDS = frozenset(
    {
        "publication_posting",
        "public_posting",
        "publication_announcement",
        "notice_posting",
        "publication_bulletin_update",
        "publication_pinned_notice",
    }
)
PUBLICATION_ACTION_TOP1 = frozenset(
    {
        "publication_posting",
        "publication_announcement",
        "public_posting",
        "notice_posting",
    }
)


class PublicationContextGuardBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_context_object_terms_do_not_route_to_publication(self) -> None:
        cases = (
            "공고번호 확인",
            "게시판 확인",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertNotIn(top3[0], PUBLICATION_IDS, msg=top3)
                for cid in top3:
                    self.assertNotIn(cid, PUBLICATION_IDS, msg=f"{title}: {top3}")

    def test_action_phrase_titles_reach_publication_family(self) -> None:
        cases = (
            "공고문 게시",
            "홈페이지 공고 게시",
            "모집 공고 게시",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], PUBLICATION_ACTION_TOP1, msg=top3)


if __name__ == "__main__":
    unittest.main()
