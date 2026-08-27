"""In-memory implementations of MemoryWriter, MemoryReader, and LinkStore.

Suitable for testing and development. Not for production persistence.
See docs/DECISIONS.md ADR-0009.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import UUID

from maya.memory.models import (
    AssociationType,
    MemoryItem,
    MemoryLink,
    MemoryStatus,
    MemoryType,
    _utc_now,
)


class InMemoryWriter:
    """Writes memory items to an in-memory dict."""

    def __init__(self, storage: dict[UUID, MemoryItem] | None = None) -> None:
        self._storage: dict[UUID, MemoryItem] = storage if storage is not None else {}

    @property
    def storage(self) -> dict[UUID, MemoryItem]:
        return self._storage

    async def write(self, item: MemoryItem) -> MemoryItem:
        self._storage[item.id] = deepcopy(item)
        return item

    async def update(self, item_id: UUID, **fields: Any) -> MemoryItem:
        if item_id not in self._storage:
            raise KeyError(f"Memory {item_id} not found")
        item = self._storage[item_id]
        updated_data = item.model_dump()
        updated_data.update(fields)
        updated_data["updated_at"] = _utc_now()
        updated_data["version"] = item.version + 1
        updated_item = MemoryItem.model_validate(updated_data)
        self._storage[item_id] = updated_item
        return updated_item

    async def update_status(self, item_id: UUID, status: MemoryStatus) -> None:
        if item_id not in self._storage:
            raise KeyError(f"Memory {item_id} not found")
        item = self._storage[item_id]
        updated_data = item.model_dump()
        updated_data["status"] = status
        updated_data["updated_at"] = _utc_now()
        updated_data["version"] = item.version + 1
        self._storage[item_id] = MemoryItem.model_validate(updated_data)


class InMemoryReader:
    """Reads memory items from a shared in-memory dict."""

    def __init__(self, storage: dict[UUID, MemoryItem]) -> None:
        self._storage = storage

    async def get(self, item_id: UUID) -> MemoryItem | None:
        item = self._storage.get(item_id)
        return deepcopy(item) if item is not None else None

    async def get_batch(self, item_ids: list[UUID]) -> list[MemoryItem]:
        return [deepcopy(self._storage[uid]) for uid in item_ids if uid in self._storage]

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        types: list[MemoryType] | None = None,
        statuses: list[MemoryStatus] | None = None,
    ) -> list[MemoryItem]:
        results = []
        status_filter = set(statuses) if statuses else {MemoryStatus.ACTIVE}
        for item in self._storage.values():
            if item.user_id != user_id:
                continue
            if item.status not in status_filter:
                continue
            if types is not None and item.memory_type not in types:
                continue
            results.append(deepcopy(item))
        return results


class InMemoryLinkStore:
    """Manages memory association links in-memory."""

    def __init__(self) -> None:
        self._links: list[MemoryLink] = []

    @property
    def links(self) -> list[MemoryLink]:
        return list(self._links)

    async def add_link(self, link: MemoryLink) -> MemoryLink:
        self._links.append(deepcopy(link))
        return link

    async def get_links(
        self,
        memory_id: UUID,
        *,
        link_types: list[AssociationType] | None = None,
        direction: str = "outgoing",
    ) -> list[MemoryLink]:
        results = []
        for link in self._links:
            match = False
            if direction in ("outgoing", "both") and link.source_id == memory_id:
                match = True
            if direction in ("incoming", "both") and link.target_id == memory_id:
                match = True
            if not match:
                continue
            if link_types is not None and link.link_type not in link_types:
                continue
            results.append(deepcopy(link))
        return results

    async def remove_link(self, source_id: UUID, target_id: UUID) -> None:
        self._links = [
            l for l in self._links
            if not (l.source_id == source_id and l.target_id == target_id)
        ]
