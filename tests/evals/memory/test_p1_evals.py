from uuid import uuid4

import pytest

from maya.core.models import ConversationTurn
from maya.llm.mock import MockLLMProvider
from maya.memory.association import (
    AssociationEngine,
)
from maya.memory.extraction import (
    ExtractionResult,
    LLMMemoryEncoder,
)
from maya.memory.lifecycle.consolidation import (
    ConsolidationOutput,
    StructuredConsolidationEngine,
)
from maya.memory.lifecycle.contradiction import (
    ContradictionOutput,
    LLMContradictionDetector,
)
from maya.memory.lifecycle.reflection import (
    LLMReflectionEngine,
    ReflectionOutput,
)
from maya.memory.models import MemoryItem, MemoryType, ProvenanceRecord


class DummyLinkStore:
    def __init__(self):
        self.links = []
    
    async def add_link(self, link):
        self.links.append(link)
        return link

@pytest.mark.asyncio
async def test_structured_extraction_and_provenance():
    # Setup mock LLM response
    mock_llm = MockLLMProvider(structured_responses={
        ExtractionResult: ExtractionResult(
            summary="User likes coffee",
            entities=["coffee", "user"],
            topics=["preferences"],
            valence=0.8,
            arousal=0.5,
            confidence=0.9
        )
    })
    encoder = LLMMemoryEncoder(llm=mock_llm)
    
    turn = ConversationTurn(user_id=uuid4(), text="I really love drinking coffee in the morning.")
    memory = await encoder.encode(turn)
    
    assert memory is not None
    assert memory.summary == "User likes coffee"
    assert memory.entities == ["coffee", "user"]
    assert memory.topics == ["preferences"]
    
    # Check provenance
    assert memory.provenance.source_type == "user_message"
    assert memory.provenance.source_id == turn.turn_id
    assert memory.provenance.method == "llm_extraction"
    assert memory.provenance.confidence == 0.9

@pytest.mark.asyncio
async def test_extraction_validation_malformed():
    class BrokenLLMProvider:
        async def generate_structured(self, **kwargs):
            return {"not_a_model": "this should fail"}
            
    encoder = LLMMemoryEncoder(llm=BrokenLLMProvider())
    turn = ConversationTurn(user_id=uuid4(), text="Test")
    memory = await encoder.encode(turn)
    
    # Should safely return None on validation failure
    assert memory is None

@pytest.mark.asyncio
async def test_automatic_association_creation():
    link_store = DummyLinkStore()
    engine = AssociationEngine(link_store=link_store)
    
    # Create two memories sharing an entity and topic
    mem1 = MemoryItem(
        user_id=uuid4(),
        memory_type=MemoryType.EPISODIC,
        content="I have a cat named Whiskers.",
        entities=["Whiskers"],
        topics=["pets"],
        provenance=ProvenanceRecord(source_type="user_message")
    )
    
    mem2 = MemoryItem(
        user_id=uuid4(),
        memory_type=MemoryType.EPISODIC,
        content="Whiskers is very playful today.",
        entities=["Whiskers"],
        topics=["pets"],
        provenance=ProvenanceRecord(source_type="user_message")
    )
    
    links = await engine.associate(new_memory=mem2, context_memories=[mem1, mem2])
    
    # Expect links for both Entity and Topic sharing
    assert len(links) > 0
    link_types = {link.link_type for link in links}
    assert "entity" in link_types
    assert "thematic" in link_types

@pytest.mark.asyncio
async def test_evidence_backed_reflection():
    mock_llm = MockLLMProvider(structured_responses={
        ReflectionOutput: ReflectionOutput(
            insights=[
                {"insight": "User is a morning person.", "reflection_type": "pattern", "confidence": 0.85}
            ]
        )
    })
    
    engine = LLMReflectionEngine(llm=mock_llm, min_memories=2)
    memories = [
        MemoryItem(user_id=uuid4(), memory_type=MemoryType.EPISODIC, content="I wake up at 5am.", topics=["sleep"], provenance=ProvenanceRecord(source_type="user")),
        MemoryItem(user_id=uuid4(), memory_type=MemoryType.EPISODIC, content="Morning jogs are the best.", topics=["exercise"], provenance=ProvenanceRecord(source_type="user"))
    ]
    
    results = await engine.reflect(memories)
    assert len(results) == 1
    
    insight = results[0]
    assert insight.insight == "User is a morning person."
    assert insight.reflection_type == "pattern"
    assert insight.confidence == 0.85
    
    # Provenance
    assert insight.provenance.source_type == "reflection"
    assert len(insight.provenance.evidence_ids) == 2

@pytest.mark.asyncio
async def test_structured_consolidation():
    mock_llm = MockLLMProvider(structured_responses={
        ConsolidationOutput: ConsolidationOutput(
            new_semantic_content="User consistently reports enjoying sci-fi movies.",
            confidence=0.9
        )
    })
    
    engine = StructuredConsolidationEngine(llm=mock_llm, min_occurrences=2)
    memories = [
        MemoryItem(user_id=uuid4(), memory_type=MemoryType.EPISODIC, content="Watched Star Wars.", topics=["sci-fi"], provenance=ProvenanceRecord(source_type="user")),
        MemoryItem(user_id=uuid4(), memory_type=MemoryType.EPISODIC, content="Dune was amazing.", topics=["sci-fi"], provenance=ProvenanceRecord(source_type="user"))
    ]
    
    result = await engine.consolidate(memories)
    assert result is not None
    assert result.new_semantic_content == "User consistently reports enjoying sci-fi movies."
    assert len(result.absorbed_ids) == 2
    assert result.provenance.source_type == "consolidation"

@pytest.mark.asyncio
async def test_contradiction_classification():
    existing_id = uuid4()
    mock_llm = MockLLMProvider(structured_responses={
        ContradictionOutput: ContradictionOutput(
            contradictions=[
                {"existing_id": str(existing_id), "description": "Changed diet.", "conflict_type": "temporal_change"}
            ]
        )
    })
    
    detector = LLMContradictionDetector(llm=mock_llm)
    existing = [
        MemoryItem(id=existing_id, user_id=uuid4(), memory_type=MemoryType.SEMANTIC, content="User is a vegetarian.", entities=["diet"], topics=["food"], provenance=ProvenanceRecord(source_type="user"))
    ]
    candidate = MemoryItem(user_id=uuid4(), memory_type=MemoryType.EPISODIC, content="I started eating meat again.", entities=["diet"], topics=["food"], provenance=ProvenanceRecord(source_type="user"))
    
    contradictions = await detector.detect(existing, candidate)
    
    assert len(contradictions) == 1
    assert contradictions[0].memory_a_id == existing_id
    assert contradictions[0].memory_b_id == candidate.id
    assert "TEMPORAL_CHANGE" in contradictions[0].description
