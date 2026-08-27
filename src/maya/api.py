from __future__ import annotations

from typing import Any

from fastapi import FastAPI  # type: ignore

from maya.conversation.engine import ConversationEngine
from maya.core.models import ChatRequest, ChatResponse
from maya.emotion.basic import KeywordAffectAnalyzer
from maya.llm.mock import MockLLMProvider
from maya.memory.manager import DefaultMemoryManager
from maya.memory.recall.activation import SpreadingActivationEngine
from maya.memory.recall.engine import MultiChannelRecallEngine
from maya.memory.recall.keyword import KeywordRecallChannel
from maya.memory.store.in_memory import InMemoryLinkStore, InMemoryReader, InMemoryWriter
from maya.persona.in_memory import InMemoryPersonaStore

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


from fastapi import WebSocket, WebSocketDisconnect


@app.websocket("/v1/voice/stream") # type: ignore
async def voice_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    from uuid import uuid4
    user_id = uuid4()
    
    # We create a dummy VAD, STT, TTS for the session
    from maya.voice.planner import SpeechPlanner
    from maya.voice.providers.mock import MockSTTProvider, MockTTSProvider, MockVADProvider
    from maya.voice.session import VoiceSession
    
    vad = MockVADProvider()
    stt = MockSTTProvider()
    tts = MockTTSProvider()
    planner = SpeechPlanner()
    
    session = VoiceSession(
        user_id=user_id,
        engine=_engine,
        vad=vad,
        stt=stt,
        tts=tts,
        planner=planner,
    )

    # Note: real websocket processing requires a queue to feed the async generators
    try:
        while True:
            data = await websocket.receive_bytes()
            # In a full implementation, we'd pipe this into an async queue
            # that process_user_audio consumes from.
    except WebSocketDisconnect:
        pass
