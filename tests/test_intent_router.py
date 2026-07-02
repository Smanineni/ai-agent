"""
test_intent_router.py — Tests for the Intent Router
=====================================================
WHAT WE TEST HERE:
    1. _parse_router_output() — the output parser that turns raw LLM text
       into a clean (intent, reasoning) tuple. Tests without any LLM call.
    2. classify_intent() return dict shape — the LLM call will fail (no credits)
       but the error should be captured cleanly with a safe fallback intent.

WHY TESTING THE PARSER IS VALUABLE:
    The parser handles messy, real-world LLM output. Testing it in isolation
    means we know exactly what it does before adding the LLM on top.
    This is the same reason you'd unit-test a JSON deserializer before testing
    the full REST endpoint that uses it.

HOW TO RUN:
    cd c:\\hybrid-ai-agent
    .\\venv\\Scripts\\Activate.ps1
    python -m tests.test_intent_router
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.router.intent_router import (
    _parse_router_output,
    classify_intent,
    QUERY_SQL,
    QUERY_DOC,
    QUERY_BOTH,
    _DEFAULT_INTENT,
)

GREEN = "\033[92m"
RED   = "\033[91m"
RESET = "\033[0m"

passed = 0
failed = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"{GREEN}  PASS{RESET}  {label}")
    else:
        failed += 1
        print(f"{RED}  FAIL{RESET}  {label}" + (f"\n       → {detail}" if detail else ""))


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 1: _parse_router_output() — no LLM needed
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 1: _parse_router_output() (no LLM needed)")
print("="*60)

# Test 1a: Clean, well-formed output — the ideal case
print("\n[1a] Clean two-line output")
intent, reasoning = _parse_router_output("QUERY_SQL\nThis asks about employee salary data.")
check("Intent is QUERY_SQL",    intent == QUERY_SQL,    f"Got: {intent}")
check("Reasoning captured",     "salary" in reasoning,  f"Got: {reasoning}")

# Test 1b: QUERY_DOC
print("\n[1b] QUERY_DOC output")
intent, reasoning = _parse_router_output("QUERY_DOC\nThis question is about leave policy.")
check("Intent is QUERY_DOC",    intent == QUERY_DOC,    f"Got: {intent}")

# Test 1c: QUERY_BOTH
print("\n[1c] QUERY_BOTH output")
intent, reasoning = _parse_router_output("QUERY_BOTH\nNeeds both database and document info.")
check("Intent is QUERY_BOTH",   intent == QUERY_BOTH,   f"Got: {intent}")

# Test 1d: LLM wraps intent in a sentence (common messy output)
print("\n[1d] Intent embedded in a sentence (e.g. 'The intent is QUERY_SQL')")
intent, reasoning = _parse_router_output("The intent is QUERY_SQL\nEmployee data question.")
check("Still extracts QUERY_SQL", intent == QUERY_SQL,  f"Got: {intent}")

# Test 1e: Lowercase output — LLM sometimes ignores casing instructions
print("\n[1e] Lowercase output (query_doc)")
intent, reasoning = _parse_router_output("query_doc\nAbout HR benefits policy.")
check("Case-insensitive: extracts QUERY_DOC", intent == QUERY_DOC, f"Got: {intent}")

# Test 1f: Unknown intent — should fall back to default (QUERY_BOTH)
print("\n[1f] Unrecognised intent falls back to QUERY_BOTH")
intent, reasoning = _parse_router_output("QUERY_UNKNOWN\nSomething unrecognised.")
check("Falls back to default",  intent == _DEFAULT_INTENT, f"Got: {intent}")

# Test 1g: Empty string — graceful handling
print("\n[1g] Empty output — graceful fallback")
intent, reasoning = _parse_router_output("")
check("Empty input returns default", intent == _DEFAULT_INTENT, f"Got: {intent}")

# Test 1h: Only one line (no reasoning)
print("\n[1h] Only intent line, no reasoning line")
intent, reasoning = _parse_router_output("QUERY_SQL")
check("Intent parsed correctly",       intent == QUERY_SQL, f"Got: {intent}")
check("Reasoning is placeholder text", reasoning != "",     f"Got: {reasoning}")

# Test 1i: Extra whitespace and blank lines
print("\n[1i] Extra whitespace and blank lines around output")
intent, reasoning = _parse_router_output("\n\n  QUERY_BOTH  \n\n  Needs both.  \n\n")
check("Strips whitespace correctly", intent == QUERY_BOTH, f"Got: {intent}")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 2: IntentResult dataclass shape
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 2: IntentResult dataclass")
print("="*60)

from app.router.intent_router import IntentResult

print("\n[2a] IntentResult has correct fields")
result = IntentResult(intent=QUERY_SQL, reasoning="Test reasoning.")
check("Has .intent",    hasattr(result, "intent"))
check("Has .reasoning", hasattr(result, "reasoning"))
check("Has .error",     hasattr(result, "error"))
check(".error defaults to None", result.error is None, f"Got: {result.error}")

print("\n[2b] IntentResult with error set")
result_err = IntentResult(intent=QUERY_BOTH, reasoning="Fallback.", error="LLM failed")
check("Error is set",   result_err.error == "LLM failed", f"Got: {result_err.error}")
check("Intent still set on error", result_err.intent == QUERY_BOTH)


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 3: classify_intent() end-to-end (LLM will fail — that's OK)
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 3: classify_intent() return shape (LLM will fail — that's OK)")
print("="*60)
print("NOTE: GPT-4o call will fail (quota exceeded). We check that the error")
print("      is captured and the safe fallback QUERY_BOTH is returned.\n")

result = classify_intent("Who are the highest paid engineers?")

check("Returns IntentResult",               isinstance(result, IntentResult))
check("Has .intent attribute",              hasattr(result, "intent"))
check("Intent is a valid string",           result.intent in {QUERY_SQL, QUERY_DOC, QUERY_BOTH},
      f"Got: {result.intent}")
check("Fallback is QUERY_BOTH on error",    result.intent == QUERY_BOTH,
      f"Got: {result.intent} (expected QUERY_BOTH as safe fallback)")
check("Error is captured (not swallowed)",  result.error is not None,
      "error field should be set since LLM call failed")

print(f"\n  Error captured: {str(result.error)[:100]}...")


# ════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
total = passed + failed
print(f"RESULTS: {passed}/{total} tests passed")
if failed == 0:
    print(f"{GREEN}All tests passed!{RESET}")
else:
    print(f"{RED}{failed} test(s) failed — see details above.{RESET}")
print("="*60 + "\n")
