"""EventStore protocol — append-only persistence for simulation events."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EventStore(Protocol):
    """Abstract append-only event store.

    Implementations: InMemoryEventStore, JSONLEventStore, SQLiteEventStore.
    """

    def append(self, event: dict) -> None:
        """Persist a single event."""
        ...

    def append_batch(self, events: list[dict]) -> None:
        """Persist multiple events at once."""
        ...

    def get_events(self, episode_id: str) -> list[dict]:
        """Retrieve all events for an episode, ordered by step."""
        ...

    def get_events_by_type(self, episode_id: str, event_type: str) -> list[dict]:
        """Retrieve events of a specific type for an episode."""
        ...

    def count(self, episode_id: str) -> int:
        """Return the number of events for an episode."""
        ...

    def clear(self) -> None:
        """Remove all events (for test teardown)."""
        ...
