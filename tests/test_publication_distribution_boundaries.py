"""Distribution vs publication boundaries for 배포·배부·게시·공고 titles.

``배포``/``배부``/보도자료·책자·앱 산출물 전달 → distribution.
``게시``/``공고``/``등록``/홈페이지 노출 → publication.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import rank_visual_candidate_rows

DISTRIBUTION_TOP1_IDS = frozenset(
    {
        "press_distribution",
        "booklet_distribution",
        "app_release",
        "document_distribution",
        "mail_distribution",
    }
)
PUBLICATION_TOP1_IDS = frozenset(
    {
        "publication_posting",
        "public_posting",
        "publication_announcement",
        "notice_posting",
        "publication_bulletin_update",
    }
)


class PublicationDistributionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_distribution_wins_on_deploy_and_distribute_titles(self) -> None:
        cases = (
            ("주간보도자료 배포", "press_distribution"),
            ("보도자료 배포", "press_distribution"),
            ("책자 배부", "booklet_distribution"),
            ("앱 신규 버전 배포", "app_release"),
            ("안내자료 배포", "document_distribution"),
            ("일반 문서 배포", "document_distribution"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertEqual(top3[0], expected, msg=top3)
                self.assertIn(top3[0], DISTRIBUTION_TOP1_IDS)

    def test_publication_wins_on_post_and_announce_titles(self) -> None:
        cases = (
            "홈페이지 공고 게시",
            "게시판 등록",
            "공개 모집 공고",
            "정책자료 공개 게시",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], PUBLICATION_TOP1_IDS, msg=top3)
                self.assertNotIn(top3[0], DISTRIBUTION_TOP1_IDS - {"mail_distribution"})

    def test_web_homepage_posting_prefers_public_posting(self) -> None:
        top3 = self._top_ids("홈페이지 배너 게시", 3)
        self.assertEqual(top3[0], "public_posting", msg=top3)

    def test_distribution_not_demoted_when_object_plus_deploy_verb(self) -> None:
        """보도자료 + 배포 stays distribution even when publication is in top3."""
        top3 = self._top_ids("보도자료 배포", 3)
        self.assertEqual(top3[0], "press_distribution", msg=top3)
        if "publication_posting" in top3:
            self.assertLess(top3.index("press_distribution"), top3.index("publication_posting"))


if __name__ == "__main__":
    unittest.main()
