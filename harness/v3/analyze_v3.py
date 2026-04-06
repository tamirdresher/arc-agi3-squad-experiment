#!/usr/bin/env python3
"""
ARC-AGI Squad Experiment V3.1 — Analysis Script

Loads all scored results and performs:
  - Summary statistics per condition × difficulty
  - GLMM for H1 and H2 (exact match ~ condition + difficulty + (1|task))
  - Fisher's exact test for H1 and H2
  - McNemar's test on majority-vote
  - Paired t-test for H3 (token overhead)
  - LMM for H4 (cell accuracy)
  - Holm-Bonferroni correction
  - Output: analysis/v3/RESULTS_SUMMARY_V3.md

Usage:
    python harness/v3/analyze_v3.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

try:
    from scipy import stats as scipy_stats
except ImportError:
    print("ERROR: scipy is required. Install with: pip install scipy", file=sys.stderr)
    sys.exit(1)

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("WARNING: statsmodels not found. GLMM analysis will be skipped.", file=sys.stderr)

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("WARNING: pandas not found. Some analyses will be limited.", file=sys.stderr)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HARNESS_DIR = Path(__file__).resolve().parent
ARC_ROOT = HARNESS_DIR.parent.parent
SCORES_DIR = ARC_ROOT / "results" / "v3" / "scores"
SELECTION_LOG = ARC_ROOT / "tasks" / "v3" / "selection-log.json"
OUTPUT_DIR = ARC_ROOT / "analysis" / "v3"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_all_scores() -> list[dict]:
    """Load all score.json files from results/v3/scores/."""
    records = []
    if not SCORES_DIR.exists():
        return records

    for task_dir in sorted(SCORES_DIR.iterdir()):
        if not task_dir.is_dir():
            continue
        task_id = task_dir.name
        for cond_dir in sorted(task_dir.iterdir()):
            if not cond_dir.is_dir():
                continue
            condition = cond_dir.name
            for run_dir in sorted(cond_dir.iterdir()):
                if not run_dir.is_dir():
                    continue
                score_file = run_dir / "score.json"
                if score_file.exists():
                    with open(score_file) as f:
                        data = json.load(f)
                    data["task_id"] = task_id
                    data["condition"] = condition
                    data["run_number"] = int(run_dir.name)
                    records.append(data)

    return records


def load_difficulty_map() -> dict[str, str]:
    """Load task_id -> difficulty mapping from selection-log.json."""
    if not SELECTION_LOG.exists():
        return {}
    with open(SELECTION_LOG) as f:
        log = json.load(f)
    return {entry["task_id"]: entry["difficulty"] for entry in log}


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------


def compute_summaries(records: list[dict], diff_map: dict[str, str]) -> dict:
    """Compute summary statistics per condition × difficulty."""
    # Group by condition and difficulty
    groups: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        cond = r["condition"]
        diff = diff_map.get(r["task_id"], "unknown")
        groups[cond][diff].append(r)

    summaries = {}
    for cond in sorted(groups.keys()):
        cond_summary = {}
        for diff in sorted(groups[cond].keys()):
            items = groups[cond][diff]
            exact_matches = [r.get("exact_match", False) for r in items]
            cell_accs = [r.get("cell_accuracy", 0.0) for r in items]
            tokens = [r.get("tokens_used") for r in items if r.get("tokens_used") is not None]
            extraction_ok = [r.get("extraction_success", False) for r in items]

            cond_summary[diff] = {
                "n_runs": len(items),
                "exact_match_rate": np.mean(exact_matches) if exact_matches else 0,
                "cell_accuracy_mean": np.mean(cell_accs) if cell_accs else 0,
                "cell_accuracy_std": np.std(cell_accs) if cell_accs else 0,
                "extraction_success_rate": np.mean(extraction_ok) if extraction_ok else 0,
                "mean_tokens": np.mean(tokens) if tokens else None,
                "n_tasks": len(set(r["task_id"] for r in items)),
            }
        summaries[cond] = cond_summary

    return summaries


# ---------------------------------------------------------------------------
# Majority vote
# ---------------------------------------------------------------------------


def compute_majority_vote(records: list[dict]) -> dict[str, dict[str, bool]]:
    """Compute majority-vote accuracy per task per condition.

    For each task × condition, take the mode of 5 runs' exact_match.
    """
    votes: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        votes[r["task_id"]][r["condition"]].append(r.get("exact_match", False))

    results = {}
    for task_id, conds in votes.items():
        results[task_id] = {}
        for cond, matches in conds.items():
            results[task_id][cond] = sum(matches) >= 3  # majority of 5
    return results


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------


def fishers_exact_test(records: list[dict], cond_a: str, cond_b: str) -> dict:
    """Fisher's exact test comparing two conditions on exact match."""
    a_matches = [r["exact_match"] for r in records if r["condition"] == cond_a]
    b_matches = [r["exact_match"] for r in records if r["condition"] == cond_b]

    a_yes = sum(a_matches)
    a_no = len(a_matches) - a_yes
    b_yes = sum(b_matches)
    b_no = len(b_matches) - b_yes

    table = [[a_yes, a_no], [b_yes, b_no]]
    odds_ratio, p_value = scipy_stats.fisher_exact(table, alternative="greater")

    return {
        "test": "Fisher's exact (one-sided)",
        "condition_a": cond_a,
        "condition_b": cond_b,
        "a_accuracy": a_yes / len(a_matches) if a_matches else 0,
        "b_accuracy": b_yes / len(b_matches) if b_matches else 0,
        "odds_ratio": odds_ratio,
        "p_value": p_value,
        "table": table,
    }


def mcnemar_test(majority_votes: dict, cond_a: str, cond_b: str) -> dict:
    """McNemar's test on majority-vote per task."""
    # Build paired contingency table
    both_correct = 0
    a_only = 0
    b_only = 0
    both_wrong = 0

    for task_id, conds in majority_votes.items():
        a = conds.get(cond_a, False)
        b = conds.get(cond_b, False)
        if a and b:
            both_correct += 1
        elif a and not b:
            a_only += 1
        elif not a and b:
            b_only += 1
        else:
            both_wrong += 1

    # McNemar's test focuses on discordant pairs
    n_discordant = a_only + b_only
    if n_discordant == 0:
        return {
            "test": "McNemar's (exact binomial)",
            "condition_a": cond_a,
            "condition_b": cond_b,
            "a_only": a_only,
            "b_only": b_only,
            "p_value": 1.0,
            "note": "No discordant pairs",
        }

    # Exact binomial test (better for small samples)
    p_value = scipy_stats.binom_test(a_only, a_only + b_only, 0.5)

    return {
        "test": "McNemar's (exact binomial)",
        "condition_a": cond_a,
        "condition_b": cond_b,
        "both_correct": both_correct,
        "a_only": a_only,
        "b_only": b_only,
        "both_wrong": both_wrong,
        "p_value": p_value,
    }


def paired_ttest_tokens(records: list[dict], cond_a: str, cond_b: str) -> dict:
    """Paired t-test for H3 (token overhead): compare mean tokens per task."""
    # Compute mean tokens per task per condition
    task_tokens: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        if r.get("tokens_used") is not None:
            task_tokens[r["task_id"]][r["condition"]].append(r["tokens_used"])

    a_means = []
    b_means = []
    for task_id in task_tokens:
        if cond_a in task_tokens[task_id] and cond_b in task_tokens[task_id]:
            a_means.append(np.mean(task_tokens[task_id][cond_a]))
            b_means.append(np.mean(task_tokens[task_id][cond_b]))

    if len(a_means) < 2:
        return {
            "test": "Paired t-test (tokens)",
            "condition_a": cond_a,
            "condition_b": cond_b,
            "p_value": None,
            "note": "Insufficient data for paired t-test",
        }

    a_arr = np.array(a_means)
    b_arr = np.array(b_means)
    overhead_pct = ((a_arr - b_arr) / b_arr * 100)

    t_stat, p_value = scipy_stats.ttest_rel(a_arr, b_arr)

    return {
        "test": "Paired t-test (tokens)",
        "condition_a": cond_a,
        "condition_b": cond_b,
        "mean_a": float(np.mean(a_arr)),
        "mean_b": float(np.mean(b_arr)),
        "mean_overhead_pct": float(np.mean(overhead_pct)),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "n_pairs": len(a_means),
    }


def run_glmm(records: list[dict], diff_map: dict[str, str]) -> dict:
    """Run GLMM: exact_match ~ condition + difficulty + (1|task_id)."""
    if not HAS_STATSMODELS or not HAS_PANDAS:
        return {"note": "statsmodels/pandas not available; GLMM skipped"}

    df = pd.DataFrame(records)
    df["difficulty"] = df["task_id"].map(diff_map).fillna("unknown")
    df["exact_match_int"] = df["exact_match"].astype(int)

    # Dummy-code condition with baseline as reference
    df["cond_cot"] = (df["condition"] == "chain-of-thought").astype(int)
    df["cond_arc"] = (df["condition"] == "arc-informed").astype(int)

    # Dummy-code difficulty with easy as reference
    df["diff_medium"] = (df["difficulty"] == "medium").astype(int)
    df["diff_hard"] = (df["difficulty"] == "hard").astype(int)

    try:
        model = smf.mixedlm(
            "exact_match_int ~ cond_cot + cond_arc + diff_medium + diff_hard",
            data=df,
            groups=df["task_id"],
        )
        result = model.fit(reml=False)

        return {
            "model": "GLMM (LMM approximation via mixedlm)",
            "n_observations": len(df),
            "n_tasks": df["task_id"].nunique(),
            "summary": str(result.summary()),
            "params": {k: float(v) for k, v in result.params.items()},
            "pvalues": {k: float(v) for k, v in result.pvalues.items()},
            "converged": result.converged,
        }
    except Exception as exc:
        return {"error": str(exc)}


def run_lmm_cell_accuracy(records: list[dict], diff_map: dict[str, str]) -> dict:
    """Run LMM for H4: cell_accuracy ~ condition + difficulty + (1|task_id)."""
    if not HAS_STATSMODELS or not HAS_PANDAS:
        return {"note": "statsmodels/pandas not available; LMM skipped"}

    df = pd.DataFrame(records)
    df["difficulty"] = df["task_id"].map(diff_map).fillna("unknown")

    df["cond_cot"] = (df["condition"] == "chain-of-thought").astype(int)
    df["cond_arc"] = (df["condition"] == "arc-informed").astype(int)
    df["diff_medium"] = (df["difficulty"] == "medium").astype(int)
    df["diff_hard"] = (df["difficulty"] == "hard").astype(int)

    try:
        model = smf.mixedlm(
            "cell_accuracy ~ cond_cot + cond_arc + diff_medium + diff_hard",
            data=df,
            groups=df["task_id"],
        )
        result = model.fit(reml=False)

        return {
            "model": "LMM (cell accuracy)",
            "n_observations": len(df),
            "summary": str(result.summary()),
            "params": {k: float(v) for k, v in result.params.items()},
            "pvalues": {k: float(v) for k, v in result.pvalues.items()},
            "converged": result.converged,
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Holm-Bonferroni correction
# ---------------------------------------------------------------------------


def holm_bonferroni(p_values: dict[str, float], alpha: float = 0.05) -> dict:
    """Apply Holm-Bonferroni correction to multiple p-values.

    Args:
        p_values: {hypothesis_name: p_value}
        alpha: family-wise error rate

    Returns:
        Dict with corrected results per hypothesis.
    """
    m = len(p_values)
    sorted_hyps = sorted(p_values.items(), key=lambda x: x[1])

    results = {}
    for rank, (name, p) in enumerate(sorted_hyps, 1):
        adjusted_alpha = alpha / (m - rank + 1)
        results[name] = {
            "p_value": p,
            "rank": rank,
            "adjusted_alpha": adjusted_alpha,
            "significant": p < adjusted_alpha,
        }
    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_report(
    summaries: dict,
    glmm_result: dict,
    lmm_result: dict,
    fisher_h1: dict,
    fisher_h2: dict,
    mcnemar_h1: dict,
    mcnemar_h2: dict,
    ttest_h3: dict,
    holm_results: dict,
    n_records: int,
) -> str:
    """Generate the RESULTS_SUMMARY_V3.md report."""
    lines = [
        "# ARC-AGI Squad Experiment V3.1 — Results Summary",
        "",
        f"**Generated:** {__import__('datetime').datetime.now().isoformat()}",
        f"**Total scored runs:** {n_records}",
        "",
        "---",
        "",
        "## 1. Summary Statistics",
        "",
    ]

    for cond in ["baseline", "chain-of-thought", "arc-informed"]:
        if cond not in summaries:
            continue
        lines.append(f"### Condition: {cond}")
        lines.append("")
        lines.append("| Difficulty | N Runs | Exact Match | Cell Accuracy | Extraction Rate | Mean Tokens |")
        lines.append("|-----------|--------|-------------|---------------|-----------------|-------------|")
        for diff in ["easy", "medium", "hard", "unknown"]:
            if diff not in summaries[cond]:
                continue
            s = summaries[cond][diff]
            tokens_str = f"{s['mean_tokens']:.0f}" if s['mean_tokens'] else "N/A"
            lines.append(
                f"| {diff} | {s['n_runs']} | "
                f"{s['exact_match_rate']:.1%} | "
                f"{s['cell_accuracy_mean']:.3f} ± {s['cell_accuracy_std']:.3f} | "
                f"{s['extraction_success_rate']:.1%} | "
                f"{tokens_str} |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 2. Hypothesis Tests",
        "",
        "### H1: ARC > Baseline (exact match)",
        "",
        f"**Fisher's exact test:** p = {fisher_h1.get('p_value', 'N/A')}",
        f"  ARC accuracy: {fisher_h1.get('a_accuracy', 'N/A'):.1%}" if isinstance(fisher_h1.get('a_accuracy'), float) else "",
        f"  Baseline accuracy: {fisher_h1.get('b_accuracy', 'N/A'):.1%}" if isinstance(fisher_h1.get('b_accuracy'), float) else "",
        "",
        f"**McNemar's test (majority vote):** p = {mcnemar_h1.get('p_value', 'N/A')}",
        "",
        "### H2: ARC > CoT (exact match)",
        "",
        f"**Fisher's exact test:** p = {fisher_h2.get('p_value', 'N/A')}",
        "",
        f"**McNemar's test (majority vote):** p = {mcnemar_h2.get('p_value', 'N/A')}",
        "",
        "### H3: Token overhead ≤ 25%",
        "",
        f"**Paired t-test:** p = {ttest_h3.get('p_value', 'N/A')}",
        f"  Mean overhead: {ttest_h3.get('mean_overhead_pct', 'N/A')}%" if isinstance(ttest_h3.get('mean_overhead_pct'), float) else "",
        "",
        "### H4: ARC > Baseline (cell accuracy)",
        "",
        f"**LMM result:** See GLMM section below.",
        "",
        "---",
        "",
        "## 3. GLMM Results",
        "",
        "```",
        json.dumps(glmm_result, indent=2, default=str),
        "```",
        "",
        "## 4. LMM (Cell Accuracy) Results",
        "",
        "```",
        json.dumps(lmm_result, indent=2, default=str),
        "```",
        "",
        "---",
        "",
        "## 5. Holm-Bonferroni Correction",
        "",
        "| Hypothesis | p-value | Adjusted α | Significant |",
        "|-----------|---------|-----------|-------------|",
    ])

    for name, res in sorted(holm_results.items(), key=lambda x: x[1]["rank"]):
        lines.append(
            f"| {name} | {res['p_value']:.4f} | {res['adjusted_alpha']:.4f} | "
            f"{'Yes' if res['significant'] else 'No'} |"
        )

    lines.extend(["", "---", "", "*End of report.*"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("Loading scores...")
    records = load_all_scores()
    if not records:
        print("No scored runs found. Run the experiment first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(records)} scored runs")
    diff_map = load_difficulty_map()

    # Summary stats
    summaries = compute_summaries(records, diff_map)

    # Majority vote
    majority_votes = compute_majority_vote(records)

    # Statistical tests
    print("Running statistical tests...")

    fisher_h1 = fishers_exact_test(records, "arc-informed", "baseline")
    fisher_h2 = fishers_exact_test(records, "arc-informed", "chain-of-thought")
    mcnemar_h1 = mcnemar_test(majority_votes, "arc-informed", "baseline")
    mcnemar_h2 = mcnemar_test(majority_votes, "arc-informed", "chain-of-thought")
    ttest_h3 = paired_ttest_tokens(records, "arc-informed", "baseline")

    # GLMM and LMM
    print("Running GLMM...")
    glmm_result = run_glmm(records, diff_map)
    lmm_result = run_lmm_cell_accuracy(records, diff_map)

    # Holm-Bonferroni
    p_values = {}
    if fisher_h1.get("p_value") is not None:
        p_values["H1 (ARC > Baseline)"] = fisher_h1["p_value"]
    if fisher_h2.get("p_value") is not None:
        p_values["H2 (ARC > CoT)"] = fisher_h2["p_value"]
    if ttest_h3.get("p_value") is not None:
        p_values["H3 (Token overhead)"] = ttest_h3["p_value"]
    # Add GLMM p-values if available
    if "pvalues" in glmm_result:
        if "cond_arc" in glmm_result["pvalues"]:
            p_values["H1-GLMM (ARC effect)"] = glmm_result["pvalues"]["cond_arc"]
    if "pvalues" in lmm_result:
        if "cond_arc" in lmm_result["pvalues"]:
            p_values["H4-LMM (ARC cell acc)"] = lmm_result["pvalues"]["cond_arc"]

    holm_results = holm_bonferroni(p_values) if p_values else {}

    # Generate report
    print("Generating report...")
    report = generate_report(
        summaries, glmm_result, lmm_result,
        fisher_h1, fisher_h2, mcnemar_h1, mcnemar_h2,
        ttest_h3, holm_results, len(records),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "RESULTS_SUMMARY_V3.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Report written to {report_path}")

    # Also save raw test results as JSON
    results_json = {
        "summaries": summaries,
        "fisher_h1": fisher_h1,
        "fisher_h2": fisher_h2,
        "mcnemar_h1": mcnemar_h1,
        "mcnemar_h2": mcnemar_h2,
        "ttest_h3": ttest_h3,
        "glmm": glmm_result,
        "lmm_cell_accuracy": lmm_result,
        "holm_bonferroni": holm_results,
    }
    json_path = OUTPUT_DIR / "results_v3.json"
    json_path.write_text(
        json.dumps(results_json, indent=2, default=str), encoding="utf-8",
    )
    print(f"Raw results written to {json_path}")


if __name__ == "__main__":
    main()
