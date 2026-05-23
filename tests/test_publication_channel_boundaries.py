"""Channel vs notice/publication boundary tests.

When a delivery channel (mail, messenger, etc.) is explicit, channel candidates
should beat notice/publication lifecycle candidates.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

CHANNEL_IDS = frozenset(
    {
        "mail_action",
        "mail_distribution",
        "mail_sharing",
        "messenger_chat",
        "phone_call",
    }
)
NOTICE_PUBLICATION_IDS = frozenset(
    {
        "notice_posting",
        "urgent_notice",
        "publication_posting",
        "public_posting",
        "publication_announcement",
        "publication_bulletin_update",
        "publication_pinned_notice",
    }
)


class PublicationChannelBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_messenger_hint_beats_notice_publication(self) -> None:
        for title in ("카카오톡 공지 전달", "카톡 안내 전달"):
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, CHANNEL_IDS)
                self.assertNotIn(cid, NOTICE_PUBLICATION_IDS)

    def test_mail_hint_beats_notice_publication(self) -> None:
        for title in ("제출자료 메일 안내", "교육안내 발송", "공지 메일 발송"):
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, {"mail_action", "mail_distribution"})
                self.assertNotIn(cid, NOTICE_PUBLICATION_IDS)

    def test_slack_channel_guidance_prefers_messenger(self) -> None:
        cid = self._cid("슬랙 채널 안내")
        self.assertEqual(cid, "messenger_chat")
        top3 = [row.candidate_id for row in rank_visual_candidate_rows("슬랙 채널 안내", self._cands)[:3]]
        self.assertNotIn("broadcast_channel_adjust", top3[:1])

    def test_mail_sharing_beats_publication_when_mail_explicit(self) -> None:
        cid = self._cid("회의자료 메일 공유")
        self.assertIn(cid, {"mail_sharing", "mail_action"})


if __name__ == "__main__":
    unittest.main()
