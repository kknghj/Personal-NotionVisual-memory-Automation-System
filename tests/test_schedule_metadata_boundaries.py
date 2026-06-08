"""Metadata Pilot M2-A: schedule/date verification over generic document review."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

TARGET_CASES: tuple[tuple[str, frozenset[str]], ...] = (
    ("알뜰폰 할인종료일 확인", frozenset({"work_calendar_organization"})),
    ("할인종료일 확인", frozenset({"work_calendar_organization"})),
    (
        "혜택 마감일 확인",
        frozenset({"work_calendar_organization", "deadline_management"}),
    ),
    (
        "신청 마감일 확인",
        frozenset({"work_calendar_organization", "deadline_management"}),
    ),
)

REGRESSION_CASES: tuple[tuple[str, str], ...] = (
    ("표창 제작시기 확인", "work_calendar_organization"),
    ("알뜰폰 할인 종료일", "work_calendar_organization"),
    ("일정표 정리", "work_calendar_organization"),
    ("회의 일정 공유", "work_calendar_organization"),
    ("교육 일정 확인", "messenger_chat"),
    ("교육 자료 확인", "document_review"),
    ("공문 확인", "document_review"),
    ("결과보고 확인", "result_reporting"),
    ("신청서 검토", "document_review"),
)


class ScheduleMetadataBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_date_verification_targets(self) -> None:
        for title, expected_ids in TARGET_CASES:
            with self.subTest(title=title):
                self.assertIn(self._cid(title), expected_ids)

    def test_schedule_regressions(self) -> None:
        for title, expected in REGRESSION_CASES:
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), expected)


if __name__ == "__main__":
    unittest.main()
