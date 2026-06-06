# P5-B Override Manual Labeling Sheet

## Purpose
이 파일은 자동 taxonomy 결과를 사람이 검토하여, override 원인을 수동 라벨링하기 위한 작업 파일입니다.

## Labeling Guide
- `source_type_manual`: override가 발생한 1차 원인
- `cause_type_manual`: 구체적 원인
- `action_hint_manual`: 이후 조치 방향
- `generalizable_manual`: 다른 유사 업무에도 적용 가능한지 여부

## Allowed source_type_manual values
- workflow_mismatch
- visual_mismatch
- boundary_ambiguity
- candidate_gap
- metadata_gap
- personal_preference
- no_candidate
- unclear

## Allowed action_hint_manual values
- add_candidate
- update_metadata
- adjust_boundary
- adjust_scoring
- suppress_overfit
- keep_as_preference
- needs_more_data

> Current-engine recheck fields included. Label **Active Gaps** and **Still No Candidate** first; skip resolved stale overrides.


## Active Gaps for Manual Labeling

현재 엔진에서도 여전히 사용자 최종 선택과 맞지 않는 사례입니다.

| id | title | recommended_visual | final_visual | current_engine_visual | current_engine_workflow | current_taxonomy | inferred_gap_type | source_type_manual | cause_type_manual | action_hint_manual | generalizable_manual | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 교육청 회의 오찬 장소 정하기 | 🤝 | 🍴 | 🤝 | meeting | workflow_mismatch | inferred_workflow_boundary |  |  |  |  | 회의는 맥락이고 실제 행동은 오찬 장소 선정 |
| 2 | 식생활교육 보도자료 확인 | 📄 | 📰 | 📄 | document | action_vs_object | inferred_workflow_boundary |  |  |  |  | 확인의 대상인 보도자료에 중점 |
| 3 | 회의실 예약 | chair (gray) | 💻 | chair (gray) | room_cleanup | workflow_mismatch | inferred_workflow_boundary |  |  |  |  | 회의 당일 회의실 세팅이 아닌 행정 내부 시스템에 의한 예약이 실제 행동임 |
| 4 | 지피터스 AI 스터디 신청 | 🧑‍🏫 | robot (orange) | 🧑‍🏫 | training_session_attendance | personal_preference | inferred_no_candidate |  |  |  |  | 스터디 대상에 중점, 지피터스라는 회사의 대표 색이 orange 임. |
| 5 | 알뜰폰 할인 종료일 | 없음 | day calendar | 📅 | work_calendar_organization | no_candidate | inferred_no_candidate |  |  |  |  | 혜택 마감일을 특정함 |
| 7 | 본인인증화면 수정 제안 | qr-code | 📞 or 📧 | qr-code | qr_code_scan_auth | boundary_ambiguity | inferred_ambiguous_channel |  |  |  |  | 화면을 수정해달라는 제안을 전화로 하는 행동임 |
| 8 | 4/9, 24 출장 여비 등록 | 💰 | 💻 | 💰 | salary_system | action_vs_object | inferred_workflow_boundary |  |  |  |  | 출장 여비 등록은 급여 관련 업무가 아니며, 개인적 출장 내역을 행정 내부 시스템으로 등록하는 행위임 |
| 9 | 자치구 담당자 공문 안내 협조 요청 | 📄 | 📧 | 📄 | document | channel_vs_object | inferred_workflow_boundary |  |  |  |  | 공문을 전파해줄 것을 메일로 요청하는 것이 실제 행위임 |
| 11 | 민방위 대피 훈련 | mop-bucket (brown) | person running (green) | mop-bucket (brown) | room_cleaning | action_vs_object | inferred_no_candidate |  |  |  |  | 긴급시 외부로 대피 훈련하는 것이 실제 행위, 초록색 비상탈출구에서 연상 |
| 12 | 보도자료 초안 검토 요청 | 📄 | 📧 or 📞 | 📄 | document | boundary_ambiguity | inferred_ambiguous_channel |  |  |  |  | 홍보 담당자에게 전화 혹은 이메일로 초안 검토를 요청하는 것이 실제 행위 |
| 13 | 서울시 누리집 분야별 새소식 게시글 예약 | 📌 | social media post (blue) | 📌 | broadcast_notice | action_vs_object | inferred_no_candidate |  |  |  |  | 온라인 게시판을 떠오르는 아이콘(서울시 누리집 대표 색이 파란색임) |
| 16 | 창의 정책 홍보 영상 제출 | 📝 | 🎥 | 📝 | document | action_vs_object | inferred_no_candidate |  |  |  |  | 제출 대상인 영상에 중점 |
| 18 | 커피, 차 픽업 | 🍰 | coffee paper cup (brown) | 🍰 | snack_pickup | action_vs_object | inferred_no_candidate |  |  |  |  | 종이 일회용 음료를 픽업하는 것이므로 케이크가 아닌 음료잔 선택(커피색인 갈색 연상) |
| 19 | 초단기근로자 간식 관련 전달 | 📄 | 🍬 or 🗣️ | 📄 | document | boundary_ambiguity | inferred_workflow_boundary |  |  |  |  | 탕비실의 간식 구매를 담당하는 근로자에게 간식 구매 관련 사항을 전달하는 행위 혹은 간식을 떠오르는 사탕에 중점을 둠 |
| 20 | 과일간식 짐 차에 싣기 | 🍱 | 🍇 or 📦 | 🍱 | food_preparation | personal_preference | inferred_workflow_boundary |  |  |  |  | 도시락은 과일간식의 이미지와 거리가 멈. 과일 이모지 혹은 과일간식을 포장한 상자 연상 |
| 21 | 재택 필요 자료 드라이브 업로드 | 📁 | folder arrow up (yellow) | 📁 | folder_organization | personal_preference | inferred_no_candidate |  |  |  |  | 업로드 행위에 중점, 노란색 폴더 연상. |
| 23 | 노션 강의 수강 | document (orange) | 🧑‍🏫 or notion | document (orange) | notion_docs_touchup | boundary_ambiguity | inferred_workflow_boundary |  |  |  |  | 강의 수강 행위 혹은 강의의 주제에 중점을 둠 |
| 36 | 을지훈련 매트리스 상태 확인 | 📄 | 🛏️ | 📄 | document | personal_preference | inferred_no_candidate |  |  |  |  | 문서 작업이 아닌 매트리스라는 물품 상태 확인하는 것으로, 매트리스와 비슷한 침대 이미지  활용 |
| 37 | 헌혈 학습시간 인정 상신 | 🗣️ | 📄 or 🩸 | 🗣️ | document | personal_preference | inferred_workflow_boundary |  |  |  |  | 공문 상신이라는 문서 작업에 중점. 혹은 헌혈의 이미지 연상 |
| 38 | 비상소집훈련 참석 | 🧑‍🏫 | 🚨 | 🧑‍🏫 | training_session_attendance | action_vs_object | inferred_no_candidate |  |  |  |  | 사이렌 이미지가 비상소집을 연상시킴. |
| 40 | 표창 제작시기 확인 | 📄 | calendar | 📄 | document | object_vs_status | inferred_no_candidate |  |  |  |  | 일반적으로 일정 확인은 확인 대상에 중점을 두나, 표창에 적절한 것이 없어 달력 아이콘 선택함 |
| 41 | 탕비실 간식 선호 조사 | 🍱 | 🍬 | 🍱 | food_preparation | action_vs_object | inferred_no_candidate |  |  |  |  | 간식은 사탕이나 케이크 이모지가 적절함 |
| 47 | 교육청 주무관 안내 협조 요청 | 📄 | 📞 | 📄 | document | channel_vs_object | inferred_workflow_boundary |  |  |  |  | 전화로 하기 때문임. 그러나 공문으로 협조 요청시 문서 이모지가 적절할 수 있음 |
| 50 | 공문 수신자 지정 관련 알아보기 | 📝 | user squares (grey) | 📝 | document | personal_preference | inferred_no_candidate |  |  |  |  | 지정해야 할 ‘수신자’를 확인하는 것으로 이를 연상하는 아이콘 사용함. |
| 51 | 공익감사단 4월 수당 신청 | 💰 | 📝 | 💰 | salary_system | personal_preference | inferred_workflow_boundary |  |  |  |  | 해당 업무는 salary system에 해당하지 않으며, 감사과에 수당 지급 요청 공문을 보내야하는 업무를 연상하는 이모지 사용함 |
| 52 | 단기위탁 교육 신청 문의 | 📞 | 💬 | 📞 | communication | channel_vs_object | inferred_workflow_boundary |  |  |  |  | 메신저를 통했기 때문임. 전화 문의라면 전화기 이모지 사용했을 것임. |
| 53 | 바이브코딩 아이디어 브레인스토밍 | angle-brackets-solidus (blue) | 🧠 | angle-brackets-solidus (blue) | coding | action_vs_object | inferred_workflow_boundary |  |  |  |  | 아이디어를 구상하는 행위에 중점을 둠 |
| 55 | 기차표 예매 | grid-rectangle-2x3 (green) | 🚄 | grid-rectangle-2x3 (green) | spreadsheet_work | visual_mismatch | inferred_no_candidate |  |  |  |  | 기차 표 예매, KTX 예매는 고속열차 이모지 사용함 |
| 57 | 정보 공개 접수 확인 | 📄 | 💻 | 📄 | document | action_vs_object | inferred_workflow_boundary |  |  |  |  | 정보공개 청구 확인은 행정 내부 시스템 이용함 |
| 63 | 과장 주재 주간회의 참석 | 🤝 | people meeting | 🤝 | meeting | action_vs_object | inferred_no_candidate |  |  |  |  | 부서, 기관 내부자들만 참석하는 회의는  악수 이모지보다 노션 아이콘 people meeting을 좀더 선호함 |
| 74 | 운영지침 공문 발송 | 📄 | document arrow right (red) | 📄 | document | action_vs_object | inferred_workflow_boundary |  |  |  |  | ‘공문 발송/송부’행위는 종이 이모지와 구분하여 노션 아이콘 document arrow right (red) 사용. |
| 75 | 실적자료 제출 독촉 | 📄 | 📞 | 📄 | document | channel_vs_object | inferred_workflow_boundary |  |  |  |  | 자료 독촉은 보통 전화 통화를 통해 이루어짐. |
| 76 | 결과보고서 제출 요청 | 📄 | 📞 or 💬 or 📧 | 📄 | document | boundary_ambiguity | inferred_ambiguous_channel |  |  |  |  | 일반적인 제출 요청은 전화, 메신저, 이메일을 사용함. 간혹 공문을 발송할 때도 있음(이 경우 ‘제출 요청 공문 송부’라고 명시함) |
| 84 | 홍보물 시안 검토 | 📄 | photo landscape | 📄 | document | personal_preference | inferred_no_candidate |  |  |  |  | 홍모물 류를 검토하는 작업은 노션 아이콘인 photo landscape 선호.(비쥬얼 후보 추가가 필요함) |
| 85 | 홍보물 시안 수정 요청 | 📝 | 📞 or 💬 or 📧 or photo landscape | 📝 | document | personal_preference | inferred_ambiguous_channel |  |  |  |  | 수정 요청의 수단에 따라 전화, 메신저, 이메일 이모지 사용. 홍보물을 연상하는 photo landscape 도 사용 가능 |
| 87 | 세금계산서 검토 | 📄 | reciept (grey) | 📄 | document | visual_mismatch | inferred_no_candidate |  |  |  |  | 세금계산서는 문서가 아닌 영수증의 일종으로 인지함 |
| 89 | 위원회 회의 수당 지급 | 💰 | 💻 | 💰 | salary_system | action_vs_object | inferred_workflow_boundary |  |  |  |  | 위원회 참석, 회의, 검토 수당은 급여 업무와 무관하며, 행정 내부 시스템을 이용해 처리함 |
| 92 | 강사 섭외 후보 추리기 | 🧑‍🏫 | 🧑‍🏫 or 📄 | 👩‍🏫 | education_fieldwork | boundary_ambiguity | inferred_workflow_boundary |  |  |  |  | 강사 자체에 초점을 두거나, 강사 프로필 문서 검토 행위에 초점을 둠. |
| 93 | 강사 섭외 진행 | 🧑‍🏫 | 🧑‍🏫 or 📧 or 📞 | 👩‍🏫 | education_fieldwork | boundary_ambiguity | inferred_ambiguous_channel |  |  |  |  | 강사 자체에 초점을 두거나, 섭외 행위 방식에 따라 여러 이모지 사용 |
| 95 | 현장교육 모니터링 출장 | 👩‍🏫 | 💼 | 👩‍🏫 | education_fieldwork | personal_preference | inferred_no_candidate |  |  |  |  | 출장은 대부분 suitcase 이모지를 선호함 |
| 99 | 운영 관련 질의 응답 | checkmark-circle (green) | speech bubbles (blue) | checkmark-circle (green) | survey_form | personal_preference | inferred_no_candidate |  |  |  |  | 질문에 답변을 다는 것을 묻고 답하는 말풍선으로 연상. |
| 101 | 강사단 평가회 사전 준비 사항 리스트 | 👩‍🏫 | checkmark list (red) | 👩‍🏫 | education_fieldwork | personal_preference | inferred_no_candidate |  |  |  |  | 행사 관련 전반적인 사항을 확인하는 류의 제목에서는 checkmark list 선호. |
| 104 | 운영평가 일정 안내 | exclamation-circle (red) | 💬 or 📧 or 📞 | exclamation-circle (red) | notification_ops | boundary_ambiguity | inferred_ambiguous_channel |  |  |  |  | 일정 안내는 보통 메신저, 메일, 전화를 통해 처리됨. |
| 105 | 센터 방문점검 실시 | mop-bucket (brown) | 💼 or 📋 | mop-bucket (brown) | room_cleaning | personal_preference | inferred_workflow_boundary |  |  |  |  | 센터로의 출장을 연상하는 서류가방 이모지 혹은 현장 점검을 연상하는 클립보드 이모지 사용함 |
| 106 | 센터 조직도 및 연락처 정비 | 📞 | network | 📞 | communication | personal_preference | inferred_no_candidate |  |  |  |  | 노션 아이콘 network 모양이 조직도를 연상시킴. 연락처 현행화에서는 전화 이모지를 사용하지 않는 것을 선호함. |

## Still No Candidate

현재 엔진도 후보를 찾지 못한 사례입니다.

| id | title | recommended_visual | final_visual | current_engine_visual | current_engine_workflow | current_taxonomy | inferred_gap_type | source_type_manual | cause_type_manual | action_hint_manual | generalizable_manual | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 54 | 제주도 비행기 예매 | 없음 | ✈️ or ticket airplane (blue) |  |  | no_candidate | inferred_no_candidate |  |  |  |  | 비행기 혹은 티켓을 연상하는 이모지 사용함 |
| 73 | 센터별 운영실적 취합 | 없음 | 📊 or 📄 |  |  | no_candidate | inferred_no_candidate |  |  |  |  | ‘실적’에 초점을 맞출 경우 그래프 이모지를, 일반적인 취합 행동에 초점을 맞출 경우 종이 이모지를 선호함 |
| 108 | 세종 출장 KTX 예매 | 없음 | 🚄 |  |  | no_candidate | inferred_no_candidate |  |  |  |  | 기차 표 예매, KTX 예매는 고속열차 이모지 사용함 |
| 109 | 부산 출장 숙소 예약 | 없음 | 🏨 |  |  | no_candidate | inferred_no_candidate |  |  |  |  | 숙소, 숙박을 연상하는 호텔 이모지를 사용함 |

## Engine Error / Needs Review

현재 엔진 재검증에 실패한 사례입니다.

| id | title | recommended_visual | final_visual | current_engine_visual | current_engine_workflow | current_taxonomy | inferred_gap_type | source_type_manual | cause_type_manual | action_hint_manual | generalizable_manual | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| — | (none) | | | | | | | | | | | |
