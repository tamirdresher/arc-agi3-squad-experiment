#!/usr/bin/env python3
"""
ARC-AGI Squad Experiment V3.1 — Task Selection Script

Selects 50 tasks from the 120 ARC-AGI-2 evaluation tasks using
objective proxy metrics for difficulty stratification.

Usage:
    python tasks/v3/select_tasks.py

Outputs:
    tasks/v3/selection-log.json  — metadata for all 50 selected tasks
    tasks/v3/exclusion-log.json  — excluded tasks with reasons
    tasks/v3/{task_id}.json      — copies of selected task files
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
ARC_ROOT = SCRIPT_DIR.parent.parent  # C:\temp\arc-experiment
EVAL_DIR = ARC_ROOT / "ARC-AGI-2" / "data" / "evaluation"
OUTPUT_DIR = SCRIPT_DIR  # tasks/v3/

# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


def compute_features(task: dict) -> dict:
    """Compute objective surface features for a task."""
    all_grids = []
    for pair in task.get("train", []):
        all_grids.append(pair["input"])
        all_grids.append(pair["output"])
    for pair in task.get("test", []):
        all_grids.append(pair["input"])
        if "output" in pair:
            all_grids.append(pair["output"])

    # Max dimension across all grids
    max_dim = 0
    for grid in all_grids:
        rows = len(grid)
        cols = max((len(r) for r in grid), default=0)
        max_dim = max(max_dim, rows, cols)

    # Unique colors across all grids
    colors = set()
    for grid in all_grids:
        for row in grid:
            for cell in row:
                colors.add(cell)
    unique_colors = len(colors)

    # Number of training examples
    num_train = len(task.get("train", []))

    # Size ratio: max output size / max input size
    input_sizes = []
    output_sizes = []
    for pair in task.get("train", []):
        inp = pair["input"]
        out = pair["output"]
        input_sizes.append(len(inp) * (len(inp[0]) if inp else 0))
        output_sizes.append(len(out) * (len(out[0]) if out else 0))

    if input_sizes and min(input_sizes) > 0:
        size_ratio = max(output_sizes) / min(input_sizes)
    else:
        size_ratio = 1.0

    return {
        "max_dim": max_dim,
        "unique_colors": unique_colors,
        "num_train": num_train,
        "size_ratio": round(size_ratio, 3),
    }


def compute_difficulty_score(features: dict) -> float:
    """Compute a composite difficulty score for tertile-based stratification.

    Higher score = harder task. Components:
    - Normalized max_dim (0-1 over range 1-30)
    - Normalized unique_colors (0-1 over range 1-10)
    - Inverted normalized num_train (fewer examples = harder)
    - Normalized size_ratio (larger output expansion = harder)
    """
    md = min(features["max_dim"], 30) / 30.0
    uc = min(features["unique_colors"], 10) / 10.0
    # Fewer training examples = harder (invert: 5->0, 1->1)
    nt = 1.0 - min(features["num_train"], 5) / 5.0
    sr = min(features["size_ratio"], 10.0) / 10.0
    return 0.35 * md + 0.30 * uc + 0.20 * nt + 0.15 * sr


def classify_difficulty_tertile(candidates: list[dict]) -> list[dict]:
    """Classify tasks into easy/medium/hard using tertile splits on composite score.

    This replaces the fixed-threshold approach since ARC-AGI-2 tasks
    have much larger grids and more colors than the original proxy assumed.
    Tertile-based splitting ensures roughly balanced difficulty tiers.
    """
    # Compute scores
    for c in candidates:
        c["difficulty_score"] = compute_difficulty_score(c["features"])

    # Sort by score
    scored = sorted(candidates, key=lambda x: x["difficulty_score"])

    n = len(scored)
    t1 = n // 3
    t2 = 2 * n // 3

    for i, c in enumerate(scored):
        if i < t1:
            c["difficulty"] = "easy"
        elif i < t2:
            c["difficulty"] = "medium"
        else:
            c["difficulty"] = "hard"

    return candidates


# ---------------------------------------------------------------------------
# Exclusion checks
# ---------------------------------------------------------------------------


def has_multiple_test_inputs(task: dict) -> bool:
    """Exclude tasks with more than one test input."""
    return len(task.get("test", [])) > 1


def is_degenerate(task: dict) -> bool:
    """Exclude tasks where test output == test input."""
    for pair in task.get("test", []):
        if "output" in pair and pair["input"] == pair["output"]:
            return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    """SHA-256 hash of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    random.seed(42)

    if not EVAL_DIR.is_dir():
        print(f"ERROR: ARC-AGI-2 evaluation directory not found: {EVAL_DIR}", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(EVAL_DIR.glob("*.json"))
    print(f"Found {len(json_files)} evaluation tasks in {EVAL_DIR}")

    # Load and classify all tasks
    candidates = []
    exclusions = []

    for jf in json_files:
        task_id = jf.stem
        with open(jf, "r", encoding="utf-8") as f:
            task = json.load(f)

        # Exclusion checks
        if has_multiple_test_inputs(task):
            exclusions.append({
                "task_id": task_id,
                "reason": "multiple_test_inputs",
                "test_count": len(task.get("test", [])),
            })
            continue

        if is_degenerate(task):
            exclusions.append({
                "task_id": task_id,
                "reason": "degenerate_output_equals_input",
            })
            continue

        # Check that test has ground truth
        if not task.get("test", []) or "output" not in task["test"][0]:
            exclusions.append({
                "task_id": task_id,
                "reason": "no_ground_truth",
            })
            continue

        features = compute_features(task)
        file_hash = sha256_file(jf)

        candidates.append({
            "task_id": task_id,
            "difficulty": "",  # assigned below by tertile
            "features": features,
            "sha256": file_hash,
            "source_path": str(jf),
        })

    print(f"Candidates after exclusion: {len(candidates)}")
    print(f"Excluded: {len(exclusions)}")

    # Classify difficulty using percentile-based tertile splits
    # (Protocol says human-calibrated; we use composite proxy as fallback)
    candidates = classify_difficulty_tertile(candidates)

    # Group by difficulty
    easy = [c for c in candidates if c["difficulty"] == "easy"]
    medium = [c for c in candidates if c["difficulty"] == "medium"]
    hard = [c for c in candidates if c["difficulty"] == "hard"]

    print(f"  Easy:   {len(easy)}")
    print(f"  Medium: {len(medium)}")
    print(f"  Hard:   {len(hard)}")

    # Target counts
    target_easy = 17
    target_medium = 17
    target_hard = 16

    # Sample from each tier; if a tier has fewer than needed, pull from medium
    random.shuffle(easy)
    random.shuffle(medium)
    random.shuffle(hard)

    selected_easy = easy[:target_easy]
    shortfall_easy = max(0, target_easy - len(selected_easy))

    selected_hard = hard[:target_hard]
    shortfall_hard = max(0, target_hard - len(selected_hard))

    # Medium absorbs any shortfall
    total_medium_needed = target_medium + shortfall_easy + shortfall_hard
    selected_medium = medium[:total_medium_needed]

    selected = selected_easy + selected_medium + selected_hard

    if len(selected) < 50:
        print(f"WARNING: Only {len(selected)} tasks selected (target: 50). "
              f"Not enough tasks in available tiers.", file=sys.stderr)

    print(f"\nSelected {len(selected)} tasks:")
    print(f"  Easy:   {len(selected_easy)}")
    print(f"  Medium: {len(selected_medium)}")
    print(f"  Hard:   {len(selected_hard)}")

    # Write selection log
    selection_log = []
    for entry in selected:
        selection_log.append({
            "task_id": entry["task_id"],
            "difficulty": entry["difficulty"],
            "difficulty_score": round(entry.get("difficulty_score", 0), 4),
            "features": entry["features"],
            "sha256": entry["sha256"],
        })

    log_path = OUTPUT_DIR / "selection-log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(selection_log, f, indent=2)
    print(f"\nSelection log written to {log_path}")

    # Write exclusion log
    excl_path = OUTPUT_DIR / "exclusion-log.json"
    with open(excl_path, "w", encoding="utf-8") as f:
        json.dump(exclusions, f, indent=2)
    print(f"Exclusion log written to {excl_path}")

    # Copy selected task files
    copied = 0
    for entry in selected:
        src = Path(entry["source_path"])
        dst = OUTPUT_DIR / f"{entry['task_id']}.json"
        shutil.copy2(src, dst)
        copied += 1
    print(f"Copied {copied} task JSON files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
