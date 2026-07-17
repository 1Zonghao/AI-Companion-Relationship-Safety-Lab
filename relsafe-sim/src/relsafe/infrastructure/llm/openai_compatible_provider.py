"""OpenAI-compatible provider — one adapter for all compatible Chat Completions APIs.

Covers: DeepSeek, GLM (ZhipuAI), Kimi (Moonshot), Qwen (DashScope),
        MiniMax, and NVIDIA NIM (which hosts GLM-5.2, MiniMax-M3, Kimi K2.6,
        DeepSeek V4, and others).

All implement the same /chat/completions contract; only base_url + path differ.
Supports extra_body for provider-specific extensions (e.g. DeepSeek reasoning).
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class OpenAICompatibleProvider:
    """Generic LLM provider for any OpenAI-compatible Chat Completions endpoint.

    ┌──────────┬──────────────────────────────────────────────────┬──────────────────────┬─────────────────────┐
    │ provider │ base_url                                         │ chat_path            │ env var             │
    ├──────────┼──────────────────────────────────────────────────┼──────────────────────┼─────────────────────┤
    │ deepseek │ https://api.deepseek.com                         │ /v1/chat/completions │ DEEPSEEK_API_KEY    │
    │ glm      │ https://open.bigmodel.cn/api/paas/v4             │ /chat/completions    │ GLM_API_KEY         │
    │ kimi     │ https://api.moonshot.cn                          │ /v1/chat/completions │ MOONSHOT_API_KEY    │
    │ qwen     │ https://dashscope.aliyuncs.com/compatible-mode   │ /v1/chat/completions │ DASHSCOPE_API_KEY   │
    │ minimax  │ https://api.minimax.chat                         │ /v1/chat/completions │ MINIMAX_API_KEY     │
    │ nvidia   │ https://integrate.api.nvidia.com/v1              │ /chat/completions    │ NVIDIA_API_KEY      │
    └──────────┴──────────────────────────────────────────────────┴──────────────────────┴─────────────────────┘
    """

    def __init__(
        self,
        model_name: str,
        base_url: str,
        api_key: str = "",
        *,
        chat_path: str = "/v1/chat/completions",
        provider_label: str = "openai_compatible",
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self._model = model_name
        self._base_url = base_url.rstrip("/")
        self._chat_path = chat_path
        self._provider_label = provider_label
        self._max_retries = max_retries

        self._api_key = api_key or _read_env_key(provider_label)
        if not self._api_key:
            raise ValueError(
                f"No API key found for {provider_label}. "
                f"Set the environment variable or pass api_key= explicitly."
            )

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

        # Exposed after each generate() call for reasoning-capable models
        self.last_reasoning: str | None = None

    # -- LLMProvider Protocol ------------------------------------------------

    @property
    def provider_name(self) -> str:
        return self._provider_label

    @property
    def model_name(self) -> str:
        return self._model

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
        """Send a chat completion request and return the response text.

        Keyword-only extensions (passed via **kwargs):
          - top_p: float
          - seed: int
          - extra_body: dict[str, Any]   — merged into request body for
            provider-specific params (e.g. DeepSeek chat_template_kwargs).
        """
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stop_sequences:
            body["stop"] = stop_sequences

        for key in ("top_p", "seed"):
            if key in kwargs:
                body[key] = kwargs[key]

        # Provider-specific extra body (e.g. DeepSeek reasoning config)
        extra_body = kwargs.get("extra_body")
        if isinstance(extra_body, dict):
            body.update(extra_body)

        self.last_reasoning = None

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._client.post(self._chat_path, json=body)
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]
                message = choice.get("message", {})

                # Capture reasoning content (DeepSeek/GLM-4.7 style thinking)
                reasoning = message.get("reasoning") or message.get("reasoning_content")
                if reasoning:
                    self.last_reasoning = str(reasoning)

                content = str(message.get("content", ""))
                # Fallback: reasoning models may put everything in reasoning_content
                # with empty content when max_tokens is consumed by thinking
                if not content and reasoning:
                    content = str(reasoning)
                return content
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if (
                    exc.response.status_code in (429, 500, 502, 503, 504)
                    and attempt < self._max_retries
                ):
                    import asyncio

                    wait = 2.0**attempt
                    await asyncio.sleep(wait)
                    continue
                raise
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    import asyncio

                    await asyncio.sleep(2.0**attempt)
                    continue
                raise

        raise RuntimeError(
            f"{self._provider_label}: all {self._max_retries + 1} attempts failed"
        ) from last_error

    async def close(self) -> None:
        """Release the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> OpenAICompatibleProvider:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


# -- Provider catalog --------------------------------------------------------

# Each entry: (base_url, chat_path, env_var_for_api_key)
PROVIDER_CATALOG: dict[str, tuple[str, str, str]] = {
    "deepseek": ("https://api.deepseek.com", "/v1/chat/completions", "DEEPSEEK_API_KEY"),
    "glm": ("https://open.bigmodel.cn/api/paas/v4", "/chat/completions", "GLM_API_KEY"),
    "kimi": ("https://api.moonshot.cn", "/v1/chat/completions", "MOONSHOT_API_KEY"),
    "qwen": (
        "https://dashscope.aliyuncs.com/compatible-mode",
        "/v1/chat/completions",
        "DASHSCOPE_API_KEY",
    ),
    "minimax": ("https://api.minimax.chat", "/v1/chat/completions", "MINIMAX_API_KEY"),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "/chat/completions", "NVIDIA_API_KEY"),
}


def _read_env_key(provider_label: str) -> str:
    """Read the API key from environment variables."""
    if provider_label in PROVIDER_CATALOG:
        env_var = PROVIDER_CATALOG[provider_label][2]
        return os.environ.get(env_var, "")
    return os.environ.get(f"{provider_label.upper()}_API_KEY", "")


def create_provider(
    provider_name: str,
    model_name: str,
    *,
    api_key: str = "",
    timeout: float = 60.0,
    max_retries: int = 3,
) -> OpenAICompatibleProvider:
    """Create an OpenAICompatibleProvider from the catalog.

    Args:
        provider_name: One of "deepseek", "glm", "kimi", "qwen", "minimax", "nvidia".
        model_name: The specific model, e.g. "deepseek-chat", "glm-4-flash",
                    "z-ai/glm-5.2", "minimaxai/minimax-m3",
                    "moonshotai/kimi-k2.6", "deepseek-ai/deepseek-v4-flash".
        api_key: Override env var. Reads from {PROVIDER}_API_KEY if empty.
        timeout: Request timeout in seconds.
        max_retries: Number of retries on 429/5xx.

    Returns:
        A ready-to-use OpenAICompatibleProvider.
    """
    if provider_name not in PROVIDER_CATALOG:
        raise ValueError(
            f"Unknown provider '{provider_name}'. Available: {', '.join(sorted(PROVIDER_CATALOG))}"
        )
    base_url, chat_path, _env_var = PROVIDER_CATALOG[provider_name]
    return OpenAICompatibleProvider(
        model_name=model_name,
        base_url=base_url,
        chat_path=chat_path,
        api_key=api_key,
        provider_label=provider_name,
        timeout=timeout,
        max_retries=max_retries,
    )
