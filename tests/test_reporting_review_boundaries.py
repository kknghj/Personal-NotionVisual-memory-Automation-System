"""document.reporting vs document.review boundary tests.

Hierarchy brief / result delivery vs pre-submit review / confirm / read.
See ``docs/workflow_ontology.md`` §8.6.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

REVIEW_IDS = frozenset(
    {
        "document_review",
        "slide_deck_final_review",
        "approval_review",
    }
)
REPORTING_IDS = frozenset(
    {
        "document_reporting",
        "result_reporting",
    }
)
REVIEW_REQUEST_IDS = frozenset({"review_request"})
REVISION_REQUEST_IDS = frozenset({"collaborative_request"})
COMPOSE_IDS = frozenset({"document_edit", "status_summary"})


class ReportingReviewBoundaryTests(unittest.TestCase):
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

    def test_reporting_oriented_titles(self) -> None:
        cases = (
            "결과보고 전달",
            "검토 결과 보고",
            "진행상황 보고",
            "식생활교육 강사양성 현장 출장 결과 보고",
        )
        for title in cases:
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, REPORTING_IDS, msg=f"{title} -> {cid}")
                top3 = self._top_ids(title, 3)
                self.assertNotIn(top3[0], REVIEW_IDS, msg=top3)

    def test_review_oriented_titles(self) -> None:
        cases = (
            "보고서 검토",
            "보고자료 확인",
            "법령 검토",
            "ppt 최종본 확인",
        )
        for title in cases:
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, REVIEW_IDS, msg=f"{title} -> {cid}")
                top3 = self._top_ids(title, 3)
                self.assertNotIn(top3[0], REPORTING_IDS, msg=top3)

    def test_result_report_delivery_not_document_review(self) -> None:
        cid = self._cid("결과보고 전달")
        self.assertIn(cid, REPORTING_IDS)
        self.assertNotEqual(cid, "document_review")
        top3 = self._top_ids("결과보고 전달", 3)
        self.assertNotEqual(top3[0], "document_review")

    def test_report_compose_prefers_document_edit(self) -> None:
        cid = self._cid("결과 보고 작성")
        self.assertIn(cid, COMPOSE_IDS, msg=f"결과 보고 작성 -> {cid}")
        self.assertNotIn(cid, REPORTING_IDS)

    def test_final_review_request_is_review_request_not_reporting(self) -> None:
        cid = self._cid("최종 검토 요청")
        self.assertIn(cid, REVIEW_REQUEST_IDS)
        self.assertNotIn(cid, REPORTING_IDS)

    def test_report_revision_request_not_reporting_family(self) -> None:
        cid = self._cid("보고서 수정 요청")
        self.assertNotIn(cid, REPORTING_IDS)
        self.assertNotIn(cid, REVIEW_IDS)


if __name__ == "__main__":
    unittest.main()
