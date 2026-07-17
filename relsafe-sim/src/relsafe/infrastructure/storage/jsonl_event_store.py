"""Event store implementations: InMemoryEventStore and JSONLEventStore."""

from __future__ import annotations

import json
from pathlib import Path


class InMemoryEventStore:
    """Append-only event store backed by a list.  Deterministic, fast, test-safe."""

    def __init__(self) -> None:
        self._events: list[dict] = []

    def append(self, event: dict) -> None:
        self._events.append(event)

    def append_batch(self, events: list[dict]) -> None:
        self._events.extend(events)

    def get_events(self, episode_id: str) -> list[dict]:
        return [e for e in self._events if e.get("episode_id") == episode_id]

    def get_events_by_type(self, episode_id: str, event_type: str) -> list[dict]:
        return [
            e
            for e in self._events
            if e.get("episode_id") == episode_id and e.get("event_type") == event_type
        ]

    def count(self, episode_id: str) -> int:
        return sum(1 for e in self._events if e.get("episode_id") == episode_id)

    def clear(self) -> None:
        self._events.clear()

    def all_events(self) -> list[dict]:
        """Return all events across all episodes (for debugging)."""
        return list(self._events)


class JSONLEventStore:
    """File-backed event store that appends JSON lines to disk."""

    def __init__(self, base_dir: str | Path = "outputs/runs") -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._events: list[dict] = []  # In-memory cache

    def append(self, event: dict) -> None:
        self._events.append(event)
        self._flush_one(event)

    def append_batch(self, events: list[dict]) -> None:
        self._events.extend(events)
        for e in events:
            self._flush_one(e)

    def get_events(self, episode_id: str) -> list[dict]:
        # Reload from file to ensure consistency
        file_path = self._file_path(episode_id)
        if not file_path.exists():
            return []
        events: list[dict] = []
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def get_events_by_type(self, episode_id: str, event_type: str) -> list[dict]:
        return [e for e in self.get_events(episode_id) if e.get("event_type") == event_type]

    def count(self, episode_id: str) -> int:
        return len(self.get_events(episode_id))

    def clear(self) -> None:
        self._events.clear()
        # Remove all jsonl files in base dir
        for f in self._base_dir.glob("*.jsonl"):
            f.unlink(missing_ok=True)

    def _file_path(self, episode_id: str) -> Path:
        # Sanitize episode_id for use as filename
        safe_id = "".join(c for c in episode_id if c.isalnum() or c in "-_.")
        return self._base_dir / f"{safe_id}.jsonl"

    def _flush_one(self, event: dict) -> None:
        episode_id = event.get("episode_id", "unknown")
        file_path = self._file_path(episode_id)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
