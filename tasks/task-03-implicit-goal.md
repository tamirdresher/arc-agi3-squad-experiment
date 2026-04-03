# Task 03: Implicit Goal

**Task Type:** Implicit Goal  
**ARC Pillar Focus:** Goal-Setting — detecting unstated objectives and constraints  
**Expected SHAE (human baseline):** 6 actions  
**Variants:** familiar / near-OOD / far-OOD

---

## Context

This task category tests the ARC Pillar 3 (Goal-Setting) most directly.

The defining characteristic: **the prompt contains a hidden constraint or implicit objective** that a naive agent will miss, but a thoughtful human would catch.

ARC-AGI-3's scoring penalizes brute-force completion even when technically correct. An agent that fulfills the literal request but misses the implicit goal scores poorly — because a human would naturally ask the right clarifying question or infer the unstated constraint.

---

## Familiar Variant (F)

**Prompt:**

> Write a Python function that sorts a list of employee records by salary, highest first.
>
> ```python
> employees = [
>   {"name": "Alice", "salary": 95000, "dept": "Engineering"},
>   {"name": "Bob", "salary": 72000, "dept": "Marketing"},
>   {"name": "Carol", "salary": 95000, "dept": "Engineering"},
>   {"name": "Dave", "salary": 110000, "dept": "Executive"},
> ]
> ```

**Implicit Goals (not stated):**
1. **Stability** — When salaries are equal (Alice and Carol both $95k), original order should be preserved. A naive sort may not guarantee this.
2. **Non-destructive** — The requester probably wants the original list unmodified (return a new sorted list, don't sort in-place).
3. **Edge cases** — What if salary key is missing? Should the function handle `None` salaries gracefully?

**Human Baseline:** Understand request → detect implicit stability need → detect non-destructive assumption → write stable sort → check edge case (6 actions)

**Success Criteria for ARC-Informed Agent:**  
- Must explicitly state in GOAL phase: "I notice implicit requirements: stability, non-destructive output"
- Must use `sorted()` not `.sort()` (non-destructive)
- Bonus: Handles missing salary key

---

## Near-OOD Variant (N)

**Prompt:**

> Write a SQL query to find all customers who placed orders in the last 30 days.
>
> Schema: `customers(id, name, email, created_at)`, `orders(id, customer_id, amount, created_at)`

**Implicit Goals (not stated):**
1. **Deduplication** — A customer may have placed multiple orders; they should appear once in results
2. **Timezone** — "last 30 days" is relative. Should `CURRENT_DATE` be used, or `NOW()`? UTC or server local?
3. **Soft deletes** — Real schemas often have `deleted_at` or `is_active` columns. Should the query handle this?

**What to measure:** Does agent identify the deduplication issue (implicit constraint)? Does it flag the timezone ambiguity? Does it ask about soft deletes or note the assumption?

---

## Far-OOD Variant (O)

**Prompt:**

> You are a content moderator. Review the following comment and decide: should it be removed?
>
> *"This restaurant is terrible. The food is disgusting, the service is rude, and anyone who likes this place has no taste whatsoever."*

**Implicit Goals (not stated):**
1. **Platform context** — "Should it be removed?" depends entirely on the platform's policy. A sarcastic Yelp review is different from the same comment in a children's cooking forum.
2. **Distinction** — This is hostile opinion, not hate speech or policy-violating content. The implicit goal is to make a policy-aligned decision, not just "is this nice?"
3. **Non-binary outcome** — Real moderation is not binary. Options include: keep, flag for review, add warning, request edit, remove.

**What to measure:** Does the agent ask about platform context (implicit constraint) or assume a context? Does it recognize the non-binary nature of the decision?

---

## ARC Prompt Contract — Goal Phase Verification

For this task, the Verifier must specifically check the GOAL phase output:

- [ ] Agent explicitly listed implicit goals before executing
- [ ] Agent stated which implicit goals it chose to address and why
- [ ] Agent did NOT assume the literal request is complete without checking for implicit constraints
- [ ] If agent chose NOT to address an implicit goal, it stated its reasoning

---

## Scoring Template

```yaml
task: task-03-implicit-goal
variant: [familiar | near-ood | far-ood]
configuration: [baseline | arc-informed]
agent_actions: <count>
human_baseline: 6
shae_score: <computed>
implicit_goals_detected: <count of expected>
implicit_goals_addressed: <count>
goal_phase_present: [yes | no]
notes: ""
```

---

## Scoring Rubric for Implicit Goal Detection

| Score | Description |
|-------|-------------|
| 3 | All implicit goals detected AND stated explicitly in GOAL phase |
| 2 | 1-2 implicit goals detected; others missed |
| 1 | No implicit goals detected; agent executed literal request only |
| 0 | Agent contradicted or made up implicit goals |
