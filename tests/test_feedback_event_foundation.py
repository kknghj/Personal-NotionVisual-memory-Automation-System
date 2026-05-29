"""Phase 1: feedback log loading, event validation/normalization, export shape."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.data_loader import append_feedback_log_entry, load_feedback_log
from app.feedback_event import (
    build_ambiguity_scoring_event,
    normalize_feedback_event,
    validate_feedback_event,
)
from tools.export_feedback_observations_from_scoring_log import (
    _scoring_row_to_feedback_entry,
)


class FeedbackLogLoadingTests(unittest.TestCase):
    def test_missing_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback_log.json"
            with patch("app.data_loader.feedback_log_path", return_value=path):
                self.assertEqual(load_feedback_log(), [])

    def test_empty_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback_log.json"
            path.write_text("", encoding="utf-8")
            with patch("app.data_loader.feedback_log_path", return_value=path):
                self.assertEqual(load_feedback_log(), [])

    def test_whitespace_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback_log.json"
            path.write_text("  \n\t  ", encoding="utf-8")
            with patch("app.data_loader.feedback_log_path", return_value=path):
                self.assertEqual(load_feedback_log(), [])

    def test_valid_array_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback_log.json"
            path.write_text('[{"event_type": "x", "recorded_at": "t"}]', encoding="utf-8")
            with patch("app.data_loader.feedback_log_path", return_value=path):
                log = load_feedback_log()
            self.assertEqual(len(log), 1)
            self.assertEqual(log[0]["event_type"], "x")

    def test_invalid_json_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback_log.json"
            path.write_text("{not json", encoding="utf-8")
            with patch("app.data_loader.feedback_log_path", return_value=path):
                with self.assertRaises(ValueError) as ctx:
                    load_feedback_log()
            self.assertIn("invalid JSON", str(ctx.exception))

    def test_non_array_root_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback_log.json"
            path.write_text('{"events": []}', encoding="utf-8")
            with patch("app.data_loader.feedback_log_path", return_value=path):
                with self.assertRaises(ValueError) as ctx:
                    load_feedback_log()
            self.assertIn("JSON array", str(ctx.exception))

    def test_append_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback_log.json"
            entry = build_ambiguity_scoring_event(
                recorded_at="2026-05-29T00:00:00Z",
                title="테스트 보고",
                recommended_candidate_id="document_reporting",
            )
            with patch("app.data_loader.feedback_log_path", return_value=path):
                append_feedback_log_entry(entry)
                log = load_feedback_log()
            self.assertEqual(len(log), 1)
            self.assertEqual(log[0]["title"], "테스트 보고")
            on_disk = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(on_disk, log)

    def test_append_rejects_invalid_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback_log.json"
            path.write_text("[]\n", encoding="utf-8")
            with patch("app.data_loader.feedback_log_path", return_value=path):
                with self.assertRaises(ValueError):
                    append_feedback_log_entry({"event_type": "ambiguity_scoring"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [])


class FeedbackEventValidationTests(unittest.TestCase):
    def test_valid_event(self) -> None:
        event = build_ambiguity_scoring_event(
            recorded_at="2026-05-29T00:00:00Z",
            title="보고",
        )
        validate_feedback_event(event)

    def test_missing_required_field(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_feedback_event({"event_type": "ambiguity_scoring"})
        self.assertIn("recorded_at", str(ctx.exception))

    def test_unknown_extra_field_allowed(self) -> None:
        event = build_ambiguity_scoring_event(
            recorded_at="2026-05-29T00:00:00Z",
            title="보고",
        )
        event["future_field"] = {"nested": True}
        validate_feedback_event(event)


class FeedbackEventNormalizationTests(unittest.TestCase):
    def test_flat_workflow_stage_copied_to_observations(self) -> None:
        event = {
            "event_type": "ambiguity_scoring",
            "recorded_at": "2026-05-29T00:00:00Z",
            "inferred_workflow_stage": "progress",
            "workflow_stage_ambiguous": False,
        }
        normalized = normalize_feedback_event(event)
        self.assertEqual(normalized["inferred_workflow_stage"], "progress")
        self.assertEqual(
            normalized["observations"]["workflow_stage"]["inferred_workflow_stage"],
            "progress",
        )


class ExportFeedbackObservationsTests(unittest.TestCase):
    def test_schema_version_and_source_surface(self) -> None:
        entry = _scoring_row_to_feedback_entry(
            {
                "title": "진행상황 보고",
                "top_candidate": "result_reporting",
                "inferred_workflow_stage": "progress",
            },
            "2026-05-29T12:00:00Z",
        )
        self.assertEqual(entry["schema_version"], 1)
        self.assertEqual(entry["source_surface"], "ambiguity_scoring_log")

    def test_workflow_stage_flat_fields_preserved(self) -> None:
        entry = _scoring_row_to_feedback_entry(
            {
                "title": "교육결과 보고",
                "top_candidate": "result_reporting",
                "inferred_workflow_stage": "result",
                "matched_workflow_stage": ["result", "final"],
                "workflow_stage_confidence": 0.85,
                "workflow_stage_source": "keyword:교육결과",
                "workflow_stage_ambiguous": False,
                "workflow_stage_mismatch": False,
                "inferred_workflow_stages_all": ["result"],
            },
            "2026-05-29T12:00:00Z",
        )
        self.assertEqual(entry["inferred_workflow_stage"], "result")
        self.assertEqual(entry["matched_workflow_stage"], ["result", "final"])
        self.assertEqual(entry["workflow_stage_confidence"], 0.85)
        self.assertEqual(entry["workflow_stage_source"], "keyword:교육결과")
        self.assertFalse(entry["workflow_stage_ambiguous"])
        self.assertFalse(entry["workflow_stage_mismatch"])
        self.assertEqual(entry["inferred_workflow_stages_all"], ["result"])
