# P5-B Feedback Insights

## Philosophy Check

This analyzer treats **workflow recall speed** and **cognitive stability** as primary
signals. Override is not always failure; accepted is not always high confidence.

## Taxonomy Sufficiency

- **wrong_recommendation:** 57.1% of overrides — true top1 errors.
- **boundary_disagreement:** 28.6% — both candidates semantically plausible.
- **ranking_instability:** 14.3% — correct visual, low margin.
- **metadata_gap:** 0.0% — weak scoring differentiation.

The four-class override taxonomy **captures live UI behavior** better than legacy accepted/override ratios alone. `wrong_top_candidate` UI reason still mixes true errors with ranking-instability memos — keep analyzer reclassification.

## Gaps Observed

- **Duplicate feedback on same recommendation_id:** 1 case(s). Users re-filed override memos when accepted lacked a note field (e.g. folder vs taxi at margin 0.001).
- **Unstable accepts without user note:** 9/9 — silent low-confidence accepts.
- **Override used as ranking memo:** 1 override(s) where system visual matched final selection.

## Accepted Memo Feature

**Recommendation: yes — pilot accepted memo / quality flag.**

Proposed schema extension:

```json
{
  "accept_quality": "stable | unstable | unsure",
  "ranking_confidence_note": "optional string",
  "top2_candidate_id": "optional correlation field"
}
```

UI: optional collapsible note on Accept when margin ≤ threshold.

## Feedback Schema Extensions

| field | purpose |
| --- | --- |
| `accept_quality` | stable vs unstable accept without fake override |
| `analyzer_override_class` | persisted post-hoc taxonomy for dashboards |
| `top1_top2_margin` | snapshot at feedback time (denormalized from rec log) |
| `top2_candidate_id` | boundary review / ontology work |
| `semantic_boundary_tags[]` | action/object, channel/document, etc. |

Keep observation-first: analyzer computes classes today; persist only after policy review.

## Boundary Backlog Signals

- `low_margin_top2_collision` — 4 hit(s)
- `action_vs_object` — 3 hit(s)
- `interface_vs_semantic` — 2 hit(s)
- `channel_vs_document` — 1 hit(s)

## Next Experiments

- channel_vs_document boundary tests for reporting/전달 titles
- raise tie-break weight or semantic bonus floor for unstable accepts

## Human Review Queue

| title | feedback | class | margin | note |
| --- | --- | --- | ---: | --- |
| 메일 미열람 자치구 담당자 전화 | override | wrong_recommendation | 0.0 | 메일 미열람은 전화하게 된 배경 정보이고, 실제 업무 행동은 담당자에게 전화하는 것임. |
| AI 단기 교육위탁 사전협의서 제출 | override | wrong_recommendation | 0.0 | — |
| 재택 필요 자료 드라이브 이동 | accepted | unstable_accept | 0.001 | — |
| 재택 필요 자료 드라이브 이동 | override | ranking_instability | 0.001 | 폴더 추천은 맞음. 다만 taxi_service와 score 차이가 0.001로 거의 동점이라 ranking |
| 동기 점심 약속 | override | boundary_disagreement | 0.002 | — |
| 강사 활동 보고 제출시 유의사항 전달 | override | boundary_disagreement | 0.02 | 제목에 '보고'가 포함되어 있지만 보고서를 작성·검토·제출하는 업무가 아니다. 핵심 workflow는 강사에 |
