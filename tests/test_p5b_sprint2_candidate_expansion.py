"""P5-B Sprint 2 candidate expansion (5 remaining catalog gaps)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match

SPRINT2_NEW_IDS = frozenset({"document_recipient_lookup", "allowance_request_document"})
CODING_IDS = frozenset({"coding", "terminal_work", "system_work"})


class Sprint2CandidateCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_sprint2_new_candidate_ids_exist(self) -> None:
        for cid in sorted(SPRINT2_NEW_IDS):
            with self.subTest(candidate_id=cid):
                self.assertIn(cid, self._cands)
                self.assertIn("workflow_priority", self._cands[cid])
                self.assertIn("semantic_metadata", self._cands[cid])

    def test_strengthened_keywords_present(self) -> None:
        def texts(cid: str) -> set[str]:
            return {m["text"] for m in self._cands[cid]["meaning"] if isinstance(m, dict)}

        self.assertIn("수신자지정", texts("document_recipient_lookup"))
        self.assertIn("수당신청", texts("allowance_request_document"))
        self.assertIn("할인종료일", texts("work_calendar_organization"))
        self.assertIn("제작시기확인", texts("work_calendar_organization"))
        self.assertIn("바이브코딩아이디어", texts("brainstorming"))


class Sprint2CandidateRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _match(self, title: str) -> tuple[str, str]:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out, msg=title)
        assert out is not None
        visual = out.data.get("visual") or {}
        return out.candidate_id, str(visual.get("value", ""))

    def test_document_recipient_lookup_titles(self) -> None:
        cid, val = self._match("공문 수신자 지정 관련 알아보기")
        self.assertEqual(cid, "document_recipient_lookup")
        self.assertEqual(val, "user squares")

    def test_allowance_request_document_titles(self) -> None:
        cases = {
            "공익감사단 4월 수당 신청": ("allowance_request_document", "📝"),
            "위원 수당 지급 신청": ("allowance_request_document", "📝"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_work_calendar_organization_gap_titles(self) -> None:
        cases = {
            "알뜰폰 할인 종료일": ("work_calendar_organization", "📅"),
            "표창 제작시기 확인": ("work_calendar_organization", "📅"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_brainstorming_vibe_coding_idea_titles(self) -> None:
        cases = {
            "바이브코딩 아이디어 브레인스토밍": ("brainstorming", "🧠"),
            "기획 브레인스토밍": ("brainstorming", "🧠"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_vibe_coding_alone_stays_coding(self) -> None:
        cid, val = self._match("바이브코딩 인강 수강")
        self.assertIn(cid, CODING_IDS)
        self.assertEqual(val, "angle-brackets-solidus")

    def test_document_edit_regression(self) -> None:
        cid, val = self._match("회의록 수정")
        self.assertEqual(cid, "document_edit")
        self.assertEqual(val, "📝")

    def test_salary_system_regression(self) -> None:
        cid, val = self._match("월급여 입력")
        self.assertEqual(cid, "salary_system")
        self.assertEqual(val, "💰")

    def test_document_review_regression(self) -> None:
        cid, _ = self._match("식생활교육 보도자료 확인")
        self.assertEqual(cid, "press_release_review")


if __name__ == "__main__":
    unittest.main()
