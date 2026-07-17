"""Response cache -- enables replay of recorded provider responses without network.

Cache key: SHA256(provider_name + model_name + prompt + temperature + max_tokens).
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def compute_cache_key(
    provider_name: str,
    model_name: str,
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Compute a deterministic cache key for a provider request.

    Same input -> same key -> same cached response.
    """
    raw = json.dumps(
        {
            "provider": provider_name,
            "model": model_name,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def compute_text_hash(text: str) -> str:
    """Compute SHA256 hash of a text string."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class ResponseCache:
    """In-memory + file-backed response cache.

    Supports:
    - Putting responses into cache (recording mode)
    - Getting responses from cache (replay mode)
    - Saving/loading cache to/from disk
    """

    def __init__(self, cache_dir: str | None = None):
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._hits = 0
        self._misses = 0

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """Get a cached response. Returns None if not found."""
        if cache_key in self._cache:
            self._hits += 1
            return copy.deepcopy(self._cache[cache_key])

        # Try disk cache
        if self._cache_dir:
            entry_path = self._cache_dir / f"{cache_key[:2]}" / f"{cache_key}.json"
            if entry_path.exists():
                try:
                    data = json.loads(entry_path.read_text(encoding="utf-8"))
                    self._cache[cache_key] = data
                    self._hits += 1
                    return dict(data)
                except (json.JSONDecodeError, OSError):
                    pass

        self._misses += 1
        return None

    def put(self, cache_key: str, response_data: dict[str, Any]) -> None:
        """Store a response in cache."""
        self._cache[cache_key] = dict(response_data)

        # Write to disk if configured
        if self._cache_dir:
            entry_dir = self._cache_dir / cache_key[:2]
            entry_dir.mkdir(parents=True, exist_ok=True)
            entry_path = entry_dir / f"{cache_key}.json"
            entry_path.write_text(
                json.dumps(response_data, indent=2, default=str), encoding="utf-8"
            )

    def load_from_dir(self, directory: str | Path) -> int:
        """Load all cached responses from a directory. Returns count loaded."""
        dir_path = Path(directory)
        if not dir_path.exists():
            return 0
        count = 0
        for json_file in dir_path.rglob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                key = json_file.stem
                self._cache[key] = data
                count += 1
            except (json.JSONDecodeError, OSError):
                continue
        return count

    def save_to_dir(self, directory: str | Path) -> int:
        """Save all cached responses to a directory. Returns count saved."""
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        count = 0
        for key, data in self._cache.items():
            entry_dir = dir_path / key[:2]
            entry_dir.mkdir(parents=True, exist_ok=True)
            entry_path = entry_dir / f"{key}.json"
            entry_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            count += 1
        return count

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def size(self) -> int:
        return len(self._cache)

    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": self.size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / max(total, 1),
        }

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
