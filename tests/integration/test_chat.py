from uuid import uuid4

from maya.conversation.engine import ConversationEngine
from maya.emotion.basic import KeywordAffectAnalyzer
from maya.llm.mock import MockLLMProvider
from maya.memory.in_memory import InMemoryStore
from maya.persona.in_memory import InMemoryPersonaStore


async def test_chat_writes_episodic_memory() -> None:
    memory = InMemoryStore()
    engine = ConversationEngine(
        memory_store=memory,
        persona_store=InMemoryPersonaStore(),
        affect_analyzer=KeywordAffectAnalyzer(),
        llm=MockLLMProvider(),
    )
    user_id = uuid4()
    response = await engine.chat(user_id=user_id, message="hello Maya")
    assert response.text
    found = await memory.search(str(user_id), "hello")
    assert len(found) == 1
    assert found[0].source == "explicit_user_message"
