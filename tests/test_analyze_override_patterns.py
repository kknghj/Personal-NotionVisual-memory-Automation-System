"""P5-A Override Pattern Analyzer tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from tools.analyze_override_patterns import (
    ANALYSIS_BASIS,
    DEFAULT_INPUT,
    GAP_TYPES,
    analyze,
    classify_gap_type,
    classify_primary_pattern,
    confidence_tier,
    example_status,
    interpretation_markdown_lines,
    load_examples,
)

ROOT = Path(__file__).resolve().parents[1]


def _example(**overrides: object) -> dict:
    base = {
        "id": 1,
        "title": "테스트 제목",
        "recommended_visual": "📄",
        "final_visual": "📧",
        "confidence": 80,
        "note": "",
        "source": "test",
    }
    base.update(overrides)
    return base


class AnalyzeOverridePatternsTests(unittest.TestCase):
    def test_load_override_examples_json(self) -> None:
        path = ROOT / DEFAULT_INPUT
        self.assertTrue(path.is_file())
        examples = load_examples(path)
        self.assertGreater(len(examples), 0)
        self.assertIn("status", examples[0])
        self.assertIn("primary_pattern", examples[0])
        self.assertIn("gap_type", examples[0])

    def test_confidence_distribution(self) -> None:
        examples = [
            {**_example(confidence=95), "status": "override", "primary_pattern": "unknown", "confidence_tier": "strong"},
            {**_example(confidence=75), "status": "override", "primary_pattern": "unknown", "confidence_tier": "medium"},
            {**_example(confidence=40), "status": "override", "primary_pattern": "unknown", "confidence_tier": "weak"},
            {**_example(confidence=None), "status": "override", "primary_pattern": "unknown", "confidence_tier": "unknown"},
        ]
        summary = analyze(examples)
        self.assertEqual(summary["confidence_distribution"]["strong"], 1)
        self.assertEqual(summary["confidence_distribution"]["medium"], 1)
        self.assertEqual(summary["confidence_distribution"]["weak"], 1)
        self.assertEqual(summary["confidence_distribution"]["unknown"], 1)

    def test_candidate_gap_when_recommended_none(self) -> None:
        item = _example(recommended_visual="없음", final_visual="🎨", note="홍보물 제작")
        self.assertEqual(classify_primary_pattern(item), "candidate_gap")

    def test_gap_type_ambiguous_channel(self) -> None:
        item = _example(
            recommended_visual="없음",
            final_visual="📞 or 📝 or 💻",
            confidence=40,
            note="민원이 전화일 수 있고, 문서 작성일 수 있고, 행정 내부 시스템을 통한 처리일 수 있음",
        )
        self.assertEqual(classify_gap_type(item), "ambiguous_channel")
        self.assertEqual(classify_primary_pattern(item), "candidate_gap")

    def test_gap_type_candidate_gap_unknown_final_visual(self) -> None:
        catalog = {
            "meta": {},
            "sample": {
                "visual": {"type": "emoji", "value": "📄"},
                "workflow_priority": 2,
                "meaning": [{"text": "공문", "workflow_resolution": 1, "interface_dominance": 0}],
            },
        }
        item = _example(final_visual="unknown-icon-xyz", recommended_visual="📄")
        self.assertEqual(classify_gap_type(item, catalog=catalog), "candidate_gap")

    def test_gap_type_keyword_gap(self) -> None:
        catalog = {
            "meta": {},
            "creative": {
                "visual": {"type": "emoji", "value": "🎨"},
                "workflow_priority": 2,
                "meaning": [
                    {"text": "배너제작", "workflow_resolution": 2, "interface_dominance": 0},
                ],
            },
        }
        item = _example(
            title="다른 업무 제목",
            recommended_visual="없음",
            final_visual="🎨",
        )
        self.assertEqual(classify_gap_type(item, catalog=catalog), "keyword_gap")

    def test_gap_type_metadata_gap(self) -> None:
        catalog = {
            "meta": {},
            "phone_call": {
                "visual": {"type": "emoji", "value": "📞"},
                "workflow_priority": 1,
                "meaning": [{"text": "전화", "workflow_resolution": 3, "interface_dominance": 1}],
            },
            "document_edit": {
                "visual": {"type": "emoji", "value": "📝"},
                "workflow_priority": 2,
                "meaning": [{"text": "공문", "workflow_resolution": 2, "interface_dominance": 0}],
            },
        }
        item = _example(
            title="공문 작성",
            recommended_visual="📝",
            final_visual="📞",
            note="전화로 요청",
        )
        self.assertEqual(classify_gap_type(item, catalog=catalog), "metadata_gap")

    def test_gap_type_none_when_accepted(self) -> None:
        item = _example(recommended_visual="📞", final_visual="📞", confidence=100)
        self.assertIsNone(classify_gap_type(item))

    def test_gap_type_summary_in_analyze(self) -> None:
        summary = analyze(load_examples(ROOT / DEFAULT_INPUT))
        self.assertIn("gap_type_summary", summary)
        for gap in GAP_TYPES:
            self.assertIn(gap, summary["gap_type_summary"])

    def test_channel_priority_from_note(self) -> None:
        item = _example(
            recommended_visual="📄",
            final_visual="📧",
            note="공문을 메일로 전달 요청",
        )
        self.assertEqual(classify_primary_pattern(item), "channel_priority")

    def test_channel_priority_from_phone_note(self) -> None:
        item = _example(
            recommended_visual="📄",
            final_visual="📞",
            note="담당자에게 전화로 요청",
        )
        self.assertEqual(classify_primary_pattern(item), "channel_priority")

    def test_interface_priority_from_system_note(self) -> None:
        item = _example(
            recommended_visual="💰",
            final_visual="💻",
            note="행정 내부 시스템으로 등록하는 행위",
        )
        self.assertEqual(classify_primary_pattern(item), "interface_priority")

    def test_object_priority_keywords(self) -> None:
        for keyword in ("보도자료", "영상", "포스터", "배너", "과일"):
            with self.subTest(keyword=keyword):
                item = _example(
                    recommended_visual="📄",
                    final_visual="🎨",
                    note=f"확인 대상인 {keyword}에 중점",
                )
                self.assertEqual(classify_primary_pattern(item), "object_priority")

    def test_representative_cases_grouped_by_pattern(self) -> None:
        examples = load_examples(ROOT / DEFAULT_INPUT)
        summary = analyze(examples)
        self.assertGreater(summary["override_count"], 0)
        for pattern, count in summary["pattern_summary"].items():
            if count:
                self.assertTrue(summary["representative_cases"][pattern])

    def test_accepted_excluded_from_override_analysis(self) -> None:
        item = _example(recommended_visual="📞", final_visual="📞", confidence=100)
        self.assertEqual(example_status(item), "accepted")
        enriched = {**item, "status": "accepted", "primary_pattern": "unknown", "confidence_tier": "strong"}
        summary = analyze([enriched])
        self.assertEqual(summary["accepted_count"], 1)
        self.assertEqual(summary["override_count"], 0)

    def test_confidence_tier_boundaries(self) -> None:
        self.assertEqual(confidence_tier(90), "strong")
        self.assertEqual(confidence_tier(89), "medium")
        self.assertEqual(confidence_tier(70), "medium")
        self.assertEqual(confidence_tier(69), "weak")
        self.assertEqual(confidence_tier(None), "unknown")

    def test_action_priority_actual_action_exception(self) -> None:
        item = _example(
            recommended_visual="🤝",
            final_visual="🍴",
            note="회의는 맥락이고 실제 행동은 오찬 장소 선정",
        )
        self.assertEqual(classify_primary_pattern(item), "action_priority")

    def test_former_unknown_cases_reclassified(self) -> None:
        cases = [
            (
                "커피, 차 픽업",
                {
                    "id": 18,
                    "title": "커피, 차 픽업",
                    "recommended_visual": "🍰",
                    "final_visual": "coffee paper cup (brown)",
                    "confidence": 70,
                    "note": "종이 일회용 음료를 픽업하는 것이므로 케이크가 아닌 음료잔 선택(커피색인 갈색 연상)",
                },
                "action_priority",
            ),
            (
                "을지훈련 매트리스 상태 확인",
                {
                    "id": 36,
                    "title": "을지훈련 매트리스 상태 확인",
                    "recommended_visual": "📄",
                    "final_visual": "🛏️",
                    "confidence": 80,
                    "note": "문서 작업이 아닌 매트리스라는 물품 상태 확인하는 것으로, 매트리스와 비슷한 침대 이미지  활용",
                },
                "object_priority",
            ),
            (
                "비상소집훈련 참석",
                {
                    "id": 38,
                    "title": "비상소집훈련 참석",
                    "recommended_visual": "🧑‍🏫",
                    "final_visual": "🚨",
                    "confidence": 100,
                    "note": "사이렌 이미지가 비상소집을 연상시킴.",
                },
                "action_priority",
            ),
            (
                "공문 수신자 지정 관련 알아보기",
                {
                    "id": 50,
                    "title": "공문 수신자 지정 관련 알아보기",
                    "recommended_visual": "📝",
                    "final_visual": "user squares (grey)",
                    "confidence": 90,
                    "note": "지정해야 할 ‘수신자’를 확인하는 것으로 이를 연상하는 아이콘 사용함.",
                },
                "object_priority",
            ),
        ]
        for label, fields, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(classify_primary_pattern(fields), expected)

    def test_full_dataset_unknown_at_most_one(self) -> None:
        summary = analyze(load_examples(ROOT / DEFAULT_INPUT))
        self.assertLessEqual(summary["pattern_summary"]["unknown"], 1)

    def test_cli_default_input(self) -> None:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/analyze_override_patterns.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            check=True,
        )
        self.assertIn("# Override Pattern Analysis", result.stdout)
        self.assertIn("## primary_pattern vs gap_type", result.stdout)
        self.assertIn("historical manual feedback", result.stdout)
        self.assertIn("gap_type=null", result.stdout)
        self.assertIn("Override cases:", result.stdout)

    def test_cli_json_output(self) -> None:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/analyze_override_patterns.py"),
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
        self.assertEqual(payload["analysis_basis"], ANALYSIS_BASIS)
        self.assertIn("interpretation_note", payload)
        self.assertIn("pattern_summary", payload)
        self.assertIn("gap_type_summary", payload)
        self.assertIn("override_count", payload)

    def test_hr_consultation_resolved_gap_interpretation(self) -> None:
        examples = load_examples(ROOT / DEFAULT_INPUT)
        hr = next(row for row in examples if row.get("title") == "인사 상담")
        self.assertEqual(hr["primary_pattern"], "candidate_gap")
        self.assertIsNone(hr["gap_type"])
        self.assertGreater(len(interpretation_markdown_lines()), 5)


if __name__ == "__main__":
    unittest.main()
