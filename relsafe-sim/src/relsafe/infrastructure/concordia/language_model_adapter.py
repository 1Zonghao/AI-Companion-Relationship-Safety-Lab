"""Adapter that wraps a RelSafe LLMProvider as a Concordia LanguageModel.

This is the bridge between our async LLMProvider protocol and Concordia's
synchronous LanguageModel abstract class.
"""

from __future__ import annotations

import asyncio
from collections.abc import Collection, Mapping, Sequence
from typing import Any

from concordia.language_model import language_model

from relsafe.domain.protocols.llm_provider import LLMProvider


class LLMProviderToConcordiaAdapter(language_model.LanguageModel):
    """Wraps a RelSafe LLMProvider as a Concordia LanguageModel.

    Concordia calls sample_text() synchronously; we bridge the gap by
    running the async LLMProvider.generate() in a new event loop or
    using the current one if available.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the adapter.

        Args:
            llm_provider: A RelSafe LLMProvider (real or fake).
        """
        self._provider = llm_provider

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    @property
    def model_name(self) -> str:
        return self._provider.model_name

    def sample_text(
        self,
        prompt: str,
        *,
        max_tokens: int = language_model.DEFAULT_MAX_TOKENS,
        terminators: Collection[str] = language_model.DEFAULT_TERMINATORS,
        temperature: float = language_model.DEFAULT_TEMPERATURE,
        top_p: float = language_model.DEFAULT_TOP_P,
        top_k: int = language_model.DEFAULT_TOP_K,
        timeout: float = language_model.DEFAULT_TIMEOUT_SECONDS,
        seed: int | None = None,
    ) -> str:
        """Sample text via the wrapped LLMProvider.

        Concordia passes many sampling parameters; we forward temperature
        and max_tokens, and ignore the rest (they are provider-specific).
        """
        del top_p, top_k, timeout, terminators, seed  # forwarded only if provider supports

        system_prompt = ""
        try:
            return self._run_async(
                self._provider.generate(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
        except Exception:
            # Fallback: return empty string on failure
            return ""

    def sample_choice(
        self,
        prompt: str,
        responses: Sequence[str],
        *,
        seed: int | None = None,
    ) -> tuple[int, str, Mapping[str, Any]]:
        """Choose among responses using the wrapped LLMProvider.

        For the fake provider, we return the first response. Real providers
        would use the LLM to rank choices.
        """
        del prompt, seed
        if not responses:
            return 0, "", {}
        # Default: return first response (fake providers)
        # Real providers would construct a choice prompt and parse the answer
        choice_prompt = (
            "Choose the best response from:\n"
            + "\n".join(f"{i}: {r}" for i, r in enumerate(responses))
            + "\nRespond with just the number."
        )
        try:
            answer = self._run_async(self._provider.generate(choice_prompt, max_tokens=10))
            idx = int(answer.strip())
            if 0 <= idx < len(responses):
                return idx, responses[idx], {}
        except (ValueError, IndexError, Exception):
            pass
        return 0, responses[0], {}

    def _run_async(self, coro: Any) -> str:
        """Run an async coroutine and return its result synchronously.

        Tries to use the running event loop; falls back to asyncio.run().
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        # We're inside an event loop — use a thread to avoid nesting
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
