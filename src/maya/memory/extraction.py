"""Memory extraction module for structured experience encoding.

Transforms raw conversation turns into structured memories.
Implements P1.1 (Structured Experience Extraction) and P1.2 (Extraction Validation).
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field, ValidationError

from maya.core.models import ConversationTurn
from maya.core.protocols import LLMProvider
from maya.memory.models import (
    EmotionalContext,
    MemoryItem,
    MemoryStatus,
    MemoryType,
    ProvenanceRecord,
    ScoringState,
    TemporalContext,
    _utc_now,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured Extraction Models
# ---------------------------------------------------------------------------


class ExtractionResult(BaseModel):
    """Structured output expected from the LLM or heuristic encoder."""
    
    summary: str = Field(description="A brief summary of the event.")
    entities: list[str] = Field(default_factory=list, description="Named entities or objects mentioned.")
    topics: list[str] = Field(default_factory=list, description="Thematic tags for the conversation.")
    temporal_landmarks: list[str] = Field(default_factory=list, description="Explicit time references mentioned.")
    
    # Emotional context
    valence: float = Field(default=0.0, ge=-1.0, le=1.0, description="Sentiment (-1 to 1)")
    arousal: float = Field(default=0.0, ge=0.0, le=1.0, description="Emotional intensity (0 to 1)")
    dominant_emotion: str | None = Field(default=None, description="Primary emotion detected, if any")
    
    # Relationships / Associations
    relationships: dict[str, str] = Field(default_factory=dict, description="Relationships between entities")
    candidate_associations: list[str] = Field(default_factory=list, description="Potential topics/entities to link")
    
    # Meta
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Salience or importance of this turn (0 to 1)")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in the extraction (0 to 1)")


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class MemoryEncoder(Protocol):
    """Protocol for extracting structured memories from conversation turns."""

    async def encode(self, turn: ConversationTurn) -> MemoryItem | None:
        """Encodes a conversation turn into a MemoryItem."""
        ...


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------


class LLMMemoryEncoder:
    """Uses an LLMProvider to perform structured experience extraction."""
    
    def __init__(self, llm: LLMProvider, model_identifier: str = "llm-encoder-v1") -> None:
        self.llm = llm
        self.model_identifier = model_identifier

    async def encode(self, turn: ConversationTurn) -> MemoryItem | None:
        system_prompt = (
            "You are a cognitive memory extractor. Extract structured context from "
            "the following user message. Provide summary, entities, topics, temporal "
            "landmarks, emotional valence/arousal, importance, relationships, and candidate "
            "associations. Output must conform to the requested schema."
        )
        user_prompt = f"User message: {turn.text}"
        
        try:
            # P1.1: Extract structured experience using LLM
            result = await self.llm.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=ExtractionResult,
            )
            if not isinstance(result, ExtractionResult):
                raise ValueError("LLM did not return the expected ExtractionResult schema")
                
        except (ValidationError, ValueError) as e:
            # P1.2: Validate all LLM-generated extraction, reject malformed output
            logger.error(f"Extraction validation failed for turn {turn.turn_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None

        # Build context sub-models
        emotional_context = EmotionalContext(
            valence=result.valence,
            arousal=result.arousal,
            dominant_emotion=result.dominant_emotion,
            affect_source="inferred",
        )
        
        temporal_context = TemporalContext(
            occurred_at=turn.created_at,
            temporal_landmarks=result.temporal_landmarks,
        )
        
        scoring_state = ScoringState(
            importance=result.importance,
            access_count=0,
            last_accessed_at=None,
        )

        # P1.2: Preserve exact provenance
        provenance = ProvenanceRecord(
            source_type="user_message",
            source_id=turn.turn_id,
            created_at=_utc_now(),
            confidence=result.confidence,
            method="llm_extraction",
        )
        
        metadata = {
            "relationships": result.relationships,
            "candidate_associations": result.candidate_associations,
            "model_identifier": self.model_identifier,
        }

        # Original conversation turn text is preserved as 'content'
        return MemoryItem(
            user_id=turn.user_id,
            memory_type=MemoryType.EPISODIC,
            status=MemoryStatus.ACTIVE,
            content=turn.text,
            summary=result.summary,
            entities=result.entities,
            topics=result.topics,
            emotional_context=emotional_context,
            temporal_context=temporal_context,
            provenance=provenance,
            scoring=scoring_state,
            metadata=metadata,
        )


class HeuristicMemoryEncoder:
    """A simple heuristic encoder for testing or fallback when LLM is unavailable."""
    
    def __init__(self, identifier: str = "heuristic-encoder-v1") -> None:
        self.identifier = identifier

    async def encode(self, turn: ConversationTurn) -> MemoryItem:
        # Simple extraction logic
        words = turn.text.split()
        summary = turn.text[:50] + ("..." if len(turn.text) > 50 else "")
        topics = ["conversation"]
        if "?" in turn.text:
            topics.append("question")
            
        emotional_context = EmotionalContext(
            valence=0.0,
            arousal=0.2,
            dominant_emotion="neutral",
            affect_source="inferred",
        )
        
        temporal_context = TemporalContext(
            occurred_at=turn.created_at,
        )
        
        provenance = ProvenanceRecord(
            source_type="user_message",
            source_id=turn.turn_id,
            created_at=_utc_now(),
            confidence=0.5,
            method="heuristic_extraction",
        )

        metadata = {
            "model_identifier": self.identifier,
        }

        return MemoryItem(
            user_id=turn.user_id,
            memory_type=MemoryType.EPISODIC,
            status=MemoryStatus.ACTIVE,
            content=turn.text,
            summary=summary,
            entities=[],
            topics=topics,
            emotional_context=emotional_context,
            temporal_context=temporal_context,
            provenance=provenance,
            scoring=ScoringState(importance=0.3),
            metadata=metadata,
        )
