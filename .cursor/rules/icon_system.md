# Icon System Rules

> **역할**: 프로젝트의 상세 철학은 [`docs/workflow_philosophy.md`](../../docs/workflow_philosophy.md), 제품·데이터 스펙은 [`docs/PRD.md`](../../docs/PRD.md)를 본다.

이 프로젝트는 일반 아이콘 추천기가 아니라
사용자의 workflow 기억 시스템이다.

핵심 원칙:

1. category보다 workflow 우선

- "무슨 업무인가"보다
  "실제로 어떤 행동을 하는가"를 우선

2. 행동 keyword 단독 해석 금지

- action + subject pair 기반 해석
- 예:
  - 음식 준비 → 🍱
  - 자료 준비 → 📄
  - 폴더 정리 → 📁

3. modifier보다 workflow anchor 우선

- 점심 카톡 확인
  → 점심 ❌ / 카톡 ⭕

- 과장님 QR 인증
  → 과장님 ❌ / QR ⭕

4. 사람보다 interface 우선 가능

- 메일 → 📧
- 전화 → 📞
- 카톡 → 💬
- QR → qr-code

5. compound noun 보호

- 교육청의 "교육"
- 보고자료의 "보고"

같은 substring은
독립 workflow keyword처럼 해석 금지

6. generic action keyword는 subject와 함께 해석

- 정리
- 준비
- 확인
- 수정
- 관리
- 운영

7. interface dominance 강하게 반영
   높은 dominance:

- 메일
- 전화
- 카톡
- QR
- 엑셀
- 네이버폼
- terminal
- code

8. workflow_priority 의미

- 1 = 강한 workflow/interface anchor
- 2 = 중간 workflow/context
- 3 = modifier/context

9. emoji와 notion icon은 동등한 trigger

10. 사용자 수정 결과가 최종 truth source
