"""SQLite implementations of MemoryWriter, MemoryReader, and LinkStore."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import aiosqlite

from maya.memory.models import (
    AssociationType,
    MemoryItem,
    MemoryLink,
    MemoryStatus,
    MemoryType,
)


class SQLiteStoreBase:
    """Base class for SQLite storage components."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._pool: aiosqlite.Connection | None = None

    async def get_connection(self) -> aiosqlite.Connection:
        if self._pool is None:
            self._pool = await aiosqlite.connect(self.db_path)
            self._pool.row_factory = aiosqlite.Row
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def init_schema(self) -> None:
        conn = await self.get_connection()
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_items (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                status TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                entities TEXT NOT NULL,
                topics TEXT NOT NULL,
                emotional_context TEXT NOT NULL,
                temporal_context TEXT,
                provenance TEXT NOT NULL,
                scoring TEXT NOT NULL,
                reconstruction_notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version INTEGER NOT NULL,
                tags TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_links (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                link_type TEXT NOT NULL,
                strength REAL NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
            """
        )
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_user_id ON memory_items (user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_status ON memory_items (status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_link_source ON memory_links (source_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_link_target ON memory_links (target_id)")
        
        await conn.commit()

def _row_to_memory_item(row: aiosqlite.Row) -> MemoryItem:
    data = dict(row)
    data["entities"] = json.loads(data["entities"])
    data["topics"] = json.loads(data["topics"])
    data["emotional_context"] = json.loads(data["emotional_context"])
    if data["temporal_context"]:
        data["temporal_context"] = json.loads(data["temporal_context"])
    data["provenance"] = json.loads(data["provenance"])
    data["scoring"] = json.loads(data["scoring"])
    data["tags"] = json.loads(data["tags"])
    data["metadata"] = json.loads(data["metadata"])
    return MemoryItem.model_validate(data)


class SQLiteWriter(SQLiteStoreBase):
    async def write(self, item: MemoryItem) -> MemoryItem:
        conn = await self.get_connection()
        data = item.model_dump(mode="json")
        await conn.execute(
            """
            INSERT INTO memory_items (
                id, user_id, memory_type, status, content, summary,
                entities, topics, emotional_context, temporal_context,
                provenance, scoring, reconstruction_notes,
                created_at, updated_at, version, tags, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(item.id),
                str(item.user_id),
                item.memory_type.value,
                item.status.value,
                item.content,
                item.summary,
                json.dumps(data["entities"]),
                json.dumps(data["topics"]),
                json.dumps(data["emotional_context"]),
                json.dumps(data["temporal_context"]) if data.get("temporal_context") else None,
                json.dumps(data["provenance"]),
                json.dumps(data["scoring"]),
                item.reconstruction_notes,
                data["created_at"],
                data["updated_at"],
                item.version,
                json.dumps(data["tags"]),
                json.dumps(data["metadata"]),
            )
        )
        await conn.commit()
        return item

    async def update(self, item_id: UUID, **fields: Any) -> MemoryItem:
        from maya.memory.models import _utc_now
        conn = await self.get_connection()
        
        cursor = await conn.execute("SELECT * FROM memory_items WHERE id = ?", (str(item_id),))
        row = await cursor.fetchone()
        if not row:
            raise KeyError(f"Memory {item_id} not found")
        
        item = _row_to_memory_item(row)
        updated_data = item.model_dump()
        updated_data.update(fields)
        updated_data["updated_at"] = _utc_now()
        updated_data["version"] = item.version + 1
        
        updated_item = MemoryItem.model_validate(updated_data)
        new_data = updated_item.model_dump(mode="json")
        
        await conn.execute(
            """
            UPDATE memory_items SET
                status = ?, content = ?, summary = ?,
                entities = ?, topics = ?, emotional_context = ?, temporal_context = ?,
                provenance = ?, scoring = ?, reconstruction_notes = ?,
                updated_at = ?, version = ?, tags = ?, metadata = ?
            WHERE id = ?
            """,
            (
                updated_item.status.value,
                updated_item.content,
                updated_item.summary,
                json.dumps(new_data["entities"]),
                json.dumps(new_data["topics"]),
                json.dumps(new_data["emotional_context"]),
                json.dumps(new_data["temporal_context"]) if new_data.get("temporal_context") else None,
                json.dumps(new_data["provenance"]),
                json.dumps(new_data["scoring"]),
                updated_item.reconstruction_notes,
                new_data["updated_at"],
                updated_item.version,
                json.dumps(new_data["tags"]),
                json.dumps(new_data["metadata"]),
                str(item_id)
            )
        )
        await conn.commit()
        return updated_item
        
    async def update_status(self, item_id: UUID, status: MemoryStatus) -> None:
        from maya.memory.models import _utc_now
        conn = await self.get_connection()
        cursor = await conn.execute("SELECT version FROM memory_items WHERE id = ?", (str(item_id),))
        row = await cursor.fetchone()
        if not row:
            raise KeyError(f"Memory {item_id} not found")
        
        version = row["version"] + 1
        now = _utc_now().isoformat()
        
        await conn.execute(
            """
            UPDATE memory_items SET status = ?, updated_at = ?, version = ? WHERE id = ?
            """,
            (status.value, now, version, str(item_id))
        )
        await conn.commit()


class SQLiteReader(SQLiteStoreBase):
    async def get(self, item_id: UUID) -> MemoryItem | None:
        conn = await self.get_connection()
        cursor = await conn.execute("SELECT * FROM memory_items WHERE id = ?", (str(item_id),))
        row = await cursor.fetchone()
        if row:
            return _row_to_memory_item(row)
        return None

    async def get_batch(self, item_ids: list[UUID]) -> list[MemoryItem]:
        if not item_ids:
            return []
        conn = await self.get_connection()
        placeholders = ",".join("?" for _ in item_ids)
        cursor = await conn.execute(
            f"SELECT * FROM memory_items WHERE id IN ({placeholders})",
            [str(uid) for uid in item_ids]
        )
        rows = await cursor.fetchall()
        return [_row_to_memory_item(row) for row in rows]

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        types: list[MemoryType] | None = None,
        statuses: list[MemoryStatus] | None = None,
    ) -> list[MemoryItem]:
        conn = await self.get_connection()
        
        query = "SELECT * FROM memory_items WHERE user_id = ?"
        params: list[Any] = [str(user_id)]
        
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            query += f" AND status IN ({placeholders})"
            params.extend([s.value for s in statuses])
        else:
            query += " AND status = ?"
            params.append(MemoryStatus.ACTIVE.value)
            
        if types:
            placeholders = ",".join("?" for _ in types)
            query += f" AND memory_type IN ({placeholders})"
            params.extend([t.value for t in types])
            
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [_row_to_memory_item(row) for row in rows]


class SQLiteLinkStore(SQLiteStoreBase):
    async def add_link(self, link: MemoryLink) -> MemoryLink:
        conn = await self.get_connection()
        data = link.model_dump(mode="json")
        await conn.execute(
            """
            INSERT INTO memory_links (
                id, source_id, target_id, link_type, strength, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(link.id),
                str(link.source_id),
                str(link.target_id),
                link.link_type.value,
                link.strength,
                data["created_at"],
                json.dumps(data["metadata"])
            )
        )
        await conn.commit()
        return link

    async def get_links(
        self,
        memory_id: UUID,
        *,
        link_types: list[AssociationType] | None = None,
        direction: str = "outgoing",
    ) -> list[MemoryLink]:
        conn = await self.get_connection()
        
        query = "SELECT * FROM memory_links WHERE "
        params: list[Any] = []
        
        if direction == "outgoing":
            query += "source_id = ?"
            params.append(str(memory_id))
        elif direction == "incoming":
            query += "target_id = ?"
            params.append(str(memory_id))
        else:  # both
            query += "(source_id = ? OR target_id = ?)"
            params.extend([str(memory_id), str(memory_id)])
            
        if link_types:
            placeholders = ",".join("?" for _ in link_types)
            query += f" AND link_type IN ({placeholders})"
            params.extend([t.value for t in link_types])
            
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        
        links = []
        for row in rows:
            data = dict(row)
            data["metadata"] = json.loads(data["metadata"])
            links.append(MemoryLink.model_validate(data))
        return links
        
    async def remove_link(self, source_id: UUID, target_id: UUID) -> None:
        conn = await self.get_connection()
        await conn.execute(
            "DELETE FROM memory_links WHERE source_id = ? AND target_id = ?",
            (str(source_id), str(target_id))
        )
        await conn.commit()
