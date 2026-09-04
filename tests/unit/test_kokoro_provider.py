import sys
from unittest.mock import MagicMock
import pytest
import numpy as np

from maya.voice.models import ExpressiveSegment, SpeechPlan
from maya.voice.providers.kokoro import KokoroTTSProvider

@pytest.fixture(autouse=True)
def mock_kokoro_onnx(monkeypatch):
    mock_kokoro_module = MagicMock()
    mock_kokoro_class = MagicMock()
    mock_kokoro_module.Kokoro = mock_kokoro_class
    monkeypatch.setitem(sys.modules, 'kokoro_onnx', mock_kokoro_module)
    return mock_kokoro_class


@pytest.fixture
def provider():
    return KokoroTTSProvider(model_path="dummy.onnx", voices_path="dummy.bin")


def test_kokoro_capabilities(provider):
    caps = provider.capabilities()
    assert caps.supports_streaming is True
    assert caps.supports_rate_control is True
    assert caps.supports_pitch_control is False
    assert caps.supports_ssml is False
    assert caps.supports_emotion_tags is False if hasattr(caps, "supports_emotion_tags") else True # wait, it's supports_style_tags
    assert caps.supports_style_tags is False


@pytest.mark.asyncio
async def test_synthesize_maps_speed_correctly(provider, monkeypatch, mock_kokoro_onnx):
    monkeypatch.setattr("maya.voice.providers.kokoro.Path.exists", lambda self: True)
    
    mock_instance = MagicMock()
    mock_instance.create.return_value = (np.array([0.0, 0.1, 0.0], dtype=np.float32), 24000)
    mock_kokoro_onnx.return_value = mock_instance
    
    plan = SpeechPlan(segments=[
        ExpressiveSegment(text="Hello", speaking_rate=1.2)
    ])
    
    chunks = []
    async for chunk in provider.synthesize(plan):
        chunks.append(chunk)
        
    assert len(chunks) == 1
    assert chunks[0].is_final is True
    assert len(chunks[0].pcm_data) > 0
    
    mock_instance.create.assert_called_once_with(
        "Hello",
        voice="af_sarah",
        speed=1.2,
        lang="en-us"
    )
