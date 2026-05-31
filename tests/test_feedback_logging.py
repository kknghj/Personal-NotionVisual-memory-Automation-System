"""P4 user feedback / override observation log (JSONL) contract tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.feedback_logging import (
    FEEDBACK_TYPES,
    REQUIRED_LOG_FIELDS,
    append_feedback_log,
    build_feedback_log_entry,
    compute_accepted_system_recommendation,
    log_user_feedback,
)


class FeedbackLoggingTests(unittest.TestCase):
    """Observation log at data/feedback_log.jsonl must not alter recommendations."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmpdir.name) / "feedback_log.jsonl"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _read_lines(self) -> list[dict]:
        if not self.log_path.is_file():
            return []
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def test_feedback_log_appended_as_jsonl(self) -> None:
        log_user_feedback(
            "보고서 확인",
            feedback_type="accepted",
            recommendation_id="rec-001",
            system_recommended_visual={"type": "emoji", "value": "📄"},
            final_selected_visual={"type": "emoji", "value": "📄"},
            log_path=self.log_path,
        )
        log_user_feedback(
            "점심 카톡 확인",
            feedback_type="override",
            recommendation_id="rec-002",
            system_recommended_visual={"type": "emoji", "value": "💬"},
            final_selected_visual={"type": "emoji", "value": "📱"},
            log_path=self.log_path,
        )
        self.assertTrue(self.log_path.is_file())
        self.assertEqual(len(self._read_lines()), 2)

    def test_required_fields_present(self) -> None:
        log_user_feedback(
            "보고서 확인",
            feedback_type="accepted",
            recommendation_id="rec-abc",
            system_recommended_visual={"type": "emoji", "value": "📄"},
            final_selected_visual={"type": "emoji", "value": "📄"},
            log_path=self.log_path,
        )
        row = self._read_lines()[0]
        for field in REQUIRED_LOG_FIELDS:
            self.assertIn(field, row, msg=field)

    def test_recommendation_id_preserved(self) -> None:
        rec_id = "550e8400-e29b-41d4-a716-446655440000"
        log_user_feedback(
            "보고서 확인",
            feedback_type="accepted",
            recommendation_id=rec_id,
            system_recommended_visual={"type": "emoji", "value": "📄"},
            final_selected_visual={"type": "emoji", "value": "📄"},
            log_path=self.log_path,
        )
        self.assertEqual(self._read_lines()[0]["recommendation_id"], rec_id)

    def test_system_and_final_visuals_recorded_separately(self) -> None:
        log_user_feedback(
            "점심 카톡 확인",
            feedback_type="override",
            recommendation_id="rec-003",
            system_recommended_visual={"type": "emoji", "value": "💬", "color": "default"},
            final_selected_visual={"type": "emoji", "value": "📱"},
            override_reason="카톡 대신 휴대폰 아이콘 선호",
            log_path=self.log_path,
        )
        row = self._read_lines()[0]
        self.assertEqual(row["system_recommended_visual"], {"type": "emoji", "value": "💬", "color": "default"})
        self.assertEqual(row["final_selected_visual"], {"type": "emoji", "value": "📱"})
        self.assertNotEqual(row["system_recommended_visual"], row["final_selected_visual"])

    def test_accepted_system_recommendation_computed(self) -> None:
        cases = [
            ("accepted", {"type": "emoji", "value": "📄"}, {"type": "emoji", "value": "📄"}, True),
            ("override", {"type": "emoji", "value": "💬"}, {"type": "emoji", "value": "📱"}, False),
            ("manual_without_recommendation", None, {"type": "emoji", "value": "📄"}, False),
            ("no_candidate_selected", {"type": "emoji", "value": "📄"}, None, False),
        ]
        for feedback_type, system_vis, final_vis, expected in cases:
            with self.subTest(feedback_type=feedback_type):
                log_user_feedback(
                    "테스트 제목",
                    feedback_type=feedback_type,
                    recommendation_id="rec-x",
                    system_recommended_visual=system_vis,
                    final_selected_visual=final_vis,
                    log_path=self.log_path,
                )
                row = self._read_lines()[-1]
                self.assertEqual(row["accepted_system_recommendation"], expected)

    def test_feedback_type_recorded(self) -> None:
        for feedback_type in sorted(FEEDBACK_TYPES):
            with self.subTest(feedback_type=feedback_type):
                log_user_feedback(
                    "테스트",
                    feedback_type=feedback_type,
                    log_path=self.log_path,
                )
                self.assertEqual(self._read_lines()[-1]["feedback_type"], feedback_type)

    def test_optional_fields_omitted_safely(self) -> None:
        log_user_feedback(
            "수동 입력",
            feedback_type="manual_without_recommendation",
            final_selected_visual={"type": "emoji", "value": "📄"},
            log_path=self.log_path,
        )
        row = self._read_lines()[0]
        self.assertIsNone(row["recommendation_id"])
        self.assertIsNone(row["system_recommended_visual"])
        self.assertIsNone(row["override_reason"])
        self.assertIsNone(row["user_note"])
        self.assertFalse(row["accepted_system_recommendation"])

    def test_logging_failure_does_not_raise(self) -> None:
        with patch(
            "app.feedback_logging.append_feedback_log",
            side_effect=OSError("disk full"),
        ):
            ok = log_user_feedback(
                "보고서 확인",
                feedback_type="accepted",
                recommendation_id="rec-fail",
                log_path=self.log_path,
            )
        self.assertFalse(ok)

    def test_build_entry_rejects_unknown_feedback_type(self) -> None:
        with self.assertRaises(ValueError):
            build_feedback_log_entry("title", feedback_type="unknown_type")

    def test_append_creates_parent_directory(self) -> None:
        nested = Path(self._tmpdir.name) / "nested" / "feedback.jsonl"
        append_feedback_log(
            {"timestamp": "2026-01-01T00:00:00Z", "probe": True},
            log_path=nested,
        )
        self.assertTrue(nested.is_file())

    def test_compute_accepted_from_visuals_when_types_match(self) -> None:
        system = {"type": "emoji", "value": "📄"}
        self.assertTrue(
            compute_accepted_system_recommendation(
                "accepted",
                system_recommended_visual=system,
                final_selected_visual=system,
            )
        )
        self.assertFalse(
            compute_accepted_system_recommendation(
                "override",
                system_recommended_visual=system,
                final_selected_visual={"type": "emoji", "value": "📱"},
            )
        )


if __name__ == "__main__":
    unittest.main()
