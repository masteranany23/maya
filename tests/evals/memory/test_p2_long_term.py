from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from maya.memory.lifecycle.maintenance import MemoryMaintenanceService
from maya.memory.manager import DefaultMemoryManager
from maya.memory.models import MemoryItem, MemoryStatus, MemoryType, ProvenanceRecord
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.store.sqlite import SQLiteLinkStore, SQLiteReader, SQLiteWriter


@pytest.mark.asyncio
async def test_long_term_memory_lifecycle(tmp_path):
    user_id = uuid4()
    db_file = tmp_path / f"{uuid4()}.sqlite"
    db_path = str(db_file)
    
    # 1. Initialize Storage
    writer = SQLiteWriter(db_path)
    reader = SQLiteReader(db_path)
    link_store = SQLiteLinkStore(db_path)
    await writer.init_schema()
    
    async def get_links(mid): return await link_store.get_links(mid, direction="both")
    activation = SpreadingActivationEngine(link_getter=get_links)
    recall = MultiChannelRecallEngine(channels=[KeywordRecallChannel()], reader=reader, activation_engine=activation)
    manager = DefaultMemoryManager(writer=writer, reader=reader, recall_engine=recall)
    
    maintenance = MemoryMaintenanceService(reader=reader, writer=writer, decay_threshold=0.2)
    
    # 2. Simulate 100 events across 30 days
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    for i in range(100):
        # We simulate the passing of time by manipulating the `created_at` field and `last_accessed_at`
        time_offset = timedelta(days=(i * 0.3)) # ~30 days total
        event_time = base_time + time_offset
        
        mem = MemoryItem(
            user_id=user_id,
            memory_type=MemoryType.EPISODIC,
            content=f"Event {i} happened today.",
            provenance=ProvenanceRecord(source_type="user", created_at=event_time)
        )
        mem.created_at = event_time
        mem.scoring.last_accessed_at = event_time
        mem.scoring.decay_rate = 0.05 # high decay
        await manager.memorize(mem)
        
    # Reinforce the first item heavily
    first_item = (await reader.list_by_user(user_id))[0]
    for _ in range(10):
        await manager.reinforce(first_item.id, is_background=False)
        
    # 3. Fast forward to day 40. Run Decay Sweep.
    # To simulate decay, we rely on the sweep checking effective_salience relative to _utc_now().
    # Let's mock _utc_now in the models so the score computes correctly.
    import maya.memory.models as models_module
    old_utc = models_module._utc_now
    
    future_time = base_time + timedelta(days=40)
    models_module._utc_now = lambda: future_time
    
    decayed = await maintenance.run_decay_sweep(user_id)
    assert decayed > 50  # Most should decay as they haven't been reinforced
    
    # The first item should NOT decay because we reinforced it
    reinforced_item = await reader.get(first_item.id)
    assert reinforced_item is not None
    assert reinforced_item.status == MemoryStatus.ACTIVE
    
    models_module._utc_now = old_utc
    
    # 4. Persistence across restart
    await writer.close()
    await reader.close()
    await link_store.close()
    
    writer2 = SQLiteWriter(db_path)
    reader2 = SQLiteReader(db_path)
    
    results = await reader2.list_by_user(user_id, statuses=[MemoryStatus.DECAYED])
    assert len(results) == decayed
    
    await writer2.close()
    await reader2.close()
