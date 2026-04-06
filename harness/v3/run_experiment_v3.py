#!/usr/bin/env python3
"""
ARC-AGI Squad Experiment V3.1 — Execution Harness

Automates 750 experimental runs: 50 tasks × 3 conditions × 5 runs.
Uses Copilot Chat API (cost = $0). Single-turn execution for all tasks.

Usage:
    python harness/v3/run_experiment_v3.py                    # full run
    python harness/v3/run_experiment_v3.py --resume            # resume from checkpoint
    python harness/v3/run_experiment_v3.py --dry-run           # test without API calls
    python harness/v3/run_experiment_v3.py --task TASKID       # run one task only
    python harness/v3/run_experiment_v3.py --limit 15          # run first N from run order
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

# Ensure harness/v3 is importable for score module
HARNESS_DIR = Path(__file__).resolve().parent
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

from score import extract_grid, score_run  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CONDITIONS = ("baseline", "chain-of-thought", "arc-informed")
DEFAULT_MODEL = "claude-sonnet-4"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
COPILOT_API_URL = "https://api.githubcopilot.com/chat/completions"
COPILOT_API_TIMEOUT = 300  # 5 minutes
COPILOT_API_HEADERS_STATIC = {
    "Content-Type": "application/json",
    "Editor-Version": "vscode/1.90.0",
    "Editor-Plugin-Version": "copilot/1.0.0",
    "Copilot-Integration-Id": "vscode-chat",
}

CEILING_CHECK_TASK_COUNT = 10
CEILING_THRESHOLD = 0.70  # Baseline >70% triggers warning

# Paths (relative to ARC_ROOT)
ARC_ROOT = HARNESS_DIR.parent.parent  # C:\temp\arc-experiment
TASK_DIR = ARC_ROOT / "tasks" / "v3"
PROMPT_DIR = ARC_ROOT / "prompts" / "v3"
RESULTS_DIR = ARC_ROOT / "results" / "v3"
SCORES_DIR = RESULTS_DIR / "scores"
RAW_DIR = RESULTS_DIR / "raw"
RUN_ORDER_PATH = ARC_ROOT / "runs" / "v3-run-order.json"

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_gh_auth_token: Optional[str] = None


def _get_gh_token() -> str:
    """Retrieve the GitHub auth token via `gh auth token`."""
    global _gh_auth_token
    if _gh_auth_token is not None:
        return _gh_auth_token

    # Try environment variable first
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        _gh_auth_token = env_token
        return _gh_auth_token

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError(f"gh auth token failed: {result.stderr.strip()}")
        _gh_auth_token = result.stdout.strip()
        if not _gh_auth_token:
            raise RuntimeError("gh auth token returned empty string")
        return _gh_auth_token
    except FileNotFoundError:
        raise RuntimeError("gh CLI not found on PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError("gh auth token timed out")


def _refresh_gh_token() -> str:
    """Force-refresh the GitHub auth token."""
    global _gh_auth_token
    _gh_auth_token = None
    return _get_gh_token()


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------


def load_prompt_templates() -> dict[str, dict[str, str]]:
    """Load all prompt templates from prompts/v3/."""
    templates = {}
    for condition, prefix in [
        ("baseline", "baseline"),
        ("chain-of-thought", "cot"),
        ("arc-informed", "arc"),
    ]:
        sys_path = PROMPT_DIR / f"{prefix}-system.txt"
        user_path = PROMPT_DIR / f"{prefix}-user-template.txt"

        with open(sys_path, "r", encoding="utf-8") as f:
            system_text = f.read().strip()
        with open(user_path, "r", encoding="utf-8") as f:
            user_template = f.read().strip()

        templates[condition] = {
            "system": system_text,
            "user_template": user_template,
        }
    return templates


def render_grid_data(task_json: dict) -> str:
    """Render the training examples and test input as grid data block."""
    lines = []
    for i, pair in enumerate(task_json["train"], 1):
        lines.append(f"Example {i}:")
        lines.append("Input:")
        lines.append(json.dumps(pair["input"]))
        lines.append("")
        lines.append("Output:")
        lines.append(json.dumps(pair["output"]))
        lines.append("")

    lines.append("Test Input:")
    lines.append(json.dumps(task_json["test"][0]["input"]))

    return "\n".join(lines)


def build_prompt(
    task_json: dict,
    condition: str,
    templates: dict[str, dict[str, str]],
) -> tuple[str, str]:
    """Build system and user prompts for a task + condition.

    Returns (system_prompt, user_prompt).
    """
    tmpl = templates[condition]
    grid_data = render_grid_data(task_json)
    user_prompt = tmpl["user_template"].replace("{grid_data}", grid_data)
    return tmpl["system"], user_prompt


# ---------------------------------------------------------------------------
# API invocation
# ---------------------------------------------------------------------------


def warmup_copilot_api(logger: logging.Logger) -> None:
    """Validate API connectivity with a minimal request."""
    token = _get_gh_token()
    headers = {**COPILOT_API_HEADERS_STATIC, "Authorization": f"Bearer {token}"}
    body = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": "Say OK"}],
        "stream": False,
    }

    for attempt in range(1, 4):
        try:
            resp = requests.post(
                COPILOT_API_URL, headers=headers, json=body, timeout=30,
            )
            if resp.status_code == 200:
                logger.info("Copilot API warmup OK (attempt %d)", attempt)
                return
            elif resp.status_code == 403:
                logger.warning("Warmup 403 (attempt %d) — refreshing token", attempt)
                token = _refresh_gh_token()
                headers["Authorization"] = f"Bearer {token}"
                time.sleep(RETRY_BASE_DELAY * attempt)
            else:
                logger.warning("Warmup HTTP %d (attempt %d)", resp.status_code, attempt)
                time.sleep(RETRY_BASE_DELAY * attempt)
        except Exception as exc:
            logger.warning("Warmup error (attempt %d): %s", attempt, exc)
            time.sleep(RETRY_BASE_DELAY * attempt)

    logger.warning("Warmup failed after 3 attempts — proceeding anyway")


def invoke_copilot_api(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    *,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> tuple[str, Optional[int], float]:
    """Call the Copilot Chat API. Returns (response_text, tokens, wall_seconds)."""
    if dry_run:
        stub = (
            f"[DRY RUN] Model={model} | "
            f"System={len(system_prompt)} chars | User={len(user_prompt)} chars\n"
            f"ANSWER: [[0, 1], [1, 0]]"
        )
        return stub, None, 0.5

    token = _get_gh_token()
    headers = {**COPILOT_API_HEADERS_STATIC, "Authorization": f"Bearer {token}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }

    start_time = time.monotonic()
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                COPILOT_API_URL,
                headers=headers,
                json=payload,
                timeout=COPILOT_API_TIMEOUT,
            )

            # Refresh token on 403
            if resp.status_code == 403:
                if logger:
                    logger.warning("API 403 (attempt %d) — refreshing token", attempt)
                token = _refresh_gh_token()
                headers["Authorization"] = f"Bearer {token}"
                time.sleep(RETRY_BASE_DELAY ** attempt)
                continue

            if resp.status_code != 200:
                try:
                    err_body = resp.json()
                    err_msg = err_body.get("error", {}).get("message", resp.text[:300])
                except Exception:
                    err_msg = resp.text[:300]
                last_error = f"HTTP {resp.status_code}: {err_msg}"
                if logger:
                    logger.warning("API error (attempt %d): %s", attempt, last_error)
                time.sleep(RETRY_BASE_DELAY ** attempt)
                continue

            # Success
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                last_error = "No choices in response"
                continue

            response_text = choices[0].get("message", {}).get("content", "")
            usage = data.get("usage")
            tokens_used = usage.get("total_tokens") if usage else None
            wall_seconds = time.monotonic() - start_time

            return response_text, tokens_used, wall_seconds

        except requests.exceptions.Timeout:
            last_error = f"Timeout after {COPILOT_API_TIMEOUT}s"
            if logger:
                logger.warning("API timeout (attempt %d)", attempt)
            time.sleep(RETRY_BASE_DELAY ** attempt)
        except requests.exceptions.ConnectionError as exc:
            last_error = f"Connection error: {exc}"
            if logger:
                logger.warning("API connection error (attempt %d): %s", attempt, exc)
            time.sleep(RETRY_BASE_DELAY ** attempt)

    wall_seconds = time.monotonic() - start_time
    raise RuntimeError(f"API failed after {MAX_RETRIES} retries: {last_error}")


# ---------------------------------------------------------------------------
# Run management
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_run_id(task_id: str, condition: str, run_number: int) -> str:
    return f"{task_id}_{condition}_{run_number}"


def is_run_completed(task_id: str, condition: str, run_number: int) -> bool:
    """Check if a run has already been completed (for resume)."""
    score_path = SCORES_DIR / task_id / condition / str(run_number) / "score.json"
    return score_path.exists()


def save_run_results(
    task_id: str,
    condition: str,
    run_number: int,
    transcript: str,
    extracted_grid: Optional[list[list[int]]],
    score_data: dict,
    tokens: Optional[int],
    wall_seconds: float,
) -> None:
    """Save all artifacts for a completed run."""
    # Raw transcript
    raw_path = RAW_DIR / task_id / condition / str(run_number)
    raw_path.mkdir(parents=True, exist_ok=True)
    (raw_path / "transcript.txt").write_text(transcript, encoding="utf-8")
    (raw_path / "extracted_grid.json").write_text(
        json.dumps(extracted_grid, indent=2) if extracted_grid else "null",
        encoding="utf-8",
    )

    # Score
    score_path = SCORES_DIR / task_id / condition / str(run_number)
    score_path.mkdir(parents=True, exist_ok=True)

    full_score = {
        "task_id": task_id,
        "condition": condition,
        "run_number": run_number,
        "timestamp": _now_iso(),
        "tokens_used": tokens,
        "wall_clock_seconds": round(wall_seconds, 2),
        "response_hash": _sha256(transcript),
        **score_data,
    }
    # Don't save the full predicted grid in score.json (too large)
    full_score.pop("predicted_grid", None)

    (score_path / "score.json").write_text(
        json.dumps(full_score, indent=2), encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Ceiling effect check (§3.7)
# ---------------------------------------------------------------------------


def check_ceiling_effect(logger: logging.Logger) -> bool:
    """After first 10 tasks complete, check if Baseline >70%.

    Returns True if ceiling effect detected (should pause).
    """
    baseline_scores = []
    task_ids_checked = set()

    if not SCORES_DIR.exists():
        return False

    for task_dir in SCORES_DIR.iterdir():
        if not task_dir.is_dir():
            continue
        baseline_dir = task_dir / "baseline"
        if not baseline_dir.exists():
            continue

        # Check if all 5 runs completed for this task's baseline
        run_scores = []
        for run_num in range(1, 6):
            score_file = baseline_dir / str(run_num) / "score.json"
            if score_file.exists():
                with open(score_file) as f:
                    data = json.load(f)
                run_scores.append(data.get("exact_match", False))

        if len(run_scores) == 5:
            task_ids_checked.add(task_dir.name)
            baseline_scores.extend(run_scores)

    if len(task_ids_checked) < CEILING_CHECK_TASK_COUNT:
        return False  # Not enough data yet

    accuracy = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0
    logger.info(
        "Ceiling check: %d tasks, %d runs, Baseline accuracy = %.1f%%",
        len(task_ids_checked), len(baseline_scores), accuracy * 100,
    )

    if accuracy > CEILING_THRESHOLD:
        logger.warning(
            "⚠️  CEILING EFFECT DETECTED: Baseline accuracy %.1f%% > %.0f%% threshold. "
            "PAUSING execution per protocol §3.7.",
            accuracy * 100, CEILING_THRESHOLD * 100,
        )
        return True
    return False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging(output_dir: Path) -> logging.Logger:
    """Configure console + file logging."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("arc_v3_experiment")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(output_dir / "experiment_v3.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Main execution loop
# ---------------------------------------------------------------------------


def load_run_order() -> list[dict]:
    """Load the deterministic run order from runs/v3-run-order.json."""
    if not RUN_ORDER_PATH.exists():
        print(f"ERROR: Run order not found at {RUN_ORDER_PATH}", file=sys.stderr)
        print("Generate it first with: python harness/v3/generate_run_order.py", file=sys.stderr)
        sys.exit(1)
    with open(RUN_ORDER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_task_json(task_id: str) -> dict:
    """Load a task JSON file from tasks/v3/."""
    path = TASK_DIR / f"{task_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Task not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_experiment(args: argparse.Namespace) -> None:
    """Main experiment execution."""
    logger = setup_logging(RESULTS_DIR)
    logger.info("=" * 60)
    logger.info("ARC-AGI Squad Experiment V3.1 — Execution Harness")
    logger.info("=" * 60)
    logger.info("Model: %s", args.model)
    logger.info("Dry run: %s", args.dry_run)
    logger.info("Resume: %s", args.resume)

    # Load templates
    templates = load_prompt_templates()
    logger.info("Loaded prompt templates for %d conditions", len(templates))

    # Load run order
    run_order = load_run_order()
    logger.info("Run order: %d total runs", len(run_order))

    # Filter if needed
    if args.task:
        run_order = [r for r in run_order if r["task_id"] == args.task]
        logger.info("Filtered to task %s: %d runs", args.task, len(run_order))

    if args.limit:
        run_order = run_order[:args.limit]
        logger.info("Limited to first %d runs", args.limit)

    # Warmup API
    if not args.dry_run:
        warmup_copilot_api(logger)

    # Track progress
    completed = 0
    skipped = 0
    failed = 0
    total = len(run_order)
    ceiling_checked = False

    for idx, run_spec in enumerate(run_order, 1):
        task_id = run_spec["task_id"]
        condition = run_spec["condition"]
        run_number = run_spec["run_number"]
        run_id = _make_run_id(task_id, condition, run_number)

        # Resume: skip completed runs
        if args.resume and is_run_completed(task_id, condition, run_number):
            skipped += 1
            continue

        logger.info(
            "[%d/%d] %s | %s | run %d",
            idx, total, task_id, condition, run_number,
        )

        try:
            # Load task
            task_json = load_task_json(task_id)
            ground_truth = task_json["test"][0]["output"]

            # Build prompt
            system_prompt, user_prompt = build_prompt(task_json, condition, templates)

            # Invoke API
            response_text, tokens, wall_seconds = invoke_copilot_api(
                system_prompt, user_prompt, args.model,
                dry_run=args.dry_run, logger=logger,
            )

            # Score
            score_data = score_run(response_text, ground_truth, task_json)

            # Save
            save_run_results(
                task_id, condition, run_number,
                response_text,
                score_data.get("predicted_grid"),
                score_data,
                tokens, wall_seconds,
            )

            completed += 1
            status = "✓" if score_data["exact_match"] else "✗"
            logger.info(
                "  %s exact=%s cell_acc=%.3f dim=%s tokens=%s %.1fs",
                status,
                score_data["exact_match"],
                score_data["cell_accuracy"],
                score_data["dimension_match"],
                tokens or "?",
                wall_seconds,
            )

        except Exception as exc:
            failed += 1
            logger.error("  FAILED: %s", exc)
            # Save error marker
            score_path = SCORES_DIR / task_id / condition / str(run_number)
            score_path.mkdir(parents=True, exist_ok=True)
            (score_path / "error.json").write_text(
                json.dumps({"error": str(exc), "timestamp": _now_iso()}),
                encoding="utf-8",
            )

        # Ceiling effect check after first N tasks
        if not ceiling_checked and not args.dry_run:
            tasks_with_baseline = set()
            if SCORES_DIR.exists():
                for td in SCORES_DIR.iterdir():
                    if td.is_dir() and (td / "baseline").is_dir():
                        runs_done = sum(
                            1 for rn in range(1, 6)
                            if (td / "baseline" / str(rn) / "score.json").exists()
                        )
                        if runs_done == 5:
                            tasks_with_baseline.add(td.name)

            if len(tasks_with_baseline) >= CEILING_CHECK_TASK_COUNT:
                if check_ceiling_effect(logger):
                    logger.warning("Execution PAUSED due to ceiling effect.")
                    logger.warning("Review results and amend protocol before continuing.")
                    break
                ceiling_checked = True

    logger.info("=" * 60)
    logger.info(
        "Done. Completed=%d Skipped=%d Failed=%d Total=%d",
        completed, skipped, failed, total,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ARC-AGI V3.1 Experiment Harness",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--task", default=None,
        help="Run only the specified task ID",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Run only the first N entries from the run order",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Test run without API calls",
    )
    parser.add_argument(
        "--resume", action="store_true", default=True,
        help="Skip already-completed runs (default: True)",
    )
    parser.add_argument(
        "--no-resume", action="store_false", dest="resume",
        help="Re-run even completed runs",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_experiment(args)
