import asyncio
from collections.abc import AsyncGenerator

from maya.voice.models import AudioFrame, SpeechPlan, TTSCapabilities, VADEvent, VADEventType, TranscriptEvent
from maya.voice.protocols import STTProvider, TTSProvider, VADProvider


class MockVADProvider(VADProvider):
    """A mock VAD provider that yields nothing by default."""
    async def listen(self, audio_stream: AsyncGenerator[AudioFrame, None]) -> AsyncGenerator[VADEvent, None]:
        async for _ in audio_stream:
            # Yield control
            await asyncio.sleep(0.01)
        yield VADEvent(type=VADEventType.SPEECH_ENDED)


class MockSTTProvider(STTProvider):
    """A mock STT provider that yields a static transcript."""
    async def transcribe(self, audio_stream: AsyncGenerator[AudioFrame, None]) -> AsyncGenerator[TranscriptEvent, None]:
        async for _ in audio_stream:
            pass
        yield TranscriptEvent(text="Hello, this is a mock transcription.", is_final=True)


class MockTTSProvider(TTSProvider):
    """A mock TTS provider that yields the text as bytes."""
    def capabilities(self) -> TTSCapabilities:
        return TTSCapabilities(
            supports_streaming=True,
            supports_pitch_control=True,
            supports_rate_control=True,
            supports_volume_control=True,
            supports_style_tags=True,
        )

    async def synthesize(self, plan: SpeechPlan) -> AsyncGenerator[AudioFrame, None]:
        for segment in plan.segments:
            await asyncio.sleep(0.1) # Simulate synthesis time
            yield AudioFrame(pcm_data=segment.text.encode("utf-8"), is_final=False)
            
        yield AudioFrame(pcm_data=b"", is_final=True)
