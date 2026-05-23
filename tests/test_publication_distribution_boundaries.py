"""Distribution vs publication boundary tests.

배포·배부·보도자료·책자·앱 배포는 publication보다 distribution 계열이 우선한다.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

DISTRIBUTION_IDS = frozenset(
    {
        "press_distribution",
        "booklet_distribution",
        "app_release",
        "document_distribution",
        "mail_distribution",
    }
)
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


class PublicationDistributionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_press_release_distribution(self) -> None:
        for title in ("보도자료 배포", "주간보도자료 배포"):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "press_distribution")

    def test_booklet_and_app_distribution(self) -> None:
        self.assertEqual(self._cid("책자 배부"), "booklet_distribution")
        self.assertEqual(self._cid("앱 신규버전 배포"), "app_release")

    def test_general_material_distribution(self) -> None:
        for title in ("결과자료 배포", "공지사항 배포", "행사포스터 배포", "신규서식 배포"):
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, DISTRIBUTION_IDS)
                self.assertNotIn(cid, PUBLICATION_IDS)

    def test_posting_action_still_publication_when_no_distribution_verb(self) -> None:
        for title in ("보도자료 게시", "교육자료 게시", "공문 게시"):
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(
                    cid,
                    {
                        "publication_posting",
                        "public_posting",
                        "publication_announcement",
                    },
                )


if __name__ == "__main__":
    unittest.main()
