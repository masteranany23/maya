from __future__ import annotations

from fastapi import FastAPI

from maya.conversation.engine import ConversationEngine
from maya.core.models import ChatRequest, ChatResponse
from maya.emotion.basic import KeywordAffectAnalyzer
from maya.llm.mock import MockLLMProvider
from maya.memory.in_memory import InMemoryStore
from maya.persona.in_memory import InMemoryPersonaStore


app = FastAPI(title="MAYA", version="0.1.0")

_memory = InMemoryStore()
_persona = InMemoryPersonaStore()
_engine = ConversationEngine(
    memory_store=_memory,
    persona_store=_persona,
    affect_analyzer=KeywordAffectAnalyzer(),
    llm=MockLLMProvider(),
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "maya"}


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await _engine.chat(user_id=request.user_id, message=request.message)
