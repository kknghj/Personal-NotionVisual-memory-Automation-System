"""``data/sample_cases.json`` 평면 배열·exact match 우선 동작 검증."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import app.main as main_module
from app.data_loader import load_sample_cases, validate_flat_sample_cases
from app.models import RecommendRequest
from app.recommender import find_exact_title_match


class SampleCasesFlatJsonTests(unittest.TestCase):
    """루트 배열·각 원소 ``title`` / ``visual`` 구조."""

    def test_load_sample_cases_returns_flat_list_of_dicts(self) -> None:
        cases = load_sample_cases()
        self.assertIsInstance(cases, list)
        self.assertGreater(len(cases), 0)
        for i, case in enumerate(cases):
            with self.subTest(index=i):
                self.assertIsInstance(case, dict)
                self.assertIn("title", case)
                self.assertIsInstance(case["title"], str)
                self.assertNotEqual(case["title"].strip(), "")
                self.assertIn("visual", case)
                vis = case["visual"]
                self.assertIsInstance(vis, dict)
                self.assertIn("type", vis)
                self.assertIn("value", vis)
                self.assertIn(vis["type"], ("emoji", "notion_icon"))
                self.assertIsInstance(vis["value"], str)
                self.assertNotEqual(vis["value"].strip(), "")


class ValidateFlatSampleCasesTests(unittest.TestCase):
    """``validate_flat_sample_cases`` 오류 메시지."""

    def test_rejects_non_list_root(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON array"):
            validate_flat_sample_cases({})

    def test_rejects_deprecated_wrapper(self) -> None:
        bad = [{"sample_case_schema": {}, "recommended_updates": []}]
        with self.assertRaisesRegex(ValueError, "deprecated wrapper"):
            validate_flat_sample_cases(bad)

    def test_rejects_recommended_updates_key(self) -> None:
        bad = [{"recommended_updates": [], "title": "x", "visual": {"type": "emoji", "value": "📧"}}]
        with self.assertRaisesRegex(ValueError, "deprecated wrapper"):
            validate_flat_sample_cases(bad)

    def test_rejects_non_object_element(self) -> None:
        with self.assertRaisesRegex(ValueError, r"item \[0\]"):
            validate_flat_sample_cases(["not-a-dict"])

    def test_rejects_empty_title(self) -> None:
        bad = [{"title": "   ", "visual": {"type": "emoji", "value": "📧"}}]
        with self.assertRaisesRegex(ValueError, "non-empty string \"title\""):
            validate_flat_sample_cases(bad)

    def test_rejects_bad_visual_type(self) -> None:
        bad = [{"title": "회의", "visual": {"type": "image", "value": "x"}}]
        with self.assertRaisesRegex(ValueError, "visual.type"):
            validate_flat_sample_cases(bad)


class SampleCasesExactMatchPriorityTests(unittest.TestCase):
    """exact hit 시 catalog 경로를 타지 않고 샘플 visual을 쓴다."""

    def setUp(self) -> None:
        main_module._sample_cases = None

    def test_find_exact_title_match_returns_case_with_sample_visual(self) -> None:
        cases = load_sample_cases()
        title = "과장님 식사 당번 메일"
        hit = find_exact_title_match(title, cases)
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit["visual"]["type"], "emoji")
        self.assertEqual(hit["visual"]["value"], "📧")

    def test_recommend_icon_does_not_call_find_best_on_exact_title(self) -> None:
        from app.main import recommend_icon

        title = "점심 카톡 확인"
        with patch("app.main.find_best_visual_candidate_match") as mock_find:
            mock_find.side_effect = AssertionError(
                "find_best_visual_candidate_match must not run when sample_cases exact matches"
            )
            res = recommend_icon(RecommendRequest(title=title))
        mock_find.assert_not_called()
        self.assertEqual(res.visual.type, "emoji")
        self.assertEqual(res.visual.value, "💬")
        self.assertIn("점심", res.reason)

    def test_strip_matches_stored_title(self) -> None:
        cases = load_sample_cases()
        hit = find_exact_title_match("  회의자료 확인  ", cases)
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit["visual"]["value"], "📄")


if __name__ == "__main__":
    unittest.main()
