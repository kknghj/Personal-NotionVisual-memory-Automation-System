"""Semantic metadata contracts for visual candidates."""

from __future__ import annotations

import unittest

from app.data_loader import load_visual_candidates


class DistributionSemanticMetadataTests(unittest.TestCase):
    """Distribution candidates expose scoring features without changing retrieval fields."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()

    def test_distribution_candidates_have_expected_semantic_metadata(self) -> None:
        expected = {
            "press_distribution": {
                "workflow_fit": ["broadcast_notice", "document"],
                "object_type": "document",
                "interaction_mode": "publish_distribute",
                "visibility": "public",
                "tone": "formal",
                "publish_distribute": "distribution",
            },
            "booklet_distribution": {
                "workflow_fit": ["document"],
                "object_type": "document",
                "interaction_mode": "publish_distribute",
                "visibility": "internal",
                "tone": "neutral",
                "publish_distribute": "distribution",
            },
            "app_release": {
                "workflow_fit": ["engineering"],
                "object_type": "code",
                "interaction_mode": "publish_distribute",
                "visibility": "public",
                "tone": "neutral",
                "publish_distribute": "distribution",
            },
            "document_distribution": {
                "workflow_fit": ["document"],
                "object_type": "document",
                "interaction_mode": "publish_distribute",
                "visibility": "internal",
                "tone": "formal",
                "publish_distribute": "distribution",
            },
            "mail_distribution": {
                "workflow_fit": ["broadcast_notice", "communication"],
                "object_type": "message",
                "interaction_mode": "publish_distribute",
                "visibility": "internal",
                "tone": "formal",
                "publish_distribute": "distribution",
            },
        }

        for candidate_id, metadata in expected.items():
            with self.subTest(candidate_id=candidate_id):
                self.assertEqual(self._cands[candidate_id]["semantic_metadata"], metadata)
                self.assertNotEqual(metadata["workflow_fit"][0], "communication")

    def test_distribution_metadata_distinguishes_sharing_and_publication(self) -> None:
        document_sharing = self._cands["document_sharing"]["semantic_metadata"]
        document_distribution = self._cands["document_distribution"]["semantic_metadata"]
        mail_sharing = self._cands["mail_sharing"]["semantic_metadata"]
        mail_distribution = self._cands["mail_distribution"]["semantic_metadata"]
        publication = self._cands["publication_posting"]["semantic_metadata"]

        self.assertEqual(document_sharing["interaction_mode"], "send_share")
        self.assertEqual(document_distribution["interaction_mode"], "publish_distribute")
        self.assertEqual(mail_sharing["workflow_fit"][0], "communication")
        self.assertEqual(mail_distribution["workflow_fit"][0], "broadcast_notice")
        self.assertEqual(publication["visibility"], "public")
        self.assertEqual(publication["object_type"], "notice")
        self.assertEqual(publication["publish_distribute"], "posting")
        self.assertEqual(document_distribution["object_type"], "document")
        self.assertEqual(mail_distribution["object_type"], "message")
        self.assertEqual(document_distribution["publish_distribute"], "distribution")


if __name__ == "__main__":
    unittest.main()
