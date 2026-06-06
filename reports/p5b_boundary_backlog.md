# P5-B Boundary Backlog

> `action_hint_manual=adjust_boundary` and `generalizable_manual in (yes, review)`

| priority | score | id | title | recommended | final | workflow | source | cause | note | boundary_question | suggested_test_case |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high | 7 | 1 | 교육청 회의 오찬 장소 정하기 | 🤝 | 🍴 | meeting | boundary_ambiguity | context_vs_action | 회의는 맥락이고 실제 행동은 오찬 장소 선정 | 회의라는 맥락보다 오찬/식사 장소 선정 행위가 우선되어야 하는가? | 교육청 회의 오찬 장소 정하기 → action (meal/travel) beats meeting context |
| high | 7 | 3 | 회의실 예약 | chair (gray) | 💻 | room_cleanup | workflow_mismatch | interface_ignored | 회의 당일 회의실 세팅이 아닌 행정 내부 시스템에 의한 예약이 실제 행동임 | 수당/여비/접수 확인 등 돈·문서 관련 대상보다 행정 내부 시스템 처리 행위가 우선되어야 하는가? | 회의실 예약 → admin system (💻) beats salary/document object |
| high | 7 | 7 | 본인인증화면 수정 제안 | qr-code | 📞 or 📧 | qr_code_scan_auth | boundary_ambiguity | object_vs_channel | 화면을 수정해달라는 제안을 전화로 하는 행동임 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | 본인인증화면 수정 제안 → channel (phone/email) beats document object |
| high | 7 | 8 | 4/9, 24 출장 여비 등록 | 💰 | 💻 | salary_system | workflow_mismatch | interface_ignored | 출장 여비 등록은 급여 관련 업무가 아니며, 개인적 출장 내역을 행정 내부 시스템으로 등록하는 행위임 | 수당/여비/접수 확인 등 돈·문서 관련 대상보다 행정 내부 시스템 처리 행위가 우선되어야 하는가? | 4/9, 24 출장 여비 등록 → admin system (💻) beats salary/document object |
| high | 7 | 9 | 자치구 담당자 공문 안내 협조 요청 | 📄 | 📧 | document | boundary_ambiguity | object_vs_channel | 공문을 전파해줄 것을 메일로 요청하는 것이 실제 행위임 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | 자치구 담당자 공문 안내 협조 요청 → channel (phone/email) beats document object |
| high | 7 | 12 | 보도자료 초안 검토 요청 | 📄 | 📧 or 📞 | document | boundary_ambiguity | object_vs_channel | 홍보 담당자에게 전화 혹은 이메일로 초안 검토를 요청하는 것이 실제 행위 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | 보도자료 초안 검토 요청 → channel (phone/email) beats document object |
| high | 7 | 47 | 교육청 주무관 안내 협조 요청 | 📄 | 📞 | document | boundary_ambiguity | object_vs_channel | 전화로 하기 때문임. 그러나 공문으로 협조 요청시 문서 이모지가 적절할 수 있음 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | 교육청 주무관 안내 협조 요청 → channel (phone/email) beats document object |
| high | 7 | 57 | 정보 공개 접수 확인 | 📄 | 💻 | document | workflow_mismatch | interface_ignored | 정보공개 청구 확인은 행정 내부 시스템 이용함 | 수당/여비/접수 확인 등 돈·문서 관련 대상보다 행정 내부 시스템 처리 행위가 우선되어야 하는가? | 정보 공개 접수 확인 → admin system (💻) beats salary/document object |
| high | 7 | 75 | 실적자료 제출 독촉 | 📄 | 📞 | document | boundary_ambiguity | object_vs_channel | 자료 독촉은 보통 전화 통화를 통해 이루어짐. | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | 실적자료 제출 독촉 → channel (phone/email) beats document object |
| high | 7 | 76 | 결과보고서 제출 요청 | 📄 | 📞 or 💬 or 📧 | document | boundary_ambiguity | object_vs_channel | 일반적인 제출 요청은 전화, 메신저, 이메일을 사용함. 간혹 공문을 발송할 때도 있음(이 경우 ‘제출 요청 공문 송부’라고 명시함) | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | 결과보고서 제출 요청 → channel (phone/email) beats document object |
| high | 7 | 89 | 위원회 회의 수당 지급 | 💰 | 💻 | salary_system | workflow_mismatch | interface_ignored | 위원회 참석, 회의, 검토 수당은 급여 업무와 무관하며, 행정 내부 시스템을 이용해 처리함 | 수당/여비/접수 확인 등 돈·문서 관련 대상보다 행정 내부 시스템 처리 행위가 우선되어야 하는가? | 위원회 회의 수당 지급 → admin system (💻) beats salary/document object |
| high | 7 | 95 | 현장교육 모니터링 출장 | 👩‍🏫 | 💼 | education_fieldwork | boundary_ambiguity | context_vs_action | 출장은 대부분 suitcase 이모지를 선호함 | 교육/현장 맥락보다 출장(이동) 행위가 우선되어야 하는가? | 현장교육 모니터링 출장 → action (meal/travel) beats meeting context |
| high | 7 | 104 | 운영평가 일정 안내 | exclamation-circle (red) | 💬 or 📧 or 📞 | notification_ops | boundary_ambiguity | object_vs_channel | 일정 안내는 보통 메신저, 메일, 전화를 통해 처리됨. | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | 운영평가 일정 안내 → channel (phone/email) beats document object |
| medium | 5 | 19 | 초단기근로자 간식 관련 전달 | 📄 | 🍬 or 🗣️ | document | workflow_mismatch | action_not_captured | 탕비실의 간식 구매를 담당하는 근로자에게 간식 구매 관련 사항을 전달하는 행위 혹은 간식을 떠오르는 사탕에 중점을 둠 | 간식 구매/전달 행위는 document workflow와 분리되어야 하는가? | 초단기근로자 간식 관련 전달 → field visit/action beats room_cleaning workflow |
| medium | 5 | 85 | 홍보물 시안 수정 요청 | 📝 | 📞 or 💬 or 📧 or photo landscape | document | boundary_ambiguity | object_vs_channel | 수정 요청의 수단에 따라 전화, 메신저, 이메일 이모지 사용. 홍보물을 연상하는 photo landscape 도 사용 가능 | 공문/자료라는 대상보다 전화·메일·메신저 전달 채널이 우선되어야 하는가? | 홍보물 시안 수정 요청 → channel (phone/email) beats document object |
