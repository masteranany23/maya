import os
import time
import pytest
from pathlib import Path

from maya.voice.models import ExpressiveSegment, SpeechPlan
from maya.voice.providers.kokoro import KokoroTTSProvider

@pytest.mark.asyncio
async def test_kokoro_smoke_test():
    """
    Smoke test for Kokoro TTS.
    Measures TTFA, latency, and ensures expressive baselines don't crash.
    Skipped if models aren't downloaded to prevent CI failure.
    """
    model_path = os.environ.get("KOKORO_MODEL_PATH", ".models/kokoro-v1.0.onnx")
    voices_path = os.environ.get("KOKORO_VOICES_PATH", ".models/voices-v1.0.bin")
    
    if not Path(model_path).exists() or not Path(voices_path).exists():
        pytest.skip("Kokoro models not downloaded. Skipping smoke test.")
        
    provider = KokoroTTSProvider(model_path=model_path, voices_path=voices_path)
    
    plan = SpeechPlan(segments=[
        ExpressiveSegment(text="Hello world! This is a test of the Kokoro ONNX CPU provider.", speaking_rate=1.0),
        ExpressiveSegment(text="Here is a second segment to test streaming.", speaking_rate=1.2)
    ])
    
    start_time = time.time()
    chunks = []
    
    async for chunk in provider.synthesize(plan):
        if not chunks:
            ttfa = time.time() - start_time
            print(f"\nTime-To-First-Audio (TTFA): {ttfa:.3f}s")
        chunks.append(chunk)
        
    total_time = time.time() - start_time
    assert len(chunks) == 2
    assert len(chunks[0].pcm_data) > 0
    assert chunks[1].is_final is True
    
    print(f"Total generation time: {total_time:.3f}s")
    
    # Expressive Baseline Check (Rate only for Kokoro)
    fast_plan = SpeechPlan(segments=[ExpressiveSegment(text="Fast text.", speaking_rate=1.5)])
    slow_plan = SpeechPlan(segments=[ExpressiveSegment(text="Slow text.", speaking_rate=0.7)])
    
    async for _ in provider.synthesize(fast_plan): pass
    async for _ in provider.synthesize(slow_plan): pass
