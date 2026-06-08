# Snapshot Diff Summary

- before: `tests/ambiguity/ambiguity_results/2026-06-08_schedule_metadata_pilot_before_scoring_log.json`
- after: `tests/ambiguity/ambiguity_results/2026-06-08_schedule_metadata_pilot_after_scoring_log.json`
- compared titles: 206

## changed top1

- 노션 일정 공유
  notion_docs_touchup -> work_calendar_organization
  semantic_bonus: 0 -> 2
- 캘린더 일정 공유
  running_appointment -> work_calendar_organization
  semantic_bonus: 0 -> 2

## semantic improvements

- 노션 일정 공유: semantic_bonus: 0 -> 2
- 캘린더 일정 공유: semantic_bonus: 0 -> 2
- 표창 제작시기 확인: runner-up schedule row semantic_bonus: 0 -> 22 (top1 pair rule row unchanged)

## regression candidates

- (none among required regression titles)

## ambiguity changes

- tie count: 13 -> 13 (delta 0)
- high_ambiguity: 91 -> 90 (delta -1)

- 표창 제작시기 확인: ambiguity_gap=0.0690 -> ambiguity_gap=0.0690
  - ambiguity_gap unchanged; schedule metadata enriches runner-up only

## movement clusters

- notion_docs_touchup -> work_calendar_organization: 1
- running_appointment -> work_calendar_organization: 1

## pilot target notes (manual verification; not all in ambiguity test set)

| title | before top1 | after top1 |
| --- | --- | --- |
| 알뜰폰 할인종료일 확인 | document_review | work_calendar_organization |
| 할인종료일 확인 | document_review | work_calendar_organization |
| 혜택 마감일 확인 | document_review | deadline_management |
| 신청 마감일 확인 | document_review | deadline_management |
