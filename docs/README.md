# Personal-NotionVisual-memory-Automation-System

## 문서 (`docs/`)

| 문서 | 설명 |
| --- | --- |
| [docs/PRD.md](PRD.md) | 요구사항, 데이터 구조, 추천 로직 |
| [docs/workflow_philosophy.md](workflow_philosophy.md) | workflow 기반 철학·원칙 |
| [docs/workflow_ontology.md](workflow_ontology.md) | **추천 의미 backbone**: workflow category·lifecycle·related 축 (living model, 고정 표준 아님) |
| [docs/ARCHITECTURE.md](ARCHITECTURE.md) | 처리 파이프라인(P0–P7), **meaning layer** 위치 |

에디터·에이전트용 축약 규칙은 `.cursor/rules/icon_system.md`에서 관리한다.

## Core concepts (짧게)

- **Workflow resolution** — 제목·compound·interface 신호를 반영한 해석 축; 파이프라인과 함께 [`ARCHITECTURE.md`](ARCHITECTURE.md).
- **Workflow ontology** — 지금 시스템이 쓰는 **workflow meaning 모델**을 문서화한 것; `feedback_log`·후보 진화에 따라 **수정·실험**한다. [`workflow_ontology.md`](workflow_ontology.md).
- **Candidate philosophy** — 어떤 후보가 왜 경쟁하는지(`visual_candidates`·pair·priority); [`workflow_philosophy.md`](workflow_philosophy.md)와 PRD와 함께 읽는다.

루트 개요는 상위 디렉터리 [`README.md`](../README.md)를 참고한다.