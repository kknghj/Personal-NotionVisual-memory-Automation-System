# Semantic metadata schema

`semantic_metadata`는 기존 `visual_candidates.json` 후보 위에 붙는 얇은 의미 메타데이터 레이어다. 현재 retrieval 중심 구조(`meaning`, pair rules, `workflow_priority`, interface dominance)는 유지하고, 후보가 어떤 workflow category·object·interaction 성격을 가지는지 추천 엔진이 구조적으로 읽을 수 있게 한다.

이 문서는 최소 schema만 정의한다. `workflow_ontology.md`의 전체 계층을 그대로 복제하지 않고, category inference와 scoring에 바로 쓸 수 있는 필드만 둔다.

## 1. 위치와 기본 형태

권장 위치는 각 visual candidate의 인라인 필드다.

```json
{
  "document_review": {
    "visual": {
      "type": "emoji",
      "value": "📄"
    },
    "workflow_priority": 2,
    "meaning": [
      {
        "text": "보고서",
        "workflow_resolution": 1,
        "interface_dominance": 0
      }
    ],
    "interface_memory": ["문서 열람 화면"],
    "usage_context": ["보고서 확인", "자료 검토"],
    "semantic_metadata": {
      "workflow_fit": ["document"],
      "object_type": "document",
      "interaction_mode": "review_confirm",
      "visibility": "internal",
      "tone": "formal"
    }
  }
}
```

`semantic_metadata`는 retrieval hit를 만들지 않는다. 후보 row가 P3 pair 또는 P4 meaning으로 생성된 뒤, P6 ranking 또는 이후 category-aware scoring에서 tie-break, penalty, explanation, feedback aggregation에 사용할 수 있는 후보 속성이다.

## 2. 필드 정의

| 필드 | 타입 | 필수 | 목적 |
| --- | --- | --- | --- |
| `workflow_fit` | `array<string enum>` | 예 | 후보가 걸치는 workflow category 목록. 첫 번째 값을 primary로 해석한다. |
| `object_type` | `string enum` | 예 | 사용자가 실제로 다루는 대상의 종류. 같은 action이라도 문서·표·시스템·공간을 구분한다. |
| `interaction_mode` | `string enum` | 예 | 후보가 대표하는 행동 방식. scoring에서 제목의 action 신호와 후보 성격을 맞추는 축이다. |
| `visibility` | `string enum` | 예 | 결과물이나 행동이 노출되는 범위. 내부 처리, 조직 공지, 외부 공개를 구분한다. |
| `tone` | `string enum` | 예 | 후보가 암시하는 업무 분위기. urgent/formal/sensitive 같은 scoring prior에 사용한다. |

### 타입 계약

```ts
type SemanticMetadata = {
  workflow_fit: WorkflowCategory[];
  object_type: ObjectType;
  interaction_mode: InteractionMode;
  visibility: Visibility;
  tone: Tone;
};
```

`workflow_fit`은 비어 있으면 안 된다. 첫 번째 원소가 primary fit이고, 두 번째 이후는 같은 후보가 함께 걸치는 secondary fit이다. 중복 값은 넣지 않는다. sub-workflow(`document.review` 등)는 이 최소 schema에 넣지 않고, 필요하면 ontology 문서나 별도 후속 필드에서 다룬다.

## 3. Enum 후보

### `workflow_fit`

값은 `workflow_ontology.md`의 top-level category를 그대로 쓴다. 예:

```json
["broadcast_notice", "communication", "document"]
```

위 예시는 `broadcast_notice`를 primary로 해석하고, `communication`과 `document`도 같은 후보의 fit으로 scoring에 사용할 수 있다는 뜻이다. enum 후보:

```json
[
  "communication",
  "notification_ops",
  "document",
  "tabular_data",
  "engineering",
  "system_admin",
  "time_scheduling",
  "digital_storage",
  "meeting_collaboration",
  "education",
  "event_social",
  "food_logistics",
  "facility_physical",
  "mobility",
  "web_publication",
  "broadcast_notice",
  "duty_roster",
  "tracking"
]
```

### `object_type`

후보가 떠올리는 실제 작업 대상이다.

```json
[
  "message",
  "document",
  "presentation",
  "spreadsheet",
  "form",
  "code",
  "shell",
  "system_record",
  "credential",
  "calendar_time",
  "file_folder",
  "meeting",
  "education_session",
  "event",
  "food_item",
  "physical_space",
  "equipment_asset",
  "vehicle_service",
  "web_content",
  "notice",
  "roster_shift",
  "status_record"
]
```

### `interaction_mode`

제목의 action phrase와 후보의 workflow를 맞추는 scoring 축이다.

```json
[
  "create_edit",
  "review_confirm",
  "request_delegate",
  "approve_signoff",
  "send_share",
  "publish_distribute",
  "coordinate",
  "monitor_track",
  "organize_cleanup",
  "setup_prepare",
  "input_process",
  "attend_participate",
  "call",
  "message",
  "meeting",
  "authenticate_access",
  "move_transport"
]
```

### `visibility`

노출 범위는 추천 충돌에서 중요하다. 공개 게시 후보는 `public`, 내부 업무 후보는 `internal`, 개인 일정·비공개 메모 후보는 `private`이 자연스럽다.

```json
[
  "private",
  "internal",
  "public"
]
```

### `tone`

최소한의 업무 분위기만 둔다. 감성 태그가 아니라 scoring prior다.

```json
[
  "neutral",
  "formal",
  "urgent",
  "sensitive"
]
```

## 4. 현재 프로젝트 구조와의 연결

현재 추천 경로는 `ARCHITECTURE.md`의 P0-P7 구조를 따른다.

1. P3 pair rules와 P4 meaning matching이 후보 row를 만든다.
2. P6 ranking이 `workflow_priority`, `interface_dominance_effective`, `keyword_workflow_resolution` 등 현재 숫자 신호로 1위를 고른다.
3. `semantic_metadata`는 이 흐름을 대체하지 않고, 후보 row의 `data["semantic_metadata"]`로 같이 운반된다.
4. 이후 recommendation engine은 다음처럼 사용할 수 있다.
   - `candidate.workflow_fit ∩ inferred_categories`가 비어 있지 않으면 score boost
   - `workflow_fit[0]`과 inferred primary category가 같으면 추가 boost
   - 제목에 UI/channel anchor가 있으면 `interaction_mode=call`, `message`, `meeting`을 modality별로 보조 boost
   - `visibility=public` 후보는 `게시`, `공고`, `누리집` 같은 공개 신호가 있을 때만 boost
   - `tone=urgent` 후보는 `긴급`, `주의`, `마감` 같은 신호와 결합할 때만 boost

Pair/synthetic row는 두 방식 중 하나로 연결한다.

- catalog 후보를 복사하는 pair row는 복사된 candidate의 `semantic_metadata`를 그대로 사용한다.
- 완전 synthetic row는 `pair_rules.json` 또는 별도 sidecar map에서 synthetic id별 metadata를 부여한다.

## 5. 기존 필드와의 역할 차이

| 필드 | 현재 역할 | `semantic_metadata`와의 차이 |
| --- | --- | --- |
| `meaning` | 제목에 포함될 수 있는 retrieval keyword 목록. 각 keyword가 `workflow_resolution`, `interface_dominance`를 갖고 P4 후보 row 생성에 직접 쓰인다. | `semantic_metadata`는 keyword가 아니며 substring match에 쓰지 않는다. 후보가 생성된 뒤 category-aware scoring과 설명에 쓰는 후보 속성이다. |
| `interface_memory` | 사용자가 떠올리는 실제 UI·서비스 화면 기억. 예: `메일창`, `통화화면`, `채팅창`. | `semantic_metadata.object_type`과 `interaction_mode`는 UI 이름이 아니라 구조화된 의미 축이다. `interface_memory`는 사람이 읽는 힌트로 남긴다. |
| `usage_context` | 이 후보가 자연스러운 예시 문맥. 큐레이션과 사람이 보는 설명에 유용하다. | `semantic_metadata`는 예시 문장이 아니라 enum 값이다. 추천 엔진이 일관되게 비교할 수 있다. |
| `workflow_priority` | catalog anchor strength. P6에서 meaning row의 `sort_secondary_wp`로 쓰인다. | `semantic_metadata`는 우선순위 숫자가 아니라 후보의 의미 좌표다. 점수화는 후속 scoring layer가 담당한다. |

겹쳐 보이는 부분은 의도된 것이다. `meaning`은 “어떤 단어가 후보를 불러오는가”, `semantic_metadata`는 “불려온 후보가 어떤 업무 의미인가”를 답한다.

## 6. 실제 JSON 예시

### Mail action

```json
{
  "mail_action": {
    "semantic_metadata": {
      "workflow_fit": ["communication", "document"],
      "object_type": "message",
      "interaction_mode": "send_share",
      "visibility": "internal",
      "tone": "neutral"
    }
  }
}
```

`메일`, `공지`, `발송` 같은 retrieval은 기존 `meaning`이 담당한다. `semantic_metadata`는 이 후보가 communication primary이고 문서 전달과도 연결될 수 있음을 scoring layer에 알려준다.

### Spreadsheet work

```json
{
  "spreadsheet_work": {
    "semantic_metadata": {
      "workflow_fit": ["tabular_data", "tracking"],
      "object_type": "spreadsheet",
      "interaction_mode": "input_process",
      "visibility": "internal",
      "tone": "neutral"
    }
  }
}
```

`엑셀 자료 정리`처럼 organize pair와 spreadsheet meaning이 경쟁할 때, 후속 scoring은 title의 interface/object 신호와 `object_type=spreadsheet`를 맞춰 tabular 후보를 보강할 수 있다.

### Publication posting

```json
{
  "publication_posting": {
    "semantic_metadata": {
      "workflow_fit": ["broadcast_notice", "communication", "document"],
      "object_type": "notice",
      "interaction_mode": "publish_distribute",
      "visibility": "public",
      "tone": "formal"
    }
  }
}
```

게시·공고 계열은 단순 문서 편집과 다르다. 공개 범위와 formal tone을 함께 두면 내부 검토 후보와 외부 게시 후보를 분리할 수 있다.

### Status tracking

```json
{
  "progress_monitoring": {
    "semantic_metadata": {
      "workflow_fit": ["tracking", "tabular_data"],
      "object_type": "status_record",
      "interaction_mode": "monitor_track",
      "visibility": "internal",
      "tone": "neutral"
    }
  }
}
```

현황·진행·응답 같은 제목은 문서나 표 후보와 붙기 쉽다. `workflow_fit[0]=tracking`은 “무엇을 작성하는가”보다 “상태를 본다”는 category inference를 가능하게 한다.

## 7. 적용 원칙

- 먼저 모든 후보에 완벽히 채우려 하지 말고, 충돌이 잦은 후보군부터 붙인다.
- enum은 feedback과 테스트에서 실제로 쓰일 때만 늘린다.
- `workflow_fit[0]`은 primary fit이다. primary category가 흔들릴 때마다 순서를 바꾸지 말고, 사용자 선택 로그로 검증한다.
- `semantic_metadata` 값만으로 retrieval 결과를 만들지 않는다. retrieval은 계속 `meaning`과 pair rules가 담당한다.
- scoring에 넣을 때는 hard rule보다 작은 boost/penalty부터 시작한다.
