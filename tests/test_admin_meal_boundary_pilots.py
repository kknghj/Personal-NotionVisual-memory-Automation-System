"""Pilot A (admin system) and Pilot B (meal/venue context) boundary tests."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match


class AdminSystemBoundaryPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_admin_system_target_cases(self) -> None:
        cases = (
            ("회의실 예약", "system_work"),
            ("4/9, 24 출장 여비 등록", "system_work"),
            ("정보 공개 접수 확인", "system_work"),
            ("위원회 회의 수당 지급", "system_work"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)

    def test_admin_system_salary_regressions(self) -> None:
        cases = (
            ("월급여 입력", "salary_system"),
            ("급여 계산", "salary_system"),
            ("급여 지급", "salary_system"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)

    def test_admin_system_room_cleanup_regressions(self) -> None:
        cases = (
            ("회의실 정리", "room_cleanup"),
            ("사무실 정리", "office_cleanup"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)

    def test_admin_system_document_review_regressions(self) -> None:
        cases = (
            ("문서 검토", "document_review"),
            ("접수 문서 확인", "document_review"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)

    def test_admin_system_travel_reservation_not_system_work(self) -> None:
        cases = (
            ("부산 출장 숙소 예약", "lodging_reservation"),
            ("세종 출장 KTX 예매", "train_reservation"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)


class MealVenueContextBoundaryPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_meal_venue_target_case(self) -> None:
        self.assertEqual(
            self._cid("교육청 회의 오찬 장소 정하기"),
            "food_meeting",
        )

    def test_meeting_regressions(self) -> None:
        cases = (
            ("부서 주간회의", frozenset({"meeting", "internal_meeting"})),
            ("과장 주재 주간회의 참석", frozenset({"internal_meeting"})),
            ("팀 회의 참석", frozenset({"meeting"})),
            ("내부 회의 준비", frozenset({"meeting"})),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertIn(self._cid(title), expected)


if __name__ == "__main__":
    unittest.main()
