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

## Engineering conclusions

- Memory should be a first-class subsystem, not just a larger prompt.
- Reflection should be asynchronous/batched later, not necessarily on every turn.
- Retrieval needs ranking and provenance.
- Affect should influence response planning, not merely append an "empathetic prompt".
- Long-term memory needs dedicated evaluation rather than anecdotal testing.
- Provider/model selection should remain independent of cognitive state.

## Research discipline

Do not write claims such as "MAYA has emotions" or "MAYA has a human psyche." Write "MAYA maintains an affective state model" or "MAYA simulates emotion-aware behavior."
