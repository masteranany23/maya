import asyncio
import io
import os
from pathlib import Path
from typing import AsyncGenerator

import numpy as np
import soundfile as sf

from maya.voice.models import AudioChunk, SpeechPlan, TTSCapabilities
from maya.voice.protocols import TTSProvider


class KokoroTTSProvider(TTSProvider):
    def __init__(
        self,
        model_path: str | None = None,
        voices_path: str | None = None,
        default_voice: str = "af_sarah"
    ) -> None:
        self._model_path = model_path or os.environ.get("KOKORO_MODEL_PATH", ".models/kokoro-v1.0.onnx")
        self._voices_path = voices_path or os.environ.get("KOKORO_VOICES_PATH", ".models/voices-v1.0.bin")
        self.default_voice = default_voice
        self._kokoro = None
        
    def capabilities(self) -> TTSCapabilities:
        return TTSCapabilities(
            supports_streaming=True, # Segment-level streaming
            supports_pitch_control=False,
            supports_rate_control=True, # Handled via speed param
            supports_volume_control=False,
            supports_ssml=False,
            supports_style_tags=False,
            supports_pauses=False,
            supports_emphasis=False,
            supports_non_speech=False,
            supported_audio_formats=["wav"]
        )
        
    def _ensure_loaded(self) -> None:
        if self._kokoro is None:
            if not Path(self._model_path).exists() or not Path(self._voices_path).exists():
                raise FileNotFoundError(
                    f"Kokoro model files not found. Ensure {self._model_path} and {self._voices_path} exist."
                )
            # Import lazily to avoid heavy dependencies at startup
            from kokoro_onnx import Kokoro
            self._kokoro = Kokoro(self._model_path, self._voices_path)
            
    async def synthesize(self, plan: SpeechPlan) -> AsyncGenerator[AudioChunk, None]:
        await asyncio.to_thread(self._ensure_loaded)
        
        for i, segment in enumerate(plan.segments):
            is_final = (i == len(plan.segments) - 1)
            
            # Kokoro supports rate control via "speed"
            speed = segment.speaking_rate
            
            # Offload heavy CPU inference to avoid blocking the async event loop
            samples, sample_rate = await asyncio.to_thread(
                self._kokoro.create, # type: ignore
                segment.text,
                voice=self.default_voice,
                speed=speed,
                lang="en-us"
            )
            
            buffer = io.BytesIO()
            sf.write(buffer, samples, sample_rate, format='wav')
            wav_bytes = buffer.getvalue()
            
            yield AudioChunk(data=wav_bytes, format="wav", is_final=is_final)
            
            # Yield control back to the event loop so interruption checks can run
            await asyncio.sleep(0)
