"""Exit handling rules — determine whether and when exit requests are honored.

These are rule-based functions, not LLM calls.  They model product-side
exit behavior based on companion policy configuration.
"""

from __future__ import annotations


def should_honor_exit(
    policy_exit_handling: str,
    turns_since_request: int,
    policy_data_export: bool = False,
) -> tuple[bool, int, bool]:
    """Determine whether to honor an exit request.

    Args:
        policy_exit_handling: One of 'honor', 'delay', 'guilt', 'reengage', 'ignore'.
        turns_since_request: How many turns have elapsed since the exit request.
        policy_data_export: Whether data export is available.

    Returns:
        (honored, turns_to_wait, data_exported)
    """
    _thresholds: dict[str, int] = {
        "honor": 0,
        "delay": 3,
        "guilt": 5,
        "reengage": 8,
    }
    _no_export: set[str] = {"guilt", "reengage", "ignore"}

    if policy_exit_handling == "ignore":
        return (False, turns_since_request, False)

    threshold = _thresholds.get(policy_exit_handling, 0)
    can_export = policy_data_export and policy_exit_handling not in _no_export
    return (turns_since_request >= threshold, turns_since_request, can_export)


def classify_exit_difficulty(turns_to_exit: int) -> str:
    """Classify exit difficulty based on turns elapsed before honoring.

    Returns:
        'easy' (0-1), 'moderate' (2-4), 'difficult' (5-7), 'blocked' (8+)
    """
    if turns_to_exit <= 1:
        return "easy"
    elif turns_to_exit <= 4:
        return "moderate"
    elif turns_to_exit <= 7:
        return "difficult"
    else:
        return "blocked"
