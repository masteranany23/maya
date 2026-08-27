from uuid import uuid4

from maya.core.models import ConversationTurn
from maya.emotion.basic import KeywordAffectAnalyzer


async def test_positive_affect_signal() -> None:
    result = await KeywordAffectAnalyzer().analyze(
        ConversationTurn(user_id=uuid4(), text="I am really excited, this is awesome")
    )
    assert result.valence > 0
    assert result.confidence > 0
