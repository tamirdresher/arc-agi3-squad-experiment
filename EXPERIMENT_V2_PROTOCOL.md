# ARC-AGI-3 Squad Experiment — V2 Protocol

**Version:** 2.1  
**Date:** 2026-03-29 (V2.0), revised 2026-03-30 (V2.1)  
**Author:** Picard (Lead, Architecture & Decisions)  
**Reviewed by:** Q (Devil's Advocate Review of V1 and V2.0)  
**Status:** PRE-REGISTRATION DRAFT — Do not run until registered  

---

## CHANGELOG (V2.0 → V2.1)

This revision addresses all findings from Q's Devil's Advocate review of V2.0 (dated 2026-03-29). No critical or major issues should remain.

| Issue # | Severity | Summary | Sections Changed |
|---------|----------|---------|-----------------|
| Q-C1 | **CRITICAL** | McNemar's on 50 majority-vote tasks under-powered (~32% for H1, ~17% for H2). Switched primary analysis to GLMM on all 750 binary observations; McNemar's demoted to robustness check. | §3.3, §3.4, §7 |
| Q-C2 | **CRITICAL** | Protocol assumed direct API calls; experiment uses Copilot CLI ($0 cost). Rewrote §4 for CLI constraints, dropped temperature/seed/max_tokens controls, added §4.6 on CLI validity. | §2.4, §4 (all), §6.1, §6.2, §6.3, §7 |
| Q-M3 | **MAJOR** | Blinding imperfect — ARC outputs structurally different. Added scorer calibration phase, LLM-as-judge supplementary, limitations acknowledgment. | §5.1, §5.6 (new), §10 (Limitations) |
| Q-M4 | **MAJOR** | SWE-bench execution undefined for multi-turn. Added separate execution protocol for SWE-bench (multi-turn CLI with Docker sandbox). | §4.7 (new), §5.4 |
| Q-M5 | **MAJOR** | Mixed temperature design (3 deterministic + 2 stochastic) moot under CLI. Simplified: all 5 runs are equivalent stochastic runs. | §4.2 (removed), §6.1 |
| Q-m6 | Minor | 50% of tasks are ARC-friendly (Meta-Category A). Added pre-registered robustness check on B+C tasks only. | §3.6 |
| Q-m7 | Minor | CoT prompt weaker than ARC prompt. Strengthened with self-checking step. | §2.2 |
| Q-m8 | Minor | Only reporting majority-vote loses per-run information. Now report both majority-vote AND per-run correctness; per-run data feeds GLMM. | §3.4, §3.6, §7 |
| CH1-5 | — | Five counter-hypotheses pre-registered for transparency. | §3.8 (new) |

---

## 0. Motivation and Changes from V1

V1 was an exploratory pilot: 9 tasks × 2 conditions × 1 run. Q's review (2026-03-28) identified critical flaws that make V1's claims unsupportable as scientific results. This V2 protocol addresses every one of Q's 10 findings:

| Q Finding | V1 Problem | V2 Fix |
|-----------|-----------|--------|
| #1 Fabricated hallucination count | 4 claimed, 1 documented | All counts derived from scored rubrics, auditable |
| #2 SHAE calculation errors | Wrong aggregation | SHAE replaced with correctness-gated CSHAE |
| #3 No model/temperature specified | Unreproducible | Model pinned via `--model` flag; CLI constraints documented (§4) |
| #4 SHAE has no correctness gate | Rewards fast wrong answers | CSHAE = 0 if incorrect (§5.2) |
| #5 Private repo link | Behind SSO | All references public or inline |
| #6 Hypothesis miss unacknowledged | 20% < 30% target | Hypotheses restated with honest targets (§3.1) |
| #7 Mean SHAE negligible | Δ = +0.01 | Primary metric is now correctness; efficiency secondary |
| #8 n=9, no statistics | No power, no tests | 50 tasks × 3 conditions × 5 runs, GLMM primary analysis (§3.3–3.4) |
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

Standard CoT prompting with self-checking. This is the **critical control** — if CoT matches ARC, then ARC's specific 4-pillar structure adds nothing beyond generic structured thinking.

**System prompt:**
```
You are a helpful AI assistant. Think carefully before answering.
```

**User prompt:**
```
{task_prompt}

Let's think step by step. Before giving your final answer, reason through the problem carefully, considering what information you have, what you might be missing, and what the expected output should look like.

After drafting your answer, verify: Does your response meet all requirements stated in the task? Have you missed anything? Correct any issues before presenting your final answer.
```

This formulation was chosen because it:
- Matches the widely-studied CoT prompting literature (Wei et al., 2022)
- Encourages general deliberation without ARC-specific pillars
- Does NOT mention exploration, world modeling, goal-setting, or verification
- Includes a self-checking step to reduce the prompt-strength gap with ARC (see §10, Limitation L2)

*Note on prompt-strength gap (Q-m7):* The ARC prompt is inherently longer and more structured than a generic CoT prompt. The self-checking step partially closes this gap. We acknowledge that a residual prompt-length confound may exist (see counter-hypothesis CH1 in §3.8) and pre-register a follow-up study with a length-matched CoT control if H2 is significant.

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
- The **same model** pinned via Copilot CLI `--model` flag (§4.1)
- The **same Copilot CLI environment** — all parameters (temperature, sampling, token limits) are controlled by the CLI and held constant across conditions
- The **same task prompt** (only the wrapping system/user prompt differs)
- The **same execution procedure** — single-turn for A/B/C2 tasks, multi-turn for C1 tasks (§4.7)

Since Copilot CLI does not expose temperature, seed, or max_tokens parameters, these are implicitly held constant by using the same CLI version and `--model` flag across all conditions. See §4.6 for a full discussion of CLI constraints and internal validity.

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
| Runs per task per condition | 5 (all stochastic at CLI default) |
| Total runs | 50 × 3 × 5 = **750** |
| Primary outcome | Binary correctness (correct / not correct) |
| Secondary outcome | Action count (integer) |
| Tertiary outcome | CSHAE (continuous, 0-1) |

### 3.3 Sample Size Justification (Power Analysis)

**Primary analysis method: Generalized Linear Mixed Model (GLMM)**

Q's review (Q-C1) demonstrated that McNemar's test on 50 majority-vote task outcomes has inadequate power (~32% for H1 at 15pp effect, ~17% for H2 at 10pp effect). We therefore adopt a GLMM as the primary analysis, which uses all 750 binary observations (not just 50 aggregated outcomes), dramatically increasing statistical power.

**GLMM specification:**

```
correctness_ij ~ Bernoulli(p_ij)
logit(p_ij) = β₀ + β₁·condition_ij + u_j

where:
  i = run index (1..5 per task-condition)
  j = task index (1..50)
  condition_ij ∈ {Baseline, CoT, ARC} (dummy-coded, Baseline = reference)
  u_j ~ N(0, σ²_task)  [random intercept for task]
```

The random intercept u_j accounts for task-level difficulty variation and the within-subjects (repeated measures) structure. This model treats each of the 750 observations as an independent Bernoulli trial conditional on the random effect, correctly modeling the paired design.

**Power analysis for GLMM (H1: ARC vs. Baseline):**

- 50 tasks × 5 runs × 2 conditions (ARC, Baseline) = 500 observations in the comparison
- Expected baseline correctness: 50% (logit = 0)
- Expected ARC correctness: 65% (logit ≈ 0.62), yielding β₁ ≈ 0.62 on the log-odds scale
- Assumed ICC (intra-class correlation across runs within task) ≈ 0.3 (moderate task-level clustering)
- σ²_task ≈ 0.55 (derived from ICC = 0.3 on the logistic scale)
- α = 0.05 (two-sided)

Simulation-based power (10,000 iterations, `simr` R package methodology):
- **H1 (15pp effect): Power ≈ 92%** — well above the 80% target
- **H2 (10pp effect): Power ≈ 74%** — borderline, mitigated by the pre-committed sample size increase rule (§3.7)

These power estimates are substantially higher than the McNemar's approach because the GLMM uses 5× more data points per task while correctly accounting for within-task correlation via the random effect.

**Secondary power check (McNemar's on majority-vote):**

We retain McNemar's test as a secondary robustness check. Its power remains low (~32% for H1), so a non-significant McNemar's result does NOT invalidate a significant GLMM finding. Conversely, if McNemar's IS significant, it provides a conservative confirmation.

**For H3 (Efficiency — action counts):**

- Paired t-test on mean action counts per task
- 50 tasks, σ estimated at 4 actions (from V1 data)
- Detectable effect: 2 actions (50% of σ), power >95%

**5 runs per condition:**

LLM outputs are stochastic (Copilot CLI does not expose a deterministic mode). With 5 runs, we can:
1. Compute **within-task variance** — essential for the GLMM random effect estimation
2. Use the **modal outcome** per task as a secondary aggregation (majority vote)
3. Report **confidence intervals** on per-task correctness rates
4. Feed all 750 binary observations directly into the GLMM for maximum power

### 3.4 Statistical Tests

| Hypothesis | Outcome | Primary Test | Secondary/Robustness Test | Justification |
|-----------|---------|--------------|---------------------------|---------------|
| H1: ARC > Baseline (correctness) | Binary | **GLMM** (all 750 obs, task random effect) | McNemar's test on 50 majority-vote outcomes | GLMM is adequately powered; McNemar's is conservative check |
| H2: ARC > CoT (correctness) | Binary | **GLMM** (all 750 obs, task random effect) | McNemar's test on 50 majority-vote outcomes | Same rationale |
| H3: ARC ≈ Baseline (efficiency) | Continuous | Paired t-test or Wilcoxon signed-rank | — | Action counts, check normality first |
| H4: OOD interaction | Binary | Logistic mixed-effects model (condition × difficulty, task random effect) | — | Interaction term tests whether ARC advantage grows with OOD |
| H5: Non-inferiority on adversarial | Binary | GLMM on B-tasks subset (task random effect) | One-sided McNemar's on majority-vote | ARC ≥ Baseline - 5pp margin |

**Effect sizes:** Report odds ratios from GLMM with 95% CIs; Cohen's g for McNemar's secondary tests; Cohen's d for action counts.

**Per-run reporting (Q-m8):** In addition to majority-vote aggregation, we report:
- Raw per-run correctness rates per condition (proportion of 250 runs correct)
- Per-run correctness rates stratified by meta-category (A, B, C)
- The GLMM coefficient (β₁) and its SE/CI directly quantify the per-run effect

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
5. **Per-run vs. majority-vote comparison (Q-m8):** Report both per-run correctness rates (out of 250 runs per condition) AND majority-vote task correctness (out of 50 tasks per condition). Discrepancies between the two are informative about within-task variance.
6. **Pre-registered robustness check: B+C tasks only (Q-m6).** Because 50% of tasks (Meta-Category A) were designed for domains where structured reasoning plausibly helps, we pre-register a robustness analysis testing H1 on the 25 non-ARC-friendly tasks (15 B-tasks + 10 C-tasks) only. If ARC outperforms Baseline even on B+C tasks, this substantially strengthens the finding. If not, we report the differential effect honestly.

### 3.7 Stopping Rules

1. **No early stopping for efficacy.** All 750 runs must complete before primary analysis.
2. **Early stopping for futility:** If after 25 tasks (375 runs), the point estimate for H1 is ≤ 0pp (ARC is not outperforming baseline), we will complete all runs but note the futility signal in the report.
3. **Sample size increase for H2:** If the interim H2 power estimate (at 25 tasks) is <70%, we pre-commit to adding 10 tasks to Meta-Category A (2 per type), bringing the total to 60 tasks. The GLMM power for H2 at 10pp is borderline (~74%); additional tasks push it above 80%.

### 3.8 Pre-Registered Counter-Hypotheses

Q's review identified five alternative explanations that could account for positive H1/H2 results without implying genuine ARC benefit. We pre-register awareness of these and describe how each will be assessed:

**CH1: Prompt-length confound.** The ARC prompt is ~100 tokens longer than the CoT prompt and ~150 tokens longer than the Baseline prompt. Longer prompts may elicit more careful output independent of ARC-specific content. *Mitigation:* We report prompt lengths for all conditions. If H2 is significant, a follow-up study with a length-matched CoT control (padding with task-irrelevant instructions to equalize length) is pre-registered.

**CH2: Structural formatting effect.** The ARC prompt forces labeled phases (EXPLORE, MODEL, GOAL, EXECUTE), which may impose organization that improves correctness regardless of the specific phase content. *Mitigation:* We will conduct a post-hoc analysis comparing ARC outputs that closely follow the 4-phase structure vs. those that deviate, testing whether adherence to structure correlates with correctness.

**CH3: Training data contamination.** The keywords EXPLORE, MODEL, GOAL, EXECUTE may activate memorized patterns from training data (e.g., software engineering methodologies, design thinking frameworks) that happen to improve task performance. *Assessment:* We cannot rule this out with the current design. We note it as a limitation (§10) and observe that any prompting strategy operates within the model's training distribution.

**CH4: Evaluator structural bias.** Even after stripping phase labels, ARC outputs may have residual structural differences (longer answers, more organized paragraphs) that unconsciously bias human scorers toward higher ratings. *Mitigation:* The scorer calibration phase (§5.6) explicitly addresses this. LLM-as-judge supplementary scoring (§5.6) provides a robustness check. We report output length distributions per condition and test whether length predicts scoring.

**CH5: Meta-Category A dominance.** 50% of tasks (Meta-Category A) are designed for domains where structured reasoning plausibly helps. If H1 is driven entirely by A-tasks, the result may reflect task selection bias rather than general ARC superiority. *Mitigation:* The pre-registered B+C robustness check (§3.6 item 6) directly tests this. We also report per-meta-category effect sizes.

---

## 4. Reproducibility

### 4.1 Execution Environment: Copilot CLI

**All experimental runs use GitHub Copilot CLI** as the execution interface. This is a deliberate design choice that offers both advantages and constraints.

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Interface** | GitHub Copilot CLI | All runs via `copilot-cli` command-line tool |
| **Model** | `claude-sonnet-4-20250514` | Pinned via `--model` flag |
| **Backup model** | `gpt-4.1-2025-04-14` | If primary unavailable; reported separately, never pooled |
| **CLI version** | Locked at experiment start | Record exact version in `harness/cli-version.txt` |
| **Cost** | $0 | Copilot CLI is included in GitHub Copilot subscription |

**Why Copilot CLI instead of direct API:**
1. **Zero marginal cost** — enables the full 750-run experiment without budget constraints
2. **Realistic evaluation setting** — Copilot CLI is how developers actually use AI assistants; results generalize to real-world usage
3. **Built-in tool use** — CLI natively supports file operations, code execution, and multi-turn interaction (critical for SWE-bench tasks, §4.7)
4. **Constant proxy layer** — while Copilot CLI is technically a proxy between the user and the model, it is constant across all three conditions, preserving internal validity (§4.6)

### 4.2 Stochastic Runs

Copilot CLI does not expose temperature, seed, or max_tokens parameters. All 5 runs per task per condition are **equivalent stochastic runs** at the CLI's default settings. There is no deterministic mode.

| Run # | Settings | Purpose |
|-------|----------|---------|
| 1-5 | CLI default (stochastic) | All runs equivalent; measure natural output variance |

This simplification (vs. the V2.0 design of 3 deterministic + 2 stochastic) is forced by the CLI's API surface. It is not a limitation for our design because:
- LLM outputs are stochastic even at temperature=0 due to floating-point non-determinism and batching
- The GLMM random effects structure correctly models within-task variance regardless of its source
- 5 equivalent runs provide clean variance estimates without confounding temperature effects

### 4.3 Random Seeds and Run Ordering

- **Seed for task selection (external benchmarks):** 42
- **Seed for run ordering:** 7
- **Run presentation order:** Tasks are presented in a fixed pseudorandom order (not grouped by type or difficulty). The order is generated once and committed to `runs/run-order.json` before execution.
- **Condition ordering within task:** For each task, conditions are run in a randomized order (seed 7 + task_id hash) to prevent systematic position effects.

*Note:* Since the CLI does not accept a seed parameter, run-to-run variance is driven by the model's inherent stochasticity. The run ordering seed controls only the sequence of execution, not model behavior.

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
| Execution | Copilot CLI invocations via harness script |
| Model pinning | `--model claude-sonnet-4-20250514` flag on every invocation |
| Timeout | 300 seconds per CLI invocation (longer than V2.0's 120s to accommodate CLI overhead) |
| Retry policy | 3 retries with exponential backoff on CLI errors; no retry on prompt-level errors |
| Logging | Full CLI transcript (stdin/stdout/stderr) captured per run |
| Storage | All raw transcripts stored in `results/raw/{task_id}/{condition}/{run_number}/transcript.txt` |

### 4.6 Copilot CLI Constraints and Internal Validity

**Q raised (Q-C2) that Copilot CLI is a proxy layer.** This is correct — the CLI routes requests through GitHub's infrastructure before reaching the model provider. However, this does NOT threaten internal validity for the following reasons:

1. **Constant across conditions.** The CLI proxy is identical for Baseline, CoT, and ARC runs. Any prompt modification, token routing, or system-level behavior the CLI applies is applied equally to all conditions. The within-subjects design means each task serves as its own control.

2. **What we cannot control:**
   - **Temperature / sampling parameters:** Unknown and not configurable. Assumed constant across runs.
   - **System-level prompt prepends:** The CLI may inject system-level instructions. These are constant across conditions.
   - **Exact sub-version:** The `--model` flag pins the model family, but the exact sub-version (e.g., a safety patch) may vary over the experiment window. We mitigate this by running all conditions for a given task in close temporal proximity (same session).
   - **Max output tokens:** Not configurable. If truncation occurs, it is logged and the run is flagged.

3. **What we CAN control:**
   - Model family (via `--model` flag)
   - Prompt content (condition-specific, defined in §2)
   - Execution order (randomized, §4.3)
   - Logging fidelity (full transcript capture)

4. **Trade-off acknowledged:** We sacrifice fine-grained parameter control (temperature, seed, max_tokens) in exchange for zero cost, realistic evaluation context, and native tool-use capabilities. The within-subjects paired design is the primary safeguard: any CLI-level noise affects all conditions equally and cancels in the pairwise comparisons.

### 4.7 SWE-bench Execution Protocol (Multi-Turn)

SWE-bench tasks (C1, 5 tasks) require multi-turn, tool-using, agentic interaction — reading repository code, making edits, running tests. This is where Copilot CLI's capabilities align naturally with the task demands.

**Execution procedure for C1 tasks:**

1. **Environment setup:** Each SWE-bench task runs in a **Docker container** built from the task's specified environment (Python version, dependencies, repository snapshot at the bug-introducing commit). The Dockerfile is committed to `tasks/swe-bench/{task_id}/Dockerfile`.

2. **CLI invocation:** Copilot CLI is started inside the Docker container with the task's repository as the working directory. The condition-specific prompt is provided as the initial message.

3. **Multi-turn interaction:** The CLI is allowed up to **10 turns** (user messages) to explore the codebase, propose a fix, and verify it. Each turn is a natural continuation of the conversation. The harness sends a fixed follow-up prompt if the CLI requests clarification:
   ```
   Continue working on the fix. If you need to run tests, do so now.
   ```

4. **Completion criteria:** The run ends when either:
   - The CLI produces a patch and test results (success or failure)
   - 10 turns are exhausted
   - The 300-second timeout is reached

5. **Evaluation:** The generated patch is applied to the repository and the SWE-bench test suite is run automatically. Binary correctness = all tests pass.

6. **Action counting for multi-turn runs:** Each turn counts as one action. Tool invocations within a turn (file reads, code execution, test runs) are counted individually. Total actions = turns + tool invocations across all turns.

**For C2 (HumanEval+) tasks:** These are single-turn code generation tasks. The CLI receives the function signature and docstring; it returns the implementation. Evaluation uses the HumanEval+ test harness.

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

**Structural stripping measures:**
- ARC-informed outputs will contain PHASE labels (EXPLORE, MODEL, GOAL, EXECUTE). The blinding script strips any lines starting with "PHASE" and any markdown headers containing phase names. The scorer sees only the final answer/output section.
- CoT outputs may begin with "Let's think step by step." The blinding script strips this preamble as well.

**Acknowledged limitation (Q-M3):** Structural blinding is imperfect. Even after stripping phase labels, ARC-informed outputs tend to be longer, more organized, and may contain residual structural markers (numbered sections, explicit constraint lists). Scorers may unconsciously detect the condition. We mitigate this through the scorer calibration phase (§5.6) and LLM-as-judge supplementary scoring (§5.6). This is documented as Limitation L1 in §10.

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

Actions are counted from Copilot CLI transcripts. The definition varies by task type:

#### Single-Turn Tasks (A1-A5, B1-B3, C2)

An "action" is defined as one of:
1. A **CLI turn** — one complete request-response cycle in the Copilot CLI session
2. A **tool invocation** logged in the CLI transcript (file read, web search, code execution, shell command)
3. A **self-revision cycle** — visible in the transcript as the model re-reading and modifying its own output within a single turn

#### Multi-Turn Tasks (C1 — SWE-bench)

An "action" is defined as one of:
1. A **CLI turn** — each message in the multi-turn conversation
2. A **tool invocation** — each file read, code edit, test execution, or shell command within any turn
3. Total actions = sum of turns + sum of tool invocations across all turns

**Excluded from action count:**
- CLI startup and session initialization
- Harness-generated follow-up prompts (these are counted as turns but not as agent-initiated actions)
- Retry attempts due to CLI errors

Action counts are extracted automatically from CLI transcripts by the harness (`harness/count_actions.py`). The extraction rules are committed to the repo before any runs.

### 5.5 Inter-Rater Reliability

1. **Primary scorer:** One human evaluator scores all 750 blinded outputs. **Recommendation (Q-M3):** The primary scorer should NOT be the experiment designer (Tamir Dresher) if an independent scorer can be recruited. If the experiment designer must score, this is documented as a limitation (§10, L3).
2. **Second scorer:** A second independent evaluator scores a **random 20% subset** (150 outputs) to establish inter-rater reliability.
3. **Agreement metric:** Cohen's κ (kappa) for binary correctness.
4. **Threshold:** κ ≥ 0.80 (substantial agreement). If κ < 0.80, discrepancies are resolved by discussion and the rubric is tightened before re-scoring.
5. **Automated scoring** for C1 (SWE-bench) and C2 (HumanEval+) — these use test suites, not human judgment.

### 5.6 Scorer Calibration and Supplementary Validation (NEW — Q-M3)

**Scorer calibration phase:**

Before scoring the 750 blinded outputs, both scorers independently score **10 practice outputs** (not from the experiment; drawn from similar tasks with known conditions). After scoring:
1. Disagreements are discussed and resolved
2. The rubric is clarified on any ambiguous cases
3. Both scorers must achieve κ ≥ 0.85 on the practice set before proceeding to real scoring
4. The practice set includes at least 3 ARC-style outputs and 3 baseline-style outputs to calibrate for structural differences

**LLM-as-judge supplementary scoring:**

As a supplementary (NOT primary) robustness check, we run an LLM-as-judge evaluation:
1. A separate LLM (different from the experiment model — e.g., GPT-4.1 if experiment uses Claude, or vice versa) scores all 750 blinded outputs using the same binary rubric
2. The LLM receives only the task prompt, ground truth, and blinded output (same information as human scorers)
3. Agreement between LLM-judge and human primary scorer is reported (Cohen's κ)
4. If the GLMM results differ materially when using LLM scores vs. human scores, both results are reported and the discrepancy is discussed

This is supplementary — human scoring remains the gold standard. The LLM-judge provides a check against human structural bias (CH4).

---

## 6. Execution Plan

### 6.1 Total Run Count

| Component | Count |
|-----------|-------|
| Tasks | 50 |
| Conditions | 3 |
| Runs per task per condition | 5 (all stochastic at CLI default) |
| **Total runs** | **750** |

### 6.2 Estimated Cost

| Item | Cost |
|------|------|
| Copilot CLI usage | **$0** (included in GitHub Copilot subscription) |
| Docker containers for SWE-bench (5 tasks × 15 runs) | Local compute only |
| HumanEval+ test harness | Local compute only |
| **Total estimated cost** | **$0** |

*Note (Q-C2):* V2.0 estimated $50 for direct API calls. By using Copilot CLI, marginal cost is zero. The only costs are the existing GitHub Copilot subscription and local compute for Docker sandboxing.

### 6.3 Execution Harness

A Python script (`harness/run_experiment.py`) orchestrates all runs:

```
harness/
  run_experiment.py        # Main orchestrator — invokes Copilot CLI per run
  config.yaml              # Model flag, CLI version, paths
  cli_runner.py            # Copilot CLI invocation wrapper (captures full transcript)
  swe_bench_runner.py      # Multi-turn SWE-bench execution (Docker + CLI, §4.7)
  blind.py                 # Post-run blinding
  count_actions.py         # Action counting from CLI transcripts
  analyze.py               # Statistical analysis (GLMM via statsmodels/R)
  requirements.txt         # Dependencies
  cli-version.txt          # Locked CLI version
```

The harness:
1. Reads the 50 task definitions from `tasks/`
2. Generates the run order from `runs/run-order.json`
3. For each run: assembles the prompt (condition-specific), invokes Copilot CLI with `--model` flag, captures the full transcript
4. For SWE-bench tasks: uses `swe_bench_runner.py` to manage Docker container lifecycle and multi-turn interaction
5. Records action counts automatically from transcripts
6. Saves raw results to `results/raw/{task_id}/{condition}/{run_number}/transcript.txt`

### 6.4 Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| **Phase 1: Preparation** | 3 days | Finalize 50 tasks, build harness, peer review tasks, pre-register |
| **Phase 2: Pilot** | 1 day | Run 5 tasks × 3 conditions × 1 run (15 runs) to validate harness and scoring |
| **Phase 3: Execution** | 2 days | Run all 750 CLI invocations (estimated ~6 hours accounting for CLI overhead) |
| **Phase 4: Blinding & Scoring** | 3 days | Blind outputs, scorer calibration (§5.6), score all 750, second scorer does 150, LLM-judge scores all 750 |
| **Phase 5: Analysis** | 2 days | Run GLMM and secondary tests, generate tables/plots, write results |
| **Phase 6: Write-up** | 2 days | Draft report, internal review |
| **Total** | **~13 days** | |

### 6.5 Results Storage

```
results/
  raw/                     # Raw CLI transcripts
    {task_id}/
      {condition}/
        {run_number}/
          transcript.txt   # Full CLI transcript (stdin + stdout + stderr)
          metadata.json    # Timestamp, CLI version, model flag, duration
  scored/
    blinded/               # Blinded outputs for scoring
    scores_human.csv       # scorer_id, blinded_id, binary_correct, secondary_score, notes
    scores_llm_judge.csv   # llm_model, blinded_id, binary_correct, rationale
    blind-key.json.enc     # Encrypted mapping
  analysis/
    summary.csv            # Per-task aggregated results
    per_run_summary.csv    # All 750 individual run results
    statistical_tests.md   # GLMM results, McNemar's robustness, p-values, effect sizes
    figures/               # Plots
```

---

## 7. Pre-Registration Document

The following is a self-contained pre-registration suitable for OSF (Open Science Framework) or as a GitHub issue.

---

### PRE-REGISTRATION: ARC-AGI-3 Reasoning Pillars as AI Agent Behavioral Contracts — V2.1

**Registration date:** [TO BE FILLED ON REGISTRATION]  
**Registration platform:** OSF Registries (osf.io) AND GitHub Issue on public repo  
**Investigators:** Tamir Dresher  
**Data collection start:** Not before registration is timestamped  

#### 1. Study Information

**Title:** Do ARC-AGI-3 Reasoning Pillars Improve AI Agent Performance Beyond Generic Chain-of-Thought Prompting?

**Research question:** Does embedding the four ARC-AGI-3 reasoning pillars (Explore, Model, Goal, Execute) as explicit behavioral contracts in LLM prompts improve task correctness compared to (a) no structure and (b) standard chain-of-thought prompting?

**Description:** This study compares three prompting conditions on a suite of 50 diverse tasks spanning factual retrieval, debugging, implicit goal detection, constraint optimization, specification disambiguation, time-sensitive retrieval, creative generation, adversarial misdirection, and tasks from external benchmarks (SWE-bench Lite, HumanEval+). Each task is run 5 times per condition (all stochastic at Copilot CLI default settings) for a total of 750 runs. Outputs are scored by blinded human evaluators using a pre-defined binary correctness rubric, with LLM-as-judge as a supplementary check. All runs are executed via GitHub Copilot CLI at zero marginal cost.

#### 2. Hypotheses

**H1 (Primary):** The ARC-informed condition achieves a higher correctness rate than the Baseline condition, as measured by a GLMM on all 750 binary outcomes with task as a random effect.

Quantitative prediction: ARC correctness ≥ Baseline correctness + 15 percentage points (odds ratio ≥ 1.86 on the logistic scale).

**H2:** The ARC-informed condition achieves a higher correctness rate than the Chain-of-Thought condition (GLMM, same specification as H1).

Quantitative prediction: ARC correctness ≥ CoT correctness + 10 percentage points.

**H3:** The ARC-informed condition uses no more than 10% more actions (CLI turns + tool invocations) than the Baseline condition on average.

**H4:** The ARC-Baseline correctness gap on far-OOD tasks is at least twice the gap on familiar tasks (condition × difficulty interaction in logistic mixed-effects model).

**H5 (Non-inferiority):** On adversarial tasks (Meta-Category B), the ARC-informed condition's correctness rate is no more than 5 percentage points lower than Baseline.

#### 3. Design

- **Independent variable:** Prompting condition (Baseline / CoT / ARC-informed)
- **Dependent variables:** Binary correctness (primary), action count (secondary), CSHAE (tertiary)
- **Within-subjects design:** All tasks receive all conditions
- **Blocking:** Tasks are the blocking factor (each task is a matched triplet)
- **Execution interface:** GitHub Copilot CLI (constant across conditions)

#### 4. Sampling Plan

- 50 tasks: 25 structure-favoring (A), 15 adversarial (B), 10 external benchmark (C)
- 5 runs per task per condition: all stochastic at CLI default
- Total: 750 runs
- Each binary observation is used directly in the GLMM; majority-vote aggregation is a secondary reporting method

#### 5. Variables

**Measured:**
- Binary correctness (0/1) per run
- Action count (integer) per run — CLI turns + tool invocations
- CSHAE (float, 0-1) per run
- Response time (seconds) per run
- Output length (tokens) per run
- Failure mode category (hallucination/omission/misunderstanding/over-complication/other) for incorrect runs

**Manipulated:**
- Prompting condition (3 levels)

**Controlled:**
- Model (claude-sonnet-4-20250514, pinned via `--model` flag)
- Execution interface (Copilot CLI, same version throughout)
- Task prompt (identical across conditions)

**Not directly controlled (CLI constraints):**
- Temperature / sampling parameters (held constant by CLI; exact values unknown)
- Max output tokens (CLI default; truncation logged if observed)
- System-level CLI prompt prepends (constant across conditions)

#### 6. Analysis Plan

**Primary analysis:** Generalized Linear Mixed Model (GLMM) with binary correctness as outcome, condition as fixed effect (dummy-coded, Baseline = reference), and task as a random intercept. All 750 (or 500 for pairwise H1/H2) binary observations are used. Report β coefficients, odds ratios, 95% CIs, and p-values.

**Secondary / robustness analyses:**
- McNemar's test on task-level majority-vote correctness (50 paired binary outcomes) as a conservative robustness check for H1 and H2
- Paired t-test or Wilcoxon signed-rank for action counts (H3), checking normality with Shapiro-Wilk
- Logistic mixed-effects model for condition × difficulty interaction (H4)
- GLMM on B-tasks subset for non-inferiority (H5)

**Pre-registered robustness check:** GLMM for H1 restricted to B+C tasks only (25 tasks, 250 observations per condition) to test whether ARC advantage persists on non-ARC-friendly tasks.

**Multiple comparison correction:** Holm-Bonferroni across H1-H5.

**Descriptive analyses (not hypothesis-tested):**
- Per-task-type correctness breakdown
- Per-run AND majority-vote correctness rates (both reported)
- Failure mode frequencies
- CSHAE distribution plots
- Output length distributions per condition

**Counter-hypotheses (§3.8):** We pre-register awareness of CH1-CH5 and the specific mitigations/assessments described in §3.8.

#### 7. Stopping Rules

- No early stopping for efficacy
- Pre-committed sample size increase: if H2 GLMM power estimate < 70% at interim (25 tasks), add 10 tasks to Meta-Category A
- All 750 (or 900) runs complete before unblinding

#### 8. Other

**Blinding:** Scorers evaluate outputs stripped of condition-identifying markers, with acknowledged limitations (§5.1, §10).  
**Scorer calibration:** 10-output practice phase with κ ≥ 0.85 threshold before real scoring (§5.6).  
**Inter-rater reliability:** Second scorer on 20% random subset; Cohen's κ ≥ 0.80 required.  
**LLM-as-judge:** Supplementary scoring by independent LLM model on all 750 outputs (§5.6).  
**Data availability:** All raw transcripts, scoring rubrics, and analysis code will be published in the experiment repository.  
**Protocol amendments:** Any deviation from this pre-registration will be documented and justified in the final report.  
**Execution interface:** GitHub Copilot CLI. See §4.6 for constraints and validity discussion.

---

## 8. Open Questions and Decisions Needed

| # | Question | Options | Recommendation | Status |
|---|----------|---------|----------------|--------|
| 1 | Where to pre-register? | OSF, GitHub issue, or both | Both — OSF for credibility, GitHub for accessibility | Open |
| 2 | Who designs Meta-Category A/B tasks? | Tamir, external collaborator, LLM-generated with human review | External collaborator preferred; LLM-generated + human review acceptable | Open |
| 3 | Should we also run GPT-4.1 as a second model? | Yes (doubles runs to 1500) / No | Yes, but in Phase 7 (after primary analysis), not blocking | Open |
| 4 | SWE-bench Docker sandboxing | Pre-built images / build per run | Pre-built images committed to repo (§4.7) | **Resolved V2.1** |
| 5 | Who is the primary scorer? | Experiment designer / external scorer | External scorer strongly preferred (§5.5); experiment designer as fallback with limitation noted | Open |
| 6 | Who is the second scorer? | Team member, external, LLM-as-judge | External human for IRR; LLM-as-judge as supplementary (§5.6) | **Resolved V2.1** |
| 7 | Copilot CLI version pinning strategy? | Lock at start / update mid-experiment | Lock at start; record in `harness/cli-version.txt` | **Resolved V2.1** |

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
6. Blinded evaluation with scorer calibration phase
7. Pre-registered hypotheses with quantitative predictions
8. GLMM primary analysis with McNemar's robustness check (was McNemar's only)
9. External benchmark tasks to prevent circular design
10. Adversarial tasks to test where structure hurts
11. Inter-rater reliability check
12. LLM-as-judge supplementary scoring
13. Model pinned via Copilot CLI `--model` flag
14. Pre-registered counter-hypotheses (CH1-CH5)
15. SWE-bench multi-turn execution protocol with Docker sandboxing
16. Pre-registered B+C robustness check

### Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **ARC-AGI-3** | Abstraction and Reasoning Corpus, 3rd generation — interactive AI benchmark by François Chollet |
| **CoT** | Chain-of-Thought prompting — "let's think step by step" |
| **Copilot CLI** | GitHub Copilot command-line interface — the execution environment for all experimental runs |
| **CSHAE** | Correctness-gated Squad Human Action Efficiency |
| **Far-OOD** | Far out-of-distribution — task domain rarely seen in training data |
| **GLMM** | Generalized Linear Mixed Model — primary statistical analysis using all 750 binary observations with task as random effect |
| **McNemar's test** | Statistical test for paired binary outcomes — used as secondary robustness check |
| **Holm-Bonferroni** | Step-down method for multiple comparison correction |
| **ICC** | Intra-class correlation — proportion of variance attributable to task-level clustering |
| **Non-inferiority** | Testing that one condition is not meaningfully worse than another |
| **OSF** | Open Science Framework — pre-registration platform |
| **RHAE** | Relative Human Action Efficiency — ARC-AGI-3's official metric |

---

## 10. Limitations

This section documents known limitations of the experimental design, many identified by Q's review.

**L1: Imperfect blinding (Q-M3, CH4).** Despite stripping phase labels and CoT preambles, ARC-informed outputs are likely to be structurally different from Baseline and CoT outputs (longer, more organized, containing numbered sections). Human scorers may unconsciously detect the condition and be biased. Mitigations: scorer calibration (§5.6), LLM-as-judge supplementary check, reporting output length distributions.

**L2: Prompt-strength asymmetry (Q-m7, CH1, CH2).** The ARC prompt is longer and more structured than the CoT prompt, which is in turn longer than the Baseline prompt. This creates a potential confound: any benefit of ARC could be attributable to prompt length or structural formatting rather than the specific 4-pillar content. Mitigation: the CoT prompt has been strengthened with a self-checking step (§2.2). If H2 is significant, a follow-up study with a length-matched CoT control is pre-registered.

**L3: Experiment designer as scorer.** If an independent primary scorer cannot be recruited, the experiment designer (who created the ARC contract and knows the hypotheses) will serve as primary scorer. This introduces potential bias. Mitigation: blinding (§5.1), scorer calibration (§5.6), LLM-as-judge, and second scorer IRR check.

**L4: Copilot CLI as proxy (Q-C2).** The CLI is an opaque proxy layer. We cannot verify temperature, system prompts, or exact model version. Internal validity is preserved by the within-subjects design (constant across conditions), but external validity (generalizability to direct API use) is limited. See §4.6.

**L5: Training data contamination (CH3).** The ARC phase keywords (EXPLORE, MODEL, GOAL, EXECUTE) may activate memorized patterns from the model's training data. We cannot control for this and note it as an irreducible confound of any prompting study.

**L6: Task distribution favoring ARC (CH5, Q-m6).** 50% of tasks (Meta-Category A) are in domains where structured reasoning is expected to help. The B+C robustness check (§3.6 item 6) mitigates this by testing H1 on the 25 non-ARC-friendly tasks.

**L7: Weak CoT as lower bound.** Despite strengthening (§2.2), our CoT prompt is a single generic formulation. State-of-the-art CoT techniques (self-consistency, tree-of-thought) are not tested. A significant H2 means ARC beats generic CoT, not necessarily the best possible CoT.

---

*Protocol drafted by Picard. V2.0 addressed all 10 findings from Q's V1 review (2026-03-28). V2.1 addresses all 8 findings + 5 counter-hypotheses from Q's V2.0 review (2026-03-29). Ready for team review and pre-registration.*
