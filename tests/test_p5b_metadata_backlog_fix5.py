"""P5-B Fix 5 — metadata backlog catalog coverage (ids 74, 2, 21, 63, 87)."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

FIX5_NEW_IDS = frozenset(
    {
        "document_dispatch",
        "press_release_review",
        "drive_file_upload",
        "internal_meeting",
        "tax_invoice_review",
    }
)
PRESS_REVIEW_IDS = frozenset({"press_release_review", "press_distribution"})
NOTICE_TOP1_IDS = frozenset(
    {
        "notice_posting",
        "urgent_notice",
        "publication_pinned_notice",
    }
)


class P5BMetadataBacklogFix5CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_fix5_candidate_ids_exist(self) -> None:
        for cid in FIX5_NEW_IDS:
            with self.subTest(candidate_id=cid):
                self.assertIn(cid, self._cands)
                self.assertIn("workflow_priority", self._cands[cid])
                self.assertIn("semantic_metadata", self._cands[cid])

    def test_press_distribution_review_keywords_enriched(self) -> None:
        meanings = self._cands["press_distribution"]["meaning"]
        texts = {entry["text"] for entry in meanings}
        self.assertIn("보도자료확인", texts)
        self.assertIn("보도자료검토", texts)


class P5BMetadataBacklogFix5RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _match(self, title: str) -> tuple[str, str, str | None]:
        out = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(out, msg=title)
        assert out is not None
        visual = out.data.get("visual") or {}
        return out.candidate_id, visual.get("value", ""), visual.get("color")

    def _top_ids(self, title: str, n: int = 5) -> list[str]:
        return [r.candidate_id for r in rank_visual_candidate_rows(title, self._cands)[:n]]

    def test_fix5_id74_document_dispatch_title(self) -> None:
        cid, val, color = self._match("운영지침 공문 발송")
        self.assertEqual(cid, "document_dispatch")
        self.assertEqual(val, "document arrow right")
        self.assertEqual(color, "red")

    def test_fix5_id21_drive_upload_title(self) -> None:
        cid, val, color = self._match("재택 필요 자료 드라이브 업로드")
        self.assertEqual(cid, "drive_file_upload")
        self.assertEqual(val, "folder arrow up")
        self.assertEqual(color, "yellow")

    def test_fix5_id63_internal_meeting_title(self) -> None:
        cid, val, _ = self._match("과장 주재 주간회의 참석")
        self.assertEqual(cid, "internal_meeting")
        self.assertEqual(val, "people meeting")

    def test_fix5_id2_press_review_catalog_coverage(self) -> None:
        top_ids = self._top_ids("식생활교육 보도자료 확인", 3)
        self.assertIn("press_release_review", top_ids)
        cid, val, _ = self._match("식생활교육 보도자료 확인")
        self.assertIn(cid, PRESS_REVIEW_IDS | {"document_review"})
        if cid in PRESS_REVIEW_IDS:
            self.assertEqual(val, "📰")

    def test_fix5_id87_tax_invoice_catalog_coverage(self) -> None:
        top_ids = self._top_ids("세금계산서 검토", 3)
        self.assertIn("tax_invoice_review", top_ids)
        cid, val, color = self._match("세금계산서 검토")
        self.assertIn(cid, {"tax_invoice_review", "document_review"})
        if cid == "tax_invoice_review":
            self.assertEqual(val, "receipt")
            self.assertEqual(color, "gray")

    def test_fix5_press_distribution_regression(self) -> None:
        cid, val = self._match("보도자료 배포")[:2]
        self.assertEqual(cid, "press_distribution")
        self.assertEqual(val, "📰")

    def test_fix5_document_distribution_regression(self) -> None:
        cid, val = self._match("행사자료 송부")[:2]
        self.assertEqual(cid, "document_distribution")
        self.assertEqual(val, "📄")

    def test_fix5_folder_organization_regression(self) -> None:
        cid, val = self._match("드라이브 폴더 공유")[:2]
        self.assertIn(cid, {"document_sharing", "folder_organization"})
        if cid == "folder_organization":
            self.assertEqual(val, "📁")

    def test_fix5_meeting_regression(self) -> None:
        cid, val = self._match("센터 실무자 간담회 개최")[:2]
        self.assertEqual(cid, "meeting")
        self.assertEqual(val, "🤝")

    def test_fix5_training_attendance_regression(self) -> None:
        cid, _, _ = self._match("AI 교육 참석")
        self.assertEqual(cid, "training_session_attendance")

    def test_fix5_spreadsheet_regression(self) -> None:
        cid, val = self._match("엑셀 자료 정리")[:2]
        self.assertEqual(cid, "spreadsheet_work")
        self.assertEqual(val, "grid-rectangle-2x3")

    def test_fix5_pinned_notice_regression(self) -> None:
        cid, _, _ = self._match("채팅방 공지 등록")
        self.assertIn(cid, NOTICE_TOP1_IDS)


if __name__ == "__main__":
    unittest.main()
