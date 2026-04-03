# Experiment Decisions Log

---

## Decision 001: ARC-Informed Prompt Contract Adopted

**Date:** 2026-03-28
**Decision Maker:** Seven (Research & Docs), Tamir Dresher (Project Owner)
**Issue:** tamirdresher_microsoft/tamresearch1#2058

### Context

ARC-AGI-3 (arXiv:2603.24621) reveals four capability gaps that doom current AI on complex agentic tasks:
1. Failing to explore before committing
2. Failing to build world models
3. Relying on memorized pattern-matching
4. Losing efficiency when plans need mid-task revision

### Decision

Adopt the four-phase ARC Prompt Contract as the behavioral baseline for all agents in this experiment:
- **Explore** before acting
- **Model** the environment explicitly
- **Set goals** including implicit ones
- **Execute with course-correction**

### Rationale

ARC-AGI-3's RHAE scoring metric (Relative Human Action Efficiency) shows that correctness alone is insufficient — efficiency under novelty is the real measure of intelligence. A squad that completes tasks through excessive retries scores near zero, even if the output is eventually correct.

---

## Decision 002: SHAE Metric as Primary Success Measure

**Date:** 2026-03-28
**Decision Maker:** Seven (Research & Docs)

### Decision

Adopt SHAE (Squad Human Action Efficiency), analogous to ARC's RHAE metric:

```
SHAE = (human_baseline_actions / agent_actions)²
```

A score of 1.0 = perfect human-equivalent efficiency. Scores below 0.25 indicate brute-force completion.

### Target Thresholds

| Task Type | SHAE Target |
|-----------|-------------|
| Simple factual | ≥ 0.7 |
| Multi-step technical | ≥ 0.5 |
| Implicit goal | ≥ 0.4 |
| Novel/OOD variants | ≥ 0.3 |

---

## Decision 003: Three-Cycle Refinement Loop Maximum

**Date:** 2026-03-28
**Decision Maker:** Seven (Research & Docs)

### Decision

Cap refinement loops at 3 cycles (generate → verify → refine × 3 max).

### Rationale

Inspired by NVIDIA NVARC's ARC Prize 2025 approach. Prevents infinite loops while enabling the generate→verify→refine pattern that demonstrated 24% ARC-AGI-2 accuracy.
