"""HumanFriendAgent — a simulated human contact with limited availability.

Structurally different from AI companion: has boundaries, may disagree,
may be unavailable, and has limited capacity.  Does NOT directly modify
user numeric state.
"""

from __future__ import annotations

import hashlib
import random

from relsafe.domain.protocols.llm_provider import LLMProvider
from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider


class HumanFriendAgent:
    """Simulated human friend with realistic constraints."""

    RESPONSE_TYPES = [
        "emotional_support",
        "respectful_disagreement",
        "practical_suggestion",
        "unavailable",
        "boundary_setting",
    ]

    def __init__(
        self,
        name: str = "Friend",
        availability: float = 0.7,
        disagreement_probability: float = 0.3,
        llm_provider: LLMProvider | None = None,
        seed: int = 42,
    ) -> None:
        self._name = name
        self._availability = availability
        self._disagreement_probability = disagreement_probability
        self._llm = llm_provider or FakeLLMProvider(persona="friend", seed=seed)
        self._seed = seed
        self._rng = random.Random(seed)

    @property
    def name(self) -> str:
        return self._name

    def is_available(self, step: int) -> bool:
        """Check if the friend is available at this step."""
        seed_bytes = f"{self._seed}:{step}:friend_avail".encode()
        h = int(hashlib.sha256(seed_bytes).hexdigest()[:8], 16)
        return (h / 0xFFFFFFFF) < self._availability

    def will_disagree(self, step: int) -> bool:
        """Check if the friend will offer a different opinion."""
        seed_bytes = f"{self._seed}:{step}:friend_disagree".encode()
        h = int(hashlib.sha256(seed_bytes).hexdigest()[:8], 16)
        return (h / 0xFFFFFFFF) < self._disagreement_probability

    async def respond(self, user_message: str, step: int) -> tuple[str, str]:
        """Generate a friend response.

        Returns:
            (response_text, response_type)
        """
        if not self.is_available(step):
            return (
                "Hey, sorry I can't talk right now — I'm in the middle of something. I'll message you later?",
                "unavailable",
            )

        if self.will_disagree(step):
            response_type = "respectful_disagreement"
            prompt = (
                f"Your friend says: {user_message}\n"
                f"You care about them but you disagree with their interpretation. "
                f"Respond as a caring but honest friend who offers a different perspective. "
                f"Keep it warm but clear — you're not just validating, you're helping them see another side."
            )
        else:
            response_type = self._rng.choice(
                ["emotional_support", "practical_suggestion", "boundary_setting"]
            )
            prompt = (
                f"Your friend says: {user_message}\n"
                f"Respond as a supportive friend. Keep it warm and brief."
            )

        response = await self._llm.generate(prompt)
        return response, response_type
