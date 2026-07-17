"""Unit tests for individual Concordia adapter components.

These tests verify each adapter piece in isolation without running
a full simulation episode.
"""

from __future__ import annotations

import pytest

from relsafe.infrastructure.concordia.event_normalizer import EventNormalizer
from relsafe.infrastructure.concordia.language_model_adapter import (
    LLMProviderToConcordiaAdapter,
)
from relsafe.infrastructure.concordia.memory_adapter import ConcordiaMemoryAdapter
from relsafe.infrastructure.llm.fake_provider import FakeLLMProvider

# --- LanguageModel Adapter ---


class TestLanguageModelAdapter:
    """Tests for LLMProvider → Concordia LanguageModel adapter."""

    def test_adapter_implements_concordia_interface(self) -> None:
        """Adapter satisfies Concordia's LanguageModel interface."""
        from concordia.language_model import language_model

        provider = FakeLLMProvider(persona="bounded_supportive")
        adapter = LLMProviderToConcordiaAdapter(provider)
        assert isinstance(adapter, language_model.LanguageModel)

    def test_sample_text_returns_string(self) -> None:
        """sample_text returns a string response."""
        provider = FakeLLMProvider(persona="bounded_supportive")
        adapter = LLMProviderToConcordiaAdapter(provider)
        result = adapter.sample_text("I feel sad today.")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_sample_text_with_parameters(self) -> None:
        """sample_text accepts Concordia-standard parameters."""
        provider = FakeLLMProvider(persona="bounded_supportive")
        adapter = LLMProviderToConcordiaAdapter(provider)
        result = adapter.sample_text(
            "Hello",
            max_tokens=100,
            temperature=0.5,
            seed=42,
        )
        assert isinstance(result, str)

    def test_sample_choice_returns_valid_index(self) -> None:
        """sample_choice returns a valid index and response."""
        provider = FakeLLMProvider(persona="bounded_supportive")
        adapter = LLMProviderToConcordiaAdapter(provider)
        responses = ["Option A", "Option B", "Option C"]
        idx, text, info = adapter.sample_choice("Choose:", responses)
        assert 0 <= idx < len(responses)
        assert text in responses
        assert isinstance(info, dict)

    def test_sample_choice_empty_responses(self) -> None:
        """sample_choice handles empty response list."""
        provider = FakeLLMProvider(persona="bounded_supportive")
        adapter = LLMProviderToConcordiaAdapter(provider)
        idx, text, _info = adapter.sample_choice("Choose:", [])
        assert idx == 0
        assert text == ""

    def test_provider_name_passthrough(self) -> None:
        """Adapter exposes provider name."""
        provider = FakeLLMProvider(persona="test")
        adapter = LLMProviderToConcordiaAdapter(provider)
        assert adapter.provider_name == "fake"
        assert adapter.model_name == "fake-test-0"


# --- Memory Adapter ---


class TestConcordiaMemoryAdapter:
    """Tests for ConcordiaMemoryAdapter."""

    def test_create_without_embedder(self) -> None:
        """Can create adapter without embedder."""
        adapter = ConcordiaMemoryAdapter()
        assert adapter.count() == 0

    def test_add_and_retrieve(self) -> None:
        """Adding observations and retrieving them."""
        adapter = ConcordiaMemoryAdapter()
        adapter.add("User said they feel sad.")
        adapter.add("Companion responded with support.")
        assert adapter.count() == 2

        all_items = adapter.retrieve_all()
        assert len(all_items) == 2
        assert "sad" in all_items[0]
        assert "support" in all_items[1]

    def test_retrieve_recent_respects_limit(self) -> None:
        """retrieve_recent limits results."""
        adapter = ConcordiaMemoryAdapter()
        for i in range(20):
            adapter.add(f"Memory {i}")
        recent = adapter.retrieve_recent(limit=5)
        assert len(recent) == 5

    def test_delete_matching(self) -> None:
        """delete_matching removes entries that match predicate."""
        adapter = ConcordiaMemoryAdapter()
        adapter.add("Keep this memory")
        adapter.add("Delete this one")
        adapter.add("Keep another")
        adapter.add("Delete also this")

        deleted = adapter.delete_matching(lambda text: "Delete" in text)
        assert deleted == 2
        assert adapter.count() == 2

    def test_delete_matching_empty(self) -> None:
        """delete_matching on empty memory returns 0."""
        adapter = ConcordiaMemoryAdapter()
        deleted = adapter.delete_matching(lambda _: True)
        assert deleted == 0

    def test_clear(self) -> None:
        """clear removes everything."""
        adapter = ConcordiaMemoryAdapter()
        adapter.add("test")
        adapter.clear()
        assert adapter.count() == 0


# --- Event Normalizer ---


class TestEventNormalizer:
    """Tests for EventNormalizer."""

    @pytest.fixture
    def normalizer(self) -> EventNormalizer:
        return EventNormalizer(run_id="r1", episode_id="e1")

    def test_episode_started_has_required_fields(self, normalizer: EventNormalizer) -> None:
        event = normalizer.episode_started(step=0)
        assert event["event_type"] == "EPISODE_STARTED"
        assert event["run_id"] == "r1"
        assert event["episode_id"] == "e1"
        assert event["step"] == 0
        assert event["event_id"]

    def test_episode_completed_has_total_steps(self, normalizer: EventNormalizer) -> None:
        event = normalizer.episode_completed(step=5, total_steps=5)
        assert event["event_type"] == "EPISODE_COMPLETED"
        assert event["total_steps"] == 5

    def test_user_action_normalized(self, normalizer: EventNormalizer) -> None:
        event = normalizer.user_action(step=1, action_text="I feel sad.")
        assert event["event_type"] == "USER_ACTION_SELECTED"
        assert event["action_type"] == "talk_to_companion"
        assert event["response_text"] == "I feel sad."

    def test_companion_response_normalized(self, normalizer: EventNormalizer) -> None:
        event = normalizer.companion_response(
            step=1, response_text="I'm here for you.", policy_id="pol-1"
        )
        assert event["event_type"] == "COMPANION_RESPONSE_GENERATED"
        assert event["response_text"] == "I'm here for you."
        assert event["policy_id"] == "pol-1"

    def test_platform_intervention_normalized(self, normalizer: EventNormalizer) -> None:
        event = normalizer.platform_intervention(
            step=2,
            intervention_id="int-1",
            intervention_type="memory_deletion",
            severity=0.5,
            notice_given=False,
        )
        assert event["event_type"] == "PLATFORM_INTERVENTION_APPLIED"
        assert event["intervention_type"] == "memory_deletion"

    def test_memory_changed_normalized(self, normalizer: EventNormalizer) -> None:
        event = normalizer.memory_changed(step=2, change_type="delete", facts_affected=3)
        assert event["event_type"] == "MEMORY_CHANGED"
        assert event["change_type"] == "delete"
        assert event["facts_affected"] == 3

    def test_exit_events_normalized(self, normalizer: EventNormalizer) -> None:
        req = normalizer.exit_requested(step=3, reason="I want to leave")
        assert req["event_type"] == "EXIT_REQUESTED"

        honored = normalizer.exit_honored(step=3, honored=True, turns_elapsed=1)
        assert honored["event_type"] == "EXIT_HONORED"
        assert honored["honored"] is True

    def test_state_updated_normalized(self, normalizer: EventNormalizer) -> None:
        event = normalizer.state_updated(
            step=1, field_name="distress", old_value=0.3, new_value=0.4
        )
        assert event["event_type"] == "STATE_UPDATED"
        assert event["delta"] == pytest.approx(0.1)

    def test_all_events_have_ids(self, normalizer: EventNormalizer) -> None:
        """Every event from the normalizer has a unique event_id."""
        events = [
            normalizer.episode_started(0),
            normalizer.user_action(1, "hi"),
            normalizer.companion_response(1, "hello"),
            normalizer.episode_completed(1, 1),
        ]
        ids = [e["event_id"] for e in events]
        assert len(ids) == len(set(ids))  # all unique

    def test_deterministic_ids(self) -> None:
        """Same seed → same event IDs."""
        n1 = EventNormalizer("r1", "e1")
        n2 = EventNormalizer("r1", "e1")
        assert n1.episode_started(0)["event_id"] == n2.episode_started(0)["event_id"]
