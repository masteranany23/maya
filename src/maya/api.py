from __future__ import annotations

from typing import Any
from fastapi import FastAPI  # type: ignore
from maya.persona.in_memory import InMemoryPersonaStore

from maya.conversation.engine import ConversationEngine
from maya.core.models import ChatRequest, ChatResponse
from maya.emotion.basic import KeywordAffectAnalyzer
from maya.llm.mock import MockLLMProvider
from maya.memory.store.in_memory import InMemoryWriter, InMemoryReader, InMemoryLinkStore
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.manager import DefaultMemoryManager

app = FastAPI(title="MAYA", version="0.1.0")

_storage: dict[Any, Any] = {}
_writer = InMemoryWriter(_storage)
_reader = InMemoryReader(_storage)
_link_store = InMemoryLinkStore()

from uuid import UUID
from maya.memory.models import MemoryLink

async def _get_links(mid: UUID) -> list[MemoryLink]:
    return await _link_store.get_links(mid, direction="both")

_activation_engine = SpreadingActivationEngine(link_getter=_get_links)
_recall_engine = MultiChannelRecallEngine(
    channels=[KeywordRecallChannel()],
    reader=_reader,
    activation_engine=_activation_engine,
)
_memory_manager = DefaultMemoryManager(
    writer=_writer,
    reader=_reader,
    recall_engine=_recall_engine,
)

_persona = InMemoryPersonaStore()
_engine = ConversationEngine(
    memory_manager=_memory_manager,
    persona_store=_persona,
    affect_analyzer=KeywordAffectAnalyzer(),
    llm=MockLLMProvider(),
)


@app.get("/health")  # type: ignore
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "maya"}


@app.post("/v1/chat", response_model=ChatResponse)  # type: ignore
async def chat(request: ChatRequest) -> ChatResponse:
    from uuid import uuid4
    return await _engine.chat(user_id=request.user_id, conversation_id=uuid4(), message=request.message)
