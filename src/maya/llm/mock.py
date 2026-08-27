from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from maya.core.models import AffectState, Persona, ResponsePlan, UserProfile


class MockLLMProvider:
    def __init__(self, structured_responses: dict[type[Any], Any] = None):
        self.structured_responses = structured_responses or {}

    async def generate(
        self,
        *,
        persona: Persona,
        profile: UserProfile,
        recall_results: list[Any],
        affect: AffectState,
        plan: ResponsePlan,
        user_message: str,
    ) -> str:
        name = profile.preferred_name
        salutation = f", {name}" if name else ""
        memory_hint = " I remember something relevant from our earlier conversation." if recall_results else ""
        return f"I hear you{salutation}.{memory_hint} You said: {user_message}"

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[Any],
    ) -> Any:
        if schema in self.structured_responses:
            return self.structured_responses[schema]
        
        # Try to return a default-constructed schema if possible, or raise
        try:
            return schema()
        except Exception:
            raise ValueError(f"No mock response configured for schema {schema.__name__}")

    async def generate_stream(
        self,
        *,
        persona: Persona,
        profile: UserProfile,
        recall_results: list[Any],
        affect: AffectState,
        plan: ResponsePlan,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        if not recall_results:
            yield "I have "
            yield "no specific "
            yield "memories about this."
            return

        yield f"Response based on {len(recall_results)} "
        yield "memories."
