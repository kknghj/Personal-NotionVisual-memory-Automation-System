"""Notice vs publication vs document_edit boundaries for 게시·공고·안내 titles.

notice: 알림·공지 내용. publication: 공식 게시·공고·공개 노출.
단순 ``안내``/``공지`` 단어만으로 publication action으로 보내지 않고,
``작성``이 있으면 document_edit과 경쟁한다.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

NOTICE_TOP1_IDS = frozenset(
    {
        "notice_posting",
        "urgent_notice",
        "publication_pinned_notice",
    }
)
PUBLICATION_TOP1_IDS = frozenset(
    {
        "publication_posting",
        "public_posting",
        "publication_announcement",
        "notice_posting",
        "publication_bulletin_update",
        "publication_pinned_notice",
    }
)
ANNOUNCEMENT_TOP1_IDS = frozenset(
    {
        "publication_announcement",
        "publication_posting",
    }
)
DOCUMENT_WRITE_TOP1_IDS = frozenset({"document_edit"})


class PublicationNoticeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_notice_posting_for_service_notice_titles(self) -> None:
        cases = (
            "공지사항 게시",
            "서비스 점검 공지 게시",
            "안내문 게시",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], NOTICE_TOP1_IDS | {"publication_posting"}, msg=top3)
                self.assertNotIn("document_edit", top3[:1])

    def test_publication_announcement_for_recruitment_and_call_titles(self) -> None:
        cases = (
            "채용 공고 게시",
            "공개 모집 공고",
            "홈페이지 공고 게시",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], ANNOUNCEMENT_TOP1_IDS, msg=top3)

    def test_bulletin_and_pin_publication_actions(self) -> None:
        self.assertEqual(self._top_ids("게시판 등록", 1)[0], "publication_bulletin_update")
        self.assertEqual(self._top_ids("상단 고정 공지", 1)[0], "publication_pinned_notice")

    def test_document_writing_beats_publication_on_compose_titles(self) -> None:
        cases = (
            "회의 안내문 작성",
            "행사 안내문 작성",
            "검토자료 작성",
            "안내문 작성",
            "운영계획 공지 작성",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], DOCUMENT_WRITE_TOP1_IDS, msg=top3)
                self.assertNotIn(
                    top3[0],
                    frozenset({"publication_posting", "publication_announcement", "notice_posting"}),
                    msg=f"publication must not beat document write: {top3}",
                )
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertEqual(match.candidate_id, "document_edit")

    def test_bare_guide_word_does_not_force_publication_top1(self) -> None:
        """``단순 안내 작성`` stays on document_edit, not publication."""
        top3 = self._top_ids("단순 안내 작성", 3)
        self.assertEqual(top3[0], "document_edit", msg=top3)


if __name__ == "__main__":
    unittest.main()
