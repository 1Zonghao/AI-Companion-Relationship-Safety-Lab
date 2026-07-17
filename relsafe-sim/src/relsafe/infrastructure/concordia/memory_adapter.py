"""ConcordiaMemoryAdapter — wraps AssociativeMemoryBank for RelSafe.

Supports writing observations, reading context, and minimal memory deletion
events, without exposing Concordia memory types to the domain layer.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from concordia.associative_memory import basic_associative_memory


def _dummy_embedder(text: str) -> np.ndarray:
    """Return a zero embedding vector for environments without real embeddings."""
    del text
    return np.zeros(128, dtype=np.float64)


class ConcordiaMemoryAdapter:
    """Adapter around Concordia's AssociativeMemoryBank.

    Provides a simplified interface for adding observations, retrieving
    context, and deleting memories.  All inputs and outputs are plain
    Python strings/list[str] — no Concordia types leak.
    """

    def __init__(
        self,
        memory_bank: basic_associative_memory.AssociativeMemoryBank | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            memory_bank: An existing Concordia memory bank, or None to create
                a new one without embedding support.
        """
        if memory_bank is None:
            self._bank = basic_associative_memory.AssociativeMemoryBank(
                sentence_embedder=_dummy_embedder,
                allow_duplicates=True,
            )
        else:
            self._bank = memory_bank

    @property
    def bank(self) -> basic_associative_memory.AssociativeMemoryBank:
        """Access the underlying Concordia memory bank.

        Only Concordia adapter code should use this property.
        """
        return self._bank

    def add(self, text: str, importance: float = 1.0) -> None:
        """Record an observation or event in memory."""
        del importance  # reserved for future use
        self._bank.add(text)
        self._bank._flush_pending()  # noqa: SLF001

    def retrieve_recent(self, limit: int = 10) -> list[str]:
        """Return the most recent memory entries."""
        self._bank._flush_pending()  # noqa: SLF001
        df = self._bank._memory_bank  # noqa: SLF001
        if df.empty:
            return []
        recent = df.tail(limit)
        return list(recent["text"])

    def retrieve_all(self) -> list[str]:
        """Return all memory entries in insertion order."""
        self._bank._flush_pending()  # noqa: SLF001
        df = self._bank._memory_bank  # noqa: SLF001
        if df.empty:
            return []
        return list(df["text"])

    def delete_matching(self, predicate: Callable[[str], bool]) -> int:
        """Delete memories matching a predicate.

        Used for memory_deletion interventions. Returns the number
        of deleted entries.

        Args:
            predicate: A function that returns True for entries to delete.

        Returns:
            Number of entries deleted.
        """
        self._bank._flush_pending()  # noqa: SLF001
        df = self._bank._memory_bank  # noqa: SLF001
        if df.empty:
            return 0
        mask = df["text"].apply(predicate)
        deleted_count = int(mask.sum())
        self._bank._memory_bank = df[~mask].reset_index(drop=True)  # noqa: SLF001
        return deleted_count

    def clear(self) -> None:
        """Remove all memories (for test teardown)."""
        self._bank._flush_pending()  # noqa: SLF001
        df = self._bank._memory_bank  # noqa: SLF001
        if not df.empty:
            self._bank._memory_bank = df.iloc[0:0]  # noqa: SLF001

    def count(self) -> int:
        """Return the number of stored memory entries."""
        self._bank._flush_pending()  # noqa: SLF001
        return len(self._bank._memory_bank)  # noqa: SLF001


def create_memory_adapter(
    embedder: Callable[[str], np.ndarray] | None = None,
) -> ConcordiaMemoryAdapter:
    """Factory: create a ConcordiaMemoryAdapter with an optional embedder."""
    bank = basic_associative_memory.AssociativeMemoryBank(
        sentence_embedder=embedder,
        allow_duplicates=True,
    )
    return ConcordiaMemoryAdapter(memory_bank=bank)
