# Feedback UI MVP (Phase 6)

## 목적

실사용 업무 제목을 입력하고 추천 결과에 대해 **accepted / override / no_candidate**를 기록하여
`data/feedback_log.jsonl`을 계속 쌓는 **내부 실험용 UI**이다.

- 공개 배포·로그인·Notion 자동 삽입은 범위 밖
- boundary 정책 수정은 범위 밖 (쌓인 로그는 P5-B analyzer로 별도 Phase에서 분석)

## 핵심 루프

1. 제목 입력
2. `POST /recommend-icon` 실행
3. top candidates + 추천 visual 확인
4. 사용자 선택 기록 (`POST /feedback`)
5. `data/feedback_log.jsonl` append
6. 추후 `tools/export_feedback_jsonl_to_override_examples.py` → P5-B analyzer 입력

## 저장 canonical

| 저장소 | Phase 6 MVP |
|--------|-------------|
| `data/feedback_log.jsonl` | **UI feedback write path (canonical)** |
| `logs/recommendation_log.jsonl` | 추천 실행 관측 (gitignored) |
| `data/feedback_log.json` | Layer A array — **MVP 범위 제외** |

`recommendation_id`(UUID)로 recommendation log ↔ feedback log를 상관한다.

## API 계약

### POST /recommend-icon

기존 `visual`, `reason` 유지 + 확장 필드.

**성공 (후보 있음)**

```json
{
  "recommendation_id": "uuid",
  "visual": { "type": "emoji", "value": "📄", "color": null },
  "reason": "...",
  "no_candidate": false,
  "recommendation_path": "visual_candidates",
  "candidates": [
    {
      "rank": 1,
      "candidate_id": "document_review",
      "visual": { "type": "emoji", "value": "📄", "color": null },
      "score": 0.892,
      "label": "문서 검토",
      "summary_reason": "제목에「확인」가 포함됨"
    }
  ]
}
```

**no_candidate (HTTP 200 — 오류 아님, 관측 이벤트)**

```json
{
  "recommendation_id": "uuid",
  "visual": null,
  "reason": "적합한 후보를 찾지 못했습니다.",
  "no_candidate": true,
  "recommendation_path": "no_candidate",
  "candidates": []
}
```

`recommendation_path` 값: `sample_cases_exact_match` | `visual_candidates` | `no_candidate`

### POST /feedback

```json
{
  "recommendation_id": "uuid-or-null",
  "input_title": "보고서 확인",
  "feedback_type": "accepted | override | no_candidate",
  "system_recommended_visual": { "type": "emoji", "value": "📄" },
  "final_selected_visual": { "type": "emoji", "value": "📄" },
  "override_reason": "wrong_top_candidate",
  "user_note": "optional"
}
```

- `feedback_type=no_candidate` → 내부 저장값 `no_candidate_selected`
- `override_reason` 필수: `override`일 때만 (enum 아래)
- `manual_without_recommendation`: 시스템 추천 없이 사용자가 visual 직접 입력 (override UI에서 no_candidate 후 manual 선택)

**override_reason enum (MVP 고정)**

- `wrong_top_candidate`
- `catalog_gap`
- `action_vs_object`
- `channel_vs_object`
- `document_vs_status`
- `boundary_ambiguity`
- `personal_preference`
- `other`

### GET /feedback/recent?limit=20

최근 feedback JSONL 항목 (역순).

### GET /visuals/catalog

override picker용 `{ candidate_id, visual, label }[]`.

## 화면 (/ui/feedback)

| 섹션 | 내용 |
|------|------|
| 입력 | title input + recommend button |
| 결과 | top candidates (label, visual, score, summary_reason) + 추천 visual/reason |
| 액션 | Accept / Override / No candidate |
| Override | catalog dropdown **+** manual input (type, value, color) |
| 사유 | correction reason `<select>` |
| 최근 | recent feedback 20건 preview |

## Override 입력

catalog에 없는 visual 직접 입력을 지원한다 (catalog_gap 분석에 중요).

- `type`: `emoji` | `notion_icon`
- `value`: 필수
- `color`: optional (notion_icon)

## P5-B 연동

Layer A append 없이, JSONL → override_examples 호환 export:

```bash
python tools/export_feedback_jsonl_to_override_examples.py
python tools/export_feedback_jsonl_to_override_examples.py --output data/override_examples_from_ui.json
```

변환 규칙:

- `recommended_visual`: system visual display string; 없으면 `"없음"`
- `final_visual`: final visual display string
- `note`: `override_reason` + `user_note` 합침
- `source`: `feedback_ui`

## 하지 않을 것

- Notion 자동 삽입
- React / Vite / SPA 프레임워크
- 사용자 계정·로그인
- `data/feedback_log.json` Layer A append
- boundary·scoring·ontology 수정
- 예쁜 대시보드 (feedback loop 우선)
