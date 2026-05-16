# PRD  
## Personal Notion Visual Memory Automation System

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

- 카테고리 분류
- 감성적 장식
- 일반 키워드 매칭

기반으로 동작한다.

하지만 사용자는:

- 실제 행동
- 작업 인터페이스
- workflow
- cognitive mode
- 서비스 UI 기억

을 기준으로 시각 요소를 선택한다.

즉 사용자의 아이콘 체계는:
# “분류”
가 아니라
# “행동 회상 시스템”

이다.

---

# 3. 사용자 행동 분석

## 핵심 특징

---

## 3-1. 행동 중심 기억

사용자는:
- 무엇을 다루는가
보다
- 실제로 어떤 행동을 하는가

를 더 중요하게 생각한다.

예:
- “강남서초 점검일정 안내”
→ 점검 ❌
→ 메일 발송 ⭕

---

## 3-2. 인터페이스 기반 기억

사용자는:
- 메일창
- 전화화면
- QR 인증화면
- 엑셀 UI
- 네이버폼 체크 UI
- 코드 에디터

같은 실제 작업 인터페이스를 기억한다.

---

## 3-3. workflow 기반 시각화

같은 금전 업무라도:

| 업무 | 사용 아이콘 |
|---|---|
| 월급여 입력 | 💰 |
| 일상경비 교부 요청 | 📝 |

처럼:
“어떻게 처리하는가”
에 따라 달라진다.

---

## 3-4. cognitive mode 기반 구분

사용자는:
- 구현
- 실행
- 사고
- 검토

를 서로 다른 모드로 인식한다.

예:

| 행동 | 시각 요소 |
|---|---|
| 브레인스토밍 | 🧠 |
| 코딩 구현 | code |
| 터미널 실행 | terminal |

---

## 3-5. 서비스 UI 색상 기억

사용자는:
서비스 자체의 시각 기억도 활용한다.

예:

| 서비스 | 색상 |
|---|---|
| Excel | green |
| Naver Form | green |
| Terminal | blue |

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
사용자가 시각 요소를 보는 순간:

- 해야 할 행동
- 작업 인터페이스
- workflow
- 서비스 UI

가 즉시 떠오르게 만드는 것이다.

---

# 5. 핵심 데이터 구조

---

# 5-1. sample_cases.json

## 역할
실제 사용자의 일정 제목과 선택 패턴을 저장한다.

## 목적
사용자의 행동 기억 방식을 AI가 학습하도록 한다.

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

  "interface_memory": [
    "엑셀",
    "스프레드시트",
    "테이블UI"
  ],

  "reason": "데이터 테이블 정리 작업 중심"
}
```

---

# 5-2. visual_candidates.json

## 역할
사용 가능한 시각 요소 vocabulary를 정의한다.

## 목적
AI가 선택 가능한 행동 회상 시각 요소를 제공한다.

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

    "meaning": [
      "엑셀",
      "스프레드시트",
      "데이터정리"
    ],

    "interface_memory": [
      "엑셀",
      "테이블UI"
    ]
  }
}
```

---

# 5-3. feedback_log.json

## 역할
GPT 추천과 실제 사용자 수정 내역 저장

---

## 목적
사용자의 실제 선택 패턴을 점진적으로 학습

---

# 6. workflow_priority 정의

| 값 | 의미 |
|---|---|
| 1 | workflow 핵심 행동 vocabulary |
| 2 | 특정 상황 보조 vocabulary |
| 3 | 개인적/특수 상황 vocabulary |

---

## 예시

### priority 1
- 📧
- 📞
- 💰
- 📝
- spreadsheet_work
- survey_form

---

### priority 2
- 🤝
- 🤵
- terminal
- urgent_notice

---

### priority 3
- 🍴
- 🚕
- 📦

---

# 7. 추천 로직

## 우선순위

---

## 1단계
sample_cases exact match

예:
```text
출장 여비 입력
```

→ 💰

---

## 2단계
visual_candidates keyword matching

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
카테고리보다 행동을 우선

---

## 원칙 2
사람보다 인터페이스를 우선할 수 있음

예:
- 과장 퇴근 인증
→ 사람 ❌
→ QR 인증 ⭕

---

## 원칙 3
서비스 UI 기억 활용 가능

예:
- Excel green
- Naver green

---

## 원칙 4
emoji와 notion icon은 동등한 기억 트리거

---

## 원칙 5
사용자 수정이 GPT 판단보다 우선

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
sample_cases 검색
↓
visual_candidates 검색
↓
workflow_priority 비교
↓
GPT 추론
↓
추천 결과 반환
↓
사용자 수정 가능
↓
feedback 저장
↓
Notion icon 자동 반영
```

---

# 11. 개발 단계

| 단계 | 목표 |
|---|---|
| 1 | Cursor 프로젝트 초기화 |
| 2 | FastAPI 서버 구축 |
| 3 | 추천 엔진 MVP |
| 4 | sample_cases matching |
| 5 | visual_candidates matching |
| 6 | GPT fallback |
| 7 | feedback 저장 |
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