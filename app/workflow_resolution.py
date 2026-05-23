"""meaning·제목의 workflow/interface 해상도(workflow_resolution) 추론.

workflow_resolution은 제목이 얼마나 구체적인 workflow/interface anchor를
포함하는지를 나타낸다. 실제 인터페이스 anchor가 많을수록 resolution이 높다.

**LOW (1)** — 일반 행동·포괄 표현. 특정 도구/채널 없이 “무엇을 하는지”만 말할 때.
예: 확인, 검토, 작성, 정리, 협의. 장비 일반명(예: PC)도 여기: workflow 분기보다
배경 명사에 가깝다.

**MID (2)** — 업무 category·workflow branch·처리 흐름의 중간 개념.
구체 제품명·UI는 아니지만, 이후 단계에서 어떤 계열(통신·인증·전산 등)로 갈지
가르치는 신호가 LOW보다 강할 때.
예: 인증, 메신저, 설문, 자동화, API, 전산, 통화(매체 구분 전의 통화 개념).

**HIGH (3)** — 실제 인터페이스·도구·연락 채널·사용자가 떠올릴 수 있는 UI anchor.
예: 엑셀, 메일, 카톡, QR, CLI, VSCode, 터미널, 전화(통화 매체로서의 채널).
"""

from __future__ import annotations

from typing import Any, Iterator

# HIGH(3): 구체 제품·채널·UI — substring이면 interface_dominance=1, workflow_resolution=3.
# ("전화"는 통화 채널 앵커; "통화" 단어는 MID에서 ‘통화 매체 미정’ 분기로 둔다.)
INTERFACE_ANCHOR_TERMS: frozenset[str] = frozenset(
    {
        "엑셀",
        "메일",
        "QR",
        "네이버폼",
        "전화",
        "카카오톡",
        "카톡",
        "슬랙",
        "Cursor",
        "VSCode",
        "CLI",
        "터미널",
        "스프레드시트",
        "앱",
    }
)

# MID(2): 도구명은 아니지만 업무 계열·workflow 분기 신호가 LOW보다 뚜렷할 때.
MID_WORKFLOW_RESOLUTION_TERMS: frozenset[str] = frozenset(
    {
        # 개발·전산·자동화 계열
        "개발",
        "구현",
        "자동화",
        "API",
        "코딩",
        "환경구축",
        "전산",
        "명령어",
        # 행정·현장·교육 등 업무 무대
        "행정처리",
        "현장",
        "수업",
        "외부시스템",
        "토탈서비스",
        "행정신청",
        "업무택시",
        # 커뮤니케이션·채널 카테고리(슬랙/카톡 등 구체 앱은 HIGH)
        "메신저",
        "채팅",
        "통화",
        # 인증·시스템·수집·표 구조 — 이후 전자결재/근태/폼·스프레드시트 등으로 갈림
        "인증",
        "시스템",
        "설문",
        "테이블",
        "배포",
        "배부",
        "공유",
        "게시",
        "공개",
        "상신",
        "브리핑",
        "요청",
        "부탁",
        "회신",
        "결재요청",
        "결재받기",
        "승인요청",
        "승인검토",
        "결재하기",
        "최종승인",
        "현황",
        "진행상황",
        "배정",
        "집행",
        "모니터링",
        "추적",
        "조율",
        "일정조율",
        "시간협의",
    }
)

# LOW(1): 일반 동사·포괄 표현·배경 명사. MID만큼의 ‘어느 계열 업무인가’ 분기력은 없을 때.
# "문의"는 행동(문의하기)에 가깝고 채널 미지정이 많아 MID보다 LOW에 둠(제목에 메일·전화 등
# HIGH가 있으면 infer는 3이 됨).
LOW_WORKFLOW_RESOLUTION_TERMS: frozenset[str] = frozenset(
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
        "표",
        "데이터정리",
        "실행",
        "세팅",
        "브레인스토밍",
        "강사",
        "점심",
        "점심약속",
        "저녁",
        "저녁약속",
        "출퇴근",
        # 일반 명사: 특정 시스템·UI 분기보다 ‘장비/매체’ 배경
        "PC",
        "문의",
        "설명",
        "공고",
        "노출",
        "등록",
        "결재",
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

# 문서·행정 subject compound — 내부 substring(교육, 보고, 회의, 신청 등)은 workflow anchor·dominance 대상이 아님
DOCUMENT_COMPOUND_SUBJECT_TERMS: frozenset[str] = frozenset(
    {
        # 교육·교육청 계열
        "교육청",
        "교육자료",
        "교육계획",
        "교육예산",
        "교육지원",
        "교육신청서",
        # 보고·발표 계열
        "출장보고서",
        "결과보고서",
        "검토보고서",
        "면접자료",
        "발표자료",
        "보고자료",
        "보고서",
        # 회의 계열
        "회의자료",
        "회의록",
        "회의안건",
        # 계획 계열
        "계획안",
        "계획서",
        "운영계획",
        # 협의 계열
        "협의회",
        "협의안",
        "협의자료",
        "협의결과",
        # 검토·확인 계열
        "검토자료",
        "검토결과",
        "검토의견",
        "확인서",
        "확인자료",
        "사실확인서",
        # 신청 계열
        "신청서",
        "신청현황",
        "신청내역",
        "신청페이지",
        # 조사 계열
        "조사표",
        "조사결과",
        "실태조사",
        "만족도조사",
        # 분석 계열
        "분석자료",
        "분석결과",
        # 운영·지원·등록·승인 계열
        "운영현황",
        "운영예산",
        "지원사업",
        "지원예산",
        "지원현황",
        "등록부",
        "등록현황",
        "등록내역",
        "승인요청서",
        "승인내역",
        "승인현황",
        # 기안
        "기안문",
        # 게시·공고 계열 object/context: 내부 action-like substring만으로 publication으로 보지 않음
        "공고번호",
        "게시판",
    }
)

# 공문·보고 등 문서 처리 신호 + subject compound(급여 subject 후순위 판단에 사용)
DOCUMENT_WORKFLOW_SIGNAL_TERMS: frozenset[str] = frozenset(
    {
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
) | DOCUMENT_COMPOUND_SUBJECT_TERMS


def _sorted_terms(terms: frozenset[str]) -> tuple[str, ...]:
    """긴 토큰을 먼저 검사해 짧은 부분 문자열 오매칭을 줄인다."""
    return tuple(sorted(terms, key=len, reverse=True))


_INTERFACE_SORTED = _sorted_terms(INTERFACE_ANCHOR_TERMS)
_MID_RESOLUTION_SORTED = _sorted_terms(MID_WORKFLOW_RESOLUTION_TERMS)
_LOW_RESOLUTION_SORTED = _sorted_terms(LOW_WORKFLOW_RESOLUTION_TERMS)
_DOCUMENT_WORKFLOW_SIGNAL_SORTED = _sorted_terms(DOCUMENT_WORKFLOW_SIGNAL_TERMS)
DOCUMENT_COMPOUND_SUBJECT_SORTED = _sorted_terms(DOCUMENT_COMPOUND_SUBJECT_TERMS)


def _canonical_title_text(title: str) -> str:
    return "".join(title.strip().split())


def compound_subject_char_mask(canonical: str) -> list[bool]:
    """compound subject 명사에 덮인 글자는 True."""
    n = len(canonical)
    cov = [False] * n
    for w in DOCUMENT_COMPOUND_SUBJECT_SORTED:
        if not w:
            continue
        start = 0
        while True:
            j = canonical.find(w, start)
            if j < 0:
                break
            for k in range(j, min(j + len(w), n)):
                cov[k] = True
            start = j + 1
    return cov


def _substring_starts(text: str, needle: str) -> list[int]:
    if not needle:
        return []
    out: list[int] = []
    start = 0
    while True:
        j = text.find(needle, start)
        if j < 0:
            break
        out.append(j)
        start = j + max(1, len(needle))
    return out


def _occurrence_hits_compound(cov: list[bool], start: int, length: int) -> bool:
    if start < 0 or length <= 0 or start + length > len(cov):
        return True
    return any(cov[start + k] for k in range(length))


def _occurrence_is_fully_compound(cov: list[bool], start: int, length: int) -> bool:
    if start < 0 or length <= 0 or start + length > len(cov):
        return True
    return all(cov[start + k] for k in range(length))


def meaning_has_noncompound_occurrence(canonical: str, phrase: str, cov: list[bool]) -> bool:
    """compound subject 내부 substring은 막고, 명시적 object+action phrase는 허용한다."""
    p = phrase.strip()
    if not p or p not in canonical:
        return False
    for j in _substring_starts(canonical, p):
        if _occurrence_hits_compound(cov, j, len(p)) and _occurrence_is_fully_compound(
            cov, j, len(p)
        ):
            continue
        return True
    return False


def organize_subject_term_occurrence_ok(canonical: str, term: str, cov: list[bool]) -> bool:
    """organize (정리) subject: compound 내부의 *부분* 매칭만 막고, 복합어 전체가 subject이면 허용.

    예: ``회의자료`` 안의 ``자료``는 거부, 단독 ``보고서``+``정리``는 ``보고서``가 복합 사전 항목이어도 허용.
    """
    p = term.strip()
    if not p or p not in canonical:
        return False
    for j in _substring_starts(canonical, p):
        L = len(p)
        if not _occurrence_hits_compound(cov, j, L):
            return True
        inner_of_longer = False
        for w in DOCUMENT_COMPOUND_SUBJECT_SORTED:
            if not w or len(w) <= L:
                continue
            for s in _substring_starts(canonical, w):
                if s <= j and j + L <= s + len(w) and (s < j or j + L < s + len(w)):
                    inner_of_longer = True
                    break
            if inner_of_longer:
                break
        if inner_of_longer:
            continue
        if canonical[j : j + L] == p:
            return True
    return False


def first_meaning_occurrence_index(canonical: str, phrase: str, cov: list[bool], prefer_last: bool) -> int:
    """compound 밖 occurrence 인덱스. 없으면 10**9."""
    p = phrase.strip()
    if not p:
        return 10**9
    valid: list[int] = []
    for j in _substring_starts(canonical, p):
        if _occurrence_hits_compound(cov, j, len(p)) and _occurrence_is_fully_compound(
            cov, j, len(p)
        ):
            continue
        valid.append(j)
    if not valid:
        return 10**9
    return max(valid) if prefer_last else min(valid)


def effective_interface_dominance_for_occurrence(
    canonical: str,
    matched: str,
    raw_dom: int,
    occ_index: int,
    cov: list[bool],
) -> int:
    """compound 밖·독립 occurrence일 때만 interface dominance 유지(내부 substring은 dominance 0)."""
    if raw_dom <= 0:
        return 0
    L = len(matched.strip())
    if occ_index >= 10**9 or _occurrence_hits_compound(cov, occ_index, L):
        return 0
    return raw_dom


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
        "시장님",
    }
)


def canonical_has_interface_anchor_noncompound(canonical: str) -> bool:
    """이미 canonical(공백 제거)일 때: INTERFACE anchor가 compound 밖에 있으면 True."""
    if not canonical:
        return False
    cov = compound_subject_char_mask(canonical)
    for a in _INTERFACE_SORTED:
        if not a or a not in canonical:
            continue
        for j in _substring_starts(canonical, a):
            if _occurrence_hits_compound(cov, j, len(a)):
                continue
            return True
    return False


def title_contains_interface_anchor(title: str) -> bool:
    """제목에 INTERFACE anchor가 있고, compound subject 안에만 있는 매칭은 제외."""
    c = _canonical_title_text(title)
    return canonical_has_interface_anchor_noncompound(c)


def title_has_document_workflow_signal(title: str) -> bool:
    """문서 처리·subject compound 등 신호가 제목에 있으면 True (급여 subject 후순위)."""
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


def infer_workflow_resolution(text: str) -> int:
    """substring 우선: HIGH(3) → MID(2) → LOW(1); 어느 집합에도 없으면 기본 2."""
    t = text.strip()
    if not t:
        return 1
    if any(a and a in t for a in _INTERFACE_SORTED):
        return 3
    if any(m and m in t for m in _MID_RESOLUTION_SORTED):
        return 2
    if any(low and low in t for low in _LOW_RESOLUTION_SORTED):
        return 1
    return 2


def iter_meaning_entries(meanings: Any) -> Iterator[tuple[str, int, int]]:
    """각 meaning에 대해 (text, workflow_resolution, interface_dominance)."""
    if not isinstance(meanings, list):
        yield from ()
        return
    for item in meanings:
        if isinstance(item, str):
            s = item.strip()
            if s:
                resolution = infer_workflow_resolution(s)
                yield s, resolution, interface_dominance(s)
            continue
        if isinstance(item, dict):
            raw = item.get("text") or item.get("term") or item.get("value")
            if not isinstance(raw, str):
                continue
            s = raw.strip()
            if not s:
                continue
            resolution_override = item.get("workflow_resolution")
            if resolution_override is None:
                resolution = infer_workflow_resolution(s)
            else:
                try:
                    resolution = int(resolution_override)
                except (TypeError, ValueError):
                    resolution = infer_workflow_resolution(s)
            dom_o = item.get("interface_dominance")
            if dom_o is None:
                dom = interface_dominance(s)
            else:
                try:
                    dom = int(dom_o)
                except (TypeError, ValueError):
                    dom = interface_dominance(s)
            yield s, resolution, dom


def workflow_resolution_for_sample_case(case: dict[str, Any]) -> int:
    """sample_cases 한 건에 붙일 대표 workflow_resolution (메타·학습 신호용)."""
    title = str(case.get("title", ""))
    focus = str(case.get("focus", ""))
    mem = case.get("interface_memory") or []
    mem_s = " ".join(m for m in mem if isinstance(m, str))
    blob = f"{title} {focus} {mem_s}"

    if any(a and a in blob for a in _INTERFACE_SORTED):
        return 3

    low_hits = sum(1 for lt in _LOW_RESOLUTION_SORTED if len(lt) >= 2 and lt in blob)
    if low_hits >= 2 and not any(
        a in blob for a in ("급여시스템", "네이버", "엑셀", "메일", "QR", "카카오", "카톡", "전화", "VSCode", "Cursor", "CLI", "터미널")
    ):
        return 1

    return 2
