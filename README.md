# Notion icon automation (personal)

노션 일정 제목을 분석해 **emoji / Notion icon** 추천을 돕는 Python **FastAPI** 서비스입니다. 실행 방법은 [`AGENTS.md`](AGENTS.md)를 참고하세요.

## Core concepts

- **Workflow resolution** — 제목·의미에서 interface 앵커·문서 신호 등을 읽어 순위·필터에 쓰는 해석 축 (`app/workflow_resolution.py`, PRD §6 근처).
- **Workflow ontology** — 추천을 “아이콘 목록”이 아니라 **업무 의미(category, sub-workflow, lifecycle, related 축)** 로 말하기 위한 **living meaning model**. 추천 철학의 **backbone**이지만 **고정 taxonomy가 아님** (`feedback_log`·튜닝·충돌에 따라 진화). 상세: [`docs/workflow_ontology.md`](docs/workflow_ontology.md).
- **Candidate philosophy** — `visual_candidates`·`pair_rules`·`sample_cases`가 함께 만드는 “어떤 후보가 경쟁하는가” 규칙. 철학 전개: [`docs/workflow_philosophy.md`](docs/workflow_philosophy.md).

## Docs

| 문서 | 내용 |
|------|------|
| [docs/PRD.md](docs/PRD.md) | 요구사항·데이터·추천 원칙 |
| [docs/workflow_ontology.md](docs/workflow_ontology.md) | Workflow meaning 모델·계층·로그 연결 방향 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 구현 파이프라인 (P0–P7) + meaning layer 위치 |
| [docs/README.md](docs/README.md) | `docs/` 인덱스 |
