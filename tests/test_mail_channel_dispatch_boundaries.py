"""Channel + dispatch boundary (Boundary Backlog 1: 행사자료 메일 송부).

When an explicit mail channel co-occurs with ``송부``, mail-channel candidates must beat
``document_distribution``. Bare ``object + 송부`` without channel stays on document dispatch.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

MAIL_CHANNEL_IDS = frozenset({"mail_action", "mail_sharing", "mail_distribution"})


class MailChannelDispatchBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_channel_plus_dispatch_prefers_mail_channel(self) -> None:
        cases = (
            "행사자료 메일 송부",
            "공문 메일 송부",
            "자료 메일 송부",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], MAIL_CHANNEL_IDS, msg=top3)
                self.assertNotEqual(top3[0], "document_distribution")
                self.assertIn(self._cid(title), MAIL_CHANNEL_IDS)

    def test_bare_dispatch_stays_document_distribution(self) -> None:
        cases = (
            "행사자료 송부",
            "자료 송부",
            "공문 송부",
        )
        for title in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "document_distribution")

    def test_mail_channel_dispatch_regressions(self) -> None:
        cases = (
            ("메일 발송", MAIL_CHANNEL_IDS),
            ("메일 확인", {"mail_action"}),
            ("이메일 자료 송부", MAIL_CHANNEL_IDS),
            ("메일로 자료 전달", MAIL_CHANNEL_IDS),
        )
        for title, expected_ids in cases:
            with self.subTest(title=title):
                self.assertIn(self._cid(title), expected_ids)


if __name__ == "__main__":
    unittest.main()
