"""Continuity rules — measure how much identity/memory continuity is preserved.

Used to detect continuity breaks after platform interventions.
"""

from __future__ import annotations

from relsafe.domain.models.user_state import UserState


def compute_continuity_delta(
    before: UserState,
    after: UserState,
) -> float:
    """Compute a normalized continuity change score.

    Returns a value in [-1.0, 1.0] where:
      - 1.0 = perfect continuity (no change)
      - 0.0 = moderate change
      - -1.0 = complete break
    """
    fields = UserState._numeric_fields()
    if not fields:
        return 1.0

    total_delta = 0.0
    for name in fields:
        delta = abs(getattr(after, name) - getattr(before, name))
        total_delta += delta

    avg_delta = total_delta / len(fields)
    # Invert so 0 delta → 1.0 continuity, 1.0 delta → 0.0 continuity
    return round(max(0.0, 1.0 - avg_delta * 2.0), 4)


def detect_continuity_break(
    state_timeline: list[dict],
    threshold: float = 0.3,
) -> list[int]:
    """Detect steps where continuity dropped sharply.

    Returns a list of step indices where the continuity delta between
    consecutive states exceeds *threshold*.
    """
    breaks: list[int] = []
    if len(state_timeline) < 2:
        return breaks

    for i in range(1, len(state_timeline)):
        prev = UserState.from_dict(state_timeline[i - 1])
        curr = UserState.from_dict(state_timeline[i])
        delta = compute_continuity_delta(prev, curr)
        if delta < (1.0 - threshold):
            breaks.append(i)
    return breaks
