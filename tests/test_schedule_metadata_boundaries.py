"""Metadata Pilot M2-A: schedule/date verification over generic document review."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

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

    def _top_rows(self, title: str, limit: int = 3) -> list[tuple[str, int]]:
        rows = rank_visual_candidate_rows(title, self._cands)[:limit]
        return [(row.candidate_id, row.semantic_bonus) for row in rows]

    def test_notion_schedule_share_stays_close_without_visibility_tone_bonus(self) -> None:
        title = "노션 일정 공유"
        rows = self._top_rows(title)
        self.assertEqual(rows[0][0], "notion_docs_touchup")
        top_ids = {candidate_id for candidate_id, _ in rows[:2]}
        self.assertEqual(
            top_ids,
            {"notion_docs_touchup", "work_calendar_organization"},
        )
        calendar_bonus = next(
            bonus for candidate_id, bonus in rows if candidate_id == "work_calendar_organization"
        )
        self.assertEqual(
            calendar_bonus,
            0,
            msg="schedule candidate must not win on visibility/tone-only bonus",
        )

    def test_calendar_schedule_share_prefers_work_calendar(self) -> None:
        title = "캘린더 일정 공유"
        rows = self._top_rows(title)
        self.assertEqual(rows[0][0], "work_calendar_organization")
        calendar_bonus = rows[0][1]
        self.assertEqual(
            calendar_bonus,
            2,
            msg="calendar share uses explicit calendar anchor boost, not visibility/tone",
        )


if __name__ == "__main__":
    unittest.main()
