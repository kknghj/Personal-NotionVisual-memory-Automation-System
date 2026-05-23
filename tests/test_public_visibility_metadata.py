"""``public`` as visibility/audience metadata — not a standalone candidate id.

Publication and distribution candidates carry ``visibility=public`` where appropriate;
titles with ``공개`` route to publication-family candidates via posting semantics.
"""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import rank_visual_candidate_rows
from app.semantic_scoring import infer_title_semantic_signals

PUBLICATION_FAMILY_IDS = frozenset(
    {
        "publication_posting",
        "public_posting",
        "publication_announcement",
        "notice_posting",
        "publication_bulletin_update",
        "publication_pinned_notice",
    }
)
PUBLIC_VISIBILITY_CANDIDATES = frozenset(
    {
        "publication_posting",
        "public_posting",
        "publication_announcement",
        "notice_posting",
        "publication_bulletin_update",
        "publication_pinned_notice",
        "press_distribution",
        "app_release",
    }
)


class PublicVisibilityMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def _top_ids(self, title: str, n: int = 3) -> list[str]:
        rows = rank_visual_candidate_rows(title, self._cands)
        if not rows:
            return []
        return [row.candidate_id for row in rows[:n]]

    def test_no_standalone_public_candidate_id(self) -> None:
        self.assertNotIn("public", self._cands)
        self.assertIn("public_posting", self._cands)

    def test_publication_family_exposes_visibility_public_metadata(self) -> None:
        for candidate_id in PUBLIC_VISIBILITY_CANDIDATES:
            with self.subTest(candidate_id=candidate_id):
                metadata = self._cands[candidate_id].get("semantic_metadata") or {}
                self.assertEqual(metadata.get("visibility"), "public")

    def test_public_posting_carries_web_publication_fit(self) -> None:
        metadata = self._cands["public_posting"]["semantic_metadata"]
        self.assertIn("web_publication", metadata["workflow_fit"])

    def test_title_public_signal_is_visibility_not_candidate(self) -> None:
        signals = infer_title_semantic_signals("정책자료 공개 게시")
        self.assertIn("public", signals.get("visibility", set()))
        top3 = self._top_ids("정책자료 공개 게시", 3)
        self.assertIn(top3[0], PUBLICATION_FAMILY_IDS, msg=top3)
        self.assertNotEqual(top3[0], "public")

    def test_bare_public_title_has_no_match_or_publication_family_only(self) -> None:
        """``공개`` alone is too weak for a dedicated candidate — visibility signal only."""
        signals = infer_title_semantic_signals("공개")
        self.assertIn("public", signals.get("visibility", set()))
        top = self._top_ids("공개", 1)
        if top:
            self.assertNotEqual(top[0], "public")
        rows = rank_visual_candidate_rows("공개", self._cands)
        self.assertEqual(len(rows), 0)

    def test_external_public_posting_routes_to_public_posting(self) -> None:
        top3 = self._top_ids("대외 공개 게시", 3)
        self.assertEqual(top3[0], "public_posting", msg=top3)


if __name__ == "__main__":
    unittest.main()
