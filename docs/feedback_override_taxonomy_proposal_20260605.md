# Override 발생 원인 Taxonomy — Hermes 최종 설계안

> **출처:** Hermes 설계 답변 (2026-06-05)  
> **관련 문서:** [feedback_override_taxonomy.md](feedback_override_taxonomy.md) — P5-B **축소 구현** 버전  
> **선행 분석:** [p5_override_pattern_analysis.md](p5_override_pattern_analysis.md) — P5-A `primary_pattern` vs `gap_type`

---

## 문서 역할

| 문서 | 역할 |
| --- | --- |
| **본 문서** (Hermes 최종 설계안) | 3-layer taxonomy 전체, 세부 semantic cause 코드, action 매핑, 집계 스키마 |
| [feedback_override_taxonomy.md](feedback_override_taxonomy.md) | 먼저 구현할 **축소판** — `source_type`, `cause_type`, `action_hint` 등 최소 필드만 |

축소판은 Hermes taxonomy의 3-layer 구조를 따르되, **CA-01, WT-05, NT-04** 등 세부 코드는 문서에 보관하고 **100건 분석 이후** 필요할 때 확장한다.  
→ 출처: [feedback_override_taxonomy.md §장기 확장 방향 / §현재는 구현하지 않는 세부 항목](feedback_override_taxonomy.md)

---

## 개요

이 taxonomy는 override feedback을 단순 예외가 아니라 추천 시스템 개선을 위한 **관측 데이터**로 분류한다.  
세 개의 layer로 구성된다.

| Layer | 질문 | 역할 |
| --- | --- | --- |
| **Layer 1** | What was broken? | override가 일어난 시점의 **엔진 상태** |
| **Layer 2** | Why did it break? | override의 **의미론적 원인** |
| **Layer 3** | What to fix? | 원인별 **대응 action** 매핑 |

---

## Layer 1: Override Source Type

`feedback_log`에서 집계 가능한 **최상위 분류**.  
축소 구현에서는 `source_type` 필드에 대응한다.

| `override_source_type` | 설명 |
| --- | --- |
| `CANDIDATE_ABSENT` | 후보가 아예 없어서 override |
| `CANDIDATE_WRONG_TOP` | 후보는 있지만 엉뚱한 것이 1위여서 override |
| `CANDIDATE_NEAR_TIE` | 맞는 후보가 있지만 2위 또는 거의 동점이어서 override |
| `PIPELINE_SKIP` | P0 sample_case가 이미 있는데 틀린 결과 반환 |
| `PHILOSOPHY_MISMATCH` | 기술적으로 맞지만 사용자의 **행동 회상** 기준과 다름 |

---

## Layer 2: Semantic Cause

각 source type 아래의 **의미론적 세부 원인**.  
축소 구현에서는 `cause_type`으로 단순화하고, 아래 코드(CA-01, WT-05, NT-04 등)는 100건 분석 후 확장한다.

### `[CANDIDATE_ABSENT]`

| 코드 | `semantic_cause` | 설명 |
| --- | --- | --- |
| CA-01 | `catalog_gap` | 해당 workflow를 커버하는 visual candidate가 없음 |
| CA-02 | `keyword_gap` | 후보는 있으나 불러오는 meaning keyword가 없음 |
| CA-03 | `compound_masking` | compound noun 내부 keyword가 마스킹되어 retrieval 안 됨 |

### `[CANDIDATE_WRONG_TOP]`

| 코드 | `semantic_cause` | 설명 |
| --- | --- | --- |
| WT-01 | `keyword_scope_wide` | 너무 일반적인 keyword가 wrong candidate를 불러옴 (예: "확인"이 `document_review` 아닌 곳에서 매칭) |
| WT-02 | `interface_ignored` | interface anchor(메일/카톡/QR)가 있는데 category 후보가 이김 |
| WT-03 | `pair_unresolved` | (action, subject) pair가 있는데 단독 keyword로만 해석됨 |
| WT-04 | `compound_false_pos` | compound 내부 substring이 독립 keyword로 동작하여 false positive |
| WT-05 | `ontology_boundary_blur` | 두 workflow category 경계가 불명확하여 wrong category가 이김 (예: `notification_ops` vs `communication`, `distribution` vs `publication`) |

### `[CANDIDATE_NEAR_TIE]`

| 코드 | `semantic_cause` | 설명 |
| --- | --- | --- |
| NT-01 | `metadata_missing` | 후보에 `semantic_metadata`가 없거나 부족하여 tie-break 불가 |
| NT-02 | `metadata_undiscriminated` | metadata 있지만 두 후보가 같은 값 공유 → 차별화 안 됨 |
| NT-03 | `stage_ambiguous` | lifecycle stage(`workflow_stage` / `document_flow_stage`)를 제목에서 추론 못함 (예: "현황" 단독) |
| NT-04 | `field_weight_flat` | discriminative field의 `FIELD_WEIGHT`가 낮아 tie가 풀리지 않음 |
| NT-05 | `object_vs_channel` | object anchor와 channel anchor가 충돌하여 순위가 불안정 (예: "메일로 자료 전달" → `distribution` vs `mail_action`) |

### `[PIPELINE_SKIP]`

| 코드 | `semantic_cause` | 설명 |
| --- | --- | --- |
| PS-01 | `sample_case_stale` | `sample_cases.json`에 있는 P0 케이스가 실제 user 의도와 달라짐 |
| PS-02 | `sample_case_missing` | 이미 알려진 truth case가 `sample_cases`에 등록 안 됨 |
| PS-03 | `p0_format_error` | title strip / whitespace 차이로 P0 exact match 실패 |

### `[PHILOSOPHY_MISMATCH]`

| 코드 | `semantic_cause` | 설명 |
| --- | --- | --- |
| PM-01 | `visual_wrong_recall` | 추천 visual이 workflow 회상에 도움 안 됨 (emoji/icon 자체가 행동 기억을 trigger하지 못함) |
| PM-02 | `action_not_captured` | 추천 후보가 subject 위주이고 action이 반영 안 됨 (예: "음식" visual이 올라오는데 "준비" action이 핵심인 케이스) |
| PM-03 | `granularity_wrong` | 추천 후보의 workflow 단위가 너무 크거나 너무 세분화됨 |
| PM-04 | `tone_mismatch` | 공식성 / 긴박성 등 tone이 맞지 않음 (예: 결재용 업무에 캐주얼 emoji) |

---

## Layer 3: 대응 Action 매핑

`semantic_cause` → `primary_action` → `secondary_action`.  
축소 구현에서는 `action_hint`로 단순화한다.

| 코드 | `semantic_cause` | primary | secondary |
| --- | --- | --- | --- |
| CA-01 | `catalog_gap` | visual candidate 수정 (신규 추가) | 추가 전 Pattern 3 결정 트리 적용 (같은 visual이면 metadata로 먼저) |
| CA-02 | `keyword_gap` | visual candidate 수정 (meaning keyword 추가) | compound 여부 확인 후 추가 (Pitfall 1 회피) |
| CA-03 | `compound_masking` | semantic boundary 수정 (P2 compound span rule 재검토) | 이 제목 유형 sample case 추가 (P0 override 고려) |
| WT-01 | `keyword_scope_wide` | visual candidate 수정 (keyword scope 축소) | 영향 범위 snapshot 검증 필수 |
| WT-02 | `interface_ignored` | scoring 조정 (`interface_dominance` 또는 `FIELD_WEIGHTS` 확인) | 해당 candidate의 interface keyword missing이면 meaning 추가 (CA-02 분기) |
| WT-03 | `pair_unresolved` | semantic boundary 수정 (`pair_rules.json` 보강 or P3 rule 추가) | sample case 추가 (해당 pair의 ground truth 고정) |
| WT-04 | `compound_false_pos` | semantic boundary 수정 (P2 compound span masking 강화) | visual candidate 수정 안 함 (retrieval layer 문제) |
| WT-05 | `ontology_boundary_blur` | semantic boundary 수정 (`workflow_ontology` 경계 조건 명문화) | scoring 조정 (metadata axis 차별화); Pattern 1 Boundary Separation 절차 적용 |
| NT-01 | `metadata_missing` | visual candidate 수정 (`semantic_metadata` 필드 보강) | 추가 field마다 snapshot 비교로 gap 감소 확인 |
| NT-02 | `metadata_undiscriminated` | semantic boundary 수정 (두 후보의 metadata 차별화) | 차별화 불가 시 scoring 조정 (새 axis 검토) |
| NT-03 | `stage_ambiguous` | scoring 조정 (confidence soft boost 수치 재조정) | sample case 추가 (compound context 있는 케이스 ground truth); 단독 ambiguous 케이스는 null 유지 (false certainty 방지) |
| NT-04 | `field_weight_flat` | scoring 조정 (`FIELD_WEIGHTS` — 전역 영향 주의, **마지막 수단**) | 조정 전 narrow guard 함수 분리 시도 먼저 |
| NT-05 | `object_vs_channel` | semantic boundary 수정 (object-bound vs channel routing 정책 명문화) | sample case 추가 (edge case ground truth) |
| PS-01 | `sample_case_stale` | sample case 추가/수정 (P0 truth 갱신) | 기존 케이스 의도 변화 여부 주석 추가 |
| PS-02 | `sample_case_missing` | sample case 추가 (반복 확인된 truth case) | — |
| PS-03 | `p0_format_error` | semantic boundary 수정 (P0 lookup 규칙 또는 title strip 로직 확인) | — |
| PM-01 | `visual_wrong_recall` | 추천 철학 수정 (해당 workflow의 행동 회상 기준 재정의) | visual candidate 수정 (더 recall-effective한 emoji/icon으로 교체) |
| PM-02 | `action_not_captured` | 추천 철학 수정 (action-subject pair 우선 원칙 재확인) | visual candidate 수정 (action 중심 후보 추가 검토) |
| PM-03 | `granularity_wrong` | 추천 철학 수정 (workflow 단위 기준 재정의) | semantic boundary 수정 (category 분리 또는 합산) |
| PM-04 | `tone_mismatch` | visual candidate 수정 (tone metadata 보강 + 후보 교체) | scoring 조정 (tone `FIELD_WEIGHT` 상향 검토) |

### primary_action 요약

| `primary_action` | 해당 `semantic_cause` |
| --- | --- |
| visual candidate 수정 | CA-01, CA-02, WT-01, WT-02, NT-01, PM-01, PM-02, PM-04 |
| sample case 추가 | CA-03, WT-03, NT-03, NT-05, PS-01, PS-02 |
| semantic boundary 수정 | CA-03, WT-03, WT-04, WT-05, NT-02, NT-05, PS-03, PM-03 |
| scoring 조정 | WT-02, NT-03, NT-04, NT-05, PM-04 |
| 추천 철학 수정 | PM-01, PM-02, PM-03, PM-04* |

\* 복합 대응. 두 action이 함께 필요한 케이스.

---

## Feedback Statistics Analyzer용 집계 스키마

이 taxonomy를 `feedback_log` entry에 직접 붙이는 형태로 설계한다.  
축소 구현 필드(`source_type`, `cause_type`, `action_hint`, `resolved_by_current_engine`, `human_review_needed`, `notes`)는 아래 `override_analysis`의 단순화 버전이다.

```json
{
  "event_type": "user_override",
  "recorded_at": "2026-06-05T10:00:00Z",
  "title": "카톡으로 회신 요청",
  "recommended_candidate_id": "notification_cleanup",
  "final_candidate_id": "messenger_chat",

  "override_analysis": {
    "override_source_type": "CANDIDATE_WRONG_TOP",
    "semantic_cause": "WT-02",
    "semantic_cause_label": "interface_ignored",
    "resolved_by_current_engine": false,
    "primary_action": "scoring_adjustment",
    "secondary_action": "visual_candidate_update",
    "human_review_needed": false,
    "notes": "카톡이 interface anchor임에도 notification_ops가 이김. interface_dominance 확인 필요."
  }
}
```

### 집계 필드

| 필드 | 집계 목적 |
| --- | --- |
| `override_source_type` | Layer 1 분포 — 어떤 종류의 실패가 가장 많은가 |
| `semantic_cause` | Layer 2 세부 — 어떤 의미 원인이 반복되는가 |
| `primary_action` | 다음 refinement cycle에서 어떤 작업이 가장 많이 필요한가 |
| `resolved_by_current_engine` | 이미 해결된 override인가 vs 잔존 gap인가 ([P5-A `gap_type` 구분과 동일](p5_override_pattern_analysis.md#primary_pattern-vs-gap_type)) |
| `human_review_needed` | analyzer가 자동 분류 불가한 케이스 비율 |

---

## 설계 결정 노트

### 1. `source_type` vs `semantic_cause` 분리

[P5-A](p5_override_pattern_analysis.md)의 `primary_pattern` vs `gap_type` 구분과 같은 논리다.  
**"어느 layer에서 실패했는가"**와 **"왜 실패했는가"**는 다른 질문이고, 집계 시 두 축을 교차하면 refinement 우선순위가 명확해진다.

> 예: `CANDIDATE_WRONG_TOP` + `WT-05`가 가장 많으면 → ontology boundary 정비가 다음 sprint

### 2. `PHILOSOPHY_MISMATCH`를 별도 source_type으로 분리

기술적으로 맞게 추천했으나 사용자가 override한 케이스는 scoring/metadata 수정이 아니라 **철학 재정의**가 필요하다.  
이 유형을 WT나 NT로 흡수하면 잘못된 technical fix로 이어질 위험이 있다.

→ 축소판 [핵심 원칙](feedback_override_taxonomy.md): *"override는 기존 추천 철학의 예외일 수도 있고, 철학 수정 신호일 수도 있다."*

### 3. `resolved_by_current_engine` 필드

[P5-A 핵심 교훈](p5_override_pattern_analysis.md#혼동하기-쉬운-조합-candidate_gap--gap_typenull) — 과거 override를 **현재 엔진 기준**으로 재평가해야 "이미 해결된 것"과 "아직 남은 gap"을 혼동하지 않는다.  
Feedback Statistics Analyzer에서 이 필드로 먼저 필터링한 뒤 집계해야 stale override가 refinement priority를 오염시키지 않는다.

### 4. `human_review_needed`

`NT-03` (`stage_ambiguous`) + `NT-05` (`object_vs_channel`) + PM 계열은 자동 분류가 어려운 케이스가 섞인다.  
이 비율을 별도로 추적해야 analyzer 신뢰도를 평가할 수 있다.

---

## 축소 구현 ↔ 본 설계안 매핑

| 축소판 ([feedback_override_taxonomy.md](feedback_override_taxonomy.md)) | Hermes 설계안 (본 문서) |
| --- | --- |
| `source_type` | Layer 1 `override_source_type` |
| `cause_type` | Layer 2 `semantic_cause` (코드 없이 label 수준) |
| `action_hint` | Layer 3 `primary_action` / `secondary_action` |
| `resolved_by_current_engine` | 동일 |
| `human_review_needed` | 동일 |
| `notes` | 동일 |
| CA-01, WT-05, NT-04 등 세부 코드 | **100건 분석 후** Layer 2 확장 |
