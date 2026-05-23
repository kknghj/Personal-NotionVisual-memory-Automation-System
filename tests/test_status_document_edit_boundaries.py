"""status_summary vs document_edit boundaries for 현황+작성 titles.

``작성`` is broad; status_summary should cover internal status materials while
formal document types (보고서, 공고문, 제출서류, 안내문) stay on document_edit
or sibling document-writing candidates.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

DOCUMENT_WRITE_TOP1_IDS = frozenset(
    {
        "document_edit",
        "publication_announcement",
        "document_submission",
        "submission_request",
    }
)
STATUS_SUMMARY_ALLOWED = frozenset({"status_summary", "document_edit"})
STATUS_SUMMARY_FORBIDDEN_TOP1 = frozenset(
    {"status_update", "status_sharing", "result_reporting"}
)


class StatusWritingBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_status_material_writing_allows_status_summary_in_top2(self) -> None:
        cases = (
            "민원 처리 현황 내부자료 작성",
            "주요사업 추진현황 주간회의 자료 작성",
            "부서별 업무 현황 자료 작성",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                top2 = top3[:2]
                self.assertTrue(
                    any(cid in STATUS_SUMMARY_ALLOWED for cid in top2),
                    msg=f"{title}: top2={top2}",
                )
                self.assertIn(top2[0], STATUS_SUMMARY_ALLOWED, msg=top2)
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)

    def test_formal_document_writing_prefers_document_candidates(self) -> None:
        cases = (
            "현황 보고서 작성",
            "현황 공고문 작성",
            "현황 제출서류 작성",
            "현황 안내문 작성",
        )
        for title in cases:
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertIn(top3[0], DOCUMENT_WRITE_TOP1_IDS, msg=top3)
                self.assertNotEqual(top3[0], "status_summary")
                self.assertTrue(
                    top3[0] != "status_summary",
                    msg=f"status_summary must not beat document write candidate: {top3}",
                )
                if "status_summary" in top3:
                    doc_rank = top3.index(top3[0])
                    summary_rank = top3.index("status_summary")
                    self.assertLess(doc_rank, summary_rank)
                for forbidden in STATUS_SUMMARY_FORBIDDEN_TOP1:
                    self.assertNotEqual(top3[0], forbidden, msg=top3)


if __name__ == "__main__":
    unittest.main()
