from typing import Any, Optional

from app.specificity import (
    DOCUMENT_COMPOUND_SUBJECT_SORTED,
    PERSON_CONTEXT_MODIFIER_TERMS,
    iter_meaning_entries,
    title_contains_interface_anchor,
    title_has_document_workflow_signal,
)

SALARY_SYSTEM_CANDIDATE_ID = "salary_system"

# 같은 후보 안에서 뒤쪽 행동 키워드(작성·검토 등)를 우선 — compound subject 뒤의 동사
DOCUMENT_WORKFLOW_LOCAL_COMPARE_IDS = frozenset({"document_edit", "document_review"})


def find_exact_title_match(title: str, cases: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    key = title.strip()
    for case in cases:
        if case.get("title", "").strip() == key:
            return case
    return None


def _canonical_title(title: str) -> str:
    return "".join(title.strip().split())


def _compound_subject_spans(canonical: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for w in DOCUMENT_COMPOUND_SUBJECT_SORTED:
        if not w or w not in canonical:
            continue
        start = 0
        while True:
            j = canonical.find(w, start)
            if j < 0:
                break
            spans.append((j, j + len(w)))
            start = j + 1
    return spans


def _interval_inside_any_span(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    for a, b in spans:
        if start >= a and end <= b:
            return True
    return False


def _meaning_occurrence_starts(canonical: str, phrase: str) -> list[int]:
    p = phrase.strip()
    if not p:
        return []
    out: list[int] = []
    start = 0
    while True:
        j = canonical.find(p, start)
        if j < 0:
            break
        out.append(j)
        start = j + max(1, len(p))
    return out


def _meaning_allowed_in_title_for_workflow(title: str, phrase: str) -> bool:
    """
    공백을 무시한 제목에서 meaning이 등장하는지.
    보고서·회의자료 등 compound subject 구간 안에만 걸린 부분 문자열(보고, 회의, 기안, 검토 등)은 무시.
    """
    canonical = _canonical_title(title)
    p = phrase.strip()
    if not p or p not in canonical:
        return False
    spans = _compound_subject_spans(canonical)
    for j in _meaning_occurrence_starts(canonical, p):
        if not _interval_inside_any_span(j, j + len(p), spans):
            return True
    return False


def _match_index_for_meaning(title: str, matched: str, candidate_id: str) -> int:
    """정렬·비교용 인덱스. document_edit/review는 compound 밖 occurrence 중 가장 뒤(실제 행동) 우선."""
    canonical = _canonical_title(title)
    m = matched.strip()
    if not m:
        return 10**9
    spans = _compound_subject_spans(canonical)
    valid = [
        j
        for j in _meaning_occurrence_starts(canonical, m)
        if not _interval_inside_any_span(j, j + len(m), spans)
    ]
    if not valid:
        return 10**9
    if candidate_id in DOCUMENT_WORKFLOW_LOCAL_COMPARE_IDS:
        return max(valid)
    return min(valid)


def _local_meaning_better(
    cand: tuple[int, int, int, int, str],
    best: tuple[int, int, int, int, str],
    candidate_id: str,
) -> bool:
    """같은 후보 안: specificity ↑, interface_dominance ↑, 위치(문서 후보는 뒤쪽 우선), 길이 ↑."""
    spec, dom, pos, ln, _t = cand
    bspec, bdom, bpos, bln, _bt = best
    if spec != bspec:
        return spec > bspec
    if dom != bdom:
        return dom > bdom
    if candidate_id in DOCUMENT_WORKFLOW_LOCAL_COMPARE_IDS:
        if pos != bpos:
            return pos > bpos
    else:
        if pos != bpos:
            return pos < bpos
    if ln != bln:
        return ln > bln
    return False


def _pick_best_meaning_for_candidate(
    meanings: Any,
    key_title: str,
    title_has_interface: bool,
    candidate_id: str,
) -> Optional[tuple[int, int, int, int, str]]:
    """
    제목에 맞는 meaning 중 하나를 고른다.
    제목에 인터페이스 앵커가 있으면 person modifier meaning만으로는 대표하지 않는다.
    """
    matches: list[tuple[int, int, int, int, str]] = []
    for text, spec, dom in iter_meaning_entries(meanings):
        if not _meaning_allowed_in_title_for_workflow(key_title, text):
            continue
        pos = _match_index_for_meaning(key_title, text, candidate_id)
        if pos >= 10**9:
            continue
        ln = len(text.strip())
        matches.append((spec, dom, pos, ln, text))

    if not matches:
        return None

    pool = matches
    if title_has_interface:
        non_person = [m for m in matches if m[4].strip() not in PERSON_CONTEXT_MODIFIER_TERMS]
        if non_person:
            pool = non_person

    best = pool[0]
    for m in pool[1:]:
        if _local_meaning_better(m, best, candidate_id):
            best = m
    return best


def find_best_visual_candidate_match(
    title: str,
    candidates: dict[str, Any],
) -> Optional[tuple[dict[str, Any], str, str, int, int, int]]:
    """
    meaning 키워드가 제목에 포함된 후보 중 정렬:
    1) interface dominance
    2) keyword specificity
    3) workflow_priority
    4) 제목에서의 등장 위치
    5) 키워드 길이
    6) candidate_id

    compound subject(보고서·회의자료 등) 안의 「보고」「회의」만으로는 매칭하지 않으며,
    document_edit/document_review는 compound 뒤쪽의 행동 키워드를 우선한다.
    """
    key_title = title.strip()
    title_has_ui = title_contains_interface_anchor(key_title)
    title_has_doc_wf = title_has_document_workflow_signal(key_title)
    rows: list[tuple[int, int, int, int, int, str, str, dict[str, Any]]] = []

    for cid, data in candidates.items():
        if cid == "meta" or not isinstance(data, dict):
            continue
        if "workflow_priority" not in data:
            continue
        if cid == SALARY_SYSTEM_CANDIDATE_ID and title_has_doc_wf:
            continue

        meanings = data.get("meaning")
        best_local = _pick_best_meaning_for_candidate(meanings, key_title, title_has_ui, cid)
        if best_local is None:
            continue

        spec, dom, pos, ln, matched = best_local
        wp_raw = data.get("workflow_priority", 0)
        try:
            wp = int(wp_raw)
        except (TypeError, ValueError):
            wp = 0

        rows.append((dom, spec, wp, pos, ln, matched, cid, data))

    if not rows:
        return None

    def _pos_sort_component(r: tuple[int, int, int, int, int, str, str, dict[str, Any]]) -> int:
        dom, spec, wp, pos, ln, matched, cid, data = r
        if cid in DOCUMENT_WORKFLOW_LOCAL_COMPARE_IDS and dom == 0 and spec <= 1:
            return -pos
        return pos

    rows.sort(key=lambda r: (-r[0], -r[1], -r[2], _pos_sort_component(r), -r[4], r[6]))
    dom, spec, wp, _pos, _ln, matched, cid, data = rows[0]
    return (data, cid, matched, wp, spec, dom)
