# P5-B Feedback Schema v2 Plan

> Implemented: accepted memo, ranking snapshot denormalization, low-confidence accept UI.

## 1. 변경한 schema

### Accepted 전용 (신규)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `accept_quality` | `stable` \| `unstable` \| `unsure` | 사용자가 인지한 accept 안정성 |
| `ranking_confidence_note` | string \| null | accepted 시 선택적 메모 |

### Ranking snapshot (accepted / override / no_candidate 공통, optional)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `top1_candidate_id` | string \| null | 당시 1순위 candidate |
| `top1_visual` | string \| null | display string (예: 📁) |
| `top1_score` | number \| null | calibration score |
| `top2_candidate_id` | string \| null | 2순위 candidate |
| `top2_visual` | string \| null | display string |
| `top2_score` | number \| null | calibration score |
| `top1_top2_margin` | number \| null | top1 − top2 |
| `ranking_confidence` | `low` \| `medium` \| `high` \| `unknown` | margin 기반 confidence |

### 기존 필드 (유지)

`recommendation_id`, `input_title`, `system_recommended_visual`, `final_selected_visual`, `feedback_type`, `override_reason`, `user_note`, `accepted_system_recommendation`, `timestamp`

## 2. 기존 로그와의 호환 방식

- v1 JSONL (28건)은 필드 없이 그대로 분석 가능.
- Analyzer 우선순위:
  1. `feedback_log.top1_top2_margin`
  2. `recommendation_log` join (`ambiguity_gap` / candidates)
- `accept_quality` 없으면 margin threshold(0.03)로 `stable_accept` / `unstable_accept` / `unsure_accept` 추론.
- `recommendation_id` join 방식은 유지.

## 3. accepted memo가 필요한 이유

실사용에서 **추천은 맞지만 ranking이 불안정**한 경우, accepted에 메모가 없어 사용자가 같은 `recommendation_id`에 override를 추가 기록함 (folder vs taxi, margin 0.001).

이 패턴은 override rate를 부풀리고 taxonomy를 왜곡함.  
→ accepted에 `ranking_confidence_note` + `accept_quality`로 **관측 의도를 정확히 기록**.

## 4. low confidence UI 동작 방식

조건: `top1_top2_margin < 0.03`

1. Accept 버튼 위에 경고 배너 표시 (top2 visual, margin)
2. Accept quality 라디오 + optional note 영역 표시
3. 기본 선택: margin 기준 auto (`unstable`)
4. 메모 없이 Accept 가능 (quality만 저장)

margin ≥ 0.03이면 패널 숨김, 서버가 `accept_quality=stable` 기본값 설정.

## 5. ranking_confidence 규칙

```text
margin < 0.03        → low
0.03 <= margin < 0.07 → medium
margin >= 0.07       → high
margin 없음          → unknown
```

## 6. 다음 피드백 수집 시 확인할 지표

| 지표 | 목표 관찰 |
| --- | --- |
| `accept_quality=unstable` 비율 | low margin accept에서 사용자 자기 인식과 시스템 margin 일치 여부 |
| `ranking_confidence_note` 작성률 | unstable accept 중 메모 남긴 비율 |
| duplicate `recommendation_id` (accepted+override) | v2 이후 감소해야 함 |
| override used as ranking memo | 동일 visual override 감소 |
| snapshot 필드 채움률 | `top1_top2_margin` null 비율 |

## 7. 구현 파일

- `app/feedback_ranking_snapshot.py` — snapshot / confidence helpers
- `app/feedback_logging.py` — log entry 확장
- `app/feedback_api.py` — POST /feedback 저장
- `app/models.py` — `RankingSnapshotInput`, `accept_quality`
- `app/static/feedback/*` — low confidence UI
- `app/p5b_feedback_analyzer.py` — v2 필드 우선 분석

## 8. 의도적으로 하지 않은 것

- scoring / ontology / boundary 수정
- threshold 정책 변경
- catalog 확장
