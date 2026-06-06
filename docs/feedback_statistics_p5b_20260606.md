# P5-B Feedback Statistics Summary — 2026-06-06

## 1. 목적

P5-B 분석도구(`tools/analyze_feedback_overrides.py`)는 **추천 로직을 직접 수정하지 않습니다**.

수집된 override / accepted / no_candidate 피드백을 taxonomy·workflow·visual·gap type 관점에서 집계하고, 이후 refinement(boundary 수정, catalog 보강, scoring 조정)의 **우선순위를 정하기 위한 관측 단계**입니다.

관련 taxonomy 정의: [`docs/feedback_override_taxonomy.md`](feedback_override_taxonomy.md)

---

## 2. 입력 데이터

| 항목 | 값 |
| --- | --- |
| 입력 파일 | `data/override_examples.json` |
| 분석 건수 | 109건 |
| 도구 | `tools/analyze_feedback_overrides.py` |

---

## 3. 실행 명령

```bash
python tools/analyze_feedback_overrides.py
python tools/analyze_feedback_overrides.py --json
python tools/analyze_feedback_overrides.py --input data/override_examples.json --top 10
python tools/analyze_feedback_overrides.py --check-current-engine --only-active-gaps --export-labeling-md reports/p5b_active_gap_labeling.md
python tools/analyze_feedback_overrides.py --check-current-engine --only-active-gaps --export-labeling-csv reports/p5b_active_gap_labeling.csv
python tools/analyze_feedback_overrides.py --check-current-engine
python tools/analyze_feedback_overrides.py --check-current-engine --json
```

---

## 4. Overall Summary

| 항목 | 건수 | 비율 |
| --- | ---: | ---: |
| Total | 109 | 100% |
| Overrides | 78 | 71.6% |
| Accepted | 31 | 28.4% |
| No candidate (`없음`) | 15 | 13.8% |

---

## 5. Taxonomy Distribution

override 78건 기준 자동 분류 분포:

| taxonomy | count | ratio |
| --- | ---: | ---: |
| personal_preference | 20 | 25.6% |
| boundary_ambiguity | 20 | 25.6% |
| no_candidate | 15 | 19.2% |
| action_vs_object | 14 | 17.9% |
| channel_vs_object | 4 | 5.1% |
| workflow_mismatch | 2 | 2.6% |
| visual_mismatch | 2 | 2.6% |
| object_vs_status | 1 | 1.3% |

`personal_preference`와 `boundary_ambiguity`가 각각 약 1/4을 차지합니다. 키워드 기반 추정이므로 수동 라벨링으로 검증이 필요합니다.

---

## 6. Workflow Override Summary

| workflow | override 건수 | total | override ratio | 비고 |
| --- | ---: | ---: | ---: | --- |
| document | 22 | 39 | 56.4% | 가장 많은 override 절대 건수 |
| communication | 7 | 9 | 77.8% | 채널·전달 계열 |
| education_fieldwork | 5 | 5 | 100% | **표본 5건 — 일반화 주의** |

`education_fieldwork`는 전체 109건 중 5건뿐이므로 100% override ratio라도 workflow 전체 실패율로 해석하면 안 됩니다.

---

## 7. Engine Gap Type Summary

현재 `visual_candidates.json` + 추천 엔진 기준 (override 78건):

| gap_type | count | ratio |
| --- | ---: | ---: |
| candidate_gap | 23 | 29.5% |
| metadata_gap | 19 | 24.4% |
| ambiguous_channel | 12 | 15.4% |
| keyword_gap | 1 | 1.3% |

`candidate_gap`과 `metadata_gap`은 boundary 수정과 별도로 catalog / metadata 보강 후보로 분리해야 합니다.

---

## 8. Visual Transition Highlights

| transition | count | 가능한 해석 |
| --- | ---: | --- |
| 💰 → 💻 | 2 | 비용/예산보다 시스템·행정 내부 등록 작업을 사용자가 더 강하게 인식 |
| 없음 → 🚮 | 2 | 삭제/정리/폐기 계열 candidate gap — catalog에 해당 visual 후보 부재 |
| 📄 → 📞 | 2 | 문서·대상물보다 전화/문의/확인 채널이 우선 — document vs communication boundary |

---

## 9. Interpretation

1. **override 71.6%는 전체 추천 실패율이 아닙니다.** 현재 데이터는 Notion에서 수동으로 모은 override 분석용 샘플로, accepted·override가 혼재하지만 override 사례가 의도적으로 많이 포함되어 있을 가능성이 큽니다.

2. **`personal_preference` 25.6%**는 note의 “연상/색/선호” 키워드 추정치입니다. 과대 분류 가능성이 있으므로 `reports/p5b_active_gap_labeling.md`에서 수동 검토가 필요합니다.

3. **`boundary_ambiguity` 25.6%**는 semantic boundary workflow(snapshot → before/after diff → regression 확인)로 넘기기 **전** 사람이 케이스를 좁혀야 합니다.

4. **`candidate_gap`(23) + `metadata_gap`(19)**는 ontology boundary와 분리해 catalog / metadata 보강 backlog로 관리해야 합니다.

---

## 10. Current Engine Recheck (2026-06-06)

과거 override를 현재 엔진에 재실행한 결과 (전체 109건 / override 78건):

| 지표 | 전체 | override만 |
| --- | ---: | ---: |
| resolved_by_current_engine | 59 | 29 |
| active_gap | 49 | 49 |
| still_no_candidate | 4 | 4 |
| partial_match | 3 | 3 |

- **29건**은 과거 override였으나 현재 엔진이 final visual과 일치 → **stale override** (boundary 수정 전 제외 대상)
- **49건**은 여전히 active gap → 수동 라벨링·boundary candidate 선정의 1차 대상
- **4건**은 현재도 후보 없음 → catalog 추가 우선

---

## 11. Next TODO

1. ~~수동 라벨링 export 생성~~ → `reports/p5b_active_gap_labeling.md` / `.csv` (active gap 49건)
2. ~~current engine recheck로 stale override와 active gap 분리~~ → `--check-current-engine`
3. **active_gap 49건만** 대상으로 수동 라벨링 (`source_type_manual`, `action_hint_manual`)
4. boundary candidate 3~5개 export 생성
5. `no_candidate` 15건을 catalog_gap / keyword_gap / metadata_gap으로 세분화
6. P5-A(`analyze_override_patterns.py`) vs P5-B(`analyze_feedback_overrides.py`) 역할 구분 문서화

---

## 12. 권장 후속 순서

```text
1~3단계 수행 (본 문서 + labeling export + engine recheck)
↓
active_gap 49건만 수동 라벨링
↓
boundary candidate 3~5개 선정
↓
ontology / metadata / scoring 수정 (semantic boundary workflow 절차 준수)
```
