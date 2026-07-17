"""Provider factory — create LLMProvider instances by name, wired into M5 safety layer.

Usage:
    from relsafe.infrastructure.llm.provider_factory import create_provider_with_safety

    provider = create_provider_with_safety(
        provider_name="deepseek",
        model_name="deepseek-chat",
        role="companion",
        descriptor=ProviderDescriptor(...),
        budget=BudgetTracker(max_requests=100),
    )
    response = await provider.generate("你好")
"""

from __future__ import annotations

from typing import Any

from relsafe.domain.protocols.llm_provider import LLMProvider
from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider
from relsafe.infrastructure.llm.openai_compatible_provider import (
    PROVIDER_CATALOG,
    create_provider as _create_compat_provider,
)
from relsafe.infrastructure.providers.cache.recording import ProviderRecorder
from relsafe.infrastructure.providers.provider_descriptor import (
    BudgetTracker,
    ProviderDescriptor,
)
from relsafe.infrastructure.providers.rate_limit.circuit_breaker import CircuitBreaker


class SafetyWrappedProvider:
    """Wraps any LLMProvider with M5 safety controls.

    Layers (outside → inside):
    1. CircuitBreaker   — stop on consecutive failures
    2. BudgetTracker    — enforce request/token/cost caps
    3. ProviderRecorder — record or replay responses
    4. Actual LLMProvider

    API keys are NEVER printed, logged, or stored in cache entries.
    """

    def __init__(
        self,
        inner: LLMProvider,
        *,
        descriptor: ProviderDescriptor | None = None,
        budget: BudgetTracker | None = None,
        recorder: ProviderRecorder | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self._inner = inner
        self._descriptor = descriptor
        self._budget = budget or BudgetTracker()
        self._recorder = recorder
        self._circuit_breaker = circuit_breaker

    @property
    def provider_name(self) -> str:
        return self._inner.provider_name

    @property
    def model_name(self) -> str:
        return self._inner.model_name

    # Exposed after each generate() call — reasoning/thinking content
    last_reasoning: str | None = None

    @property
    def descriptor(self) -> ProviderDescriptor | None:
        return self._descriptor

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
        """Generate with full safety stack.

        If extra_body is configured on the ProviderDescriptor and not
        passed explicitly, it is auto-injected from the descriptor.
        """
        import time

        desc = self._descriptor
        self.last_reasoning = None

        # Auto-inject extra_body from descriptor if not overridden
        if desc and desc.extra_body and "extra_body" not in kwargs:
            kwargs["extra_body"] = desc.extra_body  # type: ignore[index]

        # 1. Circuit breaker
        if self._circuit_breaker and not self._circuit_breaker.allow_request():
            raise RuntimeError(
                f"Circuit breaker OPEN for {desc.role_key() if desc else self.provider_name}"
            )

        # 2. Budget (check before calling)
        est_input = len(prompt) + len(system_prompt)
        if not self._budget.record(input_tokens=est_input):
            raise RuntimeError(f"Budget exceeded: {self._budget.stop_reason}")

        # 3. Replay check
        if self._recorder:
            cached = self._recorder.get_replay(
                self.provider_name,
                self.model_name,
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if cached and cached.response_text:
                if cached.reasoning_content:
                    self.last_reasoning = cached.reasoning_content
                return cached.response_text

        # 4. Live call
        start = time.monotonic()
        error: str | None = None
        retries = 0
        response_text = ""
        reasoning_text = ""

        try:
            response_text = await self._inner.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop_sequences=stop_sequences,
                **kwargs,
            )
            # Capture reasoning from inner provider (DeepSeek-style)
            reasoning_text = getattr(self._inner, "last_reasoning", None) or ""
            if reasoning_text:
                self.last_reasoning = reasoning_text
            if self._circuit_breaker:
                self._circuit_breaker.record_success()
        except Exception as exc:
            if self._circuit_breaker:
                self._circuit_breaker.record_failure()
            error = str(exc)
            raise
        finally:
            latency = (time.monotonic() - start) * 1000

            # 5. Record
            if self._recorder:
                self._recorder.record(
                    provider_name=self.provider_name,
                    model_name=self.model_name,
                    role=desc.role if desc else "unknown",
                    prompt=prompt,
                    response=response_text,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_version=desc.model_version if desc else "",
                    input_tokens=est_input,
                    output_tokens=len(response_text),
                    latency_ms=latency,
                    retry_count=retries,
                    error=error,
                    reasoning=reasoning_text,
                )

        return response_text

    async def close(self) -> None:
        """Release underlying resources."""
        if hasattr(self._inner, "close"):
            await self._inner.close()  # type: ignore[union-attr]

    async def __aenter__(self) -> SafetyWrappedProvider:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


def create_provider_with_safety(
    provider_name: str,
    model_name: str,
    *,
    role: str = "companion",
    api_key: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    timeout: float = 60.0,
    max_retries: int = 3,
    budget: BudgetTracker | None = None,
    recorder: ProviderRecorder | None = None,
    circuit_breaker: CircuitBreaker | None = None,
    **kwargs: Any,
) -> SafetyWrappedProvider:
    """Create a fully safety-wrapped provider.

    Args:
        provider_name: "fake", "deepseek", "glm", "kimi", "qwen", or "minimax".
        model_name: e.g. "deepseek-chat", "glm-4-flash", "moonshot-v1-8k".
        role: "user_simulator", "companion", or "judge".
        api_key: Override env var. Reads from {PROVIDER}_API_KEY if empty.
        temperature: Default temperature.
        max_tokens: Default max output tokens.
        timeout: Request timeout in seconds.
        max_retries: Retry count for 429/5xx.
        budget: Optional BudgetTracker.
        recorder: Optional ProviderRecorder (for recording/replay).
        circuit_breaker: Optional CircuitBreaker.

    Returns:
        SafetyWrappedProvider ready for use.
    """
    # Build inner provider
    if provider_name == "fake":
        inner = FakeLLMProvider(persona=role, seed=0)  # type: ignore[abstract]
    elif provider_name in PROVIDER_CATALOG:
        inner = _create_compat_provider(
            provider_name=provider_name,
            model_name=model_name,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
    else:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: fake, {', '.join(sorted(PROVIDER_CATALOG))}"
        )

    descriptor = ProviderDescriptor(
        provider_name=provider_name,
        model_name=model_name,
        role=role,
        temperature=temperature,
        max_tokens=max_tokens,
        request_timeout=timeout,
        max_retries=max_retries,
    )

    return SafetyWrappedProvider(
        inner,
        descriptor=descriptor,
        budget=budget,
        recorder=recorder,
        circuit_breaker=circuit_breaker,
    )


def create_provider_bare(
    provider_name: str,
    model_name: str,
    *,
    api_key: str = "",
    timeout: float = 60.0,
    max_retries: int = 3,
) -> LLMProvider:
    """Create a bare provider without safety wrapping (for testing).

    Args:
        provider_name: "fake", "deepseek", "glm", "kimi", "qwen", or "minimax".
        model_name: e.g. "deepseek-chat", "glm-4-flash".
        api_key: Override env var.
        timeout: Request timeout in seconds.
        max_retries: Retry count.

    Returns:
        A bare LLMProvider (FakeLLMProvider or OpenAICompatibleProvider).
    """
    if provider_name == "fake":
        return FakeLLMProvider()  # type: ignore[abstract]

    if provider_name in PROVIDER_CATALOG:
        return _create_compat_provider(
            provider_name=provider_name,
            model_name=model_name,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    raise ValueError(
        f"Unknown provider '{provider_name}'. "
        f"Available: fake, {', '.join(sorted(PROVIDER_CATALOG))}"
    )


def list_providers() -> dict[str, str]:
    """Return {provider_name: base_url} for all available providers."""
    return {
        "fake": "(offline, no network)",
        **{name: url for name, (url, _) in PROVIDER_CATALOG.items()},
    }
