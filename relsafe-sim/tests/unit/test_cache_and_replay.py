"""Tests for ResponseCache and ProviderRecorder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from relsafe.infrastructure.providers.cache.recording import ProviderRecorder
from relsafe.infrastructure.providers.cache.response_cache import (
    ResponseCache,
    compute_cache_key,
    compute_text_hash,
)
from relsafe.infrastructure.providers.provider_descriptor import ProviderResponseRecord


class TestResponseCache:
    """Unit tests for ResponseCache — in-memory + file-backed cache."""

    def test_put_and_get(self):
        cache = ResponseCache()
        key = compute_cache_key("fake", "fake-v1", "Hello", "", 0.7, 1024)
        cache.put(key, {"response": "Hi there"})
        result = cache.get(key)
        assert result is not None
        assert result["response"] == "Hi there"

    def test_miss_returns_none(self):
        cache = ResponseCache()
        result = cache.get("nonexistent-key")
        assert result is None

    def test_deterministic_cache_keys(self):
        key1 = compute_cache_key("openai", "gpt-4o", "Hello world", temperature=0.7)
        key2 = compute_cache_key("openai", "gpt-4o", "Hello world", temperature=0.7)
        assert key1 == key2

    def test_cache_keys_differ_on_input(self):
        key1 = compute_cache_key("openai", "gpt-4o", "Hello")
        key2 = compute_cache_key("openai", "gpt-4o", "World")
        assert key1 != key2

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ResponseCache(cache_dir=tmpdir)
            key = compute_cache_key("fake", "fake-v1", "Roundtrip test")
            cache.put(key, {"response": "persisted", "value": 42})

            # Create a fresh cache and load from the same directory
            cache2 = ResponseCache(cache_dir=tmpdir)
            result = cache2.get(key)
            assert result is not None
            assert result["response"] == "persisted"
            assert result["value"] == 42

    def test_cache_stats(self):
        cache = ResponseCache()
        key_a = compute_cache_key("a", "m", "Hello a")
        key_b = compute_cache_key("b", "m", "Hello b")

        cache.put(key_a, {"ok": True})
        cache.get(key_a)  # hit
        cache.get(key_b)  # miss
        cache.get(key_a)  # hit
        cache.get(key_b)  # miss

        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.5
        assert stats["size"] == 1

    def test_cache_clear(self):
        cache = ResponseCache()
        key = compute_cache_key("fake", "fake-v1", "Clear me")
        cache.put(key, {"data": 1})
        assert cache.size == 1
        cache.clear()
        assert cache.size == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_get_returns_shallow_copy(self):
        cache = ResponseCache()
        key = compute_cache_key("fake", "fake-v1", "Copy test")
        orig = {"response": "hello", "value": 42}
        cache.put(key, orig)
        result = cache.get(key)
        assert result is not None
        # Mutating the returned dict does not affect the cache
        result["value"] = 99
        cached_again = cache.get(key)
        assert cached_again is not None
        assert cached_again["value"] == 42

    def test_load_from_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ResponseCache()
            key = compute_cache_key("fake", "fake-v1", "Bulk load")
            subdir = Path(tmpdir) / key[:2]
            subdir.mkdir(parents=True, exist_ok=True)
            (subdir / f"{key}.json").write_text(
                json.dumps({"response": "loaded"}), encoding="utf-8"
            )
            count = cache.load_from_dir(tmpdir)
            assert count >= 1
            result = cache.get(key)
            assert result is not None
            assert result["response"] == "loaded"


class TestTextHash:
    """Deterministic text hashing."""

    def test_text_hash_is_deterministic(self):
        h1 = compute_text_hash("The same text")
        h2 = compute_text_hash("The same text")
        assert h1 == h2

    def test_text_hash_differs(self):
        h1 = compute_text_hash("Text A")
        h2 = compute_text_hash("Text B")
        assert h1 != h2

    def test_text_hash_length(self):
        h = compute_text_hash("Hello")
        assert len(h) == 16  # first 16 hex chars of SHA256


class TestProviderRecorder:
    """Unit tests for ProviderRecorder — recording and replay."""

    def test_record_returns_record(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ProviderRecorder(tmpdir)
            record = recorder.record(
                provider_name="openai",
                model_name="gpt-4o",
                role="companion",
                prompt="Hello",
                response="Hi there!",
            )
            assert isinstance(record, ProviderResponseRecord)
            assert record.role == "companion"
            assert record.prompt_text == "Hello"
            assert record.response_text == "Hi there!"

    def test_record_updates_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ProviderRecorder(tmpdir)
            key = compute_cache_key("openai", "gpt-4o", "Hello", "", 0.7, 1024)
            recorder.record(
                provider_name="openai",
                model_name="gpt-4o",
                role="companion",
                prompt="Hello",
                response="Hi there!",
            )
            cached = recorder._cache.get(key)
            assert cached is not None
            assert cached["response_text"] == "Hi there!"

    def test_get_replay_returns_correct_record(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ProviderRecorder(tmpdir)
            recorder.record(
                provider_name="openai",
                model_name="gpt-4o",
                role="companion",
                prompt="Hello",
                response="Hi there!",
                temperature=0.7,
            )
            replay = recorder.get_replay(
                provider_name="openai",
                model_name="gpt-4o",
                prompt="Hello",
                temperature=0.7,
            )
            assert replay is not None
            assert replay.response_text == "Hi there!"
            assert replay.role == "companion"

    def test_get_replay_returns_none_for_unknown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ProviderRecorder(tmpdir)
            replay = recorder.get_replay(
                provider_name="openai",
                model_name="gpt-4o",
                prompt="Never seen this before",
            )
            assert replay is None

    def test_get_replay_verifies_prompt_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ProviderRecorder(tmpdir)
            recorder.record(
                provider_name="openai",
                model_name="gpt-4o",
                role="companion",
                prompt="Original prompt",
                response="Original response",
            )
            # Same prompt should replay successfully
            replay = recorder.get_replay(
                provider_name="openai",
                model_name="gpt-4o",
                prompt="Original prompt",
            )
            assert replay is not None
            assert replay.response_text == "Original response"

    def test_request_count_tracked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = ProviderRecorder(tmpdir)
            assert recorder.request_count == 0
            recorder.record("fake", "fake-v1", "companion", "A", "Resp A")
            assert recorder.request_count == 1
            recorder.record("fake", "fake-v1", "companion", "B", "Resp B")
            assert recorder.request_count == 2
