# MAYA — Modular Human-Like Virtual Companion

MAYA is an experimental, research-grounded virtual companion designed around explicit cognitive, affective, memory, persona, and relationship modules. 

Instead of relying on a single massive "act human" system prompt, MAYA maintains structured state around the LLM, creating a deterministic, auditable, and modular cognitive pipeline:

`Input → Understanding → Memory Retrieval → Affect/Relationship Update → Response Planning → Generation → TTS Voice Synthesis`

The architecture is heavily influenced by prominent agent research including *Generative Agents*, *CoALA*, *MemGPT*, *MemoryBank*, and *LoCoMo*.

---

## 🧠 Cognitive Architecture

MAYA does not rely on opaque LLM context windows. It features a robust, multi-tier cognitive architecture:

1. **Working Memory & Turn Lifecycle**: Manages short-term context and handles interruptions dynamically.
2. **Multi-Channel Retrieval & Spreading Activation**: Retrieves long-term memories using hybrid cues (Keyword, Temporal, Emotion, Associative) and propagates activation energy through a graph of memory links (ADR-0011).
3. **Memory Lifecycle Operations**:
   - **Importance Scoring**: Evaluates the significance of new experiences.
   - **Decay & Reinforcement**: Forgets unused memories over time via exponential decay, and reinforces frequently recalled memories.
   - **Consolidation**: Synthesizes clustered episodic memories into semantic knowledge.
   - **Contradiction Detection**: Identifies and resolves conflicting information in memory.
4. **Persistent Storage**: All memories and relationship graphs are safely persisted using a robust SQLite adapter.

---

## 🗣️ Voice Integration & Expressive Synthesis (Phase 3)

MAYA features a duplex, streaming-ready voice subsystem designed for low-latency, emotionally expressive interactions:

1. **Separation of WHAT and HOW (ADR-0014)**: The conversation engine streams raw semantic text, which is buffered by a `SemanticBuffer` into natural phrases. A `SpeechPlanner` then evaluates MAYA's internal `AffectState` to generate a structured `SpeechPlan` (dictating emotion, pitch, and speaking rate).
2. **Capability Downgrade**: A `TTSAdapterLayer` safely degrades unsupported emotional parameters into flat formats if the target provider lacks advanced controls.
3. **Barge-in / Interruption**: The `VoiceSession` orchestrator supports instant VAD-triggered barge-in. Interruptions immediately halt audio synthesis and LLM generation, securely logging the interrupted turn into `WorkingMemory` without data loss.
4. **Local CPU Voice (Kokoro ONNX) (ADR-0015)**: The primary TTS provider is `KokoroTTSProvider`, utilizing the 82M parameter Kokoro model via ONNX. It runs entirely locally on CPU with an extremely small RAM footprint (<300MB), achieving near real-time Time-To-First-Audio (TTFA).

---

## 🚀 Current State

MAYA is currently completing **Phase 3 (Voice Integration)**. 
It possesses a full end-to-end cognitive memory pipeline backed by SQLite, and a streaming voice architecture capable of dynamic emotion mapping and local CPU-bound synthesis via Kokoro.

## 🛠️ Getting Started

### 1. Requirements
- Python 3.11+
- OS: Ubuntu/Linux (Recommended), macOS, or Windows.
- No dedicated GPU is required (optimized for CPU/8GB RAM).

### 2. Setup
Clone the repository and set up your virtual environment:
```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### 3. Download Voice Models (Kokoro)
To enable local voice synthesis, download the Kokoro ONNX model weights. This is required before running voice interactions:
```bash
python3 scripts/download_kokoro.py
```
*(This downloads `kokoro-v1.0.onnx` and `voices-v1.0.bin` into `.models/`)*

### 4. Running the Application
To run the primary application API:
```bash
uvicorn maya.api:app --reload
```

To run a quick voice demo showcasing MAYA's expressive synthesis (requires models to be downloaded):
```bash
PYTHONPATH=src python3 scratch/demo_voice.py
```

### 5. Running Tests
MAYA has an extensive test suite verifying cognitive rules, memory graphs, and voice architectures.
```bash
PYTHONPATH=src pytest
```

---

## 📖 Documentation
- `docs/ARCHITECTURE.md`: Deep dive into the cognitive and orchestration pipeline.
- `docs/RESEARCH.md`: Academic references and engineering conclusions.
- `docs/DECISIONS.md`: Architectural Decision Records (ADRs).
- `docs/ROADMAP.md`: High-level phase planning.
- `docs/TASKS.md`: Granular tracking of current implementation progress.
