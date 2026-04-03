# Task 01: Simple Factual

**Task Type:** Simple Factual  
**ARC Pillar Focus:** Baseline check (Execution only — minimal exploration needed)  
**Expected SHAE (human baseline):** 3 actions  
**Variants:** familiar / near-OOD / far-OOD

---

## Familiar Variant (F)

**Prompt:**

> Summarize the following paragraph in 2-3 sentences, capturing the main idea and one supporting detail.
>
> *"The Squad framework is a multi-agent orchestration system built on GitHub Copilot. It uses named AI agents — each with a specialized charter — that coordinate through GitHub issues and structured markdown state files. The framework supports background monitoring, content generation, infrastructure management, and research synthesis across a single shared repository."*

**Human Baseline:** Read paragraph → write summary → review (3 actions)  
**Expected Agent Output:** 2-3 sentence summary  
**Success Criteria:** Summary covers main idea (multi-agent orchestration) and one supporting detail

---

## Near-OOD Variant (N)

**Prompt:**

> Summarize the following paragraph in 2-3 sentences, capturing the main idea and one supporting detail.
>
> *"ARC-AGI-3, released March 2026, is the first fully interactive benchmark in the ARC series. Unlike its predecessors, it places agents in turn-based environments where they must explore, infer goals, build world models, and plan — all without explicit instructions. Humans score 100% on the benchmark; current frontier AI scores 0.26%."*

**Variation from familiar:** Same task structure, different domain (unfamiliar benchmark)  
**What to measure:** Does the agent correctly summarize a less-familiar domain without hallucinating detail?

---

## Far-OOD Variant (O)

**Prompt:**

> Summarize the following passage in 2-3 sentences, capturing the main idea and one supporting detail.
>
> *"The Banach-Tarski paradox states that it is possible, in principle, to decompose a solid ball in 3D space into a finite number of disjoint subsets and reassemble them into two identical copies of the original ball, using only rigid motions (rotations and translations). This is a consequence of the Axiom of Choice in set theory. It applies only to abstract mathematical objects, not to physical objects."*

**Variation from familiar:** Highly unfamiliar technical domain (mathematics)  
**What to measure:** Does the agent attempt to simplify incorrectly or hallucinate explanation? Does it avoid fabricating mathematical detail it doesn't understand?

---

## Scoring Template

```yaml
task: task-01-simple-factual
variant: [familiar | near-ood | far-ood]
configuration: [baseline | arc-informed]
agent_actions: <count>
human_baseline: 3
shae_score: <computed>
correct: [yes | no | partial]
notes: ""
```
