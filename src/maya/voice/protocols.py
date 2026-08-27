from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Protocol

from maya.voice.models import AudioChunk, SpeechPlan, TTSCapabilities, VADEvent


class VADProvider(Protocol):
    """Voice Activity Detection protocol."""
    async def listen(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[VADEvent, None]: ...


class STTProvider(Protocol):
    """Speech-to-Text protocol."""
    async def transcribe(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]: ...


class TTSProvider(Protocol):
    """Text-to-Speech protocol."""
    async def synthesize(self, plan: SpeechPlan) -> AsyncGenerator[AudioChunk, None]: ...
    
    def capabilities(self) -> TTSCapabilities: ...
