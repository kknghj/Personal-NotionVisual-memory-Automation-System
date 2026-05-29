"""JSON 데이터 로딩. 모든 데이터셋은 ``project/data/*.json`` 단일 경로를 사용한다.

제품·철학 마크다운은 ``project/docs/``에서 관리한다(에이전트 축약 규칙은 ``.cursor/rules/``).

권장 디렉터리 구조::
    data/
        sample_cases.json       # 제목 완전 일치용 예시
        visual_candidates.json  # meaning·후보 정의
        pair_rules.json         # prep / confirm / organize / modify 선언 규칙
        feedback_log.json       # (선택) 사용자 피드백·학습 로그; 배열 JSON 등

런타임·스크립트는 루트에 동일 파일을 두지 말고 ``data/``만 갱신한다.
"""

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def data_dir() -> Path:
    """프로젝트 ``data/`` 디렉터리 (JSON 단일 소스)."""
    return DATA_DIR


def sample_cases_path() -> Path:
    return DATA_DIR / "sample_cases.json"


def visual_candidates_path() -> Path:
    return DATA_DIR / "visual_candidates.json"


def pair_rules_path() -> Path:
    return DATA_DIR / "pair_rules.json"


def feedback_log_path() -> Path:
    """향후 피드백 적재용 경로. 파일이 없을 수 있음."""
    return DATA_DIR / "feedback_log.json"


_DEPRECATED_SAMPLE_CASE_KEYS = frozenset({"sample_case_schema", "recommended_updates"})


def validate_flat_sample_cases(raw: object) -> list[dict[str, Any]]:
    """``sample_cases.json`` 루트가 평면 케이스 배열인지 검사. 실패 시 ``ValueError``."""
    if not isinstance(raw, list):
        raise ValueError(
            "data/sample_cases.json must be a JSON array at the root "
            f"(list of case objects), got {type(raw).__name__}. "
            "See docs/sample_cases_schema.md."
        )
    for i, case in enumerate(raw):
        if not isinstance(case, dict):
            raise ValueError(
                f"data/sample_cases.json: item [{i}] must be a JSON object, "
                f"got {type(case).__name__}. See docs/sample_cases_schema.md."
            )
        if _DEPRECATED_SAMPLE_CASE_KEYS & case.keys():
            raise ValueError(
                "data/sample_cases.json: deprecated wrapper shape "
                "(keys sample_case_schema / recommended_updates). "
                "Root must be a flat array of "
                '[{"title": "...", "visual": {...}}, ...]. '
                "See docs/sample_cases_schema.md."
            )
        title = case.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(
                f'data/sample_cases.json: item [{i}] must have a non-empty string "title".'
            )
        visual = case.get("visual")
        if not isinstance(visual, dict):
            raise ValueError(
                f'data/sample_cases.json: item [{i}] (title={title!r}) must have an object "visual".'
            )
        v_type = visual.get("type")
        v_value = visual.get("value")
        if v_type not in ("emoji", "notion_icon"):
            raise ValueError(
                f'data/sample_cases.json: item [{i}] (title={title!r}) '
                f'"visual.type" must be "emoji" or "notion_icon", got {v_type!r}.'
            )
        if not isinstance(v_value, str) or not v_value.strip():
            raise ValueError(
                f'data/sample_cases.json: item [{i}] (title={title!r}) '
                f'must have a non-empty string "visual.value".'
            )
    return raw


def load_sample_cases() -> list[dict[str, Any]]:
    path = sample_cases_path()
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return validate_flat_sample_cases(raw)


def load_visual_candidates() -> dict[str, Any]:
    path = visual_candidates_path()
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_pair_rules() -> dict[str, Any]:
    path = pair_rules_path()
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_feedback_log() -> list[dict[str, Any]]:
    """Load feedback log array.

    Missing, empty, or whitespace-only file → ``[]``.
    Invalid JSON or non-array root → ``ValueError``.
    """
    path = feedback_log_path()
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"data/feedback_log.json: invalid JSON: {exc}"
        ) from exc
    if not isinstance(raw, list):
        raise ValueError(
            "data/feedback_log.json must be a JSON array at the root "
            f"(list of event objects), got {type(raw).__name__}."
        )
    return raw


def append_feedback_log_entry(entry: dict[str, Any]) -> None:
    """Append one feedback event and rewrite ``data/feedback_log.json``."""
    path = feedback_log_path()
    log = load_feedback_log()
    log.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
