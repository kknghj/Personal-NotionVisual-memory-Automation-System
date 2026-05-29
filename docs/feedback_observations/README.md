# Optional semantic observation slices (Layer B)

`data/feedback_log.json`의 각 이벤트는 **Layer A** 공통 헤더([`feedback_log_schema.md`](../feedback_log_schema.md))를 가지며, 필요할 때만 **Layer B** semantic slice를 붙인다.

## 원칙

- Slice는 **전역 필수 taxonomy가 아니다.**
- 후보마다 slice를 채울 필요 없다.
- Slice는 **hard filter·자동 penalty 입력이 아니다** — observation·calibration용이다.

## 현재 문서화된 slice

| Slice | 문서 | 구현 상태 |
|-------|------|-----------|
| `workflow_stage` | [`workflow_stage.md`](workflow_stage.md) | **부분 구현** — ambiguity scoring log·export·builder. live API/UI 적재는 후속. |

## 계획된 slice (문서만, 미구현)

아래는 **선택적** future slice 이름이다. 별도 스키마 문서·코드는 필요 시 추가한다.

| Slice | 용도 (개념) |
|-------|-------------|
| `semantic_boundary` | ontology boundary·후보 경계 ambiguity |
| `interface_channel` | interface dominance·채널 vs 객체 혼동 |
| `visual_preference` | emoji vs notion_icon, color 등 사용자 선호 |

이 디렉터리에 해당 문서가 없으면, 아직 스키마가 고정되지 않은 것이다.
