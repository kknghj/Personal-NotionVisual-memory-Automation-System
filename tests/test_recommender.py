"""compound subject·workflow 정렬 회귀 테스트."""

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match


class RecommenderCompoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out)
        return out[1]

    def test_education_office_budget_negotiation_prefers_meeting(self):
        # compound(교육청) 내부 '교육'이 아니라 끝의 '협의'가 workflow
        self.assertEqual(self._cid("교육청 급식 예산 협의"), "meeting")

    def test_education_application_form_writing_is_document_edit(self):
        # 신청서는 subject compound; 끝의 '작성'이 문서 편집 workflow
        self.assertEqual(self._cid("교육 신청서 작성"), "document_edit")

    def test_education_negotiation_two_words_prefers_meeting(self):
        # '교육'+'협의' 붙임에서 앞 어근만 막지 않음; 협의 workflow가 meeting
        self.assertEqual(self._cid("교육 협의"), "meeting")

    def _match(self, title: str) -> tuple[str, str]:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out)
        data, cid, *_ = out
        v = data.get("visual") or {}
        val = v.get("value", "")
        return cid, val

    def test_prep_document_material(self):
        for title in (
            "면접자료 준비",
            "회의자료 준비",
            "공문 준비",
            "계획안 준비",
            "보고서 준비",
        ):
            cid, emoji = self._match(title)
            self.assertEqual(cid, "prep_paired_document", msg=title)
            self.assertEqual(emoji, "📄", msg=title)

    def test_prep_food(self):
        self.assertEqual(self._match("음식 준비")[1], "🍰")
        self.assertEqual(self._match("간식 준비")[1], "🍰")
        self.assertEqual(self._match("도시락 준비")[1], "🍱")
        self.assertEqual(self._match("커피 준비")[1], "☕")
        self.assertEqual(self._match("홍차 준비")[1], "☕")

    def test_prep_event(self):
        self.assertEqual(self._match("행사 준비")[1], "🎉")
        self.assertEqual(self._match("행사 부스 준비")[1], "🎪")
        self.assertEqual(self._match("부스 준비")[1], "🎪")
        self.assertEqual(self._match("현수막 준비")[1], "🎉")
        self.assertEqual(self._match("행사 세팅 준비")[1], "🎪")

    def test_confirm_coordination_prefers_messenger_over_document_review(self):
        cid, val = self._match("팀원 다음주 재택근무 일정 확인")
        self.assertEqual(cid, "messenger_chat")
        self.assertEqual(val, "💬")

    def test_confirm_coordination_keywords(self):
        for title in (
            "일정 확인",
            "참석 여부 확인",
            "시간 확인",
            "재택근무 일정 확인",
            "가능 여부 확인",
        ):
            cid, _ = self._match(title)
            self.assertEqual(cid, "messenger_chat", msg=title)

    def test_confirm_coordination_prefers_phone_when_explicit(self):
        self.assertEqual(self._cid("다음주 출근 일정 전화 확인"), "phone_call")

    def test_confirm_document_review_without_coordination_keywords(self):
        self.assertEqual(self._cid("보고서 확인"), "document_review")


if __name__ == "__main__":
    unittest.main()
