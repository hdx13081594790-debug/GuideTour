from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, object]] = {}

    def get_or_set(self, key: str, ttl_seconds: int, factory: Callable[[], T]) -> T:
        now = time.time()
        found = self._store.get(key)
        if found and found[0] > now:
            return found[1]  # type: ignore[return-value]
        value = factory()
        self._store[key] = (now + ttl_seconds, value)
        return value

    def clear(self) -> None:
        self._store.clear()


cache = MemoryCache()
