# Task Template — v2 Experiment

> Use this template for all v2 experiment tasks. Tasks must be blinding-compatible:
> the task description itself must NOT reveal which experimental condition (ARC-informed,
> chain-of-thought, or baseline) will process it. The condition is applied by the harness, not the task.

---

## Metadata

| Field | Value |
|-------|-------|
| **Task ID** | `v2-XXX` (sequential, e.g., v2-001) |
| **Category** | `simple-factual` / `multi-step-technical` / `implicit-goal` / `compositional` / `adversarial` |
| **Domain** | Brief domain label (e.g., "TypeScript async", "SQL optimization", "content moderation") |
| **Domain Familiarity** | `familiar` / `near-OOD` / `far-OOD` |
| **Difficulty Estimate** | `easy` / `medium` / `hard` |
| **Source** | Who created this task? Is it from an existing benchmark? (e.g., "Original — created by [author]", "Adapted from SWE-bench #1234", "Derived from ARC-AGI-3 task pool") |
| **Source Benchmark** | If adapted, which benchmark and ID? (Leave blank if original) |
| **Created Date** | YYYY-MM-DD |
| **Reviewed By** | Name of independent reviewer (must not be the task author) |

---

## Human Baseline

| Field | Value |
|-------|-------|
| **Human Baseline Actions** | Integer — number of actions an experienced human would take |
| **How Determined** | `expert-estimate` / `timed-observation` / `benchmark-provided` |
| **Estimator** | Name of person who determined the baseline |
| **Estimator Familiarity** | `expert` / `competent` / `novice` in this domain |
| **Notes** | Any caveats about the baseline estimate |

---

## Task Description

> Write the task exactly as it will be presented to the agent. Do NOT include any hints
> about reasoning strategies, phase structures, or experimental conditions.

### Prompt

```
[Paste the exact prompt the agent will receive here]
```

### Supporting Materials

List any files, code snippets, or context documents provided alongside the prompt:

- `file1.ts` — [brief description]
- `context.md` — [brief description]

---

## Correctness Rubric

> Define what counts as correct, partial, and incorrect. This rubric is used by the
> blind evaluator — it must be self-contained and unambiguous.

### Correct (score: "yes")

- [ ] Requirement 1: [specific, verifiable criterion]
- [ ] Requirement 2: [specific, verifiable criterion]
- [ ] Requirement 3: [specific, verifiable criterion]
- [ ] No fabricated information or hallucinated details
- [ ] All implicit requirements addressed (list them below)

### Implicit Requirements (hidden goals)

1. [Implicit requirement 1 — what a careful human would catch]
2. [Implicit requirement 2]
3. [Implicit requirement 3]

### Partial (score: "partial")

Criteria for partial credit:
- Met some but not all explicit requirements
- Missed one or more implicit requirements
- Contains minor inaccuracies that don't invalidate the core answer

### Incorrect (score: "no")

Criteria for incorrect:
- Core answer is wrong or fabricated
- Critical requirements missed entirely
- Contains hallucinated facts or invented details

---

## Blinding Notes

> This section is for experiment administrators only. It is NOT shown to evaluators.

- **Condition assignment:** Handled by the experiment harness — not embedded in the task
- **Evaluator instructions:** "Evaluate the output against the rubric. You will not know which system produced it."
- **File naming convention:** Output files are labeled by task ID and run number only (e.g., `v2-001_run-1.json`), never by condition name

---

## v2 Experiment Controls Checklist

- [ ] Task does not mention any reasoning framework, phase structure, or condition name
- [ ] Correctness rubric is specific enough for blind evaluation
- [ ] Human baseline was determined independently (not by the task author)
- [ ] Task has been reviewed by someone other than the author
- [ ] Domain familiarity level is justified (not just guessed)
- [ ] At least 2 implicit requirements identified (for implicit-goal category)
