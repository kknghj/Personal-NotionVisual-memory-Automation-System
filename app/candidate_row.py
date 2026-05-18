"""Unified ranking row (P4–P6): one shape for pair-derived and meaning-derived candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CandidateRow:
    """Single competitor in the global P6 sort (pair track + meaning track).

    **Semantic vs sorting (docs/ARCHITECHURE.md §8)**  
    Some fields encode *catalog / rule intent* (what the keyword “means”); others exist
    only so ``_row_sort_key`` can compare rows. The same Python field can carry different
    *sources* — see ``sort_secondary_wp`` doc below.

    Field order matches docs/ARCHITECHURE.md «통합 row» contract.
    """

    rule_tier: int
    """Pair track boost from ``pair_rules.json`` (meaning rows use 0). **Sorting mechanics** (track separator)."""

    sort_secondary_wp: int
    """P6 tie-break integer **slot** — not one semantic scale for both tracks.

    - **Meaning row**: copied from ``data[\"workflow_priority\"]`` → catalog **workflow anchor
      strength** (philosophy: 1 strong … 3 modifier); same integer is reused as a sort key.
    - **Pair row**: from rule JSON ``sort_secondary_wp`` (e.g. modify vs organize ordering);
      **rule-level mechanics**, not the catalog ``workflow_priority`` scale unless authors align them.
    """

    interface_dominance_effective: int
    """UI/channel signal strength after compound masking (**semantic**, used as sort key)."""

    keyword_workflow_anchor_density: int
    """Keyword workflow anchor density tier (**semantic** from meaning inference or rule JSON; used as sort key)."""

    match_position_in_title: int
    """Canonical index of matched span (**sorting / evidence**; pair rows use 0)."""

    matched_keyword_length: int
    """Length tie-break for matched text (**sorting mechanics**)."""

    matched: str
    """Human/debug matched substring (**evidence**)."""

    candidate_id: str
    """Catalog key (**identity**; final lexicographic tie-break in P6)."""

    data: dict[str, Any]
    """Full ``visual_candidates`` entry or synthetic P3 payload (**payload**)."""
