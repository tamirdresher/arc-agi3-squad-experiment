#!/usr/bin/env python3
"""
Unit tests for the ARC-AGI-3 experiment execution harness.

Covers: task loading, prompt assembly, checkpoint resume, blinding,
run plan generation, and error handling.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

# Import the harness module (must be on sys.path or same directory)
import run_experiment as harness


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_TASK_YAML = {
    "id": "A1-01",
    "type": "factual-comprehension",
    "meta_category": "A",
    "difficulty": "familiar",
    "source": "original",
    "source_id": None,
    "prompt": "Summarize the following paragraph in 2-3 sentences.",
    "human_baseline_actions": 3,
    "expected_output": {
        "type": "rubric",
        "value": "A concise summary.",
        "rubric": [
            {"criterion": "Summary captures main idea and one detail", "weight": 0.5},
            {"criterion": "Main idea captured, detail missing", "weight": 0.3},
            {"criterion": "Main idea wrong or hallucinated", "weight": 0.2},
        ],
    },
    "designed_by": "tester",
    "reviewed_by": "reviewer",
}

SAMPLE_SWE_TASK_YAML = {
    **SAMPLE_TASK_YAML,
    "id": "C1-01",
    "type": "swe-bench-lite",
    "meta_category": "C",
    "source": "swe-bench-lite",
    "source_id": "django__django-12345",
}


def _write_task_yaml(tmpdir: str, data: dict, filename: str = "task.yaml") -> Path:
    """Helper: write a task YAML file and return its path."""
    path = Path(tmpdir) / filename
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)
    return path


# ---------------------------------------------------------------------------
# Test: Task Loading
# ---------------------------------------------------------------------------


class TestTaskLoading(unittest.TestCase):
    """Tests for load_task and load_tasks."""

    def test_load_valid_task(self) -> None:
        """A well-formed YAML file loads without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_task_yaml(tmpdir, SAMPLE_TASK_YAML)
            task = harness.load_task(Path(tmpdir) / "task.yaml")
            self.assertEqual(task.id, "A1-01")
            self.assertEqual(task.meta_category, "A")
            self.assertEqual(task.human_baseline_actions, 3)
            self.assertFalse(task.is_swe_bench)

    def test_swe_bench_detection_by_id(self) -> None:
        """Tasks with C1- prefix are detected as SWE-bench."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_task_yaml(tmpdir, SAMPLE_SWE_TASK_YAML)
            task = harness.load_task(Path(tmpdir) / "task.yaml")
            self.assertTrue(task.is_swe_bench)

    def test_swe_bench_detection_by_source(self) -> None:
        """Tasks with source='swe-bench-lite' are detected as SWE-bench."""
        data = {**SAMPLE_TASK_YAML, "id": "X-99", "source": "swe-bench-lite"}
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_task_yaml(tmpdir, data)
            task = harness.load_task(Path(tmpdir) / "task.yaml")
            self.assertTrue(task.is_swe_bench)

    def test_missing_required_field_raises(self) -> None:
        """Missing a required field raises ValueError."""
        data = {**SAMPLE_TASK_YAML}
        del data["prompt"]
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_task_yaml(tmpdir, data)
            with self.assertRaises(ValueError) as ctx:
                harness.load_task(Path(tmpdir) / "task.yaml")
            self.assertIn("prompt", str(ctx.exception))

    def test_invalid_meta_category_raises(self) -> None:
        """Invalid meta_category raises ValueError."""
        data = {**SAMPLE_TASK_YAML, "meta_category": "Z"}
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_task_yaml(tmpdir, data)
            with self.assertRaises(ValueError):
                harness.load_task(Path(tmpdir) / "task.yaml")

    def test_load_tasks_filters_by_prefix(self) -> None:
        """load_tasks with a filter returns only matching tasks."""
        task_a = {**SAMPLE_TASK_YAML, "id": "A1-01"}
        task_b = {**SAMPLE_TASK_YAML, "id": "B1-01", "meta_category": "B"}
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_task_yaml(tmpdir, task_a, "a.yaml")
            _write_task_yaml(tmpdir, task_b, "b.yaml")
            tasks = harness.load_tasks(Path(tmpdir), task_filter="A1")
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].id, "A1-01")

    def test_load_tasks_skips_bad_files(self) -> None:
        """Bad YAML files are skipped, not fatal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_task_yaml(tmpdir, SAMPLE_TASK_YAML, "good.yaml")
            # Write a broken file
            bad = Path(tmpdir) / "bad.yaml"
            bad.write_text("not: a: valid: yaml: {{{{", encoding="utf-8")
            tasks = harness.load_tasks(Path(tmpdir))
            # At least the good file should load
            self.assertGreaterEqual(len(tasks), 1)


# ---------------------------------------------------------------------------
# Test: Prompt Assembly
# ---------------------------------------------------------------------------


class TestPromptAssembly(unittest.TestCase):
    """Tests for build_prompt."""

    def _make_task(self) -> harness.Task:
        return harness.Task(
            id="A1-01", type="test", meta_category="A", difficulty="familiar",
            source="original", source_id=None,
            prompt="Do the thing.",
            human_baseline_actions=1, ground_truth="done",
            implicit_goals=[], scoring_rubric={},
            designed_by="t", reviewed_by="r",
        )

    def test_baseline_no_suffix(self) -> None:
        """Baseline condition adds no suffix to the prompt."""
        task = self._make_task()
        sys_p, user_p = harness.build_prompt(task, "baseline")
        self.assertEqual(user_p, "Do the thing.")
        self.assertIn("helpful AI assistant", sys_p)

    def test_cot_includes_step_by_step(self) -> None:
        """CoT condition includes step-by-step instruction."""
        task = self._make_task()
        _, user_p = harness.build_prompt(task, "chain-of-thought")
        self.assertIn("step by step", user_p)
        self.assertIn("verify", user_p.lower())

    def test_arc_includes_four_phases(self) -> None:
        """ARC condition includes all four phase labels."""
        task = self._make_task()
        sys_p, user_p = harness.build_prompt(task, "arc-informed")
        for phase in ["EXPLORE", "MODEL", "GOAL", "EXECUTE"]:
            self.assertIn(phase, user_p)
        self.assertIn("structured reasoning contract", sys_p)

    def test_invalid_condition_raises(self) -> None:
        """Unknown condition raises ValueError."""
        task = self._make_task()
        with self.assertRaises(ValueError):
            harness.build_prompt(task, "invalid-condition")


# ---------------------------------------------------------------------------
# Test: Checkpoint Resume
# ---------------------------------------------------------------------------


class TestCheckpoint(unittest.TestCase):
    """Tests for checkpoint save/load and resume logic."""

    def test_round_trip(self) -> None:
        """Checkpoint saves and loads correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cp = harness.Checkpoint(total_planned=100, completed=0, remaining=100)
            cp.mark_completed("run_1")
            cp.mark_completed("run_2")
            cp.mark_failed("run_3")

            harness.save_checkpoint(cp, Path(tmpdir))
            loaded = harness.load_checkpoint(Path(tmpdir))

            self.assertEqual(loaded.completed, 2)
            self.assertEqual(loaded.failed, 1)
            self.assertEqual(loaded.remaining, 97)
            self.assertIn("run_1", loaded.completed_run_ids)
            self.assertIn("run_3", loaded.failed_run_ids)

    def test_is_done(self) -> None:
        """is_done returns True for completed and failed runs."""
        cp = harness.Checkpoint()
        cp.mark_completed("a")
        cp.mark_failed("b")
        self.assertTrue(cp.is_done("a"))
        self.assertTrue(cp.is_done("b"))
        self.assertFalse(cp.is_done("c"))

    def test_fresh_checkpoint_on_no_file(self) -> None:
        """Loading from an empty directory returns a fresh checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cp = harness.load_checkpoint(Path(tmpdir))
            self.assertEqual(cp.completed, 0)
            self.assertEqual(cp.total_planned, 0)


# ---------------------------------------------------------------------------
# Test: Blinding
# ---------------------------------------------------------------------------


class TestBlinding(unittest.TestCase):
    """Tests for blinding support."""

    def test_blinded_file_omits_condition(self) -> None:
        """Blinded output files must NOT contain the condition."""
        result = harness.RunResult(
            run_id="A1-01_baseline_1",
            task_id="A1-01",
            condition="baseline",
            run_number=1,
            model="test-model",
            timestamp="2026-01-01T00:00:00Z",
            response_text="Test response",
            wall_clock_seconds=1.0,
            actions_count=1,
            tokens_used=None,
            output_hash="abc123",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            key: dict[str, dict[str, str]] = {}
            blinded_name = harness.create_blinded_copy(result, Path(tmpdir), key)

            # Read the blinded file
            blinded_path = Path(tmpdir) / "blinded" / blinded_name
            with open(blinded_path, "r") as f:
                data = json.load(f)

            # Condition MUST be absent
            self.assertNotIn("condition", data)
            # Task ID and response MUST be present
            self.assertEqual(data["task_id"], "A1-01")
            self.assertEqual(data["response_text"], "Test response")

    def test_blinding_key_maps_correctly(self) -> None:
        """Blinding key correctly maps blinded filename to condition."""
        result = harness.RunResult(
            run_id="B1-01_arc-informed_3",
            task_id="B1-01",
            condition="arc-informed",
            run_number=3,
            model="test",
            timestamp="2026-01-01T00:00:00Z",
            response_text="x",
            wall_clock_seconds=0.5,
            actions_count=1,
            tokens_used=None,
            output_hash="def456",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            key: dict[str, dict[str, str]] = {}
            blinded_name = harness.create_blinded_copy(result, Path(tmpdir), key)

            self.assertIn(blinded_name, key)
            self.assertEqual(key[blinded_name]["condition"], "arc-informed")
            self.assertEqual(key[blinded_name]["task_id"], "B1-01")


# ---------------------------------------------------------------------------
# Test: Run Plan & Randomization
# ---------------------------------------------------------------------------


class TestRunPlan(unittest.TestCase):
    """Tests for build_run_plan."""

    def _make_tasks(self, n: int = 3) -> list[harness.Task]:
        tasks = []
        for i in range(1, n + 1):
            tasks.append(harness.Task(
                id=f"A1-{i:02d}", type="test", meta_category="A",
                difficulty="familiar", source="original", source_id=None,
                prompt=f"Task {i}", human_baseline_actions=1,
                ground_truth="ok", implicit_goals=[], scoring_rubric={},
                designed_by="t", reviewed_by="r",
            ))
        return tasks

    def test_plan_total_count(self) -> None:
        """Plan produces tasks × conditions × runs entries."""
        tasks = self._make_tasks(3)
        plan = harness.build_run_plan(tasks, list(harness.VALID_CONDITIONS), 5)
        self.assertEqual(len(plan), 3 * 3 * 5)

    def test_blocks_design(self) -> None:
        """Within each task block, all conditions appear before moving on."""
        tasks = self._make_tasks(2)
        plan = harness.build_run_plan(tasks, list(harness.VALID_CONDITIONS), 2)

        # Group by task
        current_task = plan[0].task.id
        conditions_seen: set[str] = set()
        for p in plan:
            if p.task.id != current_task:
                # Moving to a new task — the previous task should have all conditions
                self.assertEqual(len(conditions_seen), 3)
                current_task = p.task.id
                conditions_seen = set()
            conditions_seen.add(p.condition)

    def test_deterministic_order(self) -> None:
        """Same tasks always produce the same order."""
        tasks = self._make_tasks(5)
        plan1 = harness.build_run_plan(tasks, ["baseline"], 1)
        plan2 = harness.build_run_plan(tasks, ["baseline"], 1)
        ids1 = [p.task.id for p in plan1]
        ids2 = [p.task.id for p in plan2]
        self.assertEqual(ids1, ids2)


# ---------------------------------------------------------------------------
# Test: Execution (dry-run)
# ---------------------------------------------------------------------------


class TestExecution(unittest.TestCase):
    """Tests for execute_single_run in dry-run mode."""

    def _make_task(self) -> harness.Task:
        return harness.Task(
            id="A1-01", type="test", meta_category="A", difficulty="familiar",
            source="original", source_id=None,
            prompt="Test prompt.",
            human_baseline_actions=1, ground_truth="ok",
            implicit_goals=[], scoring_rubric={},
            designed_by="t", reviewed_by="r",
        )

    def test_dry_run_returns_stub(self) -> None:
        """Dry-run execution returns a stub response, not an error."""
        task = self._make_task()
        result = harness.execute_single_run(
            task, "baseline", 1, "test-model", dry_run=True,
        )
        self.assertIsNone(result.error)
        self.assertIn("DRY RUN", result.response_text)
        self.assertEqual(result.run_id, "A1-01_baseline_1")

    def test_run_id_format(self) -> None:
        """Run IDs follow {task_id}_{condition}_{run_number} format."""
        task = self._make_task()
        result = harness.execute_single_run(
            task, "arc-informed", 3, "test-model", dry_run=True,
        )
        self.assertEqual(result.run_id, "A1-01_arc-informed_3")


# ---------------------------------------------------------------------------
# Test: Output
# ---------------------------------------------------------------------------


class TestOutput(unittest.TestCase):
    """Tests for save_run_result."""

    def test_output_directory_structure(self) -> None:
        """Results are saved in {task_id}/{condition}/run_{N}.json."""
        result = harness.RunResult(
            run_id="A1-01_baseline_1",
            task_id="A1-01",
            condition="baseline",
            run_number=1,
            model="m",
            timestamp="2026-01-01T00:00:00Z",
            response_text="resp",
            wall_clock_seconds=1.0,
            actions_count=1,
            tokens_used=None,
            output_hash="h",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = harness.save_run_result(result, Path(tmpdir))
            self.assertTrue(path.exists())
            self.assertEqual(path.name, "run_1.json")
            self.assertEqual(path.parent.name, "baseline")
            self.assertEqual(path.parent.parent.name, "A1-01")


# ---------------------------------------------------------------------------
# Test: Helpers
# ---------------------------------------------------------------------------


class TestHelpers(unittest.TestCase):
    """Tests for utility functions."""

    def test_sha256_deterministic(self) -> None:
        """SHA-256 of the same string is always the same."""
        h1 = harness._sha256("hello")
        h2 = harness._sha256("hello")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_make_run_id(self) -> None:
        """Run ID formatting."""
        self.assertEqual(
            harness._make_run_id("A1-01", "baseline", 2),
            "A1-01_baseline_2",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
