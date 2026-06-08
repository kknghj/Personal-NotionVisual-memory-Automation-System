# Micro-Tune Diff Summary

- before: `tests/ambiguity/ambiguity_results/2026-06-08_schedule_metadata_microtune_before_scoring_log.json`
- after: `tests/ambiguity/ambiguity_results/2026-06-08_schedule_metadata_microtune_after_scoring_log.json`
- compared titles: 206

## changed top1

- 노션 일정 공유
  work_calendar_organization -> notion_docs_touchup
  semantic_bonus: 2 -> 0 (visibility/tone drift removed)

## stable (scope drift target)

- 캘린더 일정 공유: work_calendar_organization -> work_calendar_organization
  semantic_bonus: 2 -> 2 (calendar schedule share explicit boost)

## movement metrics

- top1 movement: 1 (노션 일정 공유 only)
- high_ambiguity: 90 -> 90
- tie: unchanged
- no-candidate: 3 -> 3
- regression candidates: none
