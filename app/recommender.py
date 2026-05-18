from typing import Any, NamedTuple, Optional

from app.candidate_row import CandidateRow
from app.data_loader import load_pair_rules
from app.pair_engine import PairResolution, PairRuleEngine
from app.workflow_resolution import (
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


class BestVisualCandidateMatch(NamedTuple):
    """P7 input slice: winning catalog entry plus debug sort dimensions (tuple-compatible).

    ``workflow_priority`` mirrors ``data[\"workflow_priority\"]`` (catalog anchor strength; ARCH §8),
    not the pair-rule ``sort_secondary_wp`` slot.
    """

    data: dict[str, Any]
    candidate_id: str
    matched: str
    workflow_priority: int
    keyword_workflow_resolution: int
    interface_dominance_effective: int


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


def _candidate_row_from_pair_resolution(pr: PairResolution) -> CandidateRow:
    return CandidateRow(
        rule_tier=pr.rule_tier,
        sort_secondary_wp=pr.sort_secondary_wp,
        interface_dominance_effective=pr.interface_dominance_effective,
        keyword_workflow_resolution=pr.keyword_workflow_resolution,
        match_position_in_title=0,
        matched_keyword_length=len(pr.matched),
        matched=pr.matched,
        candidate_id=pr.candidate_id,
        data=pr.data,
    )


def _local_meaning_better(
    cand: tuple[int, int, int, int, str],
    best: tuple[int, int, int, int, str],
    candidate_id: str,
) -> bool:
    """interface_dominance → workflow_resolution → 위치 → 길이 (후보 내부)."""
    dom, resolution, pos, ln, _t = cand
    bdom, bresolution, bpos, bln, _bt = best
    if dom != bdom:
        return dom > bdom
    if resolution != bresolution:
        return resolution > bresolution
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
    for text, resolution, dom in iter_meaning_entries(meanings):
        if not meaning_has_noncompound_occurrence(canonical, text, cov):
            continue
        pos = first_meaning_occurrence_index(canonical, text, cov, prefer_last)
        if pos >= 10**9:
            continue
        dom_e = effective_interface_dominance_for_occurrence(canonical, text, dom, pos, cov)
        ln = len(text.strip())
        matches.append((dom_e, resolution, pos, ln, text))

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
) -> Optional[BestVisualCandidateMatch]:
    """
    P6 sort (see docs/ARCHITECTURE.md §8.3): ``rule_tier`` first, then branch on UI anchor.

    - **No UI anchor in title**: ``-rule_tier`` → ``-sort_secondary_wp`` → ``-interface_dominance_effective``
      → ``-keyword_workflow_resolution`` → position / length / ``candidate_id``.
    - **UI anchor present**: ``-rule_tier`` → dominance & workflow_resolution **before**
      ``-sort_secondary_wp`` so channel/tool beats catalog anchor-strength noise.

    ``CandidateRow.sort_secondary_wp`` is one **integer slot** for P6: meaning rows load it from
    ``data[\"workflow_priority\"]`` (catalog anchor strength); pair rows load ``sort_secondary_wp``
    from ``pair_rules.json`` (rule tie-break only — different semantic contract).

    ``BestVisualCandidateMatch.workflow_priority`` echoes **catalog** ``data[\"workflow_priority\"]``
    for API/debug (pair synthetic rows still carry ``workflow_priority`` inside ``data`` when set).

    compound subject 내부 substring은 매칭·interface dominance에서 제외.
    """
    key_title = title.strip()
    canonical = _canonical_title_text(key_title)
    cov = compound_subject_char_mask(canonical)
    title_has_ui = title_contains_interface_anchor(key_title)
    title_has_doc_wf = title_has_document_workflow_signal(key_title)
    rows: list[CandidateRow] = []

    for pr in _get_pair_engine().iter_matches(canonical, candidates):
        rows.append(_candidate_row_from_pair_resolution(pr))

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

        dom_e, resolution, pos, ln, matched = best_local
        if title_has_ui and matched.strip() in PERSON_CONTEXT_MODIFIER_TERMS:
            # 인터페이스 앵커가 있을 때 직책·상대만으로는 채널 후보를 대표하지 않음
            continue
        wp_raw = data.get("workflow_priority", 0)
        try:
            sort_wp = int(wp_raw)
        except (TypeError, ValueError):
            sort_wp = 0

        rows.append(
            CandidateRow(
                rule_tier=0,
                sort_secondary_wp=sort_wp,
                interface_dominance_effective=dom_e,
                keyword_workflow_resolution=resolution,
                match_position_in_title=pos,
                matched_keyword_length=ln,
                matched=matched,
                candidate_id=cid,
                data=data,
            )
        )

    if not rows:
        return None

    def _pos_key_row(r: CandidateRow) -> int:
        if (
            r.candidate_id in DOCUMENT_WORKFLOW_LOCAL_COMPARE_IDS
            and r.interface_dominance_effective == 0
            and r.keyword_workflow_resolution <= 1
        ):
            return -r.match_position_in_title
        return r.match_position_in_title

    def _row_sort_key(r: CandidateRow) -> tuple[int, int, int, int, int, int, str]:
        """P6 key; UI title reorders dominance/workflow_resolution vs ``sort_secondary_wp`` (see module docstring)."""
        if title_has_ui:
            return (
                -r.rule_tier,
                -r.interface_dominance_effective,
                -r.keyword_workflow_resolution,
                -r.sort_secondary_wp,
                _pos_key_row(r),
                -r.matched_keyword_length,
                r.candidate_id,
            )
        return (
            -r.rule_tier,
            -r.sort_secondary_wp,
            -r.interface_dominance_effective,
            -r.keyword_workflow_resolution,
            _pos_key_row(r),
            -r.matched_keyword_length,
            r.candidate_id,
        )

    rows.sort(key=_row_sort_key)
    best = rows[0]
    wp_out_raw = best.data.get("workflow_priority", 0)
    try:
        wp_out = int(wp_out_raw)
    except (TypeError, ValueError):
        wp_out = 0
    return BestVisualCandidateMatch(
        data=best.data,
        candidate_id=best.candidate_id,
        matched=best.matched,
        workflow_priority=wp_out,
        keyword_workflow_resolution=best.keyword_workflow_resolution,
        interface_dominance_effective=best.interface_dominance_effective,
    )
