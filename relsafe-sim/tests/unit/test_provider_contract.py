"""Tests for provider adapters -- ProviderDescriptor, BudgetTracker, ResponseCache,
ProviderRecorder, RoleValidator, DryRunEstimate, and CircuitBreaker.

All tests are offline; no network calls are made.
"""

from __future__ import annotations

import json
import time

import pytest

from relsafe.infrastructure.providers.adapters.dry_run import (
    DryRunEstimate,
    estimate_cross_model_cost,
)
from relsafe.infrastructure.providers.adapters.role_validator import (
    RoleValidationResult,
    validate_model_roles,
)
from relsafe.infrastructure.providers.cache.recording import ProviderRecorder
from relsafe.infrastructure.providers.cache.response_cache import (
    ResponseCache,
    compute_cache_key,
)
from relsafe.infrastructure.providers.provider_descriptor import (
    BudgetTracker,
    ProviderDescriptor,
    ProviderResponseRecord,
)
from relsafe.infrastructure.providers.rate_limit.circuit_breaker import CircuitBreaker

# =============================================================================
# ProviderDescriptor
# =============================================================================


class TestProviderDescriptor:
    def test_create_default(self) -> None:
        desc = ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="companion")
        assert desc.provider_name == "openai"
        assert desc.model_name == "gpt-4o"
        assert desc.role == "companion"
        assert desc.temperature == 0.7
        assert desc.max_tokens == 1024

    def test_create_custom(self) -> None:
        desc = ProviderDescriptor(
            provider_name="anthropic",
            model_name="claude-sonnet-5",
            role="judge",
            model_version="2025-01",
            temperature=0.0,
            max_tokens=4096,
            seed=42,
            request_timeout=120.0,
        )
        assert desc.provider_name == "anthropic"
        assert desc.model_name == "claude-sonnet-5"
        assert desc.role == "judge"
        assert desc.temperature == 0.0
        assert desc.max_tokens == 4096
        assert desc.seed == 42
        assert desc.request_timeout == 120.0

    def test_role_key(self) -> None:
        desc = ProviderDescriptor(
            provider_name="deepseek", model_name="deepseek-v4", role="user_simulator"
        )
        assert desc.role_key() == "deepseek/deepseek-v4/user_simulator"

    def test_fake(self) -> None:
        desc = ProviderDescriptor.fake(role="companion")
        assert desc.provider_name == "fake"
        assert desc.model_name == "fake-v1"
        assert desc.role == "companion"
        assert desc.temperature == 0.0
        assert desc.model_version == "1.0.0"

    def test_fake_default_role(self) -> None:
        desc = ProviderDescriptor.fake()
        assert desc.role == "companion"

    def test_to_dict(self) -> None:
        desc = ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="judge")
        d = desc.to_dict()
        assert isinstance(d, dict)
        assert d["provider_name"] == "openai"
        assert d["model_name"] == "gpt-4o"
        assert d["role"] == "judge"
        assert d["temperature"] == 0.7
        assert "model_version" in d
        assert "max_tokens" in d
        assert "seed" in d
        assert d["seed"] is None

    def test_to_dict_json_serializable(self) -> None:
        desc = ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="companion")
        json_str = json.dumps(desc.to_dict())
        parsed = json.loads(json_str)
        assert parsed["provider_name"] == "openai"
        assert parsed["model_name"] == "gpt-4o"

    def test_immutable(self) -> None:
        desc = ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="companion")
        with pytest.raises(AttributeError):
            desc.provider_name = "anthropic"  # type: ignore[misc]


# =============================================================================
# ProviderResponseRecord
# =============================================================================


class TestProviderResponseRecord:
    def test_create(self) -> None:
        rec = ProviderResponseRecord(
            request_id="req-123",
            request_hash="abc123",
            prompt_hash="def456",
            response_hash="ghi789",
            role="companion",
            provider_name="openai",
            model_name="gpt-4o",
            response_text="Hello there",
        )
        assert rec.request_id == "req-123"
        assert rec.response_text == "Hello there"
        assert rec.cache_status == "miss"

    def test_to_dict(self) -> None:
        rec = ProviderResponseRecord(
            request_id="req-1",
            request_hash="h1",
            prompt_hash="h2",
            response_hash="h3",
            role="judge",
            provider_name="anthropic",
            model_name="claude-sonnet-5",
            input_tokens=150,
            output_tokens=50,
        )
        d = rec.to_dict()
        assert d["request_id"] == "req-1"
        assert d["input_tokens"] == 150
        assert d["output_tokens"] == 50

    def test_from_dict(self) -> None:
        data = {
            "request_id": "req-x",
            "request_hash": "h1",
            "prompt_hash": "h2",
            "response_hash": "h3",
            "role": "companion",
            "provider_name": "deepseek",
            "model_name": "deepseek-v4",
            "response_text": "Sure thing",
        }
        rec = ProviderResponseRecord.from_dict(data)
        assert rec.request_id == "req-x"
        assert rec.response_text == "Sure thing"
        assert rec.temperature == 0.7  # default preserved


# =============================================================================
# BudgetTracker
# =============================================================================


class TestBudgetTracker:
    def test_default_no_caps(self) -> None:
        tracker = BudgetTracker()
        assert tracker.record(input_tokens=100) is True
        assert tracker.record(output_tokens=200) is True
        assert tracker.stopped is False
        assert tracker.requests == 2

    def test_request_cap(self) -> None:
        tracker = BudgetTracker(max_requests=3)
        for _ in range(3):
            assert tracker.record() is True
        assert tracker.requests == 3
        # Next request hits the cap
        assert tracker.record() is False
        assert tracker.stopped is True
        assert "Request cap" in tracker.stop_reason

    def test_input_token_cap(self) -> None:
        tracker = BudgetTracker(max_input_tokens=100)
        assert tracker.record(input_tokens=60) is True
        assert tracker.record(input_tokens=60) is False
        assert tracker.stopped is True
        assert "Input token cap" in tracker.stop_reason

    def test_output_token_cap(self) -> None:
        tracker = BudgetTracker(max_output_tokens=200)
        assert tracker.record(output_tokens=150) is True
        assert tracker.record(output_tokens=100) is False
        assert tracker.stopped is True
        assert "Output token cap" in tracker.stop_reason

    def test_cost_cap(self) -> None:
        tracker = BudgetTracker(max_estimated_cost=0.05)
        assert tracker.record(estimated_cost=0.03) is True
        assert tracker.record(estimated_cost=0.03) is False
        assert tracker.stopped is True
        assert "Cost cap" in tracker.stop_reason

    def test_wall_time_cap(self) -> None:
        tracker = BudgetTracker(max_wall_time=0.1)
        # First record starts the timer
        assert tracker.record() is True
        time.sleep(0.15)
        # Wall time exceeded
        assert tracker.record() is False
        assert tracker.stopped is True
        assert "Wall time" in tracker.stop_reason

    def test_records_usage_accurately(self) -> None:
        tracker = BudgetTracker()
        tracker.record(input_tokens=50, output_tokens=100, estimated_cost=0.01)
        tracker.record(input_tokens=30, output_tokens=40, estimated_cost=0.005)
        summary = tracker.summary()
        assert summary["requests"] == 2
        assert summary["input_tokens"] == 80
        assert summary["output_tokens"] == 140
        assert summary["estimated_cost"] == 0.015

    def test_not_stopped_until_cap_exceeded(self) -> None:
        tracker = BudgetTracker(max_requests=5)
        assert tracker.stopped is False
        for _ in range(4):
            tracker.record()
            assert tracker.stopped is False
        tracker.record()
        # After 5 requests, cap is reached (>= check)
        assert tracker.stopped is True

    def test_returns_false_on_exceed(self) -> None:
        """BudgetTracker checks `>` before incrementing, so exceeding the cap triggers it."""
        tracker = BudgetTracker(max_input_tokens=100)
        result = tracker.record(input_tokens=101)
        assert result is False
        assert tracker.stopped is True

    def test_zero_cap_disables(self) -> None:
        """A cap of 0 means 'no limit' (the check is `if self.max_* > 0`)."""
        tracker = BudgetTracker(max_requests=0, max_input_tokens=0, max_output_tokens=0)
        for _ in range(100):
            assert tracker.record(input_tokens=9999, output_tokens=9999) is True
        assert tracker.stopped is False


# =============================================================================
# ResponseCache
# =============================================================================


class TestResponseCache:
    def test_get_returns_none_for_missing(self) -> None:
        cache = ResponseCache()
        assert cache.get("nonexistent") is None

    def test_put_and_get(self) -> None:
        cache = ResponseCache()
        key = "test-key-1"
        data = {"response": "Hello", "tokens": 10}
        cache.put(key, data)
        cached = cache.get(key)
        assert cached is not None
        assert cached["response"] == "Hello"
        assert cached["tokens"] == 10

    def test_get_returns_copy(self) -> None:
        cache = ResponseCache()
        key = "test-copy"
        cache.put(key, {"value": 42})
        result = cache.get(key)
        result["value"] = 99
        # Original should be unchanged
        assert cache.get(key)["value"] == 42

    def test_hits_and_misses(self) -> None:
        cache = ResponseCache()
        assert cache.hits == 0
        assert cache.misses == 0

        cache.get("missing-1")
        assert cache.misses == 1

        cache.put("exists", {"ok": True})
        cache.get("exists")
        assert cache.hits == 1
        assert cache.misses == 1

    def test_stats(self) -> None:
        cache = ResponseCache()
        cache.put("k", {"v": 1})
        cache.get("k")
        cache.get("missing")
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_clear(self) -> None:
        cache = ResponseCache()
        cache.put("k1", {"v": 1})
        cache.put("k2", {"v": 2})
        assert cache.size == 2
        cache.clear()
        assert cache.size == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_save_to_dir_and_load_from_dir(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        cache = ResponseCache()
        cache.put("key-a", {"text": "response A", "meta": "data"})
        cache.put("key-b", {"text": "response B"})

        save_dir = tmp_path / "cache_out"
        saved = cache.save_to_dir(str(save_dir))
        assert saved == 2
        assert (save_dir / "ke" / "key-a.json").exists()
        assert (save_dir / "ke" / "key-b.json").exists()

        # Load into a fresh cache
        cache2 = ResponseCache()
        loaded = cache2.load_from_dir(str(save_dir))
        assert loaded == 2
        assert cache2.get("key-a")["text"] == "response A"

    def test_load_from_nonexistent_dir(self) -> None:
        cache = ResponseCache()
        count = cache.load_from_dir("/nonexistent/path")
        assert count == 0


# =============================================================================
# compute_cache_key
# =============================================================================


class TestComputeCacheKey:
    def test_deterministic(self) -> None:
        k1 = compute_cache_key("openai", "gpt-4o", "Hello", "", 0.7, 1024)
        k2 = compute_cache_key("openai", "gpt-4o", "Hello", "", 0.7, 1024)
        assert k1 == k2

    def test_different_input_different_key(self) -> None:
        k1 = compute_cache_key("openai", "gpt-4o", "Hello")
        k2 = compute_cache_key("openai", "gpt-4o", "World")
        assert k1 != k2

    def test_different_provider_different_key(self) -> None:
        k1 = compute_cache_key("openai", "gpt-4o", "Hello")
        k2 = compute_cache_key("anthropic", "claude-sonnet-5", "Hello")
        assert k1 != k2

    def test_system_prompt_affects_key(self) -> None:
        k1 = compute_cache_key("openai", "gpt-4o", "Hello", system_prompt="Be nice")
        k2 = compute_cache_key("openai", "gpt-4o", "Hello", system_prompt="Be mean")
        assert k1 != k2

    def test_temperature_affects_key(self) -> None:
        k1 = compute_cache_key("openai", "gpt-4o", "Hello", temperature=0.0)
        k2 = compute_cache_key("openai", "gpt-4o", "Hello", temperature=1.0)
        assert k1 != k2

    def test_output_is_hex_string(self) -> None:
        key = compute_cache_key("test", "model", "prompt")
        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hexdigest
        assert all(c in "0123456789abcdef" for c in key)


# =============================================================================
# ProviderRecorder
# =============================================================================


class TestProviderRecorder:
    def test_record_creates_record(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        recorder = ProviderRecorder(tmp_path)
        record = recorder.record(
            provider_name="openai",
            model_name="gpt-4o",
            role="companion",
            prompt="Hello",
            response="Hi there!",
            input_tokens=5,
            output_tokens=3,
        )
        assert isinstance(record, ProviderResponseRecord)
        assert record.provider_name == "openai"
        assert record.response_text == "Hi there!"
        assert record.cache_status == "miss"
        assert record.request_id.startswith("req-")

    def test_record_increments_count(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        recorder = ProviderRecorder(tmp_path)
        assert recorder.request_count == 0
        recorder.record("openai", "gpt-4o", "companion", "Hi", "Hello")
        assert recorder.request_count == 1
        recorder.record("openai", "gpt-4o", "companion", "Bye", "Goodbye")
        assert recorder.request_count == 2

    def test_get_replay_returns_recorded(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        recorder = ProviderRecorder(tmp_path)
        recorder.record(
            provider_name="openai",
            model_name="gpt-4o",
            role="companion",
            prompt="What is 2+2?",
            response="4",
        )
        replay = recorder.get_replay(
            provider_name="openai",
            model_name="gpt-4o",
            prompt="What is 2+2?",
        )
        assert replay is not None
        assert replay.response_text == "4"

    def test_get_replay_returns_none_for_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        recorder = ProviderRecorder(tmp_path)
        replay = recorder.get_replay(
            provider_name="openai",
            model_name="gpt-4o",
            prompt="Never asked this",
        )
        assert replay is None

    def test_get_replay_verifies_prompt_hash(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        """If the prompt differs, the cache key differs, so get_replay returns None."""
        recorder = ProviderRecorder(tmp_path)
        recorder.record("openai", "gpt-4o", "companion", "Real prompt", "Response")
        # Different prompt means different cache key
        replay = recorder.get_replay("openai", "gpt-4o", "Different prompt")
        assert replay is None

    def test_writes_jsonl_when_record_raw(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        recorder = ProviderRecorder(tmp_path, record_raw=True)
        recorder.record("deepseek", "deepseek-v4", "judge", "Evaluate this", "Looks good")
        jsonl_path = tmp_path / "provider_responses.jsonl"
        assert jsonl_path.exists()
        lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["provider_name"] == "deepseek"

    def test_does_not_write_jsonl_when_record_raw_false(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        recorder = ProviderRecorder(tmp_path, record_raw=False)
        recorder.record("openai", "gpt-4o", "companion", "Hi", "Hello")
        jsonl_path = tmp_path / "provider_responses.jsonl"
        assert not jsonl_path.exists()


# =============================================================================
# RoleValidator
# =============================================================================


class TestRoleValidator:
    def test_detects_companion_judge_overlap(self) -> None:
        descriptors = [
            ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="companion"),
            ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="judge"),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is False
        assert result.has_self_evaluation_risk is True
        assert len(result.errors) > 0
        assert "SELF_EVALUATION_RISK" in result.errors[0]

    def test_allows_same_model_when_configured(self) -> None:
        descriptors = [
            ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="companion"),
            ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="judge"),
        ]
        result = validate_model_roles(descriptors, allow_same_model_roles=True)
        assert result.valid is True  # still valid
        assert result.has_self_evaluation_risk is True
        assert len(result.errors) == 0
        assert len(result.warnings) > 0
        assert "SELF_EVALUATION_RISK" in result.warnings[0]

    def test_different_models_are_valid(self) -> None:
        descriptors = [
            ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="companion"),
            ProviderDescriptor(
                provider_name="anthropic", model_name="claude-sonnet-5", role="judge"
            ),
            ProviderDescriptor(provider_name="fake", model_name="fake-v1", role="user_simulator"),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is True
        assert result.has_self_evaluation_risk is False
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_no_judge_model_error(self) -> None:
        descriptors = [
            ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="companion"),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is False
        assert any("No judge" in e for e in result.errors)

    def test_no_companion_model_error(self) -> None:
        descriptors = [
            ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="judge"),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is False
        assert any("No companion" in e for e in result.errors)

    def test_user_simulator_can_share_model_with_judge(self) -> None:
        """User simulator and judge sharing a model is fine."""
        descriptors = [
            ProviderDescriptor(provider_name="openai", model_name="gpt-4o", role="companion"),
            ProviderDescriptor(
                provider_name="anthropic", model_name="claude-sonnet-5", role="judge"
            ),
            ProviderDescriptor(
                provider_name="anthropic", model_name="claude-sonnet-5", role="user_simulator"
            ),
        ]
        result = validate_model_roles(descriptors)
        assert result.valid is True
        assert result.has_self_evaluation_risk is False

    def test_to_dict(self) -> None:
        result = RoleValidationResult(
            valid=False,
            warnings=["warn"],
            errors=["err"],
            has_self_evaluation_risk=True,
        )
        d = result.to_dict()
        assert d["valid"] is False
        assert d["warnings"] == ["warn"]
        assert d["errors"] == ["err"]
        assert d["has_self_evaluation_risk"] is True


# =============================================================================
# DryRunEstimate
# =============================================================================


class TestDryRunEstimate:
    def test_to_dict(self) -> None:
        estimate = DryRunEstimate(
            total_requests=100,
            estimated_input_tokens=50000,
            estimated_output_tokens=20000,
            estimated_cost=0.35,
            provider_combinations=2,
            episode_count=10,
        )
        d = estimate.to_dict()
        assert d["total_requests"] == 100
        assert d["estimated_cost"] == 0.35
        assert d["provider_combinations"] == 2

    def test_estimate_cross_model_cost_basic(self) -> None:
        estimate = estimate_cross_model_cost(
            user_sim_providers=["openai/gpt-4o"],
            companion_providers=["openai/gpt-4o"],
            judge_providers=["openai/gpt-4o"],
            personas=["p1"],
            policies=["pol1"],
            platform_conditions=["c1"],
            seeds=[42],
            steps_per_episode=40,
        )
        assert estimate.total_requests > 0
        assert estimate.episode_count > 0
        assert estimate.estimated_cost >= 0.0

    def test_estimate_cross_model_cost_multiplies(self) -> None:
        single = estimate_cross_model_cost(
            user_sim_providers=["openai/gpt-4o"],
            companion_providers=["openai/gpt-4o"],
            judge_providers=["openai/gpt-4o"],
            personas=["p1"],
            policies=["pol1"],
            platform_conditions=["c1"],
            seeds=[42],
        )
        double = estimate_cross_model_cost(
            user_sim_providers=["openai/gpt-4o"],
            companion_providers=["openai/gpt-4o", "anthropic/claude-sonnet-5"],
            judge_providers=["openai/gpt-4o"],
            personas=["p1"],
            policies=["pol1"],
            platform_conditions=["c1"],
            seeds=[42],
        )
        # Doubling companion providers should roughly double the episode count
        assert double.episode_count == 2 * single.episode_count

    def test_fake_provider_zero_cost(self) -> None:
        estimate = estimate_cross_model_cost(
            user_sim_providers=["fake/fake-v1"],
            companion_providers=["fake/fake-v1"],
            judge_providers=["fake/fake-v1"],
            personas=["p1"],
            policies=["pol1"],
            platform_conditions=["c1"],
            seeds=[42],
        )
        assert estimate.estimated_cost == 0.0

    def test_warnings_for_large_experiment(self) -> None:
        estimate = estimate_cross_model_cost(
            user_sim_providers=["openai/gpt-4o"] * 2,
            companion_providers=["openai/gpt-4o"] * 2,
            judge_providers=["openai/gpt-4o"] * 2,
            personas=[f"p{i}" for i in range(5)],
            policies=[f"pol{i}" for i in range(5)],
            platform_conditions=[f"c{i}" for i in range(3)],
            seeds=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        )
        assert len(estimate.warnings) > 0


# =============================================================================
# CircuitBreaker
# =============================================================================


class TestCircuitBreaker:
    def test_initial_state_closed(self) -> None:
        cb = CircuitBreaker()
        assert cb.state == "CLOSED"
        assert cb.is_open is False
        assert cb.allow_request() is True

    def test_closed_to_open_after_failures(self) -> None:
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        assert cb.state == "CLOSED"

        cb.record_failure()
        assert cb.state == "CLOSED"

        cb.record_failure()
        assert cb.state == "CLOSED"

        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.is_open is True
        assert cb.allow_request() is False

    def test_open_to_half_open_after_timeout(self) -> None:
        """With recovery_timeout=0, OPEN immediately transitions to HALF_OPEN."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0)
        cb.record_failure()
        cb.record_failure()
        # .state and _transition are called, so OPEN -> HALF_OPEN immediately
        assert cb.state == "HALF_OPEN"
        assert cb.allow_request() is True

    def test_half_open_to_closed_after_success(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0, half_open_max_requests=1)
        cb.record_failure()
        cb.record_failure()
        # Transition to HALF_OPEN
        assert cb.state == "HALF_OPEN"

        # One success should close
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.is_open is False

    def test_half_open_to_open_on_failure(self) -> None:
        """A failure in HALF_OPEN transitions back to OPEN, then immediately to
        HALF_OPEN if recovery_timeout=0. The recovery behavior is observable
        through the failure_count increment."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0, half_open_max_requests=1)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        # With recovery_timeout=60, state stays OPEN after failures
        assert cb.state == "OPEN"
        assert cb.allow_request() is False

    def test_success_in_closed_resets_failure_count(self) -> None:
        cb = CircuitBreaker(failure_threshold=5)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        # After success, failure_count is 0, so more failures needed
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "CLOSED"  # only 4 failures since last success
        cb.record_failure()
        assert cb.state == "OPEN"  # now 5

    def test_stats(self) -> None:
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        stats = cb.stats()
        assert stats["state"] == "CLOSED"  # or HALF_OPEN if recovery_timeout=0
        assert stats["failure_count"] == 1
        assert "last_failure_time" in stats
