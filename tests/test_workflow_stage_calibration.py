"""Calibration tests for result+현황 compound and 진행 현황 confidence."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match
from app.semantic_scoring import infer_workflow_stage_detail, semantic_compatibility
from app.workflow_stage_observation import build_workflow_stage_observation


class ResultStatusCompoundTests(unittest.TestCase):
    COMPOUND_TITLES = (
        "사업 운영 결과 현황 보고",
        "성과 분석 결과 현황 보고",
        "교육 운영 결과 현황 정리",
        "점검 결과 현황 공유",
    )

    def test_compound_infers_result_mid_confidence(self) -> None:
        for title in self.COMPOUND_TITLES:
            with self.subTest(title=title):
                detail = infer_workflow_stage_detail(title)
                self.assertEqual(detail["inferred_workflow_stage"], "result")
                self.assertFalse(detail["workflow_stage_ambiguous"])
                self.assertGreaterEqual(detail["workflow_stage_confidence"], 0.6)
                self.assertLessEqual(detail["workflow_stage_confidence"], 0.75)
                self.assertTrue(
                    str(detail["workflow_stage_source"]).startswith("compound:결과+현황+")
                )

    def test_compound_does_not_fire_without_reporting_action(self) -> None:
        detail = infer_workflow_stage_detail("분기 운영 결과 현황")
        self.assertNotEqual(detail.get("workflow_stage_source"), "compound:결과+현황+보고")

    def test_hyeonhwang_alone_unchanged(self) -> None:
        for title in (
            "전국 식생활교육 현황 보고",
            "보험 가입현황 제출",
            "비상소집 응소자 현황 제출",
            "부서별 현황 자료 공유",
        ):
            with self.subTest(title=title):
                detail = infer_workflow_stage_detail(title)
                self.assertIsNone(detail["inferred_workflow_stage"])
                self.assertLessEqual(detail["workflow_stage_confidence"], 0.2)

    def test_compound_soft_boost_prefers_result_reporting(self) -> None:
        cands = load_visual_candidates()
        for title in self.COMPOUND_TITLES:
            with self.subTest(title=title):
                match = find_best_visual_candidate_match(title, cands)
                self.assertIsNotNone(match)
                self.assertEqual(match.candidate_id, "result_reporting")

    def test_compound_mismatch_resolved_for_business_result_title(self) -> None:
        obs = build_workflow_stage_observation(
            "사업 운영 결과 현황 보고",
            selected_candidate_id="result_reporting",
            selected_candidate_data={
                "semantic_metadata": {"workflow_stage": ["result", "final"]},
            },
        )
        self.assertEqual(obs["inferred_workflow_stage"], "result")
        self.assertFalse(obs["workflow_stage_mismatch"])

    def test_result_reporting_gets_compound_semantic_bonus(self) -> None:
        score, reasons, fields = semantic_compatibility(
            "성과 분석 결과 현황 보고",
            {"workflow_stage": ["result", "final"], "workflow_fit": ["document"]},
        )
        self.assertGreaterEqual(score, 3)
        self.assertTrue(any("soft boost" in reason for reason in reasons))
        self.assertIn("workflow_stage", fields)


class ProgressStatusConfidenceTests(unittest.TestCase):
    def test_spaced_progress_status_lowers_confidence(self) -> None:
        for title in (
            "프로젝트 진행 현황 정리",
            "계약 협상 진행 현황 보고",
            "시스템 개발 진행 현황 보고",
        ):
            with self.subTest(title=title):
                detail = infer_workflow_stage_detail(title)
                self.assertEqual(detail["inferred_workflow_stage"], "progress")
                self.assertGreaterEqual(detail["workflow_stage_confidence"], 0.45)
                self.assertLessEqual(detail["workflow_stage_confidence"], 0.65)
                self.assertFalse(detail["workflow_stage_ambiguous"])

    def test_chusin_hyeonhwang_without_space_moderate_confidence(self) -> None:
        detail = infer_workflow_stage_detail("주요사업 추진현황 주간회의 자료 작성")
        self.assertEqual(detail["inferred_workflow_stage"], "progress")
        self.assertEqual(detail["workflow_stage_confidence"], 0.55)
        self.assertEqual(detail["workflow_stage_source"], "contextual:추진현황")

    def test_jinhaeng_sanghwang_strong_progress(self) -> None:
        detail = infer_workflow_stage_detail("진행상황 보고")
        self.assertEqual(detail["inferred_workflow_stage"], "progress")
        self.assertEqual(detail["workflow_stage_confidence"], 0.85)
        self.assertEqual(detail["workflow_stage_source"], "keyword:진행상황")


if __name__ == "__main__":
    unittest.main()
