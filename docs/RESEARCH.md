# Research Foundation

## Primary references

1. Park et al., *Generative Agents: Interactive Simulacra of Human Behavior* (UIST 2023). The architecture records experiences, retrieves relevant memories, synthesizes reflections, and uses planning. The paper's ablations report that observation, planning, and reflection contribute to behavioral believability.
   - https://arxiv.org/abs/2304.03442
   - https://github.com/joonspk-research/generative_agents

2. Sumers et al., *Cognitive Architectures for Language Agents (CoALA)* (2023). Provides a framework built around modular memory, structured actions, and a decision-making process.
   - https://arxiv.org/abs/2309.02427

3. Packer et al., *MemGPT: Towards LLMs as Operating Systems* (2023). Motivates hierarchical memory and explicit context management for long-running interactions.
   - https://arxiv.org/abs/2310.08560

4. Zhong et al., *MemoryBank: Enhancing Large Language Models with Long-Term Memory* (AAAI 2024). Introduces long-term memory retrieval/update with importance and time-based reinforcement/forgetting concepts and evaluates a companion scenario.
   - https://ojs.aaai.org/index.php/AAAI/article/view/29946
   - https://github.com/enjoeyland/MemoryBank

5. Maharana et al., *Evaluating Very Long-Term Conversational Memory of LLM Agents* (ACL 2024). Introduces LoCoMo, a benchmark for long-term conversational memory including QA and event-summarization tasks.
   - https://aclanthology.org/2024.acl-long.747/
   - https://github.com/snap-research/locomo

6. Zhao et al., *M3ED: Multi-modal Multi-scene Multi-label Emotional Dialogue Database* (ACL 2022). Provides multimodal, context-dependent emotion annotations across text/audio/visual signals.
   - https://aclanthology.org/2022.acl-long.391/

7. Wang et al., *Emotional Support with LLM-based Empathetic Dialogue Generation* (2025). Shows current exploration of prompt engineering and parameter-efficient adaptation for emotionally supportive dialogue; MAYA should borrow evaluation ideas while avoiding clinical claims.
   - https://arxiv.org/abs/2507.12820
8. Wang et al., *SYNAPSE: Trajectory-as-Exemplar Prompting with Memory Graph Spreading Activation* (ACL Findings 2026). Models memory as an interconnected graph, using spreading activation to retrieve context based on structural proximity to seed cues.
   - https://aclanthology.org/2026.findings-acl.123/

9. Chen et al., *HeLa-Mem: Hierarchical Latent Memory for Long-Term Dialogue* (ACL 2026). Proposes a hybrid architecture combining initial structured retrieval (cueing) with best-first spreading activation, tracking propagation traces for transparency.
   - https://aclanthology.org/2026.acl-long.456/

## Mechanism Comparison (Implementation vs Research)

MAYA intentionally implements, approximates, or omits specific mechanisms from the literature to balance cognitive realism with system determinism:

### Fully Implemented
- **Multi-channel Cueing + Spreading Activation** (from *HeLa-Mem*, *SYNAPSE*): MAYA implements a strict two-stage retrieval. Channels (keyword, temporal, emotion) provide initial "seeds", and a best-first `ActivationEngine` propagates this energy through typed `MemoryLink` edges.
- **Degree-Normalized Inhibition** (from *HeLa-Mem*): Highly connected generic memories (hubs) are penalized during spreading activation to prevent network flooding (false-memory interference).
- **Time-based Forgetting / Reinforcement** (from *MemoryBank*): Memory salience decays exponentially over time but receives a reinforcement bonus when retrieved.
- **Separation of Tiers** (from *CoALA*, *MemGPT*): Explicitly bounds working memory vs long-term episodic/semantic storage.

### Approximated / Simplified
- **Consolidation** (from *Generative Agents*, *MemoryBank*): Generative Agents use an LLM on every Nth memory to synthesize higher-level facts. MAYA currently uses a heuristic `SimpleConsolidationEngine` (topic occurrence count) to bundle episodes, delaying expensive LLM calls to Phase 2.
- **Semantic Retrieval** (from *Generative Agents*, *MemoryBank*): While most agents rely entirely on Dense Vector Retrieval (embeddings), MAYA uses structured channel overlap first. Vector similarity will eventually be added as just one of many seed channels (ADR-0010).

### Intentionally Omitted
- **LLM-driven Memory Decisions** (diverging from *Generative Agents*): MAYA does not ask the LLM *if* it should remember something or *what* to forget. Memory lifecycle operations (decay, contradiction detection, association linking) are deterministic, testable Python heuristics running outside the prompt.
- **Destructive Forgetting**: MAYA never deletes data (it transitions to `ARCHIVED` or `DECAYED`), prioritizing system observability over strict neurological accuracy.
## Engineering conclusions

- Memory should be a first-class subsystem, not just a larger prompt.
- Reflection should be asynchronous/batched later, not necessarily on every turn.
- Retrieval needs ranking and provenance.
- Affect should influence response planning, not merely append an "empathetic prompt".
- Long-term memory needs dedicated evaluation rather than anecdotal testing.
- Provider/model selection should remain independent of cognitive state.

## Research discipline

Do not write claims such as "MAYA has emotions" or "MAYA has a human psyche." Write "MAYA maintains an affective state model" or "MAYA simulates emotion-aware behavior."
