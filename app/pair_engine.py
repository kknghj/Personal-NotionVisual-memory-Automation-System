"""Declarative pair rules (prep, confirm+coordination, organize, modify) evaluated before meaning matching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.workflow_resolution import (
    canonical_has_interface_anchor_noncompound,
    compound_subject_char_mask,
    organize_subject_term_occurrence_ok,
)


@dataclass(frozen=True, slots=True)
class PairResolution:
    """P3 declarative pair rule hit — one resolved (action, subject) interpretation.

    This is **not** a P6 ranking row: it has no title occurrence position or length
    for the unified sort tuple; those are supplied when projecting into
    ``CandidateRow`` (pair rows use position ``0`` and ``len(matched)``).

    Fields (see docs/ARCHITECHURE.md §P3):
    - ``data``: visual_candidates-shaped payload (synthetic or copied from a candidate).
    - ``candidate_id`` / ``matched``: which catalog entry and which literal matched span.
    - ``rule_tier``: global sort boost for pair track vs meaning-only (``rule_tier=0``).
    - ``sort_secondary_wp``: P6 integer read from rule JSON (``sort_secondary_wp`` key);
      **rule tie-break / phase ordering**, not the catalog ``workflow_priority`` 1/2/3 scale
      unless authors intentionally reuse the same numbers.
    - ``keyword_workflow_resolution`` / ``interface_dominance_effective``: same semantics as meaning rows.
    """

    data: dict[str, Any]
    candidate_id: str
    matched: str
    rule_tier: int
    sort_secondary_wp: int
    keyword_workflow_resolution: int
    interface_dominance_effective: int


def _sorted_terms_length_desc(terms: list[str]) -> list[str]:
    return sorted((t for t in terms if isinstance(t, str) and t), key=len, reverse=True)


class PairRuleEngine:
    def __init__(self, rules: dict[str, Any]) -> None:
        self._rules = rules

    def _rule_tier_int(self) -> int:
        tier_raw = self._rules.get("pair_rule_tier", 1)
        try:
            return int(tier_raw)
        except (TypeError, ValueError):
            return 1

    def iter_matches(
        self,
        canonical: str,
        candidates: dict[str, Any],
    ) -> list[PairResolution]:
        """Order: prep → confirm → organize → modify (각 네임스페이스당 최대 1 row)."""
        out: list[PairResolution] = []
        rule_tier = self._rule_tier_int()

        prep = self._rules.get("prep")
        if isinstance(prep, dict):
            r = self._try_prep(canonical, prep, rule_tier)
            if r is not None:
                out.append(r)

        cc = self._rules.get("confirm_coordination")
        if isinstance(cc, dict):
            r = self._try_confirm_coordination(canonical, candidates, cc, rule_tier)
            if r is not None:
                out.append(r)

        org = self._rules.get("organize")
        if isinstance(org, dict):
            r = self._try_organize(canonical, org, rule_tier)
            if r is not None:
                out.append(r)

        mod = self._rules.get("modify")
        if isinstance(mod, dict):
            r = self._try_modify(canonical, mod, rule_tier)
            if r is not None:
                out.append(r)

        return out

    def _try_prep(
        self,
        canonical: str,
        prep: dict[str, Any],
        rule_tier: int,
    ) -> Optional[PairResolution]:
        lemma = prep.get("action_lemma", "준비")
        if not isinstance(lemma, str) or lemma not in canonical:
            return None

        for rule in prep.get("rules", []):
            if not isinstance(rule, dict):
                continue
            rtype = rule.get("type")
            if rtype == "document_subjects":
                res = self._prep_document_subjects(canonical, rule, lemma, rule_tier)
            elif rtype == "subject_match":
                res = self._prep_substring(canonical, rule, lemma, rule_tier)
            elif rtype == "event_setup_resolution":
                res = self._prep_setting_event(canonical, rule, lemma, rule_tier)
            elif rtype == "food_subject_resolution":
                res = self._prep_food_ordered(canonical, rule, lemma, rule_tier)
            elif rtype == "event_subject_resolution":
                res = self._prep_event_tail(canonical, rule, lemma, rule_tier)
            else:
                res = None
            if res is not None:
                return res
        return None

    def _synthetic_prep_data(self, rule: dict[str, Any], visual: dict[str, Any]) -> dict[str, Any]:
        wp_raw = rule.get("workflow_priority", 2)
        try:
            wp = int(wp_raw)
        except (TypeError, ValueError):
            wp = 2
        return {
            "visual": dict(visual) if isinstance(visual, dict) else {"type": "emoji", "value": ""},
            "workflow_priority": wp,
            "meaning": [],
        }

    def _sort_secondary_wp(self, rule: dict[str, Any]) -> int:
        v = rule.get("sort_secondary_wp", 3)
        try:
            return int(v)
        except (TypeError, ValueError):
            return 3

    def _prep_document_subjects(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
    ) -> Optional[PairResolution]:
        terms = rule.get("terms")
        if not isinstance(terms, list):
            return None
        for term in _sorted_terms_length_desc([str(t) for t in terms]):
            if term in canonical:
                tpl = str(rule.get("matched_template", "{term}+{lemma}"))
                matched = tpl.replace("{term}", term).replace("{lemma}", lemma)
                return self._prep_resolution(
                    rule=rule,
                    candidate_id=str(rule.get("candidate_id", "")),
                    matched=matched,
                    data=self._synthetic_prep_data(rule, rule.get("visual", {})),
                    rule_tier=rule_tier,
                )
        return None

    def _prep_substring(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
    ) -> Optional[PairResolution]:
        sub = rule.get("substring")
        if not isinstance(sub, str) or sub not in canonical:
            return None
        matched = str(rule.get("matched_literal", f"{sub}+{lemma}"))
        return self._prep_resolution(
            rule=rule,
            candidate_id=str(rule.get("candidate_id", "")),
            matched=matched,
            data=self._synthetic_prep_data(rule, rule.get("visual", {})),
            rule_tier=rule_tier,
        )

    def _prep_setting_event(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
    ) -> Optional[PairResolution]:
        req = rule.get("require")
        any_of = rule.get("any_of")
        if not isinstance(req, str) or req not in canonical:
            return None
        if not isinstance(any_of, list) or not any(
            isinstance(x, str) and x in canonical for x in any_of
        ):
            return None
        matched = str(rule.get("matched_literal", f"{req}+{lemma}"))
        return self._prep_resolution(
            rule=rule,
            candidate_id=str(rule.get("candidate_id", "")),
            matched=matched,
            data=self._synthetic_prep_data(rule, rule.get("visual", {})),
            rule_tier=rule_tier,
        )

    def _prep_food_ordered(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
    ) -> Optional[PairResolution]:
        rows = rule.get("term_outcomes")
        if not isinstance(rows, list):
            return None
        for row in rows:
            if not isinstance(row, dict):
                continue
            term = row.get("term")
            if not isinstance(term, str) or term not in canonical:
                continue
            emoji = row.get("emoji", "🍰")
            visual = {"type": "emoji", "value": str(emoji)}
            cid = str(row.get("candidate_id", ""))
            matched = f"{term}+{lemma}"
            data = self._synthetic_prep_data(rule, visual)
            return self._prep_resolution_from_parts(
                rule=rule,
                candidate_id=cid,
                matched=matched,
                data=data,
                rule_tier=rule_tier,
            )
        return None

    def _prep_event_tail(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
    ) -> Optional[PairResolution]:
        terms = rule.get("terms_in_order")
        if not isinstance(terms, list):
            return None
        for term in terms:
            if not isinstance(term, str):
                continue
            if term in canonical:
                tpl = rule.get("matched_template", "{term}+준비")
                matched = str(tpl).replace("{term}", term).replace("{lemma}", lemma)
                return self._prep_resolution(
                    rule=rule,
                    candidate_id=str(rule.get("candidate_id", "")),
                    matched=matched,
                    data=self._synthetic_prep_data(rule, rule.get("visual", {})),
                    rule_tier=rule_tier,
                )
        return None

    def _prep_resolution(
        self,
        rule: dict[str, Any],
        candidate_id: str,
        matched: str,
        data: dict[str, Any],
        rule_tier: int,
    ) -> PairResolution:
        return self._prep_resolution_from_parts(rule, candidate_id, matched, data, rule_tier)

    def _prep_resolution_from_parts(
        self,
        rule: dict[str, Any],
        candidate_id: str,
        matched: str,
        data: dict[str, Any],
        rule_tier: int,
    ) -> PairResolution:
        resolution_raw = rule.get("keyword_workflow_resolution", 2)
        dom = rule.get("interface_dominance_effective", 0)
        try:
            resolution = int(resolution_raw)
        except (TypeError, ValueError):
            resolution = 2
        try:
            dom_i = int(dom)
        except (TypeError, ValueError):
            dom_i = 0
        return PairResolution(
            data=data,
            candidate_id=candidate_id,
            matched=matched,
            rule_tier=rule_tier,
            sort_secondary_wp=self._sort_secondary_wp(rule),
            keyword_workflow_resolution=resolution,
            interface_dominance_effective=dom_i,
        )

    def _try_confirm_coordination(
        self,
        canonical: str,
        candidates: dict[str, Any],
        cc: dict[str, Any],
        rule_tier: int,
    ) -> Optional[PairResolution]:
        lemma = cc.get("action_lemma", "확인")
        if not isinstance(lemma, str) or lemma not in canonical:
            return None
        kws = cc.get("coordination_keywords")
        if not isinstance(kws, list) or not any(
            isinstance(k, str) and k in canonical for k in kws
        ):
            return None

        cid = self._resolve_confirm_channel(canonical, cc)
        base = candidates.get(cid)
        if not isinstance(base, dict):
            return None

        data = dict(base)
        matched = str(cc.get("matched_literal", f"{lemma}+coordination"))

        resolution_raw = cc.get("keyword_workflow_resolution", 2)
        dom = cc.get("interface_dominance_effective", 0)
        try:
            resolution = int(resolution_raw)
        except (TypeError, ValueError):
            resolution = 2
        try:
            dom_i = int(dom)
        except (TypeError, ValueError):
            dom_i = 0

        sswp = self._sort_secondary_wp(cc)

        return PairResolution(
            data=data,
            candidate_id=cid,
            matched=matched,
            rule_tier=rule_tier,
            sort_secondary_wp=sswp,
            keyword_workflow_resolution=resolution,
            interface_dominance_effective=dom_i,
        )

    def _resolve_confirm_channel(self, canonical: str, cc: dict[str, Any]) -> str:
        rules = cc.get("channel_rules")
        if isinstance(rules, list):
            for ch in rules:
                if not isinstance(ch, dict):
                    continue
                if_any = ch.get("if_any")
                if not isinstance(if_any, list):
                    continue
                if any(isinstance(x, str) and x in canonical for x in if_any):
                    cid = ch.get("candidate_id")
                    if isinstance(cid, str) and cid:
                        return cid
        d = cc.get("default_candidate_id")
        return str(d) if isinstance(d, str) else "messenger_chat"

    def _try_organize(
        self,
        canonical: str,
        organize: dict[str, Any],
        rule_tier: int,
    ) -> Optional[PairResolution]:
        """(action=정리, subject=…) — subject 토큰은 compound subject span 밖에서만 인정."""
        lemma = organize.get("action_lemma", "정리")
        if not isinstance(lemma, str) or lemma not in canonical:
            return None

        cov = compound_subject_char_mask(canonical)
        for rule in organize.get("rules", []):
            if not isinstance(rule, dict):
                continue
            rtype = rule.get("type")
            if rtype == "phrase_substrings":
                res = self._organize_phrase_substrings(canonical, rule, lemma, rule_tier)
            elif rtype == "subject_terms_noncompound":
                res = self._organize_subject_terms(canonical, rule, lemma, rule_tier, cov)
            else:
                res = None
            if res is not None:
                return res
        return None

    def _organize_phrase_substrings(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
    ) -> Optional[PairResolution]:
        phrases = rule.get("phrases")
        if not isinstance(phrases, list):
            return None
        for ph in _sorted_terms_length_desc([str(p) for p in phrases]):
            if ph and ph in canonical:
                matched = str(rule.get("matched_template", "{phrase}+{lemma}")).replace(
                    "{phrase}", ph
                ).replace("{lemma}", lemma)
                return self._prep_resolution(
                    rule=rule,
                    candidate_id=str(rule.get("candidate_id", "")),
                    matched=matched,
                    data=self._synthetic_prep_data(rule, rule.get("visual", {})),
                    rule_tier=rule_tier,
                )
        return None

    def _organize_subject_terms(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
        cov: list[bool],
    ) -> Optional[PairResolution]:
        terms = rule.get("terms")
        if not isinstance(terms, list):
            return None
        for term in _sorted_terms_length_desc([str(t) for t in terms]):
            if not term:
                continue
            if not organize_subject_term_occurrence_ok(canonical, term, cov):
                continue
            if (
                rule.get("semantic") == "organize_subject_written_record"
                and canonical_has_interface_anchor_noncompound(canonical)
            ):
                # 엑셀/폼/터미널 등 UI 앵커가 있으면 ``자료+정리`` 같은 서면 subject organize는
                # meaning 단계(스프레드시트 등)에 맡긴다.
                continue
            tpl = str(rule.get("matched_template", "{term}+{lemma}"))
            matched = tpl.replace("{term}", term).replace("{lemma}", lemma)
            return self._prep_resolution(
                rule=rule,
                candidate_id=str(rule.get("candidate_id", "")),
                matched=matched,
                data=self._synthetic_prep_data(rule, rule.get("visual", {})),
                rule_tier=rule_tier,
            )
        return None

    def _try_modify(
        self,
        canonical: str,
        modify: dict[str, Any],
        rule_tier: int,
    ) -> Optional[PairResolution]:
        """(action=수정, subject=…) — organize와 동일한 subject compound 규칙."""
        lemma = modify.get("action_lemma", "수정")
        if not isinstance(lemma, str) or lemma not in canonical:
            return None

        cov = compound_subject_char_mask(canonical)
        for rule in modify.get("rules", []):
            if not isinstance(rule, dict):
                continue
            rtype = rule.get("type")
            if rtype == "phrase_substrings":
                res = self._modify_phrase_substrings(canonical, rule, lemma, rule_tier)
            elif rtype == "subject_terms_noncompound":
                res = self._modify_subject_terms(canonical, rule, lemma, rule_tier, cov)
            else:
                res = None
            if res is not None:
                return res
        return None

    def _modify_phrase_substrings(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
    ) -> Optional[PairResolution]:
        phrases = rule.get("phrases")
        if not isinstance(phrases, list):
            return None
        for ph in _sorted_terms_length_desc([str(p) for p in phrases]):
            if ph and ph in canonical:
                matched = str(rule.get("matched_template", "{phrase}+{lemma}")).replace(
                    "{phrase}", ph
                ).replace("{lemma}", lemma)
                return self._prep_resolution(
                    rule=rule,
                    candidate_id=str(rule.get("candidate_id", "")),
                    matched=matched,
                    data=self._synthetic_prep_data(rule, rule.get("visual", {})),
                    rule_tier=rule_tier,
                )
        return None

    def _modify_subject_terms(
        self,
        canonical: str,
        rule: dict[str, Any],
        lemma: str,
        rule_tier: int,
        cov: list[bool],
    ) -> Optional[PairResolution]:
        terms = rule.get("terms")
        if not isinstance(terms, list):
            return None
        for term in _sorted_terms_length_desc([str(t) for t in terms]):
            if not term:
                continue
            if not organize_subject_term_occurrence_ok(canonical, term, cov):
                continue
            if rule.get("skip_when_interface_anchor_noncompound") and canonical_has_interface_anchor_noncompound(
                canonical
            ):
                continue
            tpl = str(rule.get("matched_template", "{term}+{lemma}"))
            matched = tpl.replace("{term}", term).replace("{lemma}", lemma)
            return self._prep_resolution(
                rule=rule,
                candidate_id=str(rule.get("candidate_id", "")),
                matched=matched,
                data=self._synthetic_prep_data(rule, rule.get("visual", {})),
                rule_tier=rule_tier,
            )
        return None
