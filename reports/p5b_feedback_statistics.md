# P5-B Feedback Statistics

> Visual workflow indexing system observability — cognitive stability over raw accuracy.

## Executive Summary

- **Total logs:** 28
- **Override rate:** 25.0% (7/28)
- **Unstable accept rate:** 7.7% (1/13 accepted)
- **Unsure accept rate:** 61.5% (8 accepted)
- **Ambiguity rate (margin ≤ 0.03):** 25.0%

## Overall Metrics

| metric | count |
| --- | ---: |
| total logs | 28 |
| accepted | 13 |
| override | 7 |
| no_candidate | 8 |

## Acceptance Metrics

- stable_accept: **30.8%** (4)
- unstable_accept: **7.7%** (1)
- unsure_accept: **61.5%** (8)
- margin threshold: `0.03`

## Override Metrics

| taxonomy | count | ratio |
| --- | ---: | ---: |
| wrong_recommendation | 4 | 57.1% |
| boundary_disagreement | 2 | 28.6% |
| ranking_instability | 1 | 14.3% |
| metadata_gap | 0 | 0.0% |

## Ranking Metrics (top1 − top2 margin)

- count with margin: 12
- p50: 0.011
- p75: 0.057
- p90: 0.066
- minimum: 0.0
- maximum: 0.1
- mean: 0.028

## Ambiguity Metrics

### margin ≤ 0.01: 6 cases (21.4%)

**By workflow (top):**
- `folder_organization`: 2
- `mail_action`: 1
- `running_appointment`: 1
- `document_review`: 1
- `training_session_attendance`: 1

**By visual (top):**
- `📁`: 2
- `📧`: 1
- `🏃`: 1
- `📄`: 1
- `🧑‍🏫`: 1

### margin ≤ 0.03: 7 cases (25.0%)

**By workflow (top):**
- `folder_organization`: 2
- `mail_action`: 1
- `running_appointment`: 1
- `document_review`: 1
- `document_reporting`: 1
- `training_session_attendance`: 1

**By visual (top):**
- `📁`: 2
- `📧`: 1
- `🏃`: 1
- `📄`: 1
- `🗣️`: 1
- `🧑‍🏫`: 1

### margin ≤ 0.05: 8 cases (28.6%)

**By workflow (top):**
- `document_review`: 2
- `folder_organization`: 2
- `mail_action`: 1
- `running_appointment`: 1
- `document_reporting`: 1
- `training_session_attendance`: 1

**By visual (top):**
- `📄`: 2
- `📁`: 2
- `📧`: 1
- `🏃`: 1
- `🗣️`: 1
- `🧑‍🏫`: 1

## Top Risk Workflows

| workflow | count | override_rate | ambiguity_rate | unstable_accept | ranking_instability |
| --- | ---: | ---: | ---: | ---: | ---: |
| mail_action | 1 | 100.0% | 100.0% | 0 | 0 |
| running_appointment | 1 | 100.0% | 100.0% | 0 | 0 |
| training_session_attendance | 1 | 100.0% | 100.0% | 0 | 0 |
| folder_organization | 2 | 50.0% | 100.0% | 1 | 1 |
| document_reporting | 4 | 50.0% | 25.0% | 0 | 0 |
| coding | 2 | 50.0% | 0.0% | 0 | 0 |
| document_review | 2 | 0.0% | 50.0% | 0 | 0 |
| approval_request | 1 | 0.0% | 0.0% | 0 | 0 |
| food_meeting | 1 | 0.0% | 0.0% | 0 | 0 |
| no_candidate | 7 | 0.0% | 0.0% | 0 | 0 |

## Top Risk Visuals

| visual | count | avg_margin | override_rate | unstable_accept |
| --- | ---: | ---: | ---: | ---: |
| 📧 | 1 | 0.0 | 100.0% | 0 |
| 🧑‍🏫 | 1 | 0.0 | 100.0% | 0 |
| 🏃 | 1 | 0.002 | 100.0% | 0 |
| 📁 | 2 | 0.001 | 50.0% | 1 |
| 🗣️ | 4 | 0.02 | 50.0% | 0 |
| angle-brackets-solidus (blue) | 2 | 0.1 | 50.0% | 0 |
| grid-rectangle-2x3 (green) | 1 | — | 0.0% | 0 |
| 💰 | 1 | — | 0.0% | 0 |
| 📌 | 1 | — | 0.0% | 0 |
| 📄 | 1 | 0.032 | 0.0% | 0 |

## Boundary Candidates

- low_margin_top2_collision (4)
- action_vs_object (3)
- interface_vs_semantic (2)
- channel_vs_document (1)

## Recommended Next Actions

### Immediate

- Add metadata boost/penalty for near-tie pairs flagged as ranking_instability.
- Catalog gap backlog: 8 no_candidate events.

### Medium

- Run semantic boundary workflow pilots on top ambiguous workflow pairs.
- Extend candidate ontology for recurring boundary_disagreement clusters.

### Long Term

- Introduce ranking confidence score in API/UI.
- Add accepted memo / quality signal in feedback schema.
- Surface ranking explanation (top2 + margin) in feedback UI.
