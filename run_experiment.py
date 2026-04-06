#!/usr/bin/env python3
"""
ARC-AGI-3 Squad Experiment — Execution Harness (V2.1 Protocol)

Automates 750 experimental runs: 50 tasks × 3 conditions × 5 runs.
All runs use Copilot CLI (cost = $0). No temperature/seed control.

Usage:
    python run_experiment.py --task-dir tasks/ --output-dir results/ --conditions all --runs 5
    python run_experiment.py --task T01 --condition arc --runs 1
    python run_experiment.py --resume
    python run_experiment.py --dry-run
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
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CONDITIONS = ("baseline", "chain-of-thought", "arc-informed")
VALID_META_CATEGORIES = ("A", "B", "C")
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # seconds; exponential backoff multiplier
SWE_BENCH_MAX_TURNS = 10

# Condition prompt templates per protocol §2.1–2.3
CONDITION_PROMPTS: dict[str, dict[str, str]] = {
    "baseline": {
        "system": "You are a helpful AI assistant. Complete the following task.",
        "user_suffix": "",
    },
    "chain-of-thought": {
        "system": "You are a helpful AI assistant. Think carefully before answering.",
        "user_suffix": (
            "\n\nLet's think step by step. Before giving your final answer, "
            "reason through the problem carefully, considering what information "
            "you have, what you might be missing, and what the expected output "
            "should look like.\n\n"
            "After drafting your answer, verify: Does your response meet all "
            "requirements stated in the task? Have you missed anything? Correct "
            "any issues before presenting your final answer."
        ),
    },
    "arc-informed": {
        "system": (
            "You are a helpful AI assistant operating under a structured "
            "reasoning contract. Before executing any task, you MUST complete "
            "all four phases below in order. Label each phase explicitly in "
            "your response."
        ),
        "user_suffix": (
            "\n\nBefore answering, follow this contract:\n\n"
            "PHASE 1 — EXPLORE: What information is missing or ambiguous? "
            "List 1-3 gaps.\n"
            "PHASE 2 — MODEL: State constraints, success criteria, and risks "
            "explicitly.\n"
            "PHASE 3 — GOAL: State the target outcome. Check for implicit "
            "objectives.\n"
            "PHASE 4 — EXECUTE: Act. After each major action, verify against "
            "the world model."
        ),
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Task:
    """A single experiment task loaded from YAML."""

    id: str
    type: str
    meta_category: str
    difficulty: str
    source: str
    source_id: Optional[str]
    prompt: str
    human_baseline_actions: int
    ground_truth: str
    implicit_goals: list[str]
    scoring_rubric: dict[str, str]
    designed_by: str
    reviewed_by: str

    @property
    def is_swe_bench(self) -> bool:
        """SWE-bench tasks need multi-turn execution (protocol §4.7)."""
        return (
            self.id.upper().startswith("C1")
            or self.source.lower() == "swe-bench-lite"
        )


@dataclass
class RunResult:
    """Result of a single experimental run."""

    run_id: str
    task_id: str
    condition: str
    run_number: int
    model: str
    timestamp: str
    response_text: str
    wall_clock_seconds: float
    actions_count: int
    tokens_used: Optional[int]
    output_hash: str
    seed: Optional[int] = None
    error: Optional[str] = None


@dataclass
class Checkpoint:
    """Tracks experiment progress for resume capability."""

    total_planned: int = 0
    completed: int = 0
    failed: int = 0
    remaining: int = 0
    completed_run_ids: list[str] = field(default_factory=list)
    failed_run_ids: list[str] = field(default_factory=list)
    last_updated: str = ""

    def mark_completed(self, run_id: str) -> None:
        """Record a successful run."""
        self.completed_run_ids.append(run_id)
        self.completed += 1
        self.remaining = self.total_planned - self.completed - self.failed
        self.last_updated = _now_iso()

    def mark_failed(self, run_id: str) -> None:
        """Record a failed run."""
        self.failed_run_ids.append(run_id)
        self.failed += 1
        self.remaining = self.total_planned - self.completed - self.failed
        self.last_updated = _now_iso()

    def is_done(self, run_id: str) -> bool:
        """Check if a run was already completed or permanently failed."""
        return run_id in self.completed_run_ids or run_id in self.failed_run_ids


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    """SHA-256 hex digest of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_run_id(task_id: str, condition: str, run_number: int) -> str:
    """Canonical run ID: {task_id}_{condition}_{run_number}."""
    return f"{task_id}_{condition}_{run_number}"


def _task_order_seed(task_id: str) -> int:
    """Deterministic seed derived from task_id for randomising task order."""
    return int(hashlib.md5(task_id.encode()).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------


def setup_logging(output_dir: Path) -> logging.Logger:
    """Configure console + file logging."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("arc_experiment")
    logger.setLevel(logging.DEBUG)

    # File handler — detailed
    fh = logging.FileHandler(output_dir / "experiment.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    logger.addHandler(fh)

    # Console handler — progress only
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Task loading & validation
# ---------------------------------------------------------------------------

REQUIRED_TASK_FIELDS = {
    "id", "type", "meta_category", "prompt",
    "human_baseline_actions", "ground_truth", "scoring_rubric",
}


def load_task(path: Path) -> Task:
    """Load and validate a single YAML task file.

    Args:
        path: Path to the YAML file.

    Returns:
        A validated Task object.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML root must be a mapping, got {type(data).__name__}")

    missing = REQUIRED_TASK_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"{path}: missing required fields: {missing}")

    meta = data.get("meta_category", "")
    if meta not in VALID_META_CATEGORIES:
        raise ValueError(
            f"{path}: meta_category '{meta}' not in {VALID_META_CATEGORIES}"
        )

    return Task(
        id=str(data["id"]),
        type=str(data.get("type", "")),
        meta_category=meta,
        difficulty=str(data.get("difficulty", "unknown")),
        source=str(data.get("source", "original")),
        source_id=data.get("source_id"),
        prompt=str(data["prompt"]).strip(),
        human_baseline_actions=int(data["human_baseline_actions"]),
        ground_truth=str(data["ground_truth"]).strip(),
        implicit_goals=data.get("implicit_goals", []) or [],
        scoring_rubric=data.get("scoring_rubric", {}),
        designed_by=str(data.get("designed_by", "unknown")),
        reviewed_by=str(data.get("reviewed_by", "unknown")),
    )


def load_tasks(task_dir: Path, task_filter: Optional[str] = None) -> list[Task]:
    """Load all YAML task files from a directory.

    Args:
        task_dir: Directory containing .yaml/.yml task files.
        task_filter: Optional task ID prefix to select a subset.

    Returns:
        List of validated Task objects.
    """
    tasks: list[Task] = []
    patterns = ["*.yaml", "*.yml"]
    paths: list[Path] = []
    for pat in patterns:
        paths.extend(task_dir.glob(pat))

    for p in sorted(paths):
        try:
            task = load_task(p)
            if task_filter and not task.id.startswith(task_filter):
                continue
            tasks.append(task)
        except Exception as exc:
            # Log but don't crash — load as many tasks as possible
            print(f"WARNING: skipping {p.name}: {exc}", file=sys.stderr)

    return tasks


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------


def build_prompt(task: Task, condition: str) -> tuple[str, str]:
    """Assemble system and user prompts for a given condition.

    Args:
        task: The task to be executed.
        condition: One of 'baseline', 'chain-of-thought', 'arc-informed'.

    Returns:
        (system_prompt, user_prompt) tuple.

    Raises:
        ValueError: If condition is not recognized.
    """
    if condition not in CONDITION_PROMPTS:
        raise ValueError(f"Unknown condition '{condition}'; must be one of {VALID_CONDITIONS}")

    template = CONDITION_PROMPTS[condition]
    system_prompt = template["system"]
    user_prompt = task.prompt + template["user_suffix"]
    return system_prompt, user_prompt


# ---------------------------------------------------------------------------
# Execution engine
# ---------------------------------------------------------------------------


def invoke_copilot_cli(
    system_prompt: str,
    user_prompt: str,
    model: str,
    *,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> tuple[str, Optional[int]]:
    """Call the Copilot CLI and capture the response.

    This is the integration point. In production, this calls `gh copilot`
    (or equivalent). During development or --dry-run, returns a stub.

    Args:
        system_prompt: The system-level instruction.
        user_prompt: The user-facing prompt.
        model: Model identifier (e.g. 'claude-sonnet-4-20250514').
        dry_run: If True, return a stub response without calling the CLI.
        logger: Optional logger for diagnostics.

    Returns:
        (response_text, token_count_or_none).
    """
    if dry_run:
        stub = (
            f"[DRY RUN] Model={model} | "
            f"System prompt length={len(system_prompt)} | "
            f"User prompt length={len(user_prompt)}"
        )
        return stub, None

    # ---- Real CLI invocation ----
    # Construct the subprocess command.
    # NOTE: Adjust this command when the real Copilot CLI is available.
    # The interface is: stdin → prompt, stdout → response.
    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
    cmd = [
        "gh", "copilot", "ask",
        "--model", model,
        combined_prompt,
    ]

    if logger:
        logger.debug("CLI command: %s", " ".join(cmd[:4]) + " ...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5-minute timeout per call
        )
        response_text = result.stdout.strip()
        if result.returncode != 0:
            err_msg = result.stderr.strip() or f"exit code {result.returncode}"
            raise RuntimeError(f"CLI error: {err_msg}")
        return response_text, None  # Token counts not available via CLI

    except subprocess.TimeoutExpired:
        raise RuntimeError("CLI call timed out after 300 seconds")


def invoke_swe_bench_multi_turn(
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_turns: int = SWE_BENCH_MAX_TURNS,
    *,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> tuple[str, int, Optional[int]]:
    """Execute a SWE-bench task using multi-turn Copilot CLI with Docker sandbox.

    Per protocol §4.7, SWE-bench tasks may need up to 10 turns of
    agent interaction within a Docker sandbox environment.

    Args:
        system_prompt: System-level instruction.
        user_prompt: Initial user prompt.
        model: Model identifier.
        max_turns: Maximum number of turns (default 10).
        dry_run: If True, stub the execution.
        logger: Optional logger.

    Returns:
        (full_response_text, actions_count, tokens_or_none).
    """
    if dry_run:
        stub = (
            f"[DRY RUN — SWE-bench multi-turn] Model={model} | "
            f"Turns=1/{max_turns} | "
            f"Prompt length={len(user_prompt)}"
        )
        return stub, 1, None

    # In production, this would:
    # 1. Spin up a Docker sandbox for the SWE-bench repo
    # 2. Feed the initial prompt to the agent
    # 3. Capture agent actions (edits, shell commands)
    # 4. Feed test results back as follow-up turns
    # 5. Repeat until the agent signals completion or max_turns reached
    #
    # Stubbed for now — the interface is clear for plug-in.
    responses: list[str] = []
    actions = 0

    for turn in range(1, max_turns + 1):
        prompt = user_prompt if turn == 1 else f"[Turn {turn}] Continue from previous state."
        response, _ = invoke_copilot_cli(
            system_prompt, prompt, model, dry_run=False, logger=logger,
        )
        responses.append(f"--- Turn {turn} ---\n{response}")
        actions += 1

        # Check for completion signals
        if any(sig in response.lower() for sig in ["task complete", "all tests pass", "done"]):
            if logger:
                logger.debug("SWE-bench task signalled completion at turn %d", turn)
            break

    return "\n\n".join(responses), actions, None


def execute_single_run(
    task: Task,
    condition: str,
    run_number: int,
    model: str,
    *,
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> RunResult:
    """Execute a single experimental run with retry logic.

    Args:
        task: The task to execute.
        condition: Experimental condition.
        run_number: Which run (1-based).
        model: Model identifier.
        dry_run: If True, stub execution.
        logger: Optional logger.

    Returns:
        RunResult with captured outputs.
    """
    run_id = _make_run_id(task.id, condition, run_number)
    system_prompt, user_prompt = build_prompt(task, condition)

    last_error: Optional[str] = None
    response_text = ""
    tokens_used: Optional[int] = None
    actions_count = 1

    start_time = time.monotonic()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if task.is_swe_bench:
                response_text, actions_count, tokens_used = invoke_swe_bench_multi_turn(
                    system_prompt, user_prompt, model,
                    dry_run=dry_run, logger=logger,
                )
            else:
                response_text, tokens_used = invoke_copilot_cli(
                    system_prompt, user_prompt, model,
                    dry_run=dry_run, logger=logger,
                )
                actions_count = 1

            last_error = None
            break  # Success

        except Exception as exc:
            last_error = f"Attempt {attempt}/{MAX_RETRIES}: {exc}"
            if logger:
                logger.warning("Run %s — %s", run_id, last_error)
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                time.sleep(delay)

    elapsed = time.monotonic() - start_time

    return RunResult(
        run_id=run_id,
        task_id=task.id,
        condition=condition,
        run_number=run_number,
        model=model,
        timestamp=_now_iso(),
        response_text=response_text,
        wall_clock_seconds=round(elapsed, 2),
        actions_count=actions_count,
        tokens_used=tokens_used,
        output_hash=_sha256(response_text),
        seed=None,  # CLI has no seed control
        error=last_error,
    )


# ---------------------------------------------------------------------------
# Output & checkpointing
# ---------------------------------------------------------------------------


def save_run_result(result: RunResult, output_dir: Path) -> Path:
    """Write a single run result as JSON.

    Directory structure: results/{task_id}/{condition}/run_{N}.json

    Args:
        result: The run result to persist.
        output_dir: Root output directory.

    Returns:
        Path to the written JSON file.
    """
    run_dir = output_dir / result.task_id / result.condition
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / f"run_{result.run_number}.json"

    payload = {
        "experiment_version": "2.0",
        "run_id": result.run_id,
        "task_id": result.task_id,
        "condition": result.condition,
        "run_number": result.run_number,
        "model": result.model,
        "seed": result.seed,
        "temperature": None,  # Not controllable via CLI
        "timestamp": result.timestamp,
        "response_text": result.response_text,
        "wall_clock_seconds": result.wall_clock_seconds,
        "actions_count": result.actions_count,
        "tokens_used": result.tokens_used,
        "output_hash": result.output_hash,
        "error": result.error,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return out_path


def save_checkpoint(checkpoint: Checkpoint, output_dir: Path) -> None:
    """Persist checkpoint state to disk.

    Args:
        checkpoint: Current checkpoint state.
        output_dir: Root output directory.
    """
    cp_path = output_dir / "checkpoint.json"
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump(asdict(checkpoint), f, indent=2)


def load_checkpoint(output_dir: Path) -> Checkpoint:
    """Load checkpoint from disk, or return a fresh one.

    Args:
        output_dir: Root output directory.

    Returns:
        Loaded or new Checkpoint.
    """
    cp_path = output_dir / "checkpoint.json"
    if not cp_path.exists():
        return Checkpoint()
    with open(cp_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Checkpoint(**data)


# ---------------------------------------------------------------------------
# Blinding
# ---------------------------------------------------------------------------


def create_blinded_copy(
    result: RunResult,
    output_dir: Path,
    blinding_key: dict[str, dict[str, str]],
) -> str:
    """Create a blinded copy of a run result (condition stripped).

    Args:
        result: The original run result.
        output_dir: Root output directory.
        blinding_key: Mutable dict that accumulates the mapping.

    Returns:
        The blinded filename.
    """
    blinded_dir = output_dir / "blinded"
    blinded_dir.mkdir(parents=True, exist_ok=True)

    suffix = uuid.uuid4().hex[:8]
    blinded_name = f"{result.task_id}_run_{result.run_number}_scorer_{suffix}.json"

    payload = {
        "experiment_version": "2.0",
        "task_id": result.task_id,
        "run_number": result.run_number,
        "model": result.model,
        "seed": result.seed,
        "timestamp": result.timestamp,
        "response_text": result.response_text,
        "wall_clock_seconds": result.wall_clock_seconds,
        "actions_count": result.actions_count,
        "tokens_used": result.tokens_used,
        "output_hash": result.output_hash,
        # NOTE: 'condition' intentionally omitted for blinding
    }

    with open(blinded_dir / blinded_name, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    blinding_key[blinded_name] = {
        "task_id": result.task_id,
        "condition": result.condition,
        "run_number": str(result.run_number),
        "run_id": result.run_id,
    }

    return blinded_name


def save_blinding_key(blinding_key: dict[str, dict[str, str]], output_dir: Path) -> None:
    """Write the blinding key (sealed until scoring complete).

    Args:
        blinding_key: Mapping of blinded filenames to true conditions.
        output_dir: Root output directory.
    """
    key_path = output_dir / "blinding_key.json"
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(blinding_key, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Error logging
# ---------------------------------------------------------------------------


def log_error(output_dir: Path, run_id: str, error: str) -> None:
    """Append an error line to the errors log.

    Args:
        output_dir: Root output directory.
        run_id: The failed run's ID.
        error: Error description.
    """
    err_path = output_dir / "errors.log"
    with open(err_path, "a", encoding="utf-8") as f:
        f.write(f"{_now_iso()} | {run_id} | {error}\n")


# ---------------------------------------------------------------------------
# Run plan & randomization
# ---------------------------------------------------------------------------


@dataclass
class PlannedRun:
    """A single planned run in the execution schedule."""

    task: Task
    condition: str
    run_number: int

    @property
    def run_id(self) -> str:
        return _make_run_id(self.task.id, self.condition, self.run_number)


def build_run_plan(
    tasks: list[Task],
    conditions: list[str],
    runs_per_condition: int,
) -> list[PlannedRun]:
    """Build the full execution plan with blocked randomization.

    Per protocol: randomize task order (seed from task_id hash),
    but within each task, run all conditions before moving to the
    next task (blocks design).

    Args:
        tasks: List of tasks.
        conditions: List of conditions to run.
        runs_per_condition: Number of runs per task×condition.

    Returns:
        Ordered list of PlannedRun objects.
    """
    # Randomize task order using deterministic seed
    sorted_tasks = sorted(tasks, key=lambda t: _task_order_seed(t.id))

    plan: list[PlannedRun] = []
    for task in sorted_tasks:
        for run_num in range(1, runs_per_condition + 1):
            for condition in conditions:
                plan.append(PlannedRun(
                    task=task,
                    condition=condition,
                    run_number=run_num,
                ))
    return plan


# ---------------------------------------------------------------------------
# Main experiment loop
# ---------------------------------------------------------------------------


def run_experiment(args: argparse.Namespace) -> None:
    """Execute the full experiment.

    Args:
        args: Parsed CLI arguments.
    """
    output_dir = Path(args.output_dir)
    task_dir = Path(args.task_dir)
    logger = setup_logging(output_dir)

    logger.info("=" * 60)
    logger.info("ARC-AGI-3 Experiment Harness — V2.1 Protocol")
    logger.info("=" * 60)

    # --- Resolve conditions ---
    if args.conditions == "all":
        conditions = list(VALID_CONDITIONS)
    else:
        conditions = [c.strip() for c in args.conditions.split(",")]
        for c in conditions:
            if c not in VALID_CONDITIONS:
                logger.error("Invalid condition '%s'. Valid: %s", c, VALID_CONDITIONS)
                sys.exit(1)

    # --- Load tasks ---
    task_filter = args.task if hasattr(args, "task") and args.task else None
    tasks = load_tasks(task_dir, task_filter=task_filter)
    if not tasks:
        logger.error("No tasks found in %s (filter=%s)", task_dir, task_filter)
        sys.exit(1)
    logger.info("Loaded %d task(s) from %s", len(tasks), task_dir)

    # --- Build run plan ---
    plan = build_run_plan(tasks, conditions, args.runs)
    logger.info(
        "Run plan: %d tasks × %d conditions × %d runs = %d total runs",
        len(tasks), len(conditions), args.runs, len(plan),
    )

    # --- Load or create checkpoint ---
    checkpoint = load_checkpoint(output_dir) if args.resume else Checkpoint()
    checkpoint.total_planned = len(plan)
    checkpoint.remaining = len(plan) - checkpoint.completed - checkpoint.failed

    if args.resume and checkpoint.completed > 0:
        logger.info(
            "Resuming: %d completed, %d failed, %d remaining",
            checkpoint.completed, checkpoint.failed, checkpoint.remaining,
        )

    # --- Dry run check ---
    if args.dry_run:
        logger.info("[DRY RUN] Validating plan without executing CLI calls")

    # --- Execute ---
    blinding_key: dict[str, dict[str, str]] = {}
    total = len(plan)

    for idx, planned in enumerate(plan, 1):
        run_id = planned.run_id

        # Skip completed runs on resume
        if checkpoint.is_done(run_id):
            continue

        progress = f"[{idx}/{total}]"
        logger.info(
            "%s Running %s | task=%s condition=%s run=%d",
            progress, run_id, planned.task.id, planned.condition, planned.run_number,
        )

        try:
            result = execute_single_run(
                task=planned.task,
                condition=planned.condition,
                run_number=planned.run_number,
                model=args.model,
                dry_run=args.dry_run,
                logger=logger,
            )

            if result.error:
                # All retries exhausted
                logger.error("%s FAILED (all retries): %s", progress, result.error)
                log_error(output_dir, run_id, result.error)
                checkpoint.mark_failed(run_id)
            else:
                # Save outputs
                out_path = save_run_result(result, output_dir)
                create_blinded_copy(result, output_dir, blinding_key)
                checkpoint.mark_completed(run_id)
                logger.info(
                    "%s OK — %.1fs, %d action(s) → %s",
                    progress, result.wall_clock_seconds, result.actions_count, out_path,
                )

        except Exception as exc:
            # Catch-all: never crash the loop on a single task failure
            logger.error("%s UNEXPECTED ERROR on %s: %s", progress, run_id, exc)
            log_error(output_dir, run_id, str(exc))
            checkpoint.mark_failed(run_id)

        # Checkpoint after every run
        save_checkpoint(checkpoint, output_dir)

    # --- Finalize ---
    save_blinding_key(blinding_key, output_dir)
    save_checkpoint(checkpoint, output_dir)

    logger.info("=" * 60)
    logger.info(
        "DONE — Completed: %d | Failed: %d | Total planned: %d",
        checkpoint.completed, checkpoint.failed, checkpoint.total_planned,
    )
    logger.info("Results: %s", output_dir)
    logger.info("Blinding key: %s", output_dir / "blinding_key.json")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = argparse.ArgumentParser(
        description="ARC-AGI-3 Experiment Execution Harness (V2.1 Protocol)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run_experiment.py --task-dir tasks/ --output-dir results/\n"
            "  python run_experiment.py --task A1-01 --condition arc-informed --runs 1\n"
            "  python run_experiment.py --resume\n"
            "  python run_experiment.py --dry-run\n"
        ),
    )
    parser.add_argument(
        "--task-dir", default="tasks/",
        help="Directory containing YAML task files (default: tasks/)",
    )
    parser.add_argument(
        "--output-dir", default="results/",
        help="Output directory for results (default: results/)",
    )
    parser.add_argument(
        "--conditions", default="all",
        help=(
            "Conditions to run: 'all' or comma-separated list of "
            "'baseline,chain-of-thought,arc-informed' (default: all)"
        ),
    )
    parser.add_argument(
        "--runs", type=int, default=5,
        help="Number of runs per task per condition (default: 5)",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--task", default=None,
        help="Filter to a single task ID prefix (e.g., 'A1-01' or 'C1')",
    )
    parser.add_argument(
        "--condition", default=None,
        help="Shorthand: run a single condition (overrides --conditions)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate everything without calling the CLI",
    )

    args = parser.parse_args(argv)

    # --condition shorthand overrides --conditions
    if args.condition:
        args.conditions = args.condition

    return args


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point."""
    args = parse_args()
    run_experiment(args)


if __name__ == "__main__":
    main()
