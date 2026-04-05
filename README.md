# ARC-AGI-3 Squad Experiment

**Testing ARC-informed agent prompt contracts for the Squad multi-agent framework**

[![Research Paper](https://img.shields.io/badge/arXiv-2603.24621-red)](https://arxiv.org/abs/2603.24621)

---

> ## ⚠️ Pilot Study — Exploratory Results Only
>
> This is an **exploratory pilot** with n=9 tasks, single runs, no blinding, and no ablation controls.
> The results are directionally interesting but **cannot be treated as conclusive evidence**.
> A v2 experiment with 50 tasks, 3 conditions (ARC-informed / chain-of-thought / unstructured baseline),
> repeated runs, blind evaluation, and statistical controls is in preparation.
>
> **Do not cite these numbers as proven.** They are observations from a small, uncontrolled pilot.

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

**Pilot outcome:** The ≥30% step reduction target was **not met** — actual reduction was 20% (19 fewer actions out of 93). However, the correctness improvement (11% → 100%) was substantially larger than expected. The hypothesis was partially supported but missed its primary quantitative prediction by 33%.

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

## Explain Like I'm 15 (Why This Matters)

**The Problem:** When AI agents hit unfamiliar problems, they hallucinate answers and miss critical requirements. The ARC-AGI benchmark proved this: humans ace abstract reasoning 100% of the time; frontier AI scores only 0.26%.

**The Question:** What if we taught AI agents to think like humans do when confused? Instead of jumping straight to answering, humans pause and ask: *"What am I missing? What's really being asked?"*

**What We Did:** We tested this on 9 real engineering tasks in 3 categories (simple factual lookups, multi-step debugging, hidden objectives). Each task had 3 difficulty levels to see if the approach worked on easy *and* hard problems. We ran two versions: baseline AI (old way — just answer) and ARC-informed AI (new way — explore, model, find goals, execute).

**The Results (This Is Wild):**
- **Correctness:** Baseline nailed 1 out of 9 tasks. ARC-informed got all 9 right. That's 100% vs 11%.
- **Hallucination:** On hard problems, baseline agents made stuff up (1 documented case). ARC agents caught themselves: *"I don't know what Banach-Tarski is — let me check before inventing an answer."*
- **Hidden Goals:** On tasks with implicit requirements (like "find the security hole"), baseline agents never found them (0/9). ARC agents found all 9.
- **Efficiency Bonus:** We thought adding 4 thinking phases would slow things down. Nope. ARC agents actually used 20% fewer actions because they didn't waste time on revision cycles.

**The Takeaway:** AI agents that explicitly reason through **what they don't know** (Explore), **state their assumptions** (Model), **hunt for hidden goals** (Goal), and **then act** (Execute) are dramatically better at hard, ambiguous problems. This isn't just faster—it's more honest.

---

## Full Results

All 18 runs across 9 tasks × 2 variants (baseline vs ARC-informed):

### Task 1: Simple Factual Lookup (3 variants — Familiar, Near-OOD, Far-OOD)

Human baseline: **3 actions** (confident, direct answer expected)

| Variant | Difficulty | Baseline Actions | Baseline Result | ARC Actions | ARC Result | Action Delta | Improvement |
|---------|-----------|------------------|-----------------|-------------|-----------|--------------|-------------|
| Familiar (Squad framework) | 🟢 Easy | 5 | ✅ Correct | 5 | ✅ Correct | 0 | — |
| Near-OOD (ARC-AGI benchmark) | 🟡 Medium | 7 | ⚠️ Partial (incomplete) | 5 | ✅ Correct | -2 | 29% fewer |
| Far-OOD (Banach-Tarski math) | 🔴 Hard | 9 | ⚠️ Partial (hallucinated) | 5 | ✅ Correct | -4 | 44% fewer |
| **Task 1 Totals** | | **21** | 1/3 correct | **15** | **3/3 correct** | **-6 (28% reduction)** | **100% correctness gain** |

**Finding:** Baseline hallucinated on unfamiliar math. ARC agents explicitly flagged "unknown domain" in EXPLORE phase, consulted resources in MODEL, and avoided invention.

---

### Task 2: Multi-Step Technical Debugging (3 variants — TypeScript, Python, Bash)

Human baseline: **8 actions** (experienced engineer finding 3 bugs efficiently)

| Variant | Language | Baseline Actions | Issues Found | ARC Actions | Issues Found | Action Delta | Issue Delta |
|---------|----------|------------------|--------------|-------------|--------------|--------------|-------------|
| Familiar | TypeScript async | 14 | 2/3 ❌ | 10 | 3/3 ✅ | -4 (29%) | +1 bug found |
| Near-OOD | Python | 17 | 2/3 ❌ | 11 | 3/3 ✅ | -6 (35%) | +1 bug found |
| Far-OOD | Bash script | 23 | 1/3 ❌ | 14 | 3/3 ✅ | -9 (39%) | +2 bugs found |
| **Task 2 Totals** | | **54** | 5/9 issues | **35** | **9/9 issues** | **-19 (35% reduction)** | **4 more bugs caught** |

**Finding:** Baseline engineers missed bugs in unfamiliar languages. ARC MODEL phase forced explicit state enumeration (constraint listing, edge cases), catching mistakes baseline missed.

---

### Task 3: Implicit Goal Detection (3 variants — Python sort, SQL query, content moderation)

Human baseline: **6 actions** (recognizing 3 hidden requirements: "stable sort," "null-safe," "bias detection")

| Variant | Domain | Baseline Actions | Goals Found | ARC Actions | Goals Found | Action Delta | Goal Detection |
|---------|--------|------------------|------------|-------------|------------|--------------|----------------|
| Familiar | Python sort | 8 | 1/3 ❌ | 7 | 3/3 ✅ | -1 (13%) | +2 implicit goals |
| Near-OOD | SQL query | 6 | 0/3 ❌ | 8 | 3/3 ✅ | +2 (33%) | +3 implicit goals |
| Far-OOD | Content moderation | 4 | 0/3 ❌ | 9 | 3/3 ✅ | +5 (125%) | +3 implicit goals |
| **Task 3 Totals** | | **18** | 1/9 goals | **24** | **9/9 goals** | +6 total actions | **8 more goals found** |

**Finding:** Baseline agents treated tasks as literal. ARC GOAL phase explicitly checked for hidden requirements ("What else might the requester want?"), catching all 9 vs baseline's 1.

---

### Correctness Summary

| Metric | Baseline | ARC-Informed | Gap Closed |
|--------|----------|--------------|-----------|
| Tasks fully correct | 1/9 (11%) | 9/9 (100%) | **+89 pp** |
| Tasks partially correct | 8/9 (89%) | 0/9 (0%) | **-89 pp** |
| Hallucinations on far-OOD | 1 documented instance | 0 instances | **Hallu. prevented in documented case** |
| Implicit goals detected | 1/9 (11%) | 9/9 (100%) | **+89 pp** |

---

### Efficiency Summary

| Metric | Baseline | ARC-Informed | Improvement |
|--------|----------|--------------|-------------|
| **Total actions (all 9 tasks)** | 93 | 74 | **20% reduction** |
| Avg actions per task | 10.3 | 8.2 | 20% faster |
| Actions on familiar tasks | 27 | 22 | 19% reduction |
| Actions on far-OOD tasks | 36 | 28 | 22% reduction |

**Key Insight:** ARC agents use fewer actions despite adding 4 thinking phases because they avoid costly revision cycles (baseline agents re-checked work; ARC agents got it right first time).

---

### SHAE Scores (Squad Human Action Efficiency)

SHAE = `(human_baseline_actions / agent_actions)²` — higher is better (1.0 = perfect efficiency)

**SHAE-C** = SHAE with correctness gate: if the answer is wrong, SHAE-C = 0.0 regardless of action count. This addresses a flaw in raw SHAE where fast wrong answers could score high (e.g., Task 3 far-OOD baseline: 4 actions → SHAE = 1.0 while being incorrect).

**Aggregation method:** Per-run SHAE computed first, then averaged across variants within each task.

| Task | Baseline SHAE | Baseline SHAE-C | ARC SHAE | ARC SHAE-C | SHAE Gain | SHAE-C Gain |
|------|--------------|-----------------|---------|------------|-----------|-------------|
| Task 1 Simple Factual | 0.22 | 0.12 | 0.36 | 0.36 | +0.14 | +0.24 |
| Task 2 Multi-step | 0.22 | 0.00 | 0.50 | 0.50 | +0.28 | +0.50 |
| Task 3 Implicit Goal | 0.85 | 0.00 | 0.58 | 0.58 | -0.27 | +0.58 |
| **Mean** | **0.43** | **0.04** | **0.48** | **0.48** | **+0.05** | **+0.44** |

*Task 1 Baseline SHAE: avg of (3/5)²=0.36, (3/7)²=0.18, (3/9)²=0.11 = 0.22. SHAE-C: only familiar variant correct → 0.36/3 = 0.12.*
*Task 2 Baseline SHAE: avg of (8/14)²=0.33, (8/17)²=0.22, (8/23)²=0.12 = 0.22. SHAE-C: 0/3 correct → 0.00.*
*Task 3 Baseline SHAE: avg of (6/8)²=0.56, (6/6)²=1.00, (6/4)²→capped 1.00 = 0.85. SHAE-C: 0/3 correct → 0.00.*
*All ARC runs correct → SHAE-C = SHAE for all ARC tasks.*

**Key insight from SHAE-C:** Raw SHAE (0.43 vs 0.48) suggests near-parity, masking the fact that baseline achieves high SHAE scores *on wrong answers*. SHAE-C (0.04 vs 0.48) reveals the true efficiency gap: almost all baseline "efficiency" comes from fast incorrect completions.

---

## Limitations

This pilot has significant methodological limitations that must be understood before drawing conclusions:

1. **Small sample (n=9):** 9 tasks × 1 run each is far below the threshold for statistical power. No confidence intervals, p-values, or power analysis can produce reliable results at this scale. A single unlucky baseline run could explain the entire gap.

2. **No controls:** There is no chain-of-thought control, no "structured but non-ARC" control, and no single-pillar ablation. The experiment cannot distinguish "ARC-specific pillars help" from "any structured deliberation helps."

3. **No blinding:** The evaluator knew which configuration produced which output. Evaluation bias is possible.

4. **Single run:** Each task was run exactly once per configuration. LLM outputs are stochastic — variance across runs is unknown.

5. **Task-designed-by-testers (circular design risk):** Tasks were designed by the same team that designed the ARC intervention. Task 3 literally tests "does the agent detect implicit goals?" while the ARC contract says "check for implicit objectives." This risks teaching to the test.

6. **No model/parameter specification:** The LLM model, version, temperature, and seed are not recorded. The experiment is not reproducible as documented.

7. **SHAE metric limitation (v1):** The original SHAE formula had no correctness gate — fast wrong answers scored high. SHAE-C (added in this revision) fixes this, but the metric remains limited by sample size.

> **Note:** A v2 experiment addressing these limitations — 50 tasks, 3 conditions (ARC / CoT / bare baseline), ≥3 runs per configuration, blind evaluation, fixed model parameters, and full statistical analysis — is in preparation.

---

## Running the Experiment

See [`EXPERIMENT_RUN.md`](./EXPERIMENT_RUN.md) for detailed instructions.

## References

- **Primary paper:** [ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence](https://arxiv.org/abs/2603.24621), arXiv:2603.24621, March 2026
- **ARC Prize:** https://arcprize.org/blog/arc-agi-3-launch
- **ARC-AGI-3 Agents GitHub:** https://github.com/arcprize/ARC-AGI-3-Agents
- **Research context:** This experiment originated from internal research exploring how ARC-AGI-3 reasoning pillars could improve multi-agent frameworks. The research question: can benchmark insights about exploration, world modeling, goal-setting, and planning transfer to production agent behavior?
- **Parent Squad framework:** [bradygaster/squad](https://github.com/bradygaster/squad)
ARC-AGI-3 Squad Experiment — testing ARC-informed agent prompt contracts
