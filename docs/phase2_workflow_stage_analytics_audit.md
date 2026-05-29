# Phase 2 — workflow_stage analytics audit

## Scope

Analytics compatibility only (flat vs `observations.workflow_stage`). No scoring, penalties, or UI changes.

## Files that read workflow_stage observation fields

| File | Role | Direct flat reads | Action |
|------|------|-------------------|--------|
| `tools/analyze_workflow_stage_observations.py` | Primary aggregation (confusion, calibration, mismatch) | Yes | Normalize + read `observations.workflow_stage` |
| `tools/export_feedback_observations_from_scoring_log.py` | Scoring log → feedback_log export | Yes (filter + build) | Normalize + read slice for detection/build |
| `tools/analyze_current_state_experiment.py` | Manifest experiment reporting | Yes | Normalize per log row |
| `tools/generate_ranking_snapshots.py` | Snapshot summaries (`_workflow_stage_experiment_analysis`, `_false_certainty_cases`, `_stage_fields`) | Yes | Normalize per row |

## Out of audit scope (not workflow_stage analytics)

- `app/workflow_stage_observation.py` — observation **producer** (scoring attach), not analytics consumer
- `app/semantic_scoring.py` — inference engine
- `tools/generate_ambiguity_scoring_log.py` — log generation
- `tests/test_workflow_stage_*.py` — scoring/observation unit tests, not feedback analytics
- Semantic boundary / ranking snapshot diff tools (non–workflow_stage)

## Strategy

1. `normalized = normalize_feedback_event(event)` per row/event
2. `workflow_stage = normalized.get("observations", {}).get("workflow_stage", {})`
3. Use `workflow_stage` for all Layer B fields; keep row-level fields (`title`, `top_candidate`, `recommended_candidate_id`, rankings) on the original row

No new helper abstractions (`get_observation_slice`, etc.).

## Regression (2026-05-29)

Representative log: `tests/ambiguity/ambiguity_results/2026-05-21_current_state_workflow_stage_log.json`

Compared `tools/analyze_workflow_stage_observations.py` output to committed baseline `tests/ambiguity/ambiguity_results/current_state_workflow_stage_analytics.json`.

**Result:** identical metrics (145 total rows, 66 stage rows, same confusion matrix, mismatch rate 0.015, etc.). No intentional differences for flat scoring-log input.

New tests: `tests/test_workflow_stage_analytics_compatibility.py` (flat, nested-only, mixed, no-stage skip, flat/nested equivalence, nested export).
