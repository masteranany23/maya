from __future__ import annotations

from uuid import UUID

from maya.core.models import Persona, UserProfile


class InMemoryPersonaStore:
    def __init__(self) -> None:
        self._persona = Persona(
            name="MAYA",
            description="A warm, observant, curious AI companion who values honesty and user agency.",
            values=["honesty", "curiosity", "kindness", "user agency"],
            style=["natural", "warm", "not overly verbose", "context-sensitive"],
            boundaries=["do not claim consciousness", "do not invent memories"],
        )
        self._profiles: dict[UUID, UserProfile] = {}

    async def get_persona(self) -> Persona:
        return self._persona

    async def get_user_profile(self, user_id: str) -> UserProfile:
        uid = UUID(user_id)
        if uid not in self._profiles:
            self._profiles[uid] = UserProfile(user_id=uid)
        return self._profiles[uid]
