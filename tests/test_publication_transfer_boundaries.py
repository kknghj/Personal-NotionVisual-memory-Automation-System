"""Transfer/distribute verbs vs document_edit create_edit boundary.

``전달``/``송부``/``발송`` without ``작성``/``기안`` must not let ``document_edit``
semantic (create_edit) beat review or distribution candidates.
``공문 전달`` regression: top1 stays ``document_review`` (not collateral document_edit).
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match, rank_visual_candidate_rows

DOCUMENT_EDIT_FORBIDDEN_TOP1 = frozenset({"document_edit"})
TRANSFER_EXPECTED = {
    "공문 전달": "document_review",
    "공문 송부": "document_distribution",
    "공문 발송": "document_distribution",
}


class PublicationTransferBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        self.assertGreater(len(rows), 0, msg=title)
        return [row.candidate_id for row in rows[:n]]

    def test_transfer_titles_do_not_promote_document_edit_top1(self) -> None:
        for title, expected in TRANSFER_EXPECTED.items():
            with self.subTest(title=title):
                top3 = self._top_ids(title, 3)
                self.assertEqual(top3[0], expected, msg=top3)
                self.assertNotIn(top3[0], DOCUMENT_EDIT_FORBIDDEN_TOP1)
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertEqual(match.candidate_id, expected)

    def test_gongmun_jeondal_regression_document_review(self) -> None:
        """Collateral from document_edit metadata — intentionally reverted."""
        top3 = self._top_ids("공문 전달", 3)
        self.assertEqual(top3[0], "document_review", msg=top3)
        if "document_edit" in top3:
            self.assertLess(top3.index("document_review"), top3.index("document_edit"))


if __name__ == "__main__":
    unittest.main()
