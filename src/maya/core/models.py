from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)





class AffectState(BaseModel):
    valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    arousal: float = Field(default=0.0, ge=0.0, le=1.0)
    emotions: dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    trigger: str | None = None


class Persona(BaseModel):
    name: str = "MAYA"
    description: str = "A warm, curious, grounded AI companion."
    values: list[str] = Field(default_factory=list)
    style: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    preferred_name: str | None = None
    facts: dict[str, str] = Field(default_factory=dict)
    preferences: dict[str, str] = Field(default_factory=dict)


class ConversationTurn(BaseModel):
    turn_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    text: str
    created_at: datetime = Field(default_factory=utc_now)


class ResponsePlan(BaseModel):
    intent: str
    stance: str
    goals: list[str] = Field(default_factory=list)
    memory_ids: list[UUID] = Field(default_factory=list)


class ChatRequest(BaseModel):
    user_id: UUID
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    turn_id: UUID
    text: str
    affect: AffectState
    used_memory_ids: list[UUID] = Field(default_factory=list)
