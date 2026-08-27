from __future__ import annotations

from maya.core.models import AffectState, MemoryItem, Persona, ResponsePlan, UserProfile


class MockLLMProvider:
    async def generate(
        self,
        *,
        persona: Persona,
        profile: UserProfile,
        memories: list[MemoryItem],
        affect: AffectState,
        plan: ResponsePlan,
        user_message: str,
    ) -> str:
        name = profile.preferred_name
        salutation = f", {name}" if name else ""
        memory_hint = " I remember something relevant from our earlier conversation." if memories else ""
        return f"I hear you{salutation}.{memory_hint} You said: {user_message}"
