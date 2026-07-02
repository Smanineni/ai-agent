"""
test_orchestrator.py — Tests for the Orchestrator
===================================================
WHAT WE TEST HERE:
    The orchestrator wires together router + engines + memory.
    The LLM calls will fail (quota exceeded), so we test:

    1. _enrich_question() — memory injection into the prompt (no LLM)
    2. _combine_answers() — QUERY_BOTH result merging (no LLM)
    3. AgentResponse dataclass shape (no LLM)
    4. ask() return shape when LLM fails — error captured, memory updated
    5. Memory is updated correctly after ask() — even on LLM failure
    6. Multi-turn: memory carries across two ask() calls

HOW TO RUN:
    cd c:\\hybrid-ai-agent
    .\\venv\\Scripts\\Activate.ps1
    python -m tests.test_orchestrator
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.orchestrator.orchestrator import (
    ask,
    AgentResponse,
    _enrich_question,
    _combine_answers,
)
from app.memory.conversation_memory import ConversationMemory
from app.router.intent_router import QUERY_SQL, QUERY_DOC, QUERY_BOTH

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
# TEST GROUP 1: _enrich_question() — no LLM needed
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 1: _enrich_question() (no LLM needed)")
print("="*60)

print("\n[1a] Empty memory — question returned unchanged")
mem_empty = ConversationMemory()
result = _enrich_question("Who is Alice?", mem_empty)
check("Returns original question",     result == "Who is Alice?",
      f"Got: {result}")

print("\n[1b] Memory with 1 turn — history prepended")
mem1 = ConversationMemory(window_size=3)
mem1.add_turn("Who is the highest paid engineer?", "David Park, $145,000.")
enriched = _enrich_question("What department is he in?", mem1)

check("Contains 'Previous conversation:' header", "Previous conversation:" in enriched)
check("Contains prior human turn",                "Who is the highest paid engineer?" in enriched)
check("Contains prior assistant answer",          "David Park" in enriched)
check("Contains 'Current question:' label",       "Current question:" in enriched)
check("Contains the current question",            "What department is he in?" in enriched)

print("\n[1c] History appears BEFORE the current question")
pos_history = enriched.index("David Park")
pos_current = enriched.index("What department is he in?")
check("History precedes current question",        pos_history < pos_current)

print("\n[1d] Multiple turns in memory — all included")
mem2 = ConversationMemory(window_size=3)
mem2.add_turn("Q1", "A1")
mem2.add_turn("Q2", "A2")
enriched2 = _enrich_question("Q3", mem2)
check("Both prior turns appear in enriched text", "Q1" in enriched2 and "Q2" in enriched2)


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 2: _combine_answers() — no LLM needed
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 2: _combine_answers() (no LLM needed)")
print("="*60)

print("\n[2a] Both engines returned answers")
sql_r  = {"answer": "David Park earns $145,000.", "sql": "SELECT ...", "raw_rows": "..."}
rag_r  = {"answer": "Employees get 20 days annual leave.", "sources": ["hr_leave_policy.txt"]}
combined = _combine_answers("question", sql_r, rag_r)

check("SQL answer included",           "David Park" in combined,       f"Got: {combined}")
check("RAG answer included",           "20 days annual leave" in combined)
check("Source file mentioned",         "hr_leave_policy.txt" in combined)
check("Both sections present",         "employee database" in combined.lower() and
                                        "hr documents" in combined.lower())

print("\n[2b] Only SQL engine answered (RAG empty)")
combined_sql_only = _combine_answers("q", {"answer": "SQL answer here."}, {})
check("SQL answer present",            "SQL answer here." in combined_sql_only)

print("\n[2c] Only RAG engine answered (SQL empty)")
combined_rag_only = _combine_answers("q", {}, {"answer": "RAG answer here.", "sources": []})
check("RAG answer present",            "RAG answer here." in combined_rag_only)

print("\n[2d] Both engines empty — fallback message")
combined_none = _combine_answers("q", {}, {})
check("Returns fallback message",      "could not find" in combined_none.lower(),
      f"Got: {combined_none}")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 3: AgentResponse dataclass shape
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 3: AgentResponse dataclass")
print("="*60)

resp = AgentResponse(answer="Test answer.", intent=QUERY_SQL)
check("Has .answer",        hasattr(resp, "answer"))
check("Has .intent",        hasattr(resp, "intent"))
check("Has .sql_used",      hasattr(resp, "sql_used"))
check("Has .sources",       hasattr(resp, "sources"))
check("Has .error",         hasattr(resp, "error"))
check("Has .raw_sql_rows",  hasattr(resp, "raw_sql_rows"))
check(".sql_used defaults None",    resp.sql_used is None)
check(".sources defaults []",       resp.sources == [])
check(".error defaults None",       resp.error is None)
check(".raw_sql_rows defaults None", resp.raw_sql_rows is None)


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4: ask() return shape — LLM will fail, that's expected
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 4: ask() return shape (LLM will fail — that's OK)")
print("="*60)
print("NOTE: GPT-4o calls will fail (quota exceeded). Checking that the")
print("      orchestrator handles errors cleanly and returns AgentResponse.\n")

mem_ask = ConversationMemory(window_size=3)
response = ask("Who are the highest paid engineers?", mem_ask)

check("Returns AgentResponse",            isinstance(response, AgentResponse))
check("Has non-empty .answer",            bool(response.answer))
check(".intent is a non-empty string",    bool(response.intent))
check(".sources is a list",               isinstance(response.sources, list))


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 5: Memory is updated after ask()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 5: Memory updated after ask()")
print("="*60)

mem_mem = ConversationMemory(window_size=3)
check("Memory empty before ask()",    mem_mem.is_empty)

ask("What is the sick leave policy?", mem_mem)

check("Memory has 1 turn after ask()",       mem_mem.turn_count == 1,
      f"Got: {mem_mem.turn_count}")
check("Stored question matches",             mem_mem.get_turns()[0].question == "What is the sick leave policy?",
      f"Got: {mem_mem.get_turns()[0].question}")
check("Stored answer is non-empty string",   bool(mem_mem.get_turns()[0].answer))


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 6: Multi-turn — memory carries across calls
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 6: Multi-turn conversation")
print("="*60)

mem_multi = ConversationMemory(window_size=3)

print("  Turn 1...")
ask("Who is the highest paid engineer?", mem_multi)
check("After turn 1: memory has 1 turn",   mem_multi.turn_count == 1)

print("  Turn 2...")
ask("What is their leave entitlement?", mem_multi)
check("After turn 2: memory has 2 turns",  mem_multi.turn_count == 2,
      f"Got: {mem_multi.turn_count}")

# The second enriched question should have included the first turn's context
# We can verify by checking the memory contains both turns
turns = mem_multi.get_turns()
check("Turn 1 question stored",    turns[0].question == "Who is the highest paid engineer?")
check("Turn 2 question stored",    turns[1].question == "What is their leave entitlement?")

print("  Turn 3 — history text now contains both prior turns")
history_text = mem_multi.get_history_as_text()
check("History contains turn 1",   "Who is the highest paid engineer?" in history_text)
check("History contains turn 2",   "What is their leave entitlement?" in history_text)


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
