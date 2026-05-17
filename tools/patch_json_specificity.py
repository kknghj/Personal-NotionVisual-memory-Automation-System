"""sample_cases / visual_candidates에 specificity 필드를 반영."""

from __future__ import annotations

import json

from app.data_loader import DATA_DIR
from app.specificity import infer_specificity, interface_dominance, workflow_specificity_for_sample_case


def patch_visual_candidates() -> None:
    path = DATA_DIR / "visual_candidates.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict = {
        "meta": {
            "schema_version": 3,
            "meaning_format": {
                "text": "string",
                "specificity": "int (1=일반 행동, 2=업무 개념·중간, 3=인터페이스·도구·채널)",
                "interface_dominance": "int (1=키워드에 interface anchor 부분문자열 포함)",
            },
        }
    }
    for key, val in raw.items():
        if key == "meta":
            continue
        if not isinstance(val, dict):
            out[key] = val
            continue

        meanings = val.get("meaning")
        new_meanings: list = []
        if isinstance(meanings, list):
            for item in meanings:
                text: str | None = None
                if isinstance(item, dict):
                    raw = item.get("text") or item.get("term") or item.get("value")
                    if isinstance(raw, str):
                        text = raw.strip()
                elif isinstance(item, str):
                    text = item.strip()
                if text:
                    new_meanings.append(
                        {
                            "text": text,
                            "specificity": infer_specificity(text),
                            "interface_dominance": interface_dominance(text),
                        }
                    )
        nv = {**val, "meaning": new_meanings}
        out[key] = nv

    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_sample_cases() -> None:
    path = DATA_DIR / "sample_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    for case in cases:
        if isinstance(case, dict):
            case["workflow_specificity"] = workflow_specificity_for_sample_case(case)
    path.write_text(json.dumps(cases, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")


def main() -> None:
    patch_visual_candidates()
    patch_sample_cases()


if __name__ == "__main__":
    main()
