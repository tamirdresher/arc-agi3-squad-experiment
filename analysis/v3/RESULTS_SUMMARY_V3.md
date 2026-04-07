# ARC-AGI Squad Experiment V3.1 — Results Summary

**Generated:** 2026-04-07T08:41:12.484590
**Total scored runs:** 734

---

## 1. Summary Statistics

### Condition: baseline

| Difficulty | N Runs | Exact Match | Cell Accuracy | Extraction Rate | Mean Tokens |
|-----------|--------|-------------|---------------|-----------------|-------------|
| easy | 85 | 2.4% | 0.755 ± 0.265 | 100.0% | 7299 |
| medium | 84 | 1.2% | 0.657 ± 0.280 | 95.2% | 9128 |
| hard | 76 | 5.3% | 0.546 ± 0.342 | 97.4% | 11507 |

### Condition: chain-of-thought

| Difficulty | N Runs | Exact Match | Cell Accuracy | Extraction Rate | Mean Tokens |
|-----------|--------|-------------|---------------|-----------------|-------------|
| easy | 83 | 2.4% | 0.746 ± 0.282 | 100.0% | 7569 |
| medium | 83 | 0.0% | 0.630 ± 0.300 | 95.2% | 9393 |
| hard | 79 | 3.8% | 0.562 ± 0.348 | 98.7% | 11571 |

### Condition: arc-informed

| Difficulty | N Runs | Exact Match | Cell Accuracy | Extraction Rate | Mean Tokens |
|-----------|--------|-------------|---------------|-----------------|-------------|
| easy | 83 | 0.0% | 0.709 ± 0.310 | 96.4% | 8125 |
| medium | 84 | 2.4% | 0.659 ± 0.276 | 98.8% | 10113 |
| hard | 77 | 3.9% | 0.558 ± 0.353 | 97.4% | 12230 |

---

## 2. Hypothesis Tests

### H1: ARC > Baseline (exact match)

**Fisher's exact test:** p = 0.8071707703559157
  ARC accuracy: 2.0%
  Baseline accuracy: 2.9%

**McNemar's test (majority vote):** p = 1.0

### H2: ARC > CoT (exact match)

**Fisher's exact test:** p = 0.6217835279352879

**McNemar's test (majority vote):** p = 1.0

### H3: Token overhead ≤ 25%

**Paired t-test:** p = 1.4839455358450076e-29
  Mean overhead: 11.776124366534603%

### H4: ARC > Baseline (cell accuracy)

**LMM result:** See GLMM section below.

---

## 3. GLMM Results

```
{
  "model": "GLMM (LMM approximation via mixedlm)",
  "n_observations": 734,
  "n_tasks": 50,
  "summary": "            Mixed Linear Model Regression Results\n=============================================================\nModel:            MixedLM Dependent Variable: exact_match_int\nNo. Observations: 734     Method:             ML             \nNo. Groups:       50      Scale:              0.0127         \nMin. group size:  13      Log-Likelihood:     499.8540       \nMax. group size:  15      Converged:          Yes            \nMean group size:  14.7                                       \n--------------------------------------------------------------\n               Coef.   Std.Err.    z     P>|z|  [0.025  0.975]\n--------------------------------------------------------------\nIntercept       0.021     0.025   0.829  0.407  -0.029   0.071\ncond_cot       -0.008     0.010  -0.807  0.420  -0.028   0.012\ncond_arc       -0.008     0.010  -0.804  0.421  -0.028   0.012\ndiff_medium    -0.004     0.035  -0.111  0.912  -0.073   0.065\ndiff_hard       0.026     0.036   0.735  0.462  -0.044   0.096\nGroup Var       0.010     0.019                               \n=============================================================\n",
  "params": {
    "Intercept": 0.02112423701164688,
    "cond_cot": -0.008204216327869341,
    "cond_arc": -0.008183152011760439,
    "diff_medium": -0.0038926386347773578,
    "diff_hard": 0.026182364601735196,
    "Group Var": 0.7584319191861553
  },
  "pvalues": {
    "Intercept": 0.40694035957207475,
    "cond_cot": 0.4198422866492506,
    "cond_arc": 0.4213485796390478,
    "diff_medium": 0.9116191125620892,
    "diff_hard": 0.46242654591942245,
    "Group Var": 9.145115660180468e-06
  },
  "converged": true
}
```

## 4. LMM (Cell Accuracy) Results

```
{
  "model": "LMM (cell accuracy)",
  "n_observations": 734,
  "summary": "           Mixed Linear Model Regression Results\n===========================================================\nModel:            MixedLM Dependent Variable: cell_accuracy\nNo. Observations: 734     Method:             ML           \nNo. Groups:       50      Scale:              0.0224       \nMin. group size:  13      Log-Likelihood:     255.5062     \nMax. group size:  15      Converged:          Yes          \nMean group size:  14.7                                     \n------------------------------------------------------------\n             Coef.   Std.Err.    z     P>|z|  [0.025  0.975]\n------------------------------------------------------------\nIntercept     0.744     0.066  11.255  0.000   0.615   0.874\ncond_cot     -0.010     0.014  -0.759  0.448  -0.037   0.016\ncond_arc     -0.013     0.014  -0.964  0.335  -0.040   0.013\ndiff_medium  -0.091     0.093  -0.975  0.330  -0.273   0.091\ndiff_hard    -0.177     0.094  -1.873  0.061  -0.361   0.008\nGroup Var     0.072     0.101                               \n===========================================================\n",
  "params": {
    "Intercept": 0.7440951593106742,
    "cond_cot": -0.010280741803198415,
    "cond_arc": -0.013057516233228804,
    "diff_medium": -0.09052286722183599,
    "diff_hard": -0.1766251556508418,
    "Group Var": 3.2004194628538976
  },
  "pvalues": {
    "Intercept": 2.18304534531564e-29,
    "cond_cot": 0.4476493934671728,
    "cond_arc": 0.3351421193358345,
    "diff_medium": 0.3295938730710647,
    "diff_hard": 0.0610679655505247,
    "Group Var": 2.2796771999580933e-06
  },
  "converged": true
}
```

---

## 5. Holm-Bonferroni Correction

| Hypothesis | p-value | Adjusted α | Significant |
|-----------|---------|-----------|-------------|
| H3 (Token overhead) | 0.0000 | 0.0100 | Yes |
| H4-LMM (ARC cell acc) | 0.3351 | 0.0125 | No |
| H1-GLMM (ARC effect) | 0.4213 | 0.0167 | No |
| H2 (ARC > CoT) | 0.6218 | 0.0250 | No |
| H1 (ARC > Baseline) | 0.8072 | 0.0500 | No |

---

*End of report.*