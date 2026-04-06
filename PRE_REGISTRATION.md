# Pre-Registration: ARC-Informed Prompting V2.1

**Pre-Registration Date:** 2026-04-06  
**Pre-Registration Method:** GitHub Release (v2.1-preregistration) + Immutable git tag  
**Status:** Protocol frozen; no modifications permitted after this tag  

---

## What Was Pre-Registered

This document records the pre-registration of the **ARC-Informed Squad Prompting Experiment (V2.1)**.

### Frozen Artifacts

The following are locked at git tag `v2.1-preregistration` and cannot be modified during execution:

1. **Protocol Document:** `EXPERIMENT_V2_PROTOCOL.md`
   - Specifies all 5 hypotheses, counter-hypotheses, task taxonomy, and analysis method
   - Approved by Q (Devil's Advocate review, 2026-04-06)

2. **Task Files:** `tasks/` directory
   - 50 tasks across 10 categories
   - 5 variants per task (difficulty levels)
   - Task sourcing documented in §1 of protocol

3. **Scoring Code:** `scoring/` directory
   - Correctness-gated SHAE calculator
   - Rubric validation

4. **Execution Harness:** `run_experiment.py`
   - CLI configuration
   - Logging and result aggregation

---

## Primary Hypotheses (H1-H5)

| # | Hypothesis | Target |
|---|-----------|--------|
| **H1** | ARC-informed prompting increases correctness vs. baseline | >30% improvement |
| **H2** | ARC-informed prompting reduces hallucination on OOD tasks | Documented reduction |
| **H3** | Chain-of-thought shows measurable improvement but <ARC-informed | CoT intermediate to ARC |
| **H4** | ARC pillar ordering (Explore→Model→Goal→Execute) matters | Permuted order degrades |
| **H5** | Correctness gains hold across task difficulty categories | No category × condition interaction |

---

## Counter-Hypotheses (CH1-CH5)

| # | Counter-Hypothesis | Implication |
|----|-------|-----------|
| **CH1** | Gains due to increased token count, not ARC structure | Compare token usage per condition |
| **CH2** | Gains task-dependent; Category C tasks don't improve | Stratified analysis on C-only tasks |
| **CH3** | Correctness driven by model alone; prompt irrelevant | H0: all conditions equivalent |
| **CH4** | Gains disappear under temperature ≠ 0 | High variance under stochasticity |
| **CH5** | GLMM overfit to task distribution | Poor cross-task generalization |

These counter-hypotheses are documented per Q's devil's advocate review (2026-04-06).

---

## Experiment Design Summary

- **Design:** 3 (condition) × 10 (task category) × 5 (runs) factorial
- **Total Observations:** 750 (correctness outcomes)
- **Conditions:**
  1. Baseline (unstructured prompt)
  2. Chain-of-Thought (structured deliberation)
  3. ARC-informed (4-phase behavioral contract)
- **Task Categories:** Factual retrieval, multi-step debugging, implicit goal detection, etc.

---

## Analysis Method

**Primary Test:** Generalized Linear Mixed Model (GLMM)
- Family: Binomial (logit link)
- DV: correctness (0/1)
- Fixed Effects: condition, task_category, condition × category
- Random Effects: task_id, run_id
- Significance: α = 0.05

**Robustness Tests:**
- McNemar's test on 50 majority-vote outcomes (per Q review)
- Stratified analysis by task category
- Permutation test on counter-hypothesis CH4 (stochasticity sensitivity)

**Effect Size:** Cohen's h (difference of proportions)

---

## Protocol Approval & Review History

| Date | Reviewer | Action | Notes |
|------|----------|--------|-------|
| 2026-03-29 | Picard | Protocol v2.0 drafted | Based on v1 pilot (n=9, exploratory) |
| 2026-03-28→2026-03-30 | Q | Devil's Advocate Review | 10 findings (5 critical, 4 major, 1 minor) |
| 2026-03-30 | Picard | Protocol v2.1 released | All 10 Q findings addressed |
| 2026-04-06 | Q | Second Review (Approval) | ✅ All findings resolved; protocol approved |
| 2026-04-06 | Seven (Docs) | GitHub Release + Tag | Pre-registration finalized |

---

## Commit Hash & Tag

- **Commit:** `7d2d990` (HEAD at pre-registration)
- **Tag:** `v2.1-preregistration` (annotated, signed)
- **GitHub Release:** https://github.com/tamirdresher/arc-agi3-squad-experiment/releases/tag/v2.1-preregistration

---

## Important: Modifications Are Tracked

Any changes to the protocol, tasks, or analysis after this tag must:

1. Be recorded in a new version tag (e.g., `v2.2-preregistration`)
2. Include justification in a decision record
3. Be communicated to Q for approval

This ensures the audit trail of what was pre-registered (v2.1) vs. what was modified post-hoc.

---

## Formal OSF Registration (Planned)

A formal Open Science Framework (https://osf.io) pre-registration is planned as a follow-up.

**Why GitHub Release First?**
- GitHub Release provides an immutable, timestamped, git-backed pre-registration
- Avoids manual form filling on OSF (UI automation complexity)
- GitHub timestamp is globally verifiable via git commit history
- Protocol and tasks are directly linked (no separate archival needed)

**Next Step:** Once experimental execution is complete, results will be compared against this frozen protocol.

---

## Appendix: Key Files

| File | Purpose |
|------|---------|
| `EXPERIMENT_V2_PROTOCOL.md` | Full protocol specification (v2.1) |
| `tasks/` | 50 task files (frozen at tag) |
| `scoring/` | Correctness rubrics and SHAE calculator |
| `run_experiment.py` | Execution harness |
| `.squad/decisions.md` | Team decision records |

---

**Pre-Registration Sealed:** 2026-04-06 06:00 UTC (timestamp on GitHub Release)
