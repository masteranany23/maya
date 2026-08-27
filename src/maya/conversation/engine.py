from __future__ import annotations

from uuid import UUID

from maya.core.models import (
    AffectState,
    ChatResponse,
    ConversationTurn,
    ResponsePlan,
)
from maya.core.protocols import AffectAnalyzer, LLMProvider, PersonaStore
from maya.memory.manager import DefaultMemoryManager
from maya.memory.models import MemoryItem, MemoryType, ProvenanceRecord, RecallCue


class ConversationEngine:
    def __init__(
        self,
        *,
        memory_manager: DefaultMemoryManager,
        persona_store: PersonaStore,
        affect_analyzer: AffectAnalyzer,
        llm: LLMProvider,
    ) -> None:
        self.memory_manager = memory_manager
        self.persona_store = persona_store
        self.affect_analyzer = affect_analyzer
        self.llm = llm

    async def chat(
        self, *, user_id: UUID, conversation_id: UUID, message: str
    ) -> ChatResponse:
        # 1. Create ConversationTurn
        turn = ConversationTurn(user_id=user_id, text=message)

        # 2. Load WorkingMemory
        working_memory = await self.memory_manager.get_working_memory(user_id, conversation_id)

        # 3. Update recent turns
        working_memory.recent_turns.append(turn)
        if len(working_memory.recent_turns) > 10:
            working_memory.recent_turns.pop(0)

        # 4. Analyze affect
        affect: AffectState = await self.affect_analyzer.analyze(turn)

        # 5. Derive recall cues
        cue = RecallCue(
            user_id=user_id,
            text_query=message,
            limit=5,
        )

        # 6. MemoryManager.remember()
        recall_results = await self.memory_manager.remember(cue)

        # 7. Add selected memories to WorkingMemory
        working_memory.active_memories = [r.memory for r in recall_results]

        # 8. Response planning
        plan = ResponsePlan(
            intent="general_conversation",
            stance="warm and context-sensitive",
            goals=["answer the user", "avoid unsupported claims", "use relevant memory only"],
            memory_ids=[m.id for m in working_memory.active_memories],
        )

        # If no supporting memory, validate our confidence
        if not working_memory.active_memories:
            plan.goals.append("acknowledge lack of prior context")

        # 9. LLM generation
        persona = await self.persona_store.get_persona()
        profile = await self.persona_store.get_user_profile(str(user_id))
        
        text = await self.llm.generate(
            persona=persona,
            profile=profile,
            memories=working_memory.active_memories,
            affect=affect,
            plan=plan,
            user_message=message,
        )

        # 10/11. Encode and memorize experience
        experience = MemoryItem(
            user_id=user_id,
            memory_type=MemoryType.EPISODIC,
            content=message,
            provenance=ProvenanceRecord(source_type="user_message", method="direct_observation"),
        )
        await self.memory_manager.memorize(experience)

        # 12. Update WorkingMemory (optional - e.g. add the bot's response to recent turns, 
        # but right now we only store user turns. Let's add bot turn if needed, or just return)

        return ChatResponse(
            turn_id=turn.turn_id,
            text=text,
            affect=affect,
            used_memory_ids=[m.id for m in working_memory.active_memories],
        )
