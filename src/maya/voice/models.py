from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ExpressiveSegment(BaseModel):
    """An intermediate representation for a segment of speech, independent of the TTS provider."""
    text: str
    emotion: str | None = None
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch_tendency: float = Field(default=0.0, ge=-1.0, le=1.0) # -1 is falling, 1 is rising
    emphasis_tokens: list[str] = Field(default_factory=list)
    pauses: dict[str, float] = Field(default_factory=dict) # e.g. {"after_word": 0.5}
    non_speech_sounds: list[str] = Field(default_factory=list) # e.g. ["laughter", "breath"]


class SpeechPlan(BaseModel):
    """A planned sequence of expressive segments forming an utterance."""
    segments: list[ExpressiveSegment] = Field(default_factory=list)


class TTSCapabilities(BaseModel):
    """Flags describing what a specific TTS provider supports."""
    supports_streaming: bool = False
    supports_pitch_control: bool = False
    supports_rate_control: bool = False
    supports_volume_control: bool = False
    supports_ssml: bool = False
    supports_style_tags: bool = False
    supports_pauses: bool = False
    supports_emphasis: bool = False
    supports_non_speech: bool = False
    supported_audio_formats: list[str] = Field(default_factory=lambda: ["wav"])


class VADEventType(str, Enum):
    SPEECH_STARTED = "speech_started"
    SPEECH_ENDED = "speech_ended"
    INTERMEDIATE = "intermediate"


class VADEvent(BaseModel):
    """Voice Activity Detection event with rich metadata."""
    type: VADEventType
    timestamp: float = 0.0
    confidence: float = 1.0


class TranscriptEvent(BaseModel):
    """Speech-to-Text transcription event."""
    text: str
    is_final: bool
    confidence: float = 1.0
    timestamp: float = 0.0


class AudioFrame(BaseModel):
    """Provider-neutral wrapper for raw audio streams."""
    pcm_data: bytes
    sample_rate: int = 24000
    channels: int = 1
    timestamp: float = 0.0
    seq: int = 0
    duration: float = 0.0
    metadata: dict[str, str] = Field(default_factory=dict)
    is_final: bool = False


class VoiceSessionState(str, Enum):
    """State machine states for VoiceSession."""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


class CancellationReason(str, Enum):
    """Explicit semantic reasons for cancelling an ongoing process."""
    BARGE_IN = "barge_in"
    USER_HANGUP = "user_hangup"
    TIMEOUT = "timeout"
    SYSTEM_ERROR = "system_error"
