# Workflow ontology

> **Living meaning model**  
> 이 ontology는 **추천 시스템이 현재 시점에서 사용하는 workflow meaning 모델**을 글로 옮긴 것이다. **`feedback_log`**, **후보(`visual_candidates`) 진화**, **`workflow_resolution` 튜닝**, 실제 **추천 충돌·사용자 선택**을 보며 **계속 수정·실험**할 수 있다.  
> **절대 고정 taxonomy·표준 규격서**가 아니다. 상위 category·lifecycle·related 축은 “지금 코드·데이터와 맞추기 위한 실무 기반 recommendation meaning model”로 유지한다.

이 문서는 **visual(이모지·Notion 아이콘) 목록**이 아니라, 추천·피드백·분석에서 재사용할 **업무 workflow 의미 체계(workflow ontology)** 를 정의한다.  
**workflow category**, **lifecycle stage**, **interface anchor**(제목·의미의 UI 신호), **related category**, **채널·nuance**를 같은 말로 쓰기 위한 참조 축이다.

---

## 1. 목적

| 목적 | 설명 |
|------|------|
| **의미 안정화** | 제목·키워드가 바뀌어도 “같은 상위 업무”를 가리키는 언어를 공유한다. |
| **경쟁 후보 해석** | 같은 추천 후보 풀 안에서 **왜 A와 B가 붙는지**를 category 관점으로 설명한다. |
| **피드백 집계** | `feedback_log`에 남길 필드를 ontology 축에 맞춰 **재현 가능한 분석**을 가능하게 한다. |
| **추천 엔진 확장** | 이후 recommendation이 **category-aware**(상위 축·단계·관련 축)로 동작할 **설계 기준**을 제공한다. |

본 ontology는 **아이콘 모양**이 아니라 **업무 의미·채널·lifecycle 단계**를 1차 축으로 한다. 단순 “업무 분류표”가 아니라 실제 조직 workflow lifecycle — **작성 → 검토 → 보고 → 요청 → 결재 → 배포 → 게시 → 공유 → 추적** — 을 모델링한다.

---

## 2. Workflow category 철학

1. **상위 category가 먼저**  
   추천 결과를 해석할 때 “어떤 아이콘인가”보다 **어떤 업무 영역인가**(communication, document, system_admin 등)가 먼저 안정되어야 한다.

2. **같은 상위 안에서만 sibling 경쟁을 정의**  
   예: `document` 안의 `review` vs `reporting` vs `distribution` — 서로 **대체 가능한 후보**가 될 수 있는지는 상위가 같을 때가 많다.

3. **channel / stage / logistics 는 하위로 분리**  
   - **channel**: 전화·메신저·메일 등 연락 매체.  
   - **stage**: 검토 → 수정 → 요청 → 보고/결재 → 배포/게시/공유 등 문서 lifecycle.  
   - **logistics vs social**: 식사 **약속·모임**(사람)과 **준비·픽업**(물건 흐름)을 분리한다.

4. **visual selection은 다축 신호의 결합**  
   추천 visual은 action(요청·결재·배포), object identity(자료·책자·앱·예산), interface/channel(전화·메일·카톡), hierarchy interaction(상급자 보고·결재권자 승인), lifecycle stage(검토·signoff·tracking)가 함께 만든다.

5. **tree는 단일 상속에 가깝게 유지**  
   실제 제목은 다축이므로 **primary category 하나**로 트리에 매달고, 나머지는 **`related_categories`**로만 표현한다 (§6).

---

## 3. 상위 category (top-level) 설명

아래 이름은 **문서·코드·로그에서 쓸 canonical slug** 로 사용한다 (`snake_case`).

| Top-level | 한 줄 설명 | 대표적으로 다루는 질문 |
|-----------|------------|------------------------|
| `communication` | 사람·조직 간 메시지 전달·대화 | “어떤 채널로 말하는가?” |
| `notification_ops` | 알림 스택·센터 정리 | “도착물·배지를 정리하는가?” |
| `document` | 문서·기록물의 조직 업무 lifecycle | “검토·작성 이후 어떤 조직 행위로 이어지는가?” |
| `tabular_data` | 표·수치·폼·접수 | “셀·표·폼 UI에서 데이터를 다루는가?” |
| `engineering` | 코드·CLI·환경 | “소프트웨어를 직접 만지는가?” |
| `system_admin` | 사내/외부 행정 시스템·급여·접근 | “시스템·권한·행정 입력인가?” |
| `time_scheduling` | 마감·캘린더·개인 일정 배치 | “시간축을 어떻게 관리하는가?” |
| `digital_storage` | 파일·폴더·드라이브 트리 | “저장 계층을 정리하는가?” |
| `meeting_collaboration` | 회의·면담·발상 | “집단 인지·대면 의제인가?” |
| `education` | 교육 전달(현장) vs 수강 | “가르치러 가는가 / 배우러 가는가?” |
| `event_social` | 행사·경조·식사 모임 등 사회적 일정 | “사람·모임·경조 이벤트인가?” |
| `food_logistics` | 음식 **준비·수령** 등 물류에 가까운 축 | “먹을 것을 마련·가져오는가?” |
| `facility_physical` | 공간·비품·청소·셋업·재물·미디어 하드웨어 | “물리 공간·물건을 손대는가?” |
| `mobility` | 이동 서비스(택시 등) | “이동 수단을 쓰는가?” |
| `web_publication` | 대민·홈페이지·누리집 | “공개 웹 콘텐츠인가?” |
| `broadcast_notice` | 기관적 공지·경고 | “1:N 공지·주의인가?” |
| `duty_roster` | 당직·숙직 등 근무 형태 | “책임 근무 슬롯인가?” |
| `tracking` | 진행 상태·현황·응답·배정·집행 상황 모니터링 | “현재 어디까지 왔는가?” |

**`pair_rules` / synthetic row**  
`confirm_coordination`, `prep` 등은 **상위 축에 흡수**해 기술한다: 예) coordination은 `communication` 하위 `coordination`으로 매핑한다.

---

## 4. Sub workflow 설명

상위별 **sub_workflow** (canonical). 트리는 §5와 동일하다.

### `communication`

| sub_workflow | 설명 |
|--------------|------|
| `synchronous_voice` | 음성 통화 중심 |
| `messenger` | 카톡·메신저·채팅 UI |
| `async_mail` | 메일·공지·비동기 전달 |
| `coordination` | 일정 조율·참석 여부 확인·시간 협의처럼 채널 선택 전의 상호 조정 |
| `request_action` | 부탁·요청이 communication surface로 드러나는 bridge; primary는 보통 `document.request` |

`coordination`은 `일정 조율`, `참석 여부 확인`, `시간 협의`처럼 **상대와 상태를 맞추는 workflow**다. 실제 채널이 `전화`, `카톡`, `메일`로 명시되면 channel 후보가 visual을 이길 수 있고, 채널이 없으면 messenger/coordination 성격으로 수렴한다.

### `notification_ops`

| sub_workflow | 설명 |
|--------------|------|
| `notification_stack` | 알림·푸시·알림센터 정리 |

### `document`

| sub_workflow | 설명 |
|--------------|------|
| `review` | 기존 문서 검토·확인·열람 |
| `edit` | 작성·기안·제출·공문 등 원고/제출 파이프 |
| `collaborative` | 노션·Docs 등 **협업 문서면** |
| `archive_reference` | 바인더·법령집·자료집 등 보관·참조 묶음 |
| `presentation` | 슬라이드·발표 자료 검수 |
| `reporting` | 상급자·결재권자·관리자에게 브리핑·설명·상신·보고하는 hierarchy communication |
| `request` | delegation / action request; 요청 대상과 요청 channel이 모두 중요 |
| `approval` | 결재·승인·상신·사인처럼 권한 기반 signoff / authorization |
| `distribution` | 문서·자료·앱 버전 등 산출물을 전달·배포·배부 |
| `publication` | 공고·게시·게시판 등록처럼 외부/조직에 공개 노출 |
| `sharing` | 정보·권한·문서 내용을 상대와 함께 사용하도록 공유 |
| `prep` | “대상+준비” (pair); lifecycle상 **edit에 가까운 subject-bound 분기** |

#### `document` lifecycle 세부 원칙

- `reporting`은 단순 `review`가 아니라 **hierarchical communication / approval interaction**이다. `초안 팀장님 보고`, `예질 과장님 보고`, `시장님 보고자료 수정`, `최종안 보고`처럼 상급자·결재권자에게 설명·상신하는 행위를 `document.reporting`으로 본다.
- `request`는 단순 communication보다 **delegation / action request** 성격이 강하다. `자료 요청`, `수정 요청`, `업무 부탁`, `회신 요청`처럼 요청 대상(object)과 요청 channel이 함께 visual을 만든다. 문서 기반 요청은 📄/📝, 대면·전화·메일 요청은 🗣️/📞/📧처럼 channel visual을 쓸 수 있다.
- `approval`은 `reporting`과 다르다. `reporting`은 설명·브리핑·상신 interaction이고, `approval`은 권한 기반 signoff / authorization이다. 특히 `결재 받기`(approval request)와 `결재하기`(approval signoff)를 구분하며, 결재를 수행하는 행위는 `document_signature` visual을 사용한다.
- `distribution`은 상위 workflow가 “배포”여도 visual은 행위보다 **distributed object identity**를 우선 반영한다. 예: `주간보도자료 배포` → 📰, `책자 배포/배부` → 📔, `앱 신규 버전 배포` → `alien-pixel`, 일반 문서 배포 → 📄.
- `publication`에서는 📄가 **내용물/document**이고 📌가 **게시·고정·공고 행위**다. `공고번호`, `게시판` 같은 object/context 단어만으로는 publication action으로 보지 않고, `게시`, `등록`, `공고 게시`, `상단 고정` 같은 실제 공개 행위를 분리한다.
- `sharing`은 **공유 방식(channel)** 과 **공유 대상(content/object)** 이 모두 visual 선택에 영향을 준다. 예: `메일 공유` → 📧, `정보 공유` → 💡, `부서 암호 공유` → 🔑, `문서 공유` → 📄.

### `tabular_data`

| sub_workflow | 설명 |
|--------------|------|
| `spreadsheet` | 엑셀·테이블 일반 |
| `quantitative_budget` | 집행·산술·예산표 맥락의 계산 |
| `structured_intake` | 설문·폼·접수·응답 |

### `engineering`

| sub_workflow | 설명 |
|--------------|------|
| `application_code` | IDE 중심 구현 |
| `shell_environment` | 터미널·CLI·환경 |

### `system_admin`

| sub_workflow | 설명 |
|--------------|------|
| `internal_system` | 사내 전산·PC·승인 |
| `external_portal` | 외부 행정 포털 |
| `payroll_finance` | 급여·복지 입력·개인 금융 상환 등 |
| `access_auth_compliance` | QR 출퇴근·보안당번·잠금 등 **접근·통제** |

### `time_scheduling`

| sub_workflow | 설명 |
|--------------|------|
| `deadline_pressure` | 마감·기한 |
| `calendar_layout` | 업무 캘린더 정리·편성 |
| `personal_calendar_motion` | 운동 약속 등 개인 캘린더 (primary 정책은 TODO) |

### `digital_storage`

| sub_workflow | 설명 |
|--------------|------|
| `filesystem_tree` | 폴더·파일·드라이브 |

### `meeting_collaboration`

| sub_workflow | 설명 |
|--------------|------|
| `institutional_meeting` | 일반 회의·협의 |
| `hierarchy_meeting` | 상사·대표 면담 |
| `divergent_thinking` | 브레인스토밍·아이디어 |

### `education`

| sub_workflow | 설명 |
|--------------|------|
| `field_delivery` | 현장 교육·출강 |
| `session_attendance` | 사내 교육·세션 수강 |

### `event_social`

| sub_workflow | 설명 |
|--------------|------|
| `event_operations` | 행사 준비·운영 |
| `personal_milestone` | 결혼식 등 개인 경조 |
| `social_meal` | 점심 약속·회식 등 **사람 중심** 식사 |
| `activity_appointment` | 러닝 등 활동 약속 (related로 time과 공유 가능) |

### `food_logistics`

| sub_workflow | 설명 |
|--------------|------|
| `preparation` | 음식·도시락·간식 준비 |
| `pickup_receipt` | 픽업·수령 (대상이 간식이어도 **축은 logistics**) |

### `facility_physical`

| sub_workflow | 설명 |
|--------------|------|
| `tidy` | 정리·정돈·청소 |
| `setup_move` | 회의실 셋업·물품 이동 |
| `storage_furniture` | 캐비넷·서랍 |
| `asset_count` | 재물·비품 조사 |
| `small_equipment` | 시계 교체 등 소형 비품 |
| `media_hardware` | TV·채널 등 |

### `tracking`

| sub_workflow | 설명 |
|--------------|------|
| `status_check` | 신청 현황·상태 확인 |
| `progress_monitoring` | 진행 상황·진행 상태 모니터링 |
| `allocation_tracking` | 강사·담당자·자원 배정 현황 |
| `response_tracking` | 응답·회신·답변 현황 |
| `budget_tracking` | 예산 집행·집행 상황 추적 |

`tracking`은 단순 `review`/`document`가 아니라 **monitoring / ongoing status awareness workflow**다. 목적은 문서를 읽는 것이 아니라 진행 상태·현황·응답·배정·집행 상황을 계속 파악하는 것이다.

### `mobility` / `web_publication` / `broadcast_notice` / `duty_roster`

각각 단일 sub 또는 동명: `taxi`, `site_refresh`, `institutional_alert`, `shift_duty`.

---

## 5. Canonical workflow hierarchy (프로젝트 기준)

**표기:** `top_level` → `sub_workflow` → *(optional)* `lifecycle_stage` → `representative_candidate_ids`

`lifecycle_stage`는 **문서 등 일부 상위에서만** 쓴다. 없으면 생략.

```
communication
├─ synchronous_voice          → phone_call
├─ messenger                  → messenger_chat
├─ async_mail                 → mail_action
├─ coordination               → (pair confirm_coordination → 위 채널들)
└─ request_action             → (related bridge to document.request)

notification_ops
└─ notification_stack         → notification_cleanup

document
├─ review             [stage: review]              → document_review
├─ edit               [stage: draft|submit]        → document_edit
├─ collaborative      [stage: iterate]             → notion_docs_touchup
├─ archive_reference  [stage: maintain]            → binder_document
├─ presentation       [stage: review|finalize]     → slide_deck_final_review
├─ reporting          [stage: report]              → document_reporting, result_reporting
├─ request
│  ├─ document_request       [stage: request]      → document_request
│  ├─ review_request         [stage: request]      → review_request
│  ├─ submission_request     [stage: submit]       → submission_request, document_submission
│  ├─ verbal_request         [stage: request]      → verbal_request
│  ├─ mail_request           [stage: request]      → mail_request
│  ├─ phone_request          [stage: request]      → phone_request
│  └─ collaborative_request  [stage: request]      → collaborative_request
├─ approval
│  ├─ approval_request       [stage: approval_request] → approval_request
│  ├─ approval_review        [stage: approval_review]  → approval_review
│  ├─ approval_signoff       [stage: signoff]          → document_signature
│  └─ final_approval         [stage: final_approval]   → final_approval
├─ distribution
│  ├─ press_distribution      [stage: distribute]  → press_distribution
│  ├─ booklet_distribution    [stage: distribute]  → booklet_distribution
│  ├─ app_release             [stage: release]     → app_release
│  ├─ document_distribution   [stage: distribute]  → document_distribution
│  └─ mail_distribution       [stage: distribute]  → mail_distribution
├─ publication
│  ├─ posting                 [stage: publish]     → publication_posting, public_posting
│  ├─ announcement            [stage: publish]     → publication_announcement, notice_posting
│  ├─ bulletin_update         [stage: publish]     → publication_bulletin_update
│  └─ pinned_notice           [stage: pin]         → publication_pinned_notice
├─ sharing
│  ├─ mail_sharing            [stage: share]       → mail_sharing
│  ├─ credential_sharing      [stage: share]       → credential_sharing
│  ├─ information_sharing     [stage: share]       → information_sharing
│  └─ document_sharing        [stage: share]       → document_sharing
└─ prep               [stage: prep]                → (pair prep_paired_document 등 → document 계열 시각)

tabular_data
├─ spreadsheet                → spreadsheet_work
├─ quantitative_budget        → budget_line_calculation
└─ structured_intake          → survey_form

engineering
├─ application_code           → coding
└─ shell_environment          → terminal_work

system_admin
├─ internal_system            → system_work
├─ external_portal            → external_admin_system
├─ payroll_finance            → salary_system, housing_loan_repayment
└─ access_auth_compliance
    ├─ qr_check_in            → qr_auth, qr_code_scan_auth
    └─ security_posture       → security_work

time_scheduling
├─ deadline_pressure          → deadline_management
├─ calendar_layout            → work_calendar_organization
└─ personal_calendar_motion   → running_appointment

digital_storage
└─ filesystem_tree            → folder_organization

meeting_collaboration
├─ institutional_meeting      → meeting
├─ hierarchy_meeting          → executive_meeting
└─ divergent_thinking         → brainstorming

education
├─ field_delivery             → education_fieldwork
└─ session_attendance         → training_session_attendance

event_social
├─ event_operations           → event_preparation (+ pair 부스/행사장 등)
├─ personal_milestone         → wedding_attendance
├─ social_meal                → lunch_promise, food_meeting
└─ activity_appointment       → (running_appointment 과 중복 시 related; §6)

food_logistics
├─ preparation                → food_preparation (+ pair 음식 prep 시각들)
└─ pickup_receipt             → snack_pickup

facility_physical
├─ tidy                       → room_cleanup, office_cleanup, room_cleaning
├─ setup_move                 → meeting_room_cart_setup
├─ storage_furniture          → cabinet_organization
├─ asset_count                → inventory_work
├─ small_equipment            → department_clock_replace
└─ media_hardware             → broadcast_channel_adjust

mobility
└─ taxi                       → taxi_service

web_publication
└─ site_refresh               → website_content_refresh

broadcast_notice
└─ institutional_alert       → urgent_notice

duty_roster
└─ shift_duty                 → overnight_duty

tracking
├─ status_check               → status_check
├─ progress_monitoring        → progress_monitoring
├─ allocation_tracking        → allocation_tracking
├─ response_tracking          → response_tracking
└─ budget_tracking            → budget_tracking
```

---

## 6. Representative visual (candidate_id)

위 트리 잎에 적은 id는 **`data/visual_candidates.json`의 키** 또는 pair synthetic이 가리키는 **catalog id**이다.  
**원칙:** ontology 문서에서는 **의미 노드**를 먼저 쓰고, visual은 **대표 후보 id**로만 연결한다.

---

## 7. Category 간 경쟁 관계 (요약)

| 축 A | 축 B | 경쟁이 잦은 이유 |
|------|------|------------------|
| `document.review` | `document.edit` | 제목에 “확인 vs 수정”이 동시에 암시 |
| `document.collaborative` | `document.edit` | 노션/공문 동시 언급 |
| `document.presentation` | `document.review` | “ppt 확인”이 문서 검토로도 읽힘 |
| `document.reporting` | `document.review` | `보고`가 문서 종류가 아니라 상급자 interaction일 때 |
| `document.reporting` | `document.approval` | 설명/브리핑 interaction인지, 권한 기반 signoff인지 갈림 |
| `document.request` | `communication.request_action` | 요청의 primary가 delegation인지 channel surface인지 갈림 |
| `document.distribution` | `document.review` | `배포/배부` 행위와 배포 대상 object visual이 동시에 필요 |
| `document.publication` | `broadcast_notice` | `공지/공고`가 내용물인지 게시 행위인지 갈림 |
| `document.sharing` | `communication.async_mail` | `메일 공유`처럼 channel과 공유 action이 동시에 등장 |
| `tracking.status_check` | `document.review` | “현황 확인”은 문서 열람보다 ongoing status awareness일 수 있음 |
| `communication.messenger` | `meeting_collaboration.institutional` | “협의” 키워드 공유 |
| `tabular_data.spreadsheet` | `tabular_data.quantitative_budget` | 엑셀+예산 동시 |
| `system_admin.access_auth_compliance` (qr_a / qr_b) | 동일 | **동일 workflow 이중 아이콘** |
| `event_social.social_meal` | `time_scheduling.calendar_layout` | 점심 약속·일정 |
| `food_logistics.preparation` | `food_logistics.pickup_receipt` | 간식 **준비** vs **수령** |

---

## 8. Workflow stage 개념

**stage**는 상위 category마다 의미가 다르다. 현재 **명시적으로 쓰는 것은 주로 `document`**이다.

| stage (document) | 의미 |
|------------------|------|
| `review` | 읽고 판단 |
| `draft` | 초안 작성·편집 |
| `submit` | 제출·기안 제출 |
| `iterate` | 협업 도구에서의 다회 수정 |
| `maintain` | 보관물 갱신 |
| `finalize` | 발표 직전 확정 검수 |
| `report` | 상급자·결재권자에게 설명·브리핑·보고 |
| `request` | 상대의 행동·자료·처리를 요청 |
| `approval_request` | 결재·승인을 받아야 하는 상태 |
| `approval_review` | 결재·승인 대상을 검토 |
| `signoff` | 결재하기·사인·서명 등 권한 행사 |
| `final_approval` | 최종 승인·최종 결재 |
| `distribute` | 산출물 전달·배포·배부 |
| `release` | 앱/버전 산출물 배포 |
| `publish` | 공개 게시·공고·노출 |
| `pin` | 상단 고정·핀 고정 공지 |
| `share` | 정보·권한·문서 공동 사용 |
| `prep` | subject-bound 준비(pair) |

**원칙:** stage는 **optional**이다. 로그에 없으면 “미상”으로 두고, 추후 추론 규칙으로 채울 수 있다.

### 8.1 Workflow stage 축 (`workflow_stage`)

`lifecycle_stage`(§8 표)는 **문서 전반**의 조직 행위 단계(`review`, `submit`, `report` …)이고,  
`workflow_stage`는 **보고(reporting) 계열 후보** 안에서 **진행 중 vs 산출 완료**를 나누는 **독립 ontology 축**이다.

| `workflow_stage` | semantic meaning | lifecycle position | expected follow-up likelihood | representative keywords/signals | example task titles |
|------------------|------------------|--------------------|-------------------------------|--------------------------------|---------------------|
| `progress` | 업무·사업이 **아직 진행 중**이며, 상급자·관리자에게 **중간 브리핑·추진 상황**을 알리는 보고 | 계획 실행 중 · 마일스톤 전 | **높음** — 후속 조치·추가 보고·일정 조율이 이어질 가능성 큼 | `진행상황`, `추진`, `추진현황`, `진행`, `개선 진행`, `절차 개선` + `보고` | 식생활교육 신청 절차 개선 **진행상황** 보고 |
| `interim` | **중간 시점** 점검·중간 산출물을 올리는 보고 (완료 전이지만 결과 확정은 아님) | 중간 체크포인트 | **중간** — 수정·추가 자료 요청 또는 다음 중간/최종 보고 | `중간`, `중간보고`, `중간점검`, `중간결과` | 1분기 **중간** 점검 보고 |
| `result` | **현장·출장·집행 등이 끝난 뒤** 산출·집계 **결과**를 전달하는 보고 | 활동/집행 **직후** | **중간~낮음** — 결재·배포·공유로 이어질 수 있으나 “상황 브리핑”보다 **결과물 전달** 성격 | `결과`, `결과보고`, `출장 결과`, `현장`, `집계결과`, `운영결과`, `교육결과` | 식생활교육 강사양성 **현장 출장 결과** 보고 |
| `final` | **최종·종결** 산출을 상급자·관리자에게 **마감 보고** | 사업·과제 **종결 직전/직후** | **낮음** — 보고 후 아카이브·결재 완료·후속 공지 정도 | `최종`, `최종결과`, `최종안`, `종료`, `마감` + `보고` | **최종** 결과 보고, **최종안** 보고 |

#### Distinction (핵심)

| 대비 | 구분 |
|------|------|
| **progress vs interim** | `progress`는 **흐름·추진** 중인 상태 설명(아직 끝나지 않음). `interim`은 **명시적 중간 시점**·중간 산출(체크포인트) — “지금까지의 중간 결과”이지만 **최종 확정 전** 단계. |
| **result vs final** | `result`는 **한 차례 활동·집행의 결과물** 전달(출장·현장·집계 등). `final`은 **과제·안건 전체의 종결·최종본** 상신 — 같은 🗣️ visual이어도 **후속 행위 기대**가 다름. |
| **reporting vs result_reporting** | 둘 다 `document.reporting` · `interaction_mode=report_brief` · 상급자 브리핑이다. **차이는 `workflow_stage`**: `document_reporting` → `progress`/`interim`, `result_reporting` → `result`/`final`. **새 candidate id를 늘리지 않고** metadata로 disambiguation한다. |

#### `현황` ambiguity

`현황`은 **progress·result·tracking** 모두로 읽힐 수 있는 **고의적으로 약한 신호**다.

| 제목 패턴 | 흔한 해석 | 추천 쪽 |
|-----------|-----------|---------|
| `진행상황` / `추진현황` + 보고 | `progress` | `document_reporting` |
| `결과` / `출장` / `집계` + 보고 | `result` | `result_reporting` |
| `전국 … 현황 보고` (맥락만) | progress **또는** result (연례·집계 보고 vs 추진 보고) | **자동 hard 분류 금지** — soft `workflow_stage` bonus만 |
| `신청 현황` / `배정 현황` (모니터링) | `tracking` | `status_check`, `allocation_tracking` 등 |

예시 (ontology에 반드시 포함):

- **식생활교육 신청 절차 개선 진행상황 보고** → `progress` → `document_reporting`
- **식생활교육 강사양성 현장 출장 결과 보고** → `result` → `result_reporting`
- **전국 식생활교육 현황 보고** → `현황` 단독 → stage **미확정**; reporting 후보 간 tie 가능 · tracking과도 경쟁

#### Candidate metadata 매핑 (현재 정책)

| candidate_id | `workflow_stage` | 비고 |
|--------------|------------------|------|
| `document_reporting` | `progress`, `interim` | hierarchy 브리핑·추진 보고 |
| `result_reporting` | `result`, `final` | 결과·종결 보고 |

`interim_reporting` / `final_reporting` **별도 id 분리는 하지 않음** — candidate explosion 지양, metadata + title signal로 reranking.

#### Scoring 연동 원칙 (요약)

- **hard filter 아님** — `workflow_stage` 미매칭만으로 후보 제거하지 않음 (false negative 방지).
- **soft bonus** — 제목에서 추론한 stage ∩ 후보 `workflow_stage` 일치 시 `semantic_bonus` 가산.
- **`현황` 단독** — title inference에 stage를 붙이지 않음 (ambiguous).
- 상세 비교·snapshot은 `docs/workflow_stage_analysis_report.md` 참고.

### 8.2 Publication / notice / public / distribution / channel 경계

공지·안내·공고·게시·공개·배포·보도자료 계열은 `document_edit`, `communication` channel, `document.distribution`, `document.publication`, `broadcast_notice` 후보와 자주 경쟁한다. 이번 축의 목표는 **후보를 늘리기보다 boundary를 문서·테스트로 고정**하는 것이다.

#### 의미 축 정의

| 축 | semantic meaning | 대표 candidate | 제목 신호 (예) |
|----|------------------|----------------|----------------|
| **notice** | 조직·서비스 **내용을 알리는** 1:N 공지 | `notice_posting`, `urgent_notice` | `운영계획 공지`, `서비스 점검 공지`, `공지 등록` |
| **publication** | **공식 게시·공고·대외 노출** 행위 | `publication_posting`, `publication_announcement`, `public_posting` | `공문 게시`, `행사안내 공고`, `신청안내 게시`, `홈페이지 게시` |
| **public** *(metadata)* | **visibility / audience** — 외부·대중 대상 | *(독립 candidate 아님)* | `공개`, `대외`, `홈페이지` — `semantic_metadata.visibility=public` |
| **distribution** | **산출물 전달·배포·배부** | `press_distribution`, `booklet_distribution`, `app_release`, `document_distribution` | `보도자료 배포`, `책자 배부`, `앱 배포`, `결과자료 배포` |
| **channel** | **전달 수단** (메일·카톡·메신저·전화) | `mail_action`, `messenger_chat`, `mail_distribution`, `mail_sharing` | `메일`, `카카오톡`, `카톡`, `슬랙`, `발송`, `전달` |

`public_posting`은 **public visibility를 드러내는 publication variant**이지, `public`만을 위한 독립 action candidate가 아니다. `visibility=public`은 publication·distribution 후보 metadata와 title signal로 공유한다.

#### 경계 원칙 (우선순위)

1. **channel > notice / publication** — 채널 단서(메일·카톡·슬랙·발송·전달)가 있으면 `mail_action` / `messenger_chat` / `mail_distribution` 등 **channel 후보가 notice·publication보다 우선**한다.  
   예: `카카오톡 공지 전달` → `messenger_chat`, `제출자료 메일 안내` → `mail_action`.

2. **distribution > publication** — `배포`·`배부`·보도자료·책자·앱 버전 등 **산출물 전달**이면 publication보다 **distribution 계열**이 우선한다.  
   예: `보도자료 배포` → `press_distribution`, `앱 신규버전 배포` → `app_release`.

3. **publication > generic document** — `게시`·`공고`·`등록`·`공개 모집`·홈페이지 게시처럼 **공식 노출 행위**면 publication 계열이 우선한다.  
   예: `공문 게시` → `publication_posting`, `만족도조사 공고` → `publication_announcement`.

4. **document_edit vs notice/publication** — `안내문`·`회의자료`·`검토자료` **작성**은 `document_edit`과 경쟁한다. **단순 `안내` 단어만**으로 publication으로 보내지 않는다.  
   예: `안내문 작성` → `document_edit`, `검토결과 안내` → publication top1 금지.

5. **public = metadata** — `공개`·`대외`·`홈페이지`는 가능하면 **독립 candidate가 아니라** `semantic_metadata.visibility=public`과 title signal로 처리한다. publication/distribution 후보가 action을 담당한다.

#### notice vs publication (세부)

| 대비 | 구분 |
|------|------|
| **notice vs publication** | `공지`·`점검 공지`·`운영계획 공지` → **알림** (`notice_posting`). `게시`·`공고`·`등록` → **공식 노출** (`publication_*`). |
| **notice vs urgent_notice** | 긴급·경고 톤·기관 경보 → `urgent_notice` / `broadcast_notice`. 일반 운영 공지 → `notice_posting`. |
| **publication vs public_posting** | `public_posting`은 **web_publication + visibility=public** publication variant. 홈페이지·홍보물·배너 게시에 쓰되, `public` 단독 id는 만들지 않는다. |

#### Candidate metadata 매핑 (현재 정책)

| candidate_id | primary sub | `publish_distribute` | `visibility` | 비고 |
|--------------|-------------|----------------------|--------------|------|
| `notice_posting` | publication.announcement (notice tone) | `posting` | `public` | 공지사항·운영 공지 게시 |
| `publication_posting` | publication.posting | `posting` | `public` | 일반 공문·자료 게시 |
| `public_posting` | publication.posting | `posting` | `public` | 홈페이지·대외 공개 게시 variant |
| `publication_announcement` | publication.announcement | `posting` | `public` | 채용·행사·조사 **공고** |
| `press_distribution` | distribution | `distribution` | `public` | 보도자료 **배포** (게시 아님) |
| `document_distribution` | distribution | `distribution` | `internal` | 일반 문서·자료 배포 |
| `mail_action` | communication.async_mail | — | — | 채널 surface; notice/publication보다 채널 우선 |

#### Scoring 연동 원칙 (요약)

- **hard filter 아님** — boundary 테스트는 ranking 기대치를 고정하되, scoring은 metadata·meaning·soft bonus 순으로 조정한다.
- **`안내` 단독** — `broadcast_notice` / publication hard routing 금지; `document_edit`·`mail_action`·`document_review`와 경쟁 허용.
- **`공개` 단독** — `public` candidate 승격 금지; `visibility=public` signal + publication family reranking.
- **테스트 위치** — `tests/test_publication_notice_boundaries.py`, `test_publication_channel_boundaries.py`, `test_publication_distribution_boundaries.py`, `test_public_visibility_metadata.py`. boundary title은 `sample_cases.json` 중복 추가 없이 테스트에서만 검증한다.

### 8.3 Document flow stage (`document_flow_stage`)

제출·요청·검토·승인·반려/회송·완료 lifecycle을 **reporting `workflow_stage`와 분리**하는 축이다. candidate explosion을 피하고 metadata + title compound signal로 disambiguation한다.

| `document_flow_stage` | semantic meaning | representative candidates | 제목 신호 (예) |
|-----------------------|------------------|-------------------------|----------------|
| `request` | 상대 행동·자료·승인·검토를 **요구** | `submission_request`, `review_request`, `approval_request`, `collaborative_request` | `제출 요청`, `검토 요청`, `승인 요청`, `보완 요청` |
| `submit` | 자료·서류 **제출 행위** | `document_submission` | `자료 제출`, `실적자료 제출` |
| `review` | 제출물·결재안 **검토** | `document_review`, `approval_review` | `자료 제출 검토`, `결재 검토` |
| `approve` | 승인·결재 **실행** | `document_signature` | `결재하기`, `승인하기` |
| `reject_or_return` | 반려·회송·재제출 유도 | *(axis only — candidate TBD)* | `반려`, `회송`, `반송` |
| `complete` | 최종 승인·절차 종료 | `final_approval` | `최종 승인`, `신청 승인`, `자료 제출 승인` |

#### Distinction (핵심)

| 대비 | 구분 |
|------|------|
| **request vs submit** | `자료 제출 요청` → request. `자료 제출` → submit. bare `제출`만으로 request 후보에 bonus 주지 않는다. |
| **review vs approval_request** | `검토 요청` → request. `자료 제출 검토` → review (행위). |
| **approve vs complete** | `결재하기` → approve(signoff). `최종 승인`·`신청 승인`·`자료 제출 승인` → complete/outcome. |
| **submit + modifier** | compound phrase longest-match wins: `자료제출승인` → complete/approve, not submit. |

#### Candidate metadata 매핑 (현재 정책)

| candidate_id | `document_flow_stage` | `request_approval` (optional) |
|--------------|----------------------|-------------------------------|
| `submission_request` | `request` | `submission_request` |
| `document_submission` | `submit` | — |
| `review_request` | `request` | `review_request` |
| `approval_request` | `request` | `approval_request` |
| `collaborative_request` | `request` | `revision_request` |
| `document_review` | `review` | — |
| `approval_review` | `review` | — |
| `document_signature` | `approve` | — |
| `final_approval` | `approve`, `complete` | — |

#### Scoring 연동 원칙 (요약)

- **hard filter 아님** — stage mismatch만으로 후보 제거하지 않음.
- **longest compound wins** — `자료제출승인`이 `자료제출`보다 우선.
- **bare `제출`** — submit stage soft signal; `submission_request` interaction_mode에 매핑하지 않음.
- **테스트** — `tests/test_document_flow_boundaries.py`, `tests/test_document_flow_calibration.py`, `tests/ambiguity/document_flow_test_set.json`, `tests/ambiguity/document_flow_ground_truth.json`.

---

## 9. Related category (primary / secondary)

### 9.1 정의

- **primary_workflow_category**  
  트리에 **한 번만** 매기는 상위 축. 추천 해석·대시보드의 **주 범주**다.

- **related_workflow_categories**  
  제목이 **합법적으로 다축**일 때만 넣는다. 트리를 **두 뿌리로 분열**시키지 않는다.

### 9.2 언제 related를 쓰는가

- 제목이 **두 축을 동시에** 만족하는 경우 (예: “점심 **약속**” → social + scheduling).  
- **한 축만으로는** 사용자가 “이 업무를 설명한다”고 느끼기 어려운 경우.

### 9.3 언제 primary만 쓰는가

- 추천기가 이미 **한 후보**에 수렴했고, **대안 설명**이 같은 상위 안(sibling)에만 있을 때.  
- related를 붙이면 **오히려 로그 노이즈**가 될 때.

### 9.4 hierarchy를 흐리지 않기 위한 기준

1. **related는 최대 2~3개**를 권장한다.  
2. related는 **형제가 아닌 다른 top-level**에서만 택한다 (같은 top의 다른 sub는 “경쟁 후보”로 처리).  
3. **primary는 항상 하나**; 충돌 시 **제품 정책 표** (TODO §12)로 결정한다.

### 9.5 예시 (개념)

| candidate / 상황 | primary | related (예시) |
|--------------------|---------|------------------|
| `running_appointment` | `time_scheduling` 또는 `event_social` (정책 택일) | 나머지 하나 |
| `lunch_promise` | `event_social` | `time_scheduling` |
| `slide_deck_final_review` | `document` | `meeting_collaboration` (발표 직전 회의 맥락 시) |

---

## 10. Visual candidate 연결 — metadata schema (설계 초안)

일부 lifecycle 후보는 이미 `visual_candidates.json`에 반영되어 있다. 아래는 후보별 ontology metadata를 인라인 또는 별도 `workflow_ontology_map.json`에 추가할 때의 권장 필드 방향이다.

### 10.1 후보별 권장 필드

```json
{
  "id": "document_review",
  "workflow_category": "document",
  "sub_workflow": "review",
  "lifecycle_stage": "review",
  "related_categories": ["document.presentation"],
  "ontology_notes": "optional free text for curators"
}
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | ✓ | `visual_candidates` 키와 동일 |
| `workflow_category` | ✓ | top-level slug (§3) |
| `sub_workflow` | ✓ | §4 테이블의 값 |
| `lifecycle_stage` | 선택 | §8; 없으면 `null` 생략 |
| `workflow_stage` | 선택 | §8.1; reporting 계열 — `progress` \| `interim` \| `result` \| `final` 배열 |
| `related_categories` | 선택 | **top-level** slug 배열 (sub는 넣지 않는 것을 권장) |
| `ontology_notes` | 선택 | 큐레이터 메모 |

### 10.2 Pair / synthetic row

pair 규칙에서 생성되는 row는 **동일 스키마**를 쓰되 `id`를 `prep_paired_document` 등 **합성 id**로 두고, `workflow_category`/`sub_workflow`를 **매핑 테이블**로 부여한다 (코드 또는 JSON sidecar).

### 10.3 중복 visual (qr 두 종)

metadata 상 **같은** `(workflow_category, sub_workflow)` 를 가질 수 있다. canonicalization은 **운영 정책**(TODO)으로 처리하고, 스키마는 막지 않는다.

---

## 11. feedback_log 연결 방향

앞으로 로그 한 건에 **추천 결과뿐 아니라 ontology 슬라이스**를 남기면, “아이콘 싸움”이 아니라 **의미 축 싸움**을 분석할 수 있다.

### 11.1 권장 필드 (이벤트 단위)

| 필드 | 설명 |
|------|------|
| `primary_workflow_category` | 사용자에게 보여준 해석의 주 축 |
| `primary_sub_workflow` | 주 축의 sub |
| `lifecycle_stage` | 있으면 (문서 등) |
| `related_workflow_categories` | 다축일 때만 |
| `matched_candidate_id` | 선택된 후보 id |
| `matched_meaning_text` | 이미 있다면 유지 |
| `runner_up_candidate_ids` | 있으면 nuance 분석에 유리 |
| `rejected_candidate_ids` | 명시적 거부 UI가 있을 때 |
| `rejected_primary_categories` | (선택) 거부된 후보들의 상위만 집계용으로 |

#### 11.1.1 `workflow_stage` observation (optional, reporting 축)

§8.1 보고 lifecycle calibration용. 스키마·예시·분석: [`feedback_log_schema.md`](feedback_log_schema.md).

| 필드 | 설명 |
|------|------|
| `inferred_workflow_stage` | 제목 keyword 추론 (`progress` \| `interim` \| `result` \| `final` \| `null`) |
| `matched_workflow_stage` | 선택 후보 metadata 허용 stage 목록 |
| `user_confirmed_workflow_stage` | 사람 라벨 (ground truth) |
| `workflow_stage_confidence` | lightweight heuristic (hard rule 아님) |
| `workflow_stage_source` | `keyword:…` \| `ambiguous:현황` \| `contextual:…` \| `manual_label` |
| `workflow_stage_ambiguous` | `현황` 등 stage 단정 불가 |
| `workflow_stage_mismatch` | inferred/confirmed ∉ matched (reporting 후보만) |

**1차 적재:** ambiguity scoring log (`tools/generate_ambiguity_scoring_log.py`).  
**분석:** `tools/analyze_workflow_stage_observations.py`.

### 11.2 분석 질문 예시

- 같은 `primary_workflow_category` 안에서 **어떤 sub**가 자주 이기는가?  
- `related`가 붙은 제목에서 **사용자 수정**이 늘어나는가?  
- `document.review` vs `document.edit` **오분류**가 특정 키워드에 집중하는가?
- `document.reporting`이 `document.review`로 떨어지는 제목은 상급자·결재권자 신호가 부족한가?
- `approval_request`와 `document_signature`가 “결재 받기” vs “결재하기”를 충분히 분리하는가?
- `tracking`으로 분리한 현황·응답·배정·집행 제목에서 사용자가 문서 visual보다 상태 visual을 선호하는가?
- `document.distribution`/`sharing`에서 channel visual과 object visual 중 사용자가 무엇을 더 선호하는가?

---

## 12. Ontology 안정화 TODO (policy / 기술)

- [ ] **`running_appointment`의 primary**를 `time_scheduling` vs `event_social` 중 하나로 고정하고, 다른 쪽은 항상 `related`로만 둘지 결정한다.  
- [ ] **`qr_auth` vs `qr_code_scan_auth`**: 하나를 canonical 후보로 두고, 다른 하나는 별칭·deprecated·동일 metadata로 집계할지 결정한다.  
- [ ] **`facility_physical` 세분화**: `tidy` 안의 room/office/mop를 **로그용으로만** 나눌지, sub를 더 쪼갤지 (데이터 증가 vs 해석력 트레이드오프).  
- [ ] **`document.prep`**: pair synthetic을 **항상 document 하위**로 로그에 찍을지, `lifecycle_stage=prep`만 쓸지 통일한다.  
- [ ] **`food_logistics` vs pair prep 🍰**: “간식 준비”가 들어오면 **preparation**으로만 ontology 로그를 남길지, visual은 🍰로 유지할지 문서화한다.  
- [ ] **`messenger` vs `institutional_meeting`**: “협의” 분쟁 시 **사용자 피드백 라벨**을 둘지 (category override).  
- [ ] **`publication` object/action guard**: `공고번호`, `게시판` 같은 context 단어와 실제 `게시/등록/공고 게시` action phrase를 계속 분리할지 사용자 피드백으로 검증한다.  
- [ ] **`tracking` prior**: `현황`, `상황`, `체크`가 너무 넓게 tracking으로 흡수되지 않도록 object/action phrase 중심으로 유지한다.  
- [ ] **metadata 저장 위치**: `visual_candidates.json` 인라인 vs `data/workflow_ontology_map.json` 분리 (번들·diff 가독성).  
- [ ] **recommendation engine**: 1단계로 로그에 ontology 필드만 채우고, 2단계에서 **category prior / penalty**를 점수에 반영할지 로드맵 확정.

---

## 13. Ontology 사용 원칙 (팀·코드 공통)

1. **새 visual 후보**는 먼저 **§5 트리의 어느 잎/빈 자리**인지 정한 뒤 추가한다.  
2. **새 top-level**은 PRD·이 문서 개정 없이 추가하지 않는다.  
3. **로그·대시보드**는 기본적으로 **primary_workflow_category**로 롤업한다.  
4. **related**는 “사용자 혼란이 예상되는 제목 패턴”이 있을 때만 채운다.  
5. 이 문서의 **§5 canonical tree**가 바뀌면 **변경 요약·날짜**를 아래에 남긴다(형식은 팀이 정해도 된다).

**문서 버전 / 스냅샷:** 1.5 — document flow stage boundary(§8.3)와 `document_flow_stage` metadata/scoring policy를 추가했다. §8.1 `workflow_stage`, §8.2 publication boundary와 함께 Living meaning model 블록이 우선이며, 버전 번호는 “이후 변경 불가”를 뜻하지 않는다.
