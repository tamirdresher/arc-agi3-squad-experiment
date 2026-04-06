# Q's Fact Check — V3 ARC-AGI Experiment Protocol

**Reviewer:** Q (Devil's Advocate & Fact Checker)  
**Document Under Review:** `EXPERIMENT_V3_PROTOCOL.md` v3.0  
**Author:** Picard  
**Date:** 2026-04-09  
**Review Date:** 2026-04-09  
**Supporting Reference:** Seven's `ARC_AGI_DATASET_REFERENCE.md`

---

## VERDICT: ❌ NEEDS REVISION

**Claims verified:** 28  
**Issues found:** 8 (2 CRITICAL, 3 IMPORTANT, 3 MINOR)

The protocol is well-structured and shows strong improvement from V2.1 in automated scoring, reproducibility, and counter-hypothesis design. However, it contains a **critical baseline calibration error** that, if uncorrected, risks a repeat of the V2.1 ceiling-effect disaster — the exact scenario this redesign was meant to prevent.

---

## Issue 1: CRITICAL — Baseline Accuracy Estimate Is Wrong by 2×

### The Claim (Protocol §0.1, line 26)
> "Claude Sonnet 4 scores ~25–40% on ARC-AGI-1 training tasks (estimated from published benchmarks: Claude 3.5 Sonnet ~14% on ARC-AGI evaluation, training set is easier)"

### The Evidence

| Source | Claim | Status |
|--------|-------|--------|
| Protocol §0.1 | Claude Sonnet 4 baseline ~25–40% on ARC-AGI-1 | ❌ **Contradicted** |
| Seven's research §2 (line 71) | ARC-AGI-1 "Saturated (most modern LLMs score >90%)" | ⚠️ **Overstated for Claude Sonnet specifically, accurate for top models** |
| Seven's research §4 (lines 177-179) | "Frontier LLMs: 90%+ (dataset is saturated)" | ✅ Verified for GPT-5.4 (93.7%), overstated for Claude Sonnet |
| Seven's research §7 (line 412) | "Avoid: ARC-AGI-1 training set (too easy, saturated)" | ✅ **Verified — correct recommendation** |
| ARC Prize leaderboard (arcprize.org) | Claude Sonnet 4.6: ~60% on ARC-AGI-1 | ✅ Verified via multiple sources |
| llm-stats.com, morphllm.com, benchlm.ai | Claude Sonnet 4/4.6: 60-61% ARC-AGI-1 (eval); up to 86.5% in high-compute settings | ✅ Verified |
| llm-stats.com | GPT-5.4: 93.7% on ARC-AGI-1 | ✅ Verified |
| d3alpha.com | "ARC-AGI-1 Saturated at 95%" (headline, 2025-2026) | ✅ Verified for top models |

### Analysis

Picard extrapolated from **2024 data** (Claude 3.5 Sonnet ~14% on ARC-AGI eval) to estimate Claude Sonnet 4 at ~25-40%. This extrapolation is wrong by a factor of roughly 2×. The actual Claude Sonnet 4/4.6 performance on ARC-AGI-1 is approximately **60%**, verified across multiple independent leaderboards.

**Who is right — Seven or Picard?** Neither is precisely right, but **Seven is much closer to correct and gives the right recommendation**:
- Seven's "90%+" claim is accurate for top frontier models (GPT-5.4 at 93.7%) but overstates Claude Sonnet's specific performance
- Picard's "25-40%" is dangerously wrong — the actual value is ~60%
- Seven's recommendation to use ARC-AGI-2 and avoid ARC-AGI-1 is **correct and should be followed**

### Impact on the Protocol

At a **60% baseline** (not 30%):
- The power analysis (§3.3) is invalid — it assumes baseline 30% (logit = −0.847) but reality is 60% (logit = +0.405)
- The expected effect of 15pp (30%→45%) becomes implausible at 60%→75%
- **Easy tasks will almost certainly ceiling** — the protocol expects easy tasks at ~50-70% but they likely score 80-90%+
- The stopping rule for futility (§3.7) checks for <5% floor effects but has **no ceiling-effect stopping rule** — the EXACT failure mode from V2.1
- The contamination risk (CH6) is massively amplified — ARC-AGI-1 training set has been public for 7 years

### Moreover: The Training Set Is Likely Easier Than Evaluation

The ~60% figure is from leaderboards that typically test on evaluation/private sets. The training set — which this protocol uses — is generally **easier** because it's been used for algorithm development. Claude Sonnet's accuracy on ARC-AGI-1 training tasks could be **65-75% or higher**, further reducing headroom.

### Recommended Fix

**Switch to ARC-AGI-2 evaluation set (120 tasks).** This is exactly what Seven's research recommends (§7):
- Claude Sonnet 4.6 scores **58.3%** on ARC-AGI-2 — verified, well-calibrated
- Much lower contamination risk (released 2025 vs 2019)
- Difficulty-calibrated by human testing
- Active benchmark with ongoing community engagement
- Provides the ~40-60% baseline range needed for measurement headroom

If ARC-AGI-2 is used, select 40 tasks from the 120 public evaluation tasks using human-difficulty calibration instead of the ad-hoc proxy metrics in §1.3.

**Alternatively:** If ARC-AGI-1 must be kept, run a mandatory 5-task pilot per difficulty tier FIRST to empirically measure baseline accuracy before committing to full execution. If pilot baseline exceeds 60%, abort and switch to ARC-AGI-2. This escape hatch must be pre-registered.

---

## Issue 2: CRITICAL — No Ceiling-Effect Stopping Rule

### The Claim (Protocol §3.7)
The stopping rules include:
- No early stopping for efficacy
- Early stopping for **futility** (floor effect) at <5%
- Sample size increase for H2

### What's Missing

There is **NO ceiling-effect stopping rule**. The protocol checks for a floor (<5% accuracy) but not a ceiling (>80% accuracy). This is the EXACT failure mode that destroyed V2.1 (baseline 98%, no room for improvement).

Given Issue 1 (baseline likely ~60%+), this omission is not merely theoretical — it is the most probable failure mode.

### Recommended Fix

Add to §3.7:

> **Early stopping for ceiling effect:** If after 10 tasks (50 runs per condition), the Baseline condition shows >70% exact-match accuracy, we pause execution and convene a protocol amendment. Options: (a) switch to ARC-AGI-2, (b) restrict to medium/hard tasks only, (c) document the finding and redesign. This threshold is based on the lesson from V2.1 where >80% baseline rendered the experiment uninformative.

**Severity: CRITICAL** — Without this, the team risks burning another 600 runs for a null result.

---

## Issue 3: IMPORTANT — Prompt Length Confound Is Acknowledged But Not Controlled

### The Claim (Protocol §3.8, CH1 and CH3)
The protocol acknowledges the ARC prompt is ~150 tokens longer than Baseline and proposes a "pre-registered length-matched follow-up" as mitigation.

### Analysis

The three prompts differ substantially in instructional content:

| Condition | System Prompt | User Instructions (beyond grid data) | Total Extra Tokens (est.) |
|-----------|--------------|--------------------------------------|--------------------------|
| Baseline | ~20 words | ~30 words ("Output ONLY the JSON...") | Reference |
| CoT | ~15 words | ~80 words (4 reasoning steps) | +~50 tokens |
| ARC | ~35 words | ~200 words (4 labeled phases with specific grid-analysis instructions) | +~170 tokens |

The ARC prompt is **3-4× longer** in instructional content than Baseline (not counting shared grid data). This is not a minor difference. Research consistently shows that more detailed instructions improve LLM performance regardless of framework specificity.

Critically: **Baseline tells the model "Output ONLY the JSON array, nothing else"** — explicitly suppressing any chain-of-thought. This creates a confound where Baseline is actively handicapped, not just unassisted. CoT and ARC both allow reasoning before answering.

### Counter-Hypothesis Not Tested

CH1 and CH3 overlap confusingly and both defer to "follow-up studies." The actual experiment has NO in-protocol control for prompt length. A length-matched baseline (one that adds padding text or generic reasoning instructions of equal length) would be a much stronger control.

### Recommended Fix

Either:
1. Add a 4th condition: "Length-Matched Baseline" that includes ~170 tokens of generic instructions (e.g., "Think carefully about each example. Consider what patterns might exist. Take your time.") — same length as ARC but without the specific 4-pillar structure. This directly tests whether framework specificity matters.
2. OR: At minimum, remove the "Output ONLY the JSON" instruction from Baseline and instead use "After considering the puzzle, provide the output grid as a JSON array of arrays. Mark your final answer with 'ANSWER:'" — making the output format consistent across all conditions.

**Severity: IMPORTANT** — Without this, a positive result for ARC vs. Baseline could be entirely explained by prompt length and reasoning permission, not the 4-pillar framework.

---

## Issue 4: IMPORTANT — Difficulty Stratification Uses Untested Proxy Metrics

### The Claim (Protocol §1.3)
Difficulty is assigned using objective proxy features: max grid dimension, unique color count, number of training examples, and size ratio.

### Analysis

These proxies are reasonable intuitions but are **not validated** against actual model performance. A 5×5 grid with 2 colors could involve a fiendishly complex transformation rule (e.g., cellular automaton), while a 20×20 grid with 8 colors might involve a trivial pattern (e.g., flood fill). The proxies measure **surface complexity**, not **reasoning difficulty**.

Seven's research (§7) explicitly recommends using **human accuracy data** for difficulty calibration:
> "Tasks are ranked by human accuracy (% of participants who solved all test pairs correctly in ≤2 attempts)"

ARC-AGI-2 has this human calibration data available. ARC-AGI-1 training set does not have standardized human accuracy scores.

### Recommended Fix

If switching to ARC-AGI-2 (as recommended in Issue 1), use the published human accuracy data for stratification instead of proxy metrics. If staying with ARC-AGI-1, run a pilot with 5 tasks per proposed tier and validate that the tiers actually differ in model accuracy before committing the full selection.

**Severity: IMPORTANT** — Misclassified difficulty tiers weaken the stratified analysis and could mask interaction effects.

---

## Issue 5: IMPORTANT — Contamination Risk for ARC-AGI-1 Is Underestimated

### The Claim (Protocol §3.8, CH6; §10, L2)
The protocol acknowledges contamination risk but argues: (a) models see JSON grids without task IDs, (b) compare frequently vs. infrequently discussed tasks, (c) flag if baseline >60%.

### Analysis

ARC-AGI-1 training tasks have been public since **2019** — 7 years of exposure. They appear in:
- Hundreds of research papers analyzing specific tasks
- Blog posts with step-by-step solutions
- Training data for frontier models (Anthropic, OpenAI, Google all scrape academic papers)
- GitHub repositories with solved implementations

The mitigations are weak:
- **(a)** "No task IDs" — But the grid patterns themselves are memorizable. If the model has seen `[[1,0,0,5,0,1,0], ...]` in training data alongside its solution, it can pattern-match regardless of task IDs.
- **(b)** "Compare frequently vs. infrequently discussed" — How do you measure discussion frequency? This is undefined and may not capture training data contamination.
- **(c)** "Flag if baseline >60%" — This threshold is already below the actual expected baseline (~60%). It provides no meaningful signal.

### Recommended Fix

1. **Primary: Switch to ARC-AGI-2** (released 2025, drastically reduced contamination window)
2. If keeping ARC-AGI-1: Run a contamination detection test — present the model with partial task data (first training pair only) and see if it can predict subsequent training pairs. Tasks where the model "knows" the pattern from partial data are contaminated.
3. Raise the contamination flag threshold from 60% to 75%.

**Severity: IMPORTANT** — Contamination inflates baseline artificially, masking any framework effect and undermining internal validity.

---

## Issue 6: MINOR — CH1 and CH3 Are Redundant

### The Claim (Protocol §3.8)
CH1: "Prompt length confound. The ARC prompt is ~150 tokens longer..."
CH3: "Prompt length effect (distinct from CH1). The ARC prompt is specifically longer for grid tasks..."

### Analysis

These are the same hypothesis with slightly different framing. CH1 says "longer prompts may elicit more careful processing." CH3 says "length correlates with task complexity." Both are about prompt length driving results. The distinction between "careful processing from length" and "length correlating with complexity" is not meaningful — they test the same confound.

### Recommended Fix

Merge CH1 and CH3 into a single counter-hypothesis. Use the freed slot for a new counter-hypothesis: **CH_new: Output format confound** — Baseline instructs "Output ONLY the JSON array, nothing else" which suppresses reasoning, while CoT/ARC permit reasoning before answering. This format difference, independent of prompt length or framework content, could explain performance differences.

**Severity: MINOR** — Doesn't affect experiment validity, but cleaning up the counter-hypotheses improves clarity.

---

## Issue 7: MINOR — Output Extraction Edge Cases

### The Claim (Protocol §5.2)
The extraction code (a) looks for "ANSWER:" marker, then (b) finds the last valid JSON array of arrays.

### Analysis

The extraction logic is well-designed for the common case. Two edge cases:

1. **Training example grids in reasoning:** In CoT and ARC conditions, the model may reproduce training example grids verbatim in its reasoning (e.g., "In Example 1, the input was [[1,0,0,5,...]]"). The "last valid JSON array" heuristic handles this correctly — but what if the model states the answer FIRST and then verifies against training examples AFTER? This would cause the extractor to pick a training grid instead of the answer.

2. **Trailing commas / slightly malformed JSON:** `json.loads` is strict — `[[1,2,3,],]` will fail. LLMs occasionally produce such output. Consider adding a pre-processing step to strip trailing commas.

### Recommended Fix

1. For edge case 1: Add a validation step — if the extracted grid exactly matches any training input or output grid, flag it for manual review (likely extraction error, not a real answer).
2. For edge case 2: Add a JSON repair step before `json.loads` (strip trailing commas, fix common formatting issues).

**Severity: MINOR** — Extraction failure is logged and reported per condition. These are low-probability edge cases, but easy to fix preemptively.

---

## Issue 8: MINOR — H2 Power Is Borderline and the Increase Rule May Not Trigger

### The Claim (Protocol §3.3, §3.7)
H2 power is 67% (borderline). The sample size increase rule adds 10 tasks if interim power <65%.

### Analysis

67% power means a ~1/3 chance of missing a real 10pp effect. The mitigation (add 10 tasks if interim power <65%) is sound in principle but:
- "Interim power estimate at 20 tasks" requires estimating the effect size from partial data, which is notoriously unreliable
- If the interim estimate happens to be 66% (just above threshold), the rule doesn't trigger even though power remains inadequate
- The 65% threshold is arbitrary and close to the expected 67%

### Recommended Fix

Start with 50 tasks (not 40) to push H2 power above 80% from the outset. The marginal cost is 150 additional runs (50 × 3 conditions × 1 extra run... actually no, it's 10 extra tasks × 3 × 5 = 150 extra runs). At $0 per run, cost is not a constraint. The only cost is time.

**Severity: MINOR** — The sample size increase rule partially addresses this, but starting with adequate power is always better than hoping to detect inadequacy mid-experiment.

---

## Counter-Hypotheses Tested by Q

### CH-Q1: "The 60% baseline renders the experiment uninformative"
**Result:** ⚠️ Not necessarily. At 60% baseline, there IS room for improvement (unlike V2.1's 98%). But the protocol's power analysis, effect size predictions, and difficulty stratification are all calibrated for 30% — a 2× error. The experiment could still work if recalibrated, but running it as-written risks wasted effort on the easy tier.

### CH-Q2: "ARC-AGI-1 contamination inflates Baseline more than ARC condition"
**Result:** ⚠️ Plausible. If the model has memorized solutions from training data, all conditions benefit — but Baseline benefits MOST because the model can shortcut directly to the answer without needing to reason through the framework. The ARC condition's mandatory phases may actually slow down memorized retrieval, creating a paradox where contamination makes the framework look WORSE.

### CH-Q3: "The 4-pillar framework helps because it forces reasoning, not because of ARC-specific content"
**Result:** This is partially tested by CH5 (sham framework follow-up), but the follow-up is not part of V3 itself. Within V3, this cannot be distinguished. The CoT condition provides a partial control, but CoT is weaker than a length-matched structured baseline.

### CH-Q4: "Copilot CLI injects hidden system prompts that interact differently with the three conditions"
**Result:** ⚠️ Unverifiable. The protocol acknowledges this (L4) and relies on the within-subjects design. Acceptable risk given the constraint.

---

## Section 9 — Picard's Six Questions: Q's Verdicts

### Q1: No human scoring — is automated exact-match sufficient?
**Verdict: ✅ ACCEPTABLE.** Exact grid match is the gold standard for ARC-AGI scoring. It is objective, deterministic, and eliminates all scorer bias concerns from V2.1. An LLM-as-judge for failure mode analysis would add insight but is not necessary for primary/secondary hypotheses. Keep it as an optional post-hoc analysis.

### Q2: 40 tasks vs. 50 — is the starting N sufficient?
**Verdict: ⚠️ CONDITIONAL.** At 30% baseline, 40 tasks give 88% power for H1 — adequate. But the baseline is wrong (likely ~60%), so the power analysis must be redone. Additionally, H2 power at 67% is borderline. **Recommendation: Start with 50 tasks to ensure adequate power for both H1 and H2, especially given baseline uncertainty.** Cost is negligible.

### Q3: Single-turn only — does this underestimate ARC's value?
**Verdict: ✅ ACCEPTABLE for V3.** Single-turn is the simplest and most controlled design. Multi-turn introduces confounds (feedback quality, iterative strategy differences). Plan V3.1 with multi-turn as a follow-up if V3 shows promising results. The limitation is correctly acknowledged in L6.

### Q4: Difficulty assignment by author-defined thresholds — should an independent party set them?
**Verdict: ✅ ACCEPTABLE IF pre-registered.** The thresholds are based on objective metrics (grid dimensions, colors, training examples), not subjective judgment. As long as they're frozen before any runs, author-defined is fine. Independent validation would be ideal but adds coordination overhead. **Stronger recommendation: If switching to ARC-AGI-2, use human-accuracy-calibrated difficulty tiers instead of proxy metrics (see Issue 4).**

### Q5: ARC-AGI-1 vs. ARC-AGI-2 — is ARC-AGI-1 acceptable?
**Verdict: ❌ NO. Switch to ARC-AGI-2.** This is the central finding of this review. ARC-AGI-1 is saturated for top models (90%+), and even Claude Sonnet 4 scores ~60% — double the protocol's assumed 25-40%. Contamination risk is severe (7 years of public exposure). Seven's research explicitly and correctly recommends ARC-AGI-2. The protocol's own §9.5 pre-registers concern about >60% baseline — this threshold is already at or below the actual expected baseline. **ARC-AGI-2 provides: similar difficulty for Claude Sonnet (~58%), lower contamination, human-calibrated difficulty, active benchmark status. There is no defensible reason to prefer ARC-AGI-1.**

### Q6: Exploratory ASCII representation (10 tasks) — worth the extra runs?
**Verdict: ✅ ACCEPTABLE.** 30 extra runs at $0 cost is trivial. It directly tests CH4 (representation effect) and could inform future protocol design. Keep it as a pre-registered exploratory analysis, reported separately. Do NOT let it delay the primary analysis.

---

## Full Claim Verification Table

| # | Claim | Status | Evidence/Notes |
|---|-------|--------|---------------|
| 1 | Claude Sonnet 4 baseline ~25-40% on ARC-AGI-1 | ❌ Contradicted | Actual: ~60% (arcprize.org, llm-stats.com, morphllm.com) |
| 2 | Claude 3.5 Sonnet ~14% on ARC-AGI evaluation | ⚠️ Outdated | Was accurate for 2024; irrelevant for Claude Sonnet 4 in 2026 |
| 3 | ARC-AGI-1 training set is easier than evaluation | ✅ Verified | Standard assumption in ARC community; training used for development |
| 4 | 400 public training tasks with ground truth | ✅ Verified | github.com/fchollet/ARC-AGI/tree/master/data/training |
| 5 | Grids are 1×1 to 30×30, integers 0-9 | ✅ Verified | Matches ARC-AGI specification |
| 6 | 2-5 training examples per task | ✅ Verified | Matches Seven's research and ARC-AGI docs |
| 7 | GLMM with task random intercept appropriate | ✅ Verified | Correct for binary outcome with repeated measures within tasks |
| 8 | Power 88% for H1 at 30% baseline | ⚠️ Unverifiable | Simulation code not provided; plausible parameters but baseline is wrong |
| 9 | ICC 0.4 reasonable for ARC tasks | ✅ Verified | Higher than V2.1's 0.3; justified by greater intrinsic difficulty variation |
| 10 | Holm-Bonferroni correction for 5 hypotheses | ✅ Verified | Standard, appropriate MCC method |
| 11 | Exact grid match is standard ARC-AGI scoring | ✅ Verified | Matches official ARC Prize rules |
| 12 | Cell accuracy captures partial correctness | ✅ Verified | Valid secondary metric; well-implemented |
| 13 | Scoring code is deterministic | ✅ Verified | Pure function, no randomness |
| 14 | Output extraction handles ANSWER: marker | ✅ Verified | Code provided, logic is sound |
| 15 | ARC-AGI-1 training set public since 2019 | ✅ Verified | Original paper: Chollet 2019, arxiv 1911.01547 |
| 16 | ARC-AGI-2 released 2025 | ✅ Verified | Seven's research §2, ARC Prize website |
| 17 | 600 total runs (40×3×5) | ✅ Verified | Arithmetic correct |
| 18 | $0 cost via Copilot CLI | ✅ Verified | Included in GitHub Copilot subscription |
| 19 | Claude Sonnet 4.6 scores 58.3% on ARC-AGI-2 | ✅ Verified | Seven's research, arcprize.org leaderboard, llm-stats.com |
| 20 | Seven recommends ARC-AGI-2 over ARC-AGI-1 | ✅ Verified | Seven's §7: "Use ARC-AGI-2... Avoid: ARC-AGI-1 training set" |
| 21 | Token overhead ≤25% (H3) threshold | ⚠️ Unverified | Plausible but untested; depends on grid data size vs. instruction size |
| 22 | Exploratory ASCII uses 30 runs (10×3×1) | ✅ Verified | Arithmetic correct |
| 23 | Run ordering is deterministic (seed 7) | ✅ Verified | Code provided, reproducible |
| 24 | Timeout 300 seconds per invocation | ✅ Verified | Reasonable for single-turn LLM call |
| 25 | Retry policy: 3 retries, exponential backoff | ✅ Verified | Standard practice |
| 26 | ARC-AGI-1 GitHub URL valid | ✅ Verified | github.com/fchollet/ARC-AGI exists |
| 27 | ARC-AGI task format (JSON train/test) | ✅ Verified | Matches Seven's research and official docs |
| 28 | McNemar's test as secondary/robustness check | ✅ Verified | Appropriate for paired binary outcomes on majority-vote |

---

## Summary of Required Changes

### Before Approval (Must Fix)

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | **CRITICAL** | Baseline estimate wrong (25-40% vs actual ~60%) | Switch to ARC-AGI-2 OR recalibrate with empirical pilot |
| 2 | **CRITICAL** | No ceiling-effect stopping rule | Add ceiling check at >70% after 10 tasks |

### Strongly Recommended (Should Fix)

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 3 | **IMPORTANT** | Prompt length/format confound uncontrolled | Equalize output format instructions across conditions; consider length-matched 4th condition |
| 4 | **IMPORTANT** | Difficulty stratification uses unvalidated proxies | Use human-calibrated difficulty (available in ARC-AGI-2) |
| 5 | **IMPORTANT** | Contamination risk underestimated for ARC-AGI-1 | Switch to ARC-AGI-2; or add contamination detection test |

### Nice to Have (Optional)

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 6 | MINOR | CH1 and CH3 redundant | Merge; add output-format confound as new CH |
| 7 | MINOR | Output extraction edge cases | Add training-grid filter + JSON repair |
| 8 | MINOR | H2 power borderline at 67% | Start with 50 tasks instead of 40 |

---

## Decision for Team

I am writing this to the decisions inbox because the dataset choice affects the entire team's experiment timeline.

**The trial's verdict is clear:** ARC-AGI-1 is the wrong dataset for 2026. Seven's research got this right. Picard's baseline estimate is based on obsolete 2024 data. The protocol must switch to ARC-AGI-2 or demonstrate via empirical pilot that ARC-AGI-1 provides adequate measurement headroom. Without this change, I cannot approve V3 for execution.

---

*The trial never ends. Every claim deserves scrutiny. Not because I doubt the crew — but because the truth is always worth finding.*

**— Q**
