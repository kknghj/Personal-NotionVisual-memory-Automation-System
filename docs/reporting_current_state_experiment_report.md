# Reporting current state — workflow_stage 실험 최종 리포트

**입력:** `reporting_current_state_set.txt` (45제목) + 필수 6케이스  
**테스트셋:** `tests/ambiguity/ambiguity_test_set.json` (100 → **145**제목)  
**Manifest:** `tests/ambiguity/reporting_current_state_manifest.json`  
**Scoring log:** `tests/ambiguity/ambiguity_results/2026-05-21_current_state_workflow_stage_log.json`  
**Before (stable):** `tests/ambiguity/ambiguity_results/2026-05-21_0519_scoring_log.json`  
**Analytics:** `tests/ambiguity/ambiguity_results/current_state_workflow_stage_analytics.json`  
**Manifest 분석:** `tests/ambiguity/ambiguity_results/current_state_manifest_analysis.json`  
**Snapshots:** `tests/ambiguity/ranking_snapshots/*`

---

## 1. ambiguity test set 추가

| 그룹 | 건수 | 목적 |
|------|------|------|
| `reporting_stage_cases` | 34 | 보고·공유·정리·제출·업데이트 — reporting boundary |
| `status_ambiguity_cases` | 7 | 현황 중심 — tracking/review vs reporting |
| `result_lifecycle_cases` | 4 | 결과+현황 — `result_reporting` lifecycle |
| `intentionally_ambiguous_cases` | 4 | false certainty 탐지 (일부 중복 제목) |

**필수 6케이스 결과 (top1)**

| 제목 | top1 | stage inference | 비고 |
|------|------|-----------------|------|
| 전국 식생활교육 현황 보고 | `document_reporting` | **null**, conf 0.2, `ambiguous:현황` | 의도대로 stage 미확정 |
| 사업 운영 결과 현황 보고 | `document_reporting` | **result**, conf 0.85 | **mismatch** (result vs progress/interim metadata) |
| 부서별 현황 자료 공유 | `document_sharing` | null, ambiguous | 공유 축 유지 ✓ |
| 주요사업 추진현황 주간회의 자료 작성 | `document_edit` | progress, conf 0.85 | 작성·추진현황 — reporting 아님 ✓ |
| 보험 가입현황 제출 | `document_edit` | null, ambiguous | 제출·현황 — reporting 과적합 없음 ✓ |
| 비상소집 응소자 현황 제출 | `document_edit` | null, ambiguous | 동일 ✓ |

---

## 2. scoring log 요약 (145제목)

- **stage observation rows:** 66 (관련 제목만 필드 부착)
- **reporting near-tie (gap ≤ 0.005):** **0건** (현재 세트 전체)
- **progress ↔ result cross-confusion (top1):** **1건** (`inferred=result` → `document_reporting`)
- **stage mismatch:** **1건** (사업 운영 결과 현황 보고)
- **false certainty (manifest 기준):** **1건** (프로젝트 진행 현황 정리 — high ambiguity인데 progress @ 0.85)

### workflow_stage 필드 포함

모든 observation row에 `inferred_workflow_stage`, `workflow_stage_confidence`, `workflow_stage_source`, `workflow_stage_ambiguous`, `workflow_stage_mismatch`, `inferred_workflow_stages_all`, `matched_workflow_stage` 포함됨.

---

## 3. ranking snapshot (0519 vs current_state)

### 전체 145제목 (union 비교)

| 지표 | Before (0519) | After (current) |
|------|---------------|-----------------|
| top 변경 | — | **36** (대부분 **신규 45제목** retrieval 변화) |
| no_candidate | 48 | **16** (−32, retrieval 개선) |
| reporting near-tie | 4 | **0** |
| `document_reporting` top1 (after 분포) | — | **20** |
| `result_reporting` top1 | — | **4** |

**실제 개선 vs 우연한 이동 구분**

| 유형 | 설명 |
|------|------|
| **의미적 개선** | legacy 100제목에서 reporting/result 4 flip (이전 실험과 동일), near-tie 4→0, `교육결과 보고` 등 result 계열 분리 |
| **우연/커버리지** | 신규 45제목 중 32건 no_candidate→candidate 출현 — test set 확장 효과, workflow_stage와 무관할 수 있음 |
| **혼합** | semantic_bonus +170 — 일부는 stage bonus, 일부는 신규 후보 row 증가 |

### workflow_stage 전용 (snapshot summary)

| 항목 | 값 |
|------|-----|
| 현황 포함 제목 | 49 |
| stage null 비율 | **73.5%** |
| ambiguous flag | 36 |
| false certainty (heuristic) | 5 |
| tracking→reporting regression | **0** |
| 제출/공유/정리 → reporting flip | **0** |
| stage–top alignment (reporting top만) | aligned 8, misaligned 1 |

---

## 4. workflow_stage observation 분석

### A. ambiguous title handling

- **`현황` 단독** (전국 식생활, 주간 영업 등): `inferred=null`, conf **0.2**, source `ambiguous:현황` — **적절**
- **`운영현황` 등**: `contextual:운영현황` (5건), stage still null — 패턴 축적용
- **null 처리 비율** (현황 제목): 73.5% — 보수적

### B. false certainty

| 케이스 | 문제 |
|--------|------|
| 프로젝트 진행 현황 정리 | 공백 제거 후 `진행현황` substring → progress @ 0.85 (intentionally ambiguous 기대와 불일치) |
| 계약 협상 진행 현황 보고 등 | 동일 메커니즘 (진행+현황 인접) |

**high conf + ambiguous flag 동시:** 0건  
**mismatch:** 1건 — `사업 운영 결과 현황 보고` (result inferred, `document_reporting` won, stage bonus 미적용으로 top은 유지)

### C. reporting boundary

| inferred | 기대 top | 실측 (reporting subset) |
|----------|----------|-------------------------|
| progress | document_reporting | 3/3 일치 |
| result | result_reporting | 3/3 + 1건 document_reporting (mismatch) |
| null + 보고 | either / low conf | document_reporting 다수, near-tie 없음 |

**중간보고:** `행사 준비 현황 중간보고` → `document_reporting`, interim inferred ✓

### D. overfitting

- **제출/공유/정리 → reporting:** keyword_overfit count **0**
- **보험/비상소집 제출:** `document_edit` (제출 token) — workflow_stage가 붕괴시키지 않음 ✓
- **과적합 위험:** `진행현황` compound가 공백 없는 “진행 현황”에도 매칭 — **keyword 규칙 과확신** 1건

---

## 5. regression 분석

### 위험 regression (관측)

| 위험 | 결과 |
|------|------|
| monitoring→reporting 과이동 | **0건** (legacy intersection 기준도 0) |
| 단순 현황 → result_reporting | **0건** |
| 제출/공유/정리 붕괴 | **0건** |
| confidence inflation | 현황 대부분 0.2 유지; result phrase만 0.85 — **선별적** |

### 안정성

- **Top stability (legacy 100):** 96 stable (이전과 동일 order)
- **Ambiguity gap:** 평균 0.024→0.027 (미미)
- **Semantic bonus:** reporting 관련에서 stage +2 작동; 전역 +170은 test set 확장 영향 혼재
- **workflow_stage 영향 범위:** 66/145 rows only — **sparse, 의도적**

### residual 이슈

1. **성과 분석 결과 현황 보고** — `결과` 있으나 `현황`이 ambiguous를 덮어 null @ 0.2 (result lifecycle 기대와 불일치)  
2. **사업 운영 결과 현황 보고** — result inferred but `document_reporting` top (운영결과 키워드 vs stage bonus 미스매치)  
3. **진행 현황** (띄어쓰기) → canonical `진행현황` → false progress certainty  

---

## 6. 최종 평가 및 다음 단계

### 6.1 workflow_stage 축 품질

| 질문 | 평가 |
|------|------|
| semantic improvement? | **부분적 yes** — reporting/result near-tie 0, progress/result inference 대체로 정렬 |
| ambiguity handling 개선? | **yes** — pure `현황` null@0.2; **단**, `진행현황`·`운영결과` edge case 잔존 |
| observation 유효? | **yes** — mismatch·ambiguous·confusion matrix가 튜닝 포인트를 가리킴 |

### 6.2 현황 처리 전략

| 전략 | 평가 |
|------|------|
| 현황 단독 → null | **유지 권장** — false negative 최소 |
| contextual inference | **defer** — `contextual:운영현황` 로그만 축적 후 feedback 라벨 |
| 추가 rule 지금? | **최소만** — `운영결과`+`현황` 복합은 result 후보 boost 검토 가능; penalty는 아직 |

### 6.3 false certainty

- **과도 확신:** 1 manifest-critical + 4 heuristic (`진행`+`현황` 인접)  
- **calibration:** ambiguous→0.2 / keyword→0.85 이분화는 대체로 맞음; **중간 band(0.4–0.6)** 없음 — 후속 optional

### 6.4 ontology 방향

- **reporting optional axis 유지** — 실험에서 가치 확인  
- **다른 category 확장** — defer (sparsity)  
- **candidate split 없이 metadata** — **가능** (near-tie 0, misaligned 1)

### 6.5 추천 다음 단계 (우선순위)

| 항목 | 분류 | 이유 |
|------|------|------|
| **feedback_log + user_confirmed 축적** | immediately useful | observation·calibration ground truth (penalty/rerank는 후속 검토) |
| **현황/결과복합 contextual rule (soft only)** | immediately useful | `성과 분석 결과 현황`, `사업 운영 결과 현황` 정렬 |
| **`진행현황` vs `진행 현황` disambiguation** | immediately useful | false certainty 1건 직접 해결 |
| **monitoring/tracking ontology 분리 문서화** | immediately useful | 현황+확인/제출 케이스는 이미 tracking/edit 승 |
| **penalty 도입** | should defer | mismatch 1건; 라벨 없음 |
| **contextual 현황 hard inference** | risky / premature | over-segmentation |
| **interim/final candidate split** | risky / premature | near-tie already 0 |

---

## 7. 재현

```bash
python3 tools/merge_reporting_current_state_test_set.py
python3 tools/generate_ambiguity_scoring_log.py \
  --output tests/ambiguity/ambiguity_results/2026-05-21_current_state_workflow_stage_log.json
python3 tools/generate_ranking_snapshots.py \
  --before tests/ambiguity/ambiguity_results/2026-05-21_0519_scoring_log.json \
  --after tests/ambiguity/ambiguity_results/2026-05-21_current_state_workflow_stage_log.json
python3 tools/analyze_workflow_stage_observations.py \
  tests/ambiguity/ambiguity_results/2026-05-21_current_state_workflow_stage_log.json
python3 tools/analyze_current_state_experiment.py \
  tests/ambiguity/ambiguity_results/2026-05-21_current_state_workflow_stage_log.json
```

---

## 8. 아키텍처 관점 (future)

| 관점 | 결론 |
|------|------|
| **Ontology** | `workflow_stage`는 §8.1 reporting 전용 optional 축으로 유지 |
| **Metadata** | 2후보 `workflow_stage` 배열로 충분; explosion 불필요 |
| **Scoring** | soft bonus + observation 로그; hard filter/penalty 보류 |
| **Ambiguity** | `현황` null 전략 유효; 복합 phrase rule은 점진 추가 |
| **Regression** | tracking/제출/공유 붕괴 없음 — scope 통제 성공 |
| **Future** | observation 축적 → 분석·검토 → (선택) calibration / weighted rerank / 제한적 penalty **실험** |
