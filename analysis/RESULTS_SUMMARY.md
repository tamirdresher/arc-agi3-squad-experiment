# ARC-AGI-3 Squad Experiment V2.1 — Results Summary

## Abstract

We evaluated the ARC behavioral contract (a 4-pillar structured reasoning framework: Explore, Model, Goal, Execute) against Baseline and Chain-of-Thought (CoT) prompting across 50 diverse tasks (750 total runs) using claude-sonnet-4 via Copilot CLI. All three conditions achieved near-perfect correctness (Baseline: 98.0%, CoT: 100.0%, ARC: 100.0%), producing a ceiling effect that prevented meaningful differentiation. The primary hypothesis (H1: ARC > Baseline by ≥15pp) was not supported. The secondary hypothesis (H2: ARC > CoT by ≥10pp) was not supported. The model's inherent capability dominated task outcomes regardless of prompting strategy.

## Key Findings

| Finding | Detail |
|---------|--------|
| Overall correctness | Baseline 98.0%, CoT 100.0%, ARC 100.0% |
| Ceiling effect | Model too capable for task battery — 745/750 runs correct |
| H1 (ARC > Baseline) | **NOT SUPPORTED** — 2.0pp observed vs 15pp predicted |
| H2 (ARC > CoT) | **NOT SUPPORTED** — 0.0pp observed vs 10pp predicted |
| H3 (Efficiency parity) | **SUPPORTED** — 9.5% token overhead |
| H5 (Non-inferiority on adversarial) | **SUPPORTED** — ARC did not degrade on B-tasks |
| Only failures | T21 (ambiguous spec) under Baseline — all 5 runs |

## Statistical Evidence Summary

| Test | H1 (ARC>Base) | H2 (ARC>CoT) |
|------|---------------|---------------|
| Fisher's exact | p=0.0306, OR=inf | p=1.0000, OR=inf |
| McNemar's (majority vote) | p=1.0000 (1 discordant) | p=1.0000 (0 discordant) |

## Limitations

1. **Ceiling effect (primary):** claude-sonnet-4 achieves >98% on all conditions, leaving no room for improvement to detect
2. **Automated scoring:** Rule-based scoring instead of human scoring (protocol §5 calls for human scorers)
3. **Single model:** Results may differ for weaker models where structured reasoning could provide more lift
4. **Task difficulty:** The 50-task battery was insufficiently challenging for this model's capability level
5. **CLI constraints:** Temperature, sampling parameters not controllable (held constant by CLI)

## Conclusion

The ARC 4-pillar behavioral contract does not improve correctness over either Baseline or Chain-of-Thought prompting when the underlying model (claude-sonnet-4) is already highly capable. The structured reasoning framework is not harmful (H5 supported) but provides no measurable correctness benefit on this task battery. Future work should test with (a) harder task batteries that push model accuracy below 80%, (b) weaker models where structured reasoning may provide more differentiation, and (c) multi-turn agentic tasks where the 4-phase structure may matter more than in single-turn evaluation.
