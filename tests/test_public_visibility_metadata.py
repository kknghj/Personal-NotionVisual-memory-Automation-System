"""Public visibility as metadata — not a standalone action candidate axis."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match
from app.semantic_scoring import infer_title_semantic_signals

PUBLICATION_WITH_PUBLIC_VISIBILITY = frozenset(
    {
        "publication_posting",
        "public_posting",
        "publication_announcement",
        "notice_posting",
        "publication_bulletin_update",
        "publication_pinned_notice",
        "press_distribution",
    }
)


class PublicVisibilityMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_no_standalone_public_candidate_id(self) -> None:
        self.assertNotIn("public", self._cands)

    def test_public_posting_is_publication_variant_with_visibility_metadata(self) -> None:
        meta = self._cands["public_posting"].get("semantic_metadata") or {}
        self.assertEqual(meta.get("visibility"), "public")
        self.assertEqual(meta.get("publish_distribute"), "posting")
        self.assertIn("web_publication", meta.get("workflow_fit", []))

    def test_publication_candidates_expose_public_visibility(self) -> None:
        for cid in (
            "publication_posting",
            "publication_announcement",
            "notice_posting",
        ):
            with self.subTest(candidate=cid):
                meta = self._cands[cid].get("semantic_metadata") or {}
                self.assertEqual(meta.get("visibility"), "public")

    def test_title_public_signal_is_visibility_metadata_not_candidate(self) -> None:
        for title in ("홈페이지 공개 게시", "대외 공개 게시", "공개 모집 공고"):
            with self.subTest(title=title):
                signals = infer_title_semantic_signals(title)
                self.assertIn("public", signals.get("visibility", set()))

    def test_public_visibility_titles_route_to_publication_family(self) -> None:
        for title in ("홈페이지 공개 게시", "대외 공개 게시"):
            with self.subTest(title=title):
                match = find_best_visual_candidate_match(title, self._cands)
                self.assertIsNotNone(match)
                assert match is not None
                self.assertIn(match.candidate_id, PUBLICATION_WITH_PUBLIC_VISIBILITY)


if __name__ == "__main__":
    unittest.main()
