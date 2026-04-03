# ARC-AGI-3 Squad Experiment

**Testing ARC-informed agent prompt contracts for the Squad multi-agent framework**

[![Research Issue](https://img.shields.io/badge/Issue-%232058-blue)](https://github.com/tamirdresher_microsoft/tamresearch1/issues/2058)
[![Research Paper](https://img.shields.io/badge/arXiv-2603.24621-red)](https://arxiv.org/abs/2603.24621)

---

## Overview

ARC-AGI-3 (March 2026) is the first fully interactive AI benchmark where agents must explore environments, infer goals, build world models, and plan — all without instructions. **Humans score 100%. Frontier AI scores 0.26%.**

The four capability gaps that doom current AI on ARC-AGI-3 are the same gaps that limit Squad agents on complex real-world tasks:

| ARC Pillar | Squad Failure Mode |
|---|---|
| Exploration | Agents jump to execution before understanding context |
| World Modeling | Agents lack state across multi-step tasks |
| Goal-Setting | Agents miss implicit objectives |
| Planning & Execution | Agents don't adapt when early assumptions fail |

This experiment tests whether explicitly embedding ARC's four pillars as **behavioral contracts** in Squad agent prompts improves efficiency and robustness.

## Hypothesis

> Applying ARC-AGI-3's four pillars as explicit agent behavioral contracts will reduce task completion steps by ≥30%, reduce hallucination on novel task variants, and improve correctness on compositional tasks.

## The ARC Prompt Contract

Every agent in the ARC-informed configuration must follow this contract before executing:

```
PHASE 1 — EXPLORE: What information is missing or ambiguous? List 1-3 gaps.
PHASE 2 — MODEL:   State constraints, success criteria, and risks explicitly.
PHASE 3 — GOAL:    State the target outcome. Check for implicit objectives.
PHASE 4 — EXECUTE: Act. After each major action, verify against the world model.
```

## Structure

```
.squad/
  squad.config.ts        ← ARC-informed agent configuration
  team.md                ← Experiment agent roster
  decisions.md           ← Key decisions (SHAE metric, 3-cycle refinement cap)
  routing.md             ← How work flows through ARC-informed agents
tasks/
  task-01-simple-factual.md       ← 3 variants
  task-02-multi-step-technical.md ← 3 variants (TypeScript, Python, Bash)
  task-03-implicit-goal.md        ← 3 variants (Python sort, SQL, content mod)
scoring/
  compute-shae.py        ← SHAE score calculator
EXPERIMENT_RUN.md        ← Full setup description and how to run
```

## Scoring: SHAE

SHAE (Squad Human Action Efficiency) = `(human_baseline_actions / agent_actions)²`

Analogous to ARC-AGI-3's RHAE metric. A score of 1.0 = perfect efficiency. Brute-force correct answers score near zero.

```bash
python scoring/compute-shae.py --example
```

## Running the Experiment

See [`EXPERIMENT_RUN.md`](./EXPERIMENT_RUN.md) for detailed instructions.

## References

- **Primary paper:** [ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence](https://arxiv.org/abs/2603.24621), arXiv:2603.24621, March 2026
- **ARC Prize:** https://arcprize.org/blog/arc-agi-3-launch
- **ARC-AGI-3 Agents GitHub:** https://github.com/arcprize/ARC-AGI-3-Agents
- **Research report:** [tamirdresher_microsoft/tamresearch1#2058](https://github.com/tamirdresher_microsoft/tamresearch1/issues/2058)
- **Parent Squad framework:** [bradygaster/squad](https://github.com/bradygaster/squad)
ARC-AGI-3 Squad Experiment — testing ARC-informed agent prompt contracts
