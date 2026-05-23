"""Channel vs status_sharing boundaries for 현황 공유 titles with explicit channel hints.

status_sharing covers channel-agnostic status sharing; when the title names a
delivery channel (mail, messenger), the existing channel candidate must win.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

MAIL_CHANNEL_IDS = frozenset({"mail_action", "mail_sharing"})
MESSENGER_CHANNEL_IDS = frozenset({"messenger_chat"})


class StatusSharingChannelBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_mail_hint_prefers_mail_channel_over_status_sharing(self) -> None:
        cases = (
            ("서버 장애 대응 현황 메일 공유", MAIL_CHANNEL_IDS),
            ("고객 문의 대응 현황 이메일 공유", MAIL_CHANNEL_IDS),
        )
        for title, channel_ids in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], channel_ids, msg=top3)
                self.assertNotEqual(top3[0], "status_sharing")
                self.assertNotIn("result_reporting", top3)
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertIn(match.candidate_id, channel_ids)

    def test_messenger_hint_prefers_messenger_over_status_sharing(self) -> None:
        """Pure status-share + messenger hint → messenger_chat top1."""
        top3 = self._top_ids("프로젝트 진행 현황 메신저 공유", 3)
        self.assertEqual(top3[0], "messenger_chat", msg=top3)
        self.assertNotIn("status_sharing", top3)
        self.assertNotIn("result_reporting", top3)

    def test_event_prep_plus_messenger_keeps_channel_above_status_sharing(self) -> None:
        """행사 준비 + 카톡: event prep pair may win top1; channel still beats status_sharing."""
        title = "행사 준비 현황 카톡 공유"
        top3 = self._top_ids(title, 3)
        self.assertIn("messenger_chat", top3, msg=top3)
        self.assertNotIn("status_sharing", top3)
        self.assertNotIn("result_reporting", top3)
        self.assertLess(top3.index("messenger_chat"), len(top3))

    def test_channel_titles_do_not_route_status_sharing_to_top1(self) -> None:
        for title in (
            "서버 장애 대응 현황 메일 공유",
            "고객 문의 대응 현황 이메일 공유",
            "행사 준비 현황 카톡 공유",
            "프로젝트 진행 현황 메신저 공유",
        ):
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertNotEqual(top3[0], "status_sharing")


if __name__ == "__main__":
    unittest.main()
