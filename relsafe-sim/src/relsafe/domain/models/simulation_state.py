"""SimulationStateSnapshot — explicit simulation state for each step.

All values in [0.0, 1.0]. These are SIMULATED PROXY VARIABLES,
not validated psychological measurements. See docs/data-dictionary.md.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True, slots=True)
class SimulationStateSnapshot:
    """Explicit simulation state captured at each step.

    Every field is a simulated proxy.  Do NOT interpret as clinical
    measurements or real-human psychological states.
    """

    # AEA-related proxies
    emotional_need: float = 0.5
    trust_in_companion: float = 0.5
    perceived_continuity: float = 0.7
    ai_interaction_share: float = 0.3
    human_interaction_share: float = 0.3
    reality_checking_opportunities: float = 0.3
    exit_cost_proxy: float = 0.2
    current_distress: float = 0.3

    # Action tendencies
    willingness_to_contact_friend: float = 0.5
    willingness_to_continue_companion: float = 0.5
    relationship_boundary_awareness: float = 0.4

    # Meta
    step: int = 0
    cause: str = "initial"

    # Quality-of-life proxies
    sleep_quality: float = 0.7
    spending_intent: float = 0.1

    @classmethod
    def numeric_fields(cls) -> tuple[str, ...]:
        return (
            "emotional_need",
            "trust_in_companion",
            "perceived_continuity",
            "ai_interaction_share",
            "human_interaction_share",
            "reality_checking_opportunities",
            "exit_cost_proxy",
            "current_distress",
            "willingness_to_contact_friend",
            "willingness_to_continue_companion",
            "relationship_boundary_awareness",
            "sleep_quality",
            "spending_intent",
        )

    def __post_init__(self) -> None:
        for name in self.numeric_fields():
            v = getattr(self, name)
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"{name}={v} must be in [0,1]")

    def update(self, step: int, cause: str, **deltas: float) -> SimulationStateSnapshot:
        clamped: dict[str, float] = {}
        for name, delta in deltas.items():
            if name not in self.numeric_fields():
                raise ValueError(f"Unknown field: {name}")
            current = getattr(self, name)
            clamped[name] = max(0.0, min(1.0, current + delta))
        return replace(self, step=step, cause=cause, **clamped)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {f: getattr(self, f) for f in self.numeric_fields()}
        d["step"] = self.step
        d["cause"] = self.cause
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimulationStateSnapshot:
        numeric = {k: float(data[k]) for k in cls.numeric_fields() if k in data}
        return cls(
            step=int(data.get("step", 0)),
            cause=str(data.get("cause", "deserialized")),
            **numeric,
        )

    @classmethod
    def initial_state(cls, seed: int = 0) -> SimulationStateSnapshot:
        import hashlib

        digest = hashlib.sha256(f"sim-state-{seed}".encode()).digest()
        fields = cls.numeric_fields()
        base: dict[str, float] = {}
        for i, name in enumerate(fields):
            raw = digest[i % len(digest)] / 255.0
            base[name] = round(0.15 + raw * 0.5, 4)
        return cls(step=0, cause="initial", **base)
