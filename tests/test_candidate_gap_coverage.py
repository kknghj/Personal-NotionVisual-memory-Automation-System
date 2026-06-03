"""Coverage for candidate_gap patch: new candidates and keyword extensions."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match


class CandidateGapCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_new_candidate_ids_exist(self) -> None:
        for cid in (
            "hr_consultation",
            "creative_production",
            "handover",
            "business_card_order",
            "waste_disposal",
        ):
            with self.subTest(candidate_id=cid):
                self.assertIn(cid, self._cands)
                self.assertIn("workflow_priority", self._cands[cid])

    def test_extension_keywords_present(self) -> None:
        def texts(cid: str) -> set[str]:
            return {m["text"] for m in self._cands[cid]["meaning"] if isinstance(m, dict)}

        self.assertIn("초근결재", texts("system_work"))
        self.assertIn("고민", texts("brainstorming"))
        self.assertIn("민원응대", texts("phone_call"))
        self.assertIn("종료일", texts("work_calendar_organization"))
        self.assertIn("분리수거", texts("waste_disposal"))

    def test_creative_production_excludes_video_keywords(self) -> None:
        meanings = {
            m["text"]
            for m in self._cands["creative_production"]["meaning"]
            if isinstance(m, dict)
        }
        for banned in ("영상", "영상제작", "촬영", "홍보영상", "제작"):
            self.assertNotIn(banned, meanings)


class CandidateGapRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _match(self, title: str) -> tuple[str, str]:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out, msg=title)
        assert out is not None
        visual = out.data.get("visual") or {}
        return out.candidate_id, visual.get("value", "")

    def test_override_gap_titles_resolve(self) -> None:
        cases = {
            "인사 상담": ("hr_consultation", "👥"),
            "식생활교육 배너, 포스터 제작": ("creative_production", "🎨"),
            "업무 인수인계": ("handover", "dot arrow right arc"),
            "신규 명함 제작 신청": ("business_card_order", "identification card"),
            "알뜰폰 할인 종료일": ("work_calendar_organization", "📅"),
            "생활폐기물 처리": ("waste_disposal", "🚮"),
            "분리수거": ("waste_disposal", "🚮"),
            "초근 결재": ("system_work", "💻"),
            "합동점검 예질 질문 고민": ("brainstorming", "🧠"),
            "식생활교육 신청 민원 응대": ("phone_call", "📞"),
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(self._match(title), expected)

    def test_video_submission_not_creative_production(self) -> None:
        cid, _ = self._match("창의 정책 홍보 영상 제출")
        self.assertNotEqual(cid, "creative_production")

    def test_office_cleanup_still_wins_for_cleaning(self) -> None:
        cid, val = self._match("사무실 정리")
        self.assertEqual(cid, "office_cleanup")
        self.assertEqual(val, "person-trash-can")

    def test_civic_complaint_answer_stays_ambiguous_channel(self) -> None:
        """민원 답변은 전화·문서·시스템 모두 가능 — 단일 채널 강매칭 회피."""
        cid, val = self._match("식생활교육 민원 답변")
        self.assertIn(cid, {"phone_call", "document_edit", "system_work", "collaborative_request"})
        if cid == "phone_call":
            self.assertEqual(val, "📞")


if __name__ == "__main__":
    unittest.main()
