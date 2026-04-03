#!/usr/bin/env python3
"""
SHAE Score Calculator
Squad Human Action Efficiency — analogous to ARC-AGI-3's RHAE metric

Usage:
    python compute-shae.py --results results.yaml
    python compute-shae.py --interactive

Formula:
    SHAE = (human_baseline_actions / agent_actions)^2

A score of 1.0 = perfect human-equivalent efficiency.
A score near 0 = brute-force completion (many retries, excessive steps).
"""

import argparse
import json
import sys
from typing import Optional

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


def compute_shae(human_baseline: int, agent_actions: int) -> float:
    """Compute SHAE score: (human_baseline / agent_actions)^2, capped at 1.0."""
    if agent_actions <= 0:
        raise ValueError("agent_actions must be > 0")
    score = (human_baseline / agent_actions) ** 2
    return min(score, 1.0)  # Cannot exceed perfect efficiency


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


def score_result(result: dict) -> dict:
    """Score a single task result dict."""
    task = result.get("task", "unknown")
    variant = result.get("variant", "familiar")
    config = result.get("configuration", "baseline")
    agent_actions = result.get("agent_actions", 0)
    task_type = task.split("-", 2)[-1] if "-" in task else task  # e.g. "task-01-simple-factual" → "simple-factual"

    # Determine baseline
    baseline = result.get("human_baseline") or HUMAN_BASELINES.get(task_type, 5)

    shae = compute_shae(baseline, agent_actions) if agent_actions > 0 else 0.0
    grade = grade_shae(shae)

    return {
        "task": task,
        "variant": variant,
        "configuration": config,
        "agent_actions": agent_actions,
        "human_baseline": baseline,
        "shae_score": round(shae, 3),
        "grade": grade,
        "correct": result.get("correct", "unknown"),
    }


def print_summary(scored_results: list) -> None:
    """Print a summary table of scored results."""
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


def interactive_mode() -> None:
    """Interactive scoring — prompts user for each result."""
    print("=== SHAE Interactive Scorer ===")
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
        scored = [score_result(r) for r in results]
        print_summary(scored)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute SHAE scores for ARC-AGI-3 Squad experiment")
    parser.add_argument("--results", help="Path to results YAML or JSON file")
    parser.add_argument("--interactive", action="store_true", help="Enter results interactively")
    parser.add_argument("--example", action="store_true", help="Run with example data")
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
        scored = [score_result(r) for r in example_results]
        print_summary(scored)
    elif args.interactive:
        interactive_mode()
    elif args.results:
        try:
            with open(args.results) as f:
                data = json.load(f)
            results = data if isinstance(data, list) else data.get("results", [])
            scored = [score_result(r) for r in results]
            print_summary(scored)
        except Exception as e:
            print(f"Error reading results file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        print("\nTip: Run with --example to see sample output.")


if __name__ == "__main__":
    main()
