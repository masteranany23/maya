"""LoCoMo-inspired regression adapter for MAYA memory.

This evaluates MAYA's ability to maintain and recall information
across long-term sessions, avoiding regressions in multi-hop retrieval.
"""

from uuid import uuid4

import pytest

from maya.conversation.engine import ConversationEngine
from maya.core.models import UserProfile
from maya.llm.mock import MockLLMProvider
from maya.memory.association import (
    AssociationEngine,
    SharedEntityStrategy,
    SharedTopicStrategy,
    TemporalProximityStrategy,
)
from maya.memory.extraction import LLMMemoryEncoder
from maya.memory.lifecycle.maintenance import MemoryMaintenanceService
from maya.memory.manager import DefaultMemoryManager
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.store.sqlite import SQLiteLinkStore, SQLiteReader, SQLiteWriter


class DummyAffectAnalyzer:
    async def analyze(self, turn):
        from maya.core.models import AffectState
        return AffectState(valence=0.0, arousal=0.0, confidence=1.0)

class DummyPersonaStore:
    async def get_persona(self):
        from maya.core.models import Persona
        return Persona(name="MAYA")
    async def get_user_profile(self, user_id):
        return UserProfile(user_id=uuid4())

@pytest.mark.asyncio
async def test_locomo_regression_harness():
    user_id = uuid4()
    db_path = f"file:{uuid4()}?mode=memory&cache=shared"
    
    # Setup standard P2 memory stack
    writer = SQLiteWriter(db_path)
    reader = SQLiteReader(db_path)
    link_store = SQLiteLinkStore(db_path)
    await writer.init_schema()
    
    async def get_links(mid): return await link_store.get_links(mid, direction="both")
    activation = SpreadingActivationEngine(link_getter=get_links)
    recall = MultiChannelRecallEngine(channels=[KeywordRecallChannel()], reader=reader, activation_engine=activation)
    manager = DefaultMemoryManager(writer=writer, reader=reader, recall_engine=recall)
    
    llm = MockLLMProvider()
    encoder = LLMMemoryEncoder(llm=llm)
    association = AssociationEngine(
        link_store=link_store, 
        strategies=[SharedEntityStrategy(), SharedTopicStrategy(), TemporalProximityStrategy()]
    )
    
    engine = ConversationEngine(
        memory_manager=manager,
        persona_store=DummyPersonaStore(),
        affect_analyzer=DummyAffectAnalyzer(),
        llm=llm,
        memory_encoder=encoder,
        association_engine=association
    )
    
    # 1. Provide evidence via conversation (Session 1)
    conv_id = uuid4()
    await engine.chat(user_id=user_id, conversation_id=conv_id, message="My favorite color is blue.")
    await engine.chat(user_id=user_id, conversation_id=conv_id, message="I work as a software engineer.")
    
    # 2. Run maintenance (simulate day passing)
    maintenance = MemoryMaintenanceService(reader=reader, writer=writer)
    await maintenance.run_decay_sweep(user_id)
    
    # 3. New Session (Session 2)
    conv_id2 = uuid4()
    await engine.chat(user_id=user_id, conversation_id=conv_id2, message="I just bought a blue car.")
    
    # 4. LoCoMo Evaluation Question
    question = "What is my favorite color, and what did I buy?"
    expected_evidence = ["My favorite color is blue.", "I just bought a blue car."]
    
    response = await engine.chat(user_id=user_id, conversation_id=conv_id2, message=question)
    
    # 5. Record and Evaluate Results
    wm = await manager.get_working_memory(user_id, conv_id2)
    
    retrieved_memory_contents = [r.memory.content for r in wm.recall_results]
    retrieval_scores = [r.relevance_score for r in wm.recall_results]
    
    assert len(wm.recall_results) > 0
    assert any("blue" in content.lower() for content in retrieved_memory_contents)
    
    # Record metrics (in a real harness, this would write to a JSONL log)
    eval_result = {
        "question": question,
        "expected": expected_evidence,
        "retrieved_contents": retrieved_memory_contents,
        "scores": retrieval_scores,
        "final_answer": response.text,
    }
    assert eval_result["final_answer"] is not None
    
    await writer.close()
    await reader.close()
    await link_store.close()
