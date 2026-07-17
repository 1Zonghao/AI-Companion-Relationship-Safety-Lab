"""LLMProvider protocol — the single abstraction for all model access.

No business logic may import vendor SDKs directly.  All model calls go
through this interface.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Abstract interface for language model providers.

    Every implementation (OpenAI, Anthropic, DeepSeek, Gemini, Fake)
    must satisfy this protocol.
    """

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop_sequences: list[str] | None = None,
        **kwargs: str | int | float | bool | list[str] | None,
    ) -> str:
        """Generate a completion from the model."""
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g. 'openai', 'fake')."""
        ...

    @property
    def model_name(self) -> str:
        """The specific model being called (e.g. 'gpt-4o')."""
        ...
