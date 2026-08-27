from maya.core.models import AffectState, Persona, ResponsePlan
from maya.voice.models import ExpressiveSegment, SpeechPlan, TTSCapabilities


class SpeechPlanner:
    """Plans expressive speech segments based on text, affect, and persona."""
    
    def plan(
        self, 
        text: str, 
        affect: AffectState, 
        persona: Persona, 
        response_plan: ResponsePlan | None = None
    ) -> SpeechPlan:
        """Generates a SpeechPlan from semantic text chunks."""
        segment = ExpressiveSegment(text=text)
        stance = response_plan.stance.lower() if response_plan else ""
        
        primary_emotion = None
        if affect.emotions:
            primary_emotion = max(affect.emotions.items(), key=lambda x: x[1])[0]

        if affect.confidence < 0.4 or "uncertain" in stance or primary_emotion == "uncertain":
            segment.emotion = "uncertain"
            segment.speaking_rate = 0.9
            segment.pitch_tendency = 0.2
            segment.intensity = 0.4
        elif primary_emotion == "comforting" or "comfort" in stance or (affect.valence > 0.1 and affect.arousal < 0.3):
            segment.emotion = "comforting"
            segment.speaking_rate = 0.85
            segment.pitch_tendency = -0.2
            segment.intensity = 0.4
        elif primary_emotion == "excited" or (affect.valence > 0.5 and affect.arousal > 0.8):
            segment.emotion = "excited"
            segment.speaking_rate = 1.3
            segment.pitch_tendency = 0.8
            segment.intensity = 0.9
        elif primary_emotion == "surprised" or (affect.arousal > 0.7 and -0.2 <= affect.valence <= 0.2):
            segment.emotion = "surprised"
            segment.speaking_rate = 1.2
            segment.pitch_tendency = 0.9
            segment.intensity = 0.7
        elif primary_emotion == "happy" or (affect.valence > 0.3 and affect.arousal >= 0.3):
            segment.emotion = "happy"
            segment.speaking_rate = 1.1
            segment.pitch_tendency = 0.5
            segment.intensity = 0.6
        elif primary_emotion == "angry" or (affect.valence < -0.3 and affect.arousal > 0.6):
            segment.emotion = "angry"
            segment.speaking_rate = 1.2
            segment.pitch_tendency = -0.4
            segment.intensity = 0.9
        elif primary_emotion == "sad" or (affect.valence < -0.3 and affect.arousal <= 0.4):
            segment.emotion = "sad"
            segment.speaking_rate = 0.8
            segment.pitch_tendency = -0.5
            segment.intensity = 0.3
        else:
            segment.emotion = "neutral"
            segment.speaking_rate = 1.0
            segment.pitch_tendency = 0.0
            segment.intensity = 0.5
            
        return SpeechPlan(segments=[segment])


class TTSAdapterLayer:
    """Adapts a SpeechPlan to the specific capabilities of a TTS provider."""
    
    def __init__(self, capabilities: TTSCapabilities) -> None:
        self.capabilities = capabilities
        
    def adapt(self, plan: SpeechPlan) -> SpeechPlan:
        """Downgrades unsupported features based on capabilities."""
        adapted_segments = []
        for segment in plan.segments:
            adapted = segment.model_copy()
            
            if not self.capabilities.supports_pitch_control:
                adapted.pitch_tendency = 0.0
                
            if not self.capabilities.supports_rate_control:
                adapted.speaking_rate = 1.0
                
            if not self.capabilities.supports_volume_control:
                adapted.intensity = 0.5
                
            if not self.capabilities.supports_style_tags and not self.capabilities.supports_ssml:
                adapted.emotion = None
                
            if not self.capabilities.supports_pauses:
                adapted.pauses = {}
                
            if not self.capabilities.supports_emphasis:
                adapted.emphasis_tokens = []
                
            if not self.capabilities.supports_non_speech:
                adapted.non_speech_sounds = []
                
            adapted_segments.append(adapted)
            
        return SpeechPlan(segments=adapted_segments)
