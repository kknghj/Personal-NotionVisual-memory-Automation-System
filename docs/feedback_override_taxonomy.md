# Feedback Override Taxonomy

> P5-B **축소 구현** 버전. 전체 설계는 [Hermes 최종 설계안 (2026-06-05)](feedback_override_taxonomy_proposal_20260605.md) 참고.

## 목적
override feedback을 단순 예외가 아니라 추천 시스템 개선을 위한 관측 데이터로 분류한다.

## 핵심 원칙
- feedback log는 추천 철학을 보호하지 않는다.
- override는 기존 추천 철학의 예외일 수도 있고, 철학 수정 신호일 수도 있다.
- 초기 구현은 단순 taxonomy로 시작하고, 누적 데이터가 충분해지면 세분화한다.

## P5-B 최소 구현 필드

| 필드 | Hermes 설계안 대응 |
| --- | --- |
| `source_type` | Layer 1 `override_source_type` |
| `cause_type` | Layer 2 `semantic_cause` (label 수준) |
| `action_hint` | Layer 3 `primary_action` |
| `resolved_by_current_engine` | [P5-A `gap_type`](p5_override_pattern_analysis.md#primary_pattern-vs-gap_type)과 동일 논리 |
| `human_review_needed` | 동일 |
| `notes` | 동일 |

## 장기 확장 방향

Hermes taxonomy의 3-layer 구조를 따른다.  
→ 출처: [feedback_override_taxonomy_proposal_20260605.md](feedback_override_taxonomy_proposal_20260605.md) (Hermes 최종 설계안, 2026-06-05)

1. Override Source Type — Layer 1 `override_source_type`
2. Semantic Cause — Layer 2 `semantic_cause`
3. Action Mapping — Layer 3 `primary_action` / `secondary_action`

## 현재는 구현하지 않는 세부 항목

**CA-01**, **WT-05**, **NT-04** 등 세부 코드는 [Hermes 설계안](feedback_override_taxonomy_proposal_20260605.md#layer-2-semantic-cause)에 보관하되, 100건 분석 이후 필요할 때 확장한다.