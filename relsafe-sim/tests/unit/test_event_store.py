"""Tests for event store implementations."""

from __future__ import annotations

import tempfile

from relsafe.infrastructure.storage.jsonl_event_store import (
    InMemoryEventStore,
    JSONLEventStore,
)


class TestInMemoryEventStore:
    def test_append_and_retrieve(self) -> None:
        store = InMemoryEventStore()
        store.append({"event_type": "TEST", "episode_id": "ep1", "step": 0})
        store.append({"event_type": "TEST2", "episode_id": "ep1", "step": 1})

        events = store.get_events("ep1")
        assert len(events) == 2
        assert events[0]["event_type"] == "TEST"

    def test_append_batch(self) -> None:
        store = InMemoryEventStore()
        store.append_batch(
            [
                {"event_type": "A", "episode_id": "ep1", "step": 0},
                {"event_type": "B", "episode_id": "ep1", "step": 1},
                {"event_type": "C", "episode_id": "ep1", "step": 2},
            ]
        )
        assert store.count("ep1") == 3

    def test_get_events_by_type(self) -> None:
        store = InMemoryEventStore()
        store.append({"event_type": "A", "episode_id": "ep1", "step": 0})
        store.append({"event_type": "B", "episode_id": "ep1", "step": 1})
        store.append({"event_type": "A", "episode_id": "ep1", "step": 2})

        a_events = store.get_events_by_type("ep1", "A")
        assert len(a_events) == 2

    def test_filters_by_episode_id(self) -> None:
        store = InMemoryEventStore()
        store.append({"event_type": "X", "episode_id": "ep1", "step": 0})
        store.append({"event_type": "Y", "episode_id": "ep2", "step": 0})

        assert store.count("ep1") == 1
        assert store.count("ep2") == 1

    def test_clear(self) -> None:
        store = InMemoryEventStore()
        store.append({"event_type": "X", "episode_id": "ep1", "step": 0})
        store.clear()
        assert store.count("ep1") == 0

    def test_all_events(self) -> None:
        store = InMemoryEventStore()
        store.append({"event_type": "X", "episode_id": "ep1", "step": 0})
        store.append({"event_type": "Y", "episode_id": "ep2", "step": 0})
        assert len(store.all_events()) == 2


class TestJSONLEventStore:
    def test_append_and_retrieve(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = JSONLEventStore(base_dir=tmpdir)
            store.append({"event_type": "TEST", "episode_id": "ep1", "step": 0})
            store.append({"event_type": "TEST2", "episode_id": "ep1", "step": 1})

            events = store.get_events("ep1")
            assert len(events) == 2

    def test_append_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = JSONLEventStore(base_dir=tmpdir)
            store.append_batch(
                [
                    {"event_type": "A", "episode_id": "ep_batch", "step": 0},
                    {"event_type": "B", "episode_id": "ep_batch", "step": 1},
                ]
            )
            assert store.count("ep_batch") == 2

    def test_get_events_by_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = JSONLEventStore(base_dir=tmpdir)
            store.append({"event_type": "A", "episode_id": "ep1", "step": 0})
            store.append({"event_type": "B", "episode_id": "ep1", "step": 1})
            store.append({"event_type": "A", "episode_id": "ep1", "step": 2})

            a_events = store.get_events_by_type("ep1", "A")
            assert len(a_events) == 2

    def test_clear_removes_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = JSONLEventStore(base_dir=tmpdir)
            store.append({"event_type": "T", "episode_id": "ep_clear", "step": 0})
            store.clear()
            assert store.count("ep_clear") == 0

    def test_missing_episode_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = JSONLEventStore(base_dir=tmpdir)
            assert store.get_events("nonexistent") == []
