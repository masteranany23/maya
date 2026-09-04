import asyncio
import logging
from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

from maya.conversation.engine import ConversationEngine
from maya.core.models import AffectState
from maya.voice.buffer import SemanticBuffer
from maya.voice.models import AudioFrame, VADEvent, VADEventType, VoiceSessionState, TranscriptEvent
from maya.voice.planner import SpeechPlanner, TTSAdapterLayer
from maya.voice.protocols import STTProvider, TTSProvider, VADProvider
from maya.voice.router import AudioRouter

logger = logging.getLogger(__name__)


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
        
        self.state = VoiceSessionState.IDLE
        self._cancel_event = asyncio.Event()
        self._router = AudioRouter()
        
    async def _handle_vad(self, vad_stream: AsyncGenerator[VADEvent, None]) -> None:
        """Listens for VAD events to trigger barge-in."""
        async for event in vad_stream:
            if event.type == VADEventType.SPEECH_STARTED:
                if self.state in (VoiceSessionState.THINKING, VoiceSessionState.SPEAKING):
                    logger.info("VAD: Speech started. Triggering barge-in interruption.")
                    self.state = VoiceSessionState.INTERRUPTED
                    self._cancel_event.set()

    async def _extract_text_from_stt(self, stt_stream: AsyncGenerator[TranscriptEvent, None]) -> AsyncGenerator[str, None]:
        async for event in stt_stream:
            if event.is_final:
                yield event.text

    async def process_user_audio(self, audio_stream: AsyncGenerator[AudioFrame, None]) -> AsyncGenerator[AudioFrame, None]:
        """Main entry point for processing an audio stream."""
        self._cancel_event.clear()
        self.state = VoiceSessionState.LISTENING
        
        # 1. Route microphone audio to both VAD and STT
        await self._router.start(audio_stream)
        
        vad_audio = self._router.subscribe()
        stt_audio = self._router.subscribe()
        
        # 2. Start background VAD listener
        vad_task = asyncio.create_task(self._handle_vad(self.vad.listen(vad_audio)))
        
        try:
            # 3. Transcribe audio to text events
            text_stream = self._extract_text_from_stt(self.stt.transcribe(stt_audio))
            
            # 4. Thinking / Language Generation
            self.state = VoiceSessionState.THINKING
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
            
            # 5. Speaking / Synthesis
            async for phrase in semantic_stream:
                if self._cancel_event.is_set():
                    break
                    
                self.state = VoiceSessionState.SPEAKING
                plan = self.planner.plan(text=phrase, affect=affect, persona=persona)
                adapted_plan = self.adapter.adapt(plan)
                
                async for chunk in self.tts.synthesize(adapted_plan):
                    if self._cancel_event.is_set():
                        break
                    yield chunk
                    
            if self._cancel_event.is_set():
                self.state = VoiceSessionState.INTERRUPTED
            else:
                self.state = VoiceSessionState.IDLE
                
        finally:
            vad_task.cancel()
            await self._router.stop()
