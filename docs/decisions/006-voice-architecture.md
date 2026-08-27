# ADR-0014 — Voice Architecture Separation of WHAT and HOW
Status: Accepted

## Context
Phase P3 requires adding voice (VAD, STT, TTS) to the cognitive pipeline. Simply pipelining LLM text directly to TTS creates unnatural speech because LLM tokens are unstructured bytes, and direct LLM generation cannot optimally control prosody without deep provider coupling. Also, TTS providers vary wildly in capability (some support SSML, some support raw emotional tags, some just read text).

## Decision
1. **Semantic Buffering**: We introduce a `SemanticBuffer` that accumulates LLM token streams into natural phrase/sentence boundaries before any speech processing occurs.
2. **WHAT vs HOW**: We decouple "WHAT MAYA says" (LLM generation) from "HOW MAYA says it" (`SpeechPlanner`). 
3. **SpeechIntent IR**: We define an intermediate representation, `SpeechPlan` (composed of `ExpressiveSegment`s), capturing emotion, intensity, rate, pitch, emphasis, and pauses in a provider-agnostic way.
4. **Capability Downgrade**: A `TTSAdapterLayer` intercepts the `SpeechPlan` and strips or alters features (like removing SSML or pitch controls) based on a specific `TTSProvider`'s declared `TTSCapabilities`.
5. **Barge-In Lifecycle**: We use a `VoiceSession` orchestrator to listen to `VADEvent`s. When speech starts, it triggers an immediate `cancel_event`, aborting TTS synthesis, and recording `interrupted=True` in the `ConversationTurn`.

## Consequences
- **Positive**: Complete provider independence. We can swap a basic local TTS with a premium emotional TTS without changing cognitive logic. Interruption latency is minimal.
- **Negative**: The buffering stage adds a slight Time-To-First-Audio (TTFA) delay compared to pure token-by-token streaming, but this is an acceptable tradeoff for natural prosody.
