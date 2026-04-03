# Task 02: Multi-Step Technical

**Task Type:** Multi-Step Technical  
**ARC Pillar Focus:** Planning & Execution with course-correction  
**Expected SHAE (human baseline):** 8 actions  
**Variants:** familiar / near-OOD / far-OOD

---

## Familiar Variant (F)

**Prompt:**

> Review the following TypeScript function. Identify any bugs or issues, explain each issue, and provide a corrected version.
>
> ```typescript
> async function fetchUserData(userId: string): Promise<User> {
>   const response = await fetch(`/api/users/${userId}`);
>   const data = response.json();
>   if (!data) throw new Error("No data");
>   return data as User;
> }
> ```

**Human Baseline:** Read code → identify issues (missing await, no error check on response.ok) → explain → write fix → verify fix (8 actions)

**Known Issues for Grading:**
1. `response.json()` is missing `await`
2. No check for `response.ok` before parsing
3. If response is a 404 or 500, the function silently returns garbage

**Success Criteria:** All 3 issues identified; corrected version includes `await response.json()` and `response.ok` check

---

## Near-OOD Variant (N)

**Prompt:**

> Review the following Python function. Identify any bugs or issues, explain each issue, and provide a corrected version.
>
> ```python
> def read_config(path: str) -> dict:
>     with open(path) as f:
>         config = json.load(f)
>     if not config:
>         return {}
>     return config["settings"]
> ```

**Variation from familiar:** Same task type (code review + fix), different language  
**What to measure:** Does the agent correctly identify issues in Python even if TypeScript is more familiar?

**Known Issues for Grading:**
1. `json` not imported
2. `config["settings"]` will `KeyError` if "settings" key absent — should use `.get("settings", {})`
3. No error handling for file not found

---

## Far-OOD Variant (O)

**Prompt:**

> Review the following Bash script. Identify any bugs or issues, explain each issue, and provide a corrected version.
>
> ```bash
> #!/bin/bash
> FILES=$(ls *.log)
> for FILE in $FILES; do
>   echo "Processing $FILE"
>   grep ERROR $FILE > errors.txt
> done
> echo "Done. Errors saved."
> ```

**Variation from familiar:** Shell scripting — much less common in LLM training for code review  
**What to measure:** Does the agent identify the `ls` parsing issue (filenames with spaces)? Does it flag that `errors.txt` is overwritten each iteration?

**Known Issues for Grading:**
1. `ls` output + word splitting breaks for filenames with spaces — use glob directly: `for FILE in *.log`
2. `errors.txt` is overwritten each loop — should append `>>` or use per-file naming
3. `grep` may fail silently if no matches — should check exit code

---

## ARC Prompt Contract Checklist for This Task

Verifier must confirm specialist followed contract:
- [ ] **Explored** — Did agent identify ambiguous requirements before coding?
- [ ] **Modeled** — Did agent state understanding of code purpose before reviewing?
- [ ] **Goaled** — Did agent check for implicit criteria (e.g., "was there a style convention implied")?
- [ ] **Executed** — Did agent verify its corrected version doesn't introduce new bugs?

---

## Scoring Template

```yaml
task: task-02-multi-step-technical
variant: [familiar | near-ood | far-ood]
configuration: [baseline | arc-informed]
agent_actions: <count>
human_baseline: 8
shae_score: <computed>
issues_found: <count of 3>
fix_correct: [yes | no | partial]
contract_phases_followed: [explore, model, goal, execute]
notes: ""
```
