"""Calibrate document_flow_stage labels against ground-truth JSON."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.data_loader import load_visual_candidates
from app.recommender import find_best_visual_candidate_match
from app.semantic_scoring import infer_document_flow_stages

GROUND_TRUTH = Path("tests/ambiguity/document_flow_ground_truth.json")


class DocumentFlowCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cands = load_visual_candidates()
        payload = json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))
        cls._labels = payload["labels"]

    def test_ground_truth_candidate_accuracy(self) -> None:
        mismatches: list[str] = []
        for row in self._labels:
            title = row["title"]
            expected = row["expected_candidate"]
            match = find_best_visual_candidate_match(title, self._cands)
            actual = match.candidate_id if match else None
            if actual != expected:
                mismatches.append(f"{title!r}: expected {expected}, got {actual}")
        self.assertEqual(mismatches, [])

    def test_ground_truth_stage_inference(self) -> None:
        mismatches: list[str] = []
        for row in self._labels:
            title = row["title"]
            expected_stage = row["expected_document_flow_stage"]
            inferred = infer_document_flow_stages(title)
            primary = next(iter(inferred), None)
            if primary != expected_stage:
                mismatches.append(
                    f"{title!r}: expected stage {expected_stage}, got {primary} ({inferred})"
                )
        self.assertEqual(mismatches, [])


if __name__ == "__main__":
    unittest.main()
