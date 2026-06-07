"""P5-B low-risk candidate catalog fixes (Fix 1–4)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

TRAVEL_IDS = frozenset({"train_reservation", "flight_reservation", "lodging_reservation"})
EMERGENCY_IDS = frozenset({"emergency_drill"})
ORG_CHART_IDS = frozenset({"organization_chart"})
WEB_POSTING_IDS = frozenset({"web_posting"})
NOTICE_TOP1_IDS = frozenset(
    {
        "notice_posting",
        "urgent_notice",
        "publication_pinned_notice",
    }
)


class P5BCandidateCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_new_candidate_ids_exist(self) -> None:
        for cid in (
            "train_reservation",
            "flight_reservation",
            "lodging_reservation",
            "emergency_drill",
            "organization_chart",
            "web_posting",
        ):
            with self.subTest(candidate_id=cid):
                self.assertIn(cid, self._cands)
                self.assertIn("workflow_priority", self._cands[cid])


class P5BCandidateRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _match(self, title: str) -> tuple[str, str]:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out, msg=title)
        assert out is not None
        visual = out.data.get("visual") or {}
        return out.candidate_id, visual.get("value", "")

    def test_fix1_travel_reservation_titles(self) -> None:
        cases = {
            "기차표 예매": ("train_reservation", "🚄"),
            "세종 출장 KTX 예매": ("train_reservation", "🚄"),
            "제주도 비행기 예매": ("flight_reservation", "✈️"),
            "부산 출장 숙소 예약": ("lodging_reservation", "🏨"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_fix1_spreadsheet_regression(self) -> None:
        cid, val = self._match("엑셀 자료 정리")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    def test_fix2_emergency_drill_titles(self) -> None:
        cases = {
            "민방위 대피 훈련": ("evacuation_drill", "person running"),
            "비상소집훈련 참석": ("emergency_drill", "🚨"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_fix2_education_attendance_not_emergency(self) -> None:
        for title in ("노션 강의 수강", "교육 참석"):
            with self.subTest(title=title):
                cid, _ = self._match(title)
                self.assertNotIn(cid, EMERGENCY_IDS)

    def test_fix3_organization_chart_titles(self) -> None:
        cases = {
            "센터 조직도 및 연락처 정비": ("organization_chart", "network"),
            "조직도 수정": ("organization_chart", "network"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_fix3_phone_call_regression(self) -> None:
        cid, val = self._match("담당자 전화 문의")
        self.assertEqual(cid, "phone_call")
        self.assertEqual(val, "📞")

    def test_fix4_web_posting_titles(self) -> None:
        cases = {
            "서울시 누리집 분야별 새소식 게시글 예약": ("web_posting", "social media post"),
            "누리집 새소식 게시": ("web_posting", "social media post"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_fix4_pinned_notice_regression(self) -> None:
        cid, _ = self._match("채팅방 공지 등록")
        self.assertIn(cid, NOTICE_TOP1_IDS)


if __name__ == "__main__":
    unittest.main()
