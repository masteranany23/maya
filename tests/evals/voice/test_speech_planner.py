import pytest
from maya.core.models import AffectState, Persona, ResponsePlan
from maya.voice.planner import SpeechPlanner
from maya.voice.models import TTSCapabilities
from maya.voice.planner import TTSAdapterLayer


@pytest.fixture
def planner():
    return SpeechPlanner()


@pytest.fixture
def persona():
    return Persona()


def test_speech_planner_expressive_states(planner, persona):
    text = "I see what you mean."
    
    # 1. Neutral
    affect = AffectState(valence=0.0, arousal=0.0, confidence=1.0)
    plan = planner.plan(text, affect, persona)
    assert plan.segments[0].emotion == "neutral"
    
    # 2. Happy
    affect = AffectState(valence=0.8, arousal=0.5, confidence=1.0)
    plan = planner.plan(text, affect, persona)
    assert plan.segments[0].emotion == "happy"
    
    # 3. Excited
    affect = AffectState(valence=0.9, arousal=0.9, confidence=1.0)
    plan = planner.plan(text, affect, persona)
    assert plan.segments[0].emotion == "excited"
    
    # 4. Sad
    affect = AffectState(valence=-0.8, arousal=0.1, confidence=1.0)
    plan = planner.plan(text, affect, persona)
    assert plan.segments[0].emotion == "sad"
    
    # 5. Angry
    affect = AffectState(valence=-0.9, arousal=0.9, confidence=1.0)
    plan = planner.plan(text, affect, persona)
    assert plan.segments[0].emotion == "angry"
    
    # 6. Surprised
    affect = AffectState(valence=0.0, arousal=0.9, confidence=1.0)
    plan = planner.plan(text, affect, persona)
    assert plan.segments[0].emotion == "surprised"
    
    # 7. Comforting (Using stance)
    affect = AffectState(valence=0.2, arousal=0.1, confidence=1.0)
    response_plan = ResponsePlan(intent="support", stance="comforting and warm", goals=[])
    plan = planner.plan(text, affect, persona, response_plan)
    assert plan.segments[0].emotion == "comforting"
    
    # 8. Uncertain (Using confidence)
    affect = AffectState(valence=0.0, arousal=0.0, confidence=0.2)
    plan = planner.plan(text, affect, persona)
    assert plan.segments[0].emotion == "uncertain"

    # Verify that different emotional states produce materially different speech attributes
    # We will test two extremes
    excited_plan = planner.plan(text, AffectState(valence=0.9, arousal=0.9, confidence=1.0), persona)
    sad_plan = planner.plan(text, AffectState(valence=-0.9, arousal=0.1, confidence=1.0), persona)
    
    assert excited_plan.segments[0].speaking_rate > sad_plan.segments[0].speaking_rate
    assert excited_plan.segments[0].intensity > sad_plan.segments[0].intensity
    assert excited_plan.segments[0].pitch_tendency > sad_plan.segments[0].pitch_tendency


def test_speech_planner_graceful_degradation(planner, persona):
    text = "I see what you mean."
    
    # Generate an excited plan (uses pitch, rate, intensity, emotion tags)
    affect = AffectState(valence=0.9, arousal=0.9, confidence=1.0)
    plan = planner.plan(text, affect, persona)
    
    # A fully unsupported TTS provider
    cap = TTSCapabilities(
        supports_pitch_control=False,
        supports_rate_control=False,
        supports_volume_control=False,
        supports_style_tags=False,
        supports_ssml=False,
    )
    
    adapter = TTSAdapterLayer(cap)
    adapted = adapter.adapt(plan)
    
    seg = adapted.segments[0]
    
    # Original text is preserved
    assert seg.text == text
    
    # Expressive attributes are downgraded to neutral/None
    assert seg.emotion is None
    assert seg.pitch_tendency == 0.0
    assert seg.speaking_rate == 1.0
    assert seg.intensity == 0.5
