"""Contract tests for memory storage backends.

Any implementation of MemoryWriter/MemoryReader/LinkStore must pass these.
Import and parametrize with your concrete implementation.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from maya.memory.models import (
    AssociationType,
    MemoryItem,
    MemoryLink,
    MemoryStatus,
    MemoryType,
    ProvenanceRecord,
)
from maya.memory.store.in_memory import InMemoryLinkStore, InMemoryReader, InMemoryWriter


def _prov(**kw: object) -> ProvenanceRecord:
    defaults: dict = {"source_type": "user_message", "method": "direct_observation"}
    defaults.update(kw)
    return ProvenanceRecord(**defaults)


def _mem(user_id=None, **kw: object) -> MemoryItem:
    defaults: dict = {
        "user_id": user_id or uuid4(),
        "memory_type": MemoryType.EPISODIC,
        "content": "test",
        "provenance": _prov(),
    }
    defaults.update(kw)
    return MemoryItem(**defaults)


# ---------------------------------------------------------------------------
# Writer / Reader contract tests
# ---------------------------------------------------------------------------


class TestWriterReaderContract:
    """Tests that apply to any MemoryWriter + MemoryReader pair."""

    @pytest.fixture(params=["in_memory", "sqlite"])
    async def stores(self, request):
        if request.param == "in_memory":
            storage: dict = {}
            yield InMemoryWriter(storage), InMemoryReader(storage)
        else:
            from maya.memory.store.sqlite import SQLiteReader, SQLiteWriter
            db_path = f"file:{uuid4()}?mode=memory&cache=shared"
            writer = SQLiteWriter(db_path)
            reader = SQLiteReader(db_path)
            await writer.init_schema()
            yield writer, reader
            await writer.close()
            await reader.close()

    async def test_write_then_get(self, stores) -> None:
        writer, reader = stores
        m = _mem()
        await writer.write(m)
        got = await reader.get(m.id)
        assert got is not None
        assert got.id == m.id
        assert got.content == m.content

    async def test_get_missing_returns_none(self, stores) -> None:
        _, reader = stores
        assert await reader.get(uuid4()) is None

    async def test_get_batch(self, stores) -> None:
        writer, reader = stores
        items = [_mem() for _ in range(3)]
        for i in items:
            await writer.write(i)
        got = await reader.get_batch([items[0].id, items[2].id])
        assert len(got) == 2

    async def test_list_by_user_filters_status(self, stores) -> None:
        writer, reader = stores
        uid = uuid4()
        active = _mem(user_id=uid, content="active")
        await writer.write(active)
        archived = _mem(user_id=uid, content="archived", status=MemoryStatus.ARCHIVED)
        await writer.write(archived)
        results = await reader.list_by_user(uid)
        assert len(results) == 1
        assert results[0].content == "active"

    async def test_list_by_user_filters_type(self, stores) -> None:
        writer, reader = stores
        uid = uuid4()
        await writer.write(_mem(user_id=uid, memory_type=MemoryType.EPISODIC))
        await writer.write(_mem(user_id=uid, memory_type=MemoryType.SEMANTIC))
        results = await reader.list_by_user(uid, types=[MemoryType.SEMANTIC])
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.SEMANTIC

    async def test_update_changes_fields(self, stores) -> None:
        writer, reader = stores
        m = _mem(content="original")
        await writer.write(m)
        updated = await writer.update(m.id, content="modified")
        assert updated.content == "modified"
        assert updated.version == 2
        got = await reader.get(m.id)
        assert got is not None
        assert got.content == "modified"

    async def test_update_status(self, stores) -> None:
        writer, reader = stores
        m = _mem()
        await writer.write(m)
        await writer.update_status(m.id, MemoryStatus.DECAYED)
        got = await reader.get(m.id)
        assert got is not None
        assert got.status == MemoryStatus.DECAYED

    async def test_update_missing_raises(self, stores) -> None:
        writer, _ = stores
        with pytest.raises(KeyError):
            await writer.update(uuid4(), content="x")

    async def test_isolation_from_mutations(self, stores) -> None:
        writer, reader = stores
        m = _mem(content="original")
        await writer.write(m)
        got = await reader.get(m.id)
        assert got is not None
        # Mutating the returned object should not affect storage
        got.content = "tampered"  # type: ignore[misc]
        got2 = await reader.get(m.id)
        assert got2 is not None
        assert got2.content == "original"


# ---------------------------------------------------------------------------
# LinkStore contract tests
# ---------------------------------------------------------------------------


class TestLinkStoreContract:
    @pytest.fixture(params=["in_memory", "sqlite"])
    async def link_store(self, request):
        if request.param == "in_memory":
            yield InMemoryLinkStore()
        else:
            from maya.memory.store.sqlite import SQLiteLinkStore
            db_path = f"file:{uuid4()}?mode=memory&cache=shared"
            store = SQLiteLinkStore(db_path)
            await store.init_schema()
            yield store
            await store.close()

    async def test_add_and_get_outgoing(self, link_store) -> None:
        src, tgt = uuid4(), uuid4()
        link = MemoryLink(source_id=src, target_id=tgt, link_type=AssociationType.THEMATIC)
        await link_store.add_link(link)
        links = await link_store.get_links(src, direction="outgoing")
        assert len(links) == 1
        assert links[0].target_id == tgt

    async def test_get_incoming(self, link_store) -> None:
        src, tgt = uuid4(), uuid4()
        link = MemoryLink(source_id=src, target_id=tgt, link_type=AssociationType.CAUSAL)
        await link_store.add_link(link)
        links = await link_store.get_links(tgt, direction="incoming")
        assert len(links) == 1
        assert links[0].source_id == src

    async def test_get_both_directions(self, link_store) -> None:
        a, b, c = uuid4(), uuid4(), uuid4()
        await link_store.add_link(
            MemoryLink(source_id=a, target_id=b, link_type=AssociationType.TEMPORAL)
        )
        await link_store.add_link(
            MemoryLink(source_id=c, target_id=a, link_type=AssociationType.ENTITY)
        )
        links = await link_store.get_links(a, direction="both")
        assert len(links) == 2

    async def test_filter_by_link_type(self, link_store) -> None:
        src, tgt1, tgt2 = uuid4(), uuid4(), uuid4()
        await link_store.add_link(
            MemoryLink(source_id=src, target_id=tgt1, link_type=AssociationType.THEMATIC)
        )
        await link_store.add_link(
            MemoryLink(source_id=src, target_id=tgt2, link_type=AssociationType.CAUSAL)
        )
        links = await link_store.get_links(
            src, link_types=[AssociationType.THEMATIC], direction="outgoing"
        )
        assert len(links) == 1
        assert links[0].link_type == AssociationType.THEMATIC

    async def test_remove_link(self, link_store) -> None:
        src, tgt = uuid4(), uuid4()
        await link_store.add_link(
            MemoryLink(source_id=src, target_id=tgt, link_type=AssociationType.CONTRADICTS)
        )
        await link_store.remove_link(src, tgt)
        links = await link_store.get_links(src, direction="outgoing")
        assert len(links) == 0
