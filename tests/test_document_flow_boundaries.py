"""Document flow stage boundaries: submit / request / review / approve / complete."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows
from app.semantic_scoring import infer_document_flow_stages


class DocumentFlowBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _cid(self, title: str) -> str:
        match = find_best_visual_candidate_match(title, self._cands)
        self.assertIsNotNone(match, msg=title)
        assert match is not None
        return match.candidate_id

    def test_submit_titles_prefer_document_submission(self) -> None:
        for title in ("자료 제출", "실적자료 제출", "추진현황 제출", "활동결과 제출"):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "document_submission")
                self.assertEqual(infer_document_flow_stages(title), {"submit"})

    def test_submission_request_titles(self) -> None:
        for title in ("자료 제출 요청", "참가폼 제출 요청", "서류 제출 요청"):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "submission_request")
                self.assertEqual(infer_document_flow_stages(title), {"request"})

    def test_revision_request_titles(self) -> None:
        self.assertEqual(self._cid("자료 제출 보완 요청"), "collaborative_request")
        self.assertEqual(infer_document_flow_stages("자료 제출 보완 요청"), {"request"})

    def test_review_request_and_review_action_titles(self) -> None:
        self.assertEqual(self._cid("검토 요청"), "review_request")
        self.assertEqual(self._cid("자료 제출 검토"), "approval_review")
        self.assertEqual(self._cid("제출 자료 검토"), "approval_review")
        self.assertEqual(infer_document_flow_stages("자료 제출 검토"), {"review"})

    def test_approval_request_titles(self) -> None:
        for title in ("승인 요청", "결재 요청", "공문 결재 요청"):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "approval_request")
                self.assertEqual(infer_document_flow_stages(title), {"request"})

    def test_approval_outcome_titles(self) -> None:
        for title in (
            "자료 제출 승인",
            "자료 제출 후 승인",
            "신청 승인",
            "최종 승인",
        ):
            with self.subTest(title=title):
                self.assertEqual(self._cid(title), "final_approval")

    def test_submit_request_pair_do_not_tie_on_semantic_bonus(self) -> None:
        rows = rank_visual_candidate_rows("자료 제출 요청", self._cands)[:2]
        self.assertEqual(rows[0].candidate_id, "submission_request")
        self.assertNotEqual(rows[0].candidate_id, rows[1].candidate_id)

    def test_bare_submit_does_not_route_to_status_update(self) -> None:
        for title in ("보험 가입현황 제출", "비상소집 응소자 현황 제출"):
            with self.subTest(title=title):
                cid = self._cid(title)
                self.assertIn(cid, {"document_submission", "document_edit"})
                self.assertNotEqual(cid, "status_update")


class DocumentFlowMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_document_submission_metadata_is_submit_not_request(self) -> None:
        meta = self._cands["document_submission"]["semantic_metadata"]
        self.assertEqual(meta["interaction_mode"], "submit")
        self.assertEqual(meta["document_flow_stage"], ["submit"])
        self.assertNotIn("request_approval", meta)

    def test_approval_chain_exposes_document_flow_stage(self) -> None:
        expected = {
            "submission_request": ["request"],
            "document_submission": ["submit"],
            "review_request": ["request"],
            "approval_request": ["request"],
            "approval_review": ["review"],
            "document_signature": ["approve"],
            "final_approval": ["approve", "complete"],
            "collaborative_request": ["request"],
        }
        for candidate_id, stages in expected.items():
            with self.subTest(candidate_id=candidate_id):
                meta = self._cands[candidate_id]["semantic_metadata"]
                self.assertEqual(meta["document_flow_stage"], stages)


if __name__ == "__main__":
    unittest.main()
