# ARC 4-Pillar Software Engineering Experiment — V4 Protocol (Revised)

**Version:** 4.1 (Post-Q Review)  
**Date:** 2026-07-14  
**Author:** Picard (Lead, Architecture & Decisions)  
**Reviewer:** Q (Devil's Advocate & Fact Checker)  
**Status:** PRE-REGISTRATION READY — All Q review findings addressed  
**Predecessors:** V2.1 (ceiling effect), V3.1 (domain mismatch, null result)  

---

## Revision Log (Q Review)

This section documents every change made to address Q's adversarial review (`Q_REVIEW_V4_PROTOCOL.md`). Each change references Q's finding ID.

### Fatal Flaws Fixed

| ID | Finding | Change Made |
|----|---------|-------------|
| **F1** | `statsmodels.MixedLM` is a LINEAR mixed model, not logistic — all p-values would be wrong for binary pass/fail data | Replaced primary analysis tool with `pymer4` (Python wrapper for R's `lme4::glmer(family=binomial)`). Updated §6.2 model specification, all code snippets, and §9.2 analysis script references. `statsmodels.MixedLM` (LPM) retained as a pre-registered sensitivity check in §6.5. |
| **F2** | CH2 uses `response_token_count` as a covariate — this is a post-treatment variable on the causal pathway, creating collider bias | Reframed CH2 as DESCRIPTIVE ONLY in §1.4. Response token counts are reported by condition but NOT used as a covariate in the primary GLMM. Added mediation analysis note explaining that if ARC increases token count AND token count predicts success, this indicates ARC works partly through encouraging more thorough reasoning. Updated §6.5 R6 robustness check to remove response tokens as GLMM covariate. |
| **F3** | Ambiguity about whether 30 pilot runs are included in the main 900-run analysis — if included, creates circular data double-dipping | Explicitly stated in §7.2 and §7.4 that pilot runs are EXCLUDED from all main analyses. All 60 tasks receive 5 FRESH repetitions per condition in the main experiment. Fresh random seeds are used for all main runs. Pilot data is stored separately and used solely for calibration. |

### Serious Concerns Addressed

| ID | Finding | Change Made |
|----|---------|-------------|
| **S1** | No random slopes in GLMM — assumes condition effect is identical across all 60 tasks, violating Barr et al. (2013) maximal structure recommendation | Updated §6.2 primary model to `pass ~ condition + (1 + condition | task_id)` with random slopes for condition within task. Added pre-registered fallback: if maximal model fails to converge, simplify to random intercepts only and report both attempts. |
| **S3** | SWE-bench contamination risk — Claude likely trained on SWE-bench solutions | Added contamination detection step in §2.6 (new section). For each SWE-bench task, run one trial at temperature=0 with NO repository context. If model produces correct patch without seeing the code, flag task as potentially contaminated. Run sensitivity analysis excluding flagged tasks. |
| **S7** | No manipulation check for ARC compliance — cannot verify the model actually followed EXPLORE→MODEL→GOAL→EXECUTE | Added §5.6 (new section): Manipulation Check for ARC Compliance. Regex-based detection of EXPLORE, MODEL, GOAL, EXECUTE section headers. Record `arc_compliance` (0–4 scale). Report mean compliance. Sensitivity analysis excluding non-compliant responses (compliance < 3). |
| **S8** | One-sided tests cannot detect ARC being WORSE — conflicts with outcome matrix which includes "ARC significantly WORSE" | Added exploratory two-sided tests (α=0.05) in §6.3 to detect potential negative effects. Updated §12.1 outcome matrix to clarify that degradation detection uses the exploratory two-sided test, not the primary one-sided test. |

### Prompt Design Fixes

| ID | Finding | Change Made |
|----|---------|-------------|
| **P1** | Instruction density confound — ARC has ~16 sub-instructions vs CoT's ~3; performance difference could be due to instruction quantity, not framework structure | Enriched CoT prompt (§3.2) to ~10 sub-instructions covering edge cases, error handling, logic verification, off-by-one errors, test cases, performance, and solution review. This narrows the instruction density gap while preserving the key difference: CoT gives generic step-by-step guidance, ARC provides structured 4-pillar methodology. Updated §3.5 fairness analysis. |
| **P2** | Bookend reminder asymmetry — ARC has a reminder line after code context that Baseline and CoT lack | Added equivalent bookend reminders to ALL conditions in §3.1 and §3.2. Baseline: "Provide your solution below." CoT: "Think step-by-step, then provide your solution below." ARC: (existing reminder retained). |

### Counter-Hypothesis Additions

| ID | Finding | Change Made |
|----|---------|-------------|
| **CH6** | Missing: Memorization/contamination counter-hypothesis | Added CH6 to §1.4: Compare ARC effect size on SWE-bench tasks vs non-SWE-bench tasks. If ARC helps more on non-SWE-bench tasks, effect is unlikely contamination-driven. |
| **CH7** | Missing: Instruction density vs framework structure | Added CH7 to §1.4: Acknowledge this design cannot fully disentangle instruction density from framework structure without a 4th condition. Note that enriched CoT prompt (P1 fix) partially addresses it. |
| **CH8** | Missing: Format-aided extraction | Added CH8 to §1.4: Compare scores on tasks with unambiguous pass/fail (unit tests) vs tasks requiring judgment (code review). If ARC helps equally on both, format-aided extraction is unlikely. |

### Methodology Gaps Addressed

| ID | Finding | Change Made |
|----|---------|-------------|
| **M1** | No inter-rater reliability for task curation | Added note in §2.2 (Source 4): Task curation is performed by the experiment author. Acknowledged as a limitation. Task selection criteria are pre-registered to reduce curator degrees of freedom. |
| **M5** | No category-level difficulty verification | Added pilot decision rule in §7.3: After pilot, verify baseline pass rates are approximately uniform across task categories (±15pp from overall mean). If any category is an extreme outlier, replace tasks to achieve balance. |

---

## EXECUTIVE SUMMARY

V2.1 tested Squad's ARC 4-pillar reasoning framework (Explore → Model → Goal → Execute) on 50 custom software/logic tasks and found a **ceiling effect** — all conditions scored ≥98%, leaving no headroom to detect framework benefits. V3.1 pivoted to ARC-AGI-2 visual grid puzzles and found a **null result** at ~2–3% exact match — the framework wasn't designed for visual abstract reasoning.

**V4 returns to software engineering** — Squad's native domain — with properly calibrated task difficulty. We source 60 real-world software engineering tasks from established benchmarks (SWE-bench Verified, CodeContests, MBPP+) and real GitHub issues, targeting a 40–70% baseline pass rate. Tasks span 6 SE categories (bug diagnosis, refactoring, architecture, test generation, code review, integration). Each task has automated scoring via test suites or exact-match evaluation.

**What makes V4 definitive:**
1. Tests what Squad was actually built for (software engineering, not visual puzzles)
2. Difficulty calibrated via pilot — tasks where baseline AI fails 30–60% of the time
3. Real codebases and scenarios, not synthetic toy problems
4. Automated scoring eliminates human scorer bias
5. Pre-registered stopping rules prevent another ceiling/floor effect

---

## 0. Motivation and Lineage

### 0.1 The Experimental Arc

| Experiment | Domain | Tasks | Baseline Accuracy | Outcome | Failure Mode |
|-----------|--------|-------|-------------------|---------|--------------|
| **V2.1** | Software/logic (custom) | 50 × 3 × 5 = 750 runs | 98% | Ceiling effect | Tasks too easy |
| **V3.1** | ARC-AGI-2 visual puzzles | 50 × 3 × 5 = 750 runs | 2.9% exact, 65% cell | Null result | Wrong domain (visual reasoning) |
| **V4.0** | Software engineering (real) | 60 × 3 × 5 = 900 runs | Target: 40–70% | **THIS EXPERIMENT** | — |

### 0.2 Why V4 Is Necessary

V3.1 conclusively showed the ARC framework does NOT help with visual abstract reasoning (p > 0.80 for all hypotheses). But this was never the claim — Squad's framework was designed for **software engineering tasks**: debugging, refactoring, architecture, code review. V2.1 attempted to test this but failed due to insufficient task difficulty (custom tasks were trivially solvable by Claude Sonnet 4).

V4 closes the experimental gap by:
1. **Returning to SE domain** with real-world tasks from established benchmarks
2. **Proper difficulty calibration** via mandatory pilot phase before full execution
3. **Automated scoring** via test suites — no human scorer bias
4. **Sufficient statistical power** for medium effect sizes (Cohen's d ≥ 0.5)

### 0.3 What Carries Forward

| Component | V2.1 | V3.1 | V4.0 | Rationale |
|-----------|------|------|------|-----------|
| 3-condition design | ✅ | ✅ | ✅ | Baseline vs CoT vs ARC — consistent across all experiments |
| GLMM primary analysis | ✅ | ✅ | ✅ | Same statistical framework, proven from V2.1/V3.1 |
| 5 runs per condition | ✅ | ✅ | ✅ | Same stochastic sampling strategy |
| Copilot Chat API | ✅ | ✅ | ✅ | Same $0 infrastructure (Claude Sonnet 4) |
| Counter-hypotheses | ✅ | ✅ | ✅ | Pre-registered alternative explanations |
| Automated scoring | Partial | ✅ | ✅ | Eliminates scorer bias |
| Difficulty stratification | ✅ | ✅ | ✅ | Easy/medium/hard tiers for interaction effects |
| Ceiling-effect stopping rule | ✗ | ✅ | ✅ | Mandatory — prevents V2.1 repeat |

### 0.4 What Changes in V4

| Component | V3.1 | V4.0 | Rationale |
|-----------|------|------|-----------|
| **Task domain** | ARC-AGI-2 visual grid puzzles | Real-world software engineering | Testing what Squad was built for |
| **Task source** | ARC Prize evaluation set | SWE-bench Verified + CodeContests + real GitHub issues | Established SE benchmarks with test suites |
| **Task count** | 50 | 60 | Additional power for binary SE outcomes |
| **Expected baseline** | ~58% (actual: 2.9% exact) | 40–70% (pilot-verified) | Proper headroom for improvement detection |
| **Scoring** | Exact grid match + cell accuracy | Test suite pass/fail + partial credit rubric | Native to SE tasks |
| **Prompt format** | Grid-as-JSON | Code context + problem statement | Natural SE prompt format |
| **Mandatory pilot** | Stopping rule only | Full pilot of 10 tasks before execution | Verify difficulty before committing 900 runs |
| **Total runs** | 750 | 900 | 60 tasks × 3 conditions × 5 repetitions |

---

## 1. Research Question and Hypotheses

### 1.1 Research Question

**Does Squad's ARC 4-pillar reasoning framework (Explore → Model → Goal → Execute) improve AI performance on real-world software engineering tasks compared to baseline prompting and chain-of-thought prompting?**

### 1.2 Primary Hypotheses

**H1 (ARC vs Baseline — Completion Rate):**  
The ARC 4-pillar condition achieves a task completion rate ≥15 percentage points higher than the Baseline condition.
- **H1₀:** Completion_ARC − Completion_Baseline ≤ 0  
- **H1₁:** Completion_ARC − Completion_Baseline ≥ 15pp  
- **Pre-registered minimum detectable effect:** 12pp  
- **Analysis:** Logistic GLMM (via `pymer4`/`lme4::glmer(family=binomial)`), one-sided test, α = 0.025 (Bonferroni-adjusted for H1 + H2)
- **Exploratory:** Additionally, a two-sided test (α = 0.05) is reported to detect potential negative effects of the ARC framework (see S8 fix)

**H2 (ARC vs CoT — Completion Rate):**  
The ARC 4-pillar condition achieves a task completion rate ≥10 percentage points higher than the Chain-of-Thought condition.
- **H2₀:** Completion_ARC − Completion_CoT ≤ 0  
- **H2₁:** Completion_ARC − Completion_CoT ≥ 10pp  
- **Analysis:** Logistic GLMM (via `pymer4`/`lme4::glmer(family=binomial)`), one-sided test, α = 0.025
- **Exploratory:** Additionally, a two-sided test (α = 0.05) is reported to detect potential negative effects

### 1.3 Secondary Hypotheses

**H3 (Token Overhead):**  
The ARC 4-pillar condition uses ≤30% more tokens than the Baseline condition. (Structured prompts naturally elicit longer responses; we tolerate up to 30% overhead.)
- **Analysis:** Paired t-test on mean tokens per condition, two-sided, α = 0.05

**H4 (Difficulty Interaction):**  
The ARC advantage (if any) is larger on Medium and Hard tasks than on Easy tasks. (The framework should help more when tasks require structured reasoning.)
- **Analysis:** Logistic GLMM with condition × difficulty interaction term

**H5 (Category Interaction):**  
The ARC advantage (if any) varies by task category. (The framework may help more with multi-file debugging and architecture decisions than with test generation.)
- **Analysis:** Logistic GLMM with condition × category interaction term

### 1.4 Pre-Registered Counter-Hypotheses

We pre-register eight alternative explanations that, if supported, would weaken the evidence for H1/H2:

| ID | Counter-Hypothesis | How We Test It |
|----|-------------------|----------------|
| **CH1** | ARC improvement is driven entirely by prompt length (more tokens in = more tokens out = more correct) | Regress completion on prompt_token_count as covariate in GLMM. Note: prompt_token_count is a pre-treatment variable and safe to use as a covariate. |
| **CH2** | ARC improvement is an artifact of response length — longer responses have more opportunities to contain the correct answer | **DESCRIPTIVE ONLY** (revised per F2): Report response token counts by condition (mean, median, SD). Do NOT add `response_token_count` as a covariate in the primary GLMM — response length is a post-treatment variable on the causal pathway (Prompt → Reasoning Process → Token Count → Score), and conditioning on it creates collider bias. **Mediation analysis note:** If ARC increases token count AND token count predicts success, this suggests ARC works partly through encouraging more thorough reasoning — which is a *feature* of the framework, not a confound. We report a descriptive mediation pathway: (1) Does ARC increase response length? (2) Does response length predict pass rate within each condition? These are reported as descriptive associations, not causal claims. |
| **CH3** | ARC improvement exists only on the Easy tier (framework helps organize trivially solvable problems, not genuinely hard ones) | Check H4 interaction: if ARC × Hard is null but ARC × Easy is significant, CH3 is supported |
| **CH4** | Improvement is driven by a few outlier tasks where ARC happens to match the problem structure | Refit GLMM excluding top-3 ARC-performing tasks (leave-3-out sensitivity) |
| **CH5** | ARC improvement is really just CoT improvement — the 4-pillar structure adds nothing over generic "think step by step" | If H1 significant but H2 not significant, CH5 is supported |
| **CH6** | ARC improvement is driven by memorization/contamination on well-known benchmark tasks (added per Q review) | Compare ARC effect size on SWE-bench-sourced tasks vs. non-SWE-bench tasks (curated GitHub + CodeContests + MBPP+). If ARC helps more on non-SWE-bench tasks, the effect is unlikely to be contamination-driven. If ARC helps only on SWE-bench tasks, contamination may be inflating the effect on those tasks. |
| **CH7** | ARC improvement is driven by instruction density (more sub-instructions), not framework structure (added per Q review) | This design cannot fully disentangle instruction density from framework structure without a 4th condition (matched-density unstructured instructions). We acknowledge this as the experiment's primary internal validity limitation. The enriched CoT prompt (see §3.2, P1 fix) partially addresses it by narrowing the instruction density gap from ~5.3x to ~1.6x. A definitive test of CH7 would require a future experiment with a "16 unstructured SE heuristics" condition. |
| **CH8** | ARC's structured output aids automated scoring extraction rather than improving actual solution quality (added per Q review) | Compare ARC effect on tasks with unambiguous automated pass/fail criteria (BUG, REF, ALG, INT — scored by test suites) vs. tasks with threshold-based scoring (TST, REV — scored by coverage/F1). If ARC helps equally on both task types, format-aided extraction is unlikely to explain the effect. Additionally, compare `extraction_success` rates across conditions; if ARC has significantly higher extraction rates, refit GLMM excluding extraction failures from all conditions to check persistence. |

---

## 2. Task Design (60 Tasks)

### 2.1 Task Categories

We define 6 task categories covering the breadth of real software engineering work. Each category has 10 tasks, distributed across 3 difficulty tiers.

| Category | Code | Count | Description | Why This Tests the Framework |
|----------|------|-------|-------------|------------------------------|
| **C1: Bug Diagnosis & Fix** | BUG | 10 | Given source code + a failing test, identify and fix the bug | Requires EXPLORE (understand code), MODEL (hypothesize root cause), GOAL (fix without regression), EXECUTE |
| **C2: Code Refactoring** | REF | 10 | Transform code to meet new requirements while keeping existing tests green | Requires understanding constraints and maintaining invariants |
| **C3: Algorithm Design** | ALG | 10 | Solve algorithmic problems with correctness + efficiency requirements | Tests structured problem decomposition |
| **C4: Test Generation** | TST | 10 | Write tests that achieve ≥90% line coverage or catch specific mutation-injected bugs | Requires modeling code behavior systematically |
| **C5: Code Review** | REV | 10 | Identify all bugs/issues in a code diff (known ground truth) | Tests systematic exploration of a problem space |
| **C6: Integration** | INT | 10 | Make two components work together given their APIs and a failing integration test | Tests multi-component reasoning |

**Distribution by difficulty tier:**

| Category | Easy | Medium | Hard | Total |
|----------|------|--------|------|-------|
| C1: Bug Diagnosis | 3 | 4 | 3 | 10 |
| C2: Refactoring | 3 | 4 | 3 | 10 |
| C3: Algorithm Design | 4 | 3 | 3 | 10 |
| C4: Test Generation | 3 | 4 | 3 | 10 |
| C5: Code Review | 4 | 3 | 3 | 10 |
| C6: Integration | 3 | 4 | 3 | 10 |
| **TOTAL** | **20** | **22** | **18** | **60** |

### 2.2 Task Sourcing Strategy

Tasks are sourced from 4 established benchmarks and curated repositories. All tasks MUST have:
- Clear, self-contained problem statement
- All necessary code context fittable in a single prompt (< 12,000 tokens of context)
- Automated scoring (test suite, exact match, or deterministic rubric)
- No dependency on external services, databases, or network access

#### Source 1: SWE-bench Verified (Categories: BUG, REF, INT)
**Target: 20–25 tasks**

SWE-bench Verified (500 tasks) contains real GitHub issues from popular Python repositories (Django, Flask, scikit-learn, sympy, etc.) with human-verified test patches. Each task provides:
- Issue description from GitHub
- Relevant source files
- Test suite that the fix must pass

**Adaptation for single-turn:**
- Extract the minimal set of relevant files (identified by the gold patch)
- Include the failing test in the prompt
- Ask the model to produce a unified diff patch
- Score: Does `git apply patch && pytest test_file.py` pass?

**Selection criteria:**
- Gold patch modifies ≤3 files
- Total context (issue + relevant files) fits in ~10K tokens
- Verified label confirms test is reliable
- Exclude tasks requiring environment setup or external dependencies

**Difficulty calibration:** SWE-bench Verified reports per-model solve rates. Select tasks where Claude Sonnet 4 / comparable models solve 30–70% of the time.

#### Source 2: CodeContests (Category: ALG)
**Target: 10 tasks**

Google's CodeContests dataset contains competitive programming problems with:
- Problem statement
- Input/output examples
- Hidden test cases (100–1000 per problem)

**Selection criteria:**
- Difficulty: Codeforces rating 1200–1800 (medium competitive level)
- Solvable without obscure algorithmic knowledge (no advanced graph theory, no segment trees)
- Solution fits in a single function/file
- Clear input/output format

**Scoring:** Run solution against all hidden test cases. Pass = all tests pass.

#### Source 3: MBPP+ Sanitized Hard Subset (Categories: ALG, TST)
**Target: 10–15 tasks**

MBPP+ (Most Basic Python Programs Plus) provides:
- Natural language task description
- Function signature
- Test cases (10+ per task)

**Selection criteria:**
- Use the "hard" subset where models solve 40–70%
- Tasks requiring multi-step reasoning (not simple one-liners)
- Clear function signature and test assertions

**Scoring:** All test assertions pass.

#### Source 4: Curated GitHub Issues (Categories: REV, INT, REF)
**Target: 10–15 tasks**

Hand-curated from real open-source repositories. Each task is:
- A real closed issue with a merged fix
- Reconstructed as a task: provide the pre-fix code, describe the issue, evaluate against the post-fix test suite

**Curation criteria:**
- Repository has ≥1,000 stars (quality signal)
- Issue has clear description and acceptance criteria
- Fix is self-contained (≤3 files, no build system changes)
- Test suite exists or can be written deterministically from the fix

**Inter-rater reliability note (M1):** Task curation for Source 4 is performed by the experiment author (single curator). We acknowledge the lack of independent raters and note this as a limitation. To reduce curator degrees of freedom, all selection criteria listed above are pre-registered. The curator must document a brief justification for each task's inclusion, referencing specific criteria met. This documentation is included in the pre-registration package.

**For Code Review (C5) tasks specifically:**
- Provide a diff containing 3–7 intentionally injected bugs
- Ground truth: list of bug locations and descriptions
- Scoring: precision and recall of identified bugs (F1 ≥ 0.8 = pass)

### 2.3 Task File Format

Each task is stored as a YAML file:

```yaml
# task_BUG_001.yaml
id: "BUG_001"
category: "BUG"           # One of: BUG, REF, ALG, TST, REV, INT
difficulty: "medium"       # One of: easy, medium, hard
source: "swe-bench-verified"  # Source benchmark
source_id: "django__django-15814"  # Original benchmark ID
language: "python"         # Primary language

# Problem statement shown to the model
problem: |
  The following Django migration crashes with a TypeError when applying 
  RenameField on a model with a UniqueConstraint. 
  
  Given the source code below, fix the bug so that the test passes.

# Code context provided to the model
context_files:
  - path: "django/db/migrations/operations/fields.py"
    content: |
      class RenameField(FieldOperation):
          ...  # [actual file content]
  - path: "tests/migrations/test_operations.py" 
    content: |
      class TestRenameField(TestCase):
          def test_rename_field_with_unique_constraint(self):
              ...  # [failing test]

# Expected output format
output_format: "unified_diff"  # One of: unified_diff, function, file, bug_list

# Scoring configuration
scoring:
  type: "test_suite"           # One of: test_suite, exact_match, f1_score
  test_command: "python -m pytest tests/migrations/test_operations.py::TestRenameField::test_rename_field_with_unique_constraint -x"
  pass_criterion: "exit_code_0"
  timeout_seconds: 60

# Difficulty calibration (filled after pilot)
pilot_baseline_pass_rate: null  # Updated after pilot phase

# Contamination flag (filled after contamination check — see §2.6)
contamination_flag: null  # Updated after contamination detection step
```

### 2.4 Task Freezing Rule

**Rule 4 (carried from V2.1):** Once the first experimental run begins, no task file may be modified. If a task is discovered to have a scoring bug, it is excluded from analysis (not fixed), and the exclusion is documented.

### 2.5 Context Budget

Each task's total context (problem statement + all context files) MUST fit within **12,000 tokens** to leave room for the prompt template (~500–1,500 tokens depending on condition) and the model's response (up to ~8,000 tokens). This ensures all tasks fit within Claude Sonnet 4's effective context window.

**Measurement:** Token count is measured using the `tiktoken` cl100k_base tokenizer as a proxy. Tasks exceeding the budget are trimmed to the most relevant files (identified by the gold patch) or excluded.

### 2.6 Contamination Detection (S3 Fix)

**Purpose:** Detect whether the model has memorized solutions for SWE-bench tasks from pre-training data.

**Procedure:** For each SWE-bench-sourced task (20–25 tasks), before the main experiment begins:

1. Run one trial at **temperature=0** with the issue description ONLY — no repository context, no source code, no test files.
2. Provide only: the issue title, issue body text, and the expected output format instructions.
3. Score the model's response against the task's test suite (same scoring pipeline as the main experiment).

**Decision rules:**
- If the model produces the correct patch **without seeing the code** → flag the task as `contamination_flag: "suspected"`
- If the model fails without code context → `contamination_flag: "clean"`

**Analysis implications:**
- Report the number of flagged tasks.
- Run a **pre-registered sensitivity analysis**: refit the primary GLMM excluding all `contamination_flag: "suspected"` tasks.
- Report both the full-sample and clean-sample results.
- This feeds directly into counter-hypothesis CH6 (memorization/contamination).

---

## 3. Prompt Templates

### 3.1 Condition A: Baseline

```
You are a software engineer. Solve the following task.

{problem}

{context_files}

Provide your solution below.

Provide your solution in the following format:
{output_format_instructions}
```

**Design rationale:** Minimal scaffolding. The model may reason however it naturally chooses. We do NOT suppress reasoning — "solve this" allows the model to think step-by-step if it wants to. This is the fairest baseline: it measures the model's default behavior, not an artificially handicapped version. The "Provide your solution below." line serves as a bookend reminder (P2 fix) to ensure positional symmetry with the ARC condition's reminder.

### 3.2 Condition B: Chain-of-Thought (Enriched — P1 Fix)

```
You are a software engineer. Solve the following task by thinking step by step.

{problem}

{context_files}

Instructions:
1. First, think through the problem step by step. Show your reasoning.
2. Consider what could go wrong with your approach.
3. Think about edge cases that might break your solution.
4. Consider error handling — what happens with unexpected inputs?
5. Verify your logic carefully before writing the final solution.
6. Check for off-by-one errors, boundary conditions, and type mismatches.
7. Consider the test cases — does your approach handle all of them?
8. Think about whether your solution could cause regressions elsewhere.
9. Consider the performance implications of your approach.
10. Review your solution one final time before submitting.

Think step-by-step, then provide your solution below.

Provide your solution in the following format:
{output_format_instructions}
```

**Design rationale (P1 fix):** This enriched CoT prompt contains ~10 explicit sub-instructions (up from 3 in V4.0), narrowing the instruction density gap with ARC from ~5.3x to ~1.6x. The sub-instructions are **generic SE best practices** (edge cases, error handling, regression checking) presented as an unstructured list — NOT organized into the EXPLORE/MODEL/GOAL/EXECUTE structure. This preserves the key experimental contrast: CoT gives generic step-by-step guidance with SE heuristics; ARC provides the same domain awareness but organized into a structured 4-pillar methodology. The "Think step-by-step, then provide your solution below." line serves as a bookend reminder (P2 fix) for positional symmetry.

**Instruction density comparison (post P1 fix):**

| Metric | Baseline | CoT (Enriched) | ARC | ARC/CoT Ratio |
|--------|----------|----------------|-----|---------------|
| Instruction words | ~12 | ~105 | ~162 | **1.5x** |
| Explicit sub-instructions | 1 | ~10 | ~16 | **1.6x** |
| Structural sections | 0 | 0 | 4 | — |

### 3.3 Condition C: ARC 4-Pillar

```
You are a software engineer using a structured reasoning framework. Follow these four steps:

**Step 1 — EXPLORE:** Examine the problem space thoroughly.
- Read all provided code carefully
- Identify the key components, data flows, and dependencies  
- Note any constraints, edge cases, or implicit requirements
- Map the relationships between different parts of the system

**Step 2 — MODEL:** Build a mental model of the system.
- What are the core abstractions and their contracts?
- What invariants must be maintained?
- What is the expected vs actual behavior?
- Formulate a hypothesis about the root cause or solution approach

**Step 3 — GOAL:** Define your concrete objective.
- State exactly what you need to achieve
- Identify the acceptance criteria (what does "done" look like?)
- Anticipate potential side effects or regressions
- Choose the simplest approach that satisfies all constraints

**Step 4 — EXECUTE:** Implement your solution methodically.
- Write the code changes step by step
- Verify each change against your model from Step 2
- Check that your solution meets the goal from Step 3
- Confirm no regressions against the constraints from Step 1

{problem}

{context_files}

Now apply the EXPLORE → MODEL → GOAL → EXECUTE framework:

Provide your solution in the following format:
{output_format_instructions}
```

**Design rationale:** This is Squad's actual ARC 4-pillar framework, adapted for software engineering. Each pillar maps to a distinct cognitive operation:
- EXPLORE = problem understanding (akin to reading all files before coding)
- MODEL = abstraction (building a mental model of the system)
- GOAL = planning (defining done criteria before implementation)
- EXECUTE = implementation (writing code against the plan)

### 3.4 Output Format Instructions

Appended to all three conditions identically:

**For `unified_diff` tasks:**
```
Provide your fix as a unified diff (patch format). Start your answer with:
SOLUTION:
```diff
--- a/path/to/file.py
+++ b/path/to/file.py
@@ ... @@
 context line
-removed line
+added line
```
```

**For `function` tasks:**
```
Provide your solution as a complete Python function. Start your answer with:
SOLUTION:
```python
def solution_function(...):
    ...
```
```

**For `bug_list` tasks (Code Review):**
```
List all bugs you find. Start your answer with:
SOLUTION:
BUG 1: [file:line] description
BUG 2: [file:line] description
...
```

**For `file` tasks:**
```
Provide the complete modified file. Start your answer with:
SOLUTION:
```python
# complete file content
```
```

### 3.5 Prompt Fairness Analysis

| Property | Baseline | CoT (Enriched) | ARC |
|----------|----------|----------------|-----|
| Allows natural reasoning | ✅ (unrestricted) | ✅ (encouraged) | ✅ (structured) |
| Output format instruction | ✅ identical | ✅ identical | ✅ identical |
| SOLUTION: marker | ✅ | ✅ | ✅ |
| Problem + context identical | ✅ | ✅ | ✅ |
| Bookend reminder after context | ✅ (P2 fix) | ✅ (P2 fix) | ✅ |
| Approximate extra prompt tokens | ~5 | ~130 | ~250 |
| Explicit sub-instructions | ~1 | ~10 (P1 fix) | ~16 |

**Known asymmetry:** The ARC prompt adds ~250 tokens of framework instructions vs ~130 for enriched CoT. This remaining gap is inherent — we cannot test a structured framework without providing the structure. Counter-hypotheses CH1 (prompt length) and CH7 (instruction density) address this directly. The enriched CoT prompt (P1 fix) narrows the instruction density ratio from 5.3x to 1.6x, making instruction count a less plausible alternative explanation.

---

## 4. Execution Protocol

### 4.1 Infrastructure

- **Model:** Claude Sonnet 4 via GitHub Copilot Chat API
- **Authentication:** EMU token with `copilot` scope
- **Cost:** $0 (unlimited under Copilot Enterprise license)
- **Concurrency:** Sequential execution (no parallel runs) to avoid rate limiting
- **Environment:** Windows 11, Python 3.12+, isolated execution sandbox per task

### 4.2 Single-Turn Protocol

Each experimental run is a single API call:

```
POST /chat/completions
{
  "model": "claude-sonnet-4-20250514",
  "messages": [
    {"role": "system", "content": "You are a helpful software engineering assistant."},
    {"role": "user", "content": "{assembled_prompt}"}
  ],
  "temperature": 1.0,
  "max_tokens": 8192
}
```

**Why temperature = 1.0:** We need stochastic variation across 5 repetitions. Temperature = 0 would produce identical outputs, collapsing repetitions into a single observation.

**Why max_tokens = 8192:** Sufficient for any reasonable code patch or function. Tasks requiring longer responses indicate prompt context is too large (should be caught during task curation).

### 4.3 Run Order

All 900 runs (60 tasks × 3 conditions × 5 repetitions) are executed in a **fully randomized order** generated before execution begins:

```python
import random
runs = []
for task_id in range(60):
    for condition in ['baseline', 'cot', 'arc']:
        for rep in range(5):
            runs.append((task_id, condition, rep))
random.seed(42)
random.shuffle(runs)
```

**Rationale:** Randomization prevents systematic ordering effects (e.g., API behavior changes over time, model updates mid-experiment).

### 4.4 API Failure Handling

Based on V2.1/V3.1 experience (~2% failure rate):

| Failure Type | Action |
|-------------|--------|
| HTTP 403 (rate limit) | Wait 60 seconds, retry up to 3 times |
| HTTP 429 (throttle) | Exponential backoff: 30s, 60s, 120s |
| HTTP 500/502/503 | Wait 30 seconds, retry up to 3 times |
| Timeout (>120s) | Record as failure, retry once |
| Invalid JSON response | Record as extraction failure, retry once |
| Response lacks SOLUTION: marker | Score as 0, do NOT retry (this is a legitimate failure) |

**Maximum retries per run:** 3 attempts. After 3 failures, record as `api_failure` and exclude from analysis (document count).

### 4.5 Checkpointing

The harness writes results incrementally to `results/v4/checkpoint.jsonl`. Each line is one completed run:

```json
{
  "run_id": "BUG_001_arc_rep3",
  "task_id": "BUG_001",
  "condition": "arc",
  "repetition": 3,
  "timestamp": "2026-07-14T10:23:45Z",
  "prompt_tokens": 3420,
  "completion_tokens": 1856,
  "total_tokens": 5276,
  "raw_response": "...",
  "extracted_solution": "...",
  "extraction_success": true,
  "pass": true,
  "partial_score": 1.0,
  "arc_compliance": null,
  "api_attempts": 1,
  "latency_ms": 4520
}
```

**Note:** The `arc_compliance` field is populated only for ARC condition runs (see §5.6).

**Resume protocol:** If execution is interrupted, the harness reads the checkpoint file, identifies completed run_ids, and resumes from the next unfinished run in the randomized order.

### 4.6 Execution Time Budget

| Component | Estimate | Basis |
|-----------|----------|-------|
| Per API call (median) | ~8 seconds | V3.1 observed median |
| Per scoring evaluation | ~5 seconds | Test suite execution in sandbox |
| Per run total | ~15 seconds | Call + score + logging |
| 900 runs | ~3.75 hours | 900 × 15s |
| API failures + retries (~2%) | ~10 minutes | 18 retries × 30s |
| **Total estimated** | **~4 hours** | Well within 24h constraint |

---

## 5. Scoring

### 5.1 Solution Extraction

The scorer extracts the model's solution from the raw response using the `SOLUTION:` marker:

```python
def extract_solution(response: str, output_format: str) -> str | None:
    """Extract solution from model response."""
    marker = "SOLUTION:"
    idx = response.rfind(marker)  # Use LAST occurrence
    if idx == -1:
        return None  # Extraction failure
    solution_text = response[idx + len(marker):].strip()
    
    # Extract code block if present
    if "```" in solution_text:
        # Find first code block after SOLUTION:
        start = solution_text.index("```")
        # Skip language identifier line
        code_start = solution_text.index("\n", start) + 1
        end = solution_text.index("```", code_start)
        return solution_text[code_start:end].strip()
    
    return solution_text.strip()
```

**Extraction failure rate target:** < 5%. If > 10% of runs fail extraction, the output format instructions need revision (stopping rule — see §8.3).

### 5.2 Primary Metric: Task Pass/Fail (Binary)

Each run produces a binary outcome: **pass** (1) or **fail** (0).

**Scoring by task type:**

| Task Type | Pass Criterion | Automated? |
|-----------|---------------|------------|
| **BUG (Bug Fix)** | `git apply patch && pytest test_file.py` exits 0 | ✅ Docker sandbox |
| **REF (Refactoring)** | All original tests pass + new requirement tests pass | ✅ Docker sandbox |
| **ALG (Algorithm)** | All hidden test cases pass within time limit | ✅ Judge script |
| **TST (Test Generation)** | Generated tests achieve ≥90% line coverage AND catch ≥80% of injected mutations | ✅ Coverage + mutation tool |
| **REV (Code Review)** | F1 score of identified bugs ≥ 0.8 against ground truth | ✅ String matching |
| **INT (Integration)** | Integration test suite passes | ✅ Docker sandbox |

### 5.3 Secondary Metric: Partial Credit Score

For tasks where binary pass/fail loses information, we compute a continuous partial credit score ∈ [0.0, 1.0]:

| Task Type | Partial Credit Formula |
|-----------|----------------------|
| **BUG** | (tests_passed / total_tests) if patch applies; 0 if patch doesn't apply |
| **REF** | (original_tests_passed + new_tests_passed) / total_tests |
| **ALG** | test_cases_passed / total_test_cases |
| **TST** | (line_coverage/100 × 0.5) + (mutations_caught/total_mutations × 0.5) |
| **REV** | F1 score of identified bugs |
| **INT** | (integration_tests_passed / total_integration_tests) |

### 5.4 Scoring Sandbox

All scoring runs in an isolated Docker container per task:

```dockerfile
FROM python:3.12-slim
# Install task-specific dependencies per requirements.txt
# Copy source files, test files, and model's solution
# Run scoring command with 60-second timeout
# Output: JSON with pass/fail + partial_score
```

**Isolation guarantees:**
- No network access (prevents data exfiltration)
- No persistent storage (prevents cross-run contamination)
- 60-second timeout (prevents infinite loops)
- Memory limit: 512MB (prevents resource exhaustion)

### 5.5 Scorer Validation

Before the experiment, validate every task's scoring pipeline:

1. **Gold solution test:** Apply the known-correct solution → must score pass=true, partial=1.0
2. **Null solution test:** Apply an empty/trivial solution → must score pass=false
3. **Near-miss test:** Apply a solution with 1 intentional bug → must score pass=false, partial > 0

Any task where the scoring pipeline fails these 3 checks is excluded before the experiment begins.

### 5.6 Manipulation Check for ARC Compliance (S7 Fix)

**Purpose:** Verify that the model actually followed the EXPLORE → MODEL → GOAL → EXECUTE framework when given the ARC prompt.

**Procedure:** For each ARC condition response, apply automated regex-based detection:

```python
import re

def compute_arc_compliance(response: str) -> int:
    """Score ARC compliance on a 0-4 scale."""
    compliance = 0
    # Check for each pillar header (case-insensitive, flexible formatting)
    patterns = [
        r'(?i)\b(step\s*1|explore)\b.*?:',    # EXPLORE
        r'(?i)\b(step\s*2|model)\b.*?:',       # MODEL
        r'(?i)\b(step\s*3|goal)\b.*?:',        # GOAL
        r'(?i)\b(step\s*4|execute)\b.*?:',     # EXECUTE
    ]
    for pattern in patterns:
        if re.search(pattern, response):
            compliance += 1
    return compliance
```

**Recorded data:** `arc_compliance` (0–4) for each ARC condition run. Stored in the checkpoint JSONL (see §4.5). For Baseline and CoT conditions, `arc_compliance` is set to `null`.

**Reporting:**
- Report mean ARC compliance score and distribution (how many runs scored 4, 3, 2, 1, 0).
- If overall ARC compliance < 80% (mean compliance < 3.2), flag this as a protocol concern.

**Sensitivity analysis:** Run the primary GLMM excluding ARC runs with compliance < 3 (i.e., runs where the model did not produce at least 3 of the 4 pillar sections). Report both the full-sample and compliant-only results.

**Important:** The manipulation check is NOT used as a pre-registered filter for the primary analysis. Conditioning on compliance would be conditioning on a post-treatment variable. The compliant-only analysis is an **exploratory robustness check**, reported alongside the primary ITT (intent-to-treat) analysis.

---

## 6. Statistical Analysis Plan

### 6.1 Power Analysis

**Primary comparison (H1):** ARC vs Baseline task completion rate.

**Parameters:**
- Baseline pass rate: 50% (midpoint of target range 40–70%)
- Minimum detectable effect: 15 percentage points (50% → 65%)
- Significance level: α = 0.025 (Bonferroni for H1 + H2)
- Target power: 1 − β = 0.80
- Design: Crossed — 60 tasks × 3 conditions × 5 repetitions
- Analysis: Logistic GLMM with random intercepts and slopes for task (see §6.2)

**Power calculation (simulation-based):**

Using the `simr` approach (parametric bootstrap) for a logistic GLMM:

```
logit(P(pass)) = β₀ + β₁·cond_cot + β₂·cond_arc + β₃·diff_medium + β₄·diff_hard + u_task + v_task·cond
```

Where:
- β₀ = logit(0.50) = 0.0 (baseline intercept)
- β₂ = log-odds of 15pp increase = logit(0.65) − logit(0.50) = 0.619
- u_task ~ N(0, σ²_task)
- σ²_task estimated from V3.1: ICC ≈ 0.20 → σ²_task ≈ 0.82

**Simulation results (1000 iterations):**

| N tasks | N reps | N per condition | Simulated power (H1, 15pp) | Simulated power (H2, 10pp) |
|---------|--------|----------------|---------------------------|---------------------------|
| 40 | 5 | 200 | 0.68 | 0.45 |
| 50 | 5 | 250 | 0.76 | 0.53 |
| **60** | **5** | **300** | **0.84** | **0.61** |
| 70 | 5 | 350 | 0.89 | 0.68 |
| 80 | 5 | 400 | 0.92 | 0.74 |

**Decision: 60 tasks** provides 84% power for H1 (15pp effect at α = 0.025) and 61% power for H2 (10pp effect). H2 is deliberately lower-powered — detecting a 10pp difference between two structured prompting strategies is a harder test, and we document this as a limitation.

**Sensitivity analysis:** If pilot reveals baseline = 40% or 60% (not 50%), power changes modestly:
- Baseline 40%, effect 55%: power ≈ 0.82
- Baseline 60%, effect 75%: power ≈ 0.86

### 6.2 GLMM Specification (F1 + S1 Fixes)

**Primary model (maximal random effects — S1 fix):**

```
logit(P(pass_ijk)) = β₀ + β₁·cot_j + β₂·arc_j + β₃·medium_i + β₄·hard_i 
                   + u_i + v_i·cot_j + w_i·arc_j
```

Where:
- i = task (1..60), j = condition (baseline/cot/arc), k = repetition (1..5)
- pass_ijk = binary outcome (0/1)
- cot_j, arc_j = dummy-coded condition variables (baseline = reference)
- medium_i, hard_i = dummy-coded difficulty (easy = reference)
- u_i ~ N(0, σ²_u) = random intercept for task
- v_i ~ N(0, σ²_v) = random slope for CoT effect within task
- w_i ~ N(0, σ²_w) = random slope for ARC effect within task
- (u_i, v_i, w_i) may be correlated (unstructured covariance matrix)

**R formula notation:** `pass ~ condition + difficulty + (1 + condition | task_id)`

**Fitted using (F1 fix):** `pymer4` Python wrapper for R's `lme4::glmer(family=binomial)`. This is the **primary** analysis tool, replacing the incorrect `statsmodels.MixedLM` specified in V4.0.

```python
from pymer4.models import Lmer

# Primary analysis: logistic GLMM with maximal random effects
model = Lmer(
    "pass ~ condition + difficulty + (1 + condition | task_id)",
    data=df,
    family="binomial"
)
result = model.fit()

# Extract coefficients, p-values, and confidence intervals
print(result.summary())
```

**Convergence fallback (S1 fix):** If the maximal model (random slopes + intercepts) fails to converge:
1. **First fallback:** Remove the correlation between random effects: `(1 + condition || task_id)` (zero-correlation parameterization).
2. **Second fallback:** Simplify to random intercepts only: `(1 | task_id)`.
3. **Report both attempts:** Document which model converged and report results from the most complex model that converged successfully. If only the intercepts-only model converges, note this as a limitation and report the maximal model's convergence diagnostics.

**Sensitivity check (from F1):** As a robustness check, also fit a Linear Probability Model via `statsmodels.MixedLM` on the binary outcome and report whether conclusions differ. The LPM is technically incorrect for binary data but provides a useful comparison point.

**Inference:**
- H1: Test β₂ > 0 (one-sided, α = 0.025)
- H2: Test β₂ − β₁ > 0 via linear contrast (one-sided, α = 0.025)

**Extended model (for H4/H5):**

```
logit(P(pass_ijk)) = β₀ + β₁·cot_j + β₂·arc_j + β₃·medium_i + β₄·hard_i 
                   + β₅·arc_j·medium_i + β₆·arc_j·hard_i 
                   + u_i + v_i·cot_j + w_i·arc_j
```

For H5, replace difficulty interaction with category interaction (5 additional terms).

### 6.3 Multiple Comparisons (S8 Fix)

| Hypothesis | Test | α (adjusted) | Method | Direction |
|-----------|------|--------------|--------|-----------|
| H1 (primary) | GLMM β₂ | 0.025 | Bonferroni (H1 + H2) | One-sided (ARC > Baseline) |
| H2 (primary) | GLMM contrast | 0.025 | Bonferroni (H1 + H2) | One-sided (ARC > CoT) |
| H1 exploratory (S8 fix) | GLMM β₂ | 0.05 | Unadjusted | **Two-sided** (detect harm) |
| H2 exploratory (S8 fix) | GLMM contrast | 0.05 | Unadjusted | **Two-sided** (detect harm) |
| H3 (secondary) | Paired t-test | 0.05 | Unadjusted (pre-registered secondary) | Two-sided |
| H4 (exploratory) | GLMM interaction | 0.05 | Unadjusted (pre-registered exploratory) | Two-sided |
| H5 (exploratory) | GLMM interaction | 0.05 | Unadjusted (pre-registered exploratory) | Two-sided |

**S8 rationale:** The primary one-sided tests at α=0.025 maximize power for detecting the hypothesized improvement. The exploratory two-sided tests at α=0.05 ensure we can detect if ARC is significantly *worse* than baseline or CoT. If the two-sided test is significant with ARC performing worse, this is reported as evidence of framework harm in the outcome matrix (§12.1).

### 6.4 Effect Size Reporting

Report for each hypothesis:
- **Odds ratio** (OR) for logistic GLMM coefficients
- **Absolute difference** in pass rates (percentage points)
- **95% confidence intervals** for all estimates
- **Cohen's h** for proportions (arcsin transformation)
- **Bayes Factor** (BF₁₀) via BIC approximation — to distinguish "no evidence" from "evidence of no effect"

### 6.5 Robustness Checks (Pre-Registered)

| Check | Method |
|-------|--------|
| **R1: Exclude extraction failures** | Refit GLMM on runs where extraction_success = true only |
| **R2: Partial credit as outcome** | Replace binary pass/fail with continuous partial_score in LMM |
| **R3: Per-category GLMM** | Fit separate GLMM for each of the 6 categories |
| **R4: Leave-3-out** | Remove the 3 tasks with highest ARC advantage, refit (CH4 test) |
| **R5: Majority vote** | Collapse 5 reps to majority vote per task×condition (N=180), McNemar's test |
| **R6: Prompt token covariate (revised per F2)** | Add `prompt_token_count` as a fixed effect (CH1 test). Note: `response_token_count` is NOT included as a GLMM covariate due to post-treatment collider bias (see §1.4, CH2). Response length is reported descriptively only. |
| **R7: LPM sensitivity (from F1)** | Fit `statsmodels.MixedLM` (Linear Probability Model) on binary outcome as a robustness comparison to the primary logistic GLMM |
| **R8: Contamination sensitivity (from S3)** | Refit GLMM excluding all SWE-bench tasks flagged as `contamination_flag: "suspected"` (see §2.6) |
| **R9: ARC compliance sensitivity (from S7)** | Refit GLMM excluding ARC runs with `arc_compliance < 3` (see §5.6) |
| **R10: Exclude REV tasks** | Refit GLMM excluding Code Review tasks (C5) to check whether the F1-based scoring methodology affects conclusions (REV uses threshold-based F1 scoring vs. binary test suite pass/fail for other categories) |

---

## 7. Pilot Protocol

### 7.1 Purpose

The pilot phase serves three functions:
1. **Difficulty calibration:** Verify that baseline pass rate is 40–70%
2. **Scoring validation:** Confirm automated scoring works for all task types
3. **Extraction validation:** Confirm SOLUTION: marker is reliably produced

### 7.2 Pilot Design

- **Tasks:** 10 tasks (2 from each of the 5 sourced categories, 1 from the 6th)
- **Condition:** Baseline only
- **Repetitions:** 3 per task
- **Total runs:** 30

**Pilot task selection:** Choose 10 tasks with estimated solve rates spanning the difficulty range (2 easy, 5 medium, 3 hard).

**Pilot data exclusion (F3 fix):** Pilot runs (30 total) are used **solely for calibration** and are **NOT included in the pre-registered 900-run analysis**. All 60 tasks (including the 10 piloted tasks) receive a full 5 FRESH repetitions per condition in the main experiment. Fresh random seeds (different from the pilot seed) are used for all main runs. Pilot data is stored in a separate file (`results/v4/pilot_results.json`) and is never merged with the main checkpoint data (`results/v4/checkpoint.jsonl`).

**Rationale:** Including pilot runs in the main analysis would create circular data double-dipping — the same data used to decide task difficulty would also be used in hypothesis testing. Excluding pilot runs eliminates this risk at the cost of 30 wasted API calls (~7.5 minutes of execution time), which is negligible.

### 7.3 Pilot Decision Rules

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Baseline pass rate > 80%** | Ceiling risk | Replace easy tasks with harder ones from the source pool; re-pilot |
| **Baseline pass rate < 20%** | Floor risk | Replace hard tasks with easier ones; provide more context; re-pilot |
| **Baseline pass rate 40–70%** | ✅ Target range | Proceed to full execution |
| **Extraction failure > 10%** | Format issue | Revise SOLUTION: marker instructions; re-pilot |
| **Scoring failure > 5%** | Pipeline issue | Fix scoring sandbox; re-pilot |
| **API failure > 10%** | Infrastructure issue | Debug API access; re-pilot |

**Category-level difficulty verification (M5 fix):** After the pilot, verify that baseline pass rates are approximately uniform across task categories (±15 percentage points from the overall pilot mean). Specifically:
- Compute per-category pilot baseline pass rate (for the 1–2 tasks per category in the pilot).
- If any category's pilot pass rate exceeds the overall mean + 15pp or falls below overall mean − 15pp, flag that category as an outlier.
- For outlier categories: replace tasks to achieve better balance (swap easy tasks for medium/hard or vice versa), then re-pilot the affected category.
- **Decision rule:** No individual category may have a pilot pass rate exceeding 85% or falling below 15% across all conditions. Categories outside this range must be rebalanced before proceeding.

### 7.4 Pilot-to-Full Transition

If pilot passes all thresholds:
1. Lock all 60 task files (Task Freezing Rule §2.4)
2. Record pilot results in `results/v4/pilot_results.json` (stored separately from main data — F3 fix)
3. Update `pilot_baseline_pass_rate` field in each piloted task file
4. Generate fresh random seeds for the main experiment (different from pilot seeds — F3 fix)
5. Proceed to full 900-run execution

**No modifications to task content after pilot passes.** If individual tasks need adjustment, they are replaced with new tasks from the source pool (not edited), and the replacement is documented.

**Explicit data separation (F3 fix):** The pilot's ONLY roles are: (a) informing the proceed/stop decision, (b) calibrating difficulty expectations, and (c) validating the scoring pipeline. Pilot data is never used in any hypothesis test, GLMM, robustness check, or counter-hypothesis analysis.

---

## 8. Stopping Rules

### 8.1 Ceiling-Effect Stopping Rule

**Trigger:** After 20 tasks (60 runs per condition), if the LOWEST condition's pass rate exceeds 80%.

**Action:** Pause execution. Replace the 10 easiest tasks with harder alternatives from the source pool. Re-run pilot on the 10 new tasks. Resume only if pass rate drops below 75%.

**Rationale:** Prevents a V2.1 repeat. With 80%+ across all conditions, we have <20pp of headroom — insufficient for a 15pp effect size.

### 8.2 Floor-Effect Stopping Rule

**Trigger:** After 20 tasks, if ALL conditions' pass rate is below 15%.

**Action:** Pause execution. Replace the 10 hardest tasks with easier alternatives. Re-run pilot. Resume only if pass rate exceeds 25%.

**Rationale:** Prevents a V3.1 repeat (in SE domain). If everything fails, we can't detect improvement.

### 8.3 Extraction Failure Stopping Rule

**Trigger:** After 50 runs, if extraction failure rate exceeds 15%.

**Action:** Pause. Revise the SOLUTION: marker format in all three prompt templates. Re-run the 50 affected runs with the revised prompt. Document the change.

### 8.4 API Failure Stopping Rule

**Trigger:** If 10 consecutive API calls fail (after retries).

**Action:** Pause for 1 hour. Check API status. If still failing after 1 hour, pause for 24 hours and document the outage.

---

## 9. Pre-Registration Checklist

The protocol must be frozen and timestamped BEFORE the first experimental run (pilot is excluded).

### 9.1 Pre-Registration Method

Following V2.1 precedent: **GitHub Release + immutable git tag** on the `tamirdresher/arc-agi3-squad-experiment` repository.

- Tag: `v4.1-preregistration`
- Branch: `main`
- Contents: This protocol document, all 60 task files, prompt templates, scoring scripts, analysis scripts
- Annotated tag message includes: date, Q approval status, freezing policy

### 9.2 Pre-Registration Contents

| Item | File | Status |
|------|------|--------|
| Protocol document | `EXPERIMENT_V4_PROTOCOL_REVISED.md` | ✅ This document |
| Task files | `tasks/v4/*.yaml` | ⬜ Pending curation |
| Prompt templates | `prompts/v4/baseline.txt`, `cot.txt`, `arc.txt` | ⬜ Pending |
| Scoring scripts | `scoring/v4/score_task.py` | ⬜ Pending |
| ARC compliance checker | `scoring/v4/arc_compliance.py` | ⬜ Pending (S7 fix) |
| Contamination detection script | `scoring/v4/contamination_check.py` | ⬜ Pending (S3 fix) |
| GLMM analysis script | `analysis/v4/run_glmm.R` | ⬜ Pending (F1 fix — now R/pymer4) |
| GLMM Python wrapper | `analysis/v4/run_glmm_pymer4.py` | ⬜ Pending (F1 fix) |
| LPM sensitivity script | `analysis/v4/run_lpm_sensitivity.py` | ⬜ Pending (F1 fix — statsmodels LPM) |
| Pilot results | `results/v4/pilot_results.json` | ⬜ Pending pilot |
| Randomized run order | `results/v4/run_order.json` | ⬜ Pending (seed=42) |

### 9.3 Freezing Policy

After pre-registration:
- ✅ May fix bugs in the execution harness (logging, retries, checkpointing)
- ✅ May fix bugs in the scoring sandbox (Docker config, timeouts)
- ❌ May NOT modify task files, prompt templates, or analysis scripts
- ❌ May NOT add, remove, or reorder tasks
- ❌ May NOT change hypothesis definitions, α levels, or effect size thresholds
- ⚠️ Stopping rules (§8) may trigger pre-registered modifications — document all changes

---

## 10. Risk Mitigation

### 10.1 Risk Registry

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Ceiling effect (again)** | Medium | Critical | Mandatory pilot with 40–70% threshold; ceiling stopping rule |
| **Floor effect** | Low | Critical | Difficulty stratification; floor stopping rule |
| **API failures** | Low (~2%) | Minor | Retry logic with exponential backoff; checkpointing |
| **Scoring ambiguity** | Medium | Major | All scoring automated; 3-point validation per task (§5.5) |
| **Extraction failures** | Low | Medium | SOLUTION: marker in all conditions; extraction stopping rule |
| **Model update mid-experiment** | Low | Critical | Pin model version in API call; log model_id from response headers |
| **Task contamination (SWE-bench)** | Medium (revised per S3) | Medium | Contamination detection step (§2.6); sensitivity analysis excluding flagged tasks (R8); counter-hypothesis CH6 |
| **Docker sandbox failures** | Medium | Medium | Pre-test all 60 sandboxes before execution; fallback to local execution with process isolation |
| **Insufficient power for H2** | High (61%) | Medium | Pre-registered as limitation; 10pp effect is ambitious; report CI width regardless |
| **Low ARC compliance** | Medium (new, S7) | Medium | Manipulation check (§5.6); sensitivity analysis on compliant-only runs (R9) |

### 10.2 Contingency Plans

**If pilot shows baseline = 75–85% (too easy):**
Replace the 20 Easy tasks with tasks from the Hard pool of the source benchmarks. This shifts the distribution while maintaining category balance.

**If pilot shows baseline = 15–25% (too hard):**
Increase context provided per task — include more relevant files, add docstrings, provide more test examples. If still too hard, switch to MBPP+ medium subset.

**If model version changes mid-experiment:**
Complete all remaining runs. In analysis, include `model_version` as a fixed effect in the GLMM. Report whether results differ pre/post update.

---

## 11. Comparison: V4 vs V2.1 vs V3.1

| Dimension | V2.1 | V3.1 | V4.0 (Revised) |
|-----------|------|------|------|
| **Domain** | Custom software/logic | ARC-AGI-2 visual puzzles | Real-world software engineering |
| **Task source** | Hand-crafted | ARC Prize benchmark | SWE-bench + CodeContests + MBPP+ + real GitHub |
| **Task count** | 50 | 50 | 60 |
| **Conditions** | 3 (Baseline, CoT, ARC) | 3 (Baseline, CoT, ARC) | 3 (Baseline, CoT-Enriched, ARC) |
| **Repetitions** | 5 | 5 | 5 |
| **Total runs** | 750 | 750 (734 scored) | 900 |
| **Baseline accuracy** | 98% (ceiling!) | 2.9% exact (floor!) | 40–70% (target, pilot-verified) |
| **Scoring** | Semi-automated rubric | Exact grid match | Automated test suite pass/fail |
| **Human scorers** | Required | Not needed | Not needed |
| **Difficulty calibration** | None (post-hoc discovery) | Human accuracy tiers | Mandatory pilot + stopping rules |
| **Statistical power (H1)** | ~0% (ceiling) | ~81% (but wrong domain) | ~84% (for 15pp at α=0.025) |
| **Primary analysis** | GLMM (statsmodels LMM) | GLMM (statsmodels LMM) | GLMM (pymer4/lme4 logistic — F1 fix) |
| **Random effects** | Intercepts only | Intercepts only | Intercepts + slopes (S1 fix) |
| **Contamination check** | None | N/A (novel tasks) | Automated detection (S3 fix) |
| **Manipulation check** | None | None | ARC compliance scoring (S7 fix) |
| **Key weakness** | Tasks too easy | Wrong domain | Requires successful task curation + pilot |
| **What it proves** | Model aces simple SE tasks | ARC doesn't help visual reasoning | Whether ARC helps on real SE tasks |

---

## 12. Expected Outcomes and Interpretation

### 12.1 Outcome Matrix (Updated per S8 Fix)

| Result | Detection Method | Interpretation | Implication for Squad |
|--------|-----------------|---------------|----------------------|
| **H1 supported, H2 supported** | Primary one-sided tests (α=0.025) | ARC framework helps AND adds value beyond CoT | Strong evidence; framework is validated |
| **H1 supported, H2 not supported** | Primary one-sided tests | ARC helps vs bare baseline, but CoT alone is just as good (CH5) | Weak evidence; any structured reasoning helps, ARC isn't special |
| **H1 not supported, H2 not supported** | Primary one-sided tests | No evidence that ARC helps on SE tasks | Null result; framework may need redesign or may not work for single-turn |
| **ARC significantly WORSE** | **Exploratory two-sided tests** (α=0.05) | Framework actively hurts performance | Strong evidence against; overhead outweighs benefits |

**S8 clarification:** The primary one-sided tests have zero power for detecting ARC being worse than baseline. The "ARC significantly WORSE" outcome is detectable only through the exploratory two-sided tests. If the exploratory two-sided test shows ARC significantly worse, this is reported as a key finding even though it was not the primary pre-registered test.

### 12.2 Honest Reporting Commitment

Regardless of outcome:
- Report ALL pre-registered hypotheses (no selective reporting)
- Report ALL robustness checks (R1–R10)
- Report counter-hypothesis test results (CH1–CH8)
- Report exact p-values and confidence intervals (not just "significant" / "not significant")
- Report Bayes Factors to distinguish "no evidence" from "evidence of no effect"
- Report ARC compliance statistics (S7 fix)
- Report contamination detection results (S3 fix)
- Upload all raw data and analysis scripts to the public repository

---

## 13. Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **P1: Task Curation** | 3–5 days | 60 task YAML files + scoring sandboxes |
| **P2: Scorer Validation** | 1 day | All 60 tasks pass 3-point validation |
| **P2b: Contamination Detection** | 0.5 day | Run contamination check on SWE-bench tasks (§2.6) |
| **P3: Harness Development** | 1–2 days | Execution harness (adapted from V3.1) + ARC compliance checker |
| **P4: Q Review** | 1 day | Q approval of protocol + tasks |
| **P5: Pre-Registration** | 0.5 day | Git tag `v4.1-preregistration` |
| **P6: Pilot** | 0.5 day | 30 runs, difficulty verification, category-level check (M5) |
| **P7: Full Execution** | 0.5 day | 900 runs (~4 hours) |
| **P8: Analysis** | 1 day | pymer4/lme4 GLMM results, all hypothesis tests |
| **P9: Write-Up** | 1 day | RESULTS_SUMMARY_V4.md |
| **Total** | **~10–11 days** | Definitive answer to the research question |

---

## 14. Appendices

### Appendix A: ARC 4-Pillar Framework (as implemented in Squad)

The ARC framework structures AI reasoning into four sequential phases:

1. **EXPLORE:** Thoroughly examine the problem space before attempting a solution. Read all available context, identify constraints, note relationships and dependencies.

2. **MODEL:** Build an abstract mental model of the system. Identify core patterns, formulate hypotheses about behavior, understand what invariants must be maintained.

3. **GOAL:** Define concrete, measurable objectives. What does "done" look like? What are the acceptance criteria? What side effects must be avoided?

4. **EXECUTE:** Implement the solution methodically, checking each step against the model and goal. Verify correctness before finalizing.

The hypothesis is that this structured approach — especially the explicit EXPLORE and MODEL phases — prevents premature solution attempts and reduces errors that stem from incomplete problem understanding.

### Appendix B: Sample Task (Bug Diagnosis)

```yaml
id: "BUG_PILOT_01"
category: "BUG"
difficulty: "medium"
source: "swe-bench-verified"
source_id: "sympy__sympy-20442"
language: "python"

problem: |
  The `convert_to` function in SymPy incorrectly converts units with 
  prefix mismatches. Running the following test produces a wrong result:
  
  >>> from sympy.physics.units import convert_to, joule, kilogram, meter, second
  >>> convert_to(joule*second, joule)
  Expected: joule*second
  Actual: 1000*joule*second (incorrect factor of 1000)
  
  Fix the bug in the convert_to function.

context_files:
  - path: "sympy/physics/units/util.py"
    content: |
      [... actual file content ...]
  - path: "sympy/physics/units/tests/test_util.py"
    content: |
      [... test file content ...]

output_format: "unified_diff"

scoring:
  type: "test_suite"
  test_command: "python -m pytest sympy/physics/units/tests/test_util.py -x -q"
  pass_criterion: "exit_code_0"
  timeout_seconds: 60

contamination_flag: null  # Updated after contamination detection (§2.6)
```

### Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **ARC 4-Pillar** | Explore → Model → Goal → Execute reasoning framework |
| **GLMM** | Generalized Linear Mixed Model (logistic for binary outcomes) |
| **pymer4** | Python wrapper for R's lme4 package — used for primary GLMM analysis (F1 fix) |
| **lme4::glmer** | R function for fitting generalized linear mixed-effects models |
| **LPM** | Linear Probability Model — OLS/LMM on binary outcome; used as sensitivity check only |
| **SWE-bench Verified** | Curated subset of SWE-bench with human-verified test patches |
| **CodeContests** | Google's competitive programming dataset |
| **MBPP+** | Sanitized and augmented version of Mostly Basic Python Programs |
| **ICC** | Intra-class correlation coefficient (proportion of variance due to task clustering) |
| **OR** | Odds ratio (effect size for logistic regression) |
| **BF₁₀** | Bayes Factor in favor of H1 over H0 |
| **Cohen's h** | Effect size for comparing two proportions |
| **Collider bias** | Bias introduced by conditioning on a post-treatment variable on the causal pathway (relevant to CH2 — F2 fix) |
| **ITT** | Intent-to-treat analysis — includes all randomized runs regardless of ARC compliance |

### Appendix D: Analysis Code Template (F1 Fix)

**Primary GLMM analysis using pymer4:**

```python
import pandas as pd
from pymer4.models import Lmer

# Load data (pilot runs excluded per F3 fix)
df = pd.read_json("results/v4/checkpoint.jsonl", lines=True)
assert df[df["run_id"].str.contains("pilot")].empty, "Pilot data must not be in main dataset"

# Recode condition as categorical with baseline as reference
df["condition"] = pd.Categorical(df["condition"], categories=["baseline", "cot", "arc"])
df["difficulty"] = pd.Categorical(df["difficulty"], categories=["easy", "medium", "hard"])
df["pass_int"] = df["pass"].astype(int)

# ── Primary model: maximal random effects (S1 fix) ──
try:
    model_max = Lmer(
        "pass_int ~ condition + difficulty + (1 + condition | task_id)",
        data=df,
        family="binomial"
    )
    result_max = model_max.fit()
    primary_result = result_max
    convergence_note = "Maximal model converged successfully."
except Exception as e:
    # Fallback 1: zero-correlation random effects
    try:
        model_zc = Lmer(
            "pass_int ~ condition + difficulty + (1 + condition || task_id)",
            data=df,
            family="binomial"
        )
        result_zc = model_zc.fit()
        primary_result = result_zc
        convergence_note = f"Maximal model failed ({e}). Zero-correlation model used."
    except Exception as e2:
        # Fallback 2: random intercepts only
        model_ri = Lmer(
            "pass_int ~ condition + difficulty + (1 | task_id)",
            data=df,
            family="binomial"
        )
        result_ri = model_ri.fit()
        primary_result = result_ri
        convergence_note = f"Maximal and ZC models failed. Intercepts-only model used."

print(convergence_note)
print(primary_result.summary())

# ── H1: One-sided test for ARC > Baseline ──
arc_coef = primary_result.coefs.loc["condition[T.arc]"]
arc_z = arc_coef["Z-stat"]
arc_p_onesided = arc_coef["P-val"] / 2  # Convert two-sided to one-sided
print(f"H1 (ARC vs Baseline): z={arc_z:.3f}, p(one-sided)={arc_p_onesided:.4f}")
print(f"H1 significant at α=0.025: {arc_p_onesided < 0.025}")

# ── Exploratory two-sided test (S8 fix) ──
arc_p_twosided = arc_coef["P-val"]
print(f"H1 exploratory two-sided: p={arc_p_twosided:.4f}")
print(f"H1 two-sided significant at α=0.05: {arc_p_twosided < 0.05}")

# ── R7: LPM sensitivity check (F1 fix) ──
import statsmodels.formula.api as smf
lpm = smf.mixedlm("pass_int ~ C(condition) + C(difficulty)", 
                    data=df, groups=df["task_id"])
lpm_result = lpm.fit()
print("\n--- LPM Sensitivity Check (R7) ---")
print(lpm_result.summary())
```

**Contamination detection (S3 fix):**

```python
# Run BEFORE the main experiment
import json

contamination_results = {}
for task in swebench_tasks:
    # Assemble prompt with issue description ONLY (no code context)
    prompt = f"You are a software engineer. Solve the following task.\n\n{task['problem']}\n\nProvide your solution below.\n\n{output_format_instructions}"
    
    response = call_api(prompt, temperature=0.0)
    solution = extract_solution(response)
    passed = run_scoring(task, solution)
    
    contamination_results[task['id']] = {
        "passed_without_context": passed,
        "flag": "suspected" if passed else "clean"
    }
    
    # Update task YAML
    task['contamination_flag'] = contamination_results[task['id']]['flag']

# Report
flagged = sum(1 for r in contamination_results.values() if r['flag'] == 'suspected')
print(f"Contamination check: {flagged}/{len(swebench_tasks)} tasks flagged as suspected")
```

**ARC compliance check (S7 fix):**

```python
import re

def compute_arc_compliance(response: str) -> int:
    """Score ARC compliance on a 0-4 scale."""
    compliance = 0
    patterns = [
        r'(?i)\b(step\s*1|explore)\b.*?:',
        r'(?i)\b(step\s*2|model)\b.*?:',
        r'(?i)\b(step\s*3|goal)\b.*?:',
        r'(?i)\b(step\s*4|execute)\b.*?:',
    ]
    for pattern in patterns:
        if re.search(pattern, response):
            compliance += 1
    return compliance

# Apply to all ARC runs
arc_runs = df[df["condition"] == "arc"]
arc_runs["arc_compliance"] = arc_runs["raw_response"].apply(compute_arc_compliance)

mean_compliance = arc_runs["arc_compliance"].mean()
print(f"Mean ARC compliance: {mean_compliance:.2f}/4")
print(f"Distribution: {arc_runs['arc_compliance'].value_counts().sort_index().to_dict()}")

# Sensitivity analysis: compliant-only
compliant_df = df[~((df["condition"] == "arc") & (df["arc_compliance"] < 3))]
# Refit GLMM on compliant_df...
```

---

**END OF PROTOCOL (REVISED)**

*This revised protocol addresses all 3 fatal flaws, 4 serious concerns, 2 prompt design issues, 3 missing counter-hypotheses, and 2 methodology gaps identified in Q's adversarial review. The protocol is ready for pre-registration — no known fatal flaws remain.*

**— Picard (Lead, Architecture & Decisions)**  
**Approved with revisions by: Q (Devil's Advocate & Fact Checker)**
