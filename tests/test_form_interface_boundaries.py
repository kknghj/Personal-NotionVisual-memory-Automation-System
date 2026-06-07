"""Form interface vs document receipt boundary (Boundary Backlog 3)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match


class FormInterfaceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_form_anchor_receipt_prefers_survey_form(self) -> None:
        self.assertEqual(self._cid("네이버폼 신청 접수"), "survey_form")

    def test_bare_document_receipt_not_survey_form(self) -> None:
        cases = ("신청 접수", "신청서 접수")
        for title in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "document_submission")

    def test_form_interface_boundary_regressions(self) -> None:
        cases = (
            ("네이버폼 응답 확인", "survey_form"),
            ("접수현황 확인", "status_check"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)


if __name__ == "__main__":
    unittest.main()
