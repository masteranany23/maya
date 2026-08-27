from __future__ import annotations

from uuid import UUID

from maya.core.models import (
    AffectState,
    ChatResponse,
    ConversationTurn,
    MemoryItem,
    MemoryType,
    ResponsePlan,
)
from maya.core.protocols import AffectAnalyzer, LLMProvider, MemoryStore, PersonaStore


class ConversationEngine:
    def __init__(
        self,
        *,
        memory_store: MemoryStore,
        persona_store: PersonaStore,
        affect_analyzer: AffectAnalyzer,
        llm: LLMProvider,
    ) -> None:
        self.memory_store = memory_store
        self.persona_store = persona_store
        self.affect_analyzer = affect_analyzer
        self.llm = llm

    async def chat(self, *, user_id: UUID, message: str) -> ChatResponse:
        turn = ConversationTurn(user_id=user_id, text=message)
        persona = await self.persona_store.get_persona()
        profile = await self.persona_store.get_user_profile(str(user_id))
        affect: AffectState = await self.affect_analyzer.analyze(turn)
        memories = await self.memory_store.search(str(user_id), message)
        plan = ResponsePlan(
            intent="general_conversation",
            stance="warm and context-sensitive",
            goals=["answer the user", "avoid unsupported claims", "use relevant memory only"],
            memory_ids=[m.id for m in memories],
        )
        text = await self.llm.generate(
            persona=persona,
            profile=profile,
            memories=memories,
            affect=affect,
            plan=plan,
            user_message=message,
        )
        await self.memory_store.add(
            MemoryItem(
                memory_type=MemoryType.EPISODIC,
                content=message,
                source="explicit_user_message",
                confidence=1.0,
                importance=0.25,
                metadata={"user_id": str(user_id), "turn_id": str(turn.turn_id)},
            )
        )
        return ChatResponse(
            turn_id=turn.turn_id,
            text=text,
            affect=affect,
            used_memory_ids=[m.id for m in memories],
        )
