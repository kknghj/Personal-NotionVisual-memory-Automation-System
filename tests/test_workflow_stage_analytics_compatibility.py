"""Phase 2: workflow_stage analytics compatibility (flat, nested, mixed, absent)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.feedback_event import build_ambiguity_scoring_event, normalize_feedback_event
from tools.analyze_workflow_stage_observations import analyze
from tools.export_feedback_observations_from_scoring_log import export_from_scoring_log


def _sample_flat_row() -> dict:
    return {
        "title": "주간 추진현황 보고",
        "top_candidate": "document_reporting",
        "inferred_workflow_stage": "progress",
        "workflow_stage_confidence": 0.85,
        "workflow_stage_source": "keyword:추진현황",
        "workflow_stage_ambiguous": False,
        "workflow_stage_mismatch": False,
        "inferred_workflow_stages_all": ["progress"],
    }


def _sample_nested_event() -> dict:
    return {
        "event_type": "ambiguity_scoring",
        "recorded_at": "2026-05-29T12:00:00Z",
        "title": "교육결과 보고",
        "recommended_candidate_id": "result_reporting",
        "observations": {
            "workflow_stage": {
                "inferred_workflow_stage": "result",
                "workflow_stage_confidence": 0.9,
                "workflow_stage_source": "keyword:교육결과",
                "workflow_stage_ambiguous": False,
                "workflow_stage_mismatch": True,
                "inferred_workflow_stages_all": ["result"],
            }
        },
    }


class WorkflowStageAnalyticsCompatibilityTests(unittest.TestCase):
    def test_flat_only_event_analytics(self) -> None:
        summary = analyze([_sample_flat_row()])
        self.assertEqual(summary["stage_observation_rows"], 1)
        self.assertEqual(summary["reporting_subset_rows"], 1)
        self.assertEqual(summary["ambiguous_stage_count"], 0)
        self.assertEqual(summary["stage_mismatch_count"], 0)
        matrix = summary["workflow_stage_confusion_matrix"]
        self.assertEqual(matrix.get("inferred=progress -> top=document_reporting"), 1)

    def test_nested_only_event_analytics(self) -> None:
        summary = analyze([_sample_nested_event()])
        self.assertEqual(summary["stage_observation_rows"], 1)
        self.assertEqual(summary["reporting_subset_rows"], 1)
        self.assertEqual(summary["stage_mismatch_count"], 1)
        matrix = summary["workflow_stage_confusion_matrix"]
        self.assertEqual(matrix.get("inferred=result -> top=result_reporting"), 1)

    def test_mixed_dataset_analytics(self) -> None:
        summary = analyze([_sample_flat_row(), _sample_nested_event()])
        self.assertEqual(summary["stage_observation_rows"], 2)
        self.assertEqual(summary["reporting_subset_rows"], 2)
        self.assertEqual(summary["stage_mismatch_count"], 1)

    def test_no_workflow_stage_event_skipped(self) -> None:
        no_stage = build_ambiguity_scoring_event(
            recorded_at="2026-05-29T12:00:00Z",
            title="일반 메일 발송",
            recommended_candidate_id="mail_distribution",
        )
        summary = analyze([no_stage, _sample_flat_row()])
        self.assertEqual(summary["total_rows"], 2)
        self.assertEqual(summary["stage_observation_rows"], 1)

    def test_flat_and_nested_produce_equivalent_analytics_for_same_values(self) -> None:
        flat = _sample_flat_row()
        nested = {
            "event_type": "ambiguity_scoring",
            "recorded_at": "2026-05-29T12:00:00Z",
            "title": flat["title"],
            "recommended_candidate_id": flat["top_candidate"],
            "observations": {
                "workflow_stage": {
                    key: flat[key]
                    for key in (
                        "inferred_workflow_stage",
                        "workflow_stage_confidence",
                        "workflow_stage_source",
                        "workflow_stage_ambiguous",
                        "workflow_stage_mismatch",
                        "inferred_workflow_stages_all",
                    )
                }
            },
        }
        flat_summary = analyze([flat])
        nested_summary = analyze([nested])
        for key in (
            "stage_observation_rows",
            "reporting_subset_rows",
            "ambiguous_stage_count",
            "stage_mismatch_count",
            "workflow_stage_confusion_matrix",
        ):
            self.assertEqual(flat_summary[key], nested_summary[key], msg=key)

    def test_normalize_bridges_flat_to_observations_slice(self) -> None:
        event = {"inferred_workflow_stage": "progress", "workflow_stage_ambiguous": False}
        normalized = normalize_feedback_event(event)
        workflow_stage = normalized.get("observations", {}).get("workflow_stage", {})
        self.assertEqual(workflow_stage.get("inferred_workflow_stage"), "progress")

    def test_export_accepts_nested_scoring_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "log.json"
            log_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "중간보고 자료",
                            "top_candidate": "document_reporting",
                            "observations": {
                                "workflow_stage": {
                                    "inferred_workflow_stage": "interim",
                                    "workflow_stage_ambiguous": False,
                                }
                            },
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            entries = export_from_scoring_log(log_path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["inferred_workflow_stage"], "interim")


if __name__ == "__main__":
    unittest.main()
