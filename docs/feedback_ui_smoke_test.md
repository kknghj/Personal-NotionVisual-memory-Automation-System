# Feedback UI Smoke Test Checklist (Phase 6)

서버가 실행 중일 때 (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`) 아래 순서대로 확인한다.

**사전 조건**

- `http://localhost:8000` 응답 가능
- `data/feedback_log.jsonl` — 없으면 첫 feedback 시 자동 생성
- `logs/recommendation_log.jsonl` — 없으면 첫 추천 시 자동 생성 (gitignored)

---

## 체크리스트

| # | 확인 항목 | 입력 예시 | 기대 결과 | 확인 파일 / 위치 |
|---|-----------|-----------|-----------|------------------|
| 1 | `/ui/feedback` 접속 | 브라우저에서 `http://localhost:8000/ui/feedback/` | Feedback UI 로드: 제목 입력, **추천 실행**, Accept / Override / No candidate, Recent feedback 테이블 표시. CSS/JS 404 없음 | 브라우저 DevTools Network (200) |
| 2 | 추천 성공 1건 | 제목: **`보고서 확인`** → **추천 실행** | 상태: `추천 완료`. `recommendation_id`·`path: visual_candidates` 표시. top visual(📄 등) + **Top candidates** 1~3건 (`label`, `score`, `summary_reason`). `no_candidate` 배지 없음 | UI 결과 패널; (선택) `POST /recommend-icon` 응답 JSON |
| 3 | accepted 저장 | #2 직후 **Accept 추천** 클릭 | `저장됨 (accepted)`. Recent 테이블 최상단: `feedback_type=accepted`, system → final 동일 visual | `data/feedback_log.jsonl` 마지막 줄: `"feedback_type":"accepted"`, `"accepted_system_recommendation":true` |
| 4 | override 저장 (catalog) | 제목: **`점심 카톡 확인`** → 추천 → Catalog에서 **추천과 다른** 후보 선택 → reason: **`wrong_top_candidate`** → **Override 저장** | `저장됨 (override)`. Recent: system(💬 등) → final(다른 visual). `override_reason=wrong_top_candidate` | `data/feedback_log.jsonl`: `"feedback_type":"override"`, system/final visual 상이 |
| 5 | direct visual 입력 저장 | 제목: **`보고서 확인`** → 추천 → Catalog 미사용, 직접 입력: type **`notion_icon`**, value **`airplane`**, color **`blue`**, reason: **`catalog_gap`**, 메모: `smoke direct input` → **Override 저장** | `저장됨 (override)` 또는 system 없을 때 `manual_without_recommendation`. final: `airplane (blue)` | `data/feedback_log.jsonl`: `final_selected_visual.value` = `"airplane"`, `override_reason` = `"catalog_gap"` |
| 6 | no_candidate 저장 | 제목: **`교육자료 정리`** → **추천 실행** → **No candidate** 클릭 | 추천: `no_candidate (200)` 배지, visual 없음. 저장: `no_candidate_selected` | `data/feedback_log.jsonl`: `"feedback_type":"no_candidate_selected"`, `system_recommended_visual` null 가능 |
| 7 | `/feedback/recent` 반영 | UI **새로고침** 또는 `GET http://localhost:8000/feedback/recent?limit=20` | #3~#6에서 저장한 **4건** (역순, 최신이 위) 표시. 각 row에 `timestamp`, `input_title`, `feedback_type`, system→final | API JSON; UI Recent feedback 테이블 |
| 8 | `feedback_log.jsonl` 기록 | #3~#6 수행 후 파일 열기 | JSONL **4줄** (또는 기존 +4). 각 줄 필수: `timestamp`, `recommendation_id`, `input_title`, `feedback_type`, `accepted_system_recommendation` | `data/feedback_log.jsonl` |
| 9 | `recommendation_id` 연결 | #2 또는 #4 추천 직후 UI에 표시된 `recommendation_id` 복사 → 해당 feedback 줄과 recommendation log 대조 | feedback 줄의 `recommendation_id` = recommendation log **같은 UUID** 1줄. recommendation log: `input_title` 일치, `recommended_visual` / `no_candidate` 상태 일치 | `data/feedback_log.jsonl` + `logs/recommendation_log.jsonl` |
| 10 | export CLI 실행 | 프로젝트 루트에서: `python tools/export_feedback_jsonl_to_override_examples.py --output data/override_examples_from_ui.json` | stdout: `Wrote N rows to ...` (N ≥ 4). 출력 JSON 배열, 각 항목: `title`, `recommended_visual`, `final_visual`, `source: "feedback_ui"`. no_candidate 건: `recommended_visual: "없음"` | `data/override_examples_from_ui.json` |

---

## API-only 빠른 확인 (선택)

```bash
# 추천 성공
curl -s -X POST http://localhost:8000/recommend-icon \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"보고서 확인\"}"

# no_candidate (200)
curl -s -X POST http://localhost:8000/recommend-icon \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"교육자료 정리\"}"

# recent
curl -s "http://localhost:8000/feedback/recent?limit=5"
```

---

## recommendation_id 연결 확인 방법 (상세)

1. `보고서 확인` 추천 → UI meta 줄의 UUID 복사 (예: `a1b2c3d4-...`)
2. `logs/recommendation_log.jsonl`에서 `"recommendation_id":"a1b2c3d4-..."` 검색
   - 기대: `"input_title":"보고서 확인"`, `"no_candidate":false`, `"recommended_visual"` 존재
3. Accept 후 `data/feedback_log.jsonl`에서 동일 UUID 검색
   - 기대: `"feedback_type":"accepted"`, 같은 `input_title`

---

## 실패 시 점검

| 증상 | 확인 |
|------|------|
| UI 404 | `app/static/feedback/` 존재, 서버 reload 후 재시도 |
| 추천 실패 | `data/sample_cases.json`, `data/visual_candidates.json` 로드 가능 여부 |
| feedback 저장 422 | override 시 `override_reason` enum 8개 중 하나 선택 여부 |
| recent 비어 있음 | `data/feedback_log.jsonl` 경로·쓰기 권한 |
| recommendation log 없음 | `logs/` 디렉터리 생성 여부; 추천 실행 시 append 오류 (서버 로그 warning) |
| export 0 rows | smoke test feedback 저장 선행 여부 |

---

## Pass 기준

- [ ] 1~10 모두 기대 결과 일치
- [ ] `recommendation_id` cross-check 1건 이상 성공
- [ ] export 출력에 smoke test 4건 반영
