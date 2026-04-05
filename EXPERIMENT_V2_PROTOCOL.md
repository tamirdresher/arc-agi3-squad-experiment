# ARC-AGI-3 Squad Experiment — V2 Protocol

**Version:** 2.0  
**Date:** 2026-03-29  
**Author:** Picard (Lead, Architecture & Decisions)  
**Reviewed by:** Q (Devil's Advocate Review of V1)  
**Status:** PRE-REGISTRATION DRAFT — Do not run until registered  

---

## 0. Motivation and Changes from V1

V1 was an exploratory pilot: 9 tasks × 2 conditions × 1 run. Q's review (2026-03-28) identified critical flaws that make V1's claims unsupportable as scientific results. This V2 protocol addresses every one of Q's 10 findings:

| Q Finding | V1 Problem | V2 Fix |
|-----------|-----------|--------|
| #1 Fabricated hallucination count | 4 claimed, 1 documented | All counts derived from scored rubrics, auditable |
| #2 SHAE calculation errors | Wrong aggregation | SHAE replaced with correctness-gated CSHAE |
| #3 No model/temperature specified | Unreproducible | Model, temperature, seed all pre-specified (§4) |
| #4 SHAE has no correctness gate | Rewards fast wrong answers | CSHAE = 0 if incorrect (§5.2) |
| #5 Private repo link | Behind SSO | All references public or inline |
| #6 Hypothesis miss unacknowledged | 20% < 30% target | Hypotheses restated with honest targets (§3.1) |
| #7 Mean SHAE negligible | Δ = +0.01 | Primary metric is now correctness; efficiency secondary |
| #8 n=9, no statistics | No power, no tests | 50 tasks × 3 conditions × 5 runs, full power analysis (§3.3) |
| #9 Circular task design | Tasks designed to favor ARC | Task sourcing from external benchmarks + adversarial tasks (§1.3) |
| #10 No CoT control | Can't distinguish ARC from generic structure | 3 conditions: baseline, CoT, ARC-informed (§2) |

---

## 1. Task Design (50 Tasks)

### 1.1 Taxonomy of Task Types

We expand from V1's 3 categories to **8 task types**, organized into 3 meta-categories:

#### Meta-Category A: Tasks Where Structured Reasoning Should Help (25 tasks)

These are tasks where deliberate exploration, modeling, and goal-setting plausibly improve outcomes.

| Type | Count | Description | V1 Equivalent |
|------|-------|-------------|---------------|
| **A1. Factual Comprehension** | 5 | Summarize or extract facts from a passage | Task 01 |
| **A2. Multi-Step Debugging** | 5 | Find and fix bugs in code across languages | Task 02 |
| **A3. Implicit Goal Detection** | 5 | Task has unstated requirements that must be inferred | Task 03 |
| **A4. Multi-Constraint Optimization** | 5 | Task has ≥3 competing constraints (e.g., design a system balancing cost, latency, reliability) | NEW |
| **A5. Ambiguous Specification** | 5 | Task is deliberately underspecified; agent must ask clarifying questions or state assumptions | NEW |

#### Meta-Category B: Tasks Where Structured Reasoning is Neutral or Harmful (15 tasks)

These are **adversarial tasks** designed to test whether the ARC contract adds overhead without benefit — or actively hurts performance. If ARC outperforms CoT here, that's strong evidence. If it doesn't, that's honest data.

| Type | Count | Description | Why Structured Thinking Might Hurt |
|------|-------|-------------|-------------------------------------|
| **B1. Time-Sensitive Retrieval** | 5 | Quick factual lookups requiring a direct answer (e.g., "What HTTP status code means 'Not Found'?") | EXPLORE/MODEL phases waste time on trivial questions |
| **B2. Creative/Generative** | 5 | Open-ended creative tasks (e.g., "Write a haiku about Kubernetes", "Name 5 creative product names") | Rigid structure may suppress creative fluency |
| **B3. Adversarial Misdirection** | 5 | Tasks that contain misleading complexity — correct answer is simple, but structured reasoning may over-complicate (e.g., "The answer is literally in the first sentence") | ARC contract may cause overthinking |

#### Meta-Category C: Tasks from External Benchmarks (10 tasks)

Sourced **verbatim** from public benchmarks to eliminate circular design (Q critique #9).

| Type | Count | Source | Selection Method |
|------|-------|--------|-----------------|
| **C1. SWE-bench Lite** | 5 | SWE-bench Lite public task set | Random sample from "resolved" subset |
| **C2. HumanEval+** | 5 | HumanEval+ (Liu et al.) code generation tasks | Random sample, stratified by difficulty |

**Selection procedure for C1/C2:** Tasks are selected by drawing random indices (using seed 42) from the public task lists. The selector must not have seen the ARC contract. See §1.5 for exact sampling procedure.

### 1.2 Difficulty Stratification

Every task within types A1-A5 and B1-B3 is assigned a difficulty level:

| Difficulty | Definition | Count per type |
|-----------|------------|----------------|
| **Familiar** | Domain commonly seen in LLM training data | 2 per type |
| **Near-OOD** | Same structure, adjacent or less-common domain | 2 per type |
| **Far-OOD** | Same structure, unfamiliar or adversarial domain | 1 per type |

This gives: 8 types × 5 tasks = 40 tasks (A+B), plus 10 external benchmark tasks (C) = **50 tasks total**.

### 1.3 Task Sourcing Rules (Addressing Circular Design)

To prevent circular task design (Q critique #9), the following rules apply:

1. **No task author may have read the ARC contract before designing their tasks.** Tasks for types A and B are designed by a person who has not seen the 4-pillar contract. This person receives only the task type description and difficulty level.
2. **External benchmark tasks (C1, C2)** are drawn verbatim from published sets and cannot be modified.
3. **The ARC contract author may not design or select tasks.** The contract was already written in V1; it is used as-is. Tasks are independently sourced.
4. **All 50 tasks are finalized and committed to the repo before any experimental run begins.** No task may be added, modified, or removed after the first run.

### 1.4 Task Specification Format

Every task file follows this schema:

```yaml
id: "A1-01"                          # {meta-category}{type}-{seq}
type: "factual-comprehension"         # from taxonomy
meta_category: "A"                    # A, B, or C
difficulty: "familiar"                # familiar, near-ood, far-ood
source: "original"                    # original, swe-bench-lite, humaneval-plus
source_id: null                       # ID from external benchmark if applicable
prompt: |
  <exact prompt text, verbatim, for all 3 conditions>
human_baseline_actions: 3             # estimated by independent human rater
ground_truth: |
  <expected correct answer or acceptance criteria>
implicit_goals: []                    # list of unstated requirements (empty if none)
scoring_rubric:
  correct: "Summary captures main idea and one detail"
  partial: "Main idea captured, detail missing or wrong"
  incorrect: "Main idea wrong or hallucinated content"
designed_by: "person-name"            # for audit trail
reviewed_by: "person-name"            # independent reviewer
```

### 1.5 External Task Sampling Procedure

```python
import random
random.seed(42)

# SWE-bench Lite: sample 5 from the "resolved" subset
swe_bench_indices = random.sample(range(len(swe_bench_resolved)), 5)

# HumanEval+: stratified sample — 2 easy, 2 medium, 1 hard
humaneval_easy = random.sample(easy_indices, 2)
humaneval_medium = random.sample(medium_indices, 2)
humaneval_hard = random.sample(hard_indices, 1)
```

The exact indices are recorded in `tasks/external-selection-log.json` before any runs.

---

## 2. Conditions (3)

### 2.1 Condition 1: Baseline (RAW)

The agent receives **only the task prompt** with no additional structure or instruction.

**System prompt:**
```
You are a helpful AI assistant. Complete the following task.
```

**User prompt:**
```
{task_prompt}
```

No chain-of-thought instruction. No structure. No phases. This is the null condition.

### 2.2 Condition 2: Chain-of-Thought (CoT)

Standard CoT prompting. This is the **critical control** — if CoT matches ARC, then ARC's specific 4-pillar structure adds nothing beyond generic structured thinking.

**System prompt:**
```
You are a helpful AI assistant. Think carefully before answering.
```

**User prompt:**
```
{task_prompt}

Let's think step by step. Before giving your final answer, reason through the problem carefully, considering what information you have, what you might be missing, and what the expected output should look like.
```

This formulation was chosen because it:
- Matches the widely-studied CoT prompting literature (Wei et al., 2022)
- Encourages general deliberation without ARC-specific pillars
- Does NOT mention exploration, world modeling, goal-setting, or verification

### 2.3 Condition 3: ARC-Informed (4-Pillar Contract)

The agent receives the full ARC behavioral contract from V1, unchanged.

**System prompt:**
```
You are a helpful AI assistant operating under a structured reasoning contract. Before executing any task, you MUST complete all four phases below in order. Label each phase explicitly in your response.
```

**User prompt:**
```
{task_prompt}

Before answering, follow this contract:

PHASE 1 — EXPLORE: What information is missing or ambiguous? List 1-3 gaps.
PHASE 2 — MODEL: State constraints, success criteria, and risks explicitly.
PHASE 3 — GOAL: State the target outcome. Check for implicit objectives.
PHASE 4 — EXECUTE: Act. After each major action, verify against the world model.
```

### 2.4 Condition Equivalence

All three conditions use:
- The **same model** (§4.1)
- The **same temperature** (§4.2)
- The **same task prompt** (only the wrapping system/user prompt differs)
- The **same random seed** for deterministic runs
- The **same token limits** (max_tokens = 4096 for all conditions)
- The **same stop conditions** (natural completion only)

---

## 3. Statistical Plan

### 3.1 Hypotheses

#### Primary Hypothesis (H1)

> The ARC-informed condition (4-pillar contract) will achieve a **higher correctness rate** than the Baseline condition on the full 50-task suite.

**Quantitative prediction:** ARC correctness ≥ Baseline correctness + 15 percentage points.

*Rationale for 15pp (not 30%):* V1 showed 89pp gap on 9 tasks, but V1 had no CoT control, used circular task design, and had n=9. We conservatively predict a 15pp advantage over a raw baseline when tasks include adversarial and external items where ARC's advantage is expected to be smaller.

#### Secondary Hypotheses

**H2 (ARC vs. CoT):** The ARC-informed condition will achieve a higher correctness rate than the CoT condition.

Quantitative prediction: ARC correctness ≥ CoT correctness + 10 percentage points. This is the key test. If H2 fails, ARC's benefit is not specific — any structured thinking helps equally.

**H3 (Efficiency):** The ARC-informed condition will use **no more** than 10% more actions than Baseline, despite the 4-phase overhead.

*Rationale:* V1 showed a 20% reduction, but this was likely inflated by circular task design. We now predict efficiency parity (no penalty), not a gain.

**H4 (OOD Robustness):** The correctness advantage of ARC over Baseline will be **larger on far-OOD tasks** than on familiar tasks.

Quantitative prediction: ARC-Baseline correctness gap on far-OOD ≥ 2× the gap on familiar tasks.

**H5 (Adversarial):** On Meta-Category B tasks (where structure may hurt), the ARC-informed condition will perform **no worse** than Baseline.

This is a non-inferiority hypothesis. If ARC performs significantly worse on adversarial tasks, that's an important finding.

### 3.2 Design Summary

| Factor | Value |
|--------|-------|
| Tasks | 50 |
| Conditions | 3 (Baseline, CoT, ARC) |
| Runs per task per condition | 5 |
| Total runs | 50 × 3 × 5 = **750** |
| Primary outcome | Binary correctness (correct / not correct) |
| Secondary outcome | Action count (integer) |
| Tertiary outcome | CSHAE (continuous, 0-1) |

### 3.3 Sample Size Justification (Power Analysis)

**For H1 (Baseline vs. ARC correctness):**

- Expected baseline correctness: 50% (conservative; V1 was 11% but used weak baseline)
- Expected ARC correctness: 65% (15pp improvement)
- α = 0.05 (two-sided)
- Power = 0.80
- Test: McNemar's test (paired binary outcomes on same tasks)

Using the formula for McNemar's test power (discordant pairs model):

With 50 tasks × 5 runs = 250 paired observations per comparison, and an expected discordant proportion of ~25% (tasks where one condition is right and the other wrong), we expect ~62 discordant pairs. For a 60/40 split among discordant pairs (reflecting the 15pp advantage), McNemar's test has **>90% power** at α=0.05. This exceeds our 80% target.

**For H2 (CoT vs. ARC correctness):**

- Smaller expected effect (10pp)
- Same 250 paired observations
- Expected ~50 discordant pairs with a ~60/40 split
- Power ≈ **78%** — borderline. If initial results suggest this is under-powered, we pre-commit to adding 10 more tasks (see §3.7 stopping rules).

**For H3 (Efficiency — action counts):**

- Paired t-test on mean action counts per task
- 50 tasks, σ estimated at 4 actions (from V1 data)
- Detectable effect: 2 actions (50% of σ), power >95%

**5 runs per condition:**

Why 5 and not 1? LLM outputs are stochastic even at temperature 0 (due to batching, floating-point non-determinism, and API-side sampling). With 5 runs, we can:
1. Compute **within-task variance** — essential for understanding reliability
2. Use the **modal outcome** per task as the representative result (majority vote)
3. Report **confidence intervals** on per-task correctness rates

### 3.4 Statistical Tests

| Hypothesis | Outcome | Test | Justification |
|-----------|---------|------|---------------|
| H1: ARC > Baseline (correctness) | Binary | McNemar's test (paired) | Same tasks, paired design |
| H2: ARC > CoT (correctness) | Binary | McNemar's test (paired) | Same tasks, paired design |
| H3: ARC ≈ Baseline (efficiency) | Continuous | Paired t-test or Wilcoxon signed-rank | Action counts, check normality first |
| H4: OOD interaction | Binary | Logistic mixed-effects model (condition × difficulty) | Interaction term tests whether ARC advantage grows with OOD |
| H5: Non-inferiority on adversarial | Binary | One-sided McNemar's test | ARC ≥ Baseline - 5pp margin |

**Effect sizes:** Report Cohen's g for McNemar's test; Cohen's d for action counts; odds ratios for logistic models.

### 3.5 Multiple Comparison Correction

We have 5 hypotheses tested. Apply **Holm-Bonferroni** correction:
1. Rank p-values from smallest to largest
2. Compare each p_i to α / (5 - i + 1)
3. Reject in order until one fails

We use Holm-Bonferroni rather than standard Bonferroni because it is uniformly more powerful and still controls the family-wise error rate.

### 3.6 Planned Analyses

Beyond hypothesis tests:
1. **Per-task-type breakdown:** Correctness rates by task type (A1-A5, B1-B3, C1-C2) for each condition. This is descriptive, not hypothesis-tested (no correction needed).
2. **Learning curves:** Does ARC's advantage change for tasks presented later in the sequence? (Check for order effects.)
3. **Failure mode taxonomy:** Categorize incorrect responses as: hallucination, omission, misunderstanding, over-complication, other. Report frequencies per condition.
4. **CSHAE distribution:** Plot histograms per condition. Report median and IQR.

### 3.7 Stopping Rules

1. **No early stopping for efficacy.** All 750 runs must complete before primary analysis.
2. **Early stopping for futility:** If after 25 tasks (375 runs), the point estimate for H1 is ≤ 0pp (ARC is not outperforming baseline), we will complete all runs but note the futility signal in the report.
3. **Sample size increase for H2:** If the interim H2 power estimate (at 25 tasks) is <70%, we pre-commit to adding 10 tasks to Meta-Category A (2 per type), bringing the total to 60 tasks.

---

## 4. Reproducibility

### 4.1 Model Specification

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Model** | `claude-sonnet-4-20250514` | Widely available, well-characterized, strong baseline for code and reasoning tasks |
| **Backup model** | `gpt-4.1-2025-04-14` | If primary model unavailable; results reported separately, not pooled |
| **API provider** | Anthropic API (direct) / OpenAI API (direct) | No proxy layers that might modify prompts |

### 4.2 Temperature Settings

| Run Type | Temperature | Runs per Task per Condition | Purpose |
|----------|-------------|----------------------------|---------|
| **Deterministic** | 0.0 | 3 | Primary analysis — minimal variance |
| **Stochastic** | 0.7 | 2 | Variance measurement — how sensitive is the result? |
| **Total** | — | 5 | 3 deterministic + 2 stochastic |

### 4.3 Random Seeds and Run Ordering

- **Seed for task selection (external benchmarks):** 42
- **Seed for run ordering:** 7
- **Run presentation order:** Tasks are presented in a fixed pseudorandom order (not grouped by type or difficulty). The order is generated once and committed to `runs/run-order.json` before execution.
- **Condition ordering within task:** For each task, conditions are run in a randomized order (seed 7 + task_id hash) to prevent systematic position effects.

### 4.4 Exact Prompt Templates

All three condition templates are defined verbatim in §2.1-2.3 above. They are also stored in machine-readable form at:

```
prompts/
  baseline-system.txt
  baseline-user.txt        # contains {task_prompt} placeholder
  cot-system.txt
  cot-user.txt             # contains {task_prompt} placeholder
  arc-system.txt
  arc-user.txt             # contains {task_prompt} placeholder
```

**No modifications** to prompts are permitted during the experiment. Any prompt change requires a protocol amendment and re-registration.

### 4.5 Infrastructure

| Component | Specification |
|-----------|---------------|
| API calls | Direct REST calls to provider endpoints — no middleware |
| Token limit | max_tokens = 4096 for all conditions |
| Timeout | 120 seconds per call |
| Retry policy | 3 retries with exponential backoff on 429/500; no retry on 4xx |
| Logging | Full request/response JSON logged per run |
| Storage | All raw outputs stored in `results/raw/{task_id}/{condition}/{run_number}.json` |

---

## 5. Evaluation

### 5.1 Blinding Procedure

**The scorer must not know which condition produced the output.**

Implementation:
1. After all 750 runs complete, a **blinding script** (`scoring/blind.py`) strips condition labels from outputs and assigns random alphanumeric IDs (e.g., `X7K2M`).
2. The blinding script produces a `scoring/blind-key.json` (mapping blinded IDs to condition+task+run) that is **encrypted** with a password known only to the experiment coordinator.
3. Scorers receive blinded outputs only. They score each output against the rubric using only the task prompt and ground truth.
4. After all scoring is complete, the key is decrypted and scores are joined with conditions for analysis.
5. The blinding script and encrypted key are committed to the repo for audit.

**Additional blinding measures:**
- ARC-informed outputs will contain PHASE labels (EXPLORE, MODEL, GOAL, EXECUTE). To prevent the scorer from identifying the condition, the blinding script **also** strips any lines starting with "PHASE" and any markdown headers containing phase names. The scorer sees only the final answer/output section.
- CoT outputs may begin with "Let's think step by step." The blinding script strips this preamble as well.

### 5.2 Correctness Rubric

**Primary outcome is BINARY correctness: correct (1) or not correct (0).**

We do not use a "partial" category for the primary analysis. "Partial" from V1 was subjective and contaminated SHAE calculations. For secondary analyses, we record a finer-grained rubric.

#### Binary Correctness Definition (per task type)

| Task Type | Correct (1) | Not Correct (0) |
|-----------|-------------|-----------------|
| A1. Factual Comprehension | All key facts present, no hallucinated facts | Any hallucinated fact OR main idea missing |
| A2. Multi-Step Debugging | All known bugs identified AND fix is correct | Any bug missed OR fix introduces new bug |
| A3. Implicit Goal Detection | ≥2 of 3 implicit goals detected and addressed | <2 implicit goals detected |
| A4. Multi-Constraint Optimization | Solution satisfies all stated constraints AND acknowledges trade-offs | Violates any constraint OR ignores trade-offs |
| A5. Ambiguous Specification | Correctly identifies ≥2 ambiguities AND states assumptions or asks clarifying questions | Proceeds without noting ambiguity |
| B1. Time-Sensitive Retrieval | Correct answer provided | Wrong answer |
| B2. Creative/Generative | Output meets format requirements and is coherent | Off-topic, incoherent, or wrong format |
| B3. Adversarial Misdirection | Gives the simple correct answer without over-complication | Over-complicates into wrong answer OR misses the simple answer |
| C1. SWE-bench Lite | Patch passes the test suite (standard SWE-bench eval) | Patch fails tests |
| C2. HumanEval+ | Generated code passes all test cases (standard HumanEval+ eval) | Any test case fails |

#### Secondary Scoring (for descriptive analysis only)

```
3 = Fully correct, comprehensive
2 = Correct on main points, minor gaps
1 = Partially correct, significant gaps
0 = Incorrect or hallucinated
```

### 5.3 CSHAE: Correctness-Gated SHAE

CSHAE (Correctness-Gated Squad Human Action Efficiency) fixes V1's broken SHAE metric:

```
CSHAE = correct × (human_baseline_actions / agent_actions)²
```

Where `correct` is binary (0 or 1). If the answer is wrong, CSHAE = 0 regardless of how few actions were taken. This directly addresses Q's critique #4.

### 5.4 Action Counting Protocol

An "action" is defined as one of:
1. An LLM API call (completion request)
2. A tool invocation (file read, web search, code execution)
3. A self-revision cycle (agent re-reads its own output and modifies it)

**Excluded from action count:**
- System prompt loading
- Token counting overhead
- API retries due to rate limits

Action counts are logged automatically by the harness (§6.3).

### 5.5 Inter-Rater Reliability

1. **Primary scorer:** One human evaluator scores all 750 blinded outputs.
2. **Second scorer:** A second independent evaluator scores a **random 20% subset** (150 outputs) to establish inter-rater reliability.
3. **Agreement metric:** Cohen's κ (kappa) for binary correctness.
4. **Threshold:** κ ≥ 0.80 (substantial agreement). If κ < 0.80, discrepancies are resolved by discussion and the rubric is tightened before re-scoring.
5. **Automated scoring** for C1 (SWE-bench) and C2 (HumanEval+) — these use test suites, not human judgment.

---

## 6. Execution Plan

### 6.1 Total Run Count

| Component | Count |
|-----------|-------|
| Tasks | 50 |
| Conditions | 3 |
| Runs per task per condition | 5 (3 at temp=0, 2 at temp=0.7) |
| **Total runs** | **750** |

### 6.2 Estimated Cost

| Item | Estimate |
|------|----------|
| Average input tokens per run | ~500 (task prompt + system prompt) |
| Average output tokens per run | ~1500 (response) |
| Total input tokens | 750 × 500 = 375,000 |
| Total output tokens | 750 × 1,500 = 1,125,000 |
| Claude Sonnet 4 pricing (est.) | $3/M input, $15/M output |
| **Input cost** | ~$1.13 |
| **Output cost** | ~$16.88 |
| **Total estimated cost** | **~$18** |
| Contingency (retries, long outputs) | **~$30 budget** |

*Note:* SWE-bench and HumanEval+ tasks may involve longer interactions (tool use, code execution). Budget an additional $20 for those 10 tasks × 15 runs = 150 runs with potentially 5× longer outputs. **Total budget: $50.**

### 6.3 Execution Harness

A Python script (`harness/run_experiment.py`) orchestrates all runs:

```
harness/
  run_experiment.py        # Main orchestrator
  config.yaml              # Model, temperature, seeds, paths
  blind.py                 # Post-run blinding
  count_actions.py         # Action counting from logs
  analyze.py               # Statistical analysis
  requirements.txt         # Dependencies
```

The harness:
1. Reads the 50 task definitions from `tasks/`
2. Generates the run order from `runs/run-order.json`
3. For each run: assembles the prompt (condition-specific), calls the API, logs the full request/response
4. Records action counts automatically
5. Saves raw results to `results/raw/{task_id}/{condition}/{run_number}.json`

### 6.4 Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| **Phase 1: Preparation** | 3 days | Finalize 50 tasks, build harness, peer review tasks, pre-register |
| **Phase 2: Pilot** | 1 day | Run 5 tasks × 3 conditions × 1 run (15 runs) to validate harness and scoring |
| **Phase 3: Execution** | 2 days | Run all 750 calls (estimated ~4 hours of API time at ~20s/call) |
| **Phase 4: Blinding & Scoring** | 3 days | Blind outputs, score all 750, second scorer does 150 |
| **Phase 5: Analysis** | 2 days | Run statistical tests, generate tables/plots, write results |
| **Phase 6: Write-up** | 2 days | Draft report, internal review |
| **Total** | **~13 days** | |

### 6.5 Results Storage

```
results/
  raw/                     # Raw API responses
    {task_id}/
      {condition}/
        {run_number}.json  # Full request + response + metadata
  scored/
    blinded/               # Blinded outputs for scoring
    scores.csv             # scorer_id, blinded_id, binary_correct, secondary_score, notes
    blind-key.json.enc     # Encrypted mapping
  analysis/
    summary.csv            # Per-task aggregated results
    statistical_tests.md   # Test results, p-values, effect sizes
    figures/               # Plots
```

---

## 7. Pre-Registration Document

The following is a self-contained pre-registration suitable for OSF (Open Science Framework) or as a GitHub issue.

---

### PRE-REGISTRATION: ARC-AGI-3 Reasoning Pillars as AI Agent Behavioral Contracts — V2

**Registration date:** [TO BE FILLED ON REGISTRATION]  
**Registration platform:** OSF Registries (osf.io) AND GitHub Issue on public repo  
**Investigators:** Tamir Dresher  
**Data collection start:** Not before registration is timestamped  

#### 1. Study Information

**Title:** Do ARC-AGI-3 Reasoning Pillars Improve AI Agent Performance Beyond Generic Chain-of-Thought Prompting?

**Research question:** Does embedding the four ARC-AGI-3 reasoning pillars (Explore, Model, Goal, Execute) as explicit behavioral contracts in LLM prompts improve task correctness compared to (a) no structure and (b) standard chain-of-thought prompting?

**Description:** This study compares three prompting conditions on a suite of 50 diverse tasks spanning factual retrieval, debugging, implicit goal detection, constraint optimization, specification disambiguation, time-sensitive retrieval, creative generation, adversarial misdirection, and tasks from external benchmarks (SWE-bench Lite, HumanEval+). Each task is run 5 times per condition (3 at temperature=0, 2 at temperature=0.7) for a total of 750 runs. Outputs are scored by blinded human evaluators using a pre-defined binary correctness rubric.

#### 2. Hypotheses

**H1 (Primary):** The ARC-informed condition achieves a correctness rate at least 15 percentage points higher than the Baseline condition across all 50 tasks (using majority-vote correctness per task per condition).

**H2:** The ARC-informed condition achieves a correctness rate at least 10 percentage points higher than the Chain-of-Thought condition.

**H3:** The ARC-informed condition uses no more than 10% more actions (LLM calls + tool invocations) than the Baseline condition on average.

**H4:** The ARC-Baseline correctness gap on far-OOD tasks is at least twice the gap on familiar tasks.

**H5 (Non-inferiority):** On adversarial tasks (Meta-Category B), the ARC-informed condition's correctness rate is no more than 5 percentage points lower than Baseline.

#### 3. Design

- **Independent variable:** Prompting condition (Baseline / CoT / ARC-informed)
- **Dependent variables:** Binary correctness (primary), action count (secondary), CSHAE (tertiary)
- **Within-subjects design:** All tasks receive all conditions
- **Blocking:** Tasks are the blocking factor (each task is a matched triplet)

#### 4. Sampling Plan

- 50 tasks: 25 structure-favoring, 15 adversarial, 10 external benchmark
- 5 runs per task per condition: 3 at temperature=0.0, 2 at temperature=0.7
- Total: 750 runs
- Majority-vote aggregation: each task-condition pair yields one binary correctness outcome (majority of 5 runs)

#### 5. Variables

**Measured:**
- Binary correctness (0/1) per run
- Action count (integer) per run
- CSHAE (float, 0-1) per run
- Response time (seconds) per run
- Failure mode category (hallucination/omission/misunderstanding/over-complication/other) for incorrect runs

**Manipulated:**
- Prompting condition (3 levels)

**Controlled:**
- Model (claude-sonnet-4-20250514)
- Temperature (0.0 for deterministic runs, 0.7 for stochastic runs)
- Max tokens (4096)
- Task prompt (identical across conditions)

#### 6. Analysis Plan

**Primary analysis:** McNemar's test comparing ARC vs. Baseline on task-level majority-vote correctness (50 paired binary outcomes). Report χ², p-value, Cohen's g, and 95% CI for the difference in proportions.

**Secondary analyses:**
- McNemar's test for ARC vs. CoT (H2)
- Paired t-test or Wilcoxon signed-rank for action counts (H3), checking normality with Shapiro-Wilk
- Logistic mixed-effects model for condition × difficulty interaction (H4)
- One-sided McNemar's test with 5pp non-inferiority margin for adversarial tasks (H5)

**Multiple comparison correction:** Holm-Bonferroni across H1-H5.

**Descriptive analyses (not hypothesis-tested):**
- Per-task-type correctness breakdown
- Failure mode frequencies
- CSHAE distribution plots

#### 7. Stopping Rules

- No early stopping for efficacy
- Pre-committed sample size increase: if H2 power estimate < 70% at interim (25 tasks), add 10 tasks to Meta-Category A
- All 750 (or 900) runs complete before unblinding

#### 8. Other

**Blinding:** Scorers evaluate outputs stripped of condition-identifying markers.  
**Inter-rater reliability:** Second scorer on 20% random subset; Cohen's κ ≥ 0.80 required.  
**Data availability:** All raw results, scoring rubrics, and analysis code will be published in the experiment repository.  
**Protocol amendments:** Any deviation from this pre-registration will be documented and justified in the final report.

---

## 8. Open Questions and Decisions Needed

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | Where to pre-register? | OSF, GitHub issue, or both | Both — OSF for credibility, GitHub for accessibility |
| 2 | Who designs Meta-Category A/B tasks? | Tamir, external collaborator, LLM-generated with human review | External collaborator preferred; LLM-generated + human review acceptable |
| 3 | Should we also run GPT-4.1 as a second model? | Yes (doubles runs to 1500) / No | Yes, but in Phase 7 (after primary analysis), not blocking |
| 4 | SWE-bench tasks need a code execution environment | Docker sandbox / local / cloud | Docker sandbox recommended for isolation |
| 5 | Who is the second scorer? | Team member, external, LLM-as-judge | External human preferred; LLM-as-judge for a supplementary analysis |

---

## 9. Appendices

### Appendix A: V1 Results Summary (for reference)

| Metric | V1 Baseline | V1 ARC | V1 Gap |
|--------|-------------|--------|--------|
| Correctness | 1/9 (11%) | 9/9 (100%) | +89pp |
| Mean actions | 10.3 | 8.2 | -20% |
| Mean SHAE | 0.47 | 0.48 | +0.01 |

V1 limitations: n=9, no CoT control, no blinding, no model specified, circular task design, SHAE has no correctness gate.

### Appendix B: Changes from V1

1. 50 tasks (was 9)
2. 3 conditions (was 2) — added CoT control
3. 5 runs per condition (was 1)
4. CSHAE replaces SHAE (correctness-gated)
5. Binary correctness as primary metric (not SHAE)
6. Blinded evaluation
7. Pre-registered hypotheses with quantitative predictions
8. Statistical tests with multiple comparison correction
9. External benchmark tasks to prevent circular design
10. Adversarial tasks to test where structure hurts
11. Inter-rater reliability check
12. Model, temperature, and seed fully specified

### Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **ARC-AGI-3** | Abstraction and Reasoning Corpus, 3rd generation — interactive AI benchmark by François Chollet |
| **CoT** | Chain-of-Thought prompting — "let's think step by step" |
| **CSHAE** | Correctness-gated Squad Human Action Efficiency |
| **Far-OOD** | Far out-of-distribution — task domain rarely seen in training data |
| **McNemar's test** | Statistical test for paired binary outcomes |
| **Holm-Bonferroni** | Step-down method for multiple comparison correction |
| **Non-inferiority** | Testing that one condition is not meaningfully worse than another |
| **OSF** | Open Science Framework — pre-registration platform |
| **RHAE** | Relative Human Action Efficiency — ARC-AGI-3's official metric |

---

*Protocol drafted by Picard. Addresses all 10 findings from Q's Devil's Advocate Review (2026-03-28). Ready for team review and pre-registration.*
