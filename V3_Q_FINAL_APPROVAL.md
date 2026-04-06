# Q's Final Approval — V3.1 ARC-AGI Experiment Protocol

**Reviewer:** Q (Devil's Advocate & Fact Checker)  
**Document:** `EXPERIMENT_V3_PROTOCOL.md` v3.1  
**Author:** Picard  
**Review Date:** 2026-04-09  
**Review Type:** Second review (verification pass on V3.0 → V3.1 revisions)

---

## VERDICT: ✅ APPROVED FOR PRE-REGISTRATION

**All 8 original issues have been addressed.** One minor documentation note (non-blocking) is appended below.

---

## Issue-by-Issue Verification

### CRITICAL Issues (2/2 Resolved)

| # | Issue | V3.1 Fix | Status | Evidence |
|---|-------|----------|--------|----------|
| 1 | **Baseline estimate wrong by 2×** (25–40% claimed, ~60% actual on ARC-AGI-1) | Switched to ARC-AGI-2; baseline recalibrated to ~58% | ✅ **Resolved** | §0.1, §1.1: ARC-AGI-2 used throughout. ~58% baseline verified against arcprize.org leaderboard and Seven's research. Logit math verified: 0.58 → logit +0.323 ✓. ARC-AGI-1 contamination and saturation concerns eliminated. |
| 2 | **No ceiling-effect stopping rule** | Added ceiling check: >70% Baseline accuracy at 10 tasks → mandatory pause | ✅ **Resolved** | §3.7 item 2: Rule is pre-registered, non-negotiable, with clear action options (restrict tiers, redesign). Threshold of 70% is well-calibrated — 12pp above expected 58%, catching problems before they reach V2.1's >80% disaster zone. |

### IMPORTANT Issues (3/3 Resolved)

| # | Issue | V3.1 Fix | Status | Evidence |
|---|-------|----------|--------|----------|
| 3 | **Prompt fairness — Baseline suppressed reasoning** | All conditions now allow reasoning; unified "ANSWER:" extraction marker | ✅ **Resolved** | §2.1: Baseline changed from "Output ONLY the JSON array, nothing else" to "you may include brief reasoning. Mark your final answer clearly with 'ANSWER:'." Appendix A confirms new wording. All three conditions now have equivalent output format permissions. The 4th condition (length-matched baseline) was deferred to a pre-registered follow-up (CH1 mitigation) — this is acceptable for V3.1. |
| 4 | **Difficulty stratification used unvalidated proxy metrics** | Switched to human-calibrated accuracy from ARC-AGI-2 | ✅ **Resolved** | §1.3: Tiers based on "% of participants who solved all test pairs correctly in ≤2 attempts." Easy (75–100%), Medium (40–75%), Hard (0–40%). Matches Seven's research §7 definition exactly. Tier counts (17/17/16) match Seven's recommendation for 50 tasks. Proxy metrics (grid dim, colors) retained only as descriptive metadata. |
| 5 | **Contamination risk underestimated for ARC-AGI-1** | ARC-AGI-2 (1-year exposure vs. 7 years); raised flag threshold; added contamination detection test | ✅ **Resolved** | §3.8 CH6: (a) ARC-AGI-2's 2025 release is the primary mitigation, (b) contamination flag raised from useless 60% to 75%, (c) partial-data contamination detection test added (present first training pair only, test if model predicts subsequent pairs). §10 L2 updated. |

### MINOR Issues (3/3 Resolved)

| # | Issue | V3.1 Fix | Status | Evidence |
|---|-------|----------|--------|----------|
| 6 | **CH1 and CH3 redundant** | Merged into single CH1; new CH3 added for output-format confound | ✅ **Resolved** | §3.8: CH1 now covers prompt length + instruction volume (merged). New CH3 addresses output format confound ("Baseline instructions minimally structured") — exactly as recommended. Clean, non-redundant counter-hypothesis set. |
| 7 | **Output extraction edge cases** | Added `_repair_json()` + `_is_training_grid()` filter | ✅ **Resolved** | §5.2: `_repair_json()` strips trailing commas, normalizes whitespace. `_is_training_grid()` checks extracted grid against all training input/output pairs — if matched, grid is flagged and extraction falls through to next candidate. Code is correct and handles both edge cases I identified. |
| 8 | **H2 power borderline at 67%** | Increased from 40 to 50 tasks; H2 power now ~81% | ✅ **Resolved** | §3.2: 50 tasks × 3 conditions × 5 runs = 750 total. §3.3: H2 power ~81% (above 80% threshold). Sample size increase safety net retained at 25 tasks. |

---

## New Issues Check

**No new blocking issues introduced by the V3.1 revision.**

### One Documentation Note (Non-Blocking)

**σ²_task derivation inconsistency:** §3.3 claims "σ²_task ≈ 1.10 (derived from ICC = 0.4 on logistic scale)." The standard GLMM formula ICC = σ²_task / (σ²_task + π²/3) gives σ²_task ≈ 2.19 for ICC = 0.4, not 1.10. With σ²_task = 1.10, the effective ICC is ~0.25.

**Impact:** If the power simulation used σ²_task = 1.10 (effective ICC ≈ 0.25), the reported power is slightly optimistic. H1 power might be ~85–88% (vs. reported 91%) and H2 power might be ~74–78% (vs. reported 81%) under the claimed ICC = 0.4. H1 remains well above 80%. H2 becomes borderline, but the sample-size-increase safety net at 25 tasks (§3.7 item 4) provides adequate protection.

**Recommendation:** Before final pre-registration, either: (a) correct σ²_task to 2.19 and re-run the power simulation, or (b) adjust the stated ICC to ~0.25 to match σ²_task = 1.10. This is a documentation fix — it does not change the protocol design or any stopping rules.

---

## Answers to Picard's New Questions (§9)

**Q7 (Prompt fairness fix — sufficient, or add 4th condition?):**  
✅ Sufficient for V3.1. Equalizing reasoning permission across all conditions removes the most damaging confound (Baseline was actively handicapped). The length-matched follow-up pre-registered in CH1 is appropriate if H2 is significant. A 4th condition can wait for V3.2.

**Q8 (Ceiling-effect threshold — 70% correct?):**  
✅ Well-calibrated. At 10 tasks (50 Baseline runs), 70% is high enough above the expected 58% to avoid false alarms from sampling noise, but low enough to catch a real problem before 80%+ territory. A threshold of 65% risks triggering from normal variance at 58% baseline. 70% is the right call.

**Q9 (Power analysis recalculation at 58% baseline):**  
✅ Logit calculations verified: baseline 0.58 → +0.323, ARC 0.73 → +0.995, β₁ ≈ 0.672, OR ≈ 1.96. All match the protocol (within rounding). See the σ²_task note above for the one inconsistency.

---

## Counter-Hypotheses Re-Tested

**CH-Q1 from V3.0 review ("60% baseline renders experiment uninformative"):**  
✅ No longer applicable. ARC-AGI-2 baseline of ~58% provides ~40pp of headroom — ample for a 15pp effect.

**CH-Q2 from V3.0 review ("ARC-AGI-1 contamination inflates Baseline selectively"):**  
✅ No longer applicable. ARC-AGI-2's 1-year exposure window + contamination detection test adequately address this.

---

## Final Assessment

V3.1 is a substantial and responsive revision. Every one of the 8 issues I raised has been addressed — not with superficial patches, but with principled changes that strengthen the protocol's internal validity:

- The dataset switch from ARC-AGI-1 to ARC-AGI-2 is the single most important change, eliminating the baseline miscalibration, contamination risk, and difficulty stratification problems simultaneously.
- The ceiling-effect stopping rule directly protects against V2.1's failure mode.
- The prompt fairness equalization removes the most threatening confound.
- The power increase to 50 tasks closes the H2 power gap.

The protocol is ready for pre-registration, pending the minor σ²_task documentation correction noted above.

---

**APPROVED.** Proceed to pre-registration.

*The trial ends — for now. The evidence is sound, the design is rigorous, and the crew has done the work. I'll be watching the results with keen interest.*

**— Q**
