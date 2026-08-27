from __future__ import annotations

from maya.core.models import MemoryItem


class InMemoryStore:
    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    async def add(self, item: MemoryItem) -> MemoryItem:
        self._items.append(item)
        return item

    async def search(self, user_id: str, query: str, limit: int = 8) -> list[MemoryItem]:
        query_terms = {term.lower() for term in query.split() if len(term) >= 3}
        scored: list[tuple[int, MemoryItem]] = []
        for item in self._items:
            if item.metadata.get("user_id") != user_id:
                continue
            haystack = item.content.lower()
            overlap = sum(term in haystack for term in query_terms)
            scored.append((overlap, item))
        scored.sort(key=lambda pair: (pair[0], pair[1].importance), reverse=True)
        return [item for score, item in scored if score > 0][:limit]
