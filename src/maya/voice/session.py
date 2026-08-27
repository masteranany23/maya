import asyncio
from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

from maya.conversation.engine import ConversationEngine
from maya.core.models import AffectState
from maya.voice.buffer import SemanticBuffer
from maya.voice.models import AudioChunk, VADEvent
from maya.voice.planner import SpeechPlanner, TTSAdapterLayer
from maya.voice.protocols import STTProvider, TTSProvider, VADProvider


class VoiceSession:
    """Application-level orchestrator for voice interaction."""
    
    def __init__(
        self,
        *,
        user_id: UUID,
        engine: ConversationEngine,
        vad: VADProvider,
        stt: STTProvider,
        tts: TTSProvider,
        planner: SpeechPlanner,
    ) -> None:
        self.user_id = user_id
        self.conversation_id = uuid4()
        self.engine = engine
        self.vad = vad
        self.stt = stt
        self.tts = tts
        self.planner = planner
        self.adapter = TTSAdapterLayer(self.tts.capabilities())
        
        self._cancel_event = asyncio.Event()

    async def _handle_vad(self, audio_stream: AsyncGenerator[bytes, None]) -> None:
        """Listens for VAD events to trigger barge-in."""
        async for event in self.vad.listen(audio_stream):
            if event == VADEvent.SPEECH_STARTED:
                self._cancel_event.set()
                
    async def process_user_audio(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[AudioChunk, None]:
        """Main entry point for processing an audio stream."""
        self._cancel_event.clear()
        
        # STT converts audio to text stream
        text_stream = self.stt.transcribe(audio_stream)
        
        # engine returns a stream of LLM tokens
        llm_stream = self.engine.chat_stream(
            user_id=self.user_id,
            conversation_id=self.conversation_id,
            text_stream=text_stream,
            cancel_event=self._cancel_event,
        )
        
        buffer = SemanticBuffer()
        semantic_stream = buffer.process_stream(llm_stream)
        
        persona = await self.engine.persona_store.get_persona()
        affect = AffectState() # In real system, this comes from engine analysis
        
        async for phrase in semantic_stream:
            if self._cancel_event.is_set():
                break
                
            plan = self.planner.plan(text=phrase, affect=affect, persona=persona)
            adapted_plan = self.adapter.adapt(plan)
            
            async for chunk in self.tts.synthesize(adapted_plan):
                if self._cancel_event.is_set():
                    break
                yield chunk
