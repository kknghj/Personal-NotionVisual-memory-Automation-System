# Semantic Boundary Workflow

## 목적
workflow boundary 수정 후 regression 및 ambiguity 변화를 안정적으로 검증한다.

---

## 표준 절차

1. ontology 수정
2. visual_candidates metadata 반영
3. scoring 반영
4. boundary test 추가
5. snapshot 생성
6. before/after 비교
7. regression 확인
8. ambiguity 변화 요약

---

## 필수 확인 항목

### Regression
- 기존 stable top1 유지 여부
- unrelated workflow 영향 여부

### Ambiguity
- tie 증가/감소
- semantic gap 변화
- channel/object/action 충돌 여부

### Snapshot
- top candidate movement
- semantic bonus 변화
- no-candidate 변화

---

## 결과 보고 형식

1. 수정 파일
2. boundary 정책 요약
3. 대표 ranking 변화
4. regression 여부
5. 남은 ambiguity
6. 다음 TODO