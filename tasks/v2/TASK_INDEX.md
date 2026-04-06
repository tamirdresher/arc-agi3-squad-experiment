# Task Index — V2.1 Experiment (50 Tasks)

> Generated for the ARC-AGI-3 Squad Experiment V2.1 Protocol.
> All 50 tasks committed before any experimental run begins (per §1.3, Rule 4).

## Summary

| Meta-Category | Count | Description |
|---------------|-------|-------------|
| **A** (Structured Reasoning Helps) | 25 | Tasks where deliberate exploration, modeling, and goal-setting plausibly improve outcomes |
| **B** (Neutral/Harmful) | 15 | Adversarial tasks where structured reasoning may add overhead or hurt |
| **C** (External Benchmarks) | 10 | Verbatim tasks from HumanEval+ and SWE-bench Lite |

## Full Task Catalog

| ID | Type | Meta | Title | Difficulty | Source |
|----|------|------|-------|------------|--------|
| T01 | A1 | A | Summarize distributed consensus mechanisms | easy | original |
| T02 | A1 | A | Extract HTTP/2 protocol features | easy | original |
| T03 | A1 | A | Summarize garbage collection tradeoffs | medium | original |
| T04 | A1 | A | Extract CAP theorem misconceptions | medium | original |
| T05 | A1 | A | Analyze WebAssembly security model passage | hard | original |
| T06 | A2 | A | Debug Python binary search off-by-one error | easy | original |
| T07 | A2 | A | Debug JavaScript async callback ordering | medium | original |
| T08 | A2 | A | Debug Go concurrent map access race condition | medium | original |
| T09 | A2 | A | Debug Python integer division type error | easy | original |
| T10 | A2 | A | Debug JavaScript event listener memory leak | hard | original |
| T11 | A3 | A | Sort function with hidden requirements | medium | original |
| T12 | A3 | A | Cache with implicit thread-safety requirement | medium | original |
| T13 | A3 | A | CSV parser with implicit edge-case handling | hard | original |
| T14 | A3 | A | Password validator with implicit security requirements | medium | original |
| T15 | A3 | A | REST endpoint with implicit idempotency requirement | hard | original |
| T16 | A4 | A | Design an API rate limiter with competing constraints | hard | original |
| T17 | A4 | A | Design a task scheduler with latency, throughput, and fairness | hard | original |
| T18 | A4 | A | Design a connection pool with efficiency, memory, and failover | medium | original |
| T19 | A4 | A | Design a log aggregation pipeline with real-time, cost, and durability | hard | original |
| T20 | A4 | A | Design a feature flag system with consistency, latency, and safety | medium | original |
| T21 | A5 | A | Build a notification system (underspecified) | medium | original |
| T22 | A5 | A | Design a user authentication system (underspecified) | medium | original |
| T23 | A5 | A | Create a data pipeline (underspecified) | medium | original |
| T24 | A5 | A | Implement a search feature (underspecified) | easy | original |
| T25 | A5 | A | Build a monitoring dashboard (underspecified) | hard | original |
| T26 | B1 | B | HTTP status code for Not Found | easy | original |
| T27 | B1 | B | Default port for PostgreSQL | easy | original |
| T28 | B1 | B | Time complexity of binary search | easy | original |
| T29 | B1 | B | What does ACID stand for in databases? | easy | original |
| T30 | B1 | B | Default port for Redis | easy | original |
| T31 | B2 | B | Write a haiku about Kubernetes | easy | original |
| T32 | B2 | B | Suggest creative names for a developer tool | easy | original |
| T33 | B2 | B | Write a 100-word story about a debugging session | medium | original |
| T34 | B2 | B | Explain microservices with a non-technical analogy | easy | original |
| T35 | B2 | B | Write a limerick about git merge conflicts | medium | original |
| T36 | B3 | B | Answer hidden in the first sentence | easy | original |
| T37 | B3 | B | Simple math buried in overwhelming context | easy | original |
| T38 | B3 | B | Code that looks buggy but is correct | medium | original |
| T39 | B3 | B | Long problem with trivial solution | easy | original |
| T40 | B3 | B | Red herring data analysis | easy | original |
| T41 | C1 | C | HumanEval #31: is_prime | easy | humaneval+ |
| T42 | C1 | C | HumanEval #54: same_chars | easy | humaneval+ |
| T43 | C1 | C | HumanEval #75: is_multiply_prime | medium | humaneval+ |
| T44 | C1 | C | HumanEval #82: prime_length | easy | humaneval+ |
| T45 | C1 | C | HumanEval #119: match_parens | medium | humaneval+ |
| T46 | C2 | C | SWE-bench: django__django-11099 | easy | swe-bench |
| T47 | C2 | C | SWE-bench: django__django-11179 | medium | swe-bench |
| T48 | C2 | C | SWE-bench: requests__requests-3362 | medium | swe-bench |
| T49 | C2 | C | SWE-bench: sympy__sympy-13146 | hard | swe-bench |
| T50 | C2 | C | SWE-bench: flask__flask-4045 | hard | swe-bench |

## Difficulty Distribution

| Difficulty | Count |
|------------|-------|
| Easy | 21 |
| Medium | 18 |
| Hard | 11 |

## Type Distribution

| Type | Name | Count |
|------|------|-------|
| A1 | Factual Comprehension | 5 |
| A2 | Multi-Step Debugging | 5 |
| A3 | Implicit Goal Detection | 5 |
| A4 | Multi-Constraint Optimization | 5 |
| A5 | Ambiguous Specification | 5 |
| B1 | Time-Sensitive Retrieval | 5 |
| B2 | Creative/Generative | 5 |
| B3 | Adversarial Misdirection | 5 |
| C1 | HumanEval+ | 5 |
| C2 | SWE-bench Lite | 5 |
