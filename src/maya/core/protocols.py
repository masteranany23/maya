from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, Protocol

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
        recall_results: list[Any], # list[RecallResult] from maya.memory.models
        affect: AffectState,
        plan: ResponsePlan,
        user_message: str,
    ) -> str: ...

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[Any], # Should be type[BaseModel]
    ) -> Any: ...

    async def generate_stream(
        self,
        *,
        persona: Persona,
        profile: UserProfile,
        recall_results: list[Any],
        affect: AffectState,
        plan: ResponsePlan,
        user_message: str,
    ) -> AsyncGenerator[str, None]: ...

