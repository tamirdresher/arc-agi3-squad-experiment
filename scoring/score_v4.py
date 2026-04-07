#!/usr/bin/env python3
"""
ARC Experiment V4 — Scoring Module

Evaluates model solutions against task-defined scoring criteria.
Supports test_suite, exact_match, and f1_score methods.

Usage (standalone):
    python score_v4.py --task task.yaml --solution solution.txt

Usage (as module):
    from scoring.score_v4 import score_solution
    result = score_solution(task_data, extracted_solution)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Solution extraction
# ---------------------------------------------------------------------------

def extract_solution(response: str, output_format: str) -> Optional[str]:
    """Extract the solution from a model response using the SOLUTION: marker.

    Uses the LAST occurrence of SOLUTION: to handle cases where the model
    mentions the marker in its reasoning before the actual solution.

    Args:
        response: Raw model response text.
        output_format: Expected output format (code_block, unified_diff, etc.).

    Returns:
        Extracted solution text, or None if extraction fails.
    """
    if not response:
        return None

    marker = "SOLUTION:"
    idx = response.rfind(marker)
    if idx == -1:
        # Fallback: try to find a code block anyway
        return _extract_code_block_fallback(response, output_format)

    solution_text = response[idx + len(marker):].strip()

    # Extract code block if present
    if "```" in solution_text:
        try:
            start = solution_text.index("```")
            # Skip language identifier line
            code_start = solution_text.index("\n", start) + 1
            end = solution_text.index("```", code_start)
            return solution_text[code_start:end].strip()
        except ValueError:
            # Malformed code block — return everything after marker
            pass

    return solution_text.strip() if solution_text.strip() else None


def _extract_code_block_fallback(response: str, output_format: str) -> Optional[str]:
    """Fallback extraction: find the last code block in the response."""
    blocks = re.findall(r"```(?:\w+)?\s*\n(.*?)```", response, re.DOTALL)
    if blocks:
        return blocks[-1].strip()
    return None


# ---------------------------------------------------------------------------
# ARC compliance scoring
# ---------------------------------------------------------------------------

def compute_arc_compliance(response: str) -> int:
    """Score ARC compliance on a 0-4 scale.

    Checks for the presence of EXPLORE, MODEL, GOAL, EXECUTE section headers
    in the model's response (case-insensitive, flexible formatting).

    Args:
        response: Raw model response text.

    Returns:
        Integer 0-4 indicating how many pillar headers were found.
    """
    compliance = 0
    patterns = [
        r"(?i)\b(step\s*1|explore)\b.*?:",   # EXPLORE
        r"(?i)\b(step\s*2|model)\b.*?:",      # MODEL
        r"(?i)\b(step\s*3|goal)\b.*?:",       # GOAL
        r"(?i)\b(step\s*4|execute)\b.*?:",    # EXECUTE
    ]
    for pattern in patterns:
        if re.search(pattern, response):
            compliance += 1
    return compliance


# ---------------------------------------------------------------------------
# Scoring methods
# ---------------------------------------------------------------------------

def score_solution(
    task_data: dict[str, Any],
    extracted_solution: Optional[str],
    timeout: int = 30,
) -> dict[str, Any]:
    """Score an extracted solution against a task's scoring criteria.

    Args:
        task_data: Parsed task YAML data (dict).
        extracted_solution: The model's extracted solution text.
        timeout: Maximum seconds for test execution.

    Returns:
        Dict with keys: pass, score_detail, error.
    """
    if extracted_solution is None:
        return {
            "pass": False,
            "score_detail": {"reason": "extraction_failure"},
            "error": "Could not extract solution from model response",
        }

    scoring = task_data.get("scoring", {})
    method = scoring.get("method", "test_suite")

    if method == "test_suite":
        return _score_test_suite(task_data, extracted_solution, timeout)
    elif method == "exact_match":
        return _score_exact_match(task_data, extracted_solution)
    elif method == "f1_score":
        return _score_f1(task_data, extracted_solution)
    else:
        return {
            "pass": False,
            "score_detail": {"reason": f"unknown_method: {method}"},
            "error": f"Unknown scoring method: {method}",
        }


def _score_test_suite(
    task_data: dict[str, Any],
    solution: str,
    timeout: int,
) -> dict[str, Any]:
    """Score by writing solution to a temp dir and running the test script.

    Creates an isolated temp directory, writes the solution as solution.py,
    writes the test_script from the task YAML, and runs it with Python.
    """
    scoring = task_data.get("scoring", {})
    test_script = scoring.get("test_script", "")

    if not test_script:
        # Try test_command for non-inline tests
        test_command = scoring.get("test_command", "")
        if test_command:
            return {
                "pass": False,
                "score_detail": {"reason": "test_command_not_supported_in_pilot"},
                "error": "Pilot scorer only supports inline test_script, not test_command",
            }
        return {
            "pass": False,
            "score_detail": {"reason": "no_test_script"},
            "error": "Task has no test_script in scoring section",
        }

    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="arc_v4_score_")

        # Write the model's solution
        solution_path = os.path.join(tmp_dir, "solution.py")
        with open(solution_path, "w", encoding="utf-8") as f:
            f.write(solution)

        # Also write any context files the test might import
        for ctx_file in task_data.get("context_files", []):
            ctx_path = os.path.join(tmp_dir, os.path.basename(ctx_file["path"]))
            with open(ctx_path, "w", encoding="utf-8") as f:
                f.write(ctx_file.get("content", ""))

        # Write the test script
        test_path = os.path.join(tmp_dir, "run_test.py")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_script)

        # Execute the test
        result = subprocess.run(
            [sys.executable, "run_test.py"],
            cwd=tmp_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        passed = result.returncode == 0
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        return {
            "pass": passed,
            "score_detail": {
                "exit_code": result.returncode,
                "stdout": stdout[:2000],
                "stderr": stderr[:2000],
            },
            "error": None if passed else stderr[:500] or "Tests failed",
        }

    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score_detail": {"reason": "timeout", "timeout_seconds": timeout},
            "error": f"Test execution timed out after {timeout}s",
        }
    except Exception as exc:
        return {
            "pass": False,
            "score_detail": {"reason": "scoring_error"},
            "error": str(exc)[:500],
        }
    finally:
        if tmp_dir and os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _score_exact_match(
    task_data: dict[str, Any],
    solution: str,
) -> dict[str, Any]:
    """Score by exact string comparison against expected output."""
    scoring = task_data.get("scoring", {})
    expected = scoring.get("expected_output", "").strip()

    if not expected:
        return {
            "pass": False,
            "score_detail": {"reason": "no_expected_output"},
            "error": "Task has no expected_output for exact_match scoring",
        }

    # Normalize whitespace for comparison
    norm_solution = " ".join(solution.split())
    norm_expected = " ".join(expected.split())
    passed = norm_solution == norm_expected

    return {
        "pass": passed,
        "score_detail": {
            "match": passed,
            "expected_len": len(expected),
            "solution_len": len(solution),
        },
        "error": None if passed else "Solution does not match expected output",
    }


def _score_f1(
    task_data: dict[str, Any],
    solution: str,
) -> dict[str, Any]:
    """Score by F1 of identified issues against ground truth.

    For code review tasks: the solution lists bugs, and we compare against
    the ground truth bug list using keyword/phrase matching.
    """
    scoring = task_data.get("scoring", {})
    ground_truth_issues = scoring.get("ground_truth_issues", [])

    if not ground_truth_issues:
        return {
            "pass": False,
            "score_detail": {"reason": "no_ground_truth_issues"},
            "error": "Task has no ground_truth_issues for f1_score scoring",
        }

    # Extract identified bugs from solution
    solution_lower = solution.lower()
    true_positives = 0
    for issue in ground_truth_issues:
        # Check if any keyword from the issue appears in the solution
        issue_keywords = issue.lower().split("_")
        if any(kw in solution_lower for kw in issue_keywords if len(kw) > 2):
            true_positives += 1

    # Count predicted bugs (lines starting with BUG or numbered items)
    predicted_lines = re.findall(
        r"(?:^|\n)\s*(?:BUG\s*\d+|[\d]+[\.\):])\s*.*",
        solution,
        re.IGNORECASE,
    )
    predicted_count = max(len(predicted_lines), 1)

    precision = true_positives / predicted_count if predicted_count > 0 else 0
    recall = true_positives / len(ground_truth_issues) if ground_truth_issues else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    passed = f1 >= 0.8

    return {
        "pass": passed,
        "score_detail": {
            "f1": round(f1, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "true_positives": true_positives,
            "total_ground_truth": len(ground_truth_issues),
            "predicted_count": predicted_count,
        },
        "error": None if passed else f"F1={f1:.3f} < 0.8 threshold",
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Score a solution from command line."""
    import argparse

    try:
        import yaml
    except ImportError:
        print("ERROR: pyyaml required. pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="ARC V4 Scorer")
    parser.add_argument("--task", required=True, help="Path to task YAML file")
    parser.add_argument("--solution", required=True, help="Path to solution text file")
    parser.add_argument("--timeout", type=int, default=30, help="Scoring timeout (seconds)")
    args = parser.parse_args()

    with open(args.task, "r", encoding="utf-8") as f:
        task_data = yaml.safe_load(f)

    with open(args.solution, "r", encoding="utf-8") as f:
        solution = f.read()

    result = score_solution(task_data, solution, timeout=args.timeout)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
