"""Tests for P5-B Feedback Statistics Analyzer."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.analyze_feedback_overrides import (
    DEFAULT_INPUT,
    LABELING_CSV_COLUMNS,
    analyze,
    enrich_example,
    export_labeling_csv,
    export_labeling_markdown,
    format_markdown_report,
    load_examples,
    recheck_current_engine,
    _labeling_rows_for_export,
    _resolve_current_engine_for_title,
)

ROOT = Path(__file__).resolve().parents[1]

FIXTURE_CATALOG = {
    "meta": {},
    "mail_action": {
        "visual": {"type": "emoji", "value": "📧"},
        "workflow_priority": 1,
        "meaning": [{"text": "메일", "workflow_resolution": 3, "interface_dominance": 1}],
        "semantic_metadata": {"workflow_fit": ["communication"]},
    },
    "document_edit": {
        "visual": {"type": "emoji", "value": "📄"},
        "workflow_priority": 2,
        "meaning": [{"text": "공문", "workflow_resolution": 2, "interface_dominance": 0}],
        "semantic_metadata": {"workflow_fit": ["document_workflow"]},
    },
    "hr_consultation": {
        "visual": {"type": "emoji", "value": "👥"},
        "workflow_priority": 2,
        "meaning": [{"text": "인사", "workflow_resolution": 2, "interface_dominance": 0}],
        "semantic_metadata": {"workflow_fit": ["hr_ops"]},
    },
}

FIXTURE_EXAMPLES = [
    {
        "id": 1,
        "title": "자치구 담당자 공문 안내 협조 요청",
        "recommended_visual": "📄",
        "final_visual": "📧",
        "confidence": 60,
        "note": "공문을 전파해줄 것을 메일로 요청하는 것이 실제 행위임",
        "source": "fixture",
    },
    {
        "id": 2,
        "title": "인사 상담",
        "recommended_visual": "없음",
        "final_visual": "👥",
        "confidence": 90,
        "note": "상사랑 둘이서 인사 관련 상담하는 것이 실제 행위",
        "source": "fixture",
    },
    {
        "id": 3,
        "title": "식생활교육 민원 답변",
        "recommended_visual": "없음",
        "final_visual": "📞 or 📝 or 💻",
        "confidence": 40,
        "note": "민원이 전화일 수 있고, 문서 작성일 수 있고, 행정 내부 시스템을 통한 처리일 수 있음",
        "source": "fixture",
    },
    {
        "id": 4,
        "title": "식생활교육 민원 전화 답변",
        "recommended_visual": "📞",
        "final_visual": "📞",
        "confidence": 100,
        "note": "",
        "source": "fixture",
    },
    {
        "id": 5,
        "title": "교육청 회의 오찬 장소 정하기",
        "recommended_visual": "🤝",
        "final_visual": "🍴",
        "confidence": 90,
        "note": "회의는 맥락이고 실제 행동은 오찬 장소 선정",
        "source": "fixture",
        "workflow": "meal_planning",
    },
]


def _write_fixture(path: Path) -> None:
    path.write_text(json.dumps(FIXTURE_EXAMPLES, ensure_ascii=False, indent=2), encoding="utf-8")


class AnalyzeFeedbackOverridesTests(unittest.TestCase):
    def test_load_override_examples_json(self) -> None:
        path = ROOT / DEFAULT_INPUT
        self.assertTrue(path.is_file())
        examples = load_examples(path)
        self.assertGreater(len(examples), 0)
        first = examples[0]
        self.assertIn(first.status, {"accepted", "override"})
        self.assertIn("taxonomy_category", first.to_dict())

    def test_overall_counts_with_fixture(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        summary = analyze(examples, top_n=5)
        overall = summary["overall"]
        self.assertEqual(overall["total_examples"], 5)
        self.assertEqual(overall["accepted_count"], 1)
        self.assertEqual(overall["override_count"], 4)
        self.assertGreaterEqual(overall["no_candidate_count"], 2)

    def test_taxonomy_distribution_computed(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        summary = analyze(examples, top_n=5)
        taxonomy = {row["key"]: row["count"] for row in summary["taxonomy_distribution"]}
        self.assertGreater(sum(taxonomy.values()), 0)
        self.assertIn("no_candidate", taxonomy)

    def test_missing_fields_do_not_crash(self) -> None:
        sparse = [
            {"title": "제목만 있음"},
            {"title": "override only", "recommended_visual": "📄", "final_visual": "📧"},
        ]
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in sparse]
        summary = analyze(examples, top_n=3)
        self.assertEqual(summary["overall"]["total_examples"], 2)

    def test_markdown_contains_main_sections(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        report = format_markdown_report(analyze(examples, top_n=3))
        for heading in (
            "# P5-B Feedback Statistics Summary",
            "## 1. Overall",
            "## 2. Override Taxonomy Distribution",
            "## 3. Workflow Override Ranking",
            "## 4. Visual Transition Ranking",
            "## 5. Ambiguity / Gap Type Summary",
            "## 6. Suggested Next Review Targets",
        ):
            self.assertIn(heading, report)

    def test_json_output_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            _write_fixture(fixture_path)
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/analyze_feedback_overrides.py"),
                    "--input",
                    str(fixture_path),
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertIn("overall", payload)
            self.assertIn("taxonomy_distribution", payload)
            self.assertIn("workflow_distribution", payload)
            self.assertIn("visual_transitions", payload)
            self.assertIn("gap_type_distribution", payload)
            self.assertIn("suggested_review_targets", payload)

    def test_visual_transitions_when_present(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        summary = analyze(examples, top_n=5)
        transitions = summary["visual_transitions"]
        keys = {row["key"] for row in transitions}
        self.assertTrue(any("📄" in key and "📧" in key for key in keys))

    def test_workflow_distribution_when_field_present(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        summary = analyze(examples, top_n=5)
        workflows = summary["workflow_distribution"]
        self.assertTrue(any(row["override_count"] > 0 for row in workflows))

    def test_cli_default_input(self) -> None:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/analyze_feedback_overrides.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            check=True,
        )
        self.assertIn("# P5-B Feedback Statistics Summary", result.stdout)
        self.assertIn("Total examples:", result.stdout)

    def test_export_labeling_md_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            out_path = Path(tmp) / "labeling.md"
            _write_fixture(fixture_path)
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/analyze_feedback_overrides.py"),
                    "--input",
                    str(fixture_path),
                    "--export-labeling-md",
                    str(out_path),
                ],
                cwd=ROOT,
                check=True,
                env=env,
            )
            self.assertTrue(out_path.is_file())
            content = out_path.read_text(encoding="utf-8")
            self.assertIn("# P5-B Override Manual Labeling Sheet", content)
            self.assertIn("source_type_manual", content)
            self.assertIn("자치구 담당자 공문 안내 협조 요청", content)

    def test_export_labeling_csv_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            out_path = Path(tmp) / "labeling.csv"
            _write_fixture(fixture_path)
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/analyze_feedback_overrides.py"),
                    "--input",
                    str(fixture_path),
                    "--export-labeling-csv",
                    str(out_path),
                ],
                cwd=ROOT,
                check=True,
                env=env,
            )
            self.assertTrue(out_path.is_file())
            with out_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertGreater(len(rows), 0)
            for col in LABELING_CSV_COLUMNS:
                self.assertIn(col, rows[0])

    def test_export_manual_columns_are_empty(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "labeling.csv"
            export_labeling_csv(examples, csv_path)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                self.assertEqual(row["source_type_manual"], "")
                self.assertEqual(row["cause_type_manual"], "")
                self.assertEqual(row["action_hint_manual"], "")
                self.assertEqual(row["generalizable_manual"], "")

            md_path = Path(tmp) / "labeling.md"
            export_labeling_markdown(examples, md_path)
            for line in md_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("|") and "자치구" in line:
                    cells = [cell.strip() for cell in line.split("|")[1:-1]]
                    self.assertEqual(cells[6], "")
                    self.assertEqual(cells[7], "")
                    self.assertEqual(cells[8], "")
                    self.assertEqual(cells[9], "")

    def test_export_with_recheck_includes_engine_csv_columns(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        recheck = recheck_current_engine(examples, catalog=FIXTURE_CATALOG, sample_cases=[])
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "labeling.csv"
            export_labeling_csv(examples, csv_path, recheck=recheck)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertGreater(len(rows), 0)
            for col in (
                "current_engine_visual",
                "current_engine_candidate_id",
                "current_engine_workflow",
                "resolved_by_current_engine",
                "active_gap",
                "still_no_candidate",
                "engine_error",
            ):
                self.assertIn(col, rows[0])

    def test_export_with_recheck_md_has_sections(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        recheck = recheck_current_engine(examples, catalog=FIXTURE_CATALOG, sample_cases=[])
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "labeling.md"
            export_labeling_markdown(examples, md_path, recheck=recheck)
            content = md_path.read_text(encoding="utf-8")
            self.assertIn("## Active Gaps for Manual Labeling", content)
            self.assertIn("## Still No Candidate", content)
            self.assertIn("## Engine Error / Needs Review", content)
            self.assertIn("current_engine_visual", content)

    def test_only_active_gaps_excludes_resolved_stale(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        recheck = recheck_current_engine(examples, catalog=FIXTURE_CATALOG, sample_cases=[])
        for ex in recheck["current_engine_examples"]:
            if ex.get("id") == 1:
                ex["resolved_by_current_engine"] = True
                ex["active_gap"] = False
                ex["still_no_candidate"] = False
                ex["engine_error"] = False
        all_rows = _labeling_rows_for_export(examples, recheck, only_active_gaps=False)
        filtered = _labeling_rows_for_export(examples, recheck, only_active_gaps=True)
        self.assertIn(1, {row["id"] for row in all_rows})
        self.assertNotIn(1, {row["id"] for row in filtered})
        for row in filtered:
            self.assertNotEqual(row["resolved_by_current_engine"], "true")

    def test_only_active_gaps_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            md_path = Path(tmp) / "active.md"
            csv_path = Path(tmp) / "active.csv"
            _write_fixture(fixture_path)
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/analyze_feedback_overrides.py"),
                    "--input",
                    str(fixture_path),
                    "--check-current-engine",
                    "--only-active-gaps",
                    "--export-labeling-md",
                    str(md_path),
                    "--export-labeling-csv",
                    str(csv_path),
                ],
                cwd=ROOT,
                check=True,
                env=env,
            )
            content = md_path.read_text(encoding="utf-8")
            self.assertIn("## Active Gaps for Manual Labeling", content)
            self.assertNotIn("## Resolved (Stale — Skip Labeling)", content)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                self.assertNotEqual(row["resolved_by_current_engine"], "true")

    def test_only_active_gaps_requires_check_current_engine(self) -> None:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/analyze_feedback_overrides.py"),
                "--only-active-gaps",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--only-active-gaps requires --check-current-engine", result.stderr)

    def test_original_override_examples_not_modified_by_export(self) -> None:
        path = ROOT / DEFAULT_INPUT
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/analyze_feedback_overrides.py"),
                    "--export-labeling-md",
                    str(Path(tmp) / "labeling.md"),
                    "--export-labeling-csv",
                    str(Path(tmp) / "labeling.csv"),
                    "--check-current-engine",
                ],
                cwd=ROOT,
                check=True,
                env=env,
            )
        after = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_check_current_engine_does_not_fail(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        result = recheck_current_engine(examples, catalog=FIXTURE_CATALOG, sample_cases=[])
        self.assertIn("current_engine_recheck", result)
        self.assertIn("current_engine_examples", result)
        self.assertEqual(len(result["current_engine_examples"]), 5)

    def test_check_current_engine_json_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            _write_fixture(fixture_path)
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools/analyze_feedback_overrides.py"),
                    "--input",
                    str(fixture_path),
                    "--check-current-engine",
                    "--json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertIn("current_engine_recheck", payload)
            self.assertIn("current_engine_examples", payload)

    def test_check_current_engine_markdown_section(self) -> None:
        examples = [enrich_example(row, FIXTURE_CATALOG) for row in FIXTURE_EXAMPLES]
        summary = analyze(examples, top_n=3)
        summary.update(recheck_current_engine(examples, catalog=FIXTURE_CATALOG, sample_cases=[]))
        report = format_markdown_report(summary)
        self.assertIn("## Current Engine Recheck", report)
        self.assertIn("## Active Gap Top Examples", report)

    def test_engine_error_does_not_abort_recheck(self) -> None:
        catalog = {
            "meta": {},
            "broken": {
                "visual": {"type": "emoji", "value": "📄"},
                "workflow_priority": 1,
                "meaning": [{"text": "테스트", "workflow_resolution": 1, "interface_dominance": 0}],
            },
        }
        examples = [
            enrich_example(
                {
                    "id": 99,
                    "title": "boom",
                    "recommended_visual": "📄",
                    "final_visual": "📧",
                },
                catalog,
            )
        ]

        def _boom(_title: str, _catalog: dict, _cases: list) -> dict:
            return {
                "current_engine_candidate_id": None,
                "current_engine_visual": None,
                "current_engine_workflow": None,
                "matches_final_visual": False,
                "matches_final_candidate_id": False,
                "resolved_by_current_engine": False,
                "active_gap": False,
                "still_no_candidate": False,
                "partial_match": False,
                "engine_error": True,
                "engine_error_message": "simulated failure",
            }

        with mock.patch(
            "tools.analyze_feedback_overrides._resolve_current_engine_for_title",
            side_effect=_boom,
        ):
            result = recheck_current_engine(examples, catalog=catalog, sample_cases=[])
        self.assertEqual(result["current_engine_recheck"]["engine_errors"], 1)
        self.assertTrue(result["current_engine_examples"][0]["engine_error"])

    def test_resolve_current_engine_handles_missing_title(self) -> None:
        engine = _resolve_current_engine_for_title("", FIXTURE_CATALOG, [])
        self.assertFalse(engine["engine_error"])


if __name__ == "__main__":
    unittest.main()
