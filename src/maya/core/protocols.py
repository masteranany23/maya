from __future__ import annotations

from typing import Protocol, Any

from maya.core.models import (
    AffectState,
    ConversationTurn,
    Persona,
    ResponsePlan,
    UserProfile,
)


class PersonaStore(Protocol):
    async def get_persona(self) -> Persona: ...

    async def get_user_profile(self, user_id: str) -> UserProfile: ...


class AffectAnalyzer(Protocol):
    async def analyze(self, turn: ConversationTurn) -> AffectState: ...


class LLMProvider(Protocol):
    async def generate(
        self,
        *,
        persona: Persona,
        profile: UserProfile,
        memories: list[Any], # Actually list[MemoryItem] from maya.memory.models
        affect: AffectState,
        plan: ResponsePlan,
        user_message: str,
    ) -> str: ...
