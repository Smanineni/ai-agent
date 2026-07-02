"""
test_feedback_store.py — Tests for the Feedback Store
=======================================================
WHAT WE TEST HERE:
    The feedback store is pure SQLite — no LLM, no network.
    Every test runs instantly and fully offline.

    We test:
      1. Table creation (idempotent — safe to run twice)
      2. store_feedback() — writes a row, returns the new id
      3. Invalid rating rejected with ValueError
      4. get_thumbs_down() — returns only thumbs-down rows, most recent first
      5. add_correction() — updates a row; returns True/False
      6. get_golden_queries() — only rows with corrections
      7. get_stats() — correct counts and approval percentage
      8. Full lifecycle: submit → thumbs down → correct → appears as golden

HOW TO RUN:
    cd c:\\hybrid-ai-agent
    .\\venv\\Scripts\\Activate.ps1
    python -m tests.test_feedback_store
"""

import sys
import os
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Point the module at a TEMPORARY database for testing ─────────────────────
# We don't want tests to pollute the real company.db with fake feedback.
# We create a fresh temp .db file and patch the module's _DB_PATH before
# importing the functions.
# This is the same principle as using an in-memory H2 database in Spring Boot
# tests instead of the real PostgreSQL database.

_temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_temp_db_path = Path(_temp_db.name)
_temp_db.close()

# Patch the environment variable so feedback_store uses our temp DB
os.environ["SQLITE_DB_PATH"] = str(_temp_db_path)

# NOW import — the module will read the patched env var
import importlib
import app.feedback.feedback_store as _fs_module
importlib.reload(_fs_module)  # reload so it picks up the patched path

from app.feedback.feedback_store import (
    store_feedback,
    add_correction,
    get_thumbs_down,
    get_golden_queries,
    get_stats,
    create_feedback_table,
    THUMBS_UP,
    THUMBS_DOWN,
)

# Reload the public names to point at the reloaded module's functions
store_feedback     = _fs_module.store_feedback
add_correction     = _fs_module.add_correction
get_thumbs_down    = _fs_module.get_thumbs_down
get_golden_queries = _fs_module.get_golden_queries
get_stats          = _fs_module.get_stats
create_feedback_table = _fs_module.create_feedback_table

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
# TEST GROUP 1: Table creation
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 1: Table creation")
print("="*60)

print("\n[1a] create_feedback_table() is idempotent (safe to call twice)")
try:
    create_feedback_table()
    create_feedback_table()
    check("No error on double create", True)
except Exception as e:
    check("No error on double create", False, str(e))

print("\n[1b] Table exists in the database")
conn = sqlite3.connect(str(_temp_db_path))
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'"
).fetchall()
conn.close()
check("feedback table exists", len(tables) == 1, f"Tables found: {tables}")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 2: store_feedback()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 2: store_feedback()")
print("="*60)

print("\n[2a] Store a thumbs-up")
id1 = store_feedback(
    question="Who is the highest paid engineer?",
    answer="David Park, $145,000.",
    intent="QUERY_SQL",
    rating=THUMBS_UP,
    session_id="session-001",
)
check("Returns an integer id",        isinstance(id1, int),  f"Got: {id1!r}")
check("id is positive",               id1 > 0,              f"Got: {id1}")

print("\n[2b] Store a thumbs-down")
id2 = store_feedback(
    question="How many sick days do I get?",
    answer="You get 8 days.",  # wrong answer — will be corrected later
    intent="QUERY_DOC",
    rating=THUMBS_DOWN,
    session_id="session-001",
)
check("Second insert gets a different id", id2 != id1, f"id1={id1}, id2={id2}")

print("\n[2c] Store another thumbs-down (different session)")
id3 = store_feedback(
    question="What is the maternity leave policy?",
    answer="I don't have that information.",
    intent="QUERY_DOC",
    rating=THUMBS_DOWN,
)
check("Third insert succeeds", isinstance(id3, int) and id3 > 0)

print("\n[2d] Invalid rating raises ValueError")
try:
    store_feedback("Q", "A", "QUERY_SQL", "bad_rating")
    check("ValueError raised for bad rating", False, "No error was raised")
except ValueError:
    check("ValueError raised for bad rating", True)


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 3: get_thumbs_down()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 3: get_thumbs_down()")
print("="*60)

print("\n[3a] Returns only thumbs-down rows")
downs = get_thumbs_down()
check("Returns a list",                        isinstance(downs, list))
check("Contains 2 thumbs-down rows (not 1 thumbs-up)", len(downs) == 2,
      f"Got {len(downs)} rows")

print("\n[3b] Each row has expected keys")
if downs:
    row = downs[0]
    for key in ("id", "question", "answer", "intent", "correction", "timestamp"):
        check(f"Row has '{key}' key", key in row, f"Keys: {list(row.keys())}")

print("\n[3c] Most recent thumbs-down is first")
if len(downs) >= 2:
    check("Most recent first (id3 > id2)",
          downs[0]["id"] == id3,
          f"Expected id {id3}, got {downs[0]['id']}")

print("\n[3d] Correction field is NULL before any correction")
if downs:
    check("correction is None initially", downs[0]["correction"] is None,
          f"Got: {downs[0]['correction']}")

print("\n[3e] Respects limit parameter")
limited = get_thumbs_down(limit=1)
check("limit=1 returns exactly 1 row", len(limited) == 1, f"Got: {len(limited)}")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4: add_correction()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 4: add_correction()")
print("="*60)

print("\n[4a] Add a correction to the sick-days thumbs-down")
success = add_correction(id2, "Employees receive 10 sick days per year.")
check("Returns True when row updated",   success is True,  f"Got: {success}")

print("\n[4b] The correction now appears in get_thumbs_down()")
downs_after = get_thumbs_down()
corrected_rows = [r for r in downs_after if r["id"] == id2]
check("Row still appears in thumbs-down",     len(corrected_rows) == 1)
check("Correction text saved correctly",
      corrected_rows[0]["correction"] == "Employees receive 10 sick days per year.",
      f"Got: {corrected_rows[0]['correction']}")

print("\n[4c] add_correction() returns False for non-existent id")
result = add_correction(99999, "This id doesn't exist.")
check("Returns False for unknown id",    result is False, f"Got: {result}")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 5: get_golden_queries()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 5: get_golden_queries()")
print("="*60)

print("\n[5a] Only returns rows with corrections")
golden = get_golden_queries()
check("Returns a list",                             isinstance(golden, list))
check("Exactly 1 golden query (only id2 corrected)", len(golden) == 1,
      f"Got {len(golden)}")

print("\n[5b] Golden query has expected fields")
if golden:
    g = golden[0]
    check("Has 'question' field",    "question"   in g)
    check("Has 'correction' field",  "correction" in g)
    check("Has 'intent' field",      "intent"     in g)
    check("Correction is not None",  g["correction"] is not None)
    check("Question matches",
          g["question"] == "How many sick days do I get?",
          f"Got: {g['question']}")

print("\n[5c] Add second correction — both appear as golden")
add_correction(id3, "Maternity leave is 16 weeks fully paid.")
golden2 = get_golden_queries()
check("Now 2 golden queries",        len(golden2) == 2, f"Got {len(golden2)}")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 6: get_stats()
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 6: get_stats()")
print("="*60)

# Current state: 1 thumbs-up (id1), 2 thumbs-down (id2, id3), 2 corrected
stats = get_stats()

print(f"\n  Stats: {stats}")
check("Has 'total' key",        "total"        in stats)
check("Has 'thumbs_up' key",    "thumbs_up"    in stats)
check("Has 'thumbs_down' key",  "thumbs_down"  in stats)
check("Has 'corrected' key",    "corrected"    in stats)
check("Has 'approval_pct' key", "approval_pct" in stats)
check("total is 3",             stats["total"] == 3,       f"Got: {stats['total']}")
check("thumbs_up is 1",         stats["thumbs_up"] == 1,   f"Got: {stats['thumbs_up']}")
check("thumbs_down is 2",       stats["thumbs_down"] == 2, f"Got: {stats['thumbs_down']}")
check("corrected is 2",         stats["corrected"] == 2,   f"Got: {stats['corrected']}")
check("approval_pct is 33.3",   stats["approval_pct"] == 33.3,
      f"Got: {stats['approval_pct']}")


# ════════════════════════════════════════════════════════════════════════════
# TEST GROUP 7: Full lifecycle
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST GROUP 7: Full lifecycle — submit, rate, correct, retrieve golden")
print("="*60)

id4 = store_feedback(
    question="What is the 401k matching policy?",
    answer="The company matches 100% up to 3% of salary.",  # wrong
    intent="QUERY_DOC",
    rating=THUMBS_DOWN,
    session_id="lifecycle-test",
)
check("New feedback stored",                isinstance(id4, int) and id4 > 0)

downs_lifecycle = get_thumbs_down(limit=1)
check("Appears first in thumbs-down list",  downs_lifecycle[0]["id"] == id4)
check("No correction yet",                  downs_lifecycle[0]["correction"] is None)

add_correction(id4, "The company matches 50% on contributions up to 6% of salary.")
golden_lifecycle = get_golden_queries()
ids_in_golden = [g["id"] for g in golden_lifecycle]
check("Now appears in golden queries",      id4 in ids_in_golden,
      f"Golden ids: {ids_in_golden}")


# ════════════════════════════════════════════════════════════════════════════
# CLEANUP — remove the temp database
# ════════════════════════════════════════════════════════════════════════════
try:
    _temp_db_path.unlink()
except Exception:
    pass

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
