#!/usr/bin/env python3
"""
ARC Experiment V4 — Execution Harness

Automates experimental runs: tasks × 3 conditions × N repetitions.
Calls Copilot Chat API with temperature=1.0, model=claude-sonnet-4-20250514.

Usage:
    python run_experiment_v4.py --task-dir tasks/v4 --dry-run
    python run_experiment_v4.py --task-dir tasks/v4 --pilot --dry-run
    python run_experiment_v4.py --task-dir tasks/v4 --pilot
    python run_experiment_v4.py --task-dir tasks/v4 --reps 5
    python run_experiment_v4.py --resume
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

# Append parent so we can import the scorer
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scoring.score_v4 import extract_solution, compute_arc_compliance, score_solution


# ===========================================================================
# Constants
# ===========================================================================

VALID_CONDITIONS = ("baseline", "cot", "arc")
DEFAULT_MODEL = "claude-sonnet-4"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_MAX_TOKENS = 8192
DEFAULT_REPS = 5
PILOT_TASK_LIMIT = 10
PILOT_REPS = 1
MAX_API_RETRIES = 3
RETRY_BASE_DELAY = 2.0

# Copilot Chat API
COPILOT_API_URL = "https://api.githubcopilot.com/chat/completions"
COPILOT_API_TIMEOUT = 300  # 5 minutes
COPILOT_HEADERS_STATIC = {
    "Content-Type": "application/json",
    "Editor-Version": "vscode/1.90.0",
    "Editor-Plugin-Version": "copilot/1.0.0",
    "Copilot-Integration-Id": "vscode-chat",
}

# Cached GitHub auth token
_gh_auth_token: Optional[str] = None


# ===========================================================================
# Output format instruction templates (from protocol §3.4)
# ===========================================================================

OUTPUT_FORMAT_INSTRUCTIONS = {
    "unified_diff": (
        "Provide your fix as a unified diff (patch format). Start your answer with:\n"
        "SOLUTION:\n"
        "```diff\n"
        "--- a/path/to/file.py\n"
        "+++ b/path/to/file.py\n"
        "@@ ... @@\n"
        " context line\n"
        "-removed line\n"
        "+added line\n"
        "```"
    ),
    "code_block": (
        "Provide your solution as complete Python code. Start your answer with:\n"
        "SOLUTION:\n"
        "```python\n"
        "# your solution code\n"
        "```"
    ),
    "json_answer": (
        "Provide your answer as a JSON object. Start your answer with:\n"
        "SOLUTION:\n"
        "```json\n"
        "{...}\n"
        "```"
    ),
    "review_list": (
        "List all bugs you find. Start your answer with:\n"
        "SOLUTION:\n"
        "BUG 1: [file:line] description\n"
        "BUG 2: [file:line] description\n"
        "..."
    ),
    "function": (
        "Provide your solution as a complete Python function. Start your answer with:\n"
        "SOLUTION:\n"
        "```python\n"
        "def solution_function(...):\n"
        "    ...\n"
        "```"
    ),
    "file": (
        "Provide the complete modified file. Start your answer with:\n"
        "SOLUTION:\n"
        "```python\n"
        "# complete file content\n"
        "```"
    ),
    "bug_list": (
        "List all bugs you find. Start your answer with:\n"
        "SOLUTION:\n"
        "BUG 1: [file:line] description\n"
        "BUG 2: [file:line] description\n"
        "..."
    ),
}


# ===========================================================================
# Prompt templates (from revised protocol §3.1–3.3)
# ===========================================================================

def _format_context_files(context_files: list[dict]) -> str:
    """Format context files into a readable block for the prompt."""
    parts = []
    for cf in context_files:
        path = cf.get("path", "unknown")
        content = cf.get("content", "")
        parts.append(f"File: {path}\n```\n{content.rstrip()}\n```")
    return "\n\n".join(parts)


def build_prompt(task: dict, condition: str) -> str:
    """Assemble the full user prompt for a given task and condition.

    Returns a single user-message string (no separate system message —
    V4 protocol uses user-only format per §4.2).
    """
    problem = task.get("problem", "").strip()
    context_files = task.get("context_files", [])
    output_format = task.get("output_format", "code_block")

    context_block = _format_context_files(context_files)
    fmt_instructions = OUTPUT_FORMAT_INSTRUCTIONS.get(
        output_format,
        OUTPUT_FORMAT_INSTRUCTIONS["code_block"],
    )

    if condition == "baseline":
        return _prompt_baseline(problem, context_block, fmt_instructions)
    elif condition == "cot":
        return _prompt_cot(problem, context_block, fmt_instructions)
    elif condition == "arc":
        return _prompt_arc(problem, context_block, fmt_instructions)
    else:
        raise ValueError(f"Unknown condition: {condition}")


def _prompt_baseline(problem: str, context: str, fmt: str) -> str:
    """Protocol §3.1 — Baseline condition prompt."""
    return (
        f"You are a software engineer. Solve the following task.\n\n"
        f"{problem}\n\n"
        f"{context}\n\n"
        f"Provide your solution below.\n\n"
        f"Provide your solution in the following format:\n"
        f"{fmt}"
    )


def _prompt_cot(problem: str, context: str, fmt: str) -> str:
    """Protocol §3.2 — Enriched Chain-of-Thought condition prompt."""
    return (
        f"You are a software engineer. Solve the following task by thinking step by step.\n\n"
        f"{problem}\n\n"
        f"{context}\n\n"
        f"Instructions:\n"
        f"1. First, think through the problem step by step. Show your reasoning.\n"
        f"2. Consider what could go wrong with your approach.\n"
        f"3. Think about edge cases that might break your solution.\n"
        f"4. Consider error handling — what happens with unexpected inputs?\n"
        f"5. Verify your logic carefully before writing the final solution.\n"
        f"6. Check for off-by-one errors, boundary conditions, and type mismatches.\n"
        f"7. Consider the test cases — does your approach handle all of them?\n"
        f"8. Think about whether your solution could cause regressions elsewhere.\n"
        f"9. Consider the performance implications of your approach.\n"
        f"10. Review your solution one final time before submitting.\n\n"
        f"Think step-by-step, then provide your solution below.\n\n"
        f"Provide your solution in the following format:\n"
        f"{fmt}"
    )


def _prompt_arc(problem: str, context: str, fmt: str) -> str:
    """Protocol §3.3 — ARC 4-Pillar condition prompt."""
    return (
        f"You are a software engineer using a structured reasoning framework. "
        f"Follow these four steps:\n\n"
        f"**Step 1 — EXPLORE:** Examine the problem space thoroughly.\n"
        f"- Read all provided code carefully\n"
        f"- Identify the key components, data flows, and dependencies\n"
        f"- Note any constraints, edge cases, or implicit requirements\n"
        f"- Map the relationships between different parts of the system\n\n"
        f"**Step 2 — MODEL:** Build a mental model of the system.\n"
        f"- What are the core abstractions and their contracts?\n"
        f"- What invariants must be maintained?\n"
        f"- What is the expected vs actual behavior?\n"
        f"- Formulate a hypothesis about the root cause or solution approach\n\n"
        f"**Step 3 — GOAL:** Define your concrete objective.\n"
        f"- State exactly what you need to achieve\n"
        f"- Identify the acceptance criteria (what does \"done\" look like?)\n"
        f"- Anticipate potential side effects or regressions\n"
        f"- Choose the simplest approach that satisfies all constraints\n\n"
        f"**Step 4 — EXECUTE:** Implement your solution methodically.\n"
        f"- Write the code changes step by step\n"
        f"- Verify each change against your model from Step 2\n"
        f"- Check that your solution meets the goal from Step 3\n"
        f"- Confirm no regressions against the constraints from Step 1\n\n"
        f"{problem}\n\n"
        f"{context}\n\n"
        f"Now apply the EXPLORE → MODEL → GOAL → EXECUTE framework:\n\n"
        f"Provide your solution in the following format:\n"
        f"{fmt}"
    )


# ===========================================================================
# GitHub / Copilot API auth (reused from V2.1 harness)
# ===========================================================================

def _get_gh_token() -> str:
    """Retrieve GitHub auth token via `gh auth token`. Cached after first call."""
    global _gh_auth_token
    if _gh_auth_token is not None:
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
    """Force-refresh the cached GitHub auth token."""
    global _gh_auth_token
    _gh_auth_token = None
    return _get_gh_token()


def warmup_api(logger: logging.Logger) -> None:
    """Send a minimal warmup request to validate the API token."""
    token = _get_gh_token()
    headers = {**COPILOT_HEADERS_STATIC, "Authorization": f"Bearer {token}"}
    body = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": "Say OK"}],
        "stream": False,
    }
    for attempt in range(1, 4):
        try:
            resp = requests.post(COPILOT_API_URL, headers=headers, json=body, timeout=30)
            if resp.status_code == 200:
                logger.info("API warmup OK (attempt %d)", attempt)
                return
            elif resp.status_code == 403:
                logger.warning("API warmup 403 — refreshing token (attempt %d)", attempt)
                token = _refresh_gh_token()
                headers["Authorization"] = f"Bearer {token}"
            else:
                logger.warning("API warmup HTTP %d (attempt %d)", resp.status_code, attempt)
            time.sleep(RETRY_BASE_DELAY * attempt)
        except Exception as exc:
            logger.warning("API warmup error (attempt %d): %s", attempt, exc)
            time.sleep(RETRY_BASE_DELAY * attempt)
    logger.warning("API warmup failed after 3 attempts — proceeding anyway")


# ===========================================================================
# API invocation with retry logic (protocol §4.4)
# ===========================================================================

def call_copilot_api(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> dict[str, Any]:
    """Call the Copilot Chat API with retry logic.

    Returns dict with keys:
        response_text, prompt_tokens, response_tokens, total_tokens,
        api_attempts, latency_ms, error
    """
    if dry_run:
        return {
            "response_text": (
                f"[DRY RUN] model={model} temp={temperature} "
                f"prompt_len={len(prompt)} max_tokens={max_tokens}\n\n"
                "SOLUTION:\n```python\n# dry run placeholder\n```"
            ),
            "prompt_tokens": len(prompt) // 4,  # rough estimate
            "response_tokens": 50,
            "total_tokens": len(prompt) // 4 + 50,
            "api_attempts": 0,
            "latency_ms": 0,
            "error": None,
        }

    token = _get_gh_token()
    headers = {**COPILOT_HEADERS_STATIC, "Authorization": f"Bearer {token}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful software engineering assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    last_error = None
    for attempt in range(1, MAX_API_RETRIES + 1):
        t0 = time.monotonic()
        try:
            resp = requests.post(
                COPILOT_API_URL,
                headers=headers,
                json=payload,
                timeout=COPILOT_API_TIMEOUT,
            )

            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    last_error = "API returned no choices"
                    continue

                text = choices[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                latency = int((time.monotonic() - t0) * 1000)

                return {
                    "response_text": text,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "response_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "api_attempts": attempt,
                    "latency_ms": latency,
                    "error": None,
                }

            elif resp.status_code == 403:
                if logger:
                    logger.warning("HTTP 403 (attempt %d) — refreshing token", attempt)
                token = _refresh_gh_token()
                headers["Authorization"] = f"Bearer {token}"
                last_error = f"HTTP 403"
                time.sleep(60)

            elif resp.status_code == 429:
                delay = RETRY_BASE_DELAY * (2 ** attempt) * 15  # 30s, 60s, 120s
                if logger:
                    logger.warning("HTTP 429 (attempt %d) — waiting %.0fs", attempt, delay)
                last_error = f"HTTP 429"
                time.sleep(delay)

            elif resp.status_code >= 500:
                if logger:
                    logger.warning("HTTP %d (attempt %d) — waiting 30s", resp.status_code, attempt)
                last_error = f"HTTP {resp.status_code}"
                time.sleep(30)

            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                if logger:
                    logger.warning("Unexpected HTTP %d (attempt %d)", resp.status_code, attempt)
                time.sleep(RETRY_BASE_DELAY * attempt)

        except requests.exceptions.Timeout:
            last_error = "API timeout"
            if logger:
                logger.warning("Timeout (attempt %d)", attempt)
            time.sleep(RETRY_BASE_DELAY * attempt)

        except requests.exceptions.ConnectionError as exc:
            last_error = f"Connection error: {exc}"
            if logger:
                logger.warning("Connection error (attempt %d): %s", attempt, exc)
            time.sleep(RETRY_BASE_DELAY * attempt)

    # All retries exhausted
    return {
        "response_text": "",
        "prompt_tokens": 0,
        "response_tokens": 0,
        "total_tokens": 0,
        "api_attempts": MAX_API_RETRIES,
        "latency_ms": 0,
        "error": f"API failed after {MAX_API_RETRIES} attempts: {last_error}",
    }


# ===========================================================================
# Task loading
# ===========================================================================

REQUIRED_TASK_FIELDS = {"id", "category", "problem", "output_format", "scoring"}


def load_task(path: Path) -> dict[str, Any]:
    """Load and validate a single V4 task YAML file.
    
    Normalizes two task schemas:
      - Pilot format: output_format + scoring: {method, test_script}
      - New format: scoring_method + test_script (flat keys)
    Both are normalized to the pilot format for the harness.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML root must be a mapping")

    # Normalize flat scoring_method + test_script -> nested scoring dict
    if "scoring" not in data and "scoring_method" in data:
        method = data.pop("scoring_method")
        # Map alternate method names to harness-expected values
        if method == "test_pass":
            method = "test_suite"
        data["scoring"] = {
            "method": method,
            "test_script": data.pop("test_script", ""),
        }

    # Default output_format to code_block if missing
    if "output_format" not in data:
        data["output_format"] = "code_block"

    missing = REQUIRED_TASK_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"{path}: missing required fields: {missing}")

    return data


def load_tasks(task_dir: Path, limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Load all YAML task files from a directory."""
    tasks = []
    paths = sorted(task_dir.glob("*.yaml")) + sorted(task_dir.glob("*.yml"))

    for p in paths:
        try:
            task = load_task(p)
            tasks.append(task)
        except Exception as exc:
            print(f"WARNING: skipping {p.name}: {exc}", file=sys.stderr)

    if limit and len(tasks) > limit:
        tasks = tasks[:limit]

    return tasks


# ===========================================================================
# Run plan generation (Fisher-Yates shuffle)
# ===========================================================================

@dataclass
class PlannedRun:
    """A single planned experimental run."""
    task_id: str
    condition: str
    repetition: int
    run_id: str = ""

    def __post_init__(self):
        if not self.run_id:
            self.run_id = f"{self.task_id}_{self.condition}_rep{self.repetition}"


def generate_run_plan(
    tasks: list[dict],
    conditions: list[str],
    reps: int,
    seed: int,
) -> list[PlannedRun]:
    """Generate a fully randomized run plan.

    Uses Fisher-Yates shuffle (via random.shuffle with recorded seed)
    per protocol §4.3.
    """
    runs = []
    for task in tasks:
        task_id = task["id"]
        for cond in conditions:
            for rep in range(1, reps + 1):
                runs.append(PlannedRun(task_id=task_id, condition=cond, repetition=rep))

    rng = random.Random(seed)
    rng.shuffle(runs)
    return runs


# ===========================================================================
# Checkpoint management
# ===========================================================================

def load_completed_run_ids(checkpoint_path: Path) -> set[str]:
    """Read the checkpoint JSONL and return all completed run_ids."""
    completed = set()
    if not checkpoint_path.exists():
        return completed
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                completed.add(record.get("run_id", ""))
            except json.JSONDecodeError:
                continue
    return completed


def append_checkpoint(checkpoint_path: Path, record: dict[str, Any]) -> None:
    """Append a single run record to the checkpoint JSONL file."""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ===========================================================================
# Logging
# ===========================================================================

def setup_logging(output_dir: Path) -> logging.Logger:
    """Configure console + file logging."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("arc_v4")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers on re-init
    if logger.handlers:
        return logger

    # File handler
    fh = logging.FileHandler(output_dir / "experiment_v4.log", encoding="utf-8")
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


# ===========================================================================
# Main execution loop
# ===========================================================================

def execute_run(
    task: dict[str, Any],
    planned: PlannedRun,
    *,
    model: str,
    temperature: float,
    seed: int,
    dry_run: bool,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Execute a single experimental run and return a checkpoint record.

    Steps:
    1. Build prompt for condition
    2. Call Copilot API
    3. Extract solution from response
    4. Score the solution
    5. Compute ARC compliance (if arc condition)
    6. Return full checkpoint record
    """
    timestamp_start = datetime.now(timezone.utc).isoformat()

    # Step 1: Build prompt
    prompt = build_prompt(task, planned.condition)
    logger.debug(
        "Prompt built: task=%s cond=%s rep=%d len=%d",
        planned.task_id, planned.condition, planned.repetition, len(prompt),
    )

    # Step 2: Call API
    api_result = call_copilot_api(
        prompt,
        model=model,
        temperature=temperature,
        dry_run=dry_run,
        logger=logger,
    )

    raw_response = api_result["response_text"]
    api_error = api_result["error"]

    # Step 3: Extract solution
    output_format = task.get("output_format", "code_block")
    extracted = extract_solution(raw_response, output_format) if not api_error else None

    # Step 4: Score
    if api_error:
        score_result = {
            "pass": False,
            "score_detail": {"reason": "api_failure"},
            "error": api_error,
        }
    elif extracted is None:
        score_result = {
            "pass": False,
            "score_detail": {"reason": "extraction_failure"},
            "error": "Could not extract solution from response",
        }
    else:
        score_result = score_solution(task, extracted)

    # Step 5: ARC compliance
    arc_compliance = None
    if planned.condition == "arc" and raw_response:
        arc_compliance = compute_arc_compliance(raw_response)

    timestamp_end = datetime.now(timezone.utc).isoformat()

    # Step 6: Build checkpoint record
    record = {
        "run_id": planned.run_id,
        "task_id": planned.task_id,
        "condition": planned.condition,
        "repetition": planned.repetition,
        "timestamp_start": timestamp_start,
        "timestamp_end": timestamp_end,
        "model": model,
        "temperature": temperature,
        "random_seed": seed,
        "prompt_tokens": api_result["prompt_tokens"],
        "response_tokens": api_result["response_tokens"],
        "raw_response": raw_response,
        "extracted_solution": extracted or "",
        "pass": score_result["pass"],
        "score_detail": score_result["score_detail"],
        "arc_compliance": arc_compliance,
        "scoring_method": task.get("scoring", {}).get("method", "unknown"),
        "api_attempts": api_result["api_attempts"],
        "latency_ms": api_result["latency_ms"],
        "error": score_result.get("error") or api_error,
    }

    return record


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ARC Experiment V4 Execution Harness",
    )
    parser.add_argument(
        "--task-dir", type=Path, default=Path("tasks/v4"),
        help="Directory containing V4 task YAML files",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/v4"),
        help="Output directory for checkpoint and logs",
    )
    parser.add_argument(
        "--conditions", nargs="+", default=list(VALID_CONDITIONS),
        choices=VALID_CONDITIONS,
        help="Conditions to run (default: all three)",
    )
    parser.add_argument(
        "--reps", type=int, default=DEFAULT_REPS,
        help=f"Repetitions per task×condition (default: {DEFAULT_REPS})",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for run order (default: 42)",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Model identifier (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--temperature", type=float, default=DEFAULT_TEMPERATURE,
        help=f"Sampling temperature (default: {DEFAULT_TEMPERATURE})",
    )
    parser.add_argument(
        "--pilot", action="store_true",
        help=f"Pilot mode: first {PILOT_TASK_LIMIT} tasks, {PILOT_REPS} rep each",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Dry-run mode: stub API calls, no actual requests",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from checkpoint (skip completed runs)",
    )
    parser.add_argument(
        "--task-filter", default=None,
        help="Only run tasks whose ID starts with this prefix",
    )
    args = parser.parse_args()

    # Resolve paths relative to the experiment root
    script_dir = Path(__file__).resolve().parent.parent
    task_dir = args.task_dir if args.task_dir.is_absolute() else script_dir / args.task_dir
    output_dir = args.output_dir if args.output_dir.is_absolute() else script_dir / args.output_dir
    checkpoint_path = output_dir / "checkpoint.jsonl"

    # Setup
    logger = setup_logging(output_dir)
    logger.info("=" * 60)
    logger.info("ARC Experiment V4 — Execution Harness")
    logger.info("=" * 60)

    # Pilot mode overrides
    reps = args.reps
    task_limit = None
    if args.pilot:
        reps = PILOT_REPS
        task_limit = PILOT_TASK_LIMIT
        logger.info("PILOT MODE: %d tasks, %d rep(s)", PILOT_TASK_LIMIT, PILOT_REPS)

    if args.dry_run:
        logger.info("DRY-RUN MODE: no API calls will be made")

    # Load tasks
    logger.info("Loading tasks from %s", task_dir)
    tasks = load_tasks(task_dir, limit=task_limit)
    if not tasks:
        logger.error("No tasks found in %s", task_dir)
        sys.exit(1)

    # Apply task filter
    if args.task_filter:
        tasks = [t for t in tasks if t["id"].startswith(args.task_filter)]
        logger.info("Filtered to %d tasks matching '%s'", len(tasks), args.task_filter)

    logger.info("Loaded %d tasks", len(tasks))
    task_map = {t["id"]: t for t in tasks}

    # Generate run plan
    plan = generate_run_plan(tasks, list(args.conditions), reps, args.seed)
    logger.info(
        "Run plan: %d runs (%d tasks × %d conditions × %d reps), seed=%d",
        len(plan), len(tasks), len(args.conditions), reps, args.seed,
    )

    # Resume: load completed runs
    completed_ids = set()
    if args.resume or checkpoint_path.exists():
        completed_ids = load_completed_run_ids(checkpoint_path)
        if completed_ids:
            logger.info("Resuming: %d runs already completed", len(completed_ids))

    remaining = [r for r in plan if r.run_id not in completed_ids]
    logger.info("Remaining: %d runs to execute", len(remaining))

    if not remaining:
        logger.info("All runs already completed. Nothing to do.")
        return

    # Warmup API (skip for dry-run)
    if not args.dry_run:
        logger.info("Warming up Copilot API...")
        warmup_api(logger)

    # Execute
    passed = 0
    failed = 0
    errors = 0

    for i, run in enumerate(remaining, 1):
        task = task_map.get(run.task_id)
        if task is None:
            logger.error("Task %s not found — skipping", run.task_id)
            continue

        logger.info(
            "[%d/%d] %s | %s | rep %d",
            i, len(remaining), run.task_id, run.condition, run.repetition,
        )

        record = execute_run(
            task, run,
            model=args.model,
            temperature=args.temperature,
            seed=args.seed,
            dry_run=args.dry_run,
            logger=logger,
        )

        # Write checkpoint
        append_checkpoint(checkpoint_path, record)

        # Track stats
        if record.get("error"):
            errors += 1
            status = "ERROR"
        elif record["pass"]:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        arc_tag = ""
        if run.condition == "arc" and record.get("arc_compliance") is not None:
            arc_tag = f" arc={record['arc_compliance']}/4"

        logger.info(
            "  -> %s (tokens: %d+%d%s)",
            status,
            record["prompt_tokens"],
            record["response_tokens"],
            arc_tag,
        )

        # Brief pause between runs to be nice to the API
        if not args.dry_run and i < len(remaining):
            time.sleep(1)

    # Summary
    logger.info("=" * 60)
    logger.info("EXECUTION COMPLETE")
    logger.info(
        "  Passed: %d | Failed: %d | Errors: %d | Total: %d",
        passed, failed, errors, len(remaining),
    )
    logger.info("  Checkpoint: %s", checkpoint_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
