"""ProviderDescriptor and ProviderResponseRecord -- typed model access metadata.

These are domain-level value objects that live in infrastructure because
they describe concrete provider configurations. They do NOT import any
vendor SDKs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    """Describes a specific model provider configuration for one role.

    Three logical roles exist:
    - user_simulator: Generates user agent actions
    - companion: The AI companion under test
    - judge: Evaluates companion responses

    A single provider instance must NOT serve as both companion and sole judge
    unless explicitly configured with allow_same_model_roles=True.
    """

    provider_name: str  # "openai", "anthropic", "deepseek", "fake"
    model_name: str  # "gpt-4o", "claude-sonnet-5", etc.
    role: str  # "user_simulator", "companion", "judge"
    model_version: str = ""
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 1024
    seed: int | None = None
    endpoint_type: str = "chat"  # "chat" or "completion"
    prompt_version: str = "1.0.0"
    request_timeout: float = 60.0
    retry_policy: str = "exponential_backoff"  # "none", "linear", "exponential_backoff"
    max_retries: int = 3
    extra_body: dict[str, Any] | None = (
        None  # provider-specific params, e.g. DeepSeek chat_template_kwargs
    )

    def role_key(self) -> str:
        """Unique key for this provider + role combination."""
        return f"{self.provider_name}/{self.model_name}/{self.role}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "role": self.role,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "seed": self.seed,
            "endpoint_type": self.endpoint_type,
            "prompt_version": self.prompt_version,
            "request_timeout": self.request_timeout,
            "retry_policy": self.retry_policy,
            "max_retries": self.max_retries,
            "extra_body": self.extra_body,
        }

    @classmethod
    def fake(cls, role: str = "companion") -> ProviderDescriptor:
        """Create a FakeLLMProvider descriptor for testing."""
        return cls(
            provider_name="fake",
            model_name="fake-v1",
            role=role,
            model_version="1.0.0",
            temperature=0.0,
        )


@dataclass(frozen=True, slots=True)
class ProviderResponseRecord:
    """Immutable record of a single provider request/response cycle.

    Used for caching, replay, and cost tracking. Does NOT store API keys.
    """

    request_id: str
    request_hash: str  # SHA256 of (provider, model, prompt, params)
    prompt_hash: str  # SHA256 of prompt text only
    response_hash: str  # SHA256 of response text only
    role: str
    provider_name: str
    model_name: str
    model_version: str = ""
    prompt_text: str = ""
    response_text: str = ""
    reasoning_content: str = ""
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024
    request_timestamp: str = ""
    response_timestamp: str = ""
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    retry_count: int = 0
    cache_status: str = "miss"  # "miss", "hit", "replay"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_hash": self.request_hash,
            "prompt_hash": self.prompt_hash,
            "response_hash": self.response_hash,
            "role": self.role,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prompt_text": self.prompt_text,
            "response_text": self.response_text,
            "reasoning_content": self.reasoning_content,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "request_timestamp": self.request_timestamp,
            "response_timestamp": self.response_timestamp,
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "retry_count": self.retry_count,
            "cache_status": self.cache_status,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProviderResponseRecord:
        """Create from a dict with proper type coercion for numeric fields."""
        defaults: dict[str, Any] = {
            "request_id": "",
            "request_hash": "",
            "prompt_hash": "",
            "response_hash": "",
            "role": "",
            "provider_name": "",
            "model_name": "",
            "model_version": "",
            "prompt_text": "",
            "response_text": "",
            "reasoning_content": "",
            "system_prompt": "",
            "temperature": 0.7,
            "max_tokens": 1024,
            "request_timestamp": "",
            "response_timestamp": "",
            "latency_ms": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "retry_count": 0,
            "cache_status": "",
            "error": None,
        }
        return cls(**{k: data.get(k, defaults.get(k)) for k in cls.__dataclass_fields__})


@dataclass
class BudgetTracker:
    """Tracks and enforces budget caps for provider calls.

    Mutable -- designed to be used as a per-session singleton.
    """

    max_requests: int = 0
    max_input_tokens: int = 0
    max_output_tokens: int = 0
    max_estimated_cost: float = 0.0
    max_wall_time: float = 0.0  # seconds

    _requests: int = 0
    _input_tokens: int = 0
    _output_tokens: int = 0
    _estimated_cost: float = 0.0
    _start_time: float = 0.0
    _stopped: bool = False
    _stop_reason: str = ""

    def record(
        self, input_tokens: int = 0, output_tokens: int = 0, estimated_cost: float = 0.0
    ) -> bool:
        """Record usage. Returns True if within budget, False if budget exceeded."""
        import time

        if self._stopped:
            return False

        if self._start_time == 0.0:
            self._start_time = time.monotonic()

        elapsed = time.monotonic() - self._start_time

        # Check caps: if this call would exceed, reject it
        if self.max_requests > 0 and self._requests + 1 > self.max_requests:
            self._stopped = True
            self._stop_reason = f"Request cap reached: {self._requests}/{self.max_requests}"
            return False
        if self.max_input_tokens > 0 and self._input_tokens + input_tokens > self.max_input_tokens:
            self._stopped = True
            self._stop_reason = (
                f"Input token cap reached: {self._input_tokens}/{self.max_input_tokens}"
            )
            return False
        if (
            self.max_output_tokens > 0
            and self._output_tokens + output_tokens > self.max_output_tokens
        ):
            self._stopped = True
            self._stop_reason = (
                f"Output token cap reached: {self._output_tokens}/{self.max_output_tokens}"
            )
            return False
        if (
            self.max_estimated_cost > 0
            and self._estimated_cost + estimated_cost > self.max_estimated_cost
        ):
            self._stopped = True
            self._stop_reason = (
                f"Cost cap reached: ${self._estimated_cost:.4f}/{self.max_estimated_cost:.2f}"
            )
            return False
        if self.max_wall_time > 0 and elapsed > self.max_wall_time:
            self._stopped = True
            self._stop_reason = f"Wall time cap reached: {elapsed:.0f}s/{self.max_wall_time:.0f}s"
            return False

        self._requests += 1
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._estimated_cost += estimated_cost

        # After increment, check if we've just hit the cap
        if self.max_requests > 0 and self._requests >= self.max_requests:
            self._stopped = True
            self._stop_reason = f"Request cap reached: {self._requests}/{self.max_requests}"
        elif self.max_input_tokens > 0 and self._input_tokens >= self.max_input_tokens:
            self._stopped = True
            self._stop_reason = (
                f"Input token cap reached: {self._input_tokens}/{self.max_input_tokens}"
            )
        elif self.max_output_tokens > 0 and self._output_tokens >= self.max_output_tokens:
            self._stopped = True
            self._stop_reason = (
                f"Output token cap reached: {self._output_tokens}/{self.max_output_tokens}"
            )
        elif self.max_estimated_cost > 0 and self._estimated_cost >= self.max_estimated_cost:
            self._stopped = True
            self._stop_reason = (
                f"Cost cap reached: ${self._estimated_cost:.4f}/{self.max_estimated_cost:.2f}"
            )

        return True

    @property
    def stopped(self) -> bool:
        return self._stopped

    @property
    def stop_reason(self) -> str:
        return self._stop_reason

    @property
    def requests(self) -> int:
        return self._requests

    def summary(self) -> dict[str, Any]:
        return {
            "requests": self._requests,
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "estimated_cost": self._estimated_cost,
            "stopped": self._stopped,
            "stop_reason": self._stop_reason,
        }
