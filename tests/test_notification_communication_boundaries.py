"""notification_ops vs communication boundary tests.

One-way alert/notice/guidance vs two-way inquiry/reply/coordination.
See ``docs/workflow_ontology.md`` §8.5.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

NOTIFICATION_OPS_IDS = frozenset(
    {
        "notification_cleanup",
        "urgent_notice",
        "notice_posting",
        "mail_distribution",
    }
)
COMMUNICATION_IDS = frozenset(
    {
        "phone_call",
        "messenger_chat",
        "mail_action",
        "mail_request",
        "verbal_request",
    }
)
ONE_WAY_MAIL_IDS = frozenset({"mail_distribution", "mail_action"})


class NotificationCommunicationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_notification_oriented_titles(self) -> None:
        cases = (
            ("일정 알림 정리", NOTIFICATION_OPS_IDS),
            ("신청 안내 메일 발송", NOTIFICATION_OPS_IDS | ONE_WAY_MAIL_IDS),
            ("교육 일정 안내", NOTIFICATION_OPS_IDS | frozenset({"urgent_notice", "notice_posting"})),
            ("마감 알림 확인", NOTIFICATION_OPS_IDS),
            ("카톡 알림 정리", frozenset({"notification_cleanup"})),
        )
        for title, allowed in cases:
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, allowed, msg=f"{title} -> {cid}")

    def test_communication_oriented_titles(self) -> None:
        cases = (
            "담당자 문의",
            "카톡으로 담당자 확인",
            "메일 회신",
            "대표와 전화 협의",
            "센터 담당자와 연락",
        )
        for title in cases:
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, COMMUNICATION_IDS, msg=f"{title} -> {cid}")

    def test_one_way_guidance_mail_not_messenger_conversation(self) -> None:
        top3 = self._top_ids("안내 메일 발송", 3)
        self.assertIn(top3[0], ONE_WAY_MAIL_IDS | NOTIFICATION_OPS_IDS, msg=top3)
        self.assertNotEqual(top3[0], "messenger_chat")

    def test_mail_reply_not_one_way_notification(self) -> None:
        cid = self._cid("메일 회신")
        self.assertEqual(cid, "mail_action")
        top3 = self._top_ids("메일 회신", 3)
        self.assertNotIn("notification_cleanup", top3[:1])
        self.assertNotEqual(top3[0], "mail_distribution")

    def test_kakaotalk_alert_not_messenger_conversation(self) -> None:
        cid = self._cid("카톡 알림")
        self.assertEqual(cid, "notification_cleanup")
        top3 = self._top_ids("카톡 알림", 3)
        self.assertNotEqual(top3[0], "messenger_chat")

    def test_kakaotalk_inquiry_not_notification_cleanup(self) -> None:
        cid = self._cid("카톡 문의")
        self.assertIn(cid, COMMUNICATION_IDS)
        self.assertNotEqual(cid, "notification_cleanup")


if __name__ == "__main__":
    unittest.main()
