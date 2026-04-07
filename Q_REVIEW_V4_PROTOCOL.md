# Q's Adversarial Review — V4 Experiment Protocol

**Reviewer:** Q (Devil's Advocate & Fact Checker)  
**Document Reviewed:** `EXPERIMENT_V4_PROTOCOL.md` (996 lines, v4.0)  
**Date:** 2026-07-14  
**Review Scope:** Full protocol, all 14 sections + appendices  

---

## Review Summary

| Category | Count |
|----------|-------|
| Fatal Flaws | 3 |
| Serious Concerns | 8 |
| Methodology Gaps | 6 |
| Counter-Hypothesis Issues | 3 (1 flawed, 2 missing) |
| Prompt Design Issues | 5 |

**Verdict: APPROVE WITH CONDITIONS** — Protocol is substantially sound and represents a major improvement over V2.1/V3.1, but 3 fatal flaws must be fixed and several serious issues addressed before the first API call. Details below.

---

## 1. FATAL FLAWS (Must Fix Before Execution)

### F1. GLMM Implementation Uses Wrong Model Class (§6.2)

**The Problem:**  
§6.2 states: *"Fitted using: `statsmodels.MixedLM`"*

`statsmodels.MixedLM` fits a **Linear Mixed Model** — continuous Gaussian outcome. The primary outcome is **binary pass/fail**. Running `MixedLM` on 0/1 data produces a Linear Probability Model (LPM) with random effects, NOT a logistic GLMM. The coefficients are NOT log-odds ratios, the predicted probabilities can fall outside [0,1], and the standard errors are incorrect for binary data.

The protocol correctly specifies `lme4::glmer` as a "fallback if convergence issues arise" — but this should be the **primary** tool, not the fallback.

| Claim | Status | Evidence |
|-------|--------|----------|
| "Logistic GLMM" specified as analysis | ✅ Correct specification | §6.2, §1.2 |
| `statsmodels.MixedLM` implements logistic GLMM | ❌ **FALSE** | `MixedLM` is Gaussian LMM only |
| `lme4::glmer(family=binomial)` is correct | ✅ Correct | Standard for binary GLMM |
| Power analysis parameters (β₂=0.619, σ²=0.822) | ✅ Verified | Independently computed |

**Fix Required:** Change the primary analysis tool to `lme4::glmer(family=binomial)` in R, or use Python's `statsmodels.BinomialBayesMixedGLM` / the `pymer4` wrapper. Document `statsmodels.MixedLM` as a **sensitivity check** (the LPM is actually a useful robustness comparison), not the primary analysis.

**Severity:** Fatal. If executed as written, ALL primary p-values and odds ratios would be technically incorrect. A reviewer would reject the paper on this alone.

---

### F2. Post-Treatment Collider Bias in Counter-Hypothesis CH2 (§1.4)

**The Problem:**  
CH2 states: *"Add response_token_count as covariate; check if ARC effect disappears."*

Response token count is a **post-treatment variable** — it's caused by the condition (ARC prompts elicit longer responses) AND potentially causes the outcome (longer responses may contain more correct content). Adding it as a covariate creates **collider bias**: conditioning on a variable that sits on the causal pathway between treatment and outcome can attenuate or reverse the estimated treatment effect, even when the treatment genuinely works.

```
Causal diagram:
  Condition (ARC) ──→ Response Length ──→ Pass/Fail
       │                                     ↑
       └─────────────────────────────────────┘
              (direct effect of framework)
              
Conditioning on Response Length blocks BOTH paths,
making ARC look ineffective even if it works.
```

If ARC genuinely helps through the mechanism of *structured thinking* (which produces longer, more thorough responses), then CH2's test would incorrectly conclude the effect is "just response length." This is a textbook mediator-as-confounder error.

**Fix Required:** Replace CH2's method. Options:
1. **Instrumental variable approach:** Use prompt_token_count (pre-treatment) as an instrument
2. **Length-matched control:** Add a 4th condition — "Verbose Baseline" — that instructs the model to write at length without structure (impractical at this stage)
3. **Partial mediation analysis:** Use a proper causal mediation framework (e.g., Baron & Kenny or modern causal inference) that correctly partitions direct vs. mediated effects
4. **Keep CH2 but reframe it:** Report response length differences descriptively, note the mediator problem explicitly, and do NOT use it to dismiss the ARC effect

**Severity:** Fatal for CH2 specifically. If CH2 "succeeds" (ARC effect disappears when controlling for response length), you would draw the wrong conclusion. The entire counter-hypothesis framework's credibility rests on these tests being methodologically sound.

---

### F3. Pilot Data Double-Dipping Risk (§7.2, §7.4)

**The Problem:**  
§7.2 states: *"These 10 tasks will be INCLUDED in the full experiment (not discarded)."*

The pilot runs 10 tasks × baseline × 3 reps = 30 runs. The protocol never explicitly states whether these 30 pilot baseline runs are **excluded** from the 300 baseline runs in the main experiment (60 tasks × 5 reps). Two scenarios:

**Scenario A (pilot runs counted in main):** The 10 pilot tasks have 3 pilot reps + 2 fresh reps = 5 baseline runs, while the other 50 tasks have 0 + 5 = 5 fresh baseline runs. The pilot runs were used to SELECT the task difficulty range (decision to proceed) and are ALSO used in hypothesis testing. This is data double-dipping — the same data informs both task selection and inference. It inflates the probability that the 10 pilot tasks have baseline rates in the 40–70% range (because tasks outside that range were replaced), while the 50 non-pilot tasks are uncalibrated.

**Scenario B (pilot runs excluded from main):** The 10 pilot tasks get 5 FRESH baseline runs plus 5 CoT + 5 ARC = 15 main runs. The 30 pilot runs are discarded for analysis purposes. This is clean but wasteful, and the protocol doesn't specify this.

**Fix Required:** Explicitly state in §7.2 and §7.4:
- Pilot runs are stored separately and **excluded from all main analyses**
- All 60 tasks receive a full 5 fresh repetitions per condition in the main experiment
- The pilot's ONLY role is informing the proceed/stop decision and calibrating expectations

**Severity:** Fatal if Scenario A, easily fixable if clarified to Scenario B. As written, the ambiguity alone would draw reviewer criticism.

---

## 2. SERIOUS CONCERNS (Would Weaken Conclusions)

### S1. No Random Slopes in the GLMM (§6.2)

The model specifies only random intercepts for task:
```
logit(P(pass_ijk)) = β₀ + β₁·cot_j + β₂·arc_j + ... + u_i
```

This assumes the **condition effect is identical** across all 60 tasks. But H5 explicitly hypothesizes that ARC advantage *varies by category*, and any reasonable theory predicts it varies by task. Forcing a constant condition effect across tasks is a **maximal structure violation** that:
- Underestimates standard errors for condition effects
- Inflates Type I error rate (anti-conservative)
- Produces biased variance estimates

**Recommendation:** Specify maximal random effects structure as primary:
```
logit(P(pass_ijk)) = β₀ + β₁·cot_j + β₂·arc_j + ... + u_i + v_i·cot_j + w_i·arc_j
```
With random slopes `v_i`, `w_i` for condition within task. If convergence fails (common with binary outcomes and 60 clusters), fall back to intercepts-only — but this must be pre-registered as the fallback, not the default.

**Citation:** Barr, Levy, Scheepers & Tily (2013), "Random effects structure for confirmatory hypothesis testing" — the standard reference for maximal GLMM specification.

---

### S2. Power for H2 Is Below Conventional Threshold (§6.1)

| Hypothesis | Power | Threshold | Status |
|-----------|-------|-----------|--------|
| H1 (ARC vs Baseline, 15pp) | 84% | 80% | ✅ Adequate |
| H2 (ARC vs CoT, 10pp) | 61% | 80% | ❌ **Underpowered** |

61% power means a **39% probability of false negative** on the most scientifically interesting comparison. If H1 passes but H2 fails, we can't distinguish "ARC adds nothing over CoT" from "we didn't have enough power to detect the difference." This is especially problematic because CH5's test DEPENDS on H2's result.

The protocol acknowledges this (§6.1: "pre-registered as limitation"; §10.1 risk table), which is honest. But a 39% miss rate on your key differential claim is not a "limitation" — it's a design weakness.

**Recommendations:**
- Increase to 80 tasks (74% power for H2 per §6.1 table) or 10 reps (more practical)
- Alternatively, reduce the H2 effect threshold to 15pp (matching H1) — detecting a 10pp difference between two structured prompts was always ambitious
- At minimum, pre-register that H2 will be evaluated primarily via confidence interval width, not significance testing, given insufficient power

---

### S3. SWE-bench Task Contamination Not Adequately Mitigated (§10.1)

The risk registry claims: *"Task contamination — Low — Use SWE-bench Verified (not training set)"*

This is **dangerously optimistic**. SWE-bench is one of the most widely-used AI code benchmarks. Claude Sonnet 4 was almost certainly evaluated on (and potentially fine-tuned with awareness of) SWE-bench tasks. Even if the exact training set excluded SWE-bench Verified, the underlying GitHub issues and their solutions from Django, Flask, scikit-learn, and sympy repos are overwhelmingly likely to appear in the model's pre-training corpus.

**Evidence of concern:**
- SWE-bench papers published 2023–2024; Claude Sonnet 4 trained on data through at least 2025
- The target repos (Django, Flask) have 70K+ GitHub stars — among the most-indexed Python repos
- Individual issues with solutions are public GitHub content = training data

This doesn't confound the condition comparison (all conditions see the same task), but it:
- Creates ceiling risk on contaminated tasks (model recalls the exact fix)
- Reduces the effective difficulty calibration
- Undermines the "real-world difficulty" claim

**Recommendations:**
- Add contamination detection: For each SWE-bench task, check if the model can solve it at temperature=0 without any code context (just the issue description). If >80% solve rate without context, the task is likely memorized → exclude it.
- Increase the proportion of curated GitHub issues (Source 4) from 10–15 to 20–25, using less famous repos (<5K stars)
- Report a contamination-sensitivity analysis: re-run GLMM excluding all SWE-bench tasks

---

### S4. Single-Turn Design Limits Ecological Validity (§4.2)

The experiment uses single-turn API calls, but Squad's ARC framework is designed for **multi-turn, agentic** interactions where:
- EXPLORE involves actually running code, reading files from disk, executing tests
- MODEL is refined through iterative hypothesis testing
- GOAL is adjusted based on intermediate results
- EXECUTE includes running tests and fixing errors

In single-turn mode, EXPLORE is reduced to "read the code in the prompt" — a dramatically impoverished version of the framework. If the experiment finds no effect, it could mean:
1. The ARC framework doesn't help (the null conclusion), OR
2. The framework helps in multi-turn but not single-turn (a scope limitation)

These are very different conclusions, and the experiment cannot distinguish them.

**Recommendation:** This is a fundamental design constraint that cannot be easily fixed without a much larger experiment. Pre-register it as the **primary interpretation limitation** in §12. If null results are obtained, explicitly note that the single-turn format may have prevented the framework from demonstrating its full value.

---

### S5. SWE-bench Adaptation Reduces EXPLORE Phase Value (§2.2, Source 1)

When adapting SWE-bench tasks for single-turn, §2.2 says: *"Extract the minimal set of relevant files (identified by the gold patch)."*

This means the experimenters use the **known-correct fix** to select which files to show the model. In real engineering, finding the relevant files IS a major part of the EXPLORE phase. By pre-selecting files using the gold patch, you:

1. **Remove exploration difficulty** — the model doesn't need to search for relevant code
2. **Systematically disadvantage ARC** — the EXPLORE step ("read all provided code, identify components") becomes trivial when you've already been given exactly the right files
3. **Leak information** — knowing which files the gold patch touches tells the model where the bug lives

This could suppress the ARC effect specifically on BUG/REF/INT tasks sourced from SWE-bench (20–25 of 60 tasks).

**Recommendation:** For at least some tasks, include a few **distractor files** alongside the relevant ones (files from the same module that the gold patch does NOT touch). This makes EXPLORE non-trivial and tests whether the framework helps the model focus on the right components.

---

### S6. Code Review (C5) Scoring Is Categorically Different (§5.2)

| Category | Pass Criterion | Type |
|----------|---------------|------|
| BUG, REF, INT | Test suite passes | Objective binary |
| ALG | All test cases pass | Objective binary |
| TST | Coverage ≥90% AND mutations ≥80% | Compound threshold |
| **REV** | **F1 ≥ 0.8** | **Subjective threshold on continuous metric** |

The F1-based scoring for Code Review tasks introduces several asymmetries:
- The 0.8 threshold is arbitrary — why not 0.7 or 0.9?
- String matching for bug identification (§5.2: "String matching") is fragile — the model might describe the same bug differently than the ground truth
- F1 combines precision and recall; the model could game this differently across conditions

Including REV tasks in the same GLMM as test-suite tasks assumes comparable pass/fail calibration. If REV tasks have systematically different pass rates due to scoring methodology (not task difficulty), they add noise and could bias the condition effect estimates.

**Recommendation:** Either:
1. Pre-register the F1 threshold with a pilot-derived justification, OR
2. Report GLMM results **with and without** REV tasks as a pre-registered robustness check (add to §6.5)

---

### S7. No Manipulation Check for ARC Compliance (Missing from Protocol)

The protocol never verifies whether the model actually **follows** the 4-pillar framework when given the ARC prompt. The model might:
- Ignore the framework entirely and solve directly
- Partially comply (do EXPLORE and EXECUTE but skip MODEL and GOAL)
- Superficially comply (write "EXPLORE:" as a heading but not actually explore)

Without a manipulation check, a null result could mean "the framework doesn't help" or "the model didn't use the framework."

**Recommendation:** Add a post-hoc manipulation check:
- For each ARC run, code whether the response contains identifiable EXPLORE, MODEL, GOAL, EXECUTE sections (regex-based automated check)
- Report ARC compliance rate
- If compliance < 80%, report GLMM results on compliant-only runs as a robustness check
- Do NOT pre-register manipulation check as a filter (this would be conditioning on a post-treatment variable), but report it descriptively

---

### S8. One-Sided Tests Conflict with Outcome Matrix (§1.2 vs §12.1)

§1.2 specifies one-sided tests for H1 and H2:
- *"H1₀: Completion_ARC − Completion_Baseline ≤ 0"*

But §12.1's outcome matrix includes:
- *"ARC significantly WORSE — Framework actively hurts — Strong evidence against"*

A one-sided test at α=0.025 has **zero power** for detecting ARC being worse than baseline. If the outcome matrix includes degradation as a meaningful result, the tests should be two-sided.

**Options:**
1. Make tests two-sided at α=0.025 each (reduces power for detecting improvement to ~78% for H1)
2. Keep one-sided but remove "ARC significantly WORSE" from the outcome matrix and note that detecting harm requires a separate exploratory two-sided test
3. Keep one-sided at α=0.025 but ADD a pre-registered two-sided test at α=0.05 as a sensitivity check

**Recommendation:** Option 3. It preserves the directional power for the primary claim while explicitly testing for harm.

---

## 3. METHODOLOGY GAPS

### M1. No Inter-Rater Reliability for Task Curation (§2.2, Source 4)

Source 4 ("Curated GitHub Issues") involves human judgment: selecting repos, evaluating issue clarity, writing test suites from fixes. The protocol doesn't specify:
- Who curates the tasks (one person? multiple?)
- What rubric guides selection decisions
- Whether independent curators agree on task quality/difficulty

**Fix:** Either have two independent curators select tasks with IRR metrics, or document the single curator's selection criteria as a detailed rubric.

### M2. Missing Pre-Registered Exclusion Criteria for Edge Cases

What happens if a task:
- Passes at 100% across all conditions (effective ceiling on one task)?
- Fails at 0% across all conditions (effective floor on one task)?
- Has >50% extraction failure rate (prompt format issue for that specific task)?

The stopping rules (§8) operate at aggregate level but don't address per-task anomalies.

**Fix:** Pre-register that individual tasks with pass rates >95% or <5% across all conditions and all reps will be flagged in a sensitivity analysis (GLMM excluding extreme tasks).

### M3. Tiktoken Proxy Tokenizer May Cause Context Overflow (§2.5)

§2.5: *"Token count is measured using the `tiktoken` cl100k_base tokenizer as a proxy."*

Claude uses its own BPE tokenizer (not cl100k_base). For non-ASCII content, code with unusual variable names, or long identifiers, the token counts can diverge by 10–20%. A task measured at 11,500 tokens by tiktoken might actually be 13,000 Claude tokens, pushing the total prompt (with ARC template overhead) near the effective context window.

This is NOT a consistency concern (all conditions see the same content), but it could cause:
- Truncated inputs if the actual token count exceeds the window
- Asymmetric impact: ARC prompts add ~250 MORE tokens than baseline, so ARC has less margin

**Fix:** Measure token counts using the Claude tokenizer (or Anthropic's token counting API) for all 60 tasks. Flag any task where ARC-formatted prompt exceeds 90% of the context window.

### M4. No Pre-Registered Definition of "Practical Significance"

The protocol defines statistical significance thresholds (α=0.025) and minimum detectable effects (15pp, 10pp), but never states: **what effect size would Squad consider worth implementing?**

If ARC beats baseline by 5pp (p<0.05), is that enough to justify using the framework? If it beats by 15pp but only on Easy tasks, is that useful?

**Fix:** Pre-register a practical significance threshold: "We would recommend adopting the ARC framework if H1 is supported AND the estimated effect is ≥10pp AND it is not driven solely by Easy tasks (CH3 not supported)."

### M5. Category-Level Difficulty Verification Missing

The pilot checks aggregate baseline pass rate (40–70%), but what if:
- BUG tasks average 85% (ceiling for that category)
- ALG tasks average 15% (floor for that category)
- Aggregate is 50% (within range)

The within-category imbalance would make H5 (category interaction) uninterpretable.

**Fix:** Add a pilot decision rule: "No individual category's pilot baseline pass rate may exceed 85% or fall below 15%." Requires 2 tasks per category in the pilot (§7.2 nearly achieves this but has only 1 task for the 6th category).

### M6. Model Version Pinning Is Specified but Not Verified (§10.1)

§4.2: *"model": "claude-sonnet-4-20250514"* — good, the model version is pinned.

§10.2: *"If model version changes mid-experiment: Complete all remaining runs."*

But the Copilot Chat API is a **proxy** — it routes to Anthropic's API, and GitHub controls the routing. There's no guarantee that `claude-sonnet-4-20250514` will resolve to the same model weights throughout the experiment. The mitigation (§10.2) should also include: **check the `model` field in every API response** and flag any discrepancies.

---

## 4. COUNTER-HYPOTHESIS COVERAGE

### Existing Counter-Hypotheses

| ID | Counter-Hypothesis | Status | Q Assessment |
|----|-------------------|--------|-------------|
| CH1 | Prompt length drives improvement | ✅ Valid test | Prompt_token_count is pre-treatment; safe to use as covariate |
| CH2 | Response length drives improvement | ❌ **Flawed test** | Response_token_count is post-treatment; collider bias (see F2) |
| CH3 | ARC helps only on Easy tasks | ✅ Valid test | Tested via H4 interaction term |
| CH4 | Outlier tasks drive the effect | ✅ Valid test | Leave-3-out is standard sensitivity analysis |
| CH5 | ARC = CoT (no added value of structure) | ✅ Valid test | Directly tested by H2 |

### Missing Counter-Hypotheses

**CH6 (Memorization/Contamination):** If the model has memorized solutions for SWE-bench tasks, the ceiling effect on those tasks reduces headroom for ARC improvement. Test: Compare ARC effect size on SWE-bench-sourced tasks vs. curated GitHub tasks vs. CodeContests tasks. If ARC effect is present only on non-SWE-bench tasks, contamination is suppressing the effect on well-known tasks.

**CH7 (Instruction Density, not Framework Structure):** The ARC prompt contains ~16 explicit sub-instructions; CoT has 3; Baseline has 1. Any improvement might stem from *more explicit instructions* rather than the *specific 4-pillar structure*. Test: This is the hardest counter-hypothesis to address without a 4th condition (e.g., "16 random SE best-practice instructions, not organized into EXPLORE/MODEL/GOAL/EXECUTE"). At minimum, document this as an uncontrolled confound.

**CH8 (Format-Aided Extraction):** The ARC prompt encourages structured, labeled output. This might improve extraction success rate (finding the SOLUTION: marker) rather than actual solution quality. Test: Compare extraction_success rates across conditions. If ARC has significantly higher extraction rates, re-run GLMM excluding extraction failures from all conditions to check if the effect persists.

---

## 5. PROMPT DESIGN ISSUES

### P1. Instruction Density Confound (Critical)

Quantitative analysis of the three prompts (template text only, excluding shared `{problem}` and `{context}`):

| Metric | Baseline | CoT | ARC | ARC/CoT Ratio |
|--------|----------|-----|-----|---------------|
| Instruction words | ~9 | ~42 | ~162 | **3.9x** |
| Explicit sub-instructions | 1 | 3 | ~16 | **5.3x** |
| Structural sections | 0 | 0 | 4 | — |

The ARC prompt doesn't just add *structure* — it adds **vastly more explicit instruction content**. Each pillar includes 4 specific bullet points like "Identify the key components, data flows, and dependencies" and "What invariants must be maintained?" These are independently useful software engineering heuristics regardless of their organization into the EXPLORE/MODEL/GOAL/EXECUTE structure.

**Impact:** If ARC outperforms CoT, we cannot distinguish whether it's:
1. The 4-pillar structure (EXPLORE→MODEL→GOAL→EXECUTE ordering)
2. The 16 specific SE heuristics embedded in the prompt
3. Simply having 4x more instructional text than CoT

This is the single largest internal validity threat to the experiment. CH1 (prompt length) partially addresses it, but prompt LENGTH is not the same as instruction DENSITY.

**Recommendation:** This cannot be fully fixed without a 4th condition (impractical). Mitigations:
- Pre-register this as the experiment's primary confound
- In the CoT prompt, add more specific (but unstructured) instructions to narrow the instruction density gap — e.g., add bullets like "Consider edge cases", "Think about invariants", "Check for regressions" — without the EXPLORE/MODEL/GOAL/EXECUTE structure. Target ~8–10 sub-instructions in CoT
- This would make the comparison "structured 16 instructions vs. unstructured 10 instructions vs. minimal" — still confounded but less egregiously so

### P2. ARC Prompt Has Redundant Bookend Instruction (§3.3, line 357)

After the `{context_files}`, the ARC prompt adds:
> *"Now apply the EXPLORE → MODEL → GOAL → EXECUTE framework:"*

Neither Baseline nor CoT has an equivalent reminder instruction after the context. This gives ARC a positional advantage: the model's attention is re-anchored on the framework instructions right before generating the response.

**Fix:** Either remove the bookend line, or add equivalent reminders to the other conditions:
- Baseline: *"Now solve the task:"*
- CoT: *"Now think step by step and solve the task:"*

### P3. System Prompt Redundancy (§4.2 vs §3.1–3.3)

The system prompt is: *"You are a helpful software engineering assistant."*

Each user prompt ALSO starts with "You are a software engineer..." — creating a double identity prompt. This is consistent across conditions, so it's not a confound. But it's unnecessary and could be simplified by removing the system prompt role assignment and relying solely on the per-condition user prompt.

### P4. ARC Prompt Doesn't Require Explicit Output for Each Phase

The ARC prompt says "Examine the problem space" and "Build a mental model" but never says "**Write out** your exploration" or "**Show** your mental model." The model might internalize these steps without verbalizing them, making:
1. The manipulation check (S7) impossible on non-verbose responses
2. The framework's "forced thinking" benefit potentially weaker than intended

**Recommendation:** Add explicit verbalization instructions:
```
For each step, show your work before moving to the next step.
```
This makes the framework's reasoning visible and testable. Note: this adds further instruction content (exacerbating P1) — document this trade-off.

### P5. Temperature Interaction with Prompt Specificity

At temperature=1.0, more constrained prompts (ARC) should produce less variable outputs than less constrained prompts (Baseline). This means:
- ARC's 5 repetitions may cluster more tightly (lower within-task variance)
- Baseline's 5 repetitions may spread more widely
- This could artificially improve ARC's AVERAGE performance if the constrained distribution is centered higher

This is a subtle effect but potentially real. The GLMM's random effects should absorb some of this, but it's worth checking: report the within-task variance (across 5 reps) per condition as a descriptive statistic.

---

## 6. NUMERICAL VERIFICATION

| Claim (§ Reference) | Status | Verification |
|---------------------|--------|-------------|
| β₂ = 0.619 (§6.1) | ✅ Verified | logit(0.65) − logit(0.50) = 0.6190 |
| σ²_task = 0.82 from ICC=0.20 (§6.1) | ✅ Verified | 0.20 × (π²/3) / 0.80 = 0.8225 |
| Bonferroni α = 0.025 (§6.3) | ✅ Verified | 0.05 / 2 = 0.025 |
| 60 × 3 × 5 = 900 runs (§0.1) | ✅ Verified | Arithmetic correct |
| Pilot: 10 × 1 × 3 = 30 runs (§7.2) | ✅ Verified | Arithmetic correct |
| Execution time ~4 hours (§4.6) | ⚠️ Plausible | 900 × 15s = 13,500s = 3.75h + overhead. Assumes 15s/run — could be 20–30s if Docker sandbox startup is slow |
| Token budget: 12K context + 1.5K template + 8K response = 21.5K (§2.5) | ✅ Verified | Well within Claude's 200K context window |
| "~250 extra prompt tokens" for ARC (§3.5) | ⚠️ Approximate | ~162 additional instruction words ≈ 200–280 tokens depending on tokenizer. Plausible but should be measured precisely |

---

## 7. WHAT THE PROTOCOL GETS RIGHT

The trial never ends, but it wouldn't be honest to ignore what works. Compared to V2.1 and V3.1, this protocol is a substantial improvement:

1. **Mandatory pilot with decision rules (§7)** — directly prevents the V2.1 ceiling disaster
2. **Stopping rules for both ceiling AND floor (§8)** — learned from both prior failures
3. **Automated scoring via Docker sandboxes (§5.4)** — eliminates the human scorer bias flagged in V2.1
4. **Pre-registered counter-hypotheses (§1.4)** — shows intellectual honesty about alternative explanations
5. **Scorer validation with 3-point checks (§5.5)** — gold/null/near-miss is a solid validation approach
6. **Honest acknowledgment of H2 power limitation** — would be worse if buried
7. **Task freezing rule (§2.4)** — prevents post-hoc task modification
8. **Fully randomized run order with seed (§4.3)** — prevents ordering effects
9. **Checkpointing and resume protocol (§4.5)** — practical and necessary
10. **Bayes Factor reporting (§6.4)** — distinguishes "no evidence" from "evidence of no effect"

---

## 8. VERDICT

### APPROVE WITH CONDITIONS

The protocol may proceed to task curation and pilot execution **after** the following changes are made:

#### Must-Fix (Before Pre-Registration)

| # | Issue | Fix | Priority |
|---|-------|-----|----------|
| F1 | Wrong GLMM implementation | Change primary to `lme4::glmer(family=binomial)` | **BLOCKING** |
| F2 | CH2 collider bias | Reframe CH2; add proper mediation note; do not use as dismissal evidence | **BLOCKING** |
| F3 | Pilot data ambiguity | Explicitly exclude pilot runs from main analysis | **BLOCKING** |

#### Should-Fix (Before Full Execution)

| # | Issue | Fix | Priority |
|---|-------|-----|----------|
| S1 | No random slopes | Attempt maximal structure; pre-register fallback | HIGH |
| S3 | SWE-bench contamination | Add contamination detection check; increase curated tasks | HIGH |
| S7 | No manipulation check | Add automated ARC compliance coding | HIGH |
| P1 | Instruction density confound | Enrich CoT prompt to ~8–10 sub-instructions | HIGH |
| P2 | ARC bookend instruction | Add equivalent to Baseline and CoT | MEDIUM |
| S8 | One-sided vs harm detection | Add exploratory two-sided test | MEDIUM |

#### Document-Only (Acknowledge as Limitations)

| # | Issue | Documentation |
|---|-------|--------------|
| S2 | H2 underpowered (61%) | Already documented; emphasize CI width over significance |
| S4 | Single-turn limits validity | Pre-register as primary interpretation caveat |
| P1 | Instruction density confound | Pre-register as primary internal validity threat |
| CH7 | Instruction count vs structure | Acknowledge as uncontrolled confound |

---

*The trial never ends, but this protocol is the closest we've come to a fair test. Fix the fatal three, enrich the CoT prompt, and the experiment will produce a result worth believing — whatever that result turns out to be.*

**— Q**
