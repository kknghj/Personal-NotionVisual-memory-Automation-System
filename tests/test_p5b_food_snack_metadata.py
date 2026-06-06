"""P5-B Fix 5 — snack/food metadata enrichment."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

FIX5_SNACK_IDS = frozenset({"snack_item", "snack_pickup"})
FIX5_FRUIT_PACKAGE_IDS = frozenset({"fruit_snack", "package_loading"})
FIX5_DRINK_IDS = frozenset({"beverage_pickup"})
FOOD_PREP_IDS = frozenset({"food_preparation", "prep_paired_food_bento", "prep_paired_food_snack"})
NOTICE_TOP1_IDS = frozenset(
    {
        "notice_posting",
        "urgent_notice",
        "publication_pinned_notice",
    }
)


class P5BFoodSnackMetadataCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_fix5_candidate_ids_exist(self) -> None:
        for cid in ("snack_item", "fruit_snack", "package_loading", "beverage_pickup"):
            with self.subTest(candidate_id=cid):
                self.assertIn(cid, self._cands)
                self.assertIn("workflow_priority", self._cands[cid])


class P5BFoodSnackMetadataRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _match(self, title: str) -> tuple[str, str]:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out, msg=title)
        assert out is not None
        visual = out.data.get("visual") or {}
        return out.candidate_id, visual.get("value", "")

    def test_fix5_snack_survey_title(self) -> None:
        cid, val = self._match("탕비실 간식 선호 조사")
        self.assertIn(cid, FIX5_SNACK_IDS)
        self.assertIn(val, {"🍬", "🍰"})

    def test_fix5_fruit_snack_loading_title(self) -> None:
        cid, val = self._match("과일간식 짐 차에 싣기")
        self.assertIn(cid, FIX5_FRUIT_PACKAGE_IDS)
        self.assertIn(val, {"🍇", "📦"})

    def test_fix5_beverage_pickup_title(self) -> None:
        cid, val = self._match("커피, 차 픽업")
        self.assertIn(cid, FIX5_DRINK_IDS)
        self.assertEqual(val, "coffee paper cup")

    def test_fix5_bento_preparation_regression(self) -> None:
        cid, val = self._match("도시락 준비")
        self.assertIn(cid, FOOD_PREP_IDS)
        self.assertEqual(val, "🍱")

    def test_fix5_meal_preparation_regression(self) -> None:
        cid, val = self._match("식사 준비")
        self.assertIn(cid, FOOD_PREP_IDS)
        self.assertIn(val, {"🍱", "🍰"})

    def test_fix5_school_meal_preparation_regression(self) -> None:
        cid, val = self._match("급식 준비")
        self.assertIn(cid, FOOD_PREP_IDS)
        self.assertEqual(val, "🍱")

    def test_fix5_spreadsheet_regression(self) -> None:
        cid, val = self._match("엑셀 자료 정리")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    def test_fix5_pinned_notice_regression(self) -> None:
        cid, _ = self._match("채팅방 공지 등록")
        self.assertIn(cid, NOTICE_TOP1_IDS)


if __name__ == "__main__":
    unittest.main()
