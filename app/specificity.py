"""meaning·제목의 workflow/interface 구체성(specificity) 추론.

1 = 일반 행동·포괄 표현
2 = 업무 개념·중간 행동 (도구명까지는 아닌 카테고리·분기점)
3 = 인터페이스·도구·채널·workflow anchor (실제 UI/연락 채널 기억)
"""

from __future__ import annotations

from typing import Any, Iterator

# 실제 인터페이스 / 도구 / 채널 (specificity=3, interface dominance=1)
INTERFACE_ANCHOR_TERMS: frozenset[str] = frozenset(
    {
        "엑셀",
        "메일",
        "QR",
        "네이버폼",
        "전화",
        "카카오톡",
        "카톡",
        "Cursor",
        "VSCode",
        "CLI",
        "터미널",
        "스프레드시트",
    }
)

# 업무 개념·중간 행동 (specificity=2) — HIGH에서 내려온 포괄 개념 등
MID_SPECIFICITY_TERMS: frozenset[str] = frozenset(
    {
        "개발",
        "구현",
        "자동화",
        "행정처리",
        "교육",
        "현장",
        "수업",
        "API",
        "코딩",
        "환경구축",
        "외부시스템",
        "토탈서비스",
        "행정신청",
        "업무택시",
        "PC",
        "전산",
        "명령어",
        "문의",
    }
)

# 일반 행동·포괄 표현 (specificity=1)
LOW_SPECIFICITY_TERMS: frozenset[str] = frozenset(
    {
        "정리",
        "작성",
        "확인",
        "검토",
        "보고",
        "연락",
        "협의",
        "발송",
        "전달",
        "안내",
        "공지",
        "기입",
        "수정",
        "열람",
        "조사",
        "승인",
        "기안",
        "생각",
        "구상",
        "아이디어",
        "대면",
        "면담",
        "회의",
        "간담회",
        "보호",
        "잠금",
        "식사",
        "오찬",
        "식당",
        "회식",
        "이동",
        "교통",
        "물품",
        "비품",
        "재물",
        "바인더",
        "법령집",
        "자료집",
        "안내사항",
        "주의",
        "긴급",
        "마감",
        "기한",
        "일정관리",
        "접수",
        "응답",
        "체크",
        "설문",
        "표",
        "테이블",
        "데이터정리",
        "실행",
        "세팅",
        "브레인스토밍",
        "통화",
        "채팅",
        "메신저",
        "강사",
        "점심",
        "점심약속",
        "저녁",
        "저녁약속",
        "인증",
        "출퇴근",
        "시스템",
    }
)

# 급여·정산 subject (salary_system 후보 meaning과 맞춤; 문서 workflow가 있으면 후순위)
SALARY_SUBJECT_TERMS: frozenset[str] = frozenset(
    {
        "수당",
        "급여",
        "성과급",
        "복리",
        "여비",
        "정산",
        "출장비",
    }
)

# 보고서·회의자료 등 — meaning「보고」「회의」가 명사 안에만 들어간 매칭을 막기 위한 subject compound
# 검토보고서: 명사 접두 「검토」와 동사 「검토」 분리(검토보고서 작성 → 작성)
DOCUMENT_COMPOUND_SUBJECT_TERMS: frozenset[str] = frozenset(
    {
        "출장보고서",
        "결과보고서",
        "검토보고서",
        "보고자료",
        "보고서",
        "회의자료",
        "계획안",
        "기안문",
    }
)

# 공문·보고 등 실제 문서 처리 workflow가 제목에 있으면 subject(급여/수당…)보다 우선
DOCUMENT_WORKFLOW_SIGNAL_TERMS: frozenset[str] = frozenset(
    {
        "보고자료",
        "보고서",
        "회의자료",
        "계획안",
        "기안문",
        "결과보고서",
        "검토보고서",
        "출장보고서",
        "공문",
        "작성",
        "수정",
        "송부",
        "요청",
        "기안",
        "제출",
        "검토",
        "확인",
    }
)


def _sorted_terms(terms: frozenset[str]) -> tuple[str, ...]:
    """긴 토큰을 먼저 검사해 짧은 부분 문자열 오매칭을 줄인다."""
    return tuple(sorted(terms, key=len, reverse=True))


_INTERFACE_SORTED = _sorted_terms(INTERFACE_ANCHOR_TERMS)
_MID_SORTED = _sorted_terms(MID_SPECIFICITY_TERMS)
_LOW_SORTED = _sorted_terms(LOW_SPECIFICITY_TERMS)
_DOCUMENT_WORKFLOW_SIGNAL_SORTED = _sorted_terms(DOCUMENT_WORKFLOW_SIGNAL_TERMS)
DOCUMENT_COMPOUND_SUBJECT_SORTED = _sorted_terms(DOCUMENT_COMPOUND_SUBJECT_TERMS)

# 직책·상대 역할 — 제목에 인터페이스 앵커가 있으면 이 키워드만으로는 후보를 대표하지 않음(modifier)
PERSON_CONTEXT_MODIFIER_TERMS: frozenset[str] = frozenset(
    {
        "과장님",
        "대표",
        "팀장",
        "팀장님",
        "상사",
        "부장",
        "부장님",
        "차장",
        "차장님",
        "국장",
        "국장님",
        "사장",
        "원장",
        "교장",
        "이사",
    }
)


def title_contains_interface_anchor(title: str) -> bool:
    """제목에 INTERFACE anchor 부분문자열이 하나라도 있으면 True."""
    t = title.strip()
    if not t:
        return False
    return any(a and a in t for a in _INTERFACE_SORTED)


def title_has_document_workflow_signal(title: str) -> bool:
    """공문·보고·작성·검토 등 문서 처리 workflow가 제목에 있으면 True (급여 subject보다 우선)."""
    t = title.strip()
    if not t:
        return False
    return any(sig and sig in t for sig in _DOCUMENT_WORKFLOW_SIGNAL_SORTED)


def interface_dominance(text: str) -> int:
    """제목·키워드에 인터페이스 anchor가 부분 문자열로 들어가면 1, 아니면 0."""
    t = text.strip()
    if not t:
        return 0
    return 1 if any(a and a in t for a in _INTERFACE_SORTED) else 0


def infer_specificity(text: str) -> int:
    """substring 우선: anchor ⊂ t → 3, MID ⊂ t → 2, LOW ⊂ t → 1, 그 외 2."""
    t = text.strip()
    if not t:
        return 1
    if any(a and a in t for a in _INTERFACE_SORTED):
        return 3
    if any(m and m in t for m in _MID_SORTED):
        return 2
    if any(low and low in t for low in _LOW_SORTED):
        return 1
    return 2


def iter_meaning_entries(meanings: Any) -> Iterator[tuple[str, int, int]]:
    """각 meaning에 대해 (text, specificity, interface_dominance)."""
    if not isinstance(meanings, list):
        yield from ()
        return
    for item in meanings:
        if isinstance(item, str):
            s = item.strip()
            if s:
                sp = infer_specificity(s)
                yield s, sp, interface_dominance(s)
            continue
        if isinstance(item, dict):
            raw = item.get("text") or item.get("term") or item.get("value")
            if not isinstance(raw, str):
                continue
            s = raw.strip()
            if not s:
                continue
            sp_override = item.get("specificity")
            if sp_override is None:
                sp = infer_specificity(s)
            else:
                try:
                    sp = int(sp_override)
                except (TypeError, ValueError):
                    sp = infer_specificity(s)
            dom_o = item.get("interface_dominance")
            if dom_o is None:
                dom = interface_dominance(s)
            else:
                try:
                    dom = int(dom_o)
                except (TypeError, ValueError):
                    dom = interface_dominance(s)
            yield s, sp, dom


def workflow_specificity_for_sample_case(case: dict[str, Any]) -> int:
    """sample_cases 한 건에 붙일 대표 specificity (메타·학습 신호용)."""
    title = str(case.get("title", ""))
    focus = str(case.get("focus", ""))
    mem = case.get("interface_memory") or []
    mem_s = " ".join(m for m in mem if isinstance(m, str))
    blob = f"{title} {focus} {mem_s}"

    if any(a and a in blob for a in _INTERFACE_SORTED):
        return 3

    low_hits = sum(1 for lt in _LOW_SORTED if len(lt) >= 2 and lt in blob)
    if low_hits >= 2 and not any(
        a in blob for a in ("급여시스템", "네이버", "엑셀", "메일", "QR", "카카오", "카톡", "전화", "VSCode", "Cursor", "CLI", "터미널")
    ):
        return 1

    return 2
