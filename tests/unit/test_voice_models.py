import pytest
from pydantic import ValidationError

from maya.voice.models import ExpressiveSegment, TTSCapabilities


def test_expressive_segment_validation():
    # Valid
    seg = ExpressiveSegment(text="Hello", intensity=0.8, speaking_rate=1.5, pitch_tendency=1.0)
    assert seg.intensity == 0.8
    
    # Invalid intensity (too high)
    with pytest.raises(ValidationError):
        ExpressiveSegment(text="Hello", intensity=2.0)
        
    # Invalid speaking rate (too low)
    with pytest.raises(ValidationError):
        ExpressiveSegment(text="Hello", speaking_rate=0.1)

def test_tts_capabilities():
    cap = TTSCapabilities(supports_ssml=True)
    assert cap.supports_ssml is True
    assert cap.supports_streaming is False
