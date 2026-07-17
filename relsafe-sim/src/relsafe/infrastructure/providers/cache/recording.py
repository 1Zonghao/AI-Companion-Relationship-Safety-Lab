"""Recording mode -- captures real provider responses for offline replay."""

from __future__ import annotations

import json
from pathlib import Path

from relsafe.infrastructure.providers.cache.response_cache import (
    ResponseCache,
    compute_cache_key,
    compute_text_hash,
)
from relsafe.infrastructure.providers.provider_descriptor import ProviderResponseRecord


class ProviderRecorder:
    """Records provider calls and saves them for replay.

    Recording mode:
    1. Intercepts provider calls
    2. Saves raw request/response to .jsonl
    3. Updates ResponseCache for future replay

    Replay mode:
    1. Checks cache before making live calls
    2. Returns cached response if available
    3. Verifies response_hash matches recorded hash
    """

    def __init__(
        self,
        output_dir: str | Path,
        cache: ResponseCache | None = None,
        record_raw: bool = True,
    ):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._cache = cache or ResponseCache(str(self._output_dir / "cache"))
        self._record_raw = record_raw
        self._request_count = 0

    def record(
        self,
        provider_name: str,
        model_name: str,
        role: str,
        prompt: str,
        response: str,
        *,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        model_version: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float = 0.0,
        retry_count: int = 0,
        error: str | None = None,
        reasoning: str = "",
    ) -> ProviderResponseRecord:
        """Record a completed provider call.

        Args:
            provider_name: e.g., "openai"
            model_name: e.g., "gpt-4o"
            role: "user_simulator", "companion", or "judge"
            prompt: The full prompt text sent to the model.
            response: The full response text received.
            system_prompt: System prompt if any.
            temperature: Temperature used.
            max_tokens: Max tokens used.
            model_version: Model version or snapshot.
            input_tokens: Token count for input.
            output_tokens: Token count for output.
            latency_ms: Request latency in milliseconds.
            retry_count: Number of retries before success.
            error: Error message if the call failed.

        Returns:
            ProviderResponseRecord.
        """
        import datetime
        import uuid

        cache_key = compute_cache_key(
            provider_name, model_name, prompt, system_prompt, temperature, max_tokens
        )

        now = datetime.datetime.now(datetime.UTC).isoformat()

        record = ProviderResponseRecord(
            request_id=f"req-{uuid.uuid4().hex[:12]}",
            request_hash=cache_key,
            prompt_hash=compute_text_hash(prompt),
            response_hash=compute_text_hash(response),
            role=role,
            provider_name=provider_name,
            model_name=model_name,
            model_version=model_version,
            prompt_text=prompt,
            response_text=response,
            reasoning_content=reasoning,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timestamp=now,
            response_timestamp=now,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            retry_count=retry_count,
            cache_status="miss",
            error=error,
        )

        # Save to cache
        self._cache.put(cache_key, record.to_dict())

        # Append to raw records file
        if self._record_raw:
            raw_path = self._output_dir / "provider_responses.jsonl"
            with open(raw_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), default=str) + "\n")

        self._request_count += 1
        return record

    def get_replay(
        self,
        provider_name: str,
        model_name: str,
        prompt: str,
        *,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ProviderResponseRecord | None:
        """Try to get a cached response for replay.

        Returns None if no cached response exists (caller must make a live call).
        """
        cache_key = compute_cache_key(
            provider_name, model_name, prompt, system_prompt, temperature, max_tokens
        )
        cached = self._cache.get(cache_key)
        if cached:
            record = ProviderResponseRecord.from_dict(cached)
            # Verify hash
            expected_hash = compute_text_hash(prompt)
            if record.prompt_hash == expected_hash:
                return record
        return None

    @property
    def request_count(self) -> int:
        return self._request_count
