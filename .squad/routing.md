# Experiment Routing

> How work flows through the ARC-informed squad configuration.

## Agent Routing Table

| Task Type | First Agent | Then | Verifier |
|-----------|------------|------|----------|
| Any task | Coordinator | Explorer → Specialist | Verifier |
| Simple factual | Coordinator | Specialist (no Explorer needed) | Verifier |
| Multi-step technical | Coordinator | Explorer → Specialist → Specialist | Verifier |
| Implicit goal | Coordinator | Explorer → Specialist | Verifier × 2 |
| Novel/OOD | Coordinator | Explorer × 2 → Specialist | Verifier × 3 |

## Phase Flow

```
[Task Input]
    ↓
[Coordinator] — Establishes world model, lists constraints, success criteria, unknowns
    ↓
[Explorer] — Identifies what information is missing; outputs "exploration report"
    ↓
[Specialist] — Executes with ARC prompt contract; reads coordinator world model + explorer report
    ↓
[Verifier] — Reviews output vs. world model; triggers refinement if mismatch detected
    ↓
(Refinement loop: Specialist → Verifier, max 3 cycles)
    ↓
[Scribe] — Records action count, revision count, final output, SHAE score
    ↓
[Task Complete]
```

## Escalation Rules

- If Verifier flags mismatch after 3 cycles → escalate to human (Tamir Dresher)
- If Explorer cannot resolve information gap → Coordinator requests human clarification
- If SHAE < 0.2 on familiar task → flag for prompt contract review

## Baseline vs. ARC-Informed Routing

| | Baseline Squad | ARC-Informed Squad |
|---|---|---|
| First move | Specialist executes | Coordinator scaffolds + Explorer probes |
| Failure handling | Simple retry | Refinement loop (max 3) |
| State tracking | Session memory | Explicit world-model scratchpad |
| Success measure | Task completed: yes/no | Task completed + SHAE score |
