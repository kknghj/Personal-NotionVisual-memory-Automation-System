"""Tests for P5-B live feedback analyzer (app/p5b_feedback_analyzer.py)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.p5b_feedback_analyzer import (
    DEFAULT_MARGIN_THRESHOLD,
    analyze_feedback_rows,
    analyze_logs,
    classify_accepted,
    classify_override,
    enrich_feedback_row,
    format_insights_report,
    format_statistics_report,
    load_recommendation_index,
)
from app.feedback_ranking_snapshot import infer_ranking_confidence


FIXTURE_RECOMMENDATION = {
    "stable_mail": {
        "recommendation_id": "stable-mail",
        "top_candidate": "mail_action",
        "candidates": [
            {"rank": 1, "candidate_id": "mail_action", "score": 0.84, "semantic_bonus": 8},
            {"rank": 2, "candidate_id": "phone_call", "score": 0.41, "semantic_bonus": 0},
        ],
        "ambiguity_gap": 0.43,
    },
    "unstable_folder": {
        "recommendation_id": "unstable-folder",
        "top_candidate": "folder",
        "candidates": [
            {"rank": 1, "candidate_id": "folder", "score": 0.761, "semantic_bonus": 0},
            {"rank": 2, "candidate_id": "taxi_service", "score": 0.76, "semantic_bonus": 0},
        ],
        "ambiguity_gap": 0.001,
    },
    "boundary_channel": {
        "recommendation_id": "boundary-channel",
        "top_candidate": "document_reporting",
        "candidates": [
            {"rank": 1, "candidate_id": "document_reporting", "score": 0.56, "semantic_bonus": 10},
            {"rank": 2, "candidate_id": "messenger_notice", "score": 0.54, "semantic_bonus": 8},
        ],
        "ambiguity_gap": 0.02,
    },
    "wrong_phone": {
        "recommendation_id": "wrong-phone",
        "top_candidate": "mail_action",
        "candidates": [
            {"rank": 1, "candidate_id": "mail_action", "score": 0.55, "semantic_bonus": 4},
            {"rank": 2, "candidate_id": "phone_call", "score": 0.52, "semantic_bonus": 0},
        ],
        "ambiguity_gap": 0.03,
    },
}


FIXTURE_FEEDBACK = [
    {
        "recommendation_id": "stable-mail",
        "input_title": "메일 송부",
        "system_recommended_visual": {"type": "emoji", "value": "📧"},
        "final_selected_visual": {"type": "emoji", "value": "📧"},
        "feedback_type": "accepted",
    },
    {
        "recommendation_id": "unstable-folder",
        "input_title": "재택 필요 자료 드라이브 이동",
        "system_recommended_visual": {"type": "emoji", "value": "📁"},
        "final_selected_visual": {"type": "emoji", "value": "📁"},
        "feedback_type": "accepted",
    },
    {
        "recommendation_id": "unstable-folder",
        "input_title": "재택 필요 자료 드라이브 이동",
        "system_recommended_visual": {"type": "emoji", "value": "📁"},
        "final_selected_visual": {"type": "emoji", "value": "📁"},
        "feedback_type": "override",
        "override_reason": "wrong_top_candidate",
        "user_note": "폴더 추천은 맞음. taxi_service와 score 차이 0.001",
    },
    {
        "recommendation_id": "boundary-channel",
        "input_title": "강사 활동 보고 제출시 유의사항 전달",
        "system_recommended_visual": {"type": "emoji", "value": "🗣️"},
        "final_selected_visual": {"type": "emoji", "value": "💬"},
        "feedback_type": "override",
        "override_reason": "channel_vs_object",
        "user_note": "보고가 아니라 메신저 전달",
    },
    {
        "recommendation_id": "wrong-phone",
        "input_title": "메일 미열람 담당자 전화",
        "system_recommended_visual": {"type": "emoji", "value": "📧"},
        "final_selected_visual": {"type": "emoji", "value": "📞"},
        "feedback_type": "override",
        "override_reason": "wrong_top_candidate",
        "user_note": "실제 행동은 전화",
    },
    {
        "recommendation_id": "missing-rec",
        "input_title": "교육자료 정리",
        "system_recommended_visual": None,
        "final_selected_visual": None,
        "feedback_type": "no_candidate_selected",
    },
]


class P5BFeedbackAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rec_index = {
            row["recommendation_id"]: row for row in FIXTURE_RECOMMENDATION.values()
        }

    def test_classify_accepted_stable_vs_unstable(self) -> None:
        stable = classify_accepted(
            FIXTURE_FEEDBACK[0],
            FIXTURE_RECOMMENDATION["stable_mail"],
        )
        unstable = classify_accepted(
            FIXTURE_FEEDBACK[1],
            FIXTURE_RECOMMENDATION["unstable_folder"],
        )
        self.assertEqual(stable, "stable_accept")
        self.assertEqual(unstable, "unstable_accept")

    def test_classify_override_taxonomy(self) -> None:
        self.assertEqual(
            classify_override(
                FIXTURE_FEEDBACK[2],
                FIXTURE_RECOMMENDATION["unstable_folder"],
            ),
            "ranking_instability",
        )
        self.assertEqual(
            classify_override(
                FIXTURE_FEEDBACK[3],
                FIXTURE_RECOMMENDATION["boundary_channel"],
            ),
            "boundary_disagreement",
        )
        self.assertEqual(
            classify_override(
                FIXTURE_FEEDBACK[4],
                FIXTURE_RECOMMENDATION["wrong_phone"],
            ),
            "wrong_recommendation",
        )

    def test_analyze_fixture_summary(self) -> None:
        rows = [
            enrich_feedback_row(entry, self.rec_index) for entry in FIXTURE_FEEDBACK
        ]
        summary = analyze_feedback_rows(rows)
        overall = summary["overall"]
        self.assertEqual(overall["total_logs"], 6)
        self.assertEqual(overall["accepted_count"], 2)
        self.assertEqual(overall["override_count"], 3)
        self.assertEqual(overall["no_candidate_count"], 1)
        self.assertEqual(summary["acceptance_metrics"]["stable_accept_count"], 1)
        self.assertEqual(summary["acceptance_metrics"]["unstable_accept_count"], 1)
        self.assertEqual(summary["override_metrics"]["ranking_instability"]["count"], 1)
        self.assertEqual(summary["override_metrics"]["wrong_recommendation"]["count"], 1)
        self.assertEqual(summary["override_metrics"]["boundary_disagreement"]["count"], 1)

    def test_ranking_metrics_percentiles(self) -> None:
        rows = [
            enrich_feedback_row(entry, self.rec_index) for entry in FIXTURE_FEEDBACK
        ]
        ranking = analyze_feedback_rows(rows)["ranking_metrics"]
        self.assertGreaterEqual(ranking["count_with_margin"], 4)
        self.assertLessEqual(ranking["minimum"], ranking["p50"])
        self.assertLessEqual(ranking["p50"], ranking["maximum"])

    def test_ambiguity_threshold_buckets(self) -> None:
        rows = [
            enrich_feedback_row(entry, self.rec_index) for entry in FIXTURE_FEEDBACK
        ]
        ambiguity = analyze_feedback_rows(rows)["ambiguity_metrics"]["thresholds"]
        self.assertGreaterEqual(ambiguity["0.01"]["count"], 1)
        self.assertIn("folder", ambiguity["0.03"]["by_workflow"])

    def test_boundary_discovery_detects_pairs(self) -> None:
        rows = [
            enrich_feedback_row(entry, self.rec_index) for entry in FIXTURE_FEEDBACK
        ]
        patterns = analyze_feedback_rows(rows)["boundary_discovery"]["pattern_counts"]
        self.assertTrue(
            any("folder vs taxi" in key or "interface_vs_semantic" in key for key in patterns)
        )

    def test_reports_contain_required_sections(self) -> None:
        rows = [
            enrich_feedback_row(entry, self.rec_index) for entry in FIXTURE_FEEDBACK
        ]
        summary = analyze_feedback_rows(rows)
        stats = format_statistics_report(summary)
        insights = format_insights_report(summary)
        for heading in (
            "## Executive Summary",
            "## Top Risk Workflows",
            "## Top Risk Visuals",
            "## Boundary Candidates",
            "## Recommended Next Actions",
        ):
            self.assertIn(heading, stats)
        for heading in (
            "## Taxonomy Sufficiency",
            "## Accepted Memo Feature",
            "## Feedback Schema Extensions",
        ):
            self.assertIn(heading, insights)

    def test_analyze_logs_from_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            feedback_path = tmp_path / "feedback.jsonl"
            rec_path = tmp_path / "recommendation.jsonl"
            for entry in FIXTURE_FEEDBACK:
                feedback_path.write_text(
                    (feedback_path.read_text(encoding="utf-8") if feedback_path.exists() else "")
                    + json.dumps(entry, ensure_ascii=False)
                    + "\n",
                    encoding="utf-8",
                )
            for entry in FIXTURE_RECOMMENDATION.values():
                rec_path.write_text(
                    (rec_path.read_text(encoding="utf-8") if rec_path.exists() else "")
                    + json.dumps(entry, ensure_ascii=False)
                    + "\n",
                    encoding="utf-8",
                )
            summary = analyze_logs(feedback_path, rec_path)
            self.assertEqual(summary["overall"]["total_logs"], 6)

    def test_load_recommendation_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rec.jsonl"
            path.write_text(
                json.dumps(FIXTURE_RECOMMENDATION["stable_mail"], ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            index = load_recommendation_index(path)
            self.assertIn("stable-mail", index)

    def test_default_margin_threshold(self) -> None:
        self.assertEqual(DEFAULT_MARGIN_THRESHOLD, 0.03)

    def test_accepted_stores_accept_quality_unstable(self) -> None:
        entry = {
            "feedback_type": "accepted",
            "accept_quality": "unstable",
            "top1_top2_margin": 0.001,
        }
        result = classify_accepted(entry, None)
        self.assertEqual(result, "unstable_accept")

    def test_analyzer_prefers_feedback_log_margin_without_recommendation_join(self) -> None:
        entry = {
            "recommendation_id": "orphan",
            "input_title": "재택 필요 자료 드라이브 이동",
            "feedback_type": "accepted",
            "top1_top2_margin": 0.001,
            "top1_candidate_id": "folder_organization",
            "top2_candidate_id": "taxi_service",
        }
        row = enrich_feedback_row(entry, {})
        self.assertEqual(row.margin, 0.001)
        self.assertEqual(row.accept_class, "unstable_accept")
        self.assertEqual(row.workflow, "folder_organization")

    def test_legacy_feedback_without_schema_fields(self) -> None:
        entry = {
            "recommendation_id": "stable-mail",
            "feedback_type": "accepted",
        }
        row = enrich_feedback_row(entry, self.rec_index)
        self.assertEqual(row.accept_class, "stable_accept")
        self.assertAlmostEqual(row.margin or 0, 0.43, places=2)

        legacy_no_rec = {
            "feedback_type": "accepted",
        }
        self.assertEqual(classify_accepted(legacy_no_rec, None), "unsure_accept")

    def test_ranking_confidence_thresholds(self) -> None:
        self.assertEqual(infer_ranking_confidence(0.001), "low")
        self.assertEqual(infer_ranking_confidence(0.05), "medium")
        self.assertEqual(infer_ranking_confidence(0.08), "high")
        self.assertEqual(infer_ranking_confidence(None), "unknown")

    def test_accepted_memo_not_counted_as_override_taxonomy(self) -> None:
        entry = {
            "feedback_type": "accepted",
            "accept_quality": "unstable",
            "ranking_confidence_note": "폴더 추천은 맞지만 taxi_service와 거의 동점",
            "top1_top2_margin": 0.001,
            "system_recommended_visual": {"type": "emoji", "value": "📁"},
            "final_selected_visual": {"type": "emoji", "value": "📁"},
        }
        row = enrich_feedback_row(entry, {})
        summary = analyze_feedback_rows([row])
        self.assertEqual(summary["overall"]["override_count"], 0)
        self.assertEqual(summary["overall"]["accepted_count"], 1)
        self.assertEqual(summary["acceptance_metrics"]["unstable_accept_count"], 1)
        self.assertEqual(summary["override_metrics"]["ranking_instability"]["count"], 0)


if __name__ == "__main__":
    unittest.main()
