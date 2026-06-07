# Boundary Design Principles

## 목적

Boundary는 candidate를 추가하는 작업이 아니다.

Boundary의 목적은

> 여러 후보가 모두 논리적으로 맞을 때,
> 무엇을 우선적으로 인식할 것인가를 정의하는 것

이다.

---

# 1. Boundary 수정의 기본 원칙

Boundary는 추천 결과를 맞추기 위한 임시 보정 수단이 아니다.

다음 조건을 모두 만족할 때만 boundary 수정이 허용된다.

1. candidate가 이미 존재한다.
2. metadata만으로 해결되지 않는다.
3. top candidate 경쟁이 발생한다.
4. 우선순위 판단 기준이 존재한다.

예시:

* 보도자료 확인
* 세금계산서 검토
* 행사자료 메일 송부
* 네이버폼 신청 접수

---

# 2. Candidate 문제와 Boundary 문제를 구분한다

## Candidate 문제

후보 자체가 존재하지 않는다.

예:

* 드라이브 업로드
* 세금계산서 검토
* 내부회의 참석

초기 상태

해결 방법:

* candidate 추가
* metadata 보강
* keyword coverage 보강

---

## Boundary 문제

후보는 존재하지만 우선순위가 충돌한다.

예:

보도자료 확인

* document_review
* press_release_review

세금계산서 검토

* document_review
* tax_invoice_review

해결 방법:

* boundary 조정
* scoring 조건 조정
* dominance 규칙 조정

---

# 3. Boundary Pilot 방식

Boundary는 대규모 수정하지 않는다.

반드시 Pilot 방식으로 진행한다.

절차:

1. 문제 정의
2. 현재 ranking 분석
3. 충돌 원인 분석
4. 최소 수정안 설계
5. 테스트 작성
6. snapshot 생성
7. regression 확인
8. 채택 여부 결정

---

# 4. 최소 수정 원칙

Boundary는 가능한 한 좁게 적용한다.

좋은 예:

"object-specific review compound가 존재할 때만 generic review boost 제한"

나쁜 예:

"모든 review 점수 하향"

좋은 예:

"메일 channel이 명시된 경우만 mail dominance 적용"

나쁜 예:

"송부 계열 전체를 mail 우선"

---

# 5. Object-Specific Review Boundary

## 배경

다음 사례에서 문제가 발견되었다.

### 사례 1

식생활교육 보도자료 확인

기존:

document_review

후보 존재:

press_release_review

---

### 사례 2

세금계산서 검토

기존:

document_review

후보 존재:

tax_invoice_review

---

원인:

generic document_review가 review soft boost를 받아
object-specific review candidate를 지속적으로 이김.

---

## Pilot 결과

채택

적용 원칙:

object-specific review compound가 존재하는 경우

* generic document_review review boost 제한
* object-specific review candidate review boost 적용

예:

* 보도자료 확인
* 보도자료 검토
* 세금계산서 검토
* 영수증 검토

---

## 중요

이번 구현은 Pilot 구현이다.

현재는 명시적 object term 목록을 사용한다.

예:

* 보도자료
* 세금계산서
* 영수증
* 계산서

---

## 장기 일반화 방향

향후 object-specific review candidate가 증가할 경우

boundary 코드에 object 명사를 직접 추가하지 않는다.

대신 candidate metadata를 활용한다.

예:

* semantic_role
* object_type
* interaction_mode=review_confirm

등을 이용하여

"object-specific review candidate"

를 자동 판별하는 일반화 구조를 검토한다.

---

# 6. Regression Gate

Boundary는 정확도보다 안정성을 우선한다.

채택 조건:

* 의도한 title만 변경
* unrelated workflow 영향 없음
* high ambiguity 급증 없음
* tie count 급증 없음
* no_candidate 증가 없음
* 기존 stable top1 유지

---

# 7. Boundary Backlog 우선순위

현재 후보:

1. 행사자료 메일 송부
2. 본인인증화면 수정 제안
3. 네이버폼 신청 접수
4. 정책자료 게시
5. 보도자료 검토 요청
6. 자료제출검토

---

충돌 유형:

* channel vs object
* interface vs action
* form vs submission
* publication vs document
* request vs review
* submission vs review

Boundary는 위 충돌 유형별로 독립적으로 검증한다.

여러 유형을 한 번에 수정하지 않는다.

---

# 8. Boundary 설계 철학

Boundary의 목표는

"정답률을 높이는 것"

이 아니다.

Boundary의 목표는

> 추천 결과가 왜 그렇게 나왔는지 설명 가능하게 만드는 것

이다.

설명할 수 없는 규칙은 채택하지 않는다.

하드코딩된 예외보다

일반화 가능한 규칙을 우선한다.

추천 정확도보다

회귀 가능성이 낮고 설명 가능한 구조를 우선한다.
