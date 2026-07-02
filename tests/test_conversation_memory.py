"""
test_conversation_memory.py — Tests for ConversationMemory
============================================================
WHAT WE TEST HERE:
    Everything in conversation_memory.py is pure Python — no LLM, no network,
    no database. So every test here runs instantly and fully offline.

    We test:
      1. Basic add and retrieve
      2. Sliding window eviction (oldest turn dropped when full)
      3. get_history_as_text() format
      4. get_messages() format (role/content dicts)
      5. clear() resets state
      6. Edge cases: empty memory, window_size=1, single turn

HOW TO RUN:
    cd c:\\hybrid-ai-agent
    .\\venv\\Scripts\\Activate.ps1
    python -m tests.test_conversation_memory
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory.conversation_memory import ConversationMemory, Turn

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
# TEST GROUP 1: Basic operations
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 1: Basic add and retrieve")
print("="*60)

mem = ConversationMemory(window_size=3)

print("\n[1a] Fresh memory is empty")
check("is_empty is True",    mem.is_empty)
check("turn_count is 0",     mem.turn_count == 0)
check("get_messages() == []", mem.get_messages() == [])
check("get_history_as_text() == ''", mem.get_history_as_text() == "")

print("\n[1b] Add one turn")
mem.add_turn(
    question="Who is the highest paid engineer?",
    answer="David Park, $145,000.",
    intent="QUERY_SQL"
)
check("turn_count is 1",    mem.turn_count == 1)
check("is_empty is False",  not mem.is_empty)

turns = mem.get_turns()
check("get_turns() returns 1 Turn",          len(turns) == 1)
check("Turn.question stored correctly",       turns[0].question == "Who is the highest paid engineer?")
check("Turn.answer stored correctly",         turns[0].answer == "David Park, $145,000.")
check("Turn.intent stored correctly",         turns[0].intent == "QUERY_SQL")

print("\n[1c] Add second turn")
mem.add_turn(
    question="What department is he in?",
    answer="Engineering."
)
check("turn_count is 2",   mem.turn_count == 2)


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 2: Sliding window eviction
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 2: Sliding window eviction (window_size=3)")
print("="*60)

mem2 = ConversationMemory(window_size=3)
for i in range(1, 6):   # Add 5 turns to a window of 3
    mem2.add_turn(question=f"Question {i}", answer=f"Answer {i}")

print("\n[2a] After 5 turns with window=3, only last 3 are kept")
check("turn_count is 3 (not 5)",    mem2.turn_count == 3,
      f"Got: {mem2.turn_count}")

turns2 = mem2.get_turns()
check("Oldest surviving turn is Turn 3",  turns2[0].question == "Question 3",
      f"Got: {turns2[0].question}")
check("Middle turn is Turn 4",            turns2[1].question == "Question 4",
      f"Got: {turns2[1].question}")
check("Newest turn is Turn 5",            turns2[2].question == "Question 5",
      f"Got: {turns2[2].question}")

print("\n[2b] Add one more — window rolls forward")
mem2.add_turn(question="Question 6", answer="Answer 6")
turns2b = mem2.get_turns()
check("turn_count still 3",               mem2.turn_count == 3)
check("Oldest is now Turn 4",             turns2b[0].question == "Question 4",
      f"Got: {turns2b[0].question}")
check("Newest is now Turn 6",             turns2b[2].question == "Question 6",
      f"Got: {turns2b[2].question}")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 3: get_history_as_text()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 3: get_history_as_text() format")
print("="*60)

mem3 = ConversationMemory(window_size=3)
mem3.add_turn("Who is Alice?",    "Alice Sharma, Senior Engineer.")
mem3.add_turn("What is her salary?", "115,000.")

print("\n[3a] Text contains Human/Assistant labels")
text = mem3.get_history_as_text()
check("Contains 'Human:' label",     "Human:" in text,         f"Got:\n{text}")
check("Contains 'Assistant:' label", "Assistant:" in text,     f"Got:\n{text}")
check("Contains first question",     "Who is Alice?" in text,  f"Got:\n{text}")
check("Contains first answer",       "Alice Sharma" in text,   f"Got:\n{text}")
check("Contains second question",    "What is her salary?" in text)
check("Contains second answer",      "115,000." in text)

print("\n[3b] Turns appear in chronological order (oldest first)")
pos_q1 = text.index("Who is Alice?")
pos_q2 = text.index("What is her salary?")
check("First question appears before second", pos_q1 < pos_q2,
      f"pos_q1={pos_q1}, pos_q2={pos_q2}")

print("\n[3c] Empty memory returns empty string")
mem_empty = ConversationMemory()
check("Empty memory → empty string", mem_empty.get_history_as_text() == "")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4: get_messages()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 4: get_messages() format (role/content dicts)")
print("="*60)

mem4 = ConversationMemory(window_size=2)
mem4.add_turn("What projects are active?", "The AI Modernisation project is active.")
mem4.add_turn("Who leads it?",             "David Park leads it.")

print("\n[4a] Returns list of dicts with role and content keys")
messages = mem4.get_messages()
check("Returns a list",                     isinstance(messages, list))
check("2 turns → 4 messages",              len(messages) == 4,
      f"Got: {len(messages)}")
check("First message role is 'human'",      messages[0]["role"] == "human",
      f"Got: {messages[0]['role']}")
check("Second message role is 'assistant'", messages[1]["role"] == "assistant",
      f"Got: {messages[1]['role']}")
check("First human content correct",        messages[0]["content"] == "What projects are active?")
check("First assistant content correct",    messages[1]["content"] == "The AI Modernisation project is active.")
check("Alternates human/assistant",         messages[2]["role"] == "human" and messages[3]["role"] == "assistant")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 5: clear()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 5: clear() resets state")
print("="*60)

mem5 = ConversationMemory(window_size=3)
mem5.add_turn("Q1", "A1")
mem5.add_turn("Q2", "A2")
check("Before clear: 2 turns", mem5.turn_count == 2)

mem5.clear()
check("After clear: 0 turns",         mem5.turn_count == 0)
check("After clear: is_empty True",   mem5.is_empty)
check("After clear: messages empty",  mem5.get_messages() == [])
check("After clear: text is ''",      mem5.get_history_as_text() == "")

print("\n[5b] Can add turns again after clear")
mem5.add_turn("New Q1", "New A1")
check("After re-add: turn_count is 1", mem5.turn_count == 1)
check("New question stored correctly", mem5.get_turns()[0].question == "New Q1")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 6: Edge cases
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 6: Edge cases")
print("="*60)

print("\n[6a] window_size=1 keeps only the single latest turn")
mem6 = ConversationMemory(window_size=1)
mem6.add_turn("First question", "First answer")
mem6.add_turn("Second question", "Second answer")
check("Only 1 turn kept",              mem6.turn_count == 1)
check("Latest turn is the one stored", mem6.get_turns()[0].question == "Second question",
      f"Got: {mem6.get_turns()[0].question}")

print("\n[6b] Turn without intent has intent=None")
mem7 = ConversationMemory()
mem7.add_turn("Q?", "A.")  # no intent arg
check("intent defaults to None", mem7.get_turns()[0].intent is None)

print("\n[6c] __repr__ is readable")
mem8 = ConversationMemory(window_size=5)
mem8.add_turn("Q", "A")
r = repr(mem8)
check("repr contains window_size", "window_size=5" in r, f"Got: {r}")
check("repr contains turn count",  "turns=1" in r,       f"Got: {r}")


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
