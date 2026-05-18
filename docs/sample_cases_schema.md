# `data/sample_cases.json` 스키마 (런타임)

런타임 exact match용 `data/sample_cases.json`은 **루트가 케이스 객체의 배열**이어야 합니다.

```json
[
  {
    "title": "string",
    "visual": {
      "type": "emoji | notion_icon",
      "value": "string",
      "color": "optional string"
    },
    "workflow_type": "string",
    "pair_context": {
      "action": "string",
      "subject": "string"
    },
    "modifier": ["string"],
    "focus": "string",
    "interface_memory": ["string"],
    "cognitive_mode": ["string"],
    "reason": "string",
    "workflow_anchor_density": 1
  }
]
```

## 필수 필드 (exact match 경로)

- **`title`**: 요청 제목과 `strip()` 후 문자열이 **완전히 같을** 때 해당 케이스가 선택됩니다.
- **`visual`**: `app.models.Visual`과 호환되는 객체 (`type`, `value`, 선택 `color`).

### exact match의 범위

현재 exact match는
`title.strip()` 기반의 완전 일치만 사용합니다.

즉 아래 semantic pipeline 기능은
exact layer에서는 수행되지 않습니다.

- canonical normalization
- 공백 제거 canonical 비교
- modifier suppression
- pair interpretation
- interface dominance
- ranking

이 기능들은
sample_cases exact match 이후의 semantic pipeline에서만 수행됩니다.

그 외 필드(`workflow_type`, `pair_context`, …)는 메타·학습·문서용으로 두어도 되며, `app/main.py`의 exact match 응답에서는 주로 `visual`과 `reason`·`workflow_anchor_density`만 쓰입니다.

## 금지: 래퍼 루트

다음과 같은 **구버전 래퍼**는 사용하지 않습니다.

- 루트 배열 한 요소 안에 `sample_case_schema` + `recommended_updates`만 두는 형태

설명용 스키마는 이 문서(`docs/sample_cases_schema.md`)에만 두고, JSON 루트는 항상 평면 케이스 배열로 유지합니다.

## 로더 검증

`app.data_loader.load_sample_cases()`는 JSON을 읽은 뒤 루트가 배열인지, 각 원소에 문자열 `title`과 객체 `visual`이 있는지 검사합니다. 구조가 맞지 않으면 `ValueError`로 실패합니다.
