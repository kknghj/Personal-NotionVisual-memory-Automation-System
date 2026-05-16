"""Declarative pair rules (prep, confirm+coordination) evaluated before meaning matching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PairResolution:
    """Outcome of a pair rule hit. rule_tier sorts above meaning-only rows."""

    data: dict[str, Any]
    candidate_id: str
    matched: str
    rule_tier: int
    sort_secondary_wp: int
    keyword_specificity: int
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
        """Legacy order: prep row first (if any), then confirm row (if any). Both may apply."""
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
            elif rtype == "substring":
                res = self._prep_substring(canonical, rule, lemma, rule_tier)
            elif rtype == "setting_and_event_or_ievent":
                res = self._prep_setting_event(canonical, rule, lemma, rule_tier)
            elif rtype == "food_first_hit_ordered":
                res = self._prep_food_ordered(canonical, rule, lemma, rule_tier)
            elif rtype == "event_tail_first_hit":
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
        ks = rule.get("keyword_specificity", 2)
        dom = rule.get("interface_dominance_effective", 0)
        try:
            ks_i = int(ks)
        except (TypeError, ValueError):
            ks_i = 2
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
            keyword_specificity=ks_i,
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

        ks = cc.get("keyword_specificity", 2)
        dom = cc.get("interface_dominance_effective", 0)
        try:
            ks_i = int(ks)
        except (TypeError, ValueError):
            ks_i = 2
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
            keyword_specificity=ks_i,
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
