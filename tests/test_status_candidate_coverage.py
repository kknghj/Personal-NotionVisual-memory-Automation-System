"""Status candidate coverage: null-top reduction and reporting boundary regression.

Complements ``test_status_workflow_coverage.py`` with ranking-depth checks
(top1/top2) and workflow_stage contracts for reporting titles.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows
from app.semantic_scoring import (
    detect_status_work_action,
    infer_workflow_stage_detail,
    is_result_status_reporting_compound,
)

STATUS_CANDIDATE_IDS = frozenset({"status_summary", "status_sharing", "status_update"})


class StatusCandidateCoverageTests(unittest.TestCase):
    """New status_* candidates appear in ranking for 현황 정리/공유/업데이트 titles."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 2) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def _assert_status_in_top_n(self, title: str, expect_id: str, n: int = 2) -> None:
        top = self._top_ids(title, n)
        self.assertIn(expect_id, top, msg=f"{title}: top{n}={top}")

    def test_coverage_titles_no_longer_null_top(self) -> None:
        for title in (
            "프로젝트 진행 현황 정리",
            "서버 장애 대응 현황 공유",
            "재고 관리 현황 업데이트",
        ):
            with self.subTest(title=title):
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)

    def test_status_summary_top_or_top2(self) -> None:
        self._assert_status_in_top_n("프로젝트 진행 현황 정리", "status_summary", 1)
        self._assert_status_in_top_n("분기별 예산 집행 현황 정리", "status_summary", 2)

    def test_budget_title_may_compete_with_spreadsheet(self) -> None:
        top2 = self._top_ids("분기별 예산 집행 현황 정리", 2)
        self.assertIn("status_summary", top2)
        self.assertTrue(
            top2[0] in {"status_summary", "spreadsheet_work", "budget_tracking"},
            msg=top2,
        )

    def test_status_sharing_top_or_top2(self) -> None:
        self._assert_status_in_top_n("서버 장애 대응 현황 공유", "status_sharing", 1)

    def test_department_share_allows_document_or_status_sharing(self) -> None:
        top2 = self._top_ids("부서별 현황 자료 공유", 2)
        self.assertIn(top2[0], ("document_sharing", "status_sharing"))
        self.assertIn("status_sharing", top2)
        self.assertNotIn("result_reporting", top2)

    def test_status_update_top_or_top2(self) -> None:
        self._assert_status_in_top_n("재고 관리 현황 업데이트", "status_update", 1)


class StatusBoundaryRegressionTests(unittest.TestCase):
    """결과+현황 compound and reporting/submission routes stay on legacy candidates."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_result_status_compound_prefers_result_reporting(self) -> None:
        for title in (
            "점검 결과 현황 공유",
            "교육 운영 결과 현황 정리",
            "사업 운영 결과 현황 보고",
        ):
            with self.subTest(title=title):
                self.assertTrue(is_result_status_reporting_compound(title))
                self.assertEqual(self._cid(title), "result_reporting")

    def test_nationwide_status_report_keeps_document_reporting(self) -> None:
        self.assertEqual(self._cid("전국 식생활교육 현황 보고"), "document_reporting")
        detail = infer_workflow_stage_detail("전국 식생활교육 현황 보고")
        self.assertIsNone(detail["inferred_workflow_stage"])
        self.assertLessEqual(detail["workflow_stage_confidence"], 0.2)

    def test_submission_titles_stay_off_status_update(self) -> None:
        for title in ("보험 가입현황 제출", "비상소집 응소자 현황 제출"):
            with self.subTest(title=title):
                self.assertIsNone(detect_status_work_action(title))
                self.assertEqual(self._cid(title), "document_edit")
                rows = rank_visual_candidate_rows(title, self._cands)
                self.assertFalse(any(r.candidate_id == "status_update" for r in rows[:3]))

    def test_jinhaeng_sanghwang_report_keeps_progress_strong_signal(self) -> None:
        detail = infer_workflow_stage_detail("진행상황 보고")
        self.assertEqual(detail["inferred_workflow_stage"], "progress")
        self.assertGreaterEqual(detail["workflow_stage_confidence"], 0.8)
        self.assertEqual(detail["workflow_stage_source"], "keyword:진행상황")
        self.assertEqual(self._cid("진행상황 보고"), "document_reporting")


class StatusWorkSemanticBoostTests(unittest.TestCase):
    def test_detect_status_work_action_mapping(self) -> None:
        self.assertEqual(
            detect_status_work_action("프로젝트 진행 현황 정리"),
            "organize_summarize",
        )
        self.assertEqual(
            detect_status_work_action("서버 장애 대응 현황 공유"),
            "share_status",
        )
        self.assertEqual(
            detect_status_work_action("재고 관리 현황 업데이트"),
            "update_status",
        )
        self.assertIsNone(detect_status_work_action("점검 결과 현황 공유"))
        self.assertIsNone(detect_status_work_action("보험 가입현황 제출"))


if __name__ == "__main__":
    unittest.main()
