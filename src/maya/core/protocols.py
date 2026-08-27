from __future__ import annotations

from typing import Protocol

from maya.core.models import (
    AffectState,
    ConversationTurn,
    MemoryItem,
    Persona,
    ResponsePlan,
    UserProfile,
)


class MemoryStore(Protocol):
    async def add(self, item: MemoryItem) -> MemoryItem: ...

    async def search(self, user_id: str, query: str, limit: int = 8) -> list[MemoryItem]: ...


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
        memories: list[MemoryItem],
        affect: AffectState,
        plan: ResponsePlan,
        user_message: str,
    ) -> str: ...
