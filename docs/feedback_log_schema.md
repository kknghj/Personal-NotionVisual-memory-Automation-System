# feedback_log architecture

`data/feedback_log.json`은 추천·선택·수정이 **실제로 어떻게 일어났는지**를 쌓는 **관측 로그(observation log)** 이다.

## Philosophy

| 원칙 | 의미 |
|------|------|
| **observation first** | 사실(추천, 후보, 선택, 변경, 추론 신호)을 먼저 기록한다. |
| **policy later** | 로그로 무엇을 학습·튜닝할지는 **나중에** 결정한다. |

`feedback_log`는:

- **an observation log** — 무엇이 일어났는지의 기록
- **not a training dataset** — 곧바로 가중치·penalty·hard rule의 입력으로 쓰이지 않는다

개인용 추천 시스템 규모에 맞게 **가볍게** 유지한다. (단일 JSON 배열 파일, enterprise analytics 아님.)

---

## Storage

| 항목 | 값 |
|------|-----|
| 경로 | `data/feedback_log.json` |
| 형식 | JSON **배열** 루트 (`[ ... ]`) |
| 로더 | `app/data_loader.py` — `load_feedback_log()`, `append_feedback_log_entry()` |
| 예시 | `data/feedback_log_examples.json` |

Phase 0: 파일은 유효한 빈 배열 `[]` 로 초기화한다. (0-byte 파일은 `json.load` 실패 가능.)

---

## Architecture: Layer A + Layer B

### Layer A — Common feedback event

모든 `event_type`에 공통으로 적용되는 **이벤트 봉투(envelope)** 개념이다.  
구현 시 필드명·중첩 구조는 진화할 수 있으나, 기록해야 할 **의미 단위**는 아래와 같다.

| 개념 | 설명 |
|------|------|
| **Identity** | `event_type`, `recorded_at` (ISO-8601 UTC) |
| **Context** | `title` (일정 제목 등); 필요 시 `input_context` (modifier·pair 힌트 등, 후속) |
| **Recommendation** | 시스템이 제안한 것 — `recommended_candidate_id`, `recommended_visual` (후속), 상위 N 요약 `ranking_summary` (후속) |
| **User selection** | 사용자가 고른 것 — `user_selected_candidate_id`, `user_selected_visual` (후속) |
| **Correction** | 추천과 다른 최종 선택 — `changed`, `change_type`, `selection_source` (후속) |
| **Provenance** | `source_surface` — 이벤트가 어디서 기록됐는지 (예: `ambiguity_scoring_log`, `recommend_api`, `notion_ui`) |
| **Notes** | `reason` (시스템), `user_note` (사용자, 후속) |

**필수/선택 구현 상태:** Layer A 전체 envelope는 **문서화됨**. `event_type`·`recorded_at`·`title`·`recommended_candidate_id`·`user_selected_candidate_id` 정도만 export 경로에서 쓰인다. 나머지 Layer A 필드는 **후속 PR**에서 추가한다.

향후 호환을 위해 `schema_version` 같은 버전 필드를 둘 수 있다 (아직 필수 아님).

### Layer B — Optional semantic observation slices

ontology·의미 축별 **선택적** 관측 블록이다. 이벤트마다 0개 이상.

- 후보 전역에 slice를 **강제하지 않는다.**
- slice 없이도 유효한 feedback 이벤트이다.

| Slice | 문서 | 상태 |
|-------|------|------|
| `workflow_stage` | [`feedback_observations/workflow_stage.md`](feedback_observations/workflow_stage.md) | **부분 구현** (scoring log·export·builder) |
| `semantic_boundary` | (미작성) | 계획만 |
| `interface_channel` | (미작성) | 계획만 |
| `visual_preference` | (미작성) | 계획만 |

Slice 인덱스: [`feedback_observations/README.md`](feedback_observations/README.md)

---

## Event types (vocabulary)

| `event_type` | 의미 | 구현 상태 |
|--------------|------|-----------|
| `ambiguity_scoring` | 오프라인 ambiguity scoring log에서 export된 관측 | **부분** — scoring log + `tools/export_feedback_observations_from_scoring_log.py` |
| `recommendation` | 라이브 추천 API가 응답을 낸 순간 | **후속** — `/recommend-icon` 미연동 |
| `user_selection` | 사용자가 추천을 그대로 수락 | **후속** — UI 없음 |
| `user_correction` | 사용자가 추천과 다르게 수정 | **후속** — 예시만 `feedback_log_examples.json` |
| `manual_label` | 사람이 semantic 라벨을 붙임 | **후속** |
| `batch_import` | 도구가 일괄 적재 | **후속** |

---

## What exists today (summary)

| 구성요소 | 상태 |
|----------|------|
| `data/feedback_log.json` | `[]` placeholder |
| `append_feedback_log_entry()` | 코드 있음; **프로덕션 write path 거의 없음** |
| `workflow_stage` slice | scoring log attachment + export + `app/workflow_stage_observation.py` |
| Live recommendation / user feedback 적재 | **없음** |

---

## Out of scope (current system)

`feedback_log`는 **현재** 다음을 **하지 않는다**:

- scoring **penalty** 자동 적용
- **reranking** 가중치 실시간 변경
- 후보 **hard filter**
- **ML training** 파이프라인
- **Notion** 실시간 feedback pipeline
- 대시보드·라벨링 UI

이들은 로그가 쌓인 뒤에도 **정책 결정이 별도**여야 한다.

---

## Related docs

- Workflow meaning model: [`workflow_ontology.md`](workflow_ontology.md) §11
- Product data mention: [`PRD.md`](PRD.md) §5-3 (observation-first; aligned with this doc)
- Examples: `data/feedback_log_examples.json`

---

## Reproduce workflow_stage path (today)

`workflow_stage` slice만 다루는 상세·필드·정책·분석 명령은 전용 문서에 있다:

→ [`feedback_observations/workflow_stage.md`](feedback_observations/workflow_stage.md)
