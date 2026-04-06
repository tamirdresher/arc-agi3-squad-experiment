#!/usr/bin/env python3
"""
ARC-AGI Squad Experiment V3.1 — Scoring Module

Implements protocol §5.1-5.2:
  - exact_match: binary grid comparison
  - cell_accuracy: proportion of matching cells
  - dimension_match: whether predicted grid has correct dimensions
  - extract_grid: robust grid extraction from LLM response text
"""

from __future__ import annotations

import json
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Scoring functions (§5.1)
# ---------------------------------------------------------------------------


def exact_match(predicted: list[list[int]], ground_truth: list[list[int]]) -> bool:
    """Binary exact match: True if all cells match, False otherwise."""
    if len(predicted) != len(ground_truth):
        return False
    for pred_row, gt_row in zip(predicted, ground_truth):
        if len(pred_row) != len(gt_row):
            return False
        if pred_row != gt_row:
            return False
    return True


def cell_accuracy(predicted: list[list[int]], ground_truth: list[list[int]]) -> float:
    """Proportion of cells matching ground truth.

    Handles dimension mismatches by only scoring the overlapping region.
    Non-overlapping cells count as incorrect.
    """
    gt_rows = len(ground_truth)
    gt_cols = len(ground_truth[0]) if gt_rows > 0 else 0
    total_cells = gt_rows * gt_cols

    if total_cells == 0:
        return 1.0 if len(predicted) == 0 else 0.0

    pred_rows = len(predicted)
    pred_cols = len(predicted[0]) if pred_rows > 0 else 0

    matching_cells = 0
    for r in range(gt_rows):
        for c in range(gt_cols):
            if r < pred_rows and c < pred_cols:
                if predicted[r][c] == ground_truth[r][c]:
                    matching_cells += 1

    return matching_cells / total_cells


def dimension_match(predicted: list[list[int]], ground_truth: list[list[int]]) -> bool:
    """Does the predicted grid have correct dimensions?"""
    if len(predicted) != len(ground_truth):
        return False
    for pred_row, gt_row in zip(predicted, ground_truth):
        if len(pred_row) != len(gt_row):
            return False
    return True


# ---------------------------------------------------------------------------
# Output extraction (§5.2)
# ---------------------------------------------------------------------------


def _repair_json(text: str) -> str:
    """Repair common JSON formatting issues from LLM output.

    Handles trailing commas, stray whitespace in arrays, and
    other minor formatting problems.
    """
    # Remove trailing commas before ] or }
    text = re.sub(r',\s*\]', ']', text)
    text = re.sub(r',\s*\}', '}', text)
    return text


def _is_valid_grid(grid) -> bool:
    """Check if a parsed JSON value is a valid ARC grid.

    Valid grid: non-empty list of lists, all cells are ints 0-9,
    all rows have the same length.
    """
    if not isinstance(grid, list) or len(grid) == 0:
        return False
    if not all(isinstance(row, list) for row in grid):
        return False
    if not all(
        isinstance(cell, int) and 0 <= cell <= 9
        for row in grid
        for cell in row
    ):
        return False
    # All rows must have the same length
    row_lengths = set(len(row) for row in grid)
    if len(row_lengths) != 1:
        return False
    if 0 in row_lengths:
        return False
    return True


def _is_training_grid(grid, task_json: Optional[dict] = None) -> bool:
    """Check if extracted grid matches any training input or output.

    Prevents the extractor from returning a training example that
    the model reproduced during reasoning rather than the actual answer.
    """
    if task_json is None:
        return False
    for pair in task_json.get("train", []):
        if grid == pair.get("input"):
            return True
        if grid == pair.get("output"):
            return True
    # Also check test input (model might echo it)
    for pair in task_json.get("test", []):
        if grid == pair.get("input"):
            return True
    return False


def extract_grid(
    response_text: str,
    task_json: Optional[dict] = None,
) -> Optional[list[list[int]]]:
    """Extract the output grid from the model's response.

    Priority:
      1. Look for 'ANSWER:' marker and parse JSON after it
      2. Find the last valid JSON array of arrays in the response
      3. Return None if no valid grid found

    If task_json is provided, validates that extracted grid is not
    a training example (which would indicate extraction error).
    """
    # Strategy 1: ANSWER marker
    answer_match = re.search(r'ANSWER:\s*(\[[\s\S]*)', response_text, re.IGNORECASE)
    if answer_match:
        text_after_marker = answer_match.group(1)
        grid = _try_parse_grid(text_after_marker, task_json)
        if grid is not None:
            return grid

    # Strategy 2: Last valid JSON array of arrays
    candidates = _find_json_arrays(response_text)
    for candidate in reversed(candidates):
        grid = _try_parse_grid(candidate, task_json)
        if grid is not None:
            return grid

    return None  # Extraction failed


def _try_parse_grid(
    text: str,
    task_json: Optional[dict] = None,
) -> Optional[list[list[int]]]:
    """Try to parse a JSON grid from text, with repair and validation."""
    # Find the first complete top-level array
    bracket_depth = 0
    start = None
    for i, char in enumerate(text):
        if char == '[' and bracket_depth == 0:
            start = i
        if char == '[':
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
            if bracket_depth == 0 and start is not None:
                candidate = text[start:i + 1]
                try:
                    repaired = _repair_json(candidate)
                    grid = json.loads(repaired)
                    if _is_valid_grid(grid) and not _is_training_grid(grid, task_json):
                        return grid
                except (json.JSONDecodeError, ValueError):
                    pass
                start = None
    return None


def _find_json_arrays(text: str) -> list[str]:
    """Find all top-level JSON arrays in text."""
    bracket_depth = 0
    candidates = []
    start = None
    for i, char in enumerate(text):
        if char == '[' and bracket_depth == 0:
            start = i
        if char == '[':
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
            if bracket_depth == 0 and start is not None:
                candidates.append(text[start:i + 1])
                start = None
    return candidates


def score_run(
    response_text: str,
    ground_truth: list[list[int]],
    task_json: Optional[dict] = None,
) -> dict:
    """Score a single run.

    Returns a dict with all scoring metrics and extraction metadata.
    """
    predicted = extract_grid(response_text, task_json)

    if predicted is None:
        return {
            "extraction_success": False,
            "predicted_grid": None,
            "exact_match": False,
            "cell_accuracy": 0.0,
            "dimension_match": False,
            "predicted_rows": None,
            "predicted_cols": None,
            "ground_truth_rows": len(ground_truth),
            "ground_truth_cols": len(ground_truth[0]) if ground_truth else 0,
        }

    return {
        "extraction_success": True,
        "predicted_grid": predicted,
        "exact_match": exact_match(predicted, ground_truth),
        "cell_accuracy": round(cell_accuracy(predicted, ground_truth), 6),
        "dimension_match": dimension_match(predicted, ground_truth),
        "predicted_rows": len(predicted),
        "predicted_cols": len(predicted[0]) if predicted else 0,
        "ground_truth_rows": len(ground_truth),
        "ground_truth_cols": len(ground_truth[0]) if ground_truth else 0,
    }
