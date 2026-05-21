"""Unit tests for workflow_stage title inference and semantic bonus."""

from __future__ import annotations

import unittest

from app.semantic_scoring import infer_title_workflow_stages, semantic_compatibility


class WorkflowStageInferenceTests(unittest.TestCase):
    def test_progress_and_result_phrases(self) -> None:
        self.assertEqual(
            infer_title_workflow_stages("식생활교육 신청 절차 개선 진행상황 보고"),
            {"progress"},
        )
        self.assertEqual(
            infer_title_workflow_stages("식생활교육 강사양성 현장 출장 결과 보고"),
            {"result"},
        )
        self.assertEqual(
            infer_title_workflow_stages("최종결과 보고"),
            {"final", "result"},
        )

    def test_ambiguous_hyeonhwang_alone_does_not_infer_stage(self) -> None:
        self.assertEqual(
            infer_title_workflow_stages("전국 식생활교육 현황 보고"),
            set(),
        )


class WorkflowStageSemanticBonusTests(unittest.TestCase):
    def test_stage_match_adds_bonus(self) -> None:
        score, reasons, fields = semantic_compatibility(
            "교육결과 보고",
            {"workflow_stage": ["result", "final"], "workflow_fit": ["document"]},
        )
        self.assertGreaterEqual(score, 2)
        self.assertTrue(any("workflow_stage" in reason for reason in reasons))
        self.assertIn("workflow_stage", fields)

    def test_mismatched_stage_does_not_remove_other_signals(self) -> None:
        score, _, fields = semantic_compatibility(
            "진행상황 보고",
            {
                "workflow_stage": ["result", "final"],
                "interaction_mode": "report_brief",
                "workflow_fit": ["document"],
            },
        )
        self.assertIn("interaction_mode", fields)
        self.assertNotIn("workflow_stage", fields)
        self.assertGreater(score, 0)


if __name__ == "__main__":
    unittest.main()
