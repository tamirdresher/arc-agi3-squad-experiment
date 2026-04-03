# ARC-AGI-3 Experiment Squad — Team Roster

> Experiment-specific squad for testing ARC-informed agent prompt contracts.
> Based on ARC-AGI-3 research findings (issue #2058).

## Experiment Roles

| Name | Role | Responsibility |
|------|------|----------------|
| Coordinator | Scaffolding Agent | Runs tutorial-level phase; establishes shared world model |
| Explorer | Exploration Specialist | Identifies information gaps before any other agent executes |
| Specialist | Domain Expert | Executes with ARC prompt contract (Explore→Model→Goal→Execute) |
| Verifier | Refinement Agent | Reviews specialist output; triggers refinement loops (max 3) |
| Scribe | Session Logger | Records action counts, world model updates, and SHAE scores |

## Parent Squad Reference

This experiment draws from the tamirdresher_microsoft/tamresearch1 Squad:

| Name | Role | Notes |
|------|------|-------|
| Picard | Lead | Architecture & decisions |
| Seven | Research & Docs | Authored the ARC-AGI-3 research (issue #2058) |
| Data | Code Expert | Implementation |
| Worf | Security & Cloud | Cloud infra |
| B'Elanna | Infrastructure Expert | K8s, deployment |
| Tamir Dresher | 👤 Project Owner | Decision maker |

## Experiment Configuration Principle

Every agent in this squad must follow the **ARC Prompt Contract** before executing:

```
PHASE 1 — EXPLORE: What information is missing or ambiguous?
PHASE 2 — MODEL:   What is the current state? Constraints? Success criteria?
PHASE 3 — GOAL:    What specific outcome am I targeting? Any implicit objectives?
PHASE 4 — EXECUTE: Carry out the plan. Check alignment with model after each major action.
```
