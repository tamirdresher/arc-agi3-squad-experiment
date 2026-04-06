#!/usr/bin/env python3
"""Generate all 50 V2.1 experiment task YAML files."""
import os
import yaml

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def write_task(task):
    """Write a single task dict to a YAML file."""
    tid = task["id"]
    path = os.path.join(OUT_DIR, f"{tid}.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(task, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
    return path

def make_tasks():
    tasks = []

    # ==================================================================
    # A1: Factual Comprehension (T01-T05)
    # ==================================================================

    tasks.append({
        "id": "T01",
        "title": "Summarize distributed consensus mechanisms",
        "type": "A1",
        "meta_category": "A",
        "description": "Tests ability to extract and summarize key points from a technical passage about distributed consensus algorithms.",
        "prompt": (
            "Read the following passage and provide a summary in exactly 3 bullet points, "
            "each no longer than one sentence.\n\n"
            "Passage:\n"
            "The Raft consensus algorithm was designed as an understandable alternative to Paxos. "
            "It decomposes consensus into three sub-problems: leader election, log replication, and safety. "
            "In Raft, at most one leader exists at any time; the leader accepts client requests, replicates "
            "log entries to follower nodes, and tells followers when it is safe to apply entries to their "
            "state machines. If the leader fails, a new election begins after a randomized timeout. Raft "
            "guarantees that committed entries are durable and will eventually be applied by all nodes, "
            "provided a majority of nodes are operational. Unlike Paxos, Raft does not allow holes in the "
            "log, simplifying reasoning about consistency. The algorithm has been formally verified using "
            "TLA+ and implemented in systems like etcd and CockroachDB."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Three bullet points capturing: (1) Raft as Paxos alternative, (2) sub-problems/leader-based approach, (3) guarantees/implementations.",
            "rubric": [
                {"criterion": "Mentions Raft is an understandable alternative to Paxos", "weight": 0.3},
                {"criterion": "Covers at least 2 of the 3 sub-problems or the leader-based mechanism", "weight": 0.4},
                {"criterion": "Mentions durability guarantees or real-world implementations (etcd, CockroachDB)", "weight": 0.3},
            ],
        },
        "human_baseline_actions": 3,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "comprehension", "distributed-systems"],
    })

    tasks.append({
        "id": "T02",
        "title": "Extract HTTP/2 protocol features",
        "type": "A1",
        "meta_category": "A",
        "description": "Tests careful reading to extract specific technical facts from a passage about HTTP/2.",
        "prompt": (
            "Read the following passage and answer these three questions. Each answer must be exactly one sentence.\n\n"
            "Passage:\n"
            "HTTP/2, standardized in RFC 7540, introduced several key improvements over HTTP/1.1. It uses "
            "binary framing instead of textual protocols, which reduces parsing complexity and error rates. "
            "Multiplexing allows multiple request-response pairs to share a single TCP connection simultaneously, "
            "eliminating head-of-line blocking at the HTTP level (though TCP-level head-of-line blocking remains). "
            "Header compression via HPACK reduces overhead for repeated headers, which is especially beneficial "
            "for APIs that send similar headers across many requests. Server push allows the server to proactively "
            "send resources to the client before they are requested, although this feature has seen limited adoption "
            "and is deprecated in some implementations. HTTP/2 requires TLS in practice, even though the "
            "specification allows plaintext connections — all major browsers mandate encryption.\n\n"
            "Questions:\n"
            "1. What specific problem does multiplexing solve, and what related problem does it NOT solve?\n"
            "2. Why is HPACK particularly beneficial for APIs?\n"
            "3. What is the practical requirement that all major browsers impose on HTTP/2 that goes beyond the specification?"
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Accurate answers to all three questions based solely on the passage.",
            "rubric": [
                {"criterion": "Q1: Multiplexing eliminates HTTP-level head-of-line blocking but not TCP-level", "weight": 0.35},
                {"criterion": "Q2: HPACK helps APIs because they send similar/repeated headers across requests", "weight": 0.30},
                {"criterion": "Q3: Browsers require TLS/encryption even though the spec allows plaintext", "weight": 0.35},
            ],
        },
        "human_baseline_actions": 4,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "comprehension", "networking", "http"],
    })

    tasks.append({
        "id": "T03",
        "title": "Summarize garbage collection tradeoffs",
        "type": "A1",
        "meta_category": "A",
        "description": "Tests ability to identify tradeoffs from a nuanced technical passage.",
        "prompt": (
            "Read the following passage and list exactly 3 tradeoffs described. For each tradeoff, state "
            "the two competing concerns in the format 'X vs Y'.\n\n"
            "Passage:\n"
            "Modern garbage collectors face several fundamental tradeoffs. Throughput-oriented collectors "
            "like G1 batch work into large pauses, achieving high overall throughput but causing latency "
            "spikes that can exceed 200ms. Low-latency collectors like ZGC and Shenandoah use concurrent "
            "marking and relocation to keep pauses under 1ms, but consume 10-15% of CPU cycles for "
            "concurrent GC work, reducing application throughput. Generational collectors exploit the weak "
            "generational hypothesis — most objects die young — to focus collection on the young generation, "
            "but this requires write barriers on every reference store, adding 2-5% overhead even when no "
            "collection is occurring. Compacting collectors eliminate fragmentation and enable fast "
            "bump-pointer allocation, but compaction requires copying objects, which means updating every "
            "reference to moved objects — a cost proportional to the live set size rather than the garbage volume."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Three tradeoffs in X vs Y format from the passage.",
            "rubric": [
                {"criterion": "Identifies throughput vs latency tradeoff (G1 vs ZGC/Shenandoah)", "weight": 0.35},
                {"criterion": "Identifies generational efficiency vs write barrier overhead", "weight": 0.35},
                {"criterion": "Identifies compaction benefits (no fragmentation) vs reference-update/copying cost", "weight": 0.30},
            ],
        },
        "human_baseline_actions": 4,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "comprehension", "garbage-collection", "systems"],
    })

    tasks.append({
        "id": "T04",
        "title": "Extract CAP theorem misconceptions",
        "type": "A1",
        "meta_category": "A",
        "description": "Tests precise extraction from a passage that contains subtle distinctions about CAP theorem.",
        "prompt": (
            "Read the following passage carefully. Then answer: According to this passage, what are two "
            "common misconceptions about the CAP theorem, and what is the actual nuance the author describes?\n\n"
            "Passage:\n"
            "The CAP theorem, proved by Gilbert and Lynch in 2002, states that a distributed system cannot "
            "simultaneously provide all three of Consistency, Availability, and Partition tolerance. A common "
            "misconception is that you must permanently choose two of three ('pick 2 out of 3'). In reality, "
            "partition events are rare — most of the time, you can provide both consistency and availability. "
            "The real choice happens only during a network partition: at that point, you must choose between "
            "consistency (reject operations that could lead to divergence) and availability (accept operations, "
            "risking inconsistency that must be resolved later). A second misconception is that 'consistency' "
            "in CAP means the same as in ACID. CAP consistency refers specifically to linearizability — a "
            "strong single-object guarantee — whereas ACID consistency is about application-level invariants. "
            "Systems like DynamoDB operate in a nuanced middle ground, offering tunable consistency: eventually "
            "consistent reads by default, with optional strongly consistent reads at higher latency."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Two misconceptions and the actual nuance.",
            "rubric": [
                {"criterion": "Misconception 1: Must permanently pick 2 of 3 (actually choice only matters during partitions)", "weight": 0.35},
                {"criterion": "Misconception 2: CAP consistency = ACID consistency (CAP = linearizability, ACID = app invariants)", "weight": 0.35},
                {"criterion": "Nuance: Tunable consistency as middle ground (e.g., DynamoDB)", "weight": 0.30},
            ],
        },
        "human_baseline_actions": 5,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "comprehension", "distributed-systems", "cap-theorem"],
    })

    tasks.append({
        "id": "T05",
        "title": "Analyze WebAssembly security model passage",
        "type": "A1",
        "meta_category": "A",
        "description": "Tests extraction of security-specific details from a dense technical passage about WebAssembly.",
        "prompt": (
            "Read the following passage and answer: What are the four specific security properties of "
            "WebAssembly's sandbox model described here, and what is the one acknowledged limitation?\n\n"
            "Passage:\n"
            "WebAssembly (Wasm) executes within a sandboxed environment that provides four key security "
            "properties. First, memory isolation: each Wasm module operates within a linear memory region "
            "that it cannot escape; all memory accesses are bounds-checked, and out-of-bounds access traps "
            "rather than corrupting host memory. Second, control-flow integrity: indirect calls are validated "
            "against a type table, preventing ROP-style attacks that exploit arbitrary jumps. Third, no "
            "ambient authority: a Wasm module has zero capabilities by default — it cannot access the file "
            "system, network, or even the system clock unless the host explicitly provides these through "
            "imported functions. Fourth, deterministic execution: given the same inputs and imports, a Wasm "
            "module produces identical outputs regardless of platform, which aids security auditing. However, "
            "the sandbox does not protect against algorithmic complexity attacks — a malicious module can "
            "still consume excessive CPU time or memory within its allocation, requiring the host to impose "
            "resource limits externally through mechanisms like fuel metering or memory caps."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Four security properties and one limitation.",
            "rubric": [
                {"criterion": "Lists all 4 properties: memory isolation, control-flow integrity, no ambient authority, deterministic execution", "weight": 0.5},
                {"criterion": "Provides accurate description for each property", "weight": 0.25},
                {"criterion": "Identifies limitation: no protection against algorithmic complexity / resource exhaustion attacks", "weight": 0.25},
            ],
        },
        "human_baseline_actions": 5,
        "difficulty": "hard",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "comprehension", "webassembly", "security"],
    })

    # ==================================================================
    # A2: Multi-Step Debugging (T06-T10)
    # ==================================================================

    tasks.append({
        "id": "T06",
        "title": "Debug Python binary search off-by-one error",
        "type": "A2",
        "meta_category": "A",
        "description": "Tests ability to find and fix an off-by-one error in a Python binary search implementation.",
        "prompt": (
            "The following Python function is supposed to return the index of `target` in a sorted list, "
            "or -1 if not found. It has exactly one bug. Find it and provide the corrected function.\n\n"
            "```python\n"
            "def binary_search(arr, target):\n"
            "    left, right = 0, len(arr)\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n"
            "```\n\n"
            "Test cases that should pass:\n"
            "- binary_search([1, 3, 5, 7, 9], 5) == 2\n"
            "- binary_search([1, 3, 5, 7, 9], 1) == 0\n"
            "- binary_search([1, 3, 5, 7, 9], 9) == 4\n"
            "- binary_search([1, 3, 5, 7, 9], 4) == -1\n"
            "- binary_search([], 1) == -1"
        ),
        "expected_output": {
            "type": "code_test",
            "value": "right should be initialized to len(arr) - 1, not len(arr). The current code causes an IndexError when checking arr[mid] because mid can equal len(arr).",
            "rubric": [
                {"criterion": "Correctly identifies the bug: right = len(arr) should be right = len(arr) - 1", "weight": 0.5},
                {"criterion": "Provides corrected code that passes all test cases", "weight": 0.4},
                {"criterion": "Explains why the original code fails (IndexError on arr[mid] when mid == len(arr))", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 3,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["debugging", "python", "off-by-one", "binary-search"],
    })

    tasks.append({
        "id": "T07",
        "title": "Debug JavaScript async callback ordering",
        "type": "A2",
        "meta_category": "A",
        "description": "Tests ability to find a bug in JavaScript async code where a callback returns before async work completes.",
        "prompt": (
            "The following JavaScript function should read three files in parallel and return their combined "
            "contents as a single string. It has exactly one bug. Find it and provide the corrected function.\n\n"
            "```javascript\n"
            "const fs = require('fs').promises;\n\n"
            "async function readAllFiles(filePaths) {\n"
            "    const results = [];\n"
            "    filePaths.forEach(async (path) => {\n"
            "        const content = await fs.readFile(path, 'utf-8');\n"
            "        results.push(content);\n"
            "    });\n"
            "    return results.join('\\n');\n"
            "}\n"
            "```\n\n"
            "Expected behavior: Given ['a.txt', 'b.txt', 'c.txt'], returns the contents of all three "
            "files joined by newlines. Currently returns an empty string."
        ),
        "expected_output": {
            "type": "code_test",
            "value": "forEach does not await async callbacks. Use Promise.all with map instead.",
            "rubric": [
                {"criterion": "Identifies bug: forEach does not await async callbacks, so results is empty when join is called", "weight": 0.5},
                {"criterion": "Corrected code uses Promise.all(filePaths.map(...)) or equivalent awaitable pattern", "weight": 0.4},
                {"criterion": "Explains the timing issue clearly", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 4,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["debugging", "javascript", "async", "promises"],
    })

    tasks.append({
        "id": "T08",
        "title": "Debug Go concurrent map access race condition",
        "type": "A2",
        "meta_category": "A",
        "description": "Tests ability to identify a race condition in Go code with concurrent map writes.",
        "prompt": (
            "The following Go program counts word frequencies across multiple files concurrently. It "
            "panics intermittently with 'concurrent map writes'. Find the one bug and provide the fix.\n\n"
            "```go\n"
            "package main\n\n"
            "import (\n"
            '    "fmt"\n'
            '    "strings"\n'
            '    "sync"\n'
            ")\n\n"
            "func countWords(texts []string) map[string]int {\n"
            "    counts := make(map[string]int)\n"
            "    var wg sync.WaitGroup\n\n"
            "    for _, text := range texts {\n"
            "        wg.Add(1)\n"
            "        go func(t string) {\n"
            "            defer wg.Done()\n"
            "            for _, word := range strings.Fields(t) {\n"
            "                counts[strings.ToLower(word)]++\n"
            "            }\n"
            "        }(text)\n"
            "    }\n\n"
            "    wg.Wait()\n"
            "    return counts\n"
            "}\n\n"
            'func main() {\n'
            '    texts := []string{"Hello World", "hello Go", "world of Go"}\n'
            "    fmt.Println(countWords(texts))\n"
            "}\n"
            "```"
        ),
        "expected_output": {
            "type": "code_test",
            "value": "The map is accessed concurrently by multiple goroutines without synchronization. Fix with a sync.Mutex around map writes.",
            "rubric": [
                {"criterion": "Identifies the bug: concurrent unsynchronized map writes cause panic", "weight": 0.4},
                {"criterion": "Provides fix using sync.Mutex (or sync.RWMutex, or sync.Map) to protect map access", "weight": 0.5},
                {"criterion": "Corrected code compiles and produces correct word counts", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 4,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["debugging", "go", "concurrency", "race-condition"],
    })

    tasks.append({
        "id": "T09",
        "title": "Debug Python integer division type error",
        "type": "A2",
        "meta_category": "A",
        "description": "Tests ability to find a type-related bug in Python code computing a running average.",
        "prompt": (
            "The following Python function computes a running average of a stream of numbers. It has "
            "exactly one bug that causes incorrect results. Find and fix it.\n\n"
            "```python\n"
            "def running_average(numbers):\n"
            '    """Return a list of running averages.\n'
            "    \n"
            "    Example: [10, 20, 30] -> [10.0, 15.0, 20.0]\n"
            '    """\n'
            "    result = []\n"
            "    total = 0\n"
            "    for i, num in enumerate(numbers):\n"
            "        total += num\n"
            "        avg = total // (i + 1)\n"
            "        result.append(avg)\n"
            "    return result\n"
            "```\n\n"
            "Test cases:\n"
            "- running_average([10, 20, 30]) should return [10.0, 15.0, 20.0]\n"
            "- running_average([1, 2, 3, 4]) should return [1.0, 1.5, 2.0, 2.5]\n"
            "- running_average([7]) should return [7.0]"
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Uses // (floor division) instead of / (true division). This truncates fractional results.",
            "rubric": [
                {"criterion": "Identifies the bug: // (floor division) should be / (true division)", "weight": 0.5},
                {"criterion": "Provides corrected code with / operator that passes all test cases", "weight": 0.4},
                {"criterion": "Explains that // truncates toward negative infinity, losing decimal precision", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 2,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["debugging", "python", "type-error", "division"],
    })

    tasks.append({
        "id": "T10",
        "title": "Debug JavaScript event listener memory leak",
        "type": "A2",
        "meta_category": "A",
        "description": "Tests ability to find a logic error in JavaScript that causes a memory leak via unremoved event listeners.",
        "prompt": (
            "The following JavaScript class manages a WebSocket connection with auto-reconnect. After "
            "running for several hours, memory usage grows unboundedly. Find the one bug causing the "
            "memory leak and provide the fix.\n\n"
            "```javascript\n"
            "class WebSocketManager {\n"
            "    constructor(url) {\n"
            "        this.url = url;\n"
            "        this.messageHandlers = [];\n"
            "        this.connect();\n"
            "    }\n\n"
            "    connect() {\n"
            "        this.ws = new WebSocket(this.url);\n"
            "        this.ws.addEventListener('message', (event) => {\n"
            "            this.messageHandlers.forEach(h => h(event.data));\n"
            "        });\n"
            "        this.ws.addEventListener('close', () => {\n"
            "            console.log('Disconnected, reconnecting in 1s...');\n"
            "            setTimeout(() => this.connect(), 1000);\n"
            "        });\n"
            "    }\n\n"
            "    onMessage(handler) {\n"
            "        this.messageHandlers.push(handler);\n"
            "    }\n"
            "}\n"
            "```\n\n"
            "Usage pattern that causes the leak:\n"
            "```javascript\n"
            "const mgr = new WebSocketManager('ws://localhost:8080');\n"
            "setInterval(() => {\n"
            "    mgr.onMessage((data) => console.log(data));\n"
            "}, 5000);\n"
            "```"
        ),
        "expected_output": {
            "type": "code_test",
            "value": "The messageHandlers array grows without bound because onMessage always pushes new handlers and never removes old ones. Each setInterval call adds a duplicate handler.",
            "rubric": [
                {"criterion": "Identifies the bug: messageHandlers array grows unboundedly as duplicate handlers accumulate", "weight": 0.4},
                {"criterion": "Provides fix: add deduplication, or return an unsubscribe function, or clear handlers on reconnect", "weight": 0.5},
                {"criterion": "Notes that the usage pattern (setInterval + onMessage) is the trigger", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 5,
        "difficulty": "hard",
        "source": "original",
        "source_id": None,
        "tags": ["debugging", "javascript", "memory-leak", "event-listeners"],
    })

    # ==================================================================
    # A3: Implicit Goal Detection (T11-T15)
    # ==================================================================

    tasks.append({
        "id": "T11",
        "title": "Sort function with hidden requirements",
        "type": "A3",
        "meta_category": "A",
        "description": "Task asks for a sort function but test cases reveal it must handle None values and be stable.",
        "prompt": (
            "Write a Python function `sort_records(records)` that sorts a list of records by their "
            "'priority' field in ascending order.\n\n"
            "Each record is a dict like: {'name': 'task-A', 'priority': 3}\n\n"
            "Test cases:\n"
            "```python\n"
            "# Basic sorting\n"
            "assert sort_records([{'name': 'c', 'priority': 3}, {'name': 'a', 'priority': 1}]) == \\\n"
            "    [{'name': 'a', 'priority': 1}, {'name': 'c', 'priority': 3}]\n\n"
            "# Must handle None priority (should sort to end)\n"
            "assert sort_records([{'name': 'a', 'priority': None}, {'name': 'b', 'priority': 1}]) == \\\n"
            "    [{'name': 'b', 'priority': 1}, {'name': 'a', 'priority': None}]\n\n"
            "# Must be stable: equal priorities preserve original order\n"
            "assert sort_records([{'name': 'x', 'priority': 2}, {'name': 'y', 'priority': 2}]) == \\\n"
            "    [{'name': 'x', 'priority': 2}, {'name': 'y', 'priority': 2}]\n\n"
            "# Empty list\n"
            "assert sort_records([]) == []\n"
            "```"
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Function must: (1) sort by priority ascending, (2) handle None by sorting to end, (3) be stable for equal priorities.",
            "rubric": [
                {"criterion": "Basic sorting by priority works correctly", "weight": 0.3},
                {"criterion": "None priorities are sorted to the end (not crash or sort to front)", "weight": 0.35},
                {"criterion": "Sort is stable — equal priorities preserve insertion order", "weight": 0.25},
                {"criterion": "Handles empty list edge case", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 4,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["implicit-goal", "python", "sorting", "edge-cases"],
    })

    tasks.append({
        "id": "T12",
        "title": "Cache with implicit thread-safety requirement",
        "type": "A3",
        "meta_category": "A",
        "description": "Task asks for a cache but the usage context implies thread safety is required.",
        "prompt": (
            "Implement a Python class `LRUCache` with a maximum capacity. It should support `get(key)` "
            "and `put(key, value)` operations, both in O(1) time.\n\n"
            "```python\n"
            "cache = LRUCache(capacity=2)\n"
            "cache.put('a', 1)\n"
            "cache.put('b', 2)\n"
            "cache.get('a')      # returns 1\n"
            "cache.put('c', 3)   # evicts 'b' (least recently used)\n"
            "cache.get('b')      # returns None\n"
            "```\n\n"
            "This cache will be used in a multi-threaded web server handling 10,000 requests per second. "
            "Multiple request handler threads will read from and write to the cache concurrently.\n\n"
            "Provide the complete implementation."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "LRU cache with O(1) ops, correct eviction, and thread safety.",
            "rubric": [
                {"criterion": "Implements correct LRU eviction (O(1) get and put using OrderedDict or dict+doubly-linked-list)", "weight": 0.35},
                {"criterion": "Thread-safe: uses threading.Lock or equivalent around shared state mutations", "weight": 0.35},
                {"criterion": "get returns None for missing keys, put evicts LRU when at capacity", "weight": 0.2},
                {"criterion": "Handles edge cases: zero capacity, overwriting existing keys", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 6,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["implicit-goal", "python", "cache", "thread-safety"],
    })

    tasks.append({
        "id": "T13",
        "title": "CSV parser with implicit edge-case handling",
        "type": "A3",
        "meta_category": "A",
        "description": "Asks for a CSV parser but test data reveals it must handle quoted fields with embedded commas and newlines.",
        "prompt": (
            "Write a Python function `parse_csv(text)` that takes a CSV string and returns a list of "
            "lists (rows and columns).\n\n"
            "Test data:\n"
            '```\n'
            'name,city,note\n'
            'Alice,Portland,simple\n'
            '"Bob ""Bobby""",Denver,"has a comma, here"\n'
            '"Carol","","multi\n'
            'line note"\n'
            '```\n\n'
            "Expected output:\n"
            "```python\n"
            "[\n"
            "    ['name', 'city', 'note'],\n"
            "    ['Alice', 'Portland', 'simple'],\n"
            '    [\'Bob "Bobby"\', \'Denver\', \'has a comma, here\'],\n'
            "    ['Carol', '', 'multi\\nline note'],\n"
            "]\n"
            "```\n\n"
            "Do not use the csv module or any external libraries."
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Parser handles: basic CSV, quoted fields with commas, escaped quotes (doubled), multiline fields.",
            "rubric": [
                {"criterion": "Basic CSV parsing works (unquoted fields, simple rows)", "weight": 0.2},
                {"criterion": "Handles quoted fields containing commas", "weight": 0.25},
                {"criterion": "Handles escaped quotes (doubled quotes within quoted fields)", "weight": 0.25},
                {"criterion": "Handles multiline values within quoted fields", "weight": 0.3},
            ],
        },
        "human_baseline_actions": 7,
        "difficulty": "hard",
        "source": "original",
        "source_id": None,
        "tags": ["implicit-goal", "python", "parsing", "csv", "edge-cases"],
    })

    tasks.append({
        "id": "T14",
        "title": "Password validator with implicit security requirements",
        "type": "A3",
        "meta_category": "A",
        "description": "Asks for a password validator with explicit rules, but the context implies additional security requirements.",
        "prompt": (
            "Write a Python function `validate_password(password)` that returns True if the password meets "
            "these requirements:\n"
            "- At least 8 characters long\n"
            "- Contains at least one uppercase letter\n"
            "- Contains at least one lowercase letter\n"
            "- Contains at least one digit\n"
            "- Contains at least one special character (!@#$%^&*)\n\n"
            "This function will be used in a user registration API endpoint. Return a tuple of "
            "(bool, str) where the string explains why validation failed, or 'Valid' if it passed.\n\n"
            "Test cases:\n"
            "```python\n"
            "assert validate_password('Abcdef1!')[0] == True\n"
            "assert validate_password('short1!')[0] == False\n"
            "assert validate_password('A' * 1000000 + '1!a')[0]  # should not hang or crash\n"
            "assert validate_password('')[0] == False\n"
            "assert validate_password(None)  # should not raise an exception\n"
            "```"
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Must handle: explicit rules + None input gracefully + very long input without hanging (no ReDoS) + empty string.",
            "rubric": [
                {"criterion": "All explicit validation rules implemented correctly", "weight": 0.3},
                {"criterion": "Handles None input without raising an exception", "weight": 0.25},
                {"criterion": "Handles extremely long input efficiently (no ReDoS or O(n^2) behavior)", "weight": 0.25},
                {"criterion": "Returns informative (bool, str) tuples with clear failure messages", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 5,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["implicit-goal", "python", "validation", "security"],
    })

    tasks.append({
        "id": "T15",
        "title": "REST endpoint with implicit idempotency requirement",
        "type": "A3",
        "meta_category": "A",
        "description": "Asks for a REST endpoint; usage context implies idempotency and error handling requirements.",
        "prompt": (
            "Write a Python Flask endpoint `POST /api/orders` that creates a new order from a JSON body:\n"
            "```json\n"
            '{"customer_id": "C123", "items": [{"sku": "WIDGET-1", "qty": 2}], "request_id": "req-abc-123"}\n'
            "```\n\n"
            "The endpoint should validate the input, save the order (you can use a simple in-memory dict), "
            "and return the created order with a generated order ID.\n\n"
            "Context: This API is called by a mobile app over unreliable cellular networks. The app retries "
            "failed requests with the same request_id. The order triggers a payment charge.\n\n"
            "Provide the complete Flask route handler."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Must implement: input validation, order creation, AND idempotency via request_id to prevent duplicate charges.",
            "rubric": [
                {"criterion": "Implements idempotency: same request_id returns same order without creating duplicates", "weight": 0.35},
                {"criterion": "Validates input (customer_id, items array, required fields)", "weight": 0.25},
                {"criterion": "Returns proper HTTP status codes (201 for new, 200 for idempotent retry, 400 for invalid)", "weight": 0.2},
                {"criterion": "Generates unique order ID and stores the order", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 6,
        "difficulty": "hard",
        "source": "original",
        "source_id": None,
        "tags": ["implicit-goal", "python", "flask", "rest-api", "idempotency"],
    })

    # ==================================================================
    # A4: Multi-Constraint Optimization (T16-T20)
    # ==================================================================

    tasks.append({
        "id": "T16",
        "title": "Design an API rate limiter with competing constraints",
        "type": "A4",
        "meta_category": "A",
        "description": "Tests ability to balance fairness, performance, and memory constraints in system design.",
        "prompt": (
            "Design an API rate limiter that satisfies ALL of the following constraints:\n\n"
            "1. **Fairness**: Each user gets exactly 100 requests per minute. No user can starve another.\n"
            "2. **Performance**: Rate-limit check must complete in O(1) time per request.\n"
            "3. **Memory**: Total memory usage must not exceed 50MB for 1 million concurrent users.\n"
            "4. **Accuracy**: Must not allow more than 105 requests per minute per user (5% burst tolerance).\n\n"
            "Provide:\n"
            "a) The algorithm choice with justification (why it meets all 4 constraints)\n"
            "b) The data structure and memory calculation showing it fits in 50MB for 1M users\n"
            "c) Python pseudocode for the `is_allowed(user_id) -> bool` function\n"
            "d) What happens when constraint 3 conflicts with constraint 4 (tradeoff analysis)"
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Design addressing all 4 constraints with explicit tradeoff analysis.",
            "rubric": [
                {"criterion": "Chooses appropriate algorithm (sliding window counter, token bucket, or leaky bucket) with O(1) check", "weight": 0.3},
                {"criterion": "Memory calculation is correct and fits 50MB for 1M users (e.g., ~50 bytes per user)", "weight": 0.3},
                {"criterion": "Pseudocode is correct and implements the described algorithm", "weight": 0.2},
                {"criterion": "Explicitly addresses constraint conflicts and tradeoffs", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 8,
        "difficulty": "hard",
        "source": "original",
        "source_id": None,
        "tags": ["multi-constraint", "system-design", "rate-limiting", "optimization"],
    })

    tasks.append({
        "id": "T17",
        "title": "Design a task scheduler with latency, throughput, and fairness",
        "type": "A4",
        "meta_category": "A",
        "description": "Tests multi-constraint reasoning for a task scheduling system.",
        "prompt": (
            "Design a task scheduling system for a shared compute cluster that must satisfy:\n\n"
            "1. **Latency**: High-priority tasks must start within 100ms of submission.\n"
            "2. **Throughput**: The scheduler must handle 10,000 task submissions per second.\n"
            "3. **Fairness**: No tenant should receive less than their proportional share of resources over any 5-minute window.\n"
            "4. **Efficiency**: CPU utilization must stay above 85% when there are pending tasks.\n\n"
            "Provide:\n"
            "a) The scheduling algorithm and its priority mechanism\n"
            "b) How fairness is enforced alongside priority\n"
            "c) How the system achieves 10K tasks/sec throughput\n"
            "d) A concrete scenario where two constraints conflict and how you resolve it"
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Scheduling design addressing all 4 constraints with conflict resolution.",
            "rubric": [
                {"criterion": "Proposes a viable scheduling algorithm (multi-level feedback queue, weighted fair queueing, or similar)", "weight": 0.25},
                {"criterion": "Priority mechanism allows high-priority tasks to start within 100ms without starving low-priority", "weight": 0.25},
                {"criterion": "Describes specific mechanism for fairness enforcement (quotas, tokens, DRF)", "weight": 0.25},
                {"criterion": "Identifies and resolves a concrete conflict (e.g., priority vs fairness when high-pri tasks dominate)", "weight": 0.25},
            ],
        },
        "human_baseline_actions": 8,
        "difficulty": "hard",
        "source": "original",
        "source_id": None,
        "tags": ["multi-constraint", "system-design", "scheduling", "optimization"],
    })

    tasks.append({
        "id": "T18",
        "title": "Design a connection pool with efficiency, memory, and failover",
        "type": "A4",
        "meta_category": "A",
        "description": "Tests reasoning about database connection pool tradeoffs.",
        "prompt": (
            "Design a database connection pool for a microservice that must satisfy:\n\n"
            "1. **Efficiency**: Connection acquisition must take < 1ms for 99th percentile under normal load.\n"
            "2. **Memory**: Maximum 50 connections per service instance (database limit: 500 total across 10 instances).\n"
            "3. **Failover**: If the primary database fails, switch to a read replica within 5 seconds.\n"
            "4. **Idle cleanup**: Connections idle for > 30 seconds should be closed to free database resources.\n\n"
            "Provide:\n"
            "a) The pool sizing strategy (min, max, idle settings) with justification\n"
            "b) The connection validation approach (how do you detect stale/broken connections?)\n"
            "c) The failover mechanism (how do you switch 50 connections to a replica in < 5s?)\n"
            "d) What happens under connection exhaustion — how does constraint 1 degrade gracefully?"
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Pool design addressing all 4 constraints with graceful degradation analysis.",
            "rubric": [
                {"criterion": "Pool sizing is justified (min/max/idle with math for 50-connection limit)", "weight": 0.25},
                {"criterion": "Connection validation approach is practical (test-on-borrow, background pings, or TCP keepalive)", "weight": 0.25},
                {"criterion": "Failover mechanism is realistic (drain existing, redirect new, health checks)", "weight": 0.25},
                {"criterion": "Describes graceful degradation under exhaustion (queuing, backpressure, timeout)", "weight": 0.25},
            ],
        },
        "human_baseline_actions": 7,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["multi-constraint", "system-design", "connection-pool", "database"],
    })

    tasks.append({
        "id": "T19",
        "title": "Design a log aggregation pipeline with real-time, cost, and durability",
        "type": "A4",
        "meta_category": "A",
        "description": "Tests multi-constraint reasoning for a log aggregation system.",
        "prompt": (
            "Design a log aggregation system that must satisfy:\n\n"
            "1. **Real-time**: Logs must be searchable within 5 seconds of emission.\n"
            "2. **Cost**: Total storage cost must be < $500/month for 10TB of logs per day.\n"
            "3. **Durability**: No log line may be lost, even during component failures.\n"
            "4. **Retention**: Logs must be queryable for 30 days; after that, archived for 1 year.\n\n"
            "Provide:\n"
            "a) The architecture (which components: queue, indexer, storage tiers)\n"
            "b) How you achieve the 5-second search latency with 10TB/day volume\n"
            "c) A cost breakdown showing how $500/month is achievable\n"
            "d) How durability is guaranteed across the pipeline (no lost logs)"
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Architecture addressing all 4 constraints with cost breakdown.",
            "rubric": [
                {"criterion": "Architecture has appropriate components (ingestion queue, indexing layer, hot/cold storage tiers)", "weight": 0.25},
                {"criterion": "5-second latency is achievable with described indexing approach", "weight": 0.25},
                {"criterion": "Cost breakdown is realistic and shows path to <$500/month (tiered storage, compression)", "weight": 0.25},
                {"criterion": "Durability guarantee is credible (WAL, replication, or acknowledgment-based pipeline)", "weight": 0.25},
            ],
        },
        "human_baseline_actions": 8,
        "difficulty": "hard",
        "source": "original",
        "source_id": None,
        "tags": ["multi-constraint", "system-design", "logging", "cost-optimization"],
    })

    tasks.append({
        "id": "T20",
        "title": "Design a feature flag system with consistency, latency, and safety",
        "type": "A4",
        "meta_category": "A",
        "description": "Tests multi-constraint reasoning for a feature flag system used in production.",
        "prompt": (
            "Design a feature flag system for a global web application with these constraints:\n\n"
            "1. **Consistency**: When a flag is toggled off (kill switch), all servers must stop serving "
            "the feature within 10 seconds.\n"
            "2. **Latency**: Feature flag evaluation must add < 1ms to request processing (p99).\n"
            "3. **Safety**: A flag change must not be able to cause a full outage (blast radius control).\n"
            "4. **Auditability**: Every flag change must be traceable to a person, time, and reason.\n\n"
            "Provide:\n"
            "a) The architecture for flag storage, distribution, and evaluation\n"
            "b) How you achieve < 1ms evaluation (hint: consider local caching)\n"
            "c) The blast radius control mechanism (gradual rollout, canary, etc.)\n"
            "d) How you reconcile constraint 1 (fast propagation) with constraint 3 (blast radius control)"
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Feature flag design addressing all 4 constraints with conflict resolution.",
            "rubric": [
                {"criterion": "Architecture includes local cache for <1ms reads with push/pull sync mechanism", "weight": 0.25},
                {"criterion": "Kill switch propagation within 10s is achievable (push notification or aggressive polling)", "weight": 0.25},
                {"criterion": "Blast radius control: percentage rollouts, user segment targeting, or canary groups", "weight": 0.25},
                {"criterion": "Addresses tension between fast kill switch and gradual rollout with a clear resolution", "weight": 0.25},
            ],
        },
        "human_baseline_actions": 7,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["multi-constraint", "system-design", "feature-flags", "distributed-systems"],
    })

    # ==================================================================
    # A5: Ambiguous Specification (T21-T25)
    # ==================================================================

    tasks.append({
        "id": "T21",
        "title": "Build a notification system (underspecified)",
        "type": "A5",
        "meta_category": "A",
        "description": "Deliberately vague specification to test assumption-stating behavior.",
        "prompt": "Build a notification system for our application.",
        "expected_output": {
            "type": "rubric",
            "value": "Must state assumptions before designing. Quality of assumptions matters more than the design itself.",
            "rubric": [
                {"criterion": "Explicitly states assumptions about notification channels (email, push, SMS, in-app)", "weight": 0.3},
                {"criterion": "States assumptions about volume, frequency, and delivery guarantees", "weight": 0.25},
                {"criterion": "Asks clarifying questions OR explicitly calls out what is underspecified", "weight": 0.25},
                {"criterion": "Provides a design that is consistent with stated assumptions", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 6,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["ambiguous", "specification", "assumptions", "system-design"],
    })

    tasks.append({
        "id": "T22",
        "title": "Design a user authentication system (underspecified)",
        "type": "A5",
        "meta_category": "A",
        "description": "Vague auth spec to test whether model identifies missing requirements.",
        "prompt": "Design an authentication system for our new web app. It needs to be secure and user-friendly.",
        "expected_output": {
            "type": "rubric",
            "value": "Must identify and state assumptions about MFA, session management, OAuth, password policy, etc.",
            "rubric": [
                {"criterion": "Identifies and states assumptions about auth methods (password, OAuth, SSO, passwordless)", "weight": 0.3},
                {"criterion": "Addresses session management (tokens, cookies, expiration, refresh)", "weight": 0.25},
                {"criterion": "Considers security requirements (MFA, rate limiting, password hashing algorithm)", "weight": 0.25},
                {"criterion": "Acknowledges what is underspecified and either asks questions or documents assumptions", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 6,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["ambiguous", "specification", "authentication", "security"],
    })

    tasks.append({
        "id": "T23",
        "title": "Create a data pipeline (underspecified)",
        "type": "A5",
        "meta_category": "A",
        "description": "Extremely vague data pipeline spec to test assumption identification.",
        "prompt": "We need a data pipeline. It should take data from our sources and make it available for analytics.",
        "expected_output": {
            "type": "rubric",
            "value": "Must clarify: data sources, volume, latency requirements, schema, quality checks, destinations.",
            "rubric": [
                {"criterion": "States assumptions about data sources (databases, APIs, files, streams)", "weight": 0.25},
                {"criterion": "Addresses batch vs streaming, latency requirements, and volume estimates", "weight": 0.25},
                {"criterion": "Considers data quality, schema evolution, and error handling", "weight": 0.25},
                {"criterion": "Identifies key unknowns and either asks or documents assumptions for each", "weight": 0.25},
            ],
        },
        "human_baseline_actions": 6,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["ambiguous", "specification", "data-pipeline", "etl"],
    })

    tasks.append({
        "id": "T24",
        "title": "Implement a search feature (underspecified)",
        "type": "A5",
        "meta_category": "A",
        "description": "Vague search feature request to test requirement elicitation.",
        "prompt": (
            "Add search to our e-commerce site. Customers should be able to find products quickly."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Must clarify: search scope, ranking, filters, autocomplete, fuzzy matching, index size.",
            "rubric": [
                {"criterion": "States assumptions about what is searchable (products, categories, descriptions, reviews)", "weight": 0.25},
                {"criterion": "Addresses search quality concerns (relevance ranking, typo tolerance, synonyms)", "weight": 0.25},
                {"criterion": "Considers UX features (autocomplete, faceted filtering, pagination)", "weight": 0.25},
                {"criterion": "Identifies infrastructure unknowns (catalog size, update frequency, latency budget)", "weight": 0.25},
            ],
        },
        "human_baseline_actions": 5,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["ambiguous", "specification", "search", "e-commerce"],
    })

    tasks.append({
        "id": "T25",
        "title": "Build a monitoring dashboard (underspecified)",
        "type": "A5",
        "meta_category": "A",
        "description": "Vague monitoring request to test ability to decompose ambiguous requirements.",
        "prompt": "We need a monitoring dashboard for our microservices. It should help us detect and debug production issues.",
        "expected_output": {
            "type": "rubric",
            "value": "Must clarify: what signals (metrics/logs/traces), alerting, SLOs, drill-down, on-call integration.",
            "rubric": [
                {"criterion": "Identifies the three pillars of observability (metrics, logs, traces) and states which are in scope", "weight": 0.3},
                {"criterion": "Addresses alerting and on-call integration assumptions", "weight": 0.25},
                {"criterion": "Considers SLO/SLI definitions and what 'healthy' means for the services", "weight": 0.25},
                {"criterion": "Acknowledges unknowns about number of services, traffic volume, existing tooling", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 6,
        "difficulty": "hard",
        "source": "original",
        "source_id": None,
        "tags": ["ambiguous", "specification", "monitoring", "observability"],
    })

    # ==================================================================
    # B1: Time-Sensitive Retrieval (T26-T30)
    # ==================================================================

    tasks.append({
        "id": "T26",
        "title": "HTTP status code for Not Found",
        "type": "B1",
        "meta_category": "B",
        "description": "Trivial factual lookup — should be answered immediately without deliberation.",
        "prompt": "What HTTP status code means 'Not Found'?",
        "expected_output": {
            "type": "exact",
            "value": "404",
            "rubric": [
                {"criterion": "Answer is 404", "weight": 1.0},
            ],
        },
        "human_baseline_actions": 1,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "quick-retrieval", "http"],
    })

    tasks.append({
        "id": "T27",
        "title": "Default port for PostgreSQL",
        "type": "B1",
        "meta_category": "B",
        "description": "Trivial factual lookup about database defaults.",
        "prompt": "What is the default port number for PostgreSQL?",
        "expected_output": {
            "type": "exact",
            "value": "5432",
            "rubric": [
                {"criterion": "Answer is 5432", "weight": 1.0},
            ],
        },
        "human_baseline_actions": 1,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "quick-retrieval", "database", "postgresql"],
    })

    tasks.append({
        "id": "T28",
        "title": "Time complexity of binary search",
        "type": "B1",
        "meta_category": "B",
        "description": "Basic CS knowledge retrieval.",
        "prompt": "What is the time complexity of binary search on a sorted array of n elements?",
        "expected_output": {
            "type": "exact",
            "value": "O(log n)",
            "rubric": [
                {"criterion": "Answer is O(log n) or O(log2 n)", "weight": 1.0},
            ],
        },
        "human_baseline_actions": 1,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "quick-retrieval", "algorithms", "complexity"],
    })

    tasks.append({
        "id": "T29",
        "title": "What does ACID stand for in databases?",
        "type": "B1",
        "meta_category": "B",
        "description": "Acronym expansion — direct factual recall.",
        "prompt": "What does the acronym ACID stand for in the context of database transactions?",
        "expected_output": {
            "type": "exact",
            "value": "Atomicity, Consistency, Isolation, Durability",
            "rubric": [
                {"criterion": "All four words correct: Atomicity, Consistency, Isolation, Durability", "weight": 1.0},
            ],
        },
        "human_baseline_actions": 1,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "quick-retrieval", "database", "transactions"],
    })

    tasks.append({
        "id": "T30",
        "title": "Default port for Redis",
        "type": "B1",
        "meta_category": "B",
        "description": "Trivial port number recall.",
        "prompt": "What is the default port number for Redis?",
        "expected_output": {
            "type": "exact",
            "value": "6379",
            "rubric": [
                {"criterion": "Answer is 6379", "weight": 1.0},
            ],
        },
        "human_baseline_actions": 1,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["factual", "quick-retrieval", "redis", "database"],
    })

    # ==================================================================
    # B2: Creative/Generative (T31-T35)
    # ==================================================================

    tasks.append({
        "id": "T31",
        "title": "Write a haiku about Kubernetes",
        "type": "B2",
        "meta_category": "B",
        "description": "Creative task — structured reasoning may suppress creative fluency.",
        "prompt": "Write a haiku (5-7-5 syllable structure) about Kubernetes.",
        "expected_output": {
            "type": "rubric",
            "value": "A valid haiku about Kubernetes.",
            "rubric": [
                {"criterion": "Follows 5-7-5 syllable structure", "weight": 0.4},
                {"criterion": "Content relates to Kubernetes (containers, orchestration, pods, clusters)", "weight": 0.3},
                {"criterion": "Creative quality — evocative imagery or wit, not just technical description", "weight": 0.3},
            ],
        },
        "human_baseline_actions": 2,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["creative", "poetry", "kubernetes"],
    })

    tasks.append({
        "id": "T32",
        "title": "Suggest creative names for a developer tool",
        "type": "B2",
        "meta_category": "B",
        "description": "Open-ended naming brainstorm — structure may limit creative breadth.",
        "prompt": (
            "Suggest 5 creative and memorable names for a developer productivity tool that automates "
            "code reviews using AI. The names should be catchy, easy to remember, and hint at the "
            "tool's purpose. For each name, provide a one-sentence tagline."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Five creative names with taglines.",
            "rubric": [
                {"criterion": "Provides exactly 5 distinct names", "weight": 0.2},
                {"criterion": "Names are creative, memorable, and not generic (e.g., not 'AI Code Reviewer')", "weight": 0.3},
                {"criterion": "Names hint at the tool's purpose (code review, AI, quality)", "weight": 0.2},
                {"criterion": "Each name has a compelling one-sentence tagline", "weight": 0.3},
            ],
        },
        "human_baseline_actions": 3,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["creative", "naming", "brainstorming"],
    })

    tasks.append({
        "id": "T33",
        "title": "Write a 100-word story about a debugging session",
        "type": "B2",
        "meta_category": "B",
        "description": "Short creative fiction — tests creative fluency under a word constraint.",
        "prompt": (
            "Write a short story in exactly 100 words (+-5 words) about a programmer's most "
            "frustrating debugging session. It should have a twist ending."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "A 100-word story about debugging with a twist ending.",
            "rubric": [
                {"criterion": "Word count is between 95 and 105 words", "weight": 0.2},
                {"criterion": "Story is about a debugging session and is relatable to programmers", "weight": 0.3},
                {"criterion": "Has a clear twist ending that is surprising but logical", "weight": 0.3},
                {"criterion": "Writing quality: engaging prose, not just a technical description", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 4,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["creative", "fiction", "debugging", "storytelling"],
    })

    tasks.append({
        "id": "T34",
        "title": "Explain microservices with a non-technical analogy",
        "type": "B2",
        "meta_category": "B",
        "description": "Tests creative communication — explaining tech concepts to non-engineers.",
        "prompt": (
            "Explain the concept of microservices architecture to a 10-year-old using an analogy from "
            "everyday life. The explanation should be no longer than 4 sentences and should cover why "
            "microservices are useful (not just what they are)."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "A clear, age-appropriate analogy that covers both what and why.",
            "rubric": [
                {"criterion": "Uses a concrete, relatable analogy (not abstract technical terms)", "weight": 0.3},
                {"criterion": "Explains what microservices are (independent, small pieces working together)", "weight": 0.3},
                {"criterion": "Explains why they are useful (independence, fix one without breaking others)", "weight": 0.2},
                {"criterion": "4 sentences or fewer, accessible to a 10-year-old", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 3,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["creative", "analogy", "microservices", "communication"],
    })

    tasks.append({
        "id": "T35",
        "title": "Write a limerick about git merge conflicts",
        "type": "B2",
        "meta_category": "B",
        "description": "Constrained creative writing — limerick form with technical subject.",
        "prompt": "Write a limerick (AABBA rhyme scheme) about git merge conflicts.",
        "expected_output": {
            "type": "rubric",
            "value": "A valid limerick about git merge conflicts.",
            "rubric": [
                {"criterion": "Follows AABBA rhyme scheme with correct limerick meter", "weight": 0.4},
                {"criterion": "Content is about git merge conflicts specifically", "weight": 0.3},
                {"criterion": "Humor or wit — makes the reader smile", "weight": 0.3},
            ],
        },
        "human_baseline_actions": 3,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["creative", "poetry", "git", "humor"],
    })

    # ==================================================================
    # B3: Adversarial Misdirection (T36-T40)
    # ==================================================================

    tasks.append({
        "id": "T36",
        "title": "Answer hidden in the first sentence",
        "type": "B3",
        "meta_category": "B",
        "description": "The answer is literally in the first sentence; the rest is distraction.",
        "prompt": (
            "The function should return 42. Now, consider the following complex scenario: you are designing "
            "a distributed hash table that must support consistent hashing with virtual nodes across a "
            "cluster of 128 machines. Each machine handles approximately 50,000 requests per second, and "
            "the system must maintain sub-millisecond latency for key lookups. The replication factor is 3, "
            "and the system uses vector clocks for conflict resolution. Given that the hash ring has 2^32 "
            "positions and each physical node maps to 150 virtual nodes, calculate the expected load "
            "imbalance ratio. However, before all that — what should the function return?"
        ),
        "expected_output": {
            "type": "exact",
            "value": "42",
            "rubric": [
                {"criterion": "Answer is 42 (stated in the first sentence)", "weight": 0.8},
                {"criterion": "Does not get distracted by the complex distributed systems scenario", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 1,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["adversarial", "misdirection", "simplicity"],
    })

    tasks.append({
        "id": "T37",
        "title": "Simple math buried in overwhelming context",
        "type": "B3",
        "meta_category": "B",
        "description": "A trivial arithmetic problem surrounded by irrelevant technical complexity.",
        "prompt": (
            "A Kubernetes cluster has 3 nodes. Each node runs 4 pods. A rolling update replaces pods "
            "one at a time. The cluster uses Calico for CNI with BGP peering, and each pod gets a /32 "
            "IP from a /24 subnet allocated per node. The kube-proxy runs in IPVS mode with "
            "round-robin scheduling. Service mesh is Istio 1.20 with mTLS enabled and PERMISSIVE mode "
            "for gradual migration. The Envoy sidecar consumes approximately 50Mi of memory and 0.1 "
            "CPU cores per pod.\n\n"
            "Question: How many pods are running in total across the cluster?"
        ),
        "expected_output": {
            "type": "exact",
            "value": "12",
            "rubric": [
                {"criterion": "Answer is 12 (3 nodes x 4 pods = 12)", "weight": 0.8},
                {"criterion": "Shows simple multiplication, not distracted by CNI/mesh details", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 1,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["adversarial", "misdirection", "arithmetic", "kubernetes"],
    })

    tasks.append({
        "id": "T38",
        "title": "Code that looks buggy but is correct",
        "type": "B3",
        "meta_category": "B",
        "description": "Code uses unusual patterns that look like bugs but are intentionally correct.",
        "prompt": (
            "Review the following Python code and determine if it has any bugs. If there are bugs, "
            "describe them. If the code is correct, say so and explain why each unusual-looking part "
            "is actually valid.\n\n"
            "```python\n"
            "def flatten(lst):\n"
            "    result = []\n"
            "    for item in lst:\n"
            "        if isinstance(item, list):\n"
            "            result += flatten(item)\n"
            "        else:\n"
            "            result += [item]\n"
            "    return result\n\n"
            "# Test\n"
            "assert flatten([1, [2, [3, 4], 5], 6]) == [1, 2, 3, 4, 5, 6]\n"
            "assert flatten([]) == []\n"
            "assert flatten([1, 2, 3]) == [1, 2, 3]\n"
            "assert flatten([[[[1]]]]) == [1]\n"
            "```"
        ),
        "expected_output": {
            "type": "rubric",
            "value": "The code is correct. It recursively flattens nested lists. No bugs.",
            "rubric": [
                {"criterion": "Correctly identifies the code as bug-free", "weight": 0.6},
                {"criterion": "Does not invent non-existent bugs (false positives are penalized)", "weight": 0.3},
                {"criterion": "Explains why the recursive approach works correctly", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 3,
        "difficulty": "medium",
        "source": "original",
        "source_id": None,
        "tags": ["adversarial", "code-review", "python", "false-positive"],
    })

    tasks.append({
        "id": "T39",
        "title": "Long problem with trivial solution",
        "type": "B3",
        "meta_category": "B",
        "description": "Extremely long problem description where the solution is trivially simple.",
        "prompt": (
            "You are implementing a critical component of a real-time trading system. The system processes "
            "millions of orders per day across multiple asset classes including equities, fixed income, "
            "derivatives, and commodities. The matching engine must maintain price-time priority and "
            "support multiple order types: market, limit, stop, stop-limit, iceberg, and fill-or-kill. "
            "The system runs on a cluster of 24 bare-metal servers with FPGA-accelerated network cards "
            "for sub-microsecond latency. Each server has 512GB of RAM and dual EPYC processors.\n\n"
            "Your specific task: Write a function that takes two integers and returns their sum.\n\n"
            "The function signature is: `def add(a: int, b: int) -> int`"
        ),
        "expected_output": {
            "type": "code_test",
            "value": "def add(a: int, b: int) -> int:\n    return a + b",
            "rubric": [
                {"criterion": "Returns a + b (the correct trivial implementation)", "weight": 0.7},
                {"criterion": "Does not over-engineer (no unnecessary complexity from the trading context)", "weight": 0.3},
            ],
        },
        "human_baseline_actions": 1,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["adversarial", "misdirection", "over-engineering", "simplicity"],
    })

    tasks.append({
        "id": "T40",
        "title": "Red herring data analysis",
        "type": "B3",
        "meta_category": "B",
        "description": "Presents complex data but the question is answerable from one obvious number.",
        "prompt": (
            "Analyze the following server metrics from the past hour:\n\n"
            "| Timestamp | CPU% | Memory% | Disk I/O (MB/s) | Network (Mbps) | Active Connections | Error Rate |\n"
            "|-----------|------|---------|-----------------|----------------|-------------------|------------|\n"
            "| 14:00 | 45 | 62 | 120 | 450 | 1200 | 0.01% |\n"
            "| 14:15 | 47 | 63 | 125 | 460 | 1250 | 0.01% |\n"
            "| 14:30 | 46 | 62 | 118 | 455 | 1180 | 0.02% |\n"
            "| 14:45 | 48 | 64 | 130 | 470 | 1300 | 0.01% |\n\n"
            "Based on this data: Is the server experiencing any issues that require immediate attention?"
        ),
        "expected_output": {
            "type": "rubric",
            "value": "No. All metrics are within normal ranges. No anomalies detected.",
            "rubric": [
                {"criterion": "Correctly identifies that no immediate issues exist — all metrics are stable and within normal ranges", "weight": 0.6},
                {"criterion": "Does not fabricate problems or raise false alarms from the stable data", "weight": 0.3},
                {"criterion": "Brief, confident answer rather than lengthy over-analysis", "weight": 0.1},
            ],
        },
        "human_baseline_actions": 2,
        "difficulty": "easy",
        "source": "original",
        "source_id": None,
        "tags": ["adversarial", "data-analysis", "false-alarm", "monitoring"],
    })

    # ==================================================================
    # C1: HumanEval+ (T41-T45)
    # ==================================================================

    tasks.append({
        "id": "T41",
        "title": "HumanEval #31: is_prime",
        "type": "C1",
        "meta_category": "C",
        "description": "HumanEval+ problem #31 — determine if a number is prime.",
        "prompt": (
            "def is_prime(n):\n"
            '    """Return true if a given number is prime, and false otherwise.\n'
            "    >>> is_prime(6)\n"
            "    False\n"
            "    >>> is_prime(101)\n"
            "    True\n"
            "    >>> is_prime(11)\n"
            "    True\n"
            "    >>> is_prime(13441)\n"
            "    True\n"
            "    >>> is_prime(61)\n"
            "    True\n"
            "    >>> is_prime(4)\n"
            "    False\n"
            "    >>> is_prime(1)\n"
            "    False\n"
            '    """'
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Correct is_prime implementation that handles edge cases (0, 1, 2, negative numbers) and passes all HumanEval+ test cases.",
            "rubric": [
                {"criterion": "Correct for all basic primes and composites", "weight": 0.4},
                {"criterion": "Handles edge cases: 0, 1, 2, negative numbers", "weight": 0.3},
                {"criterion": "Efficient: O(sqrt(n)) or better", "weight": 0.3},
            ],
        },
        "human_baseline_actions": 3,
        "difficulty": "easy",
        "source": "humaneval+",
        "source_id": "HumanEval/31",
        "tags": ["benchmark", "humaneval", "python", "math", "primality"],
    })

    tasks.append({
        "id": "T42",
        "title": "HumanEval #54: same_chars",
        "type": "C1",
        "meta_category": "C",
        "description": "HumanEval+ problem #54 — check if two words have the same character set.",
        "prompt": (
            "def same_chars(s0: str, s1: str) -> bool:\n"
            '    """\n'
            "    Check if two words have the same characters.\n"
            "    >>> same_chars('eabcdzzzz', 'dddzzzzzzzddeddabc')\n"
            "    True\n"
            "    >>> same_chars('abcd', 'dddddddabc')\n"
            "    True\n"
            "    >>> same_chars('dddddddabc', 'abcd')\n"
            "    True\n"
            "    >>> same_chars('eabcd', 'dddddddabc')\n"
            "    False\n"
            "    >>> same_chars('abcd', 'dddddddabce')\n"
            "    False\n"
            "    >>> same_chars('aabb', 'aaccc')\n"
            "    False\n"
            '    """'
        ),
        "expected_output": {
            "type": "code_test",
            "value": "return set(s0) == set(s1)",
            "rubric": [
                {"criterion": "Correctly compares character sets (not multisets) of both strings", "weight": 0.6},
                {"criterion": "Passes all HumanEval+ test cases including edge cases", "weight": 0.4},
            ],
        },
        "human_baseline_actions": 2,
        "difficulty": "easy",
        "source": "humaneval+",
        "source_id": "HumanEval/54",
        "tags": ["benchmark", "humaneval", "python", "strings"],
    })

    tasks.append({
        "id": "T43",
        "title": "HumanEval #75: is_multiply_prime",
        "type": "C1",
        "meta_category": "C",
        "description": "HumanEval+ problem #75 — check if a number is a product of exactly three primes.",
        "prompt": (
            "def is_multiply_prime(a):\n"
            '    """Write a function that returns true if the given number is the multiplication of 3 prime numbers\n'
            "    and false otherwise.\n"
            "    Knowing that (a) is less than 100.\n"
            "    Example:\n"
            "    is_multiply_prime(30) == True\n"
            "    30 = 2 * 3 * 5\n"
            '    """'
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Correct implementation that checks if a is expressible as p1*p2*p3 where p1,p2,p3 are primes (not necessarily distinct).",
            "rubric": [
                {"criterion": "Correctly identifies numbers that are products of exactly 3 primes (e.g., 30=2*3*5, 8=2*2*2)", "weight": 0.5},
                {"criterion": "Returns False for numbers that are not products of exactly 3 primes (e.g., 12=2*2*3 is True, 16=2*2*2*2 is False)", "weight": 0.3},
                {"criterion": "Handles edge cases (a < 8 should be False, a = 0, a = 1)", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 4,
        "difficulty": "medium",
        "source": "humaneval+",
        "source_id": "HumanEval/75",
        "tags": ["benchmark", "humaneval", "python", "math", "factorization"],
    })

    tasks.append({
        "id": "T44",
        "title": "HumanEval #82: prime_length",
        "type": "C1",
        "meta_category": "C",
        "description": "HumanEval+ problem #82 — check if string length is prime.",
        "prompt": (
            "def prime_length(string):\n"
            '    """Write a function that takes a string and returns True if the string\n'
            "    length is a prime number or False otherwise\n"
            "    Examples\n"
            "    prime_length('Hello') == True\n"
            "    prime_length('abcdcba') == True\n"
            "    prime_length('kittens') == True\n"
            "    prime_length('orange') == False\n"
            '    """'
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Check if len(string) is prime using standard primality test.",
            "rubric": [
                {"criterion": "Correctly determines if string length is prime", "weight": 0.5},
                {"criterion": "Handles edge cases: empty string (length 0, not prime), single char (length 1, not prime)", "weight": 0.3},
                {"criterion": "Primality check is correct (not treating 0 or 1 as prime)", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 3,
        "difficulty": "easy",
        "source": "humaneval+",
        "source_id": "HumanEval/82",
        "tags": ["benchmark", "humaneval", "python", "strings", "math"],
    })

    tasks.append({
        "id": "T45",
        "title": "HumanEval #119: match_parens",
        "type": "C1",
        "meta_category": "C",
        "description": "HumanEval+ problem #119 — check if concatenating two paren strings can form a balanced sequence.",
        "prompt": (
            "def match_parens(lst):\n"
            '    """\n'
            "    You are given a list of two strings, both strings consist of open\n"
            "    parentheses '(' or close parentheses ')' only.\n"
            "    Your job is to check if it is possible to concatenate the two strings in\n"
            "    some order, that the resulting string will be good.\n"
            "    A string S is considered to be good if and only if all parentheses in S\n"
            "    are balanced. For example: the string '(())()' is good, while the string\n"
            "    '())' is not.\n"
            "    Return 'Yes' if there's a way to make a good string, and return 'No' otherwise.\n\n"
            "    Examples:\n"
            "    match_parens(['()(', ')']) == 'Yes'\n"
            "    match_parens([')', ')']) == 'No'\n"
            '    """'
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Try both concatenation orders (s0+s1 and s1+s0), check if either produces balanced parentheses.",
            "rubric": [
                {"criterion": "Tries both orderings of concatenation", "weight": 0.3},
                {"criterion": "Correctly validates balanced parentheses (counter never goes negative, ends at 0)", "weight": 0.4},
                {"criterion": "Returns 'Yes' or 'No' as strings, not booleans", "weight": 0.1},
                {"criterion": "Passes all HumanEval+ test cases", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 5,
        "difficulty": "medium",
        "source": "humaneval+",
        "source_id": "HumanEval/119",
        "tags": ["benchmark", "humaneval", "python", "parentheses", "strings"],
    })

    # ==================================================================
    # C2: SWE-bench (T46-T50)
    # ==================================================================

    tasks.append({
        "id": "T46",
        "title": "SWE-bench: django__django-11099",
        "type": "C2",
        "meta_category": "C",
        "description": "SWE-bench Lite task — fix UsernameValidator to reject trailing newline.",
        "prompt": (
            "Repository: django/django\n"
            "Commit: d4df5e1b0b1c643fe0fc614242c0d6a820545ed1\n\n"
            "Issue: UsernameValidator allows trailing newline in usernames\n\n"
            "The ASCIIUsernameValidator and UnicodeUsernameValidator use re.match() with the regex "
            "pattern r'^[\\w.@+-]+$'. However, re.match with $ allows a trailing newline character. "
            "This means a username like 'validuser\\n' passes validation, which is incorrect.\n\n"
            "The fix should ensure that the validators reject strings containing any newline characters. "
            "The regex anchor \\Z should be used instead of $ to prevent this.\n\n"
            "Test command: python -m pytest tests/auth_tests/test_validators.py -x\n\n"
            "Provide the exact file path and code change needed to fix this issue."
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Change $ to \\Z in the regex patterns in django/contrib/auth/validators.py",
            "rubric": [
                {"criterion": "Identifies the correct file: django/contrib/auth/validators.py", "weight": 0.3},
                {"criterion": "Changes $ to \\Z in both ASCIIUsernameValidator and UnicodeUsernameValidator regex patterns", "weight": 0.5},
                {"criterion": "Does not introduce any other changes or break existing functionality", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 4,
        "difficulty": "easy",
        "source": "swe-bench",
        "source_id": "django__django-11099",
        "tags": ["benchmark", "swe-bench", "django", "regex", "validation"],
    })

    tasks.append({
        "id": "T47",
        "title": "SWE-bench: django__django-11179",
        "type": "C2",
        "meta_category": "C",
        "description": "SWE-bench Lite task — fix delete() to return per-model deletion counts.",
        "prompt": (
            "Repository: django/django\n"
            "Commit: 8a844e761d9b4cf1d35e2d4e8b55da5e40e592e3\n\n"
            "Issue: QuerySet.delete() should return a dict of per-model deletion counts\n\n"
            "Currently, QuerySet.delete() on a model with cascading deletes returns a tuple where "
            "the second element is a dict like {'app.Model': count}. However, when deleting objects "
            "that have no related objects to cascade-delete, the function returns an empty dict {} "
            "instead of including the primary model's count.\n\n"
            "Expected: Model.objects.filter(...).delete() should always include the primary model "
            "in the deletion count dict, even if the count is 0 for related models.\n\n"
            "The deletion collector in django/db/models/deletion.py should be updated to ensure the "
            "primary model's count is always included in the result.\n\n"
            "Test command: python -m pytest tests/delete/tests.py -x\n\n"
            "Provide the exact file path and code change needed."
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Update django/db/models/deletion.py Collector.delete() to always include the primary model in the returned dict.",
            "rubric": [
                {"criterion": "Identifies the correct file: django/db/models/deletion.py", "weight": 0.3},
                {"criterion": "Modifies the Collector.delete() method to include the origin model in the return dict", "weight": 0.5},
                {"criterion": "Fix is minimal and does not change the method signature or break cascading deletes", "weight": 0.2},
            ],
        },
        "human_baseline_actions": 6,
        "difficulty": "medium",
        "source": "swe-bench",
        "source_id": "django__django-11179",
        "tags": ["benchmark", "swe-bench", "django", "orm", "delete"],
    })

    tasks.append({
        "id": "T48",
        "title": "SWE-bench: requests__requests-3362",
        "type": "C2",
        "meta_category": "C",
        "description": "SWE-bench Lite task — fix urllib3 exception wrapping in requests.",
        "prompt": (
            "Repository: psf/requests\n"
            "Commit: 36453b95b13079296776d11b09cab2567ea3e703\n\n"
            "Issue: urllib3 exceptions not properly wrapped\n\n"
            "When urllib3 raises a DecodeError or TimeoutError, the requests library should wrap "
            "these in requests.exceptions.ContentDecodingError and requests.exceptions.ConnectionError "
            "respectively. Currently, these exceptions propagate unwrapped, breaking the abstraction "
            "layer that requests provides over urllib3.\n\n"
            "Users should never see raw urllib3 exceptions when using the requests library.\n\n"
            "Test command: python -m pytest tests/test_requests.py -x\n\n"
            "Provide the exact file path and code change needed to fix this issue."
        ),
        "expected_output": {
            "type": "code_test",
            "value": "Add except clauses in requests/adapters.py to catch urllib3.exceptions.DecodeError and TimeoutError, re-raising as requests exceptions.",
            "rubric": [
                {"criterion": "Identifies the correct file: requests/adapters.py (in the send() method)", "weight": 0.3},
                {"criterion": "Adds exception handling for urllib3 DecodeError -> ContentDecodingError", "weight": 0.35},
                {"criterion": "Adds exception handling for urllib3 TimeoutError -> ConnectionError", "weight": 0.35},
            ],
        },
        "human_baseline_actions": 5,
        "difficulty": "medium",
        "source": "swe-bench",
        "source_id": "psf__requests-3362",
        "tags": ["benchmark", "swe-bench", "requests", "exception-handling", "python"],
    })

    tasks.append({
        "id": "T49",
        "title": "SWE-bench: sympy__sympy-13146",
        "type": "C2",
        "meta_category": "C",
        "description": "SWE-bench Lite task — fix simplification of Rational exponents.",
        "prompt": (
            "Repository: sympy/sympy\n"
            "Commit: 2381701bfce5e9b47a8bb1c10c1e56dfe0a3cad0\n\n"
            "Issue: Exponent simplification produces wrong result for Rational bases\n\n"
            "In SymPy, evaluating `(-2)**Rational(1,3)` should return the real cube root `-2**(1/3)` "
            "but instead returns a complex result. The issue is in the power evaluation logic "
            "in `sympy/core/power.py` where negative bases with rational exponents are not handled "
            "correctly for odd roots.\n\n"
            "The real cube root of -8 is -2, but SymPy returns `2*(-1)**(1/3)` which is a complex number.\n\n"
            "Expected behavior:\n"
            "  (-8)**Rational(1, 3) should simplify to -2\n"
            "  (-2)**Rational(1, 3) should simplify to -2**(1/3), not 2*(-1)**(1/3)\n\n"
            "Test command: python -m pytest sympy/core/tests/test_power.py -x\n\n"
            "Provide the diagnosis and the approach to fix this issue."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Identifies the issue in power evaluation for negative bases with odd rational exponents.",
            "rubric": [
                {"criterion": "Identifies the correct file: sympy/core/power.py (Pow.__new__ or eval method)", "weight": 0.3},
                {"criterion": "Correctly diagnoses: negative base with odd-denominator rational exponent should yield real result", "weight": 0.4},
                {"criterion": "Proposes adding a check: if base < 0 and exponent denominator is odd, extract the sign", "weight": 0.3},
            ],
        },
        "human_baseline_actions": 7,
        "difficulty": "hard",
        "source": "swe-bench",
        "source_id": "sympy__sympy-13146",
        "tags": ["benchmark", "swe-bench", "sympy", "math", "simplification"],
    })

    tasks.append({
        "id": "T50",
        "title": "SWE-bench: flask__flask-4045",
        "type": "C2",
        "meta_category": "C",
        "description": "SWE-bench Lite task — fix Blueprint.cli to properly register CLI commands.",
        "prompt": (
            "Repository: pallets/flask\n"
            "Commit: 1d55b80bf0fbb3e19232b5e5129c33fc1fcd5e2c\n\n"
            "Issue: Nested Blueprint CLI groups lose their commands\n\n"
            "When registering CLI commands on a Blueprint using `@bp.cli.command()`, the commands "
            "are not properly available when the Blueprint is registered on the app. The issue is "
            "that Blueprint.cli creates an AppGroup, but the commands registered on it are lost "
            "during the deferred registration process because the cli group is recreated.\n\n"
            "Steps to reproduce:\n"
            "```python\n"
            "from flask import Flask, Blueprint\n"
            "bp = Blueprint('test', __name__)\n\n"
            "@bp.cli.command('hello')\n"
            "def hello_cmd():\n"
            "    print('Hello from blueprint!')\n\n"
            "app = Flask(__name__)\n"
            "app.register_blueprint(bp)\n\n"
            "# Running 'flask test hello' should work but the command is not found\n"
            "```\n\n"
            "Test command: python -m pytest tests/test_cli.py -x\n\n"
            "Provide the diagnosis and approach to fix this issue."
        ),
        "expected_output": {
            "type": "rubric",
            "value": "Identifies the deferred registration issue with Blueprint CLI commands.",
            "rubric": [
                {"criterion": "Identifies the issue is in Blueprint's deferred CLI command registration", "weight": 0.3},
                {"criterion": "Correctly points to flask/blueprints.py or flask/cli.py as the relevant files", "weight": 0.3},
                {"criterion": "Proposes fix: preserve CLI commands during blueprint registration (copy commands from blueprint cli to app cli group)", "weight": 0.4},
            ],
        },
        "human_baseline_actions": 8,
        "difficulty": "hard",
        "source": "swe-bench",
        "source_id": "pallets__flask-4045",
        "tags": ["benchmark", "swe-bench", "flask", "cli", "blueprints"],
    })

    return tasks


# ---- Main ----
all_tasks = make_tasks()
for t in all_tasks:
    write_task(t)
    tid = t["id"]
    ttl = t["title"]
    print(f"  Created {tid}: {ttl}")

print(f"\nTotal tasks created: {len(all_tasks)}")
