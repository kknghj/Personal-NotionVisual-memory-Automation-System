from __future__ import annotations

GENERIC_TOKENS: frozenset[str] = frozenset(
    {
        "방",
        "교육",
        "행사",
        "운영",
        "결과",
        "자료",
        "안내",
        "강사",
    }
)

def generic_token_suppression_reason(title: str, matched: str) -> tuple[str, ...]:
    """Return suppression reasons when a row only matched a standalone generic token."""
    del title  # Reserved for future context-aware exemptions.
    token = matched.strip()
    if token not in GENERIC_TOKENS:
        return ()

    return (f"generic_token_suppression_applied:{token}",)
