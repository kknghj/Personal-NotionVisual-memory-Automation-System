"""tracking/status_work vs document.reporting boundary tests.

Ongoing status visibility vs hierarchy brief / result delivery.
See ``docs/workflow_ontology.md`` §8.7.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

TRACKING_STATUS_IDS = frozenset(
    {
        "status_check",
        "progress_monitoring",
        "allocation_tracking",
        "response_tracking",
        "budget_tracking",
        "status_summary",
        "status_sharing",
        "status_update",
    }
)
REPORTING_IDS = frozenset(
    {
        "document_reporting",
        "result_reporting",
    }
)
REVIEW_IDS = frozenset(
    {
        "document_review",
        "slide_deck_final_review",
        "approval_review",
    }
)


class StatusReportingBoundaryTests(unittest.TestCase):
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

    def test_status_monitor_titles_prefer_tracking_family(self) -> None:
        cases = (
            ("운영 현황 확인", {"status_check"}),
            ("고객 민원 처리 현황 확인", {"status_check"}),
        )
        for title, expected_top in cases:
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, TRACKING_STATUS_IDS, msg=f"{title} -> {cid}")
                self.assertIn(cid, expected_top, msg=f"{title} -> {cid}")
                top3 = self._top_ids(title, 3)
                self.assertNotIn(top3[0], REPORTING_IDS, msg=top3)
                self.assertNotIn(top3[0], REVIEW_IDS, msg=top3)

    def test_status_reporting_titles_prefer_reporting_family(self) -> None:
        cases = (
            "진행 현황 보고",
            "실적 보고",
            "진행상황 보고",
        )
        for title in cases:
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, REPORTING_IDS, msg=f"{title} -> {cid}")
                top3 = self._top_ids(title, 3)
                self.assertNotIn(top3[0], {"status_check", "progress_monitoring"}, msg=top3)

    def test_result_status_report_title(self) -> None:
        cid = self._cid("결과 현황 보고")
        self.assertIn(cid, REPORTING_IDS)
        self.assertEqual(cid, "result_reporting")

    def test_status_share_not_reporting(self) -> None:
        cid = self._cid("신청 현황 공유")
        self.assertIn(cid, {"status_sharing", "document_sharing"})
        self.assertNotIn(cid, REPORTING_IDS)

    def test_bare_status_title_has_tracking_candidate(self) -> None:
        cid = self._cid("사업 추진 현황")
        self.assertIn(
            cid,
            {"progress_monitoring", "status_check", "document_reporting"},
            msg=f"사업 추진 현황 -> {cid}",
        )
        self.assertNotIn(cid, REVIEW_IDS)

    def test_status_organize_stays_status_work(self) -> None:
        cid = self._cid("운영 현황 정리")
        self.assertEqual(cid, "status_summary")
        self.assertNotIn(cid, REPORTING_IDS)

    def test_nationwide_status_report_stays_reporting(self) -> None:
        cid = self._cid("전국 식생활교육 현황 보고")
        self.assertIn(cid, REPORTING_IDS)

    def test_reporting_review_regression_unchanged(self) -> None:
        self.assertEqual(self._cid("보고서 검토"), "document_review")
        self.assertEqual(self._cid("검토 결과 보고"), "result_reporting")
        self.assertEqual(self._cid("결과보고 전달"), "result_reporting")


if __name__ == "__main__":
    unittest.main()
