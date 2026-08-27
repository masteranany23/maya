import pytest

from maya.voice.buffer import SemanticBuffer


async def mock_stream(chunks: list[str]):
    for chunk in chunks:
        yield chunk

@pytest.mark.asyncio
async def test_semantic_buffer_splits_on_boundaries():
    buffer = SemanticBuffer()
    
    # "Hello there! " -> "Hello there!"
    # "How are you? I am " -> "How are you?"
    # "good." -> "I am good."
    
    chunks = [
        "Hello th",
        "ere! Ho",
        "w are yo",
        "u? I am ",
        "good."
    ]
    
    stream = buffer.process_stream(mock_stream(chunks))
    results = [phrase async for phrase in stream]
    
    assert results == [
        "Hello there!",
        "How are you?",
        "I am good."
    ]

@pytest.mark.asyncio
async def test_semantic_buffer_handles_newlines():
    buffer = SemanticBuffer()
    chunks = ["First line.\nSecond", " line\nThird line"]
    
    stream = buffer.process_stream(mock_stream(chunks))
    results = [phrase async for phrase in stream]
    
    assert results == [
        "First line.",
        "Second line",
        "Third line"
    ]
