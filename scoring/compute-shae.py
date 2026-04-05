#!/usr/bin/env python3
"""
SHAE Score Calculator — v2
Squad Human Action Efficiency — inspired by ARC-AGI-3's RHAE metric

Usage:
    python compute-shae.py --results results.json                  # v1 (backward compat)
    python compute-shae.py --results results.json --v2             # v2 with correctness gate + stats
    python compute-shae.py --interactive
    python compute-shae.py --example
    python compute-shae.py --example --v2

Formula:
    SHAE   = (human_baseline_actions / agent_actions)^2    [capped at 1.0]
    SHAE-C = SHAE if correct == "yes" else 0.0             [correctness-gated]

SHAE-C is the v2 primary metric. Original SHAE is retained for comparison.
A score of 1.0 = perfect human-equivalent efficiency.
A score of 0.0 = wrong answer (SHAE-C) or brute-force (SHAE).

Changes from v1:
    - SHAE-C: correctness gate (wrong answers → 0.0)
    - Statistical helpers: mean+CI, Cohen's d, chi-squared
    - --v2 flag activates new scoring mode
    - Backward compatible with v1 data and behavior
"""

import argparse
import json
import math
import sys
from typing import List, Optional, Tuple


# Human baseline action counts per task type (set in squad.config.ts)
HUMAN_BASELINES = {
    "simple-factual": 3,
    "multi-step-technical": 8,
    "implicit-goal": 6,
}

THRESHOLDS = {
    "excellent": 0.7,
    "good": 0.5,
    "acceptable": 0.3,
    "brute-force": 0.1,
}


# ---------------------------------------------------------------------------
# Statistical Helpers (v2)
# ---------------------------------------------------------------------------

def compute_mean_ci(values: List[float], confidence: float = 0.95) -> Tuple[float, float, float]:
    """Compute mean with confidence interval using t-distribution approximation.

    Returns (mean, ci_lower, ci_upper).
    For n < 30, uses a simplified t-critical lookup; for n >= 30 uses z ≈ 1.96.
    """
    n = len(values)
    if n == 0:
        return (0.0, 0.0, 0.0)
    if n == 1:
        return (values[0], values[0], values[0])

    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_err = math.sqrt(variance / n)

    # Simplified t-critical values for 95% CI (two-tailed)
    # Exact values for common small n; approximation otherwise
    t_critical_95 = {
        2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
        7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228,
        12: 2.201, 15: 2.145, 20: 2.093, 25: 2.064, 30: 2.045,
    }
    if confidence != 0.95:
        # Fallback to z for non-standard confidence
        import statistics
        z = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}.get(confidence, 1.960)
        margin = z * std_err
    elif n - 1 in t_critical_95:
        margin = t_critical_95[n - 1] * std_err
    elif n >= 30:
        margin = 1.960 * std_err
    else:
        # Interpolate from nearest lower key
        keys = sorted(t_critical_95.keys())
        df = n - 1
        lower_key = max(k for k in keys if k <= df) if any(k <= df for k in keys) else keys[0]
        margin = t_critical_95[lower_key] * std_err

    return (round(mean, 4), round(mean - margin, 4), round(mean + margin, 4))


def compute_effect_size(group1: List[float], group2: List[float]) -> float:
    """Compute Cohen's d effect size between two groups.

    d = (mean2 - mean1) / pooled_std
    Interpretation: |d| < 0.2 = negligible, 0.2-0.5 = small, 0.5-0.8 = medium, > 0.8 = large
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return float('nan')

    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1)

    # Pooled standard deviation
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = math.sqrt(pooled_var)

    if pooled_std == 0:
        return float('inf') if mean2 != mean1 else 0.0

    return round((mean2 - mean1) / pooled_std, 4)


def chi_squared_test(correct_counts: List[int], total_counts: List[int]) -> Tuple[float, float]:
    """Chi-squared test for comparing correctness rates across conditions.

    Args:
        correct_counts: [baseline_correct, arc_correct, ...]
        total_counts:   [baseline_total,   arc_total,   ...]

    Returns (chi2_statistic, p_value_approx).
    Uses chi-squared with Yates' correction for 2x2 tables.
    P-value from chi-squared CDF approximation (Wilson-Hilferty).
    """
    k = len(correct_counts)
    if k != len(total_counts) or k < 2:
        return (float('nan'), float('nan'))

    incorrect_counts = [total_counts[i] - correct_counts[i] for i in range(k)]
    total = sum(total_counts)
    total_correct = sum(correct_counts)
    total_incorrect = total - total_correct

    if total == 0 or total_correct == 0 or total_incorrect == 0:
        return (float('nan'), float('nan'))

    # Expected counts under null hypothesis (equal correctness rates)
    chi2 = 0.0
    for i in range(k):
        exp_correct = total_counts[i] * total_correct / total
        exp_incorrect = total_counts[i] * total_incorrect / total

        if exp_correct > 0:
            chi2 += (correct_counts[i] - exp_correct) ** 2 / exp_correct
        if exp_incorrect > 0:
            chi2 += (incorrect_counts[i] - exp_incorrect) ** 2 / exp_incorrect

    # Degrees of freedom
    df = k - 1

    # Approximate p-value using Wilson-Hilferty transformation
    if df == 0:
        return (chi2, float('nan'))
    try:
        z = ((chi2 / df) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(2.0 / (9.0 * df))
        # Standard normal CDF approximation
        p_value = 0.5 * math.erfc(z / math.sqrt(2))
    except (ValueError, ZeroDivisionError):
        p_value = float('nan')

    return (round(chi2, 4), round(p_value, 6))


def interpret_effect_size(d: float) -> str:
    """Interpret Cohen's d magnitude."""
    if math.isnan(d):
        return "insufficient data"
    ad = abs(d)
    if ad < 0.2:
        return "negligible"
    elif ad < 0.5:
        return "small"
    elif ad < 0.8:
        return "medium"
    else:
        return "large"


# ---------------------------------------------------------------------------
# Core SHAE Scoring
# ---------------------------------------------------------------------------

def compute_shae(human_baseline: int, agent_actions: int) -> float:
    """Compute SHAE score: (human_baseline / agent_actions)^2, capped at 1.0."""
    if agent_actions <= 0:
        raise ValueError("agent_actions must be > 0")
    score = (human_baseline / agent_actions) ** 2
    return min(score, 1.0)  # Cannot exceed perfect efficiency


def compute_shae_c(human_baseline: int, agent_actions: int, correct: str) -> float:
    """Compute SHAE-C (correctness-gated): SHAE if correct == 'yes', else 0.0.

    This is the v2 primary metric. Wrong answers score zero regardless of efficiency.
    """
    if correct != "yes":
        return 0.0
    return compute_shae(human_baseline, agent_actions)


def grade_shae(score: float) -> str:
    """Return qualitative grade for a SHAE score."""
    if score >= THRESHOLDS["excellent"]:
        return "Excellent"
    elif score >= THRESHOLDS["good"]:
        return "Good"
    elif score >= THRESHOLDS["acceptable"]:
        return "Acceptable"
    elif score >= THRESHOLDS["brute-force"]:
        return "Brute Force"
    else:
        return "Failed (effectively)"


def score_result(result: dict, v2: bool = False) -> dict:
    """Score a single task result dict.

    Args:
        result: Task result dictionary with agent_actions, correct, etc.
        v2: If True, include SHAE-C (correctness-gated) score.
    """
    task = result.get("task", "unknown")
    variant = result.get("variant", "familiar")
    config = result.get("configuration", "baseline")
    agent_actions = result.get("agent_actions", 0)
    correct = result.get("correct", "unknown")

    # Extract task type for baseline lookup
    # e.g. "task-01-simple-factual" → "simple-factual"
    task_type = task.split("-", 2)[-1] if "-" in task else task

    # Determine human baseline
    baseline = result.get("human_baseline") or HUMAN_BASELINES.get(task_type, 5)

    shae = compute_shae(baseline, agent_actions) if agent_actions > 0 else 0.0
    grade = grade_shae(shae)

    scored = {
        "task": task,
        "variant": variant,
        "configuration": config,
        "agent_actions": agent_actions,
        "human_baseline": baseline,
        "shae_score": round(shae, 3),
        "grade": grade,
        "correct": correct,
    }

    if v2:
        shae_c = compute_shae_c(baseline, agent_actions, correct) if agent_actions > 0 else 0.0
        scored["shae_c_score"] = round(shae_c, 3)
        scored["shae_c_grade"] = grade_shae(shae_c) if correct == "yes" else "Gated (incorrect)"

    return scored


# ---------------------------------------------------------------------------
# Summary Printers
# ---------------------------------------------------------------------------

def print_summary(scored_results: list, v2: bool = False) -> None:
    """Print a summary table of scored results."""
    if v2:
        _print_summary_v2(scored_results)
    else:
        _print_summary_v1(scored_results)


def _print_summary_v1(scored_results: list) -> None:
    """Original v1 summary — backward compatible."""
    print("\n=== SHAE Scoring Results ===\n")
    print(f"{'Task':<35} {'Variant':<10} {'Config':<14} {'Actions':<9} {'SHAE':<7} {'Grade':<15} {'Correct'}")
    print("-" * 110)
    for r in scored_results:
        print(
            f"{r['task']:<35} {r['variant']:<10} {r['configuration']:<14} "
            f"{r['agent_actions']:<9} {r['shae_score']:<7} {r['grade']:<15} {r['correct']}"
        )

    # Compute averages by configuration
    configs = set(r["configuration"] for r in scored_results)
    print("\n=== Averages by Configuration ===\n")
    for cfg in sorted(configs):
        cfg_results = [r for r in scored_results if r["configuration"] == cfg]
        avg_shae = sum(r["shae_score"] for r in cfg_results) / len(cfg_results)
        print(f"  {cfg}: avg SHAE = {avg_shae:.3f} ({grade_shae(avg_shae)})")


def _print_summary_v2(scored_results: list) -> None:
    """v2 summary with SHAE, SHAE-C, and statistical analysis."""
    print("\n=== SHAE v2 Scoring Results ===\n")
    print(
        f"{'Task':<35} {'Variant':<10} {'Config':<14} {'Actions':<8} "
        f"{'SHAE':<7} {'SHAE-C':<8} {'Correct':<9} {'Grade (C)'}"
    )
    print("-" * 120)
    for r in scored_results:
        shae_c = r.get("shae_c_score", "—")
        shae_c_str = f"{shae_c:<8}" if isinstance(shae_c, (int, float)) else f"{shae_c:<8}"
        grade_c = r.get("shae_c_grade", "—")
        print(
            f"{r['task']:<35} {r['variant']:<10} {r['configuration']:<14} "
            f"{r['agent_actions']:<8} {r['shae_score']:<7} {shae_c_str} "
            f"{r['correct']:<9} {grade_c}"
        )

    # Separate by configuration
    configs = sorted(set(r["configuration"] for r in scored_results))
    print("\n=== Averages by Configuration (v2) ===\n")

    config_shae = {}
    config_shae_c = {}
    config_correct = {}
    config_total = {}

    for cfg in configs:
        cfg_results = [r for r in scored_results if r["configuration"] == cfg]
        shae_vals = [r["shae_score"] for r in cfg_results]
        shae_c_vals = [r.get("shae_c_score", 0.0) for r in cfg_results]
        n_correct = sum(1 for r in cfg_results if r["correct"] == "yes")
        n_total = len(cfg_results)

        config_shae[cfg] = shae_vals
        config_shae_c[cfg] = shae_c_vals
        config_correct[cfg] = n_correct
        config_total[cfg] = n_total

        mean_shae, lo_shae, hi_shae = compute_mean_ci(shae_vals)
        mean_shae_c, lo_c, hi_c = compute_mean_ci(shae_c_vals)

        print(f"  {cfg}:")
        print(f"    SHAE:       mean = {mean_shae:.3f}  [95% CI: {lo_shae:.3f} – {hi_shae:.3f}]")
        print(f"    SHAE-C:     mean = {mean_shae_c:.3f}  [95% CI: {lo_c:.3f} – {hi_c:.3f}]")
        print(f"    Correctness: {n_correct}/{n_total} ({100*n_correct/n_total:.0f}%)")
        print()

    # Statistical comparisons (if exactly 2 configs)
    if len(configs) == 2:
        cfg_a, cfg_b = configs[0], configs[1]
        print("=== Statistical Comparison ===\n")

        # Effect sizes
        d_shae = compute_effect_size(config_shae[cfg_a], config_shae[cfg_b])
        d_shae_c = compute_effect_size(config_shae_c[cfg_a], config_shae_c[cfg_b])
        print(f"  SHAE   Cohen's d: {d_shae:+.3f} ({interpret_effect_size(d_shae)})")
        print(f"  SHAE-C Cohen's d: {d_shae_c:+.3f} ({interpret_effect_size(d_shae_c)})")

        # Chi-squared test on correctness
        chi2, p = chi_squared_test(
            [config_correct[cfg_a], config_correct[cfg_b]],
            [config_total[cfg_a], config_total[cfg_b]],
        )
        print(f"  Correctness χ²:  {chi2:.3f}, p ≈ {p:.4f}")
        if p < 0.05:
            print("  → Statistically significant difference in correctness (p < 0.05)")
        elif not math.isnan(p):
            print("  → NOT statistically significant (p ≥ 0.05) — interpret with caution")
        print()

        # Caveat
        print("  ⚠️  CAUTION: n is small. These statistics are indicative, not conclusive.")
        print("      A v2 experiment with larger n and repeated runs is needed for confirmation.")
        print()


# ---------------------------------------------------------------------------
# Interactive Mode
# ---------------------------------------------------------------------------

def interactive_mode(v2: bool = False) -> None:
    """Interactive scoring — prompts user for each result."""
    mode_label = "v2 (SHAE + SHAE-C)" if v2 else "v1 (SHAE only)"
    print(f"=== SHAE Interactive Scorer ({mode_label}) ===")
    print("Enter results for each task run. Type 'done' to finish.\n")
    results = []
    while True:
        task = input("Task type (simple-factual | multi-step-technical | implicit-goal | done): ").strip()
        if task == "done":
            break
        variant = input("Variant (familiar | near-ood | far-ood): ").strip()
        config = input("Configuration (baseline | arc-informed): ").strip()
        try:
            agent_actions = int(input("Number of agent actions: ").strip())
        except ValueError:
            print("Invalid number, skipping.")
            continue
        correct = input("Correct? (yes | no | partial): ").strip()
        results.append({
            "task": f"task-{task}",
            "variant": variant,
            "configuration": config,
            "agent_actions": agent_actions,
            "correct": correct,
        })
    if results:
        scored = [score_result(r, v2=v2) for r in results]
        print_summary(scored, v2=v2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute SHAE scores for ARC-AGI-3 Squad experiment",
        epilog="v2 mode adds SHAE-C (correctness gate) and statistical analysis.",
    )
    parser.add_argument("--results", help="Path to results JSON file")
    parser.add_argument("--interactive", action="store_true", help="Enter results interactively")
    parser.add_argument("--example", action="store_true", help="Run with example data")
    parser.add_argument(
        "--v2", action="store_true",
        help="Activate v2 scoring: SHAE-C (correctness gate), confidence intervals, effect sizes",
    )
    args = parser.parse_args()

    if args.example:
        example_results = [
            {"task": "task-01-simple-factual", "variant": "familiar", "configuration": "baseline", "agent_actions": 4, "correct": "yes"},
            {"task": "task-01-simple-factual", "variant": "familiar", "configuration": "arc-informed", "agent_actions": 3, "correct": "yes"},
            {"task": "task-02-multi-step-technical", "variant": "familiar", "configuration": "baseline", "agent_actions": 15, "correct": "partial"},
            {"task": "task-02-multi-step-technical", "variant": "familiar", "configuration": "arc-informed", "agent_actions": 9, "correct": "yes"},
            {"task": "task-03-implicit-goal", "variant": "familiar", "configuration": "baseline", "agent_actions": 5, "correct": "partial"},
            {"task": "task-03-implicit-goal", "variant": "familiar", "configuration": "arc-informed", "agent_actions": 6, "correct": "yes"},
            {"task": "task-01-simple-factual", "variant": "near-ood", "configuration": "baseline", "agent_actions": 6, "correct": "partial"},
            {"task": "task-01-simple-factual", "variant": "near-ood", "configuration": "arc-informed", "agent_actions": 4, "correct": "yes"},
        ]
        scored = [score_result(r, v2=args.v2) for r in example_results]
        print_summary(scored, v2=args.v2)
    elif args.interactive:
        interactive_mode(v2=args.v2)
    elif args.results:
        try:
            with open(args.results) as f:
                data = json.load(f)
            results = data if isinstance(data, list) else data.get("results", [])
            scored = [score_result(r, v2=args.v2) for r in results]
            print_summary(scored, v2=args.v2)
        except Exception as e:
            print(f"Error reading results file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        print("\nTip: Run with --example to see sample output.")
        print("     Run with --example --v2 to see v2 scoring with SHAE-C.")


if __name__ == "__main__":
    main()
