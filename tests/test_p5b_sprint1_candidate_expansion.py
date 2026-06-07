"""P5-B Sprint 1 candidate expansion (6 catalog additions)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

SPRINT1_IDS = frozenset(
    {
        "performance_aggregation",
        "evacuation_drill",
        "promotional_material_review",
        "inquiry_response",
        "event_preparation_checklist",
        "site_inspection_visit",
    }
)
EMERGENCY_IDS = frozenset({"emergency_drill", "evacuation_drill"})


class Sprint1CandidateCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_sprint1_candidate_ids_exist(self) -> None:
        for cid in sorted(SPRINT1_IDS):
            with self.subTest(candidate_id=cid):
                self.assertIn(cid, self._cands)
                self.assertIn("workflow_priority", self._cands[cid])
                self.assertIn("semantic_metadata", self._cands[cid])


class Sprint1CandidateRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _match(self, title: str) -> tuple[str, str]:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out, msg=title)
        assert out is not None
        visual = out.data.get("visual") or {}
        return out.candidate_id, str(visual.get("value", ""))

    def test_performance_aggregation_titles(self) -> None:
        cases = {
            "센터별 운영실적 취합": ("performance_aggregation", "📊"),
            "분기 운영 실적 집계": ("performance_aggregation", "📊"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_evacuation_drill_titles(self) -> None:
        cases = {
            "민방위 대피 훈련": ("evacuation_drill", "person running"),
            "외부 대피 훈련 실시": ("evacuation_drill", "person running"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_emergency_drill_siren_regression(self) -> None:
        cid, val = self._match("비상소집훈련 참석")
        self.assertEqual(cid, "emergency_drill")
        self.assertEqual(val, "🚨")

    def test_promotional_material_review_titles(self) -> None:
        cases = {
            "홍보물 시안 검토": ("promotional_material_review", "photo landscape"),
            "배너 시안 검토": ("promotional_material_review", "photo landscape"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_inquiry_response_titles(self) -> None:
        cases = {
            "운영 관련 질의 응답": ("inquiry_response", "speech bubbles"),
            "질의응답 처리": ("inquiry_response", "speech bubbles"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_event_preparation_checklist_titles(self) -> None:
        cases = {
            "강사단 평가회 사전 준비 사항 리스트": (
                "event_preparation_checklist",
                "checkmark list",
            ),
            "평가회 사전 준비 사항 리스트": ("event_preparation_checklist", "checkmark list"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_site_inspection_visit_titles(self) -> None:
        cases = {
            "센터 방문점검 실시": ("site_inspection_visit", "clipboard"),
            "교육센터 현장 점검": ("site_inspection_visit", "clipboard"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_room_cleaning_regression(self) -> None:
        cid, val = self._match("회의실 청소")
        self.assertEqual(cid, "room_cleanup")
        self.assertEqual(val, "chair")

    def test_survey_form_regression(self) -> None:
        cid, _ = self._match("만족도조사 설문")
        self.assertEqual(cid, "survey_form")
        self.assertNotEqual(cid, "inquiry_response")

    def test_document_review_press_regression(self) -> None:
        cid, _ = self._match("식생활교육 보도자료 확인")
        self.assertEqual(cid, "press_release_review")


if __name__ == "__main__":
    unittest.main()
