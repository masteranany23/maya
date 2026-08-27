import asyncio
from collections.abc import AsyncGenerator

from maya.voice.models import AudioChunk, SpeechPlan, TTSCapabilities, VADEvent


class MockVADProvider:
    async def listen(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[VADEvent, None]:
        async for _ in audio_stream:
            # Just consume
            pass
        yield VADEvent.SPEECH_ENDED


class MockSTTProvider:
    async def transcribe(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
        async for chunk in audio_stream:
            yield chunk.decode("utf-8")


class MockTTSProvider:
    def capabilities(self) -> TTSCapabilities:
        return TTSCapabilities(
            supports_streaming=True,
            supports_pitch_control=False,
            supports_rate_control=True,
            supports_volume_control=True,
            supports_ssml=False,
        )

    async def synthesize(self, plan: SpeechPlan) -> AsyncGenerator[AudioChunk, None]:
        for segment in plan.segments:
            yield AudioChunk(data=segment.text.encode("utf-8"), is_final=False)
            await asyncio.sleep(0.01)
        yield AudioChunk(data=b"", is_final=True)
