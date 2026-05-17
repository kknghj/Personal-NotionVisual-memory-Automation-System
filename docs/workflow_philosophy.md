# workflow philosophy

> **위치**: `docs/workflow_philosophy.md`. 요구사항·데이터 구조는 [`PRD.md`](PRD.md), 에이전트용 규칙 요약은 [`.cursor/rules/icon_system.md`](../.cursor/rules/icon_system.md).

이 프로젝트는 일반 아이콘 추천기가 아니라
사용자의 행동 회상 시스템이다.

사용자는:
- 카테고리
보다
- 실제 행동(workflow)
- 행동 대상(subject/object)
- 인터페이스 기억
- 서비스 UI 기억
- cognitive mode

를 우선한다.

즉:
이 시스템은 단순 keyword matcher가 아니라,
사용자의 workflow 기억 구조를 해석하는 시스템이다.

--------------------------------------------------
핵심 원칙
--------------------------------------------------

## 1. 카테고리보다 workflow를 우선

사용자는:
“무슨 업무인가”
보다
“실제로 어떤 행동을 수행하는가”

를 더 중요하게 기억한다.

예:
- 급여 관련 보고자료 작성
→ 급여 ❌
→ 작성 ⭕

- 수당 반납 공문 송부
→ 수당 ❌
→ 공문 송부 ⭕

--------------------------------------------------

## 2. 행동 keyword는 단독으로 해석하지 않는다

동일한 행동 keyword라도,
대상(subject)에 따라
completely different workflow mode가 생성될 수 있다.

예:

- 면접자료 준비 → 📄
- 음식 준비 → 🍱
- 행사 준비 → 🎉

- 일정 확인 → 💬
- 회의자료 확인 → 📄

- 바탕화면 폴더 정리 → 📁
- 회의실 정리 → chair
- 카톡 알림 정리 → bell

즉:
(action, subject)
pair를 함께 해석해야 한다.

--------------------------------------------------

## 3. modifier보다 workflow anchor를 우선

사용자의 일정 표현에는:
- modifier(context)
- workflow anchor

가 함께 존재한다.

예:

- 점심 카톡 확인
→ 점심 ❌
→ 카톡 ⭕

- 과장님 QR 인증
→ 과장님 ❌
→ QR ⭕

즉:
modifier는 context 역할이며,
실제 workflow/interface가 dominance를 가진다.

--------------------------------------------------

## 4. 사람보다 인터페이스를 우선 가능

예:
- 과장님 메일 전달
→ 사람 ❌
→ 메일 ⭕

- 대표 전화 문의
→ 사람 ❌
→ 전화 ⭕

- 과장님 QR 인증
→ 사람 ❌
→ QR 인증 ⭕

--------------------------------------------------

## 5. compound noun 내부 substring은 dominance를 갖지 않는다

예:
- 교육청
- 보고자료
- 회의자료
- 계획안

같은 표현은:
하나의 subject noun으로 취급한다.

즉:
- 교육청의 "교육"
- 보고자료의 "보고"

같은 substring은
독립 workflow keyword처럼 동작하면 안 된다.

--------------------------------------------------

## 6. generic action keyword는 단독 dominance를 갖지 않는다

아래 행동 keyword는:
대상(subject)과 함께 해석되어야 한다.

- 정리
- 준비
- 확인
- 수정
- 관리
- 운영

즉:
단일 행동보다
“무엇을 하는가”
를 우선 해석한다.

--------------------------------------------------

## 7. 인터페이스 기반 기억을 강하게 반영

사용자는:
실제 사용한 인터페이스를 강하게 기억한다.

높은 interface dominance 예시:

- 메일 → 📧
- 전화 → 📞
- 카카오톡 → 💬
- QR 인증 → qr-code
- Excel 작업 → green spreadsheet icon
- Naver Form → green checkmark-circle
- 코딩 구현 → code
- 실행/환경설정 → terminal

--------------------------------------------------

## 8. emoji와 notion icon은 동등한 기억 trigger

중요한 것은:
예쁜 디자인이 아니라,

- 행동 회상 속도
- workflow 직관성
- interface 연상 가능성

이다.

--------------------------------------------------

## 9. workflow_priority는 “중요도”가 아니라
“workflow 기억 anchor 강도”를 의미한다

- priority 1:
강한 interface/workflow anchor

- priority 2:
중간 수준 workflow/context

- priority 3:
modifier/context/개인적 상황

### 9.1 런타임에서의 대응 (semantic vs sorting)

- **Semantic (데이터 계약)**: ``visual_candidates.json``의 필드 이름 ``workflow_priority`` — 위 1·2·3 철학이 **카탈로그 작성 규약**이다. 문서·리뷰 시에는 **workflow anchor strength** / **catalog anchor level** 같은 표현을 병기하면 혼동이 줄어든다.
- **Sorting mechanics**: P6 통합 정렬에서 같은 숫자가 ``CandidateRow.sort_secondary_wp`` 슬롯에 **복사**되어, meaning 행끼리 또는 pair와의 **tie-break**에 쓰인다. 이 슬롯은 **pair 규칙**에서는 ``pair_rules.json``의 **별도** 키 ``sort_secondary_wp``(예: modify vs organize 순서)에서 오므로, **“이름은 비슷하지만 pair 쪽 값은 catalog 1/2/3 스케일과 동일하지 않을 수 있다”**는 점이 혼동의 원인이었다. 상세 비교 순서는 [`ARCHITECHURE.md`](ARCHITECHURE.md) §8.5 참고.

--------------------------------------------------

## 10. 사용자 수정 기록이 최종 truth source

AI 일반 추론보다:
실제 사용자의 수정 결과를 우선한다.

이 시스템은:
일반 icon recommendation AI가 아니라,

사용자의 workflow 기억 시스템이다.