from maya.voice.models import ExpressiveSegment, SpeechPlan, TTSCapabilities
from maya.voice.planner import TTSAdapterLayer


def test_tts_adapter_strips_unsupported_features():
    # Base plan with all features
    segment = ExpressiveSegment(
        text="Hello",
        emotion="happy",
        intensity=0.9,
        speaking_rate=1.5,
        pitch_tendency=0.5,
        emphasis_tokens=["Hello"],
        pauses={"after_word": 0.5},
        non_speech_sounds=["laughter"]
    )
    plan = SpeechPlan(segments=[segment])
    
    # Provider with minimal capabilities
    cap = TTSCapabilities(
        supports_pitch_control=False,
        supports_rate_control=False,
        supports_volume_control=False,
        supports_style_tags=False,
        supports_pauses=False,
        supports_emphasis=False,
        supports_non_speech=False,
    )
    
    adapter = TTSAdapterLayer(cap)
    adapted_plan = adapter.adapt(plan)
    adapted_segment = adapted_plan.segments[0]
    
    # Should be stripped to defaults/None
    assert adapted_segment.text == "Hello"
    assert adapted_segment.emotion is None
    assert adapted_segment.intensity == 0.5
    assert adapted_segment.speaking_rate == 1.0
    assert adapted_segment.pitch_tendency == 0.0
    assert adapted_segment.emphasis_tokens == []
    assert adapted_segment.pauses == {}
    assert adapted_segment.non_speech_sounds == []
