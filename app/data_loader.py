import json
from pathlib import Path
from typing import Any


def sample_cases_path() -> Path:
    return Path(__file__).resolve().parent.parent / "sample_cases.json"


def visual_candidates_path() -> Path:
    return Path(__file__).resolve().parent.parent / "visual_candidates.json"


def pair_rules_path() -> Path:
    return Path(__file__).resolve().parent.parent / "pair_rules.json"


def load_sample_cases() -> list[dict[str, Any]]:
    path = sample_cases_path()
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_visual_candidates() -> dict[str, Any]:
    path = visual_candidates_path()
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_pair_rules() -> dict[str, Any]:
    path = pair_rules_path()
    with path.open(encoding="utf-8") as f:
        return json.load(f)
