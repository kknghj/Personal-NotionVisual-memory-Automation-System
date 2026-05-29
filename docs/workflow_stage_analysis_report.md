# Workflow stage 도입 — 구현·scoring·snapshot 분석 리포트

**비교 로그**

| 역할 | 파일 |
|------|------|
| Before | `tests/ambiguity/ambiguity_results/2026-05-21_0519_scoring_log.json` |
| After | `tests/ambiguity/ambiguity_results/2026-05-21_workflow_stage_scoring_log.json` |

**산출물**

- `tests/ambiguity/ranking_snapshots/before_vs_after_snapshot.json`
- `tests/ambiguity/ranking_snapshots/ranking_movement_summary.json`
- `tests/ambiguity/ranking_snapshots/semantic_improvement_cases.json`
- `tests/ambiguity/ranking_snapshots/regression_cases.json`

---

## 1. 구현 요약

| 영역 | 변경 |
|------|------|
| Ontology | `docs/workflow_ontology.md` §8.1 — `progress` / `interim` / `result` / `final`, reporting vs result_reporting, `현황` ambiguity |
| Metadata | `document_reporting.workflow_stage`: `[progress, interim]` · `result_reporting`: `[result, final]` |
| Meaning 정리 | `document_reporting`에서 `결과보고` 등 result 전용 token 제거 → `result_reporting` 단일 retrieval |
| Scoring | `app/semantic_scoring.py` — title `workflow_stage` inference + `FIELD_WEIGHTS["workflow_stage"]=2` soft bonus |
| Schema | `docs/semantic_metadata_schema.md` — optional `workflow_stage` 필드 |

`interim_reporting` / `final_reporting` **별도 candidate id는 추가하지 않음** (metadata + 기존 2 id 유지).

---

## 2. Scoring 연결 검토 (hard filter vs soft bonus vs weighted rerank)

### Title keyword → stage inference

| 신호 | `workflow_stage` | 비고 |
|------|------------------|------|
| `진행상황`, `추진현황`, `진행보고` … | `progress` | 강한 progress 신호 |
| `중간보고`, `중간점검` … | `interim` | |
| `결과보고`, `출장결과`, `교육결과` … | `result` | `최종결과`는 `final`+`result` |
| `최종안`, `최종결과`, `종료` … | `final` | |
| `현황` **단독** | *(추론 안 함)* | progress/result/tracking 모두 가능 — false negative 방지 |
| `종료`, `중간` (짧은 토큰) | 해당 stage | 문맥 오탐 가능 → 가중치만 2, filter 없음 |

### 세 가지 적용 방식 비교

| 방식 | 장점 | 단점 | 본 단계 선택 |
|------|------|------|--------------|
| **Hard filter** | 경계 선명 | metadata 없는 제목·약한 신호에서 후보 소실 (false negative) | **미채택** |
| **Soft semantic bonus** | 기존 P6 키 유지, sparse metadata 대응 | gap이 작으면 여전히 tie 가능 | **채택** (+2, `workflow_fit`과 동급) |
| **Weighted rerank feature** | 관측·분석 후 feature화에 유리 | 별도 feature 파이프라인·캘리브레이션 필요 | **후속** (`feedback_log`에 stage 관측 축적 후) |

**Ambiguity penalty**는 이번에 **도입하지 않음**. stage 불일치만으로 감점하면 “보고”만 있는 제목에서 `document_reporting`이 과도하게 깎일 수 있음. 대신 **result 전용 meaning 중복 제거**로 retrieval collision을 먼저 줄임.

**Candidate reranking**: `semantic_bonus`가 P6 sort key에 이미 포함되어 있어, stage 일치 시 `result_reporting`이 동일 token·동일 base semantic(7)에서 **+2**로 앞서게 됨.

---

## 3. Snapshot — ambiguity 감소 여부

`ranking_movement_summary.json` → `workflow_stage_ambiguity_analysis`:

| 지표 | Before (0519) | After (workflow_stage) |
|------|---------------|-------------------------|
| reporting focus 제목 수 | 6 | 6 |
| top1/top2가 reporting 쌍이고 gap ≤ 0.005 | **4** | **0** |
| 위 near-tie **해소** | — | **4** |
| reporting ↔ result_reporting top flip | — | **4** (의도된 개선) |

### reporting vs result_reporting

| 제목 | Before top1 | After top1 | gap (after) |
|------|-------------|------------|---------------|
| 결과보고 전달 | `document_reporting` | `result_reporting` | 0.02 |
| 교육결과 보고 | `document_reporting` | `result_reporting` | 0.058 |
| 정산결과 보고 | `document_reporting` | `result_reporting` | 0.058 |
| 최종결과 보고 | `document_reporting` | `result_reporting` | 0.058 |

4건 모두 **0 tie → result 쪽 승리**. `semantic_improvement` / `workflow_boundary_improvement` 라벨.

### 진행상황 / 현황 계열

| 제목 | Before | After | 해석 |
|------|--------|-------|------|
| 진행상황 보고 | `document_reporting` (gap 0.056) | 동일 + `workflow_stage` bonus | progress 신호 유지, tracking 2위와 분리 유지 |
| 운영현황 전달 / 현황자료 전달 | `document_review` 등 | **변화 없음** | `현황` 단독은 stage 미추론 — 의도된 ambiguous 처리 |
| (예시) 전국 식생활교육 현황 보고 | 테스트셋 미포함 | ontology·inference에서 stage 없음 | feedback 라벨 권장 |

### 전역 지표

| 지표 | Δ |
|------|---|
| `top_candidate_changed_count` | 4 (전부 reporting 경계) |
| `semantic_bonus_total` | +12 |
| `high_ambiguity` | −2 |
| `average_ambiguity_gap` | +0.002 (미미) |
| reporting 관련 **regression_cases** | **0** |

**Top candidate stability**: 100제목 중 96 stable — 변경은 reporting/result 경계에 집중 (overfitting 위험 낮음).

**Semantic bonus precision**: stage match는 **명시적 result/progress phrase가 있을 때만** 발화 → 4 flip 모두 기대 방향; `현황`만 있는 제목은 bonus 없음.

---

## 4. 최종 평가 (요청 5항목)

### 4.1 workflow_stage 도입 효과

- reporting 계열 **semantic lifecycle**을 ontology·metadata·scoring에 한 축으로 연결.
- near-tied reporting 쌍 **4/4 해소** (ambiguity test subset).
- candidate id 증가 없이 `result_reporting` top1 **0 → 4** (테스트셋 내 result 계열 보고 제목).

### 4.2 실제 ambiguity 감소 여부

- **예**: `결과보고`·`교육결과`·`최종결과` + 보고류 — **감소 확인**.
- **부분적**: `현황` 단독·전달/공유 동사 결합 제목 — 여전히 `document_review` / distribution 계열과 경쟁 (stage 축 범위 밖).

### 4.3 over-segmentation 위험

- `interim_reporting` / `final_reporting` id 분리 **하지 않음** → explosion 없음.
- `최종결과 보고`처럼 `final`+`result` 동시 추론은 허용 (둘 다 `result_reporting` metadata와 호환).

### 4.4 ontology complexity 증가 수준

- **중간**: §8 `lifecycle_stage`와 별도 §8.1 `workflow_stage` — 문서·큐레이터 인지 부담은 있으나, reporting 후보 2개에만 필수.
- 다른 sub_workflow에는 당장 필수 아님.

### 4.5 추천 다음 단계

1. `feedback_log`에 `inferred_workflow_stage` / `matched_workflow_stage` 기록 — **구현됨** (`docs/feedback_observations/workflow_stage.md`, `app/workflow_stage_observation.py`).
2. `현황 보고`류 소량 라벨링 후, 맥락 규칙(연례·집계 vs 추진)만 **선택적** bonus.
3. ambiguity test set에 예시 3건(식생활 진행/출장 결과/전국 현황) 추가.
4. stage 불일치 **penalty**는 `feedback_log` 관측·라벨 검증 **후** 0.5~1 수준으로만 **오프라인 실험** (런타임 자동 적용 아님).

### 4.6 독립 ontology 축 vs lifecycle metadata 축소

| 판단 | 근거 |
|------|------|
| **reporting / result_reporting 경계에서는 독립 축 유지 가치 있음** | 동일 visual·동일 interaction_mode에서도 lifecycle이 갈림; snapshot이 이를 증명. |
| **전역 top-level taxonomy로 승격할 필요는 없음** | `document.reporting` sub_workflow 아래 **optional metadata**가 적절. |
| **축소(merge into lifecycle_stage only)는 비권장** | §8 `report` stage만으로는 progress vs result 구분 불가. |

**결론**: `workflow_stage`는 **reporting 계열에 한정된 독립 ontology 축**으로 유지하고, 다른 category에는 필요 시에만 점진 확장.

---

## 5. 재현

```bash
export PATH="$HOME/.local/bin:$PATH"
python3 -m pytest tests/ -v
python3 tools/generate_ambiguity_scoring_log.py \
  --output tests/ambiguity/ambiguity_results/2026-05-21_workflow_stage_scoring_log.json
python3 tools/generate_ranking_snapshots.py
```

`tools/generate_ranking_snapshots.py`의 `LATEST_LOG`는 workflow_stage after 로그를 가리킨다. before는 자동으로 직전 타임스탬프 로그(`0519`)를 선택한다.
