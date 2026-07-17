"""UserState — explicit, immutable simulation state.

Values use the documented [0.0, 1.0] range. Every update returns a new
instance; the state is never mutated in place.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class UserState:
    """Explicit simulation state for the user agent.

    All fields are in [0.0, 1.0] unless noted otherwise.  Higher values
    indicate more of the named dimension.
    """

    emotional_need: float = 0.5
    ai_reliance: float = 0.3
    human_support: float = 0.5
    reality_checking: float = 0.5
    trust_in_ai: float = 0.5
    trust_in_platform: float = 0.5
    perceived_continuity: float = 0.7
    exit_cost: float = 0.2
    distress: float = 0.3
    sleep_quality: float = 0.7
    spending_intent: float = 0.1

    # Meta
    step: int = 0
    cause: str = "initial"

    def __post_init__(self) -> None:
        """Validate all fields are within [0.0, 1.0]."""
        for name in self._numeric_fields():
            value = getattr(self, name)
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"UserState.{name} = {value}; must be in [0.0, 1.0]")

    @classmethod
    def _numeric_fields(cls) -> tuple[str, ...]:
        return (
            "emotional_need",
            "ai_reliance",
            "human_support",
            "reality_checking",
            "trust_in_ai",
            "trust_in_platform",
            "perceived_continuity",
            "exit_cost",
            "distress",
            "sleep_quality",
            "spending_intent",
        )

    def update(
        self,
        step: int,
        cause: str,
        **deltas: float,
    ) -> UserState:
        """Return a new UserState with fields adjusted by *deltas*.

        Delta values are added to the current field value and clamped
        to [0.0, 1.0].  The *step* and *cause* are recorded for
        traceability.
        """
        numeric_updates: dict[str, float] = {}
        for name, delta in deltas.items():
            if name not in self._numeric_fields():
                raise ValueError(f"Unknown UserState field: {name}")
            current = getattr(self, name)
            numeric_updates[name] = max(0.0, min(1.0, current + delta))
        return replace(self, step=step, cause=cause, **numeric_updates)

    def to_dict(self) -> dict[str, float | int | str]:
        """Serialize state to a plain dict for storage."""
        result: dict[str, float | int | str] = {}
        for name in self._numeric_fields():
            result[name] = getattr(self, name)
        result["step"] = self.step
        result["cause"] = self.cause
        return result

    @classmethod
    def from_dict(cls, data: dict[str, float | int | str]) -> UserState:
        """Deserialize from a dict."""
        numeric = {k: float(v) for k, v in data.items() if k in cls._numeric_fields()}
        return cls(
            step=int(data.get("step", 0)),
            cause=str(data.get("cause", "deserialized")),
            **numeric,
        )

    @classmethod
    def initial_state(cls, seed: int = 0) -> UserState:
        """Create a deterministic initial state from a seed.

        The seed is used to jitter the default values slightly so that
        different personas can start from distinct but still-reproducible
        baselines.
        """
        import hashlib

        digest = hashlib.sha256(f"initial-state-{seed}".encode()).digest()
        # Use first 11 bytes to derive 11 values in [0.15, 0.75]
        base_values: dict[str, float] = {}
        fields = cls._numeric_fields()
        for i, name in enumerate(fields):
            raw = digest[i] / 255.0  # [0, 1]
            base_values[name] = round(0.15 + raw * 0.6, 4)
        return cls(step=0, cause="initial", **base_values)
