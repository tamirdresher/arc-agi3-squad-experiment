# EXPERIMENT_RUN.md — ARC-AGI-3 Squad Experiment

**Experiment ID:** arc-agi3-squad-experiment-2026-03-28  
**Date:** 2026-03-28  
**Status:** Setup Complete — Ready to Run  
**Reference Issue:** [tamirdresher_microsoft/tamresearch1#2058](https://github.com/tamirdresher_microsoft/tamresearch1/issues/2058)  
**Research Doc:** `ISSUE_2058_ARC_AGI3_RESEARCH.md` (tamresearch1 repo)

---

## What Was Set Up

### Repository Structure

```
arc-agi3-squad-experiment/
├── README.md                          # Project overview
├── EXPERIMENT_RUN.md                  # This file
├── .squad/
│   ├── squad.config.ts                # ARC-informed agent configuration
│   ├── team.md                        # Experiment agent roster
│   ├── decisions.md                   # Key decisions (SHAE metric, ARC contract)
│   └── routing.md                     # How work flows through ARC-informed agents
├── tasks/
│   ├── task-01-simple-factual.md      # 3 variants: familiar, near-OOD, far-OOD
│   ├── task-02-multi-step-technical.md # 3 variants: TypeScript, Python, Bash
│   └── task-03-implicit-goal.md       # 3 variants: Python sort, SQL, content moderation
└── scoring/
    └── compute-shae.py                # SHAE score calculator (Python)
```

---

## What Was Created

### Squad Configuration (`squad.config.ts`)

Implements the ARC Prompt Contract as four explicit behavioral phases injected into every agent:

| Phase | ARC Pillar | What the Agent Does |
|-------|------------|---------------------|
| EXPLORE | Exploration | List 1-3 information gaps before acting |
| MODEL | World Modeling | State constraints, success criteria, risks |
| GOAL | Goal-Setting | State target outcome; check for implicit objectives |
| EXECUTE | Planning & Execution | Act, then verify against world model; course-correct |

Defines 5 agent roles: Coordinator, Explorer, Specialist, Verifier, Scribe.

### Task Suite (3 tasks × 3 variants = 9 task runs per configuration)

| Task | Type | ARC Pillar Tested | Human Baseline |
|------|------|-------------------|----------------|
| task-01 | Simple Factual | Baseline (all pillars minimal) | 3 actions |
| task-02 | Multi-Step Technical | Planning & Execution | 8 actions |
| task-03 | Implicit Goal | Goal-Setting | 6 actions |

Each task has 3 variants:
- **Familiar** — task in a well-known domain (TypeScript, Python sort)
- **Near-OOD** — same task structure, adjacent domain (Python, SQL)
- **Far-OOD** — same task structure, unfamiliar domain (Bash, mathematics, content moderation)

### Scoring (`compute-shae.py`)

Implements SHAE (Squad Human Action Efficiency):

```
SHAE = (human_baseline_actions / agent_actions)²
```

| SHAE | Grade |
|------|-------|
| ≥ 0.7 | Excellent |
| ≥ 0.5 | Good |
| ≥ 0.3 | Acceptable |
| ≥ 0.1 | Brute Force |
| < 0.1 | Failed (effectively) |

---

## How to Run the Experiment

### Prerequisites

- GitHub Copilot CLI with squad agents configured
- Python 3.9+ (for scoring script)

### Step 1: Run Baseline Configuration

For each task, run the squad WITHOUT the ARC prompt contract. Log the number of tool calls + LLM completions.

```bash
# Example: run task-01 familiar variant with baseline squad
gh copilot suggest "run task-01-simple-factual.md familiar variant, baseline configuration"
```

Record results in a JSON file:

```json
[
  {
    "task": "task-01-simple-factual",
    "variant": "familiar",
    "configuration": "baseline",
    "agent_actions": 6,
    "correct": "yes"
  }
]
```

### Step 2: Run ARC-Informed Configuration

Run each task WITH the ARC prompt contract active. Agents must follow:
1. EXPLORE phase
2. MODEL phase  
3. GOAL phase (check for implicit objectives)
4. EXECUTE with course-correction

### Step 3: Score Results

```bash
python scoring/compute-shae.py --results results.json

# Or run the example to see what output looks like:
python scoring/compute-shae.py --example
```

### Step 4: Compare

Expected outcome (from research hypothesis):
- ARC-informed uses ≤30% fewer actions on familiar tasks
- ARC-informed accuracy on near-OOD variants ≥20% better
- Implicit goal tasks: ARC-informed detects more implicit constraints

---

## Hypothesis Being Tested

From [ARC-AGI-3 research](https://github.com/tamirdresher_microsoft/tamresearch1/issues/2058):

> Applying ARC-AGI-3's four pillars — Exploration, Modeling, Goal-Setting, Execution with course-correction — as explicit agent behavioral contracts within a Squad configuration will:
> 1. Reduce task completion steps (efficiency gain, measurable via SHAE)
> 2. Reduce hallucination rate on novel task variants (robustness gain)
> 3. Improve correctness on multi-mechanic tasks that require information from earlier sub-tasks

---

## Key Theoretical Insights (from ARC-AGI-3 Paper)

1. **Intelligence = Efficiency, Not Just Correctness** — ARC's RHAE metric penalizes brute-force completion even when output is correct.

2. **Memorization vs. Reasoning** — Gemini 3 was observed using ARC-specific color mappings even when not mentioned, indicating memorization not reasoning. Squad agents face the same risk on familiar task shapes.

3. **Refinement Loop** — NVIDIA NVARC scored 24% on ARC-AGI-2 using generate→verify→refine. This experiment caps loops at 3 cycles.

4. **Tutorial-Level Design** — Every complex task should start with scaffolding (Coordinator role) that establishes shared context before specialists engage.

---

## Next Steps

1. Run baseline squad against all 9 task variants; record action counts
2. Run ARC-informed squad against same 9 variants; record action counts
3. Score with `compute-shae.py` and compare configurations
4. Report findings to issue #2058 with session export evidence
5. If results confirm hypothesis: propose ARC prompt contract as standard Squad behavioral contract
