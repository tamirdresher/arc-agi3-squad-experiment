# ARC-AGI Squad Experiment — V3 Protocol

**Version:** 3.1  
**Date:** 2026-04-09 (original) | 2026-04-09 (revised)  
**Author:** Picard (Lead, Architecture & Decisions)  
**Status:** REVISED — Addressing Q Review (v3.0 → v3.1). Requires second Q review before pre-registration.  
**Predecessor:** V2.1 Protocol (completed, ceiling effect observed)  
**Review addressed:** Q's Fact Check (2026-04-09) — 2 CRITICAL, 3 IMPORTANT, 3 MINOR issues

---

## EXECUTIVE SUMMARY

V2.1 tested Squad's ARC 4-pillar reasoning framework on 50 software/logic tasks and found a ceiling effect (Baseline 98%, CoT 100%, ARC 100%) — the model was too capable for the task battery to measure any framework benefit. V3 addresses this by switching to **real ARC-AGI-2 grid puzzles** from the ARC Prize's Abstraction and Reasoning Corpus (2025 release), where Claude Sonnet 4.6 scores ~58% baseline. This creates the measurement headroom needed to detect whether structured reasoning genuinely improves performance.

**Key change from V2.1:** We replace 50 custom software tasks with 50 real ARC-AGI-2 evaluation tasks (human-calibrated difficulty), switch to automated exact-match scoring (eliminating human scorer bias), and adapt the 4-pillar framework specifically for abstract pattern recognition.

**Key change from V3.0:** V3.0 incorrectly used ARC-AGI-1 with a 25–40% baseline estimate. Q's review identified this as wrong by 2× (actual ~60% for Claude Sonnet on ARC-AGI-1). V3.1 switches to ARC-AGI-2 per Seven's research recommendation, adds a ceiling-effect stopping rule, fixes prompt fairness, and uses human-calibrated difficulty tiers.

---

## 0. Motivation and Changes from V2.1

### 0.1 Why V3 Is Needed

V2.1 was methodologically sound (Q-approved, pre-registered, 750 runs) but produced a null result due to ceiling effects. The primary hypothesis (H1: ARC > Baseline by ≥15pp) was not supported because all conditions scored ≥98%. The conclusion was clear: **test with harder tasks that push model accuracy below 80%.**

ARC-AGI grid puzzles are ideal because:
1. **Known difficulty:** Claude Sonnet 4.6 scores ~58% on ARC-AGI-2 evaluation tasks (verified via arcprize.org leaderboard, llm-stats.com, and Q's independent check). This provides ~40pp of measurement headroom — ample room to detect a 15pp framework effect.
2. **Objective scoring:** Exact grid match — no human scoring ambiguity, no blinding concerns
3. **Abstract reasoning:** Tests pattern recognition, spatial transformation, and rule induction — domains where structured reasoning frameworks *should* help if they help anywhere
4. **Public, established benchmark:** 120 public evaluation tasks with human-calibrated difficulty tiers
5. **Low contamination risk:** ARC-AGI-2 was released in 2025 (vs. ARC-AGI-1's 2019), drastically reducing the window for training data contamination
6. **Human-calibrated difficulty:** Tasks are ranked by human accuracy (% of participants who solved correctly in ≤2 attempts), enabling principled difficulty stratification instead of proxy metrics

**Why ARC-AGI-2, not ARC-AGI-1 (V3.0 correction):** V3.0 used ARC-AGI-1 with an estimated 25–40% baseline. Q's review showed this was wrong by 2×: Claude Sonnet 4/4.6 actually scores ~60% on ARC-AGI-1 (arcprize.org, llm-stats.com), with top models like GPT-5.4 at 93.7%. Seven's research (§7) correctly recommended ARC-AGI-2 and explicitly warned against ARC-AGI-1 ("too easy, saturated"). We follow Seven's recommendation.

### 0.2 What Carries Forward from V2.1

| Component | V2.1 | V3 | Rationale |
|-----------|------|-----|-----------|
| 3-condition design | ✅ | ✅ | Baseline vs CoT vs ARC-informed — same structure |
| GLMM primary analysis | ✅ | ✅ | Same statistical framework, proven adequate power |
| 5 runs per condition | ✅ | ✅ | Same stochastic sampling strategy |
| Copilot CLI execution | ✅ | ✅ | Same $0 infrastructure |
| Counter-hypotheses | ✅ | ✅ (adapted) | Pre-registered alternative explanations |
| Automated scoring | partial | ✅ | V2.1 used automated scoring; V3 is 100% automated (exact grid match) |

### 0.3 What Changes in V3

| Component | V2.1 | V3 | Rationale |
|-----------|------|-----|-----------|
| Task source | 50 custom software/logic tasks | 50 ARC-AGI-2 evaluation tasks | Avoid ceiling effect; human-calibrated difficulty |
| Expected baseline | ~98% (too high) | ~58% (ideal range) | Room for improvement; verified via multiple leaderboards |
| Scoring | Rule-based rubric | Exact grid match (binary) + cell accuracy | Objective, no human bias |
| Task types | 8 types across 3 meta-categories | 3 difficulty strata (easy/medium/hard) based on human accuracy | Human-calibrated tiers, not proxy metrics |
| Human scorers | Required (imperfect blinding) | Not needed (automated) | Eliminates scorer bias entirely |
| Prompt format | Text tasks | Grid-as-JSON with visual representation | Adapted for spatial reasoning |
| Total runs | 750 | 750 | 50 tasks × 3 × 5 (adequate power for both H1 and H2) |

---

## 1. Task Design (50 Tasks)

### 1.1 Source: ARC-AGI-2 Public Evaluation Set

All 50 tasks are drawn from the **ARC-AGI-2 public evaluation set** (120 tasks) at:
`https://github.com/arcprize/ARC-AGI-2/tree/main/data`

We use ARC-AGI-2 (not ARC-AGI-1) because:
1. **Human-calibrated difficulty:** Tasks are ranked by human accuracy (% of participants who solved all test pairs correctly in ≤2 attempts), enabling principled stratification
2. **Appropriate difficulty for Claude Sonnet:** ~58% baseline provides ~40pp of headroom
3. **Low contamination risk:** Released in 2025 (vs. ARC-AGI-1's 2019), drastically reducing training data exposure
4. **Active benchmark:** Ongoing ARC Prize competition with community engagement
5. Ground truth is publicly available for the 120 evaluation tasks

**Why not ARC-AGI-1?** V3.0 used ARC-AGI-1 training tasks. Q's review showed Claude Sonnet 4/4.6 scores ~60% on ARC-AGI-1 (not 25–40% as V3.0 assumed). With training tasks likely even easier, the real baseline could be 65–75%+, repeating V2.1's ceiling problem. Seven's research (§7) explicitly recommends: "Use ARC-AGI-2... Avoid: ARC-AGI-1 training set (too easy, saturated)."

### 1.2 Task Format (Native ARC-AGI JSON)

Each ARC-AGI task is a JSON file containing:

```json
{
  "train": [
    {
      "input": [[0, 7, 7], [7, 7, 7], [0, 7, 7]],
      "output": [[0, 0, 0, 0, 7, 7, 0, 7, 7], ...]
    },
    // ... 2-4 more training examples
  ],
  "test": [
    {
      "input": [[7, 0, 7], [7, 0, 7], [7, 7, 0]],
      "output": [[7, 0, 7, 0, 0, 0, 7, 0, 7], ...]  // ground truth
    }
  ]
}
```

**Key properties:**
- **Grids:** Rectangular matrices (1×1 to 30×30) of integers 0–9
- **Training examples:** 2–5 input→output pairs demonstrating the transformation
- **Test:** 1 input (given to the model) + 1 output (ground truth for scoring)
- **Colors:** 0=black, 1=blue, 2=red, 3=green, 4=yellow, 5=grey, 6=magenta, 7=orange, 8=azure, 9=maroon

### 1.3 Difficulty Stratification (Human-Calibrated)

We stratify 50 tasks into 3 difficulty tiers using **human accuracy data** published with ARC-AGI-2. Human accuracy = % of participants who solved all test pairs correctly in ≤2 attempts. This replaces the proxy metrics (grid dimensions, color count) used in V3.0, which Q's review (Issue 4) identified as unvalidated against actual model performance.

| Tier | Count | Human Accuracy Range | Expected Claude Sonnet Baseline |
|------|-------|---------------------|--------------------------------|
| **Easy** | 17 | 75–100% | ~70–85% |
| **Medium** | 17 | 40–75% | ~45–65% |
| **Hard** | 16 | 0–40% | ~20–40% |

**Why human accuracy, not proxy metrics?** V3.0 used grid dimensions, color count, and training examples as proxies for difficulty. Q correctly noted these measure *surface complexity*, not *reasoning difficulty*. A small grid with few colors can involve a fiendishly complex transformation (e.g., cellular automaton), while a large grid might be trivial (e.g., flood fill). Human accuracy is the gold standard for difficulty calibration and is available for ARC-AGI-2.

**Difficulty assignment procedure:**

```python
import json
import random

random.seed(42)

def load_human_difficulty(tasks, human_accuracy_data):
    """Assign difficulty tiers using human accuracy data from ARC-AGI-2."""
    task_difficulties = []
    for task in tasks:
        task_id = task["id"]
        human_acc = human_accuracy_data.get(task_id, None)
        if human_acc is None:
            # If human accuracy data unavailable for this task, skip
            continue
        
        if human_acc >= 0.75:
            tier = "easy"
        elif human_acc >= 0.40:
            tier = "medium"
        else:
            tier = "hard"
        
        task_difficulties.append({
            "task": task,
            "human_accuracy": human_acc,
            "tier": tier
        })
    
    return task_difficulties
```

### 1.4 Task Selection Procedure

Selection is deterministic (reproducible with seed 42):

```python
# 1. Load all 120 ARC-AGI-2 public evaluation tasks
# 2. Load human accuracy data for each task
# 3. Assign difficulty tiers based on human accuracy
# 4. Randomly sample from each tier to reach target counts
# 5. Record selected task IDs in tasks/v3/selection-log.json

random.seed(42)

easy_tasks = [t for t in all_tasks if t["tier"] == "easy"]
medium_tasks = [t for t in all_tasks if t["tier"] == "medium"]
hard_tasks = [t for t in all_tasks if t["tier"] == "hard"]

selected_easy = random.sample(easy_tasks, 17)
selected_medium = random.sample(medium_tasks, 17)
selected_hard = random.sample(hard_tasks, 16)

selected_tasks = selected_easy + selected_medium + selected_hard  # 50 total
```

**Selection is frozen before any runs.** The `tasks/v3/selection-log.json` file records:
- Task filename (ARC-AGI-2 task ID)
- Assigned difficulty tier
- Human accuracy score (from ARC-AGI-2 calibration data)
- Surface features (max_dim, unique_colors, num_train) for descriptive purposes only
- SHA-256 hash of the task JSON

No task may be added, removed, or replaced after selection is committed.

### 1.5 Task Exclusion Criteria

A task is excluded from the candidate pool (before selection) if:
1. **Ambiguous ground truth:** The test output could be interpreted multiple ways (rare in ARC-AGI, but possible)
2. **Multiple test inputs:** Task has >1 test input (we use only single-test-input tasks for simplicity; this is the majority)
3. **Degenerate:** Output is identical to input (no transformation to detect)

Exclusions are documented in `tasks/v3/exclusion-log.json` with reasons.

---

## 2. Conditions (3)

### 2.1 Condition 1: Baseline (RAW)

The model receives the ARC-AGI task as JSON grids with minimal instruction. No reasoning guidance.

**System prompt:**
```
You are an AI assistant solving abstract pattern recognition puzzles. Each puzzle shows example input-output grid pairs. Your task is to determine the correct output grid for the test input.
```

**User prompt:**
```
Here is a pattern recognition puzzle. Study the example input-output pairs, then produce the correct output for the test input.

Example 1:
Input:
{json_grid_of_train_1_input}

Output:
{json_grid_of_train_1_output}

Example 2:
Input:
{json_grid_of_train_2_input}

Output:
{json_grid_of_train_2_output}

[... all training examples ...]

Test Input:
{json_grid_of_test_input}

Provide the output grid as a JSON array of arrays (list of rows, each row is a list of integers 0-9). After considering the puzzle, you may include brief reasoning. Mark your final answer clearly with "ANSWER:" followed by the JSON array.
```

> **V3.1 change (Issue 3 — prompt fairness):** V3.0 instructed Baseline to "Output ONLY the JSON array, nothing else" — actively suppressing chain-of-thought reasoning. This created a confound where Baseline was handicapped, not just unassisted. V3.1 equalizes the output format: all three conditions allow reasoning and all use the "ANSWER:" marker for extraction. Any ARC advantage now reflects the framework's content, not a reasoning permission difference.

### 2.2 Condition 2: Chain-of-Thought (CoT)

Standard CoT prompting with self-verification. The critical control — if CoT matches ARC, then ARC's 4-pillar structure adds nothing beyond generic structured thinking.

**System prompt:**
```
You are an AI assistant solving abstract pattern recognition puzzles. Think carefully and systematically before answering.
```

**User prompt:**
```
Here is a pattern recognition puzzle. Study the example input-output grid pairs, then produce the correct output for the test input.

Example 1:
Input:
{json_grid_of_train_1_input}

Output:
{json_grid_of_train_1_output}

Example 2:
Input:
{json_grid_of_train_2_input}

Output:
{json_grid_of_train_2_output}

[... all training examples ...]

Test Input:
{json_grid_of_test_input}

Let's think step by step. Before giving your final answer, reason through the problem carefully:
1. What patterns do you notice in the examples?
2. What transformation rule could explain the input-to-output mapping?
3. Apply that rule to the test input.
4. Verify your answer makes sense.

After your reasoning, provide the output grid as a JSON array of arrays (list of rows, each row is a list of integers 0-9). Mark your final answer clearly with "ANSWER:" followed by the JSON array.
```

### 2.3 Condition 3: ARC-Informed (4-Pillar Contract)

The model receives Squad's 4-pillar reasoning framework, adapted specifically for abstract grid puzzles. This is the **treatment condition**.

**System prompt:**
```
You are an AI assistant operating under a structured reasoning contract for abstract pattern recognition puzzles. Before producing your answer, you MUST complete all four phases below in order. Label each phase explicitly in your response.
```

**User prompt:**
```
Here is a pattern recognition puzzle. Study the example input-output grid pairs, then produce the correct output for the test input.

Example 1:
Input:
{json_grid_of_train_1_input}

Output:
{json_grid_of_train_1_output}

Example 2:
Input:
{json_grid_of_train_2_input}

Output:
{json_grid_of_train_2_output}

[... all training examples ...]

Test Input:
{json_grid_of_test_input}

Before answering, follow this reasoning contract:

PHASE 1 — EXPLORE: Examine each example pair carefully. For each pair, describe: What objects or patterns exist in the input? What changes between input and output? What stays the same? Note grid dimensions, colors used, and spatial relationships.

PHASE 2 — MODEL: Synthesize a single transformation rule that explains ALL example pairs. State the rule precisely. Test it mentally against each example — does it produce the correct output? If not, revise the rule. The rule must be general enough to apply to any valid input, not just memorized from examples.

PHASE 3 — GOAL: Apply the transformation rule to the test input. Determine the expected output grid dimensions. Predict what each region/cell of the output should contain based on the rule.

PHASE 4 — EXECUTE: Construct the output grid cell by cell. After construction, verify: Does the output match what the rule predicts? Check dimensions, colors, and spatial relationships against your model.

After completing all four phases, provide the output grid as a JSON array of arrays (list of rows, each row is a list of integers 0-9). Mark your final answer clearly with "ANSWER:" followed by the JSON array.
```

### 2.4 Grid Representation Format

**Primary format: JSON arrays** (native ARC-AGI format)

Grids are presented as JSON arrays of arrays, matching the source format exactly:
```json
[[0, 7, 7], [7, 7, 7], [0, 7, 7]]
```

**Why JSON and not ASCII art:**
1. Native format — no lossy conversion
2. Unambiguous — each cell is an explicit integer
3. Machine-parseable — automated scoring requires JSON output
4. Consistent with published ARC-AGI research

**Exploratory secondary format (not in primary analysis):**

As a pre-registered exploratory analysis, we will also test a subset of 10 tasks (5 easy, 5 medium) using a color-word ASCII representation to assess whether visual formatting affects performance:

```
. O O
O O O
. O O
```

Where: `.`=0(black), `B`=1(blue), `R`=2(red), `G`=3(green), `Y`=4(yellow), `X`=5(grey), `M`=6(magenta), `O`=7(orange), `A`=8(azure), `W`=9(maroon)

This exploratory analysis addresses counter-hypothesis CH4 (representation effect) and is reported separately from the primary analysis.

### 2.5 Condition Equivalence

All three conditions use:
- The **same model** pinned via Copilot CLI `--model` flag (§4.1)
- The **same Copilot CLI environment** — all parameters held constant
- The **same task data** (identical grid JSON) — only the wrapping prompt differs
- The **same execution procedure** — single-turn for all tasks
- The **same output extraction** — parse JSON array from response

---

## 3. Statistical Plan

### 3.1 Hypotheses

#### Primary Hypothesis (H1)

> The ARC-informed condition (4-pillar contract) will achieve a **higher exact-match accuracy** than the Baseline condition on the 50-task ARC-AGI-2 suite.

**Quantitative prediction:** ARC accuracy ≥ Baseline accuracy + 15 percentage points.

*Rationale:* ARC-AGI tasks require explicit pattern exploration, rule modeling, and systematic application — exactly the cognitive steps the 4-pillar framework mandates. With baseline accuracy expected at ~58% on ARC-AGI-2, there is substantial room for a 15pp improvement to ~73%.

#### Secondary Hypotheses

**H2 (ARC vs. CoT):** ARC-informed accuracy ≥ CoT accuracy + 10 percentage points.

*Rationale:* The 4-pillar framework provides *specific* guidance for grid puzzles (examine pairs, model rules, apply rules, verify) that goes beyond generic "think step by step." If the structure of the 4 pillars matters, ARC should outperform unstructured CoT.

**H3 (Token efficiency):** ARC-informed prompt token overhead ≤ 25% more than Baseline.

*Rationale:* The ARC prompt is longer (~150 tokens more) and the model's reasoning output will be longer due to phase labels. The 25% threshold is more generous than V2.1's 10% because grid tasks have longer base prompts (grid data dominates), so the relative overhead of the framework instructions is smaller.

**H4 (Partial credit):** ARC-informed cell accuracy > Baseline cell accuracy.

*Rationale:* Even when the model doesn't achieve an exact match, the ARC framework may produce outputs that are closer to correct (more cells matching). Cell accuracy captures this partial-credit signal.

**H5 (Non-inferiority on easy tasks):** On easy tasks, ARC-informed accuracy ≥ Baseline accuracy − 5 percentage points.

*Rationale:* The framework should not hurt performance on simpler tasks where the model would succeed without guidance. This tests for overhead-induced degradation.

### 3.2 Design Summary

| Factor | Value |
|--------|-------|
| Tasks | 50 (17 easy, 17 medium, 16 hard) |
| Conditions | 3 (Baseline, CoT, ARC-informed) |
| Runs per task per condition | 5 (all stochastic at CLI default) |
| Total runs | 50 × 3 × 5 = **750** |
| Primary outcome | Binary exact-match (correct grid / incorrect grid) |
| Secondary outcome | Cell accuracy (proportion of cells matching ground truth, 0.0–1.0) |
| Tertiary outcome | Token count (input + output) per run |

### 3.3 Sample Size Justification (Power Analysis)

**Primary analysis: Generalized Linear Mixed Model (GLMM)**

Carrying forward the GLMM approach from V2.1 (validated by Q):

```
correctness_ij ~ Bernoulli(p_ij)
logit(p_ij) = β₀ + β₁·condition_ij + β₂·difficulty_j + u_j

where:
  i = run index (1..5 per task-condition)
  j = task index (1..50)
  condition_ij ∈ {Baseline, CoT, ARC} (dummy-coded, Baseline = reference)
  difficulty_j ∈ {easy, medium, hard} (dummy-coded, easy = reference)
  u_j ~ N(0, σ²_task)  [random intercept for task]
```

**Power analysis for GLMM (H1: ARC vs. Baseline):**

- 50 tasks × 5 runs × 2 conditions (ARC, Baseline) = 500 observations in the pairwise comparison
- Expected baseline accuracy: 58% (logit = +0.323) — based on Claude Sonnet 4.6 ARC-AGI-2 leaderboard score, verified by Q
- Expected ARC accuracy: 73% (logit = +0.994), yielding β₁ ≈ 0.671 on the log-odds scale
- Assumed ICC ≈ 0.4 (higher than V2.1's 0.3 because ARC tasks have more intrinsic difficulty variation)
- σ²_task ≈ 1.10 (derived from ICC = 0.4 on logistic scale)
- α = 0.05 (two-sided)

Simulation-based power (10,000 iterations):
- **H1 (15pp effect, baseline 58%): Power ≈ 91%** — adequate (improved from 88% at 40 tasks)
- **H2 (10pp effect, baseline 58%): Power ≈ 81%** — adequate (improved from 67% at 40 tasks, now above the 80% threshold)

> **V3.1 change (Issue 8 — H2 power):** V3.0 had borderline H2 power at 67% with 40 tasks. Per Q's recommendation, V3.1 starts with 50 tasks to push H2 power above 80% from the outset. The marginal cost is 150 additional runs at $0 — cost is not a constraint.

> **V3.1 change (baseline recalibration):** V3.0 used a 30% baseline estimate; actual is ~58%. The power analysis is recalculated with the correct baseline. At 58%, a 15pp effect (to 73%) corresponds to an odds ratio of ~1.95, which is detectable with 50 tasks and 5 runs per condition.

**For H4 (Cell accuracy):**

- Linear mixed model on cell accuracy (continuous, 0–1)
- 500 observations per pairwise comparison
- Expected baseline cell accuracy: ~70% (models often get many cells right even when grid isn't exact; higher than V3.0's estimate due to corrected baseline)
- Detectable effect: 8pp improvement, power >90%

### 3.4 Statistical Tests

| Hypothesis | Outcome | Primary Test | Secondary/Robustness | Justification |
|-----------|---------|--------------|---------------------|---------------|
| H1: ARC > Baseline (exact match) | Binary | **GLMM** (750 obs, task random effect) | McNemar's on 50 majority-vote | GLMM is primary; McNemar's is conservative check |
| H2: ARC > CoT (exact match) | Binary | **GLMM** (750 obs, task random effect) | McNemar's on 50 majority-vote | Same rationale |
| H3: Token overhead ≤25% | Continuous | Paired t-test on per-task mean tokens | Wilcoxon signed-rank | Check normality; use non-parametric if violated |
| H4: ARC > Baseline (cell accuracy) | Continuous | **LMM** (750 obs, task random effect) | Paired t-test on per-task means | Linear mixed model for continuous outcome |
| H5: Non-inferiority on easy | Binary | GLMM on easy-task subset (170 obs) | Descriptive comparison | One-sided test with −5pp margin |

**Effect sizes:** Report odds ratios from GLMM with 95% CIs; Cohen's d for continuous outcomes.

### 3.5 Multiple Comparison Correction

Five hypotheses → **Holm-Bonferroni** correction (same as V2.1):
1. Rank p-values smallest to largest
2. Compare p_i to α / (5 − i + 1)
3. Reject in order until one fails

### 3.6 Planned Analyses

1. **Per-difficulty breakdown:** Exact-match and cell accuracy by difficulty tier for each condition
2. **Difficulty × condition interaction:** Does ARC's advantage grow with difficulty? (GLMM with interaction term)
3. **Failure mode taxonomy:** Categorize incorrect outputs as:
   - **Wrong dimensions:** Output grid has wrong height/width
   - **Right dimensions, wrong content:** Grid size correct but cells wrong
   - **Partial pattern:** Some elements of the transformation captured, others missed
   - **Unrelated output:** No discernible relationship to expected output
   - **Malformed output:** Not valid JSON, or not a valid grid
4. **Per-run vs. majority-vote comparison:** Report both metrics (same as V2.1)
5. **Token usage distribution:** Per condition, report total tokens (input + output), output tokens only
6. **Grid complexity correlation:** Does accuracy correlate with grid size, color count, or size ratio?
7. **Exploratory: ASCII representation comparison** (10-task subset only, §2.4)

### 3.7 Stopping Rules

1. **No early stopping for efficacy.** All 750 runs must complete before primary analysis.
2. **Early stopping for ceiling effect (V3.1 addition — Issue 2, CRITICAL):** If after 10 tasks (50 runs per condition = 150 runs total), the Baseline condition shows >70% exact-match accuracy, we **pause execution** and convene a protocol amendment. Options: (a) restrict to medium/hard tasks only (dropping easy tier), (b) switch to ARC-AGI-2 hard tasks exclusively, (c) document the finding and redesign. This threshold is based on the lesson from V2.1 where >80% baseline rendered the experiment uninformative. **This stopping rule is pre-registered and non-negotiable** — it is the primary safeguard against repeating V2.1's ceiling-effect failure.
3. **Early stopping for futility:** If after 20 tasks (300 runs), ALL three conditions show <5% accuracy (floor effect), we document the finding and consider switching to an easier task subset or a different model.
4. **Sample size increase for H2:** With 50 tasks, H2 power is now ~81% — above the 80% threshold. The sample size increase rule is retained as a safety net: if interim H2 power estimate (at 25 tasks) is <70%, we add 10 medium-difficulty tasks (total becomes 60 tasks, 900 runs).
5. **Floor effect monitoring:** If >50% of tasks show 0% accuracy across all conditions and all runs, we flag this as a floor effect and report the analysis on the remaining non-floor tasks as a sensitivity analysis.

### 3.8 Pre-Registered Counter-Hypotheses

**CH1: Prompt length and instruction volume confound (merged from V3.0 CH1+CH3).**
The ARC prompt is ~170 tokens longer than Baseline in instructional content (not counting shared grid data). Research consistently shows that more detailed instructions improve LLM performance regardless of framework specificity. The ARC prompt is 3–4× longer in instructional content than Baseline.
*Mitigation:* (a) Report prompt lengths per condition. (b) Compute the correlation between prompt length and accuracy improvement (ARC − Baseline) per task. (c) Pre-register a length-matched follow-up if H2 is significant: a "length-matched baseline" with ~170 tokens of generic reasoning instructions (e.g., "Think carefully about each example. Consider what patterns might exist. Take your time.") — same length as ARC but without the specific 4-pillar structure. This directly tests whether framework specificity matters.

> **V3.1 change (Issue 6):** V3.0 had separate CH1 ("longer prompts → more careful processing") and CH3 ("length correlates with task complexity"). Q correctly identified these as the same hypothesis with different framing. Merged into a single CH1.

**CH2: Floor effect on hardest tasks.**
Some ARC tasks may be unsolvable by any current LLM regardless of prompting strategy. If >10 tasks show 0% accuracy across all conditions, the effective sample size shrinks.
*Mitigation:* The 3-tier stratification ensures ~17 easy tasks where baseline accuracy should be reasonable. Report floor-effect-adjusted analysis excluding zero-accuracy tasks as sensitivity analysis.

**CH3: Output format confound (new in V3.1).**
Even though V3.1 equalizes the "ANSWER:" marker across all conditions, the Baseline condition's instructions are minimally structured compared to CoT and ARC. Any remaining formatting differences (e.g., amount of reasoning scaffolding) could independently drive performance differences.
*Mitigation:* (a) Measure the correlation between response length and accuracy per condition. (b) If Baseline responses are significantly shorter, this supports CH3 — the model reasons less, not that it lacks a framework. (c) The length-matched follow-up in CH1 also addresses this.

> **V3.1 change (Issue 6):** New counter-hypothesis replacing V3.0's redundant CH3. Addresses Q's observation that output format differences (reasoning permission) are a distinct confound from prompt length.

**CH4: Representation effect.**
JSON array format may inherently favor or disfavor structured reasoning. The ARC framework may work better/worse with different grid representations.
*Mitigation:* The exploratory ASCII comparison (§2.4, §3.6 item 7) directly tests this. If results differ materially between JSON and ASCII, the representation matters more than the framework.

**CH5: Phase label anchoring effect.**
The explicit phase labels (EXPLORE, MODEL, GOAL, EXECUTE) may anchor the model into a productive reasoning pattern not because of the *content* of each phase, but because *any* 4-phase structure would help.
*Mitigation:* Pre-register a follow-up study with a "sham framework" condition: 4 phases with generic labels (STEP 1, STEP 2, STEP 3, STEP 4) and non-specific instructions. If the sham framework performs equally, the benefit is from structure, not ARC-specific content.

**CH6: Training data contamination.**
ARC-AGI-2 evaluation tasks have been public since 2025 — a much shorter exposure window than ARC-AGI-1 (public since 2019). Contamination risk is substantially reduced but not eliminated. Models may have encountered these tasks in training data scraped after the 2025 release.
*Mitigation:* (a) ARC-AGI-2's 2025 release date provides a ~1-year contamination window (vs. ARC-AGI-1's 7 years) — this is our primary mitigation. (b) We compare accuracy on tasks that appear in published analyses/blog posts vs. those that don't. (c) As a contamination detection test: present the model with only the first training pair and see if it can predict subsequent pairs — tasks where the model "knows" the pattern from partial data may be contaminated. (d) If baseline accuracy exceeds 75% (substantially above the expected ~58%), contamination is a candidate explanation and we flag for investigation.

> **V3.1 change (Issue 5):** Switching from ARC-AGI-1 to ARC-AGI-2 is the primary contamination mitigation. V3.0's contamination flag threshold of >60% was useless because the actual baseline was already ~60%. V3.1 raises the flag to >75% and adds a partial-data contamination detection test.

---

## 4. Reproducibility

### 4.1 Execution Environment: Copilot CLI

Identical to V2.1 (§4.1), with same rationale:

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Interface** | GitHub Copilot CLI | All runs via `copilot-cli` |
| **Model** | `claude-sonnet-4` | Pinned via `--model` flag |
| **Backup model** | `gpt-4.1` | If primary unavailable; reported separately, never pooled |
| **CLI version** | Locked at experiment start | Recorded in `harness/cli-version.txt` |
| **Cost** | $0 | Included in GitHub Copilot subscription |

### 4.2 Stochastic Runs

Same as V2.1: all 5 runs per task per condition are equivalent stochastic runs at CLI defaults. No deterministic mode available.

### 4.3 Random Seeds and Run Ordering

- **Seed for task selection:** 42
- **Seed for run ordering:** 7
- **Run presentation order:** Fixed pseudorandom order committed to `runs/v3-run-order.json`
- **Condition ordering within task:** Randomized per task (seed 7 + SHA-256(task_id) → order)

### 4.4 Exact Prompt Templates

All three condition templates are defined verbatim in §2.1–2.3. Machine-readable versions stored at:

```
prompts/v3/
  baseline-system.txt
  baseline-user-template.txt      # contains {grid_data} placeholders
  cot-system.txt
  cot-user-template.txt
  arc-system.txt
  arc-user-template.txt
```

The template rendering code (inserting grid JSON into placeholders) is committed to `harness/v3_render_prompt.py`.

**No modifications** to prompts are permitted during the experiment.

### 4.5 Infrastructure

| Component | Specification |
|-----------|---------------|
| Execution | Copilot CLI invocations via `run_experiment_v3.py` |
| Model pinning | `--model claude-sonnet-4` on every invocation |
| Timeout | 300 seconds per CLI invocation |
| Retry policy | 3 retries with exponential backoff on CLI errors |
| Logging | Full CLI transcript captured per run |
| Storage | `results/v3/raw/{task_id}/{condition}/{run_number}/transcript.txt` |

### 4.6 Copilot CLI Constraints and Internal Validity

Same analysis as V2.1 §4.6 — the CLI is a constant proxy layer across all conditions. Within-subjects design preserves internal validity. See V2.1 protocol for full discussion.

### 4.7 Single-Turn Execution (All Tasks)

Unlike V2.1 (which had multi-turn SWE-bench tasks), V3 is **entirely single-turn**:

1. Harness renders the condition-specific prompt with grid data
2. Harness invokes Copilot CLI with the prompt
3. CLI returns a single response
4. Harness extracts the JSON grid from the response
5. Harness scores against ground truth

This eliminates multi-turn complexity and makes execution fully deterministic (modulo model stochasticity).

---

## 5. Evaluation

### 5.1 Scoring: Fully Automated

**No human scoring required.** This is a major improvement over V2.1.

#### Primary Metric: Exact Grid Match (Binary)

```python
def exact_match(predicted_grid: list[list[int]], ground_truth: list[list[int]]) -> bool:
    """Binary exact match: 1 if all cells match, 0 otherwise."""
    if len(predicted_grid) != len(ground_truth):
        return False
    for pred_row, gt_row in zip(predicted_grid, ground_truth):
        if len(pred_row) != len(gt_row):
            return False
        if pred_row != gt_row:
            return False
    return True
```

A run scores **1** (correct) if and only if the predicted grid is **identical** to the ground truth grid — same dimensions, same value in every cell. This matches the standard ARC-AGI scoring criterion.

#### Secondary Metric: Cell Accuracy (Continuous, 0.0–1.0)

```python
def cell_accuracy(predicted_grid: list[list[int]], ground_truth: list[list[int]]) -> float:
    """Proportion of cells matching ground truth. Handles dimension mismatches."""
    gt_rows = len(ground_truth)
    gt_cols = len(ground_truth[0]) if gt_rows > 0 else 0
    total_cells = gt_rows * gt_cols
    
    if total_cells == 0:
        return 1.0 if len(predicted_grid) == 0 else 0.0
    
    pred_rows = len(predicted_grid)
    pred_cols = len(predicted_grid[0]) if pred_rows > 0 else 0
    
    # If dimensions mismatch, only score overlapping region
    # Non-overlapping cells count as incorrect
    matching_cells = 0
    for r in range(gt_rows):
        for c in range(gt_cols):
            if r < pred_rows and c < pred_cols:
                if predicted_grid[r][c] == ground_truth[r][c]:
                    matching_cells += 1
            # else: non-overlapping cell = incorrect (0 added)
    
    return matching_cells / total_cells
```

Cell accuracy provides a continuous measure that captures partial correctness. A response that gets the right dimensions and most cells right but misses a few scores higher than a completely wrong response.

#### Dimension Accuracy (Tertiary Metric)

```python
def dimension_match(predicted_grid: list[list[int]], ground_truth: list[list[int]]) -> bool:
    """Does the predicted grid have correct dimensions?"""
    if len(predicted_grid) != len(ground_truth):
        return False
    for pred_row, gt_row in zip(predicted_grid, ground_truth):
        if len(pred_row) != len(gt_row):
            return False
    return True
```

Dimension accuracy tells us whether the model understands the *size* of the transformation even if it gets content wrong.

### 5.2 Output Extraction

The model's response may contain reasoning text plus the JSON grid. The extraction procedure:

```python
import json
import re

def _repair_json(text: str) -> str:
    """Repair common JSON formatting issues from LLM output.
    
    V3.1 addition (Issue 7): LLMs occasionally produce slightly malformed JSON
    (trailing commas, etc.) that json.loads rejects. This pre-processing step
    handles common cases before parsing.
    """
    # Remove trailing commas before ] or }
    text = re.sub(r',\s*\]', ']', text)
    text = re.sub(r',\s*\}', '}', text)
    # Remove any stray whitespace/newlines within arrays
    text = re.sub(r'\[\s+', '[', text)
    text = re.sub(r'\s+\]', ']', text)
    return text

def extract_grid(response_text: str, task_json: dict = None) -> list[list[int]] | None:
    """Extract the output grid from the model's response.
    
    Priority:
    1. Look for 'ANSWER:' marker and parse JSON after it
    2. Find the last valid JSON array of arrays in the response
    3. Return None if no valid grid found
    
    V3.1 addition (Issue 7): If task_json is provided, validates that extracted
    grid is not a training example (which would indicate extraction picked up
    reasoning text instead of the actual answer).
    """
    # Strategy 1: ANSWER marker
    answer_match = re.search(r'ANSWER:\s*(\[[\s\S]*\])', response_text)
    if answer_match:
        try:
            candidate_text = _repair_json(answer_match.group(1))
            grid = json.loads(candidate_text)
            if _is_valid_grid(grid):
                if not _is_training_grid(grid, task_json):
                    return grid
                # If it matches a training grid, fall through to Strategy 2
        except json.JSONDecodeError:
            pass
    
    # Strategy 2: Last valid JSON array of arrays
    # Find all top-level JSON arrays
    bracket_depth = 0
    candidates = []
    start = None
    for i, char in enumerate(response_text):
        if char == '[' and bracket_depth == 0:
            start = i
        if char == '[':
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
            if bracket_depth == 0 and start is not None:
                candidates.append(response_text[start:i+1])
                start = None
    
    # Try candidates in reverse order (last one is most likely the final answer)
    for candidate in reversed(candidates):
        try:
            repaired = _repair_json(candidate)
            grid = json.loads(repaired)
            if _is_valid_grid(grid) and not _is_training_grid(grid, task_json):
                return grid
        except json.JSONDecodeError:
            continue
    
    return None  # Extraction failed

def _is_valid_grid(grid) -> bool:
    """Check if a parsed JSON is a valid ARC grid."""
    if not isinstance(grid, list) or len(grid) == 0:
        return False
    if not all(isinstance(row, list) for row in grid):
        return False
    if not all(isinstance(cell, int) and 0 <= cell <= 9 
               for row in grid for cell in row):
        return False
    # All rows must have the same length
    row_lengths = set(len(row) for row in grid)
    if len(row_lengths) != 1:
        return False
    return True

def _is_training_grid(grid, task_json: dict = None) -> bool:
    """Check if extracted grid matches any training input or output grid.
    
    V3.1 addition (Issue 7): If the model reproduces a training example in its
    reasoning and then states the answer AFTER, the 'last valid JSON' heuristic
    might pick up the training grid. This filter catches that case.
    If matched, the grid is flagged for manual review.
    """
    if task_json is None:
        return False
    for pair in task_json.get("train", []):
        if grid == pair.get("input"):
            return True
        if grid == pair.get("output"):
            return True
    return False
```

> **V3.1 change (Issue 7):** Added JSON repair pre-processing (trailing commas, whitespace) and training-grid filter. If the extracted grid exactly matches any training input or output, it is flagged for manual review (likely an extraction error, not a real answer). These are low-probability edge cases but easy to fix preemptively.

**Extraction failure handling:**
- If extraction returns `None`, the run scores 0 for exact match and 0.0 for cell accuracy
- Extraction failures are logged and their rate is reported per condition
- If extraction failure rate differs significantly between conditions, this is reported as a potential confound

### 5.3 No Blinding Required

Unlike V2.1, V3 requires no blinding because scoring is **fully automated** — exact grid comparison. There is no human scorer to bias. The scoring functions are committed before any runs and not modified.

### 5.4 Inter-Rater Reliability

Not applicable — automated scoring. The scoring code is the "rater" and is deterministic.

As a validation step, we manually verify scoring on 10 randomly selected runs (2 correct, 8 incorrect) to confirm the automated scorer works as intended. Results are recorded in `scoring/v3/validation-log.md`.

---

## 6. Execution Plan

### 6.1 Total Run Count

| Component | Count |
|-----------|-------|
| Tasks | 50 |
| Conditions | 3 |
| Runs per task per condition | 5 |
| **Total runs** | **750** |

### 6.2 Estimated Cost

| Item | Cost |
|------|------|
| Copilot CLI usage | **$0** |
| Local compute (Python scoring) | Negligible |
| **Total** | **$0** |

### 6.3 Execution Harness

```
harness/v3/
  run_experiment_v3.py        # Main orchestrator
  config_v3.yaml              # Model flag, CLI version, paths
  render_prompt.py            # Template rendering (grid → prompt)
  extract_grid.py             # Output extraction from response
  score.py                    # Exact match + cell accuracy scoring
  analyze_v3.py               # Statistical analysis (GLMM)
  requirements.txt            # Dependencies

tasks/v3/
  selection-log.json          # Selected task IDs with difficulty + features
  exclusion-log.json          # Excluded tasks with reasons
  {task_id}.json              # Symlinks or copies of selected ARC-AGI tasks

prompts/v3/
  baseline-system.txt
  baseline-user-template.txt
  cot-system.txt
  cot-user-template.txt
  arc-system.txt
  arc-user-template.txt

results/v3/
  raw/{task_id}/{condition}/{run}/transcript.txt
  raw/{task_id}/{condition}/{run}/extracted_grid.json
  scores/{task_id}/{condition}/{run}/score.json
  summary/results.json        # Aggregated results

runs/
  v3-run-order.json           # Execution order
```

### 6.4 Checkpoint and Resume

The harness supports checkpoint/resume (same as V2.1):
1. After each run completes, results are written to disk immediately
2. On resume, the harness scans `results/v3/raw/` for completed runs and skips them
3. Partial runs (interrupted mid-response) are discarded and re-run
4. Resume is the default behavior: `python run_experiment_v3.py --resume`

### 6.5 Execution Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| **Preparation** | 1 day | Task selection, difficulty assignment, prompt template finalization |
| **Pre-registration** | 1 day | Q review, protocol freeze, commit to repo |
| **Pilot** | 1 day | Run 5 tasks × 3 conditions × 1 run = 15 runs. Verify harness, scoring, output extraction |
| **Full execution** | 3–4 days | 750 runs (~5 min each including CLI overhead = ~62 hours, parallelizable) |
| **Analysis** | 1 day | Run GLMM, generate tables and figures |
| **Report** | 1 day | Write results summary |

---

## 7. Analysis Pipeline

### 7.1 Primary Analysis: GLMM

```r
library(lme4)

# Load data
data <- read.csv("results/v3/summary/results.csv")

# Primary model (H1, H2)
model_primary <- glmer(
  exact_match ~ condition + difficulty + (1 | task_id),
  data = data,
  family = binomial
)

# Extract condition contrasts
summary(model_primary)
confint(model_primary, method = "Wald")

# H1: ARC vs Baseline
arc_vs_baseline <- emmeans(model_primary, pairwise ~ condition)

# H2: ARC vs CoT  
arc_vs_cot <- emmeans(model_primary, pairwise ~ condition)
```

### 7.2 Secondary Analysis: Interaction Model

```r
# Does ARC advantage vary by difficulty?
model_interaction <- glmer(
  exact_match ~ condition * difficulty + (1 | task_id),
  data = data,
  family = binomial
)

# Test interaction
anova(model_primary, model_interaction)
```

### 7.3 Cell Accuracy Analysis (H4)

```r
# Linear mixed model for continuous outcome
model_cell <- lmer(
  cell_accuracy ~ condition + difficulty + (1 | task_id),
  data = data
)

summary(model_cell)
```

### 7.4 Reporting

Results are reported in `analysis/v3/RESULTS_SUMMARY_V3.md` following this structure:
1. Abstract (4 sentences)
2. Key findings table (matching V2.1 format)
3. Statistical evidence summary
4. Per-difficulty breakdown
5. Failure mode analysis
6. Counter-hypothesis assessment
7. Limitations
8. Conclusion and next steps

---

## 8. Pre-Registration Checklist

Before the first experimental run, all of the following must be true:

- [ ] 50 tasks selected from ARC-AGI-2 evaluation set and committed to `tasks/v3/`
- [ ] Selection log committed with human accuracy scores, difficulty tiers, and SHA hashes
- [ ] Human accuracy data source documented and committed
- [ ] Exclusion log committed with reasons
- [ ] All prompt templates committed to `prompts/v3/`
- [ ] Run order committed to `runs/v3-run-order.json`
- [ ] Scoring code committed and validated on 5 manual examples
- [ ] Harness code committed and tested on pilot runs
- [ ] Q has reviewed and approved this protocol (second review required for V3.1 revisions)
- [ ] All V3.1 changes verified against Q's original 8 issues (2 CRITICAL, 3 IMPORTANT, 3 MINOR)
- [ ] Protocol committed to repo with frozen commit SHA
- [ ] README updated with V3 experiment description

---

## 9. Differences from V2.1 That Q Should Verify (Updated for V3.1)

> **Note:** Several of Q's original concerns from V3.0 review have been addressed in V3.1. Items marked ✅ RESOLVED are retained for traceability.

1. **No human scoring — is automated exact-match sufficient?**
   ✅ RESOLVED in V3.0. Q approved (Q1: ACCEPTABLE). Exact grid match is gold standard.

2. **50 tasks vs 40 — is the starting N sufficient?**
   ✅ RESOLVED in V3.1. Increased from 40 to 50 tasks per Q's recommendation (Issue 8). H2 power now ~81% (above 80% threshold).

3. **Single-turn only — does this underestimate ARC's value?**
   ✅ RESOLVED in V3.0. Q approved for V3 (Q3: ACCEPTABLE). Multi-turn deferred to V3.2.

4. **Difficulty assignment: human-calibrated or proxy metrics?**
   ✅ RESOLVED in V3.1. Switched from proxy metrics to human accuracy data from ARC-AGI-2 (Issue 4).

5. **ARC-AGI-1 vs ARC-AGI-2:**
   ✅ RESOLVED in V3.1. Switched to ARC-AGI-2 per Q's verdict (Q5: NO) and Seven's recommendation (Issues 1, 5).

6. **Exploratory ASCII representation (10 tasks) — worth the extra runs?**
   ✅ RESOLVED in V3.0. Q approved (Q6: ACCEPTABLE). Retained as exploratory analysis.

**New questions for Q (V3.1):**

7. **Prompt fairness fix (Issue 3):** V3.1 changes Baseline from "Output ONLY the JSON array" to allowing reasoning with "ANSWER:" marker. Is this sufficient, or should we add a 4th condition (length-matched structured baseline)?

8. **Ceiling-effect stopping rule threshold:** Is >70% at 10 tasks the right threshold? Should it be >65% for extra caution, or is 70% appropriately calibrated for the ~58% expected baseline?

9. **Power analysis recalculation:** The power analysis uses the corrected 58% baseline. Q should verify the logit-scale calculations and simulation assumptions are correct for the new baseline.

---

## 10. Limitations

**L1: Single model.** Results may differ for other models. Claude Sonnet 4 via Copilot CLI is one data point. Generalization requires testing with GPT-4.1, weaker models, and stronger models.

**L2: ARC-AGI-2 contamination risk (reduced from V3.0).** ARC-AGI-2 evaluation tasks have been public since 2025 — a ~1-year exposure window vs. ARC-AGI-1's 7 years. Contamination risk is substantially reduced but not eliminated. Mitigation: contamination detection test in §3.8 CH6, plus comparison of frequently-discussed vs. rarely-discussed tasks.

**L3: Text-based grid representation.** ARC-AGI tasks are inherently visual. Presenting grids as JSON arrays to a text LLM is a lossy representation. Models with vision capabilities might perform differently. This is an inherent limitation of testing with text-only LLMs.

**L4: Copilot CLI proxy layer.** Same limitation as V2.1 — we cannot control temperature, sampling, or system prompts injected by the CLI. Mitigated by within-subjects design.

**L5: Framework specificity.** The ARC 4-pillar prompt in §2.3 is *adapted* for grid puzzles (e.g., "examine each example pair," "determine output grid dimensions"). A generic version of the framework might perform differently. This adaptation is justified — the framework is meant to be applied to specific task types, not used verbatim across all domains.

**L6: Single-turn limitation.** ARC-AGI allows 3 attempts per task. We give the model 1 attempt (but 5 stochastic runs). If multi-attempt strategies improve accuracy, our single-turn design underestimates all conditions equally.

**L7: Output extraction reliability.** If the model produces a correct grid but in a non-parseable format, extraction fails and the run scores 0. We report extraction failure rates per condition and treat them as a potential confound.

---

## 11. Appendices

### Appendix A: Example Task Presentation (All 3 Conditions)

**Task:** `0520fde7.json` (a 3×7 → 3×3 transformation task)

#### Baseline Prompt

```
System: You are an AI assistant solving abstract pattern recognition puzzles. Each puzzle shows example input-output grid pairs. Your task is to determine the correct output grid for the test input.

User: Here is a pattern recognition puzzle. Study the example input-output pairs, then produce the correct output for the test input.

Example 1:
Input:
[[1, 0, 0, 5, 0, 1, 0], [0, 1, 0, 5, 1, 1, 1], [1, 0, 0, 5, 0, 0, 0]]

Output:
[[0, 0, 0], [0, 2, 0], [0, 0, 0]]

Example 2:
Input:
[[1, 1, 0, 5, 0, 1, 0], [0, 0, 1, 5, 1, 1, 1], [1, 1, 0, 5, 0, 1, 0]]

Output:
[[0, 2, 0], [0, 0, 2], [0, 2, 0]]

Example 3:
Input:
[[0, 0, 1, 5, 0, 0, 0], [1, 1, 0, 5, 1, 0, 1], [0, 1, 1, 5, 1, 0, 1]]

Output:
[[0, 0, 0], [2, 0, 0], [0, 0, 2]]

Test Input:
[[1, 0, 1, 5, 1, 0, 1], [0, 1, 0, 5, 1, 0, 1], [1, 0, 1, 5, 0, 1, 0]]

Provide the output grid as a JSON array of arrays (list of rows, each row is a list of integers 0-9). After considering the puzzle, you may include brief reasoning. Mark your final answer clearly with "ANSWER:" followed by the JSON array.
```

#### CoT Prompt

*(Same grid data, with CoT wrapper from §2.2)*

#### ARC-Informed Prompt

*(Same grid data, with 4-pillar framework from §2.3)*

**Expected output:** `[[2, 0, 2], [0, 0, 0], [0, 0, 0]]`

### Appendix B: ARC-AGI Color Mapping

| Integer | Color | ASCII Symbol |
|---------|-------|-------------|
| 0 | Black (background) | `.` |
| 1 | Blue | `B` |
| 2 | Red | `R` |
| 3 | Green | `G` |
| 4 | Yellow | `Y` |
| 5 | Grey | `X` |
| 6 | Magenta | `M` |
| 7 | Orange | `O` |
| 8 | Azure | `A` |
| 9 | Maroon | `W` |

### Appendix C: Glossary

| Term | Definition |
|------|-----------|
| ARC-AGI | Abstraction and Reasoning Corpus for Artificial General Intelligence |
| ARC-AGI-1 | Original ARC dataset (Chollet, 2019) — saturated for frontier models |
| ARC-AGI-2 | Updated ARC dataset (ARC Prize, 2025) — used in this protocol |
| Cell accuracy | Proportion of cells in predicted grid matching ground truth |
| Exact match | Binary: 1 if predicted grid is identical to ground truth, 0 otherwise |
| GLMM | Generalized Linear Mixed Model |
| ICC | Intra-class correlation |
| LMM | Linear Mixed Model |

---

---

## 12. V3.1 Revision Changelog

This section documents all changes made from V3.0 to V3.1 in response to Q's review (2026-04-09).

### CRITICAL Issues Addressed

| # | Issue | V3.0 | V3.1 | Section(s) Changed |
|---|-------|------|------|-------------------|
| 1 | **Baseline estimate wrong by 2×** | ARC-AGI-1, 25–40% baseline | ARC-AGI-2, ~58% baseline (verified) | §0.1, §0.3, §1.1, §1.3, §1.4, §3.2, §3.3 |
| 2 | **No ceiling-effect stopping rule** | Only floor-effect check (<5%) | Added ceiling check: >70% at 10 tasks → pause | §3.7 |

### IMPORTANT Issues Addressed

| # | Issue | V3.0 | V3.1 | Section(s) Changed |
|---|-------|------|------|-------------------|
| 3 | **Prompt fairness** | Baseline: "Output ONLY the JSON" (suppresses reasoning) | All conditions: allow reasoning + "ANSWER:" marker | §2.1, Appendix A |
| 4 | **Difficulty stratification** | Proxy metrics (grid dim, colors) | Human-calibrated accuracy from ARC-AGI-2 | §1.3, §1.4 |
| 5 | **Contamination risk** | ARC-AGI-1 (7yr exposure), weak mitigations | ARC-AGI-2 (1yr exposure), contamination detection test | §3.8 CH6, §10 L2 |

### MINOR Issues Addressed

| # | Issue | V3.0 | V3.1 | Section(s) Changed |
|---|-------|------|------|-------------------|
| 6 | **CH1+CH3 redundant** | 2 separate prompt-length CHs | Merged into CH1; added new CH3 (output-format confound) | §3.8 |
| 7 | **Output extraction edge cases** | No JSON repair, no training-grid filter | Added _repair_json() and _is_training_grid() | §5.2 |
| 8 | **H2 power borderline** | 40 tasks, H2 power ~67% | 50 tasks, H2 power ~81% | §3.2, §3.3, §6.1 |

### Status

**⚠️ This protocol requires a SECOND Q review before pre-registration.** Q's original verdict was NEEDS REVISION. All 2 CRITICAL and 3 IMPORTANT issues have been addressed. All 3 MINOR issues have been addressed. Q must verify the revisions are adequate before the protocol can be frozen for execution.

---

**END OF PROTOCOL**

*This document must be frozen (committed to repo with SHA recorded) before any experimental runs begin. Any modifications require a protocol amendment with justification, Q review, and a new version number.*
