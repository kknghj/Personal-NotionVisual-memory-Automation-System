# P5-A Override Pattern Analysis

`tools/analyze_override_patterns.py`가 `data/override_examples.json`(Notion 수동 feedback)을 읽어 override 사례를 분류합니다.

P5-B(후속 튜닝·스냅샷)를 보기 전에, 출력 필드 **`primary_pattern`** 과 **`gap_type`** 의 기준 시점이 다르다는 점을 먼저 이해해야 합니다.

## primary_pattern vs gap_type

| | `primary_pattern` | `gap_type` |
| --- | --- | --- |
| **기준 시점** | feedback 기록 당시(과거) | 분석 실행 **현재** |
| **입력** | `recommended_visual`, `final_visual`, `note`, `title` | 현재 `visual_candidates.json` + recommendation engine + 위 feedback 필드 |
| **질문** | 사용자는 **왜** 추천을 바꿨는가? | **지금** 엔진이 왜 이 사례를 맞추지 못하는가? |
| **없음(null)** | override만 분류(accepted는 `unknown` 등) | gap 없음 = accepted이거나, 현재 엔진·카탈로그가 final과 정합 |

JSON 메타데이터:

```json
{
  "analysis_basis": {
    "primary_pattern": "historical_feedback",
    "gap_type": "current_engine"
  }
}
```

## primary_pattern

수동 feedback에 적힌 **추천 당시** 값과 **사용자 최종 선택**의 차이를 설명합니다.

```text
추천 당시  recommended_visual
        ↓  (사용자 override)
최종      final_visual
```

대표 패턴:

- `candidate_gap` — 추천이 `없음`이었거나, note에 후보 부재 힌트
- `channel_priority` — 문서·회의 맥락보다 메일·전화 등 **채널**을 택함
- `interface_priority` — 행정 내부 시스템·UI·등록·결재 등 **인터페이스** 우선
- `object_priority` — 보도자료·영상·배너 등 **대상물** 우선
- `action_priority` — 제목/ note의 **실제 행동** 우선

## gap_type

현재 카탈로그·키워드·metadata·엔진으로 제목을 **다시 추천**해 보고, final visual과의 갭을 분류합니다(override만, accepted는 `null`).

| `gap_type` | 의미 |
| --- | --- |
| `candidate_gap` | final에 맞는 visual **candidate 자체**가 카탈로그에 없음 |
| `keyword_gap` | candidate는 있으나 meaning **키워드** 부족으로 매칭 실패 |
| `metadata_gap` | 매칭은 되나 visual·usage·semantic metadata가 final과 어긋남 |
| `ambiguous_channel` | 전화·문서·시스템 등 **여러 채널**이 동시에 가능 |
| `null` | 현재 기준 갭 없음(또는 accepted) |

## 혼동하기 쉬운 조합: `candidate_gap` + `gap_type=null`

**분석 오류가 아닙니다.** 흔히 **과거에는 문제였으나 현재는 해결된 사례**입니다.

### 예: 인사 상담

**feedback 당시**

```text
title: 인사 상담
recommended_visual: 없음
final_visual: 👥
→ primary_pattern = candidate_gap
```

당시에는 추천 후보가 없어 사용자가 👥를 직접 선택한 상황입니다.

**`hr_consultation` 등 패치 이후(현재 엔진)**

```text
인사 상담 → hr_consultation → 👥
→ gap_type = null
```

카탈로그·키워드가 보강되어 **지금** 돌리면 엔진이 final과 맞출 수 있습니다.  
그런데 `primary_pattern`은 여전히 `candidate_gap`입니다 — **과거 feedback 스냅샷**을 그대로 반영하기 때문입니다.

### 다른 예시 패턴

| 제목 | `primary_pattern` (과거) | `gap_type` (현재) | 해석 |
| --- | --- | --- | --- |
| 인사 상담 | `candidate_gap` | `null` | 후보 추가로 **해결됨** |
| 식생활교육 배너, 포스터 제작 | `candidate_gap` | `null` | `creative_production` 추가 후 해결 |
| 초근 결재 | `candidate_gap` | `null` | `system_work` 키워드 확장 후 해결 |
| 식생활교육 민원 답변 | `candidate_gap` | `ambiguous_channel` | 과거엔 없음; 지금도 **다채널** ambiguity |
| 보도자료 초안 검토 요청 | `channel_priority` | `metadata_gap` | 과거엔 채널 우선; 지금은 엔진이 문서 쪽으로 매칭 |

## 실행

```bash
python tools/analyze_override_patterns.py
python tools/analyze_override_patterns.py --json
```

Markdown·JSON 출력 상단에 동일한 해석 노트가 포함됩니다.

## P5-B에서의 활용

- **`primary_pattern` 높음 + `gap_type` null 다수** → 이미 패치된 override; regression·스냅샷으로 **재발 방지** 확인
- **`gap_type` 잔존** → 아직 catalog/keyword/metadata 작업 대상
- **`ambiguous_channel`** → scoring 강화보다 note·confidence·다채널 정책 검토

관련 구현: `tools/analyze_override_patterns.py`, 테스트 `tests/test_analyze_override_patterns.py`.
