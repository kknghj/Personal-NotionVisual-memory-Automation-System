"""Channel vs notice/publication boundaries when delivery medium is explicit.

When the title names mail, messenger, or similar channel hints, channel candidates
must beat notice_posting and publication_* candidates.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

MAIL_CHANNEL_IDS = frozenset({"mail_action", "mail_sharing", "mail_distribution"})
MESSENGER_CHANNEL_IDS = frozenset({"messenger_chat"})
PUBLICATION_IDS = frozenset(
    {
        "publication_posting",
        "publication_announcement",
        "notice_posting",
        "public_posting",
    }
)


class PublicationChannelBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_mail_hint_beats_notice_and_publication(self) -> None:
        cases = (
            ("안내 메일 발송", MAIL_CHANNEL_IDS),
            ("공지 메일 발송", MAIL_CHANNEL_IDS),
            ("공고 메일 발송", MAIL_CHANNEL_IDS),
        )
        for title, channel_ids in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], channel_ids, msg=top3)
                self.assertNotIn(top3[0], PUBLICATION_IDS)
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertIn(match.candidate_id, channel_ids)

    def test_messenger_hint_beats_notice_and_publication(self) -> None:
        cases = (
            "공지 카톡 전달",
            "행사 안내 메신저 공유",
            "카톡 공지 전달",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], MESSENGER_CHANNEL_IDS, msg=top3)
                self.assertNotIn(top3[0], PUBLICATION_IDS)

    def test_mail_sharing_beats_publication_on_share_titles(self) -> None:
        cases = (
            "자료 메일 공유",
            "공지사항 메일 공유",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], MAIL_CHANNEL_IDS, msg=top3)
                self.assertNotIn(top3[0], PUBLICATION_IDS)

    def test_channel_titles_do_not_route_publication_to_top1(self) -> None:
        for title in (
            "안내 메일 발송",
            "공지 카톡 전달",
            "행사 안내 메신저 공유",
            "자료 메일 공유",
        ):
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertNotIn(top3[0], PUBLICATION_IDS, msg=top3)


if __name__ == "__main__":
    unittest.main()
