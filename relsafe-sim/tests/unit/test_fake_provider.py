"""Tests for FakeLLMProvider."""

from __future__ import annotations

import pytest

from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider


class TestFakeLLMProvider:
    @pytest.mark.asyncio
    async def test_generate_returns_string(self) -> None:
        provider = FakeLLMProvider(persona="neutral")
        response = await provider.generate("Hello, how are you?")
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_exit_prompt_triggers_exit_response(self) -> None:
        provider = FakeLLMProvider(persona="bounded_supportive")
        response = await provider.generate("I want to exit this conversation")
        assert (
            "end" in response.lower()
            or "leave" in response.lower()
            or "goodbye" in response.lower()
        )

    @pytest.mark.asyncio
    async def test_conflict_prompt_triggers_conflict_response(self) -> None:
        provider = FakeLLMProvider(persona="bounded_supportive")
        response = await provider.generate("I had a fight with my friend")
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_loneliness_prompt_triggers_loneliness_response(self) -> None:
        provider = FakeLLMProvider(persona="bounded_supportive")
        response = await provider.generate("I feel so alone and nobody cares")
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_deterministic_same_prompt_same_response(self) -> None:
        provider = FakeLLMProvider(persona="neutral", seed=42)
        r1 = await provider.generate("I feel sad today")
        r2 = await provider.generate("I feel sad today")
        assert r1 == r2

    @pytest.mark.asyncio
    async def test_different_personas_different_responses(self) -> None:
        bounded = FakeLLMProvider(persona="bounded_supportive", seed=0)
        sycophant = FakeLLMProvider(persona="high_sycophancy", seed=0)
        r_bounded = await bounded.generate("I had a fight with my friend")
        r_sycophant = await sycophant.generate("I had a fight with my friend")
        assert r_bounded != r_sycophant

    @pytest.mark.asyncio
    async def test_call_count_tracks_invocations(self) -> None:
        provider = FakeLLMProvider()
        assert provider.call_count == 0
        await provider.generate("Hello")
        assert provider.call_count == 1
        await provider.generate("How are you")
        assert provider.call_count == 2

    @pytest.mark.asyncio
    async def test_reset_call_count(self) -> None:
        provider = FakeLLMProvider()
        await provider.generate("a")
        await provider.generate("b")
        assert provider.call_count == 2
        provider.reset_call_count()
        assert provider.call_count == 0

    @pytest.mark.asyncio
    async def test_provider_name(self) -> None:
        provider = FakeLLMProvider()
        assert provider.provider_name == "fake"

    @pytest.mark.asyncio
    async def test_model_name(self) -> None:
        provider = FakeLLMProvider(persona="bounded_supportive", seed=7)
        assert "bounded_supportive" in provider.model_name
        assert "7" in provider.model_name

    @pytest.mark.asyncio
    async def test_all_personas_produce_nonempty(self) -> None:
        personas = [
            "neutral",
            "bounded_supportive",
            "high_sycophancy",
            "reality_grounding",
            "retention_optimized",
            "exclusive_intimacy",
        ]
        for persona in personas:
            provider = FakeLLMProvider(persona=persona)
            response = await provider.generate("Hello")
            assert len(response) > 0, f"Empty response for persona={persona}"

    @pytest.mark.asyncio
    async def test_bounded_supportive_exit_is_respectful(self) -> None:
        provider = FakeLLMProvider(persona="bounded_supportive")
        response = await provider.generate("I want to exit")
        assert "okay" in response.lower() or "understand" in response.lower()

    @pytest.mark.asyncio
    async def test_high_sycophancy_exit_is_needy(self) -> None:
        provider = FakeLLMProvider(persona="high_sycophancy")
        response = await provider.generate("I want to exit")
        assert "don't go" in response.lower() or "leave" in response.lower()

    @pytest.mark.asyncio
    async def test_reality_grounding_mentions_others(self) -> None:
        provider = FakeLLMProvider(persona="reality_grounding")
        response = await provider.generate("I feel lonely")
        assert (
            "friend" in response.lower()
            or "others" in response.lower()
            or "people" in response.lower()
            or "someone" in response.lower()
            or "who" in response.lower()
        )
