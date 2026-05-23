"""Publication vs notice vs document_edit boundary tests.

Notice = 알림·공지 내용 전달. Publication = 공식 게시·공고·노출.
Bare ``안내`` without 게시/공고 action must not route to publication.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

NOTICE_IDS = frozenset({"notice_posting", "urgent_notice"})
PUBLICATION_IDS = frozenset(
    {
        "publication_posting",
        "public_posting",
        "publication_announcement",
        "publication_bulletin_update",
        "publication_pinned_notice",
    }
)
DOCUMENT_EDIT_ID = "document_edit"


class PublicationNoticeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_notice_titles_prefer_notice_posting(self) -> None:
        for title in (
            "운영계획 공지",
            "서비스 점검 공지",
            "앱 업데이트 공지",
        ):
            with self.subTest(title=title):
                self.assertIn(self._cid(title), NOTICE_IDS)

    def test_publication_posting_and_announcement_titles(self) -> None:
        expectations = {
            "공문 게시": PUBLICATION_IDS,
            "신청안내 게시": PUBLICATION_IDS,
            "정책자료 게시": PUBLICATION_IDS,
            "홍보물 게시": PUBLICATION_IDS,
            "행사안내 공고": {"publication_announcement"},
            "만족도조사 공고": {"publication_announcement"},
            "공개 모집 공고": {"publication_announcement"},
        }
        for title, allowed in expectations.items():
            with self.subTest(title=title):
                self.assertIn(self._cid(title), allowed)

    def test_chat_room_notice_registration_stays_notice_family(self) -> None:
        cid = self._cid("채팅방 공지 등록")
        self.assertIn(cid, NOTICE_IDS | {"notice_posting"})

    def test_guidance_document_writing_stays_document_edit(self) -> None:
        for title in (
            "안내문 작성",
            "회의자료 작성",
            "검토자료 작성",
            "교육안내 자료 작성",
        ):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), DOCUMENT_EDIT_ID)

    def test_bare_guidance_without_posting_not_publication_top1(self) -> None:
        for title in ("검토결과 안내", "운영결과 안내", "만족도조사 링크 안내"):
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertNotIn(cid, PUBLICATION_IDS)

    def test_document_edit_beats_publication_for_internal_guidance_material(self) -> None:
        top3 = [
            row.candidate_id
            for row in rank_visual_candidate_rows("안내문 송부", self._cands)[:3]
        ]
        self.assertIn(DOCUMENT_EDIT_ID, top3[:2])


if __name__ == "__main__":
    unittest.main()
