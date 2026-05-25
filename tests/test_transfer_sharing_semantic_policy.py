"""전달 / 송부 / 공유 semantic policy boundaries.

Generic ``전달`` must not route to ``mail_action`` without channel.
``송부`` formal dispatch → ``document_distribution`` (not ``document_edit``).
Document vs access/key ``공유`` split.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

MAIL_CHANNEL_IDS = frozenset({"mail_action", "mail_sharing", "mail_distribution"})
DISTRIBUTION_IDS = frozenset(
    {
        "document_distribution",
        "mail_distribution",
        "press_distribution",
        "booklet_distribution",
        "app_release",
    },
)
DOCUMENT_SHARING_IDS = frozenset({"document_sharing", "status_sharing"})
ACCESS_SHARING_IDS = frozenset({"credential_sharing"})


class TransferSharingSemanticPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_generic_transfer_does_not_force_mail_action(self) -> None:
        """``자료 전달`` — object-bound transfer; must not top1 ``mail_action``."""
        top3 = self._top_ids("자료 전달", 3)
        self.assertNotEqual(top3[0], "mail_action", msg=top3)
        self.assertEqual(top3[0], "document_distribution", msg=top3)
        match = find_best_visual_candidate_match("자료 전달", self._cands)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertNotEqual(match.candidate_id, "mail_action")
        self.assertEqual(match.candidate_id, "document_distribution")

    def test_channel_plus_transfer_prefers_mail_action(self) -> None:
        top3 = self._top_ids("메일로 자료 전달", 3)
        self.assertIn(top3[0], MAIL_CHANNEL_IDS, msg=top3)
        match = find_best_visual_candidate_match("메일로 자료 전달", self._cands)
        self.assertIsNotNone(match)
        assert match is not None
        self.assertIn(match.candidate_id, MAIL_CHANNEL_IDS)

    def test_formal_dispatch_titles_prefer_document_distribution(self) -> None:
        cases = (
            "공문 송부",
            "검토자료 송부",
            "정산서류 송부",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertEqual(top3[0], "document_distribution", msg=top3)
                self.assertNotEqual(top3[0], "document_edit")
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertEqual(match.candidate_id, "document_distribution")

    def test_document_sharing_titles(self) -> None:
        cases = (
            "문서 공유",
            "자료 공유",
            "링크 공유",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], DOCUMENT_SHARING_IDS, msg=top3)
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertIn(match.candidate_id, DOCUMENT_SHARING_IDS)

    def test_access_sharing_beats_document_sharing(self) -> None:
        cases = (
            "암호 공유",
            "계정 권한 공유",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], ACCESS_SHARING_IDS, msg=top3)
                if "document_sharing" in top3:
                    self.assertLess(
                        top3.index(top3[0]),
                        top3.index("document_sharing"),
                    )
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertIn(match.candidate_id, ACCESS_SHARING_IDS)

    def test_songbu_not_document_edit_top1(self) -> None:
        """Regression: bare ``송부`` on document subjects must not top1 ``document_edit``."""
        for title in ("안내문 송부", "행사자료 송부"):
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertNotEqual(top3[0], "document_edit", msg=top3)
                self.assertIn(top3[0], DISTRIBUTION_IDS, msg=top3)

    def test_mail_channel_can_win_on_mail_dispatch_phrase(self) -> None:
        """Channel + dispatch: mail channel may beat ``document_distribution`` (policy allows)."""
        top3 = self._top_ids("공문 메일 송부", 3)
        self.assertIn(top3[0], MAIL_CHANNEL_IDS | {"document_distribution"}, msg=top3)
        if top3[0] in MAIL_CHANNEL_IDS:
            return
        self.assertEqual(top3[0], "document_distribution")

    def test_mail_channel_synonyms_prefer_mail_candidates(self) -> None:
        """``이메일``·``아웃룩`` are mail interface anchors like ``메일``."""
        cases = (
            "이메일 자료 송부",
            "아웃룩으로 자료 전달",
            "이메일 발송",
            "메일 발송",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], MAIL_CHANNEL_IDS, msg=top3)
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertIn(match.candidate_id, MAIL_CHANNEL_IDS)

    def test_object_bound_transfer_routes_to_document_distribution(self) -> None:
        """``object + 전달`` (no channel) → ``document_distribution``, not ``document_review``."""
        cases = (
            "자료 전달",
            "공문 전달",
            "회의자료 전달",
            "검토자료 전달",
            "결과자료 전달",
            "파일 전달",
            "서류 전달",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertEqual(top3[0], "document_distribution", msg=top3)
                self.assertNotEqual(top3[0], "document_review")
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertEqual(match.candidate_id, "document_distribution")

    def test_ambiguous_transfer_titles_not_forced_to_distribution(self) -> None:
        """Bare/generic transfer without distribution object stays ambiguous or non-distribution top1."""
        cases = (
            ("운영현황 전달", "document_review"),
            ("내용 전달", "document_review"),
            ("정보 전달", "document_review"),
            ("결과보고 전달", "result_reporting"),
        )
        for title, expected_top in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertEqual(top3[0], expected_top, msg=top3)
                self.assertNotEqual(top3[0], "document_distribution")

    def test_object_bound_transfer_regressions(self) -> None:
        """Channel/formal dispatch/sharing policies must survive object-bound routing."""
        cases = (
            ("메일로 자료 전달", MAIL_CHANNEL_IDS),
            ("공문 송부", {"document_distribution"}),
            ("문서 공유", DOCUMENT_SHARING_IDS),
            ("암호 공유", ACCESS_SHARING_IDS),
        )
        for title, expected_ids in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], expected_ids, msg=top3)
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertIn(match.candidate_id, expected_ids)


if __name__ == "__main__":
    unittest.main()
