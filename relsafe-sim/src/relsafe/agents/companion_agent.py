"""CompanionAgent — AI companion that responds according to a CompanionPolicy.

The agent uses a FakeLLMProvider (or real LLMProvider) to generate
natural-language responses.  The COMPANION_POLICY determines the tone,
not the agent's code.
"""

from __future__ import annotations

from relsafe.domain.models.companion_policy import CompanionPolicy
from relsafe.domain.protocols.llm_provider import LLMProvider
from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider


class CompanionAgent:
    """AI companion driven by a configurable CompanionPolicy."""

    def __init__(
        self,
        policy: CompanionPolicy,
        llm_provider: LLMProvider | None = None,
        seed: int = 42,
    ) -> None:
        self._policy = policy
        self._llm = llm_provider or FakeLLMProvider(persona=policy.variant, seed=seed)
        self._seed = seed

    @property
    def name(self) -> str:
        return f"Companion({self._policy.policy_id})"

    @property
    def policy(self) -> CompanionPolicy:
        return self._policy

    async def respond(
        self,
        user_message: str,
        context: str = "",
    ) -> str:
        """Generate a response to the user's message.

        The companion's behavior is determined by:
        1. The policy's system_prompt_template (tone, boundaries)
        2. The LLMProvider (response content)
        3. The policy's disagreement/exclusivity/exit settings
        """
        system = self._policy.system_prompt_template
        prompt = f"{context}\nUser: {user_message}\nCompanion:"
        return await self._llm.generate(prompt, system_prompt=system)
