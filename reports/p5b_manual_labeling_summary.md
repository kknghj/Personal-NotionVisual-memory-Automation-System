# P5-B Manual Labeling Summary

> Aggregated from manual labels in `reports/p5b_active_gap_labeling.csv`. Analysis-only — does not modify catalog or engine.

## 1. Overall

- total_rows: 49
- active_gap_rows: 49
- still_no_candidate_rows: 4
- completed_manual_rows: 49
- missing_manual_rows: 0
- active_gap with missing manual: 0
- generalizable_yes: 36
- generalizable_review: 12
- generalizable_no: 1

## 2. Manual Label Distribution

### source_type_manual

| value | count |
| --- | ---: |
| boundary_ambiguity | 15 |
| candidate_gap | 11 |
| workflow_mismatch | 9 |
| visual_mismatch | 8 |
| no_candidate | 4 |
| metadata_gap | 1 |
| personal_preference | 1 |

### cause_type_manual

| value | count |
| --- | ---: |
| visual_wrong_recall | 11 |
| object_vs_channel | 10 |
| object_priority | 7 |
| action_not_captured | 6 |
| catalog_gap | 6 |
| interface_ignored | 4 |
| context_vs_action | 2 |
| status_marker | 2 |
| personal_association | 1 |

### action_hint_manual

| value | count |
| --- | ---: |
| add_candidate | 19 |
| adjust_boundary | 15 |
| update_metadata | 9 |
| needs_more_data | 5 |
| keep_as_preference | 1 |

### generalizable_manual

| value | count |
| --- | ---: |
| yes | 36 |
| review | 12 |
| no | 1 |

## 3. Action Bucket Summary

| bucket | count |
| --- | ---: |
| add_candidate | 19 |
| update_metadata | 9 |
| adjust_boundary | 15 |
| defer | 6 |

## 4. Top Add Candidate Targets

| priority | score | id | title | suggested_direction | generalizable |
| --- | ---: | --- | --- | --- | --- |
| high | 9 | 54 | 제주도 비행기 예매 | travel_ticket / flight / ✈️ | yes |
| high | 9 | 108 | 세종 출장 KTX 예매 | train_reservation / KTX / 🚄 | yes |
| high | 9 | 109 | 부산 출장 숙소 예약 | lodging_reservation / hotel / 🏨 | yes |
| high | 7 | 55 | 기차표 예매 | train_reservation / KTX / 🚄 | yes |
| high | 7 | 73 | 센터별 운영실적 취합 | performance_aggregation / chart or document | review |
| medium | 5 | 5 | 알뜰폰 할인 종료일 | deadline_status / day calendar | yes |
| medium | 5 | 11 | 민방위 대피 훈련 | evacuation_training / emergency / 🚨 | yes |
| medium | 5 | 13 | 서울시 누리집 분야별 새소식 게시글 예약 | web_posting / social media post | yes |
| medium | 5 | 18 | 커피, 차 픽업 | beverage_pickup / coffee cup | yes |
| medium | 5 | 38 | 비상소집훈련 참석 | evacuation_training / emergency / 🚨 | yes |

## 5. Top Metadata Update Targets

| priority | score | id | title | suggested_direction | generalizable |
| --- | ---: | --- | --- | --- | --- |
| medium | 6 | 20 | 과일간식 짐 차에 싣기 | snack/food candidate should not overmatch fruit snack logistics | yes |
| medium | 6 | 21 | 재택 필요 자료 드라이브 업로드 | upload keywords should prefer folder-arrow-up over generic folder | yes |
| medium | 6 | 36 | 을지훈련 매트리스 상태 확인 | physical item inspection should prefer bed/mattress visual over document | yes |
| medium | 6 | 41 | 탕비실 간식 선호 조사 | snack/food candidate should not overmatch fruit snack logistics | yes |
| medium | 6 | 63 | 과장 주재 주간회의 참석 | internal_meeting should prefer people meeting over handshake | yes |
| medium | 6 | 74 | 운영지침 공문 발송 | document send/dispatch should prefer document-arrow-right over generic paper | yes |
| medium | 6 | 87 | 세금계산서 검토 | tax invoice review should prefer receipt over generic document | yes |
| medium | 4 | 2 | 식생활교육 보도자료 확인 | press release review should prefer newspaper over generic document | review |
| medium | 4 | 16 | 창의 정책 홍보 영상 제출 | video submission should prefer camera/video over document edit | review |

## 6. Top Boundary Adjustment Targets

| priority | score | id | title | boundary_question | generalizable |
| --- | ---: | --- | --- | --- | --- |
| high | 7 | 1 | 교육청 회의 오찬 장소 정하기 | 회의라는 맥락보다 오찬/식사 장소 선정 행위가 우선되어야 하는가? | yes |
| high | 7 | 3 | 회의실 예약 | 수당/여비/접수 확인 등 돈·문서 관련 대상보다 행정 내부 시스템 처리 행위가 우선되어야 하는가? | yes |
| high | 7 | 7 | 본인인증화면 수정 제안 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | yes |
| high | 7 | 8 | 4/9, 24 출장 여비 등록 | 수당/여비/접수 확인 등 돈·문서 관련 대상보다 행정 내부 시스템 처리 행위가 우선되어야 하는가? | yes |
| high | 7 | 9 | 자치구 담당자 공문 안내 협조 요청 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | yes |
| high | 7 | 12 | 보도자료 초안 검토 요청 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | yes |
| high | 7 | 47 | 교육청 주무관 안내 협조 요청 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | yes |
| high | 7 | 57 | 정보 공개 접수 확인 | 수당/여비/접수 확인 등 돈·문서 관련 대상보다 행정 내부 시스템 처리 행위가 우선되어야 하는가? | yes |
| high | 7 | 75 | 실적자료 제출 독촉 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | yes |
| high | 7 | 76 | 결과보고서 제출 요청 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | yes |

## 7. Deferred / Preference-only Cases

| id | title | action_hint | generalizable | source_type |
| --- | --- | --- | --- | --- |
| 23 | 노션 강의 수강 | needs_more_data | review | boundary_ambiguity |
| 37 | 헌혈 학습시간 인정 상신 | needs_more_data | review | boundary_ambiguity |
| 52 | 단기위탁 교육 신청 문의 | needs_more_data | review | boundary_ambiguity |
| 92 | 강사 섭외 후보 추리기 | needs_more_data | review | boundary_ambiguity |
| 93 | 강사 섭외 진행 | needs_more_data | review | boundary_ambiguity |
| 4 | 지피터스 AI 스터디 신청 | keep_as_preference | no | personal_preference |

## 8. Recommended Next 3~5 Fixes

### 1. Travel reservation candidates 추가 (🚄, ✈️, 🏨)
- 관련 사례 id: 54, 108, 109, 55
- 수정 유형: add_candidate
- 기대 효과: 출장·교통·숙박 예매 업무에서 still_no_candidate 및 visual mismatch 해소
- regression 위험: low
- 필요한 테스트: 기차표/KTX/비행기/숙소 예매 boundary test + ranking snapshot

### 2. Emergency drill / evacuation candidate 추가 (🚨, person running)
- 관련 사례 id: 11, 38
- 수정 유형: add_candidate
- 기대 효과: 비상훈련·대피 업무가 room_cleaning/training_session과 분리
- regression 위험: low-medium
- 필요한 테스트: 민방위/비상소집 boundary test

### 3. Organization chart / network candidate 추가
- 관련 사례 id: 106
- 수정 유형: add_candidate
- 기대 효과: 조직도·연락처 정비 업무에서 phone_call 오매칭 방지
- regression 위험: low
- 필요한 테스트: 조직도/연락처 정비 title ranking test

### 4. Web posting / social media post candidate 추가
- 관련 사례 id: 13
- 수정 유형: add_candidate
- 기대 효과: 온라인 게시 예약 업무 visual recall 개선
- regression 위험: low
- 필요한 테스트: 게시글 예약 title test

### 5. Metadata: snack/food candidate should not overmatch fruit snack logistics
- 관련 사례 id: 20
- 수정 유형: update_metadata
- 기대 효과: 과일간식 짐 차에 싣기에서 final visual 선호 반영
- regression 위험: low
- 필요한 테스트: metadata snapshot for id=20
