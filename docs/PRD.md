# PRD  
## Personal Notion Visual Memory Automation System

> **문서 위치**: `docs/PRD.md`. 철학·원칙 전개는 [`workflow_philosophy.md`](workflow_philosophy.md), **추천 의미·workflow 계층(backbone)** 은 [`workflow_ontology.md`](workflow_ontology.md), 파이프라인 개략은 [`ARCHITECTURE.md`](ARCHITECTURE.md), 에이전트용 축약 규칙은 [`.cursor/rules/icon_system.md`](../.cursor/rules/icon_system.md).

---

# 1. 프로젝트 개요

## 프로젝트명
Personal Notion Visual Memory Automation System

---

## 프로젝트 목표

노션 일정 제목 및 메모를 분석하여,
사용자의 실제 행동 기억 방식에 맞는:

- emoji
- Notion icon
- icon color

를 자동 추천하고,
최종적으로 Notion 페이지 아이콘까지 자동 반영하는 개인 AI 시스템을 구축한다.

---

# 2. 문제 정의

기존 일정 관리 시스템의 아이콘은 대부분:

* 카테고리 분류
* 감성적 장식
* 단순 keyword matching
* 일반 NLP 기반 태그 분류

방식으로 동작한다.

하지만 사용자는:

* 실제 행동(workflow)
* 작업 인터페이스
* 행동 대상(subject/object)
* cognitive mode
* 서비스 UI 기억
* 행동 + 대상 조합(pair interpretation)

을 기준으로 시각 요소를 선택한다.

즉 사용자의 아이콘 체계는:

# “분류 시스템”

이 아니라

# “행동 회상 시스템”

이다.

또한 사용자는:
단일 행동 keyword만으로 행동을 인식하지 않는다.

예:

* “회의자료 수정”
* “음식 준비”
* “일정 확인”
* “바탕화면 폴더 정리”

처럼:
동일한 행동 keyword라도,
무엇을 대상으로 하는가(subject)에 따라
완전히 다른 workflow와 visual을 연상한다.

즉:
이 시스템은:

# “행동 keyword 매칭”

이 아니라

# “workflow 해석(interpreting workflow intention)”

을 목표로 한다.

---

## 2-1. Workflow ontology와 추천 의미 모델

추천은 **단어 포함(keyword matching)만**으로 끝나지 않는다. 제목의 단어는 **workflow meaning**(어떤 업무 영역인지, 문서 lifecycle의 어디인지, 전화·메신저·메일 등 **communication nuance**, 제목에 드러나는 **interface anchor**)를 띄우는 단서이고, `visual_candidates`의 `meaning`·`workflow_resolution`·`workflow_priority`와 compound·pair 규칙은 그 의미를 **규칙과 순위로 구현**하는 층이다.

프로젝트는 이 의미 축을 한곳에 정리한 **[`workflow_ontology.md`](workflow_ontology.md)** 를 **추천 철학의 backbone**(공통 언어)로 둔다. 상위 **workflow category**, **sub workflow**, **lifecycle stage**, **related category**(한 제목이 두 축일 때의 보조 태그) 등을 여기서 정의·조정한다.

이 ontology는 **절대적인 단일 taxonomy 표준**이 아니라, **`feedback_log`**, **후보 데이터 진화**, **`workflow_resolution` 튜닝**, 실제 **추천 충돌·사용자 선택 패턴**에 맞춰 **계속 고쳐 쓰는 living document**에 가깝다. 구현이 앞서가면 문서를 그에 맞게 줄인다.

계층·후보 매핑 방향·로그 필드 제안의 상세는 **`workflow_ontology.md`** 본문을 따른다.

---

# 3. 사용자 행동 분석

## 핵심 특징

---

## 3-1. 행동 중심 기억

사용자는:

* 무엇을 다루는가
  보다
* 실제로 어떤 행동을 하는가

를 더 중요하게 생각한다.

예:

* “강남서초 점검일정 안내”
  → 점검 ❌
  → 메일 발송 ⭕

---

## 3-2. 인터페이스 기반 기억

사용자는:

* 메일창
* 전화화면
* QR 인증화면
* 엑셀 UI
* 네이버폼 체크 UI
* 코드 에디터
* 터미널 화면

같은 실제 작업 인터페이스를 기억한다.

즉:
카테고리보다:

# “실제 사용한 인터페이스”

가 더 강한 기억 anchor가 된다.

---

## 3-3. workflow 기반 시각화

같은 업무 category라도:
실제 처리 workflow에 따라 visual이 달라진다.

예:

| 업무          | 사용 visual |
| ----------- | --------- |
| 월급여 입력      | 💰        |
| 일상경비 교부 요청  | 📝        |
| 강사 일정 메일 안내 | 📧        |
| 과장님 QR 인증   | qr-code   |

즉:
사용자는:
“무슨 업무인가”
보다

# “실제로 어떤 행동을 수행하는가”

를 기반으로 시각 요소를 선택한다.

---

## 3-4. 행동 + 대상(pair) 기반 해석

사용자는:
행동 keyword를 단독으로 해석하지 않는다.

동일한 행동이라도:
대상(subject/object)에 따라 completely different workflow를 연상한다.

예:

| 표현         | 기대 visual         |
| ---------- | ----------------- |
| 면접자료 준비    | 📄                |
| 음식 준비      | 🍱                |
| 행사 준비      | 🎉                |
| 일정 확인      | 💬                |
| 회의자료 확인    | 📄                |
| 바탕화면 폴더 정리 | 📁                |
| 회의실 정리     | chair             |
| 카톡 알림 정리   | bell-notification |

즉:
시스템은:

# 행동 keyword

가 아니라

# “행동 + 대상 pair”

를 함께 해석해야 한다.

---

## 3-5. modifier와 workflow anchor 분리

사용자의 일정 표현에는:

* modifier(context)
* workflow anchor

가 함께 존재한다.

예:

| modifier | workflow anchor |
| -------- | --------------- |
| 점심       | 카톡              |
| 과장님      | 메일              |
| 저녁       | 전화              |

사용자는:
modifier보다:

# 실제 행동 workflow(anchor)

를 더 중요하게 기억한다.

즉:

* 점심 카톡 확인 → 💬
* 과장님 메일 전달 → 📧

처럼:
modifier는 context 역할만 수행한다.

---

## 3-6. compound noun 기반 의미 보호

사용자는:
compound noun 내부 substring을
독립 workflow keyword로 인식하지 않는다.

예:

* 교육청
* 보고자료
* 회의자료
* 계획안
* 검토보고서

같은 표현은:
하나의 subject noun으로 인식된다.

즉:

* “보고자료”의 “보고”
* “교육청”의 “교육”

같은 substring은:
독립 workflow dominance를 가져서는 안 된다.

---

## 3-7. cognitive mode 기반 구분

사용자는:

* 구현
* 실행
* 사고
* 검토
* 정리
* 커뮤니케이션

을 서로 다른 cognitive mode로 인식한다.

예:

| 행동     | visual   |
| ------ | -------- |
| 브레인스토밍 | 🧠       |
| 코딩 구현  | code     |
| 터미널 실행 | terminal |
| 자료 검토  | 📄       |
| 카톡 문의  | 💬       |

즉:
시스템은:
단순 업무 category가 아니라,

# 사용자의 cognitive workflow mode

를 해석해야 한다.

---

## 3-8. 서비스 UI 색상 기억

사용자는:
서비스 자체의 시각 기억도 활용한다.

예:

| 서비스        | 색상    |
| ---------- | ----- |
| Excel      | green |
| Naver Form | green |
| Terminal   | blue  |

즉 색상도:

# workflow 회상 보조 요소

로 작동한다.

---

# 4. 핵심 철학

이 프로젝트는:

# “아이콘 추천기”

가 아니다.

대신:

# “행동 회상 인터페이스 AI”

이다.

목표는:
사용자가 visual을 보는 순간:

* 해야 할 행동
* 작업 인터페이스
* workflow
* 서비스 UI
* cognitive mode
* 행동 대상(subject)

이 즉시 떠오르게 만드는 것이다.

즉:
이 시스템의 목적은:
“예쁜 아이콘 추천”
이 아니라,

# “사용자의 행동 기억 구조를 시각적으로 압축”

하는 것이다.


---

# 5. 핵심 데이터 구조

JSON 데이터셋(본 장에서 서술하는 `data/sample_cases.json`, `data/visual_candidates.json`, `data/feedback_log.json` 등)은 저장소에서 **`data/`** 디렉터리 아래 단일 경로로 관리한다. 선언적 페어 규칙은 `data/pair_rules.json`을 사용한다.

---

# 5-1. data/sample_cases.json

## 역할

실제 사용자의 일정 제목과
실제 선택한 visual 패턴을 저장한다.

---

## 목적

사용자의:

* workflow 기억 방식
* 행동 + 대상(pair) 해석 방식
* interface 기억
* modifier 사용 패턴
* cognitive mode

를 AI가 학습하도록 한다.

즉:
단순 keyword 학습이 아니라,

# “사용자의 행동 회상 구조”

를 학습하는 데이터셋이다.

---

## 핵심 특징

`data/sample_cases.json`은:
단순 title-example 데이터가 아니다.

각 사례는:

* 어떤 행동을 수행하는지
* 무엇을 대상으로 하는지
* 어떤 interface를 사용하는지
* 어떤 workflow mode인지

를 함께 표현한다.

---

## 구조 예시

```json
{
  "title": "교육 신청 현황 엑셀 정리",

  "visual": {
    "type": "notion_icon",
    "value": "grid-rectangle-2x3",
    "color": "green"
  },

  "focus": "엑셀 테이블 정리",

  "workflow_type": "spreadsheet_workflow",

  "pair_context": {
    "action": "정리",
    "subject": "엑셀 현황"
  },

  "interface_memory": [
    "엑셀",
    "스프레드시트",
    "테이블UI"
  ],

  "modifier": [
    "교육신청"
  ],

  "reason": "데이터 테이블 정리 작업 중심"
}
```

---

# 5-2. data/visual_candidates.json

후보 항목이 **어느 workflow meaning 영역에 속하는지**는 [`workflow_ontology.md`](workflow_ontology.md)의 계층·메타데이터 방향과 맞추어 읽는다(ontology는 **evolving** 문서다).

## 역할

사용 가능한 visual vocabulary와
workflow interpretation rule을 정의한다.

---

## 목적

AI가:

* workflow
* 행동 대상(subject)
* interface
* cognitive mode

를 기반으로
사용자의 기억 구조에 맞는 visual을 선택하도록 한다.

---

## 핵심 특징

`data/visual_candidates.json`은:
단순 keyword dictionary가 아니다.

각 visual은:

* 어떤 workflow인지
* 어떤 대상(subject)과 잘 결합되는지
* 어떤 interface를 연상시키는지
* 어떤 modifier에 약한지

를 함께 가진다.

즉:

# “workflow semantic vocabulary”

역할을 수행한다.

---

## 구조 예시

```json
{
  "spreadsheet_work": {

    "visual": {
      "type": "notion_icon",
      "value": "grid-rectangle-2x3",
      "color": "green"
    },

    "workflow_priority": 1,

    "workflow_type": "spreadsheet_workflow",

    "meaning": [
      {
        "text": "엑셀",
        "workflow_resolution": 3,
        "interface_dominance": 10
      },
      {
        "text": "스프레드시트",
        "workflow_resolution": 3,
        "interface_dominance": 10
      }
    ],

    "paired_subjects": [
      "현황",
      "정산",
      "명단",
      "데이터"
    ],

    "interface_memory": [
      "엑셀",
      "테이블UI"
    ],

    "cognitive_mode": [
      "데이터정리",
      "테이블작업"
    ]
  }
}
```

---

# 5-3. data/feedback_log.json

## 역할

`data/feedback_log.json`은 **관측 로그(observation log)** 이다.  
추천 API·오프라인 scoring·(후속) 사용자 UI에서 일어난 **사실**을 시간순으로 남긴다.

**training dataset이 아니다.** 로그 한 건이 곧바로 가중치·penalty·hard rule을 바꾸지 않는다.

스키마·철학: [`feedback_log_schema.md`](feedback_log_schema.md)

---

## 목적 (observation first, policy later)

### 지금 (기록)

* 시스템이 **무엇을 추천**했는지 (`recommended_candidate_id`, visual, reason 등 — 후속 필드 확장)
* **어떤 후보**가 상위에 있었는지 (ranking 요약 — 후속)
* 사용자가 **무엇을 선택·수정**했는지 (`user_selected_*`, correction 이벤트 — 후속 UI)
* **semantic observation slice** (예: `workflow_stage` ambiguity·mismatch — 부분 구현, scoring log export)
* 분석·회귀·calibration을 위한 **증거(evidence)** 보존

### 나중 (정책 결정 — 미구현)

반복 패턴이 쌓인 뒤에만, 사람이 검토하고 다음을 **검토할지** 결정한다:

* ontology·`visual_candidates` 수정
* soft calibration·bonus/penalty **실험**
* reranking feature·개인화 설정
* hard filter 도입 여부

즉 **개인화(personalization)** 는 가능한 **후속 목표**이지, 로그 적재와 동시에 일어나지 않는다.

---

## 핵심 특징

단순 “correction만 모은 파일”이 아니라, **추천 맥락 + 선택/수정 + (선택) semantic slice**를 한 이벤트로 묶는다.

기록 대상 예 (Layer A·B — 구현은 단계적으로):

* 추천 visual·후보 id
* 사용자 최종 선택 visual·후보 id
* 변경 여부·변경 유형 (`user_correction` 등 — 후속)
* modifier·workflow pair·keyword 충돌 맥락 (`input_context` — 후속)
* reporting 축 `workflow_stage` 관측 ([`feedback_observations/workflow_stage.md`](feedback_observations/workflow_stage.md))

---

## 현재 구현 범위 (요약)

| 항목 | 상태 |
|------|------|
| `feedback_log.json` placeholder (`[]`) | ✓ |
| `append_feedback_log_entry()` | 코드만; live API/UI 미연동 |
| ambiguity scoring → export | ✓ |
| penalty / rerank / hard filter / ML / Notion pipeline | **하지 않음** |

---

# 6. workflow_priority 정의

workflow_priority는:
“중요도”
가 아니라,

# “workflow 기억 anchor 강도”

를 의미한다.

즉:
사용자가 visual을 보았을 때,
얼마나 즉시 행동을 회상하는가를 나타낸다.

---

| 값 | 의미                            |
| - | ----------------------------- |
| 1 | 강한 workflow/interface anchor  |
| 2 | 중간 수준 workflow/context anchor |
| 3 | modifier/context/개인적 상황       |

---

## priority 1

실제 interaction interface 또는
강한 행동 workflow

예:

* 📧
* 📞
* 💬
* qr-code
* spreadsheet_work
* survey_form
* terminal
* code_editor

특징:

* 즉시 행동 회상 가능
* 높은 interface dominance
* modifier보다 우선됨

---

## priority 2

특정 상황 workflow 또는
중간 수준 cognitive mode

예:

* 🤝
* 👩‍🏫
* 📄
* 🧠
* 🎉
* 📁

특징:

* 특정 맥락에서 강해짐
* 행동 + 대상(pair)에 영향받음

---

## priority 3

modifier/context/개인적 상황 vocabulary

예:

* 🍚
* 🚕
* 📦
* 🤵
* 🍽️

특징:

* workflow anchor를 직접 결정하지 않음
* context 설명 역할
* interface dominance를 이기지 못함


---

# 7. 추천 로직

## 우선순위

---

## 1단계
data/sample_cases.json exact match

예:
```text
출장 여비 입력
```

→ 💰

---

## 2단계
data/visual_candidates.json keyword matching

예:
```text
메일
```

→ 📧

---

## 3단계
workflow_priority 기반 선택

더 구체적인 workflow를 우선 추천

예:
- 📝
- spreadsheet_work

동시 후보일 경우:
→ spreadsheet_work 우선

---

## 4단계
GPT 행동 추론 fallback

규칙 없는 경우:
- 행동
- 인터페이스
- workflow
- 서비스 UI

기반으로 추론

---

# 8. 핵심 추천 원칙

## 원칙 1

카테고리보다 workflow를 우선한다

사용자는:
“무슨 업무인가”
보다
“실제로 어떤 행동을 수행하는가”

를 더 중요하게 기억한다.

예:

* 급여 관련 보고자료 작성
  → 급여 ❌
  → 작성 ⭕

* 수당 반납 공문 송부
  → 수당 ❌
  → 공문 송부 ⭕

즉:
업무 category보다
실제 workflow/action을 우선 추천한다.

---

## 원칙 2

행동 keyword는 단독으로 해석하지 않는다

동일한 행동 keyword라도:
대상(subject/object)에 따라
completely different workflow mode를 생성할 수 있다.

예:

| 표현         | 기대 visual         |
| ---------- | ----------------- |
| 면접자료 준비    | 📄                |
| 음식 준비      | 🍱                |
| 행사 준비      | 🎉                |
| 일정 확인      | 💬                |
| 회의자료 확인    | 📄                |
| 바탕화면 폴더 정리 | 📁                |
| 회의실 정리     | chair             |
| 카톡 알림 정리   | bell-notification |

즉:
시스템은:
단일 행동 keyword가 아니라,

# “행동 + 대상 pair”

를 기반으로 workflow를 해석한다.

---

## 원칙 3

사람보다 인터페이스를 우선할 수 있음

사용자는:
사람(person)보다
실제 interaction interface를 더 강하게 기억한다.

예:

* 과장님 메일 전달
  → 과장님 ❌
  → 메일 ⭕

* 대표 전화 문의
  → 대표 ❌
  → 전화 ⭕

* 과장님 QR 인증
  → 사람 ❌
  → QR 인증 ⭕

즉:
사람 keyword는:
modifier/context로 취급될 수 있으며,

* 메일
* 전화
* QR
* 카톡

같은 interface/workflow keyword를 우선 추천한다.

---

## 원칙 4

modifier보다 workflow anchor를 우선한다

사용자의 일정 표현에는:

* modifier(context)
* workflow anchor

가 함께 존재한다.

예:

| modifier | workflow anchor |
| -------- | --------------- |
| 점심       | 카톡              |
| 저녁       | 메일              |
| 과장님      | QR              |

사용자는:
modifier보다
실제 행동 workflow(anchor)를 더 중요하게 기억한다.

예:

* 점심 카톡 확인 → 💬
* 저녁 메일 안내 → 📧
* 과장님 QR 인증 → qr-code

즉:
modifier는 context 역할만 수행하며,
visual dominance는 workflow anchor가 가진다.

---

## 원칙 5

compound noun 내부 substring은 dominance를 갖지 않는다

사용자는:
compound noun 내부 substring을
독립 workflow keyword로 인식하지 않는다.

예:

* 교육청
* 보고자료
* 회의자료
* 계획안
* 검토보고서

같은 표현은:
하나의 subject noun으로 취급한다.

즉:

* “교육청”의 “교육”
* “보고자료”의 “보고”
* “회의자료”의 “회의”

같은 substring은:
독립 workflow dominance를 가져서는 안 된다.

---

## 원칙 6

실제 사용 인터페이스는 높은 dominance를 가진다

사용자는:
카테고리보다
실제 사용한 인터페이스를 강하게 기억한다.

따라서 아래 keyword는:
높은 interface dominance를 가진다.

* 메일
* 전화
* 카톡
* QR
* 엑셀
* 네이버폼
* 터미널
* Cursor
* VSCode

예:

* 엑셀 정리 → spreadsheet
* 카톡 문의 → 💬
* QR 등록 → qr-code

즉:
실제 interaction interface를 우선 추천한다.

---

## 원칙 7

generic action keyword는 단독 dominance를 가지지 않는다

아래와 같은 일반 행동 keyword는:
단독으로는 의미가 약하다.

* 정리
* 준비
* 확인
* 수정
* 관리
* 운영

이 keyword들은:
대상(subject/object)과 함께 해석되어야 한다.

예:

* 캐비넷 정리 → 🗄️
* 회의실 정리 → chair
* 음식 준비 → 🍱
* 면접자료 준비 → 📄
* 일정 확인 → 💬
* 회의자료 확인 → 📄

즉:
generic action 자체보다
행동 대상(subject)을 우선 해석한다.

---

## 원칙 8

emoji와 notion icon은 동등한 기억 trigger이다

사용자에게:
emoji와 notion icon은
모두 동일한 workflow 기억 trigger 역할을 수행한다.

중요한 것은:
“예쁜 디자인”
이 아니라,

* 행동 회상 속도
* workflow 직관성
* interface 연상 가능성

이다.

---

## 원칙 9

서비스 UI 색상 기억을 활용할 수 있다

사용자는:
서비스 자체의 시각 기억도 활용한다.

예:

| 서비스        | 색상    |
| ---------- | ----- |
| Excel      | green |
| Naver Form | green |
| Terminal   | blue  |

즉:
색상도 workflow 회상 보조 요소로 활용 가능하다.

---

## 원칙 10

사용자 수정이 AI 판단보다 우선한다

이 시스템은:
일반적인 icon recommendation AI가 아니라,

“사용자의 workflow 기억 시스템”

이다.

따라서:
**평가·튜닝 시** AI 일반 추론보다 실제 사용자 선택·수정을 우선한다.

즉:
사용자의 실제 선택 패턴이 **ground truth** 로 쓰이지만,  
`feedback_log`에 기록된다고 해서 **즉시 학습·랭킹 변경이 일어나지는 않는다** (관측 후 정책 결정).

---

# 9. API 구조

---

## POST /recommend-icon

### 입력

```json
{
  "title": "교육 신청 현황 엑셀 정리"
}
```

---

## 출력

```json
{
  "visual": {
    "type": "notion_icon",
    "value": "grid-rectangle-2x3",
    "color": "green"
  },

  "focus": "엑셀 테이블 정리",

  "reason": "데이터 테이블 정리 작업 중심"
}
```

---

# 10. 시스템 흐름

```text
노션 일정 생성
↓
icon 없는 일정 탐색
↓
일정 제목 분석
↓
data/sample_cases.json 검색
↓
data/visual_candidates.json 검색
↓
workflow_priority 비교
↓
GPT 추론
↓
추천 결과 반환
↓
사용자 수정 가능
↓
data/feedback_log.json 에 관측 이벤트 기록 (후속; 현재 미연동)
↓
Notion icon 자동 반영 (후속)
```

---

# 11. 개발 단계

| 단계 | 목표 |
|---|---|
| 1 | Cursor 프로젝트 초기화 |
| 2 | FastAPI 서버 구축 |
| 3 | 추천 엔진 MVP |
| 4 | data/sample_cases.json matching |
| 5 | data/visual_candidates.json matching |
| 6 | GPT fallback |
| 7 | data/feedback_log.json 관측 적재 (API/UI 연동 후속) |
| 8 | Notion API 연결 |
| 9 | 자동 실행 |
| 10 | 개발일지 자동화 |

---

# 12. 개발일지 자동화 목표

개발 과정 중:

- 구현 내용
- 설계 변경
- 추천 기준 수정
- workflow 추가

를 자동으로 노션 개발일지 DB에 기록한다.

---

# 13. 성공 기준

## 1차 성공
추천 결과를 보고:
“왜 이 아이콘이 선택됐는지 납득된다.”

---

## 2차 성공
사용자 수정 빈도가 감소한다.

---

## 3차 성공
시각 요소만 보고도:
- 행동
- workflow
- 인터페이스

가 즉시 떠오른다.

---

# 14. 최종 프로젝트 정의

# “사용자의 행동 기억 방식과 workflow 인터페이스를 학습하여, 미래의 행동을 가장 빠르게 회상하게 만드는 개인 시각 기억 AI 시스템”