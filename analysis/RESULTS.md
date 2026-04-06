# ARC-AGI-3 Squad Experiment V2.1 — Analysis Results

**Generated:** 2026-04-06 11:44 UTC
**Model:** claude-sonnet-4 (via Copilot CLI)
**Total runs scored:** 750 (50 tasks × 3 conditions × 5 runs)
**Pre-registration tag:** v2.1-preregistration

---

## 1. Descriptive Statistics

### 1.1 Overall Correctness by Condition

| Condition | N | Correct | Rate | Mean CSHAE | Mean Tokens | Mean Wall Clock (s) |
|-----------|---|---------|------|------------|-------------|---------------------|
| baseline | 250 | 245 | **98.0%** | 0.980 | 1082 | 13.6 |
| chain-of-thought | 250 | 250 | **100.0%** | 1.000 | 1100 | 14.5 |
| arc-informed | 250 | 250 | **100.0%** | 1.000 | 1185 | 15.6 |

### 1.2 Correctness by Meta-Category

| Meta-Cat | Baseline | CoT | ARC-Informed |
|----------|----------|-----|--------------|
| **A** (25 tasks) | 120/125 (96.0%) | 125/125 (100.0%) | 125/125 (100.0%) |
| **B** (15 tasks) | 75/75 (100.0%) | 75/75 (100.0%) | 75/75 (100.0%) |
| **C** (10 tasks) | 50/50 (100.0%) | 50/50 (100.0%) | 50/50 (100.0%) |

### 1.3 Correctness by Task Type

| Type | Description | Baseline | CoT | ARC |
|------|-------------|----------|-----|-----|
| A1 | Factual Comprehension | 100% | 100% | 100% |
| A2 | Multi-Step Debugging | 100% | 100% | 100% |
| A3 | Implicit Goal Detection | 100% | 100% | 100% |
| A4 | Multi-Constraint Optimization | 100% | 100% | 100% |
| A5 | Ambiguous Specification | 80% | 100% | 100% |
| B1 | Time-Sensitive Retrieval | 100% | 100% | 100% |
| B2 | Creative/Generative | 100% | 100% | 100% |
| B3 | Adversarial Misdirection | 100% | 100% | 100% |
| C1 | HumanEval+ | 100% | 100% | 100% |
| C2 | SWE-bench Lite | 100% | 100% | 100% |

## 2. GLMM Analysis

**Model specification:** `correct ~ condition + (1|task_id)` (Bernoulli GLMM)

**Status:** GLMM fitted via Variational Bayes (BinomialBayesMixedGLM)

| Coefficient | Estimate | SE | z | p-value | OR | 95% CI |
|-------------|----------|----|----|---------|-----|---------|
| intercept | 6.427 | 0.494 | — | — | — | — |
| cot_vs_baseline | 3.296 | 1.163 | 2.833 | 0.0046 | 26.998 | [2.761, 263.999] |
| arc_vs_baseline | 3.296 | 1.163 | 2.833 | 0.0046 | 26.998 | [2.761, 263.999] |

## 3. Fisher's Exact Test (Robustness)

| Comparison | Table | OR | p-value | Significant (α=0.05)? |
|------------|-------|-----|---------|----------------------|
| H1_arc_vs_baseline | [[250, 0], [245, 5]] | inf | 0.0306 | Yes |
| H2_arc_vs_cot | [[250, 0], [250, 0]] | inf | 1.0000 | No |
| H3_cot_vs_baseline | [[250, 0], [245, 5]] | inf | 0.0306 | Yes |

## 4. McNemar's Test on Majority-Vote (Robustness)

| Comparison | Discordant (wins) | p-value | Significant? |
|------------|-------------------|---------|-------------|
| H1_arc_vs_baseline | 1 vs 0 (n=1) | 1.0000 | No |
| H2_arc_vs_cot | 0 vs 0 (n=0) | 1.0000 | No |
| H3_cot_vs_baseline | 1 vs 0 (n=1) | 1.0000 | No |

## 5. Efficiency Analysis (H3)

| Metric | Baseline | CoT | ARC |
|--------|----------|-----|-----|
| Mean tokens | 1082 | — | 1185 |
| Mean wall clock (s) | 13.6 | 14.5 | 15.6 |
| Overhead vs baseline | — | — | 9.5% |

## 6. Hypothesis Verdicts

| Hypothesis | Prediction | Observed | Verdict |
|------------|------------|----------|---------|
| **H1** | ARC-informed > Baseline (correctness) by ≥15pp | Observed 2.0pp difference (100.0% vs 98.0%). Statistically s | **NOT SUPPORTED** |
| **H2** | ARC-informed > CoT (correctness) by ≥10pp | Observed 0.0pp difference. Both conditions at ceiling (100.0 | **NOT SUPPORTED** |
| **H3** | ARC ≤ 10% more actions/tokens than Baseline | ARC overhead: 9.5% more tokens (1185 vs 1082). Within the 10 | **SUPPORTED** |
| **H4** | ARC advantage larger on hard/far-OOD tasks (≥2× easy gap) | Hard gap: 0.0pp, Easy gap: 0.0pp. Ceiling effect prevents me | **NOT SUPPORTED** |
| **H5** | ARC ≥ Baseline - 5pp on adversarial (B) tasks | ARC 100.0% vs Baseline 100.0% on B-tasks (diff: 0.0pp). With | **SUPPORTED** |

### H1: ARC-informed > Baseline (correctness) by ≥15pp

**Verdict: NOT SUPPORTED**

Observed 2.0pp difference (100.0% vs 98.0%). Statistically significant (p=0.0306). Ceiling effect: model is too capable for task difficulty.

### H2: ARC-informed > CoT (correctness) by ≥10pp

**Verdict: NOT SUPPORTED**

Observed 0.0pp difference. Both conditions at ceiling (100.0% vs 100.0%). No evidence ARC-specific structure adds value beyond generic CoT.

### H3: ARC ≤ 10% more actions/tokens than Baseline

**Verdict: SUPPORTED**

ARC overhead: 9.5% more tokens (1185 vs 1082). Within the 10% threshold.

### H4: ARC advantage larger on hard/far-OOD tasks (≥2× easy gap)

**Verdict: NOT SUPPORTED**

Hard gap: 0.0pp, Easy gap: 0.0pp. Ceiling effect prevents meaningful comparison.

### H5: ARC ≥ Baseline - 5pp on adversarial (B) tasks

**Verdict: SUPPORTED**

ARC 100.0% vs Baseline 100.0% on B-tasks (diff: 0.0pp). Within non-inferiority margin.

## 7. Ceiling Effect Analysis

The most striking finding is the **near-perfect correctness** across all conditions:

- Baseline: 98.0%
- CoT: 100.0%
- ARC-informed: 100.0%

This represents a **ceiling effect**: the model (claude-sonnet-4) is sufficiently capable that it achieves near-perfect performance even without structured reasoning prompts. The 50-task battery, while diverse, does not push the model to its limits.

**Implications:**
1. The GLMM is poorly powered to detect differences near the ceiling (floor effects in failure counts)
2. The predicted 15pp (H1) and 10pp (H2) effects are unsupported — not because ARC is unhelpful, but because the baseline is already excellent
3. The structured reasoning contract (ARC) does not *hurt* performance (H5 supported)
4. A harder task battery is needed to differentiate conditions meaningfully

## 8. Counter-Hypothesis Assessment

| CH | Assessment |
|----|-----------|
| CH1 (Prompt-length) | Moot — no meaningful correctness difference to explain |
| CH2 (Structural formatting) | Moot — ceiling effect prevents assessment |
| CH3 (Training data contamination) | Cannot be assessed with this data |
| CH4 (Evaluator structural bias) | N/A — automated scoring used |
| CH5 (Meta-A dominance) | Only T21 failures observed; all in Meta-A under baseline |
