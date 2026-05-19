"""Recommender semantic contract tests (P2–P6).

Maps to ``docs/ARCHITECTURE.md``: P2 ``compound_subject_char_mask``, P3
``PairRuleEngine`` / ``PairResolution``, P4–P5 meaning expansion and filters,
P6 unified ``CandidateRow`` ranking and ``BestVisualCandidateMatch`` output.

Each ``TestCase`` subclass guards one **semantic contract** family so failures
point to the broken philosophy (compound vs pair vs interface vs organize vs
global rank), not a monolithic class name.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match


class RecommenderSemanticTestCase(unittest.TestCase):
    """Shared catalog fixture and tuple unpack helpers (P7 input slice compatible)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out)
        return out.candidate_id

    def _match(self, title: str) -> tuple[str, str]:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out)
        data = out.data
        v = data.get("visual") or {}
        val = v.get("value", "")
        return out.candidate_id, val


class CompoundProtectionTests(RecommenderSemanticTestCase):
    """P2 compound span: 내부 substring은 workflow anchor·dominance·organize subject로 쓰이지 않음.

    ``DOCUMENT_COMPOUND_SUBJECT_TERMS`` 마스크와 meaning occurrence 규칙이
    교육청·신청서·교육자료 등 복합 명사를 보호하는지 검증한다.
    """

    def test_education_office_budget_negotiation_prefers_meeting(self):
        # compound(교육청) 내부 '교육'이 아니라 끝의 '협의'가 workflow
        self.assertEqual(self._cid("교육청 급식 예산 협의"), "meeting")

    def test_education_application_form_writing_is_document_edit(self):
        # 신청서는 subject compound; 끝의 '작성'이 문서 편집 workflow
        self.assertEqual(self._cid("교육 신청서 작성"), "document_edit")

    def test_education_negotiation_two_words_prefers_meeting(self):
        # '교육'+'협의' 붙임에서 앞 어근만 막지 않음; 협의 workflow가 meeting
        self.assertEqual(self._cid("교육 협의"), "meeting")

    def test_organize_written_record_respects_compound_subject(self):
        # ``교육자료`` compound 안의 ``자료``로 organize subject를 쓰지 않음 → 매칭 없음
        out = find_best_visual_candidate_match("교육자료 정리", self._cands)
        self.assertIsNone(out)


class PairInterpretationTests(RecommenderSemanticTestCase):
    """P3 declarative pair resolution: prep / confirm_coordination / organize / modify pair track.

    ``PairResolution`` row가 ``pair_rules.json`` 순서·lemma 조건에 맞게 생성되는지,
    coordination 키워드 없을 때는 pair가 아닌 meaning 경로로 떨어지는지 검증한다.
    """

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
            "일정 조율",
            "시간 협의",
        ):
            cid, _ = self._match(title)
            self.assertEqual(cid, "messenger_chat", msg=title)

    def test_confirm_coordination_prefers_phone_when_explicit(self):
        self.assertEqual(self._cid("다음주 출근 일정 전화 확인"), "phone_call")

    def test_confirm_document_review_without_coordination_keywords(self):
        # coordination 키워드 없음 → P3 confirm row 없음 → meaning ``document_review``
        self.assertEqual(self._cid("보고서 확인"), "document_review")


class InterfaceDominanceTests(RecommenderSemanticTestCase):
    """INTERFACE anchor + P6 rank: 채널·도구가 시간·긴급·저녁 등 modifier와 직책 토큰보다 우선.

    제목에 인터페이스 앵커가 있을 때 ``interface_dominance_effective``·workflow_resolution
    쪽 계약이 ``workflow_priority`` 노이즈에 밀리지 않는지, 직책은
    ``PERSON_CONTEXT_MODIFIER_TERMS`` 처리로 채널을 가리지 않는지 검증한다.
    """

    def test_modifier_suppression_prefers_mail_over_lunch_context(self):
        # ``점심``은 LOW_WORKFLOW_RESOLUTION; ``메일`` 앵커가 있으면 채널 workflow가 우선
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


class ModifySemanticTests(RecommenderSemanticTestCase):
    """P3 modify pair: (action=수정, subject=…) + interface dominance vs 서면 subject."""

    def test_modify_document_subjects_use_document_edit(self):
        for title in ("보고서 수정", "회의자료 수정", "공문 수정", "신청서 수정"):
            cid, val = self._match(title)
            self.assertEqual(cid, "document_edit", msg=title)
            self.assertEqual(val, "📝", msg=title)

    def test_modify_spreadsheet_subject(self):
        cid, val = self._match("엑셀 수정")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    def test_modify_form_subject(self):
        cid, val = self._match("네이버폼 수정")
        self.assertEqual(cid, "survey_form")
        self.assertEqual(val, "checkmark-circle")

    def test_modify_code_subject(self):
        for title in ("코드 수정", "Cursor 버그 수정", "VSCode 설정 반영 수정"):
            cid, val = self._match(title)
            self.assertEqual(cid, "coding", msg=title)
            self.assertEqual(val, "angle-brackets-solidus", msg=title)

    def test_modify_settings_and_shell_subject(self):
        cid, val = self._match("설정 수정")
        self.assertEqual(cid, "terminal_work")
        self.assertEqual(val, "command-line-rectangle")
        cid2, val2 = self._match("터미널 PATH 수정")
        self.assertEqual(cid2, "terminal_work")
        self.assertEqual(val2, "command-line-rectangle")

    def test_modify_written_record_defers_when_spreadsheet_anchor_present(self):
        cid, val = self._match("엑셀 보고서 수정")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    def test_modify_written_record_respects_compound_inner_material(self):
        # ``출장보고서`` 안의 ``보고서`` substring으로는 modify subject를 쓰지 않음
        out = find_best_visual_candidate_match("출장보고서 수정", self._cands)
        self.assertIsNone(out)

    def test_modify_action_alone_does_not_imply_document(self):
        out = find_best_visual_candidate_match("내용 수정", self._cands)
        self.assertIsNone(out)


class DocumentLifecycleExpansionTests(RecommenderSemanticTestCase):
    """Expanded ontology: request / approval / tracking plus document lifecycle leaves."""

    def test_reporting_is_hierarchical_communication_not_plain_review(self):
        cases = {
            "초안 팀장님 보고": ("document_reporting", "🗣️"),
            "예질 과장님 보고": ("document_reporting", "🗣️"),
            "시장님 보고자료 수정": ("document_reporting", "🗣️"),
            "최종안 보고": ("document_reporting", "🗣️"),
        }
        for title, (expect_cid, expect_visual) in cases.items():
            cid, val = self._match(title)
            self.assertEqual(cid, expect_cid, msg=title)
            self.assertEqual(val, expect_visual, msg=title)

    def test_report_document_subject_still_allows_plain_document_review(self):
        cid, val = self._match("보고서 확인")
        self.assertEqual(cid, "document_review")
        self.assertEqual(val, "📄")

    def test_request_uses_delegation_object_and_channel(self):
        cases = {
            "자료 요청": ("document_request", "📄"),
            "수정 요청": ("collaborative_request", "📝"),
            "업무 부탁": ("collaborative_request", "📝"),
            "회신 요청": ("mail_request", "📧"),
            "대면 요청": ("verbal_request", "🗣️"),
            "전화 요청": ("phone_request", "📞"),
            "메일 요청": ("mail_request", "📧"),
        }
        for title, (expect_cid, expect_visual) in cases.items():
            cid, val = self._match(title)
            self.assertEqual(cid, expect_cid, msg=title)
            self.assertEqual(val, expect_visual, msg=title)

    def test_approval_distinguishes_request_from_signoff(self):
        cases = {
            "결재 요청": ("approval_request", "📝"),
            "결재 받기": ("approval_request", "📝"),
            "승인 검토": ("approval_review", "📄"),
            "결재하기": ("document_signature", "signature"),
            "사인": ("document_signature", "signature"),
            "최종 승인": ("final_approval", "✅"),
        }
        for title, (expect_cid, expect_visual) in cases.items():
            cid, val = self._match(title)
            self.assertEqual(cid, expect_cid, msg=title)
            self.assertEqual(val, expect_visual, msg=title)

    def test_distribution_visual_tracks_distributed_object_identity(self):
        cases = {
            "주간보도자료 배포": ("press_distribution", "📰"),
            "책자 배포": ("booklet_distribution", "📔"),
            "책자 배부": ("booklet_distribution", "📔"),
            "앱 신규 버전 배포": ("app_release", "alien-pixel"),
            "일반 문서 배포": ("document_distribution", "📄"),
            "메일 배포": ("mail_distribution", "📧"),
        }
        for title, (expect_cid, expect_visual) in cases.items():
            cid, val = self._match(title)
            self.assertEqual(cid, expect_cid, msg=title)
            self.assertEqual(val, expect_visual, msg=title)

    def test_publication_distinguishes_action_from_context_object(self):
        cid, val = self._match("공지 게시")
        self.assertEqual(cid, "publication_announcement")
        self.assertEqual(val, "📌")

        cid2, val2 = self._match("게시판 등록")
        self.assertEqual(cid2, "publication_bulletin_update")
        self.assertEqual(val2, "📌")

        cid3, val3 = self._match("상단 고정공지")
        self.assertEqual(cid3, "publication_pinned_notice")
        self.assertEqual(val3, "📌")

        cid4, val4 = self._match("공고번호 확인")
        self.assertEqual(cid4, "document_review")
        self.assertEqual(val4, "📄")

        out = find_best_visual_candidate_match("게시판", self._cands)
        self.assertIsNone(out)

    def test_sharing_uses_channel_and_shared_object(self):
        cases = {
            "메일 공유": ("mail_sharing", "📧"),
            "정보 공유": ("information_sharing", "💡"),
            "부서 암호 공유": ("credential_sharing", "🔑"),
            "문서 공유": ("document_sharing", "📄"),
        }
        for title, (expect_cid, expect_visual) in cases.items():
            cid, val = self._match(title)
            self.assertEqual(cid, expect_cid, msg=title)
            self.assertEqual(val, expect_visual, msg=title)

    def test_tracking_is_status_awareness_not_plain_document_review(self):
        cases = {
            "신청 현황 확인": ("status_check", "📊"),
            "예산 집행 현황": ("budget_tracking", "💰"),
            "강사 배정 현황": ("allocation_tracking", "📋"),
            "진행 상황 체크": ("progress_monitoring", "🚦"),
            "응답 현황": ("response_tracking", "📬"),
        }
        for title, (expect_cid, expect_visual) in cases.items():
            cid, val = self._match(title)
            self.assertEqual(cid, expect_cid, msg=title)
            self.assertEqual(val, expect_visual, msg=title)


class OrganizeSemanticTests(RecommenderSemanticTestCase):
    """P3 organize pair + P6: (action=정리, subject=…) 와 meaning·인터페이스 충돌.

    ``organize`` ``PairResolution``이 폴더·회의실·알림·서면 자료 등에 대해 기대
    ``candidate_id``를 내고, 인터페이스 앵커가 있을 때 서면 subject organize가
    spreadsheet / survey / terminal meaning을 가리지 않는지 검증한다.
    """

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
        # compound 밖 ``엑셀`` + ``정리``: organize ``자료``가 스프레드시트 meaning에 밀리지 않음
        cid, val = self._match("교육 신청 현황 엑셀 정리")
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

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


class RankingContractTests(RecommenderSemanticTestCase):
    """P6 unified ranking: ``CandidateRow`` sort — pair tier vs meaning, wp vs dominance, overlap.

    ``rule_tier``(pair track)과 meaning track의 상대 우선, ``workflow_priority``와
    인터페이스 앵커 정렬, 복합 제목에서의 안정 선택(semantic overlap)을 검증한다.
    """

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

    def test_confirm_coordination_stable_under_person_and_meal_modifiers(self):
        # P3 confirm pair(row tier)이 점심·직책 modifier 위에 안정적으로 유지
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

    def test_organize_and_modify_both_present_modify_pair_rank_contract(self):
        # P3에서 organize·modify row가 같이 올라올 때 sort_secondary_wp 계약(modify=4 > organize=3)
        cid, val = self._match("회의자료 정리 및 수정")
        self.assertEqual(cid, "document_edit")
        self.assertEqual(val, "📝")


if __name__ == "__main__":
    unittest.main()
