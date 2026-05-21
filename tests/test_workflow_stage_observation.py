"""Tests for feedback_log workflow_stage observation builder."""

from __future__ import annotations

import unittest

from app.semantic_scoring import infer_workflow_stage_detail
from app.workflow_stage_observation import (
    attach_workflow_stage_to_log_entry,
    build_workflow_stage_observation,
    observation_is_relevant,
)


class InferWorkflowStageDetailTests(unittest.TestCase):
    def test_ambiguous_hyeonhwang(self) -> None:
        detail = infer_workflow_stage_detail("전국 식생활교육 현황 보고")
        self.assertIsNone(detail["inferred_workflow_stage"])
        self.assertEqual(detail["workflow_stage_source"], "ambiguous:현황")
        self.assertEqual(detail["workflow_stage_confidence"], 0.2)
        self.assertTrue(detail["workflow_stage_ambiguous"])

    def test_contextual_operating_status(self) -> None:
        detail = infer_workflow_stage_detail("기관 운영 현황 공유")
        self.assertIsNone(detail["inferred_workflow_stage"])
        self.assertEqual(detail["workflow_stage_source"], "contextual:운영현황")


class WorkflowStageObservationTests(unittest.TestCase):
    def test_mismatch_when_inferred_progress_top_result_reporting(self) -> None:
        obs = build_workflow_stage_observation(
            "진행상황 보고",
            selected_candidate_id="result_reporting",
            selected_candidate_data={
                "semantic_metadata": {"workflow_stage": ["result", "final"]},
            },
        )
        self.assertEqual(obs["inferred_workflow_stage"], "progress")
        self.assertTrue(obs["workflow_stage_mismatch"])
        self.assertEqual(obs["matched_workflow_stage"], ["result", "final"])

    def test_user_confirmed_used_for_mismatch(self) -> None:
        obs = build_workflow_stage_observation(
            "전국 식생활교육 현황 보고",
            selected_candidate_id="document_reporting",
            selected_candidate_data={
                "semantic_metadata": {"workflow_stage": ["progress", "interim"]},
            },
            user_confirmed_workflow_stage="result",
        )
        self.assertIsNone(obs["inferred_workflow_stage"])
        self.assertEqual(obs["user_confirmed_workflow_stage"], "result")
        self.assertTrue(obs["workflow_stage_mismatch"])

    def test_irrelevant_title_skips_attachment(self) -> None:
        entry = {"title": "엑셀 자료 정리", "top_candidate": "spreadsheet_work", "rankings": []}
        out = attach_workflow_stage_to_log_entry(entry, {})
        self.assertNotIn("inferred_workflow_stage", out)

    def test_relevant_reporting_title_attaches_fields(self) -> None:
        entry = {
            "title": "교육결과 보고",
            "top_candidate": "result_reporting",
            "rankings": [{"candidate": "result_reporting"}],
        }
        cands = {
            "result_reporting": {
                "semantic_metadata": {"workflow_stage": ["result", "final"]},
            }
        }
        out = attach_workflow_stage_to_log_entry(entry, cands)
        self.assertEqual(out["inferred_workflow_stage"], "result")
        self.assertFalse(out["workflow_stage_mismatch"])

    def test_observation_is_relevant_for_hyeonhwang(self) -> None:
        self.assertTrue(observation_is_relevant("운영현황 전달"))


if __name__ == "__main__":
    unittest.main()
