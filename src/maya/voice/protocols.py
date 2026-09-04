from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Protocol

from maya.voice.models import AudioFrame, SpeechPlan, TTSCapabilities, VADEvent, TranscriptEvent


class VADProvider(Protocol):
    """Voice Activity Detection protocol."""
    async def listen(self, audio_stream: AsyncGenerator[AudioFrame, None]) -> AsyncGenerator[VADEvent, None]: ...


class STTProvider(Protocol):
    """Speech-to-Text protocol."""
    async def transcribe(self, audio_stream: AsyncGenerator[AudioFrame, None]) -> AsyncGenerator[TranscriptEvent, None]: ...


class TTSProvider(Protocol):
    """Text-to-Speech protocol."""
    async def synthesize(self, plan: SpeechPlan) -> AsyncGenerator[AudioFrame, None]: ...
    
    def capabilities(self) -> TTSCapabilities: ...
