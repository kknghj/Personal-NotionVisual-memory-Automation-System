# feedback_log schema — workflow_stage observations

`data/feedback_log.json`은 사용자 선택·추천 결과·ontology 슬라이스를 축적하는 **선택적** 배열 JSON이다.  
`workflow_stage`는 **reporting 계열 optional semantic axis**이며, global mandatory taxonomy·hard filter가 **아니다**.

---

## 1. Logging 위치 (현재 단계)

| 우선순위 | 위치 | 현재 상태 | 역할 |
|----------|------|-----------|------|
| 1 | **Ambiguity scoring log** | **구현됨** | `tools/generate_ambiguity_scoring_log.py`가 제목별 observation 필드를 붙임. 대량 regression·calibration에 적합. |
| 2 | Recommendation result log | **스키마만** | `/recommend-icon` 응답 후 동일 `build_workflow_stage_observation()` 호출 가능 (API 필드 확장은 후속). |
| 3 | User override / correction | **스키마만** | `user_confirmed_workflow_stage` + `workflow_stage_source: manual_label`. |
| 4 | Feedback collection pipeline | **후속** | Notion UI·배치 적재 시 `append_feedback_log_entry()` 사용. |

**원칙:** lightweight observation, analytics-ready, future rerank feature extraction.  
관련 제목·reporting 후보가 있을 때만 필드를 채워 **로그 노이즈·sparsity 부담**을 줄인다.

---

## 2. Event 공통 형태

```json
{
  "event_type": "ambiguity_scoring",
  "recorded_at": "2026-05-21T12:00:00Z",
  "title": "교육결과 보고",
  "recommended_candidate_id": "result_reporting",
  "user_selected_candidate_id": "",
  "inferred_workflow_stage": "result",
  "matched_workflow_stage": ["result", "final"],
  "user_confirmed_workflow_stage": "",
  "workflow_stage_confidence": 0.85,
  "workflow_stage_source": "keyword:교육결과",
  "workflow_stage_ambiguous": false,
  "workflow_stage_mismatch": false,
  "inferred_workflow_stages_all": ["result"]
}
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `event_type` | ✓ | `ambiguity_scoring` \| `recommendation` \| `user_correction` |
| `recorded_at` | ✓ | ISO-8601 UTC |
| `title` | ✓ | 일정 제목 |
| `recommended_candidate_id` | 선택 | 시스템 1위 후보 |
| `user_selected_candidate_id` | 선택 | 사용자 최종 선택 (없으면 `""`) |

### 2.1 workflow_stage optional fields

| 필드 | 타입 | 설명 |
|------|------|------|
| `inferred_workflow_stage` | `string \| null` | 제목 keyword/context 기반 **시스템 1차 추론** (`progress` \| `interim` \| `result` \| `final`). ambiguous면 `null`. |
| `matched_workflow_stage` | `string[]` | 선택된 후보 `semantic_metadata.workflow_stage` 허용 목록 |
| `user_confirmed_workflow_stage` | `string` | 사람 라벨 (검증·ground truth). 없으면 `""` |
| `workflow_stage_confidence` | `number` | 0.0–1.0 heuristic (hard rule 아님) |
| `workflow_stage_source` | `string` | 추론 근거 (아래 표) |
| `workflow_stage_ambiguous` | `boolean` | `현황` 등으로 stage 단정 불가 |
| `workflow_stage_mismatch` | `boolean` | `(confirmed \|\| inferred)` ∉ `matched_workflow_stage` (reporting 후보만) |
| `inferred_workflow_stages_all` | `string[]` | 복수 stage 추론 시 전체 (분석용) |

### 2.2 `workflow_stage_source` 값

| 패턴 | 예 |
|------|-----|
| `keyword:{term}` | `keyword:진행상황`, `keyword:결과보고` |
| `ambiguous:{token}` | `ambiguous:현황` |
| `contextual:{phrase}` | `contextual:운영현황` (현황 단독·compound 힌트) |
| `manual_label` | 사용자 확정 라벨 이벤트 |
| `""` | reporting 축과 무관하거나 stage 신호 없음 |

### 2.3 Confidence heuristic (현재)

| 상황 | confidence |
|------|------------|
| 긴 keyword match (len ≥ 4) | 0.85 |
| 짧은 keyword (예: `중간`) | 0.65 |
| 복수 stage 동시 추론 | ≤ 0.75 |
| ambiguous `현황` (stage null) | 0.2 |
| 신호 없음 | 0.0 |

---

## 3. 정책 — ambiguous / mismatch

### A. Ambiguous inferred stage

`현황`만 있고 progress/result/interim/final keyword가 없을 때:

```json
{
  "inferred_workflow_stage": null,
  "matched_workflow_stage": ["progress", "interim"],
  "workflow_stage_confidence": 0.2,
  "workflow_stage_source": "ambiguous:현황",
  "workflow_stage_ambiguous": true,
  "workflow_stage_mismatch": false
}
```

`운영현황`·`신청현황` 등은 stage를 붙이지 않고 `workflow_stage_source: contextual:운영현황` 등으로 **패턴만** 기록한다.

### B. Mismatch case

시스템이 `progress`로 추론했는데 1위가 `result_reporting`일 때:

```json
{
  "title": "…진행상황 보고…",
  "inferred_workflow_stage": "progress",
  "recommended_candidate_id": "result_reporting",
  "matched_workflow_stage": ["result", "final"],
  "workflow_stage_mismatch": true,
  "workflow_stage_confidence": 0.85,
  "workflow_stage_source": "keyword:진행상황"
}
```

향후 penalty 실험·false negative 분석·ontology refinement 입력으로 사용한다.

---

## 4. Logging examples

예시 파일: `data/feedback_log_examples.json`  
코드: `app/workflow_stage_observation.py`, `app/semantic_scoring.infer_workflow_stage_detail()`

---

## 5. Analytics (future-compatible)

`tools/analyze_workflow_stage_observations.py`가 scoring log 또는 `feedback_log.json`에서 집계:

- **confusion matrix** — `inferred_workflow_stage` × `recommended_candidate_id` (reporting subset)
- **progress ↔ result confusion** — off-diagonal count
- **ambiguous token frequency** — `workflow_stage_source` prefix `ambiguous:` / `contextual:`
- **현황 usage distribution** — 제목에 `현황` 포함 비율 vs ambiguous 비율
- **stage mismatch rate** — `workflow_stage_mismatch` 비율
- **confidence calibration** — confirmed label 있을 때 confidence bucket별 accuracy

현재 단계: **구조·스크립트만** 제공. 대시보드·자동 penalty 연동은 **불필요**.

---

## 6. 구현 범위 vs 후속

| 항목 | 지금 | 후속 |
|------|------|------|
| Schema + observation builder | ✓ | — |
| Ambiguity log attachment | ✓ | — |
| `feedback_log.json` append API | ✓ (`append_feedback_log_entry`) | UI 연동 |
| Recommendation API 필드 | 문서화만 | `RecommendResponse` extension |
| Penalty / rerank from log | **하지 않음** | feedback 축적 후 |
| User labeling UI | **하지 않음** | manual_label 적재 |

### 가치 평가 (현재)

- reporting/result_reporting **ambiguity 감소 검증**을 scoring log만으로 재현 가능.
- `현황`·mismatch를 **명시적 필드**로 쌓아 ground truth·penalty 실험 기반 마련.
- candidate explosion·hard filter 없이 **soft calibration** 철학 유지.

### 아직 불필요한 것

- 전역 mandatory `workflow_stage` on 모든 candidates
- Hard filter / automatic penalty from log
- 별도 `interim_reporting` candidate ids
- 실시간 Notion feedback pipeline (스키마만 준비)

---

## 7. 재현

```bash
python3 tools/generate_ambiguity_scoring_log.py \
  --output tests/ambiguity/ambiguity_results/latest_scoring_log.json
python3 tools/analyze_workflow_stage_observations.py \
  tests/ambiguity/ambiguity_results/latest_scoring_log.json
python3 tools/export_feedback_observations_from_scoring_log.py \
  --scoring-log tests/ambiguity/ambiguity_results/latest_scoring_log.json \
  --output data/feedback_log.json
```
