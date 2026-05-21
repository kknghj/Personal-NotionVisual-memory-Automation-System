"""Merge reporting_current_state_manifest titles into ambiguity_test_set.json."""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path("tests/ambiguity/reporting_current_state_manifest.json")
TEST_SET = Path("tests/ambiguity/ambiguity_test_set.json")


def _collect_titles(manifest: dict) -> list[str]:
    titles: list[str] = []
    for key in (
        "reporting_stage_cases",
        "status_ambiguity_cases",
        "result_lifecycle_cases",
        "intentionally_ambiguous_cases",
    ):
        for item in manifest.get(key, []):
            if isinstance(item, dict) and isinstance(item.get("title"), str):
                titles.append(item["title"].strip())
    return titles


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    existing = json.loads(TEST_SET.read_text(encoding="utf-8"))
    seen = {item["title"].strip() for item in existing if isinstance(item, dict)}
    added = 0
    for title in _collect_titles(manifest):
        if title in seen:
            continue
        existing.append({"title": title, "case_group": "reporting_current_state"})
        seen.add(title)
        added += 1
    TEST_SET.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"added": added, "total": len(existing)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
