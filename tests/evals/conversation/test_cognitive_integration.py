"""End-to-end cognitive memory integration tests."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from maya.conversation.engine import ConversationEngine
from maya.core.models import AffectState, ConversationTurn, Persona, ResponsePlan, UserProfile
from maya.memory.manager import DefaultMemoryManager
from maya.memory.models import AssociationType, MemoryItem, MemoryLink, MemoryType, ProvenanceRecord
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.store.in_memory import InMemoryLinkStore, InMemoryReader, InMemoryWriter


class StubAffectAnalyzer:
    async def analyze(self, turn: ConversationTurn) -> AffectState:
        return AffectState(valence=0.5, arousal=0.5, confidence=1.0)


class StubPersonaStore:
    async def get_persona(self) -> Persona:
        return Persona(name="MAYA")

    async def get_user_profile(self, user_id: str) -> UserProfile:
        return UserProfile(user_id=UUID(user_id))


class StubLLMProvider:
    async def generate(
        self,
        *,
        persona: Persona,
        profile: UserProfile,
        recall_results: list[Any],
        affect: AffectState,
        plan: ResponsePlan,
        user_message: str,
    ) -> str:
        if not recall_results:
            return "I have no specific memories about this."
        return f"Response based on {len(recall_results)} memories."


def _setup_engine() -> tuple[ConversationEngine, dict, InMemoryLinkStore]:
    storage: dict[UUID, MemoryItem] = {}
    writer = InMemoryWriter(storage)
    reader = InMemoryReader(storage)
    link_store = InMemoryLinkStore()

    async def get_links(mid: UUID) -> list[MemoryLink]:
        return await link_store.get_links(mid, direction="both")

    activation_engine = SpreadingActivationEngine(
        link_getter=get_links,
        attenuation_factor=0.9,
        activation_threshold=0.1,
    )

    recall_engine = MultiChannelRecallEngine(
        channels=[KeywordRecallChannel()],
        reader=reader,
        activation_engine=activation_engine,
    )

    memory_manager = DefaultMemoryManager(
        writer=writer,
        reader=reader,
        recall_engine=recall_engine,
    )

    engine = ConversationEngine(
        memory_manager=memory_manager,
        persona_store=StubPersonaStore(),
        affect_analyzer=StubAffectAnalyzer(),
        llm=StubLLMProvider(),
    )

    return engine, storage, link_store


@pytest.fixture
def conversation_stack() -> tuple[ConversationEngine, dict, InMemoryLinkStore]:
    return _setup_engine()


class TestCognitiveIntegration:
    async def test_working_memory_and_reinforcement(
        self, conversation_stack: tuple[ConversationEngine, dict, InMemoryLinkStore]
    ) -> None:
        """J6: Prove core API uses working memory and reinforcement."""
        engine, storage, _ = conversation_stack
        user_id = uuid4()
        conv_id = uuid4()

        # Seed a memory
        m = MemoryItem(
            user_id=user_id,
            memory_type=MemoryType.EPISODIC,
            content="I love pizza",
            provenance=ProvenanceRecord(source_type="user_message", method="direct_observation"),
        )
        await engine.memory_manager.memorize(m)

        # First chat triggers recall of pizza
        resp = await engine.chat(user_id=user_id, conversation_id=conv_id, message="What do I love? pizza!")
        
        # Check WorkingMemory
        wm = await engine.memory_manager.get_working_memory(user_id, conv_id)
        assert len(wm.recent_turns) == 1
        assert wm.recent_turns[0].text == "What do I love? pizza!"
        assert any(mem.id == m.id for mem in wm.active_memories)

        # Check reinforcement
        updated_m = storage[m.id]
        assert updated_m.scoring.access_count == 1
        assert updated_m.scoring.last_accessed_at is not None

    async def test_false_memory_resistance(
        self, conversation_stack: tuple[ConversationEngine, dict, InMemoryLinkStore]
    ) -> None:
        """J8: False-memory resistance."""
        engine, storage, _ = conversation_stack
        user_id = uuid4()
        conv_id = uuid4()

        # No memories exist
        resp = await engine.chat(user_id=user_id, conversation_id=conv_id, message="What did I do yesterday?")
        
        # Assert no memories were used
        assert len(resp.used_memory_ids) == 0
        assert resp.text == "I have no specific memories about this."

    async def test_autobiographical_recall_eval(
        self, conversation_stack: tuple[ConversationEngine, dict, InMemoryLinkStore]
    ) -> None:
        """J7: Flagship autobiographical recall evaluation."""
        engine, storage, link_store = conversation_stack
        user_id = uuid4()
        conv_id = uuid4()

        # Build the graph directly in storage to simulate the past events
        m1 = MemoryItem(
            user_id=user_id, memory_type=MemoryType.EPISODIC,
            content="I failed the robotics competition",
            provenance=ProvenanceRecord(source_type="user_message", method="direct_observation"),
        )
        m2 = MemoryItem(
            user_id=user_id, memory_type=MemoryType.EPISODIC,
            content="I felt so embarrassed afterward",
            provenance=ProvenanceRecord(source_type="user_message", method="direct_observation"),
        )
        m3 = MemoryItem(
            user_id=user_id, memory_type=MemoryType.EPISODIC,
            content="I considered quitting robotics completely",
            provenance=ProvenanceRecord(source_type="user_message", method="direct_observation"),
        )
        m4 = MemoryItem(
            user_id=user_id, memory_type=MemoryType.EPISODIC,
            content="I decided to return to robotics",
            provenance=ProvenanceRecord(source_type="user_message", method="direct_observation"),
        )

        for m in [m1, m2, m3, m4]:
            await engine.memory_manager.memorize(m)

        await link_store.add_link(MemoryLink(source_id=m1.id, target_id=m2.id, link_type=AssociationType.CAUSAL, strength=1.0))
        await link_store.add_link(MemoryLink(source_id=m2.id, target_id=m3.id, link_type=AssociationType.CAUSAL, strength=1.0))
        await link_store.add_link(MemoryLink(source_id=m3.id, target_id=m4.id, link_type=AssociationType.THEMATIC, strength=1.0))

        # The query does NOT contain 'failure', 'embarrassment', or 'quitting'.
        # But 'competition' connects it to m1, which connects it to the rest.
        resp = await engine.chat(
            user_id=user_id, 
            conversation_id=conv_id, 
            message="I'm thinking about entering another competition."
        )

        # Inspect retrieved memories
        assert m1.id in resp.used_memory_ids
        assert m2.id in resp.used_memory_ids
        assert m3.id in resp.used_memory_ids

        # Get the working memory to check the traces
        wm = await engine.memory_manager.get_working_memory(user_id, conv_id)
        active_ids = {m.id for m in wm.active_memories}
        assert m1.id in active_ids
        assert m3.id in active_ids

