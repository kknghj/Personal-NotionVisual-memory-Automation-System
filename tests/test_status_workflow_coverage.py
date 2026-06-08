"""Status workflow (현황 정리/공유/업데이트) coverage and boundary guard tests.

Case notes (competing candidates — not enforced here):
- ``분기별 예산 집행 현황 정리``: spreadsheet_work may compete with status_summary.
- ``주요사업 추진현황 주간회의 자료 작성``: document_edit may compete with status_summary.
- ``부서별 현황 자료 공유``: document_sharing may compete with status_sharing.
- Channel hints (메일/카톡/메신저): see ``tests/test_status_channel_boundaries.py``.
- Formal document writing (보고서/공고문/…): see ``tests/test_status_document_edit_boundaries.py``.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_sample_cases, load_visual_candidates
from app.recommender import find_best_visual_candidate_match, find_exact_title_match
from app.semantic_scoring import infer_workflow_stage_detail


class StatusWorkflowSemanticTests(unittest.TestCase):
    """Primary status_summary / status_sharing / status_update semantic routing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_status_summary_core_titles(self) -> None:
        for title in (
            "프로젝트 진행 현황 정리",
            "부서별 업무 추진 현황 정리",
            "클레임 처리 진행 현황 정리",
            "협력업체 계약 진행 현황 정리",
            "민원 처리 현황 내부자료 작성",
        ):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "status_summary")

    def test_status_sharing_core_titles(self) -> None:
        for title in (
            "서버 장애 대응 현황 공유",
            "위험 요소 대응 현황 공유",
            "콘텐츠 제작 현황 공유",
            "신규 서비스 테스트 현황 공유",
            "고객 문의 대응 현황 공유",
        ):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "status_sharing")

    def test_status_update_core_titles(self) -> None:
        for title in (
            "재고 관리 현황 업데이트",
            "고객 문의 처리 현황 업데이트",
            "시스템 개발 진행 현황 업데이트",
            "신청 접수 현황 업데이트",
            "장비 점검 현황 업데이트",
            "교육 신청 현황 업데이트",
            "프로젝트 이슈 대응 현황 업데이트",
        ):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "status_update")

    def test_status_sharing_visual_is_paper_airplane_blue(self) -> None:
        data = self._cands["status_sharing"]
        visual = data["visual"]
        self.assertEqual(visual["type"], "notion_icon")
        self.assertEqual(visual["value"], "paper airplane")
        self.assertEqual(visual["color"], "blue")

    def test_status_update_visual_is_refresh_emoji(self) -> None:
        visual = self._cands["status_update"]["visual"]
        self.assertEqual(visual["type"], "emoji")
        self.assertEqual(visual["value"], "🔄")


class StatusWorkflowBoundaryTests(unittest.TestCase):
    """Existing reporting/edit/sharing candidates must not be displaced by status_*."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_result_status_compound_stays_on_result_reporting(self) -> None:
        for title in (
            "점검 결과 현황 공유",
            "교육 운영 결과 현황 정리",
            "사업 운영 결과 현황 보고",
        ):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "result_reporting")

    def test_nationwide_status_report_stays_document_reporting(self) -> None:
        self.assertEqual(self._cid("전국 식생활교육 현황 보고"), "document_reporting")

    def test_nationwide_status_report_workflow_stage_stays_null(self) -> None:
        detail = infer_workflow_stage_detail("전국 식생활교육 현황 보고")
        self.assertIsNone(detail["inferred_workflow_stage"])
        self.assertLessEqual(detail["workflow_stage_confidence"], 0.2)

    def test_submission_titles_do_not_route_to_status_update(self) -> None:
        for title in ("보험 가입현황 제출", "비상소집 응소자 현황 제출"):
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, {"document_submission", "document_edit"})
                self.assertNotEqual(cid, "status_update")

    def test_department_status_share_not_result_reporting(self) -> None:
        cid = self._cid("부서별 현황 자료 공유")
        self.assertIn(cid, ("status_sharing", "document_sharing"))
        self.assertNotEqual(cid, "result_reporting")


class StatusWorkflowExactMatchTests(unittest.TestCase):
    """Runtime exact-match samples for 27 status-work titles in ``sample_cases.json``.

    Channel- and document-type boundary titles (e.g. ``… 메일 공유``, ``현황 보고서 작성``)
    are covered in ``test_status_channel_boundaries`` / ``test_status_document_edit_boundaries``
    only — not duplicated in ``sample_cases.json``.
    """

    EXPECTED_STATUS_TITLES: frozenset[str] = frozenset(
        {
            "프로젝트 진행 현황 정리",
            "부서별 업무 추진 현황 정리",
            "클레임 처리 진행 현황 정리",
            "주요사업 추진현황 주간회의 자료 작성",
            "분기별 예산 집행 현황 정리",
            "협력업체 계약 진행 현황 정리",
            "민원 처리 현황 내부자료 작성",
            "서버 장애 대응 현황 공유",
            "위험 요소 대응 현황 공유",
            "콘텐츠 제작 현황 공유",
            "부서별 현황 자료 공유",
            "신규 서비스 테스트 현황 공유",
            "고객 문의 대응 현황 공유",
            "행사 준비 현황 관계자 공유",
            "재고 관리 현황 업데이트",
            "고객 문의 처리 현황 업데이트",
            "시스템 개발 진행 현황 업데이트",
            "신청 접수 현황 업데이트",
            "장비 점검 현황 업데이트",
            "교육 신청 현황 업데이트",
            "프로젝트 이슈 대응 현황 업데이트",
            "점검 결과 현황 공유",
            "교육 운영 결과 현황 정리",
            "전국 식생활교육 현황 보고",
            "보험 가입현황 제출",
            "사업 운영 결과 현황 보고",
            "비상소집 응소자 현황 제출",
        }
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls._cases = load_sample_cases()
        cls._cands = load_visual_candidates()

    def test_all_status_workflow_titles_have_exact_match_rows(self) -> None:
        for title in sorted(self.EXPECTED_STATUS_TITLES):
            with self.subTest(title=title):
                hit = find_exact_title_match(title, self._cases)
                self.assertIsNotNone(hit)
                assert hit is not None
                self.assertIn("workflow_type", hit)

    def test_status_summary_exact_visual(self) -> None:
        match = find_best_visual_candidate_match("프로젝트 진행 현황 정리", self._cands)
        assert match is not None
        self.assertEqual(match.candidate_id, "status_summary")
        self.assertEqual(match.data["visual"]["value"], "📋")

    def test_status_sharing_exact_visual(self) -> None:
        hit = find_exact_title_match("서버 장애 대응 현황 공유", self._cases)
        assert hit is not None
        self.assertEqual(hit["visual"]["type"], "notion_icon")
        self.assertEqual(hit["visual"]["value"], "paper airplane")
        self.assertEqual(hit["visual"]["color"], "blue")

    def test_status_update_exact_visual(self) -> None:
        hit = find_exact_title_match("재고 관리 현황 업데이트", self._cases)
        assert hit is not None
        self.assertEqual(hit["visual"]["value"], "🔄")
        self.assertEqual(hit["workflow_type"], "status_update")


if __name__ == "__main__":
    unittest.main()
