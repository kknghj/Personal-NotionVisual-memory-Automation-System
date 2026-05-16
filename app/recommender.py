from typing import Any, Optional

from app.data_loader import load_pair_rules
from app.pair_engine import PairRuleEngine
from app.specificity import (
    PERSON_CONTEXT_MODIFIER_TERMS,
    compound_subject_char_mask,
    effective_interface_dominance_for_occurrence,
    first_meaning_occurrence_index,
    iter_meaning_entries,
    meaning_has_noncompound_occurrence,
    title_contains_interface_anchor,
    title_has_document_workflow_signal,
    _canonical_title_text,
)

SALARY_SYSTEM_CANDIDATE_ID = "salary_system"

DOCUMENT_WORKFLOW_LOCAL_COMPARE_IDS = frozenset({"document_edit", "document_review"})

_pair_engine: PairRuleEngine | None = None


def _get_pair_engine() -> PairRuleEngine:
    global _pair_engine
    if _pair_engine is None:
        _pair_engine = PairRuleEngine(load_pair_rules())
    return _pair_engine


def find_exact_title_match(title: str, cases: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    key = title.strip()
    for case in cases:
        if case.get("title", "").strip() == key:
            return case
    return None


def _local_meaning_better(
    cand: tuple[int, int, int, int, str],
    best: tuple[int, int, int, int, str],
    candidate_id: str,
) -> bool:
    """interface_dominance → specificity → 위치 → 길이 (후보 내부)."""
    dom, spec, pos, ln, _t = cand
    bdom, bspec, bpos, bln, _bt = best
    if dom != bdom:
        return dom > bdom
    if spec != bspec:
        return spec > bspec
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
    canonical: str,
    cov: list[bool],
) -> Optional[tuple[int, int, int, int, str]]:
    """
    compound subject 밖(+ embedded 어근 오른쪽 glue 없음)에서만 meaning 매칭.
    """
    prefer_last = candidate_id in DOCUMENT_WORKFLOW_LOCAL_COMPARE_IDS
    matches: list[tuple[int, int, int, int, str]] = []
    for text, spec, dom in iter_meaning_entries(meanings):
        if not meaning_has_noncompound_occurrence(canonical, text, cov):
            continue
        pos = first_meaning_occurrence_index(canonical, text, cov, prefer_last)
        if pos >= 10**9:
            continue
        dom_e = effective_interface_dominance_for_occurrence(canonical, text, dom, pos, cov)
        ln = len(text.strip())
        matches.append((dom_e, spec, pos, ln, text))

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
    정렬: rule_tier → sort_secondary_wp(legacy workflow_priority tie) → interface_dominance
    → specificity → 제목 위치 → 키워드 길이 → candidate_id

    pair rule hits use rule_tier from pair_rules.json; meaning-only rows use rule_tier=0.
    Returned workflow_priority int is data[\"workflow_priority\"] (PRD anchor strength),
    not the legacy sort boost.

    compound subject 내부 substring은 매칭·interface dominance에서 제외.
    """
    key_title = title.strip()
    canonical = _canonical_title_text(key_title)
    cov = compound_subject_char_mask(canonical)
    title_has_ui = title_contains_interface_anchor(key_title)
    title_has_doc_wf = title_has_document_workflow_signal(key_title)
    rows: list[tuple[int, int, int, int, int, int, str, str, dict[str, Any]]] = []

    for pr in _get_pair_engine().iter_matches(canonical, candidates):
        rows.append(
            (
                pr.rule_tier,
                pr.sort_secondary_wp,
                pr.interface_dominance_effective,
                pr.keyword_specificity,
                0,
                len(pr.matched),
                pr.matched,
                pr.candidate_id,
                pr.data,
            )
        )

    for cid, data in candidates.items():
        if cid == "meta" or not isinstance(data, dict):
            continue
        if "workflow_priority" not in data:
            continue
        if cid == SALARY_SYSTEM_CANDIDATE_ID and title_has_doc_wf:
            continue

        meanings = data.get("meaning")
        best_local = _pick_best_meaning_for_candidate(
            meanings, key_title, title_has_ui, cid, canonical, cov
        )
        if best_local is None:
            continue

        dom_e, spec, pos, ln, matched = best_local
        wp_raw = data.get("workflow_priority", 0)
        try:
            sort_wp = int(wp_raw)
        except (TypeError, ValueError):
            sort_wp = 0

        rows.append(
            (
                0,
                sort_wp,
                dom_e,
                spec,
                pos,
                ln,
                matched,
                cid,
                data,
            )
        )

    if not rows:
        return None

    def _pos_key_row(
        r: tuple[int, int, int, int, int, int, str, str, dict[str, Any]],
    ) -> int:
        _rt, _swp, dom_e, spec, pos, _ln, _matched, cid, _data = r
        if cid in DOCUMENT_WORKFLOW_LOCAL_COMPARE_IDS and dom_e == 0 and spec <= 1:
            return -pos
        return pos

    rows.sort(key=lambda r: (-r[0], -r[1], -r[2], -r[3], _pos_key_row(r), -r[5], r[7]))
    _rt, _swp, dom_e, spec, _pos, _ln, matched, cid, data = rows[0]
    wp_out_raw = data.get("workflow_priority", 0)
    try:
        wp_out = int(wp_out_raw)
    except (TypeError, ValueError):
        wp_out = 0
    return (data, cid, matched, wp_out, spec, dom_e)
