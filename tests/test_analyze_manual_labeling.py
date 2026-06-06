"""Tests for P5-B Manual Labeling Aggregator."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze_manual_labeling import (
    REQUIRED_COLUMNS,
    analyze,
    analyze_to_json,
    export_boundary_backlog,
    export_candidate_backlog,
    export_metadata_backlog,
    format_summary_markdown,
    load_labeling_csv,
)

FIXTURE_ROWS = [
    {
        "id": "1",
        "title": "교육청 회의 오찬 장소 정하기",
        "recommended_visual": "🤝",
        "final_visual": "🍴",
        "current_taxonomy": "workflow_mismatch",
        "inferred_gap_type": "inferred_workflow_boundary",
        "current_engine_visual": "🤝",
        "current_engine_candidate_id": "meeting",
        "current_engine_workflow": "meeting",
        "resolved_by_current_engine": "false",
        "active_gap": "true",
        "still_no_candidate": "false",
        "source_type_manual": "boundary_ambiguity",
        "cause_type_manual": "context_vs_action",
        "action_hint_manual": "adjust_boundary",
        "generalizable_manual": "yes",
        "note": "회의는 맥락이고 실제 행동은 오찬 장소 선정",
    },
    {
        "id": "54",
        "title": "제주도 비행기 예매",
        "recommended_visual": "없음",
        "final_visual": "✈️",
        "current_taxonomy": "no_candidate",
        "inferred_gap_type": "inferred_no_candidate",
        "current_engine_visual": "",
        "current_engine_candidate_id": "",
        "current_engine_workflow": "",
        "resolved_by_current_engine": "false",
        "active_gap": "true",
        "still_no_candidate": "true",
        "source_type_manual": "no_candidate",
        "cause_type_manual": "catalog_gap",
        "action_hint_manual": "add_candidate",
        "generalizable_manual": "yes",
        "note": "비행기 혹은 티켓을 연상하는 이모지 사용함",
    },
    {
        "id": "63",
        "title": "과장 주재 주간회의 참석",
        "recommended_visual": "🤝",
        "final_visual": "people meeting",
        "current_taxonomy": "action_vs_object",
        "inferred_gap_type": "inferred_no_candidate",
        "current_engine_visual": "🤝",
        "current_engine_candidate_id": "meeting",
        "current_engine_workflow": "meeting",
        "resolved_by_current_engine": "false",
        "active_gap": "true",
        "still_no_candidate": "false",
        "source_type_manual": "visual_mismatch",
        "cause_type_manual": "visual_wrong_recall",
        "action_hint_manual": "update_metadata",
        "generalizable_manual": "yes",
        "note": "내부 회의는 people meeting 선호",
    },
    {
        "id": "4",
        "title": "지피터스 AI 스터디 신청",
        "recommended_visual": "🧑‍🏫",
        "final_visual": "robot (orange)",
        "current_taxonomy": "personal_preference",
        "inferred_gap_type": "inferred_no_candidate",
        "current_engine_visual": "🧑‍🏫",
        "current_engine_candidate_id": "training_session_attendance",
        "current_engine_workflow": "training_session_attendance",
        "resolved_by_current_engine": "false",
        "active_gap": "true",
        "still_no_candidate": "false",
        "source_type_manual": "personal_preference",
        "cause_type_manual": "personal_association",
        "action_hint_manual": "keep_as_preference",
        "generalizable_manual": "no",
        "note": "회사 대표 색 orange",
    },
    {
        "id": "99",
        "title": "미라벨링 케이스",
        "recommended_visual": "📄",
        "final_visual": "📄",
        "current_taxonomy": "action_vs_object",
        "inferred_gap_type": "inferred_no_candidate",
        "current_engine_visual": "📄",
        "current_engine_candidate_id": "document",
        "current_engine_workflow": "document",
        "resolved_by_current_engine": "false",
        "active_gap": "true",
        "still_no_candidate": "false",
        "source_type_manual": "",
        "cause_type_manual": "",
        "action_hint_manual": "",
        "generalizable_manual": "",
        "note": "manual labels missing",
    },
    {
        "id": "108",
        "title": "세종 출장 KTX 예매",
        "recommended_visual": "없음",
        "final_visual": "🚄",
        "current_taxonomy": "no_candidate",
        "inferred_gap_type": "inferred_no_candidate",
        "current_engine_visual": "",
        "current_engine_candidate_id": "",
        "current_engine_workflow": "",
        "resolved_by_current_engine": "false",
        "active_gap": "true",
        "still_no_candidate": "true",
        "source_type_manual": "inferred_no_candidate",
        "cause_type_manual": "catalog_gap",
        "action_hint_manual": "add_candidate",
        "generalizable_manual": "yes",
        "note": "unknown source type value",
    },
]


def write_fixture_csv(path: Path, rows: list[dict[str, str]] | None = None) -> None:
    rows = rows if rows is not None else FIXTURE_ROWS
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in REQUIRED_COLUMNS})


class TestAnalyzeManualLabeling(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture_path = Path(self.temp_dir.name) / "labeling.csv"
        write_fixture_csv(self.fixture_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_load_csv(self) -> None:
        rows = load_labeling_csv(self.fixture_path)
        self.assertEqual(len(rows), len(FIXTURE_ROWS))
        self.assertEqual(rows[0].title, "교육청 회의 오찬 장소 정하기")

    def test_missing_manual_rows(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        self.assertEqual(result.overall["missing_manual_rows"], 1)
        self.assertEqual(result.overall["completed_manual_rows"], len(FIXTURE_ROWS) - 1)

    def test_distributions(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        self.assertIn("boundary_ambiguity", result.distributions["source_type_manual"])
        self.assertIn("add_candidate", result.distributions["action_hint_manual"])
        self.assertIn("yes", result.distributions["generalizable_manual"])

    def test_action_buckets(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        self.assertEqual(len(result.buckets["add_candidate"]), 2)
        self.assertEqual(len(result.buckets["update_metadata"]), 1)
        self.assertEqual(len(result.buckets["adjust_boundary"]), 1)
        self.assertGreaterEqual(len(result.buckets["defer"]), 1)

    def test_priority_score(self) -> None:
        rows = load_labeling_csv(self.fixture_path)
        travel = next(row for row in rows if row.id == "54")
        self.assertGreaterEqual(travel.priority_score(), 7)
        self.assertEqual(travel.priority_label(), "high")

    def test_summary_markdown_export(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        md = format_summary_markdown(result)
        self.assertIn("# P5-B Manual Labeling Summary", md)
        self.assertIn("## 8. Recommended Next 3~5 Fixes", md)

    def test_candidate_backlog_export(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        md = export_candidate_backlog(result)
        self.assertIn("# P5-B Candidate Backlog", md)
        self.assertIn("제주도 비행기 예매", md)

    def test_metadata_backlog_export(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        md = export_metadata_backlog(result)
        self.assertIn("# P5-B Metadata Backlog", md)
        self.assertIn("과장 주재 주간회의 참석", md)

    def test_boundary_backlog_export(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        md = export_boundary_backlog(result)
        self.assertIn("# P5-B Boundary Backlog", md)
        self.assertIn("오찬", md)

    def test_json_output_valid(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        payload = analyze_to_json(result)
        serialized = json.dumps(payload, ensure_ascii=False)
        parsed = json.loads(serialized)
        self.assertIn("overall", parsed)
        self.assertIn("action_buckets", parsed)

    def test_unknown_manual_values_reported(self) -> None:
        result = analyze(load_labeling_csv(self.fixture_path))
        self.assertIn("source_type_manual", result.unknown_manual_values)
        self.assertIn("inferred_no_candidate", result.unknown_manual_values["source_type_manual"])


if __name__ == "__main__":
    unittest.main()
