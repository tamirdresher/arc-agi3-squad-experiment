#!/usr/bin/env python3
"""
ARC-AGI Squad Experiment V3.1 — Run Order Generator

Generates a deterministic pseudorandom ordering of all 750 runs.
Seed: 7. Condition order within each task is randomized per-task
using seed 7 + SHA-256(task_id).

Usage:
    python harness/v3/generate_run_order.py

Output:
    runs/v3-run-order.json
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEED = 7
CONDITIONS = ["baseline", "chain-of-thought", "arc-informed"]
RUNS_PER_CONDITION = 5

HARNESS_DIR = Path(__file__).resolve().parent
ARC_ROOT = HARNESS_DIR.parent.parent
SELECTION_LOG = ARC_ROOT / "tasks" / "v3" / "selection-log.json"
OUTPUT_PATH = ARC_ROOT / "runs" / "v3-run-order.json"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def task_condition_seed(task_id: str) -> int:
    """Deterministic seed for per-task condition ordering: 7 + SHA-256(task_id)."""
    h = hashlib.sha256(task_id.encode("utf-8")).hexdigest()
    return SEED + int(h[:8], 16)


def main() -> None:
    # Load selected tasks
    if not SELECTION_LOG.exists():
        print(f"ERROR: Selection log not found at {SELECTION_LOG}", file=sys.stderr)
        print("Run select_tasks.py first.", file=sys.stderr)
        sys.exit(1)

    with open(SELECTION_LOG, "r", encoding="utf-8") as f:
        selection = json.load(f)

    task_ids = [entry["task_id"] for entry in selection]
    print(f"Generating run order for {len(task_ids)} tasks")
    print(f"  {len(task_ids)} tasks × {len(CONDITIONS)} conditions × {RUNS_PER_CONDITION} runs = "
          f"{len(task_ids) * len(CONDITIONS) * RUNS_PER_CONDITION} total runs")

    # Generate all run entries
    all_runs = []
    for task_id in task_ids:
        # Per-task condition ordering
        rng = random.Random(task_condition_seed(task_id))
        task_conditions = CONDITIONS[:]
        rng.shuffle(task_conditions)

        for condition in task_conditions:
            for run_number in range(1, RUNS_PER_CONDITION + 1):
                all_runs.append({
                    "task_id": task_id,
                    "condition": condition,
                    "run_number": run_number,
                })

    # Global shuffle with master seed
    rng_global = random.Random(SEED)
    rng_global.shuffle(all_runs)

    print(f"Generated {len(all_runs)} run entries")

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_runs, f, indent=2)
    print(f"Run order written to {OUTPUT_PATH}")

    # Quick verification
    task_set = set(r["task_id"] for r in all_runs)
    cond_set = set(r["condition"] for r in all_runs)
    print(f"Verification: {len(task_set)} unique tasks, {len(cond_set)} conditions")


if __name__ == "__main__":
    main()
