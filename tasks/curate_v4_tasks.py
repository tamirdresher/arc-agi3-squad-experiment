#!/usr/bin/env python3
"""
ARC Experiment V4 — Pilot Task Curator

Generates 10 synthetic pilot task YAML files for harness validation.
Tasks span BUG, REF, ALG, TST, REV categories with self-contained scoring.

Usage:
    python curate_v4_tasks.py
    python curate_v4_tasks.py --output-dir tasks/v4/
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Pilot task definitions (10 tasks, 2 per category minimum)
# ---------------------------------------------------------------------------

PILOT_TASKS = [
    # ======================================================================
    # BUG-001: Off-by-one in pagination
    # ======================================================================
    {
        "id": "PILOT-BUG-001",
        "category": "BUG",
        "difficulty": "easy",
        "source": "pilot-synthetic",
        "title": "Fix off-by-one error in pagination",
        "problem": (
            "The following pagination function has a bug that causes it to report\n"
            "an incorrect total_pages count when the total number of items is exactly\n"
            "divisible by page_size. For example, 20 items with page_size=10 should\n"
            "yield 2 pages, but the function reports 3. Fix the bug.\n"
        ),
        "context_files": [
            {
                "path": "paginator.py",
                "content": (
                    "def paginate(items, page, page_size=10):\n"
                    "    total_pages = len(items) // page_size + 1  # BUG: should use ceil division\n"
                    "    if page < 1 or page > total_pages:\n"
                    "        return []\n"
                    "    start = (page - 1) * page_size\n"
                    "    end = start + page_size\n"
                    "    return items[start:end]\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "test_suite",
            "test_script": (
                "import sys, math\n"
                "exec(open('solution.py').read())\n"
                "\n"
                "# Test 1: Normal pagination\n"
                "items = list(range(25))\n"
                "assert paginate(items, 1) == list(range(10)), 'Page 1 of 25 items failed'\n"
                "assert paginate(items, 2) == list(range(10, 20)), 'Page 2 of 25 items failed'\n"
                "assert paginate(items, 3) == list(range(20, 25)), 'Page 3 of 25 items failed'\n"
                "\n"
                "# Test 2: Exact division — the bug case\n"
                "items = list(range(20))\n"
                "assert paginate(items, 1) == list(range(10)), 'Page 1 of 20 items failed'\n"
                "assert paginate(items, 2) == list(range(10, 20)), 'Page 2 of 20 items failed'\n"
                "assert paginate(items, 3) == [], 'Page 3 of 20 items should be empty'\n"
                "\n"
                "# Test 3: Single page\n"
                "items = list(range(5))\n"
                "assert paginate(items, 1) == list(range(5)), 'Single page failed'\n"
                "assert paginate(items, 2) == [], 'Out of range should be empty'\n"
                "\n"
                "# Test 4: Empty list\n"
                "assert paginate([], 1) == [], 'Empty list failed'\n"
                "\n"
                "print('ALL TESTS PASSED')\n"
            ),
        },
    },

    # ======================================================================
    # BUG-002: Dictionary merge overwrites nested keys
    # ======================================================================
    {
        "id": "PILOT-BUG-002",
        "category": "BUG",
        "difficulty": "medium",
        "source": "pilot-synthetic",
        "title": "Fix shallow merge that clobbers nested dicts",
        "problem": (
            "The deep_merge function is supposed to recursively merge two dictionaries,\n"
            "but it currently does a shallow update that overwrites nested dicts entirely\n"
            "instead of merging them. Fix the function so nested dicts are merged recursively.\n"
        ),
        "context_files": [
            {
                "path": "merge.py",
                "content": (
                    "def deep_merge(base, override):\n"
                    "    \"\"\"Recursively merge override into base. Returns new dict.\"\"\"\n"
                    "    result = base.copy()\n"
                    "    result.update(override)  # BUG: clobbers nested dicts\n"
                    "    return result\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "test_suite",
            "test_script": (
                "exec(open('solution.py').read())\n"
                "\n"
                "# Test 1: Simple merge\n"
                "a = {'x': 1, 'y': 2}\n"
                "b = {'y': 3, 'z': 4}\n"
                "r = deep_merge(a, b)\n"
                "assert r == {'x': 1, 'y': 3, 'z': 4}, f'Simple merge failed: {r}'\n"
                "\n"
                "# Test 2: Nested merge (the bug case)\n"
                "a = {'db': {'host': 'localhost', 'port': 5432}, 'debug': True}\n"
                "b = {'db': {'port': 3306}}\n"
                "r = deep_merge(a, b)\n"
                "assert r == {'db': {'host': 'localhost', 'port': 3306}, 'debug': True}, f'Nested merge failed: {r}'\n"
                "\n"
                "# Test 3: Deep nesting\n"
                "a = {'a': {'b': {'c': 1, 'd': 2}}}\n"
                "b = {'a': {'b': {'d': 3, 'e': 4}}}\n"
                "r = deep_merge(a, b)\n"
                "assert r == {'a': {'b': {'c': 1, 'd': 3, 'e': 4}}}, f'Deep nesting failed: {r}'\n"
                "\n"
                "# Test 4: Original dicts not mutated\n"
                "a = {'x': {'y': 1}}\n"
                "b = {'x': {'z': 2}}\n"
                "r = deep_merge(a, b)\n"
                "assert a == {'x': {'y': 1}}, 'Base dict was mutated'\n"
                "assert b == {'x': {'z': 2}}, 'Override dict was mutated'\n"
                "\n"
                "print('ALL TESTS PASSED')\n"
            ),
        },
    },

    # ======================================================================
    # REF-001: Extract method refactoring
    # ======================================================================
    {
        "id": "PILOT-REF-001",
        "category": "REF",
        "difficulty": "easy",
        "source": "pilot-synthetic",
        "title": "Extract validation into a separate function",
        "problem": (
            "The process_order function contains inline validation logic mixed with\n"
            "business logic. Refactor it to extract the validation into a separate\n"
            "validate_order(order) function that returns a list of error strings\n"
            "(empty list if valid). The process_order function should call\n"
            "validate_order and return errors if any, otherwise proceed.\n"
        ),
        "context_files": [
            {
                "path": "orders.py",
                "content": (
                    "def process_order(order):\n"
                    "    # Validation mixed with business logic\n"
                    "    errors = []\n"
                    "    if not order.get('customer_id'):\n"
                    "        errors.append('Missing customer_id')\n"
                    "    if not order.get('items') or len(order['items']) == 0:\n"
                    "        errors.append('Order must have at least one item')\n"
                    "    if order.get('total', 0) <= 0:\n"
                    "        errors.append('Total must be positive')\n"
                    "    if errors:\n"
                    "        return {'status': 'error', 'errors': errors}\n"
                    "    \n"
                    "    # Business logic\n"
                    "    return {\n"
                    "        'status': 'ok',\n"
                    "        'order_id': f\"ORD-{order['customer_id']}\",\n"
                    "        'total': order['total'],\n"
                    "    }\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "test_suite",
            "test_script": (
                "exec(open('solution.py').read())\n"
                "\n"
                "# Test 1: validate_order exists and works\n"
                "errors = validate_order({})\n"
                "assert isinstance(errors, list), 'validate_order must return a list'\n"
                "assert 'Missing customer_id' in errors\n"
                "\n"
                "# Test 2: Valid order passes validation\n"
                "valid = {'customer_id': 'C1', 'items': ['A'], 'total': 50}\n"
                "assert validate_order(valid) == [], f'Valid order should have no errors: {validate_order(valid)}'\n"
                "\n"
                "# Test 3: process_order still works with valid order\n"
                "result = process_order(valid)\n"
                "assert result['status'] == 'ok'\n"
                "assert result['order_id'] == 'ORD-C1'\n"
                "\n"
                "# Test 4: process_order returns errors for invalid order\n"
                "result = process_order({'total': -1})\n"
                "assert result['status'] == 'error'\n"
                "assert len(result['errors']) >= 2  # missing customer_id + missing items\n"
                "\n"
                "# Test 5: process_order uses validate_order (not duplicated logic)\n"
                "import inspect\n"
                "src = inspect.getsource(process_order)\n"
                "assert 'validate_order' in src, 'process_order should call validate_order'\n"
                "\n"
                "print('ALL TESTS PASSED')\n"
            ),
        },
    },

    # ======================================================================
    # REF-002: Replace magic numbers with named constants
    # ======================================================================
    {
        "id": "PILOT-REF-002",
        "category": "REF",
        "difficulty": "easy",
        "source": "pilot-synthetic",
        "title": "Replace magic numbers with named constants",
        "problem": (
            "The shipping cost calculator uses magic numbers throughout.\n"
            "Refactor to use named constants at module level. The function\n"
            "behavior must remain identical. Define constants for all numeric\n"
            "literals used in the function (thresholds and rates).\n"
        ),
        "context_files": [
            {
                "path": "shipping.py",
                "content": (
                    "def calculate_shipping(weight, distance, express=False):\n"
                    "    if weight <= 0 or distance <= 0:\n"
                    "        raise ValueError('Weight and distance must be positive')\n"
                    "    \n"
                    "    if weight < 5:\n"
                    "        base = 4.99\n"
                    "    elif weight < 20:\n"
                    "        base = 9.99\n"
                    "    else:\n"
                    "        base = 19.99\n"
                    "    \n"
                    "    distance_charge = distance * 0.05\n"
                    "    \n"
                    "    if express:\n"
                    "        return (base + distance_charge) * 1.5\n"
                    "    return base + distance_charge\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "test_suite",
            "test_script": (
                "exec(open('solution.py').read())\n"
                "import re\n"
                "\n"
                "# Test 1: Behavior unchanged\n"
                "assert calculate_shipping(2, 100) == 4.99 + 100 * 0.05\n"
                "assert calculate_shipping(10, 50) == 9.99 + 50 * 0.05\n"
                "assert calculate_shipping(25, 200) == 19.99 + 200 * 0.05\n"
                "assert calculate_shipping(2, 100, express=True) == (4.99 + 5.0) * 1.5\n"
                "\n"
                "# Test 2: ValueError still raised\n"
                "try:\n"
                "    calculate_shipping(-1, 10)\n"
                "    assert False, 'Should raise ValueError'\n"
                "except ValueError:\n"
                "    pass\n"
                "\n"
                "# Test 3: Named constants exist (check that module-level UPPER_CASE names exist)\n"
                "with open('solution.py') as f:\n"
                "    src = f.read()\n"
                "# Must have at least 3 module-level constants (UPPER_CASE = number)\n"
                "constants = re.findall(r'^[A-Z][A-Z_0-9]+\\s*=\\s*[\\d.]+', src, re.MULTILINE)\n"
                "assert len(constants) >= 3, f'Expected >=3 named constants, found {len(constants)}: {constants}'\n"
                "\n"
                "# Test 4: No magic numbers in the function body (except 0)\n"
                "# Find function body\n"
                "func_start = src.index('def calculate_shipping')\n"
                "func_body = src[func_start:]\n"
                "# Should not contain literal 4.99, 9.99, 19.99, 0.05, 1.5 in function body\n"
                "for magic in ['4.99', '9.99', '19.99', '0.05', '1.5']:\n"
                "    assert magic not in func_body.split(':', 1)[1] if ':' in func_body else True, \\\n"
                "        f'Magic number {magic} still in function body'\n"
                "\n"
                "print('ALL TESTS PASSED')\n"
            ),
        },
    },

    # ======================================================================
    # ALG-001: Implement binary search
    # ======================================================================
    {
        "id": "PILOT-ALG-001",
        "category": "ALG",
        "difficulty": "easy",
        "source": "pilot-synthetic",
        "title": "Implement binary search returning insertion point",
        "problem": (
            "Implement a function bisect_left(arr, target) that returns the leftmost\n"
            "index where target could be inserted in the sorted array arr to maintain\n"
            "sorted order. If target already exists, return the index of the first\n"
            "occurrence. Do NOT use the bisect module.\n"
        ),
        "context_files": [
            {
                "path": "search.py",
                "content": (
                    "def bisect_left(arr, target):\n"
                    "    \"\"\"Return leftmost insertion point for target in sorted arr.\"\"\"\n"
                    "    # TODO: implement\n"
                    "    pass\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "test_suite",
            "test_script": (
                "exec(open('solution.py').read())\n"
                "\n"
                "# Test 1: Basic cases\n"
                "assert bisect_left([1, 3, 5, 7], 5) == 2\n"
                "assert bisect_left([1, 3, 5, 7], 4) == 2\n"
                "assert bisect_left([1, 3, 5, 7], 0) == 0\n"
                "assert bisect_left([1, 3, 5, 7], 8) == 4\n"
                "\n"
                "# Test 2: Duplicates — must return leftmost\n"
                "assert bisect_left([1, 2, 2, 2, 3], 2) == 1\n"
                "\n"
                "# Test 3: Empty array\n"
                "assert bisect_left([], 5) == 0\n"
                "\n"
                "# Test 4: Single element\n"
                "assert bisect_left([5], 3) == 0\n"
                "assert bisect_left([5], 5) == 0\n"
                "assert bisect_left([5], 7) == 1\n"
                "\n"
                "# Test 5: Large array (must be efficient — no timeout)\n"
                "big = list(range(0, 1000000, 2))  # even numbers\n"
                "assert bisect_left(big, 500000) == 250000\n"
                "assert bisect_left(big, 500001) == 250001\n"
                "\n"
                "# Test 6: No bisect module used\n"
                "with open('solution.py') as f:\n"
                "    src = f.read()\n"
                "assert 'import bisect' not in src, 'Must not use bisect module'\n"
                "\n"
                "print('ALL TESTS PASSED')\n"
            ),
        },
    },

    # ======================================================================
    # ALG-002: LRU cache with O(1) operations
    # ======================================================================
    {
        "id": "PILOT-ALG-002",
        "category": "ALG",
        "difficulty": "medium",
        "source": "pilot-synthetic",
        "title": "Implement LRU cache with O(1) get and put",
        "problem": (
            "Implement an LRUCache class with a fixed capacity.\n"
            "- LRUCache(capacity): Initialize with given capacity.\n"
            "- get(key): Return the value if key exists, else -1. Marks key as recently used.\n"
            "- put(key, value): Insert or update the key-value pair. If the cache exceeds\n"
            "  capacity, evict the least recently used item.\n"
            "Do NOT use functools.lru_cache or collections.OrderedDict.\n"
        ),
        "context_files": [
            {
                "path": "lru.py",
                "content": (
                    "class LRUCache:\n"
                    "    def __init__(self, capacity: int):\n"
                    "        pass  # TODO\n"
                    "    \n"
                    "    def get(self, key: int) -> int:\n"
                    "        pass  # TODO\n"
                    "    \n"
                    "    def put(self, key: int, value: int) -> None:\n"
                    "        pass  # TODO\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "test_suite",
            "test_script": (
                "exec(open('solution.py').read())\n"
                "\n"
                "# Test 1: Basic operations\n"
                "cache = LRUCache(2)\n"
                "cache.put(1, 1)\n"
                "cache.put(2, 2)\n"
                "assert cache.get(1) == 1\n"
                "cache.put(3, 3)  # evicts key 2\n"
                "assert cache.get(2) == -1\n"
                "cache.put(4, 4)  # evicts key 1\n"
                "assert cache.get(1) == -1\n"
                "assert cache.get(3) == 3\n"
                "assert cache.get(4) == 4\n"
                "\n"
                "# Test 2: Update existing key\n"
                "cache = LRUCache(2)\n"
                "cache.put(1, 1)\n"
                "cache.put(2, 2)\n"
                "cache.put(1, 10)  # update, key 1 is now most recent\n"
                "cache.put(3, 3)  # should evict key 2 (least recent)\n"
                "assert cache.get(2) == -1\n"
                "assert cache.get(1) == 10\n"
                "\n"
                "# Test 3: Capacity 1\n"
                "cache = LRUCache(1)\n"
                "cache.put(1, 1)\n"
                "assert cache.get(1) == 1\n"
                "cache.put(2, 2)\n"
                "assert cache.get(1) == -1\n"
                "assert cache.get(2) == 2\n"
                "\n"
                "# Test 4: Get makes key recently used\n"
                "cache = LRUCache(2)\n"
                "cache.put(1, 1)\n"
                "cache.put(2, 2)\n"
                "cache.get(1)     # key 1 is now most recent\n"
                "cache.put(3, 3)  # should evict key 2\n"
                "assert cache.get(2) == -1\n"
                "assert cache.get(1) == 1\n"
                "\n"
                "# Test 5: No OrderedDict or lru_cache\n"
                "with open('solution.py') as f:\n"
                "    src = f.read()\n"
                "assert 'OrderedDict' not in src, 'Must not use OrderedDict'\n"
                "assert 'lru_cache' not in src, 'Must not use functools.lru_cache'\n"
                "\n"
                "print('ALL TESTS PASSED')\n"
            ),
        },
    },

    # ======================================================================
    # TST-001: Write tests for a stack implementation
    # ======================================================================
    {
        "id": "PILOT-TST-001",
        "category": "TST",
        "difficulty": "easy",
        "source": "pilot-synthetic",
        "title": "Write unit tests for a stack implementation",
        "problem": (
            "Write a comprehensive test suite for the Stack class below.\n"
            "Your tests should cover: push, pop, peek, is_empty, size,\n"
            "underflow error handling, and multiple sequential operations.\n"
            "Provide the tests as a Python script using assert statements.\n"
            "The test script should import the Stack class and run all tests.\n"
        ),
        "context_files": [
            {
                "path": "stack.py",
                "content": (
                    "class Stack:\n"
                    "    def __init__(self):\n"
                    "        self._items = []\n"
                    "    \n"
                    "    def push(self, item):\n"
                    "        self._items.append(item)\n"
                    "    \n"
                    "    def pop(self):\n"
                    "        if not self._items:\n"
                    "            raise IndexError('pop from empty stack')\n"
                    "        return self._items.pop()\n"
                    "    \n"
                    "    def peek(self):\n"
                    "        if not self._items:\n"
                    "            raise IndexError('peek at empty stack')\n"
                    "        return self._items[-1]\n"
                    "    \n"
                    "    def is_empty(self):\n"
                    "        return len(self._items) == 0\n"
                    "    \n"
                    "    def size(self):\n"
                    "        return len(self._items)\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "test_suite",
            "test_script": (
                "# The solution should be a test script. We run it and check it exercises the Stack.\n"
                "# First, make the Stack available.\n"
                "with open('stack.py', 'w') as f:\n"
                "    f.write('''\n"
                "class Stack:\n"
                "    def __init__(self):\n"
                "        self._items = []\n"
                "    def push(self, item):\n"
                "        self._items.append(item)\n"
                "    def pop(self):\n"
                "        if not self._items:\n"
                "            raise IndexError('pop from empty stack')\n"
                "        return self._items.pop()\n"
                "    def peek(self):\n"
                "        if not self._items:\n"
                "            raise IndexError('peek at empty stack')\n"
                "        return self._items[-1]\n"
                "    def is_empty(self):\n"
                "        return len(self._items) == 0\n"
                "    def size(self):\n"
                "        return len(self._items)\n"
                "''')\n"
                "\n"
                "# Run the model's test script\n"
                "exec(open('solution.py').read())\n"
                "\n"
                "# Meta-check: the solution should reference key methods\n"
                "with open('solution.py') as f:\n"
                "    src = f.read()\n"
                "required = ['push', 'pop', 'peek', 'is_empty', 'size']\n"
                "for method in required:\n"
                "    assert method in src, f'Tests should exercise .{method}()'\n"
                "\n"
                "# Meta-check: should test underflow\n"
                "assert 'IndexError' in src or 'empty' in src.lower(), 'Should test empty stack behavior'\n"
                "\n"
                "print('ALL TESTS PASSED')\n"
            ),
        },
    },

    # ======================================================================
    # TST-002: Write edge-case tests for string utils
    # ======================================================================
    {
        "id": "PILOT-TST-002",
        "category": "TST",
        "difficulty": "medium",
        "source": "pilot-synthetic",
        "title": "Write edge-case tests for string truncation utility",
        "problem": (
            "Write a test suite for the truncate function below. Focus on edge cases:\n"
            "empty strings, max_len shorter than suffix, unicode characters,\n"
            "exact boundary lengths, and type errors. Use assert statements.\n"
        ),
        "context_files": [
            {
                "path": "strutils.py",
                "content": (
                    "def truncate(text, max_len=50, suffix='...'):\n"
                    "    \"\"\"Truncate text to max_len chars, adding suffix if truncated.\"\"\"\n"
                    "    if not isinstance(text, str):\n"
                    "        raise TypeError('text must be a string')\n"
                    "    if max_len < len(suffix):\n"
                    "        raise ValueError('max_len must be >= len(suffix)')\n"
                    "    if len(text) <= max_len:\n"
                    "        return text\n"
                    "    return text[:max_len - len(suffix)] + suffix\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "test_suite",
            "test_script": (
                "# Make the function available\n"
                "with open('strutils.py', 'w') as f:\n"
                "    f.write('''\n"
                "def truncate(text, max_len=50, suffix='...'):\n"
                "    if not isinstance(text, str):\n"
                "        raise TypeError('text must be a string')\n"
                "    if max_len < len(suffix):\n"
                "        raise ValueError('max_len must be >= len(suffix)')\n"
                "    if len(text) <= max_len:\n"
                "        return text\n"
                "    return text[:max_len - len(suffix)] + suffix\n"
                "''')\n"
                "\n"
                "exec(open('solution.py').read())\n"
                "\n"
                "with open('solution.py') as f:\n"
                "    src = f.read()\n"
                "\n"
                "# Must test: truncation, no-truncation, empty string, TypeError, ValueError\n"
                "assert 'truncate' in src, 'Tests should call truncate'\n"
                "checks = [\n"
                "    ('TypeError', 'Should test TypeError for non-string input'),\n"
                "    ('ValueError', 'Should test ValueError for small max_len'),\n"
                "]\n"
                "for keyword, msg in checks:\n"
                "    assert keyword in src, msg\n"
                "\n"
                "# Must have at least 5 assertions\n"
                "assert src.count('assert') >= 5, f'Expected >=5 assertions, found {src.count(\"assert\")}'\n"
                "\n"
                "print('ALL TESTS PASSED')\n"
            ),
        },
    },

    # ======================================================================
    # REV-001: Code review — find bugs in a function
    # ======================================================================
    {
        "id": "PILOT-REV-001",
        "category": "REV",
        "difficulty": "medium",
        "source": "pilot-synthetic",
        "title": "Review: find bugs in user session handler",
        "problem": (
            "Review the following session management code and identify all bugs.\n"
            "List each bug with a description of the issue and its impact.\n"
        ),
        "context_files": [
            {
                "path": "session.py",
                "content": (
                    "import time\n"
                    "import hashlib\n"
                    "\n"
                    "sessions = {}  # BUG 1: global mutable state, not thread-safe\n"
                    "\n"
                    "def create_session(user_id):\n"
                    "    token = hashlib.md5(str(user_id).encode()).hexdigest()  # BUG 2: predictable token\n"
                    "    sessions[token] = {\n"
                    "        'user_id': user_id,\n"
                    "        'created': time.time(),\n"
                    "        'expires': time.time() + 3600,\n"
                    "    }\n"
                    "    return token\n"
                    "\n"
                    "def get_session(token):\n"
                    "    session = sessions.get(token)\n"
                    "    if session:\n"
                    "        return session  # BUG 3: no expiry check\n"
                    "    return None\n"
                    "\n"
                    "def delete_session(token):\n"
                    "    del sessions[token]  # BUG 4: KeyError if token doesn't exist\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "f1_score",
            "ground_truth_issues": [
                "thread_safety",
                "predictable_token",
                "no_expiry_check",
                "key_error_delete",
            ],
        },
    },

    # ======================================================================
    # REV-002: Code review — find issues in API endpoint
    # ======================================================================
    {
        "id": "PILOT-REV-002",
        "category": "REV",
        "difficulty": "medium",
        "source": "pilot-synthetic",
        "title": "Review: find issues in REST API handler",
        "problem": (
            "Review the following API endpoint code and identify all bugs\n"
            "and security issues. List each issue with a description.\n"
        ),
        "context_files": [
            {
                "path": "api.py",
                "content": (
                    "import sqlite3\n"
                    "import json\n"
                    "\n"
                    "def get_user(request):\n"
                    "    user_id = request.args.get('id')\n"
                    "    # BUG 1: SQL injection — string formatting instead of parameterized query\n"
                    "    conn = sqlite3.connect('users.db')\n"
                    "    cursor = conn.execute(f\"SELECT * FROM users WHERE id = '{user_id}'\")\n"
                    "    row = cursor.fetchone()\n"
                    "    conn.close()\n"
                    "    \n"
                    "    if row:\n"
                    "        # BUG 2: exposes all columns including password_hash\n"
                    "        return json.dumps({'user': dict(zip(['id','name','email','password_hash'], row))})\n"
                    "    # BUG 3: no proper HTTP status code handling (returns None implicitly)\n"
                    "    # BUG 4: no input validation on user_id\n"
                ),
            }
        ],
        "output_format": "code_block",
        "scoring": {
            "method": "f1_score",
            "ground_truth_issues": [
                "sql_injection",
                "password_hash_exposure",
                "missing_error_response",
                "no_input_validation",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# YAML serialization (manual — avoids pyyaml formatting quirks)
# ---------------------------------------------------------------------------

def _yaml_str(val: str, indent: int = 0) -> str:
    """Format a string value for YAML, using block scalar if multiline."""
    prefix = " " * indent
    if "\n" in val:
        lines = val.rstrip("\n").split("\n")
        block = "\n".join(f"{prefix}  {line}" for line in lines)
        return f"|\n{block}\n"
    else:
        # Simple string — quote if it contains special chars
        if any(c in val for c in ":#{}[]&*!|>'\",@`"):
            return f'"{val}"'
        return val


def task_to_yaml(task: dict) -> str:
    """Convert a task dict to YAML string."""
    lines = []
    lines.append(f"id: \"{task['id']}\"")
    lines.append(f"category: \"{task['category']}\"")
    lines.append(f"difficulty: \"{task['difficulty']}\"")
    lines.append(f"source: \"{task['source']}\"")
    lines.append(f"title: \"{task['title']}\"")

    # Problem (block scalar)
    lines.append("problem: |")
    for line in task["problem"].rstrip("\n").split("\n"):
        lines.append(f"  {line}")

    # Context files
    lines.append("context_files:")
    for cf in task["context_files"]:
        lines.append(f"  - path: \"{cf['path']}\"")
        lines.append("    content: |")
        for line in cf["content"].rstrip("\n").split("\n"):
            lines.append(f"      {line}")

    # Output format
    lines.append(f"output_format: \"{task['output_format']}\"")

    # Scoring
    scoring = task["scoring"]
    lines.append("scoring:")
    lines.append(f"  method: \"{scoring['method']}\"")

    if "test_script" in scoring:
        lines.append("  test_script: |")
        for line in scoring["test_script"].rstrip("\n").split("\n"):
            lines.append(f"    {line}")

    if "ground_truth_issues" in scoring:
        lines.append("  ground_truth_issues:")
        for issue in scoring["ground_truth_issues"]:
            lines.append(f"    - \"{issue}\"")

    if "expected_output" in scoring:
        lines.append(f"  expected_output: \"{scoring['expected_output']}\"")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate V4 pilot task YAML files",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent / "v4"),
        help="Output directory for task files (default: tasks/v4/)",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for task in PILOT_TASKS:
        filename = f"{task['id'].lower().replace('-', '_')}.yaml"
        filepath = out_dir / filename
        yaml_content = task_to_yaml(task)
        filepath.write_text(yaml_content, encoding="utf-8")
        print(f"  Created: {filepath}")

    print(f"\nGenerated {len(PILOT_TASKS)} pilot tasks in {out_dir}")
    print("\nCategory distribution:")
    from collections import Counter
    cats = Counter(t["category"] for t in PILOT_TASKS)
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
