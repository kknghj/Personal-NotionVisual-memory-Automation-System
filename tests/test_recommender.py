"""compound subject·workflow 정렬 회귀 테스트.

Semantic contract smoke tests (modifier / interface / pair tiers) live in the same
class so they share fixtures; they guard docs/PRD-style intent: interface anchors
and pair rules must not be drowned by generic modifiers or high workflow_priority
noise when the title clearly names a channel or tool.
"""

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

    def test_organize_pair_subject_resolution(self):
        cases = {
            "바탕화면 폴더 정리": ("folder_organization", "📁"),
            "파일 정리": ("folder_organization", "📁"),
            "회의실 정리": ("room_cleanup", "chair"),
            "사무실 정리": ("office_cleanup", "person-trash-can"),
            "방 정리": ("room_cleaning", "mop-bucket"),
            "카톡 알림 정리": ("notification_cleanup", "bell-notification"),
            "자료 정리": ("document_review", "📄"),
            "보고서 정리": ("document_review", "📄"),
            "캐비넷 정리": ("cabinet_organization", "🗄️"),
        }
        for title, (expect_cid, expect_visual) in cases.items():
            cid, val = self._match(title)
            self.assertEqual(cid, expect_cid, msg=title)
            self.assertEqual(val, expect_visual, msg=title)

    def test_organize_spreadsheet_still_wins_with_excel_anchor(self):
        cid, val = self._match("교육 신청 현황 엑셀 정리")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    def test_organize_written_record_respects_compound_subject(self):
        out = find_best_visual_candidate_match("교육자료 정리", self._cands)
        self.assertIsNone(out)

    # --- Modifier suppression: time/urgency LOW terms must not beat INTERFACE anchors ---
    def test_modifier_suppression_prefers_mail_over_lunch_context(self):
        # ``점심``은 LOW_SPECIFICITY; 제목에 ``메일`` 앵커가 있으면 채널 workflow가 우선
        cid, val = self._match("점심 메일 확인")
        self.assertEqual(cid, "mail_action")
        self.assertEqual(val, "📧")

    def test_modifier_suppression_prefers_messenger_over_evening_context(self):
        cid, val = self._match("저녁 카톡 확인")
        self.assertEqual(cid, "messenger_chat")
        self.assertEqual(val, "💬")

    def test_modifier_suppression_prefers_phone_over_urgent_modifier(self):
        # ``긴급``은 urgent_notice 후보에도 걸리지만 ``전화`` 인터페이스가 우선
        cid, val = self._match("긴급 전화 문의")
        self.assertEqual(cid, "phone_call")
        self.assertEqual(val, "📞")

    # --- People vs interface: role tokens alone must not steal channel icons ---
    def test_people_context_does_not_beat_phone_interface(self):
        cid, val = self._match("과장님 전화 문의")
        self.assertEqual(cid, "phone_call")
        self.assertEqual(val, "📞")

    def test_people_context_does_not_beat_mail_interface(self):
        cid, val = self._match("대표 메일 전달")
        self.assertEqual(cid, "mail_action")
        self.assertEqual(val, "📧")

    def test_people_context_does_not_beat_messenger_interface(self):
        cid, val = self._match("팀장 카톡 확인")
        self.assertEqual(cid, "messenger_chat")
        self.assertEqual(val, "💬")

    # --- Interface dominance over organize/document-style subjects ---
    def test_interface_anchor_beats_organize_written_record_for_spreadsheet(self):
        # organize ``자료+정리``보다 엑셀 meaning(인터페이스 dominance)이 앞서야 함
        cid, val = self._match("엑셀 자료 정리")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    def test_interface_anchor_beats_document_edit_for_survey_form(self):
        cid, val = self._match("네이버폼 신청서 수정")
        self.assertEqual(cid, "survey_form")
        self.assertEqual(val, "checkmark-circle")

    def test_interface_anchor_beats_generic_organize_for_terminal(self):
        cid, val = self._match("터미널 환경 설정 정리")
        self.assertEqual(cid, "terminal_work")
        self.assertEqual(val, "command-line-rectangle")

    # --- Pair tier / workflow_priority vs interface: rule_tier 유지 + UI 앵커 우선 정렬 ---
    def test_pair_organize_spreadsheet_unchanged_for_education_status_sheet(self):
        # pair organize가 스프레드시트 meaning을 가리지 않는 기존 계약(회귀)
        cid, val = self._match("교육 신청 현황 엑셀 정리")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    def test_prep_document_subject_outranks_event_when_shared_prep_lemma(self):
        # prep 규칙 순서상 ``자료+준비``가 ``행사+준비``보다 먼저 — 문서 준비 우선 계약
        cid, val = self._match("행사 자료 준비")
        self.assertEqual(cid, "prep_paired_document")
        self.assertEqual(val, "📄")

    def test_spreadsheet_wins_over_high_wp_event_when_excel_anchor_present(self):
        # 행사(event_preparation wp=3)보다 엑셀 인터페이스 meaning이 우선
        cid, val = self._match("행사 엑셀 정리")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    # --- Stacked signals: confirm pair > generic modifiers; prep > executive noise ---
    def test_confirm_coordination_stable_under_person_and_meal_modifiers(self):
        cid, val = self._match("과장님 점심 카톡 일정 확인")
        self.assertEqual(cid, "messenger_chat")
        self.assertEqual(val, "💬")

    def test_prep_document_wins_when_executive_and_event_words_present(self):
        cid, val = self._match("대표 행사 자료 준비")
        self.assertEqual(cid, "prep_paired_document")
        self.assertEqual(val, "📄")

    def test_mail_interface_stable_with_urgency_and_compound_meeting_material(self):
        # compound ``회의자료`` 내부는 앵커로 쓰지 않고, 밖의 ``메일``이 채널을 고정
        cid, val = self._match("긴급 회의자료 메일 전달")
        self.assertEqual(cid, "mail_action")
        self.assertEqual(val, "📧")


if __name__ == "__main__":
    unittest.main()
