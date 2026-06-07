"""UI/screen anchor vs document_edit boundary (Boundary Backlog 2)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

UI_INTERFACE_IDS = frozenset(
    {
        "qr_code_scan_auth",
        "qr_auth",
        "coding",
        "survey_form",
        "notion_docs_touchup",
        "spreadsheet_work",
        "terminal_work",
    }
)
GENERIC_REVIEW_ID = "document_review"


class InterfaceUiScreenBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_ui_screen_compose_prefers_interface_candidate(self) -> None:
        cases = (
            ("본인인증화면 수정 제안", "qr_code_scan_auth"),
            ("로그인 화면 수정", "coding"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)
                self.assertIn(self._cid(title), UI_INTERFACE_IDS)

    def test_document_compose_stays_document_edit(self) -> None:
        cases = (
            "문서 수정 제안",
            "보고서 수정",
        )
        for title in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "document_edit")

    def test_ui_screen_review_stays_generic_review(self) -> None:
        self.assertEqual(self._cid("본인인증 화면 검토"), GENERIC_REVIEW_ID)

    def test_request_compound_not_forced_to_ui_compose(self) -> None:
        self.assertEqual(self._cid("신청화면 수정 요청"), "collaborative_request")

    def test_ui_screen_boundary_regressions(self) -> None:
        rows = rank_visual_candidate_rows("안내문 수정", self._cands)
        self.assertGreater(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
