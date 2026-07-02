"""
feedback_store.py — Feedback Loop: Rating Storage and Golden Queries
=====================================================================
WHAT THIS FILE DOES:
    Records every thumbs-up / thumbs-down rating from the Streamlit UI,
    stores it in a SQLite table, and provides query functions so humans
    can review bad answers, add corrections, and build a golden query set.

THE DATA FLOW:
    User reads answer in Streamlit UI
        ↓
    Clicks 👍 or 👎
        ↓
    store_feedback() writes to the 'feedback' table
        ↓
    (later) Human reviewer opens admin panel
        ↓
    get_thumbs_down() shows bad answers
        ↓
    Reviewer writes correct answer
        ↓
    add_correction() updates the row
        ↓
    get_golden_queries() returns verified pairs
        → used for regression tests / few-shot prompting

WHY SQLITE (not a separate DB)?
    The feedback volume for a prototype is low (hundreds of rows, not millions).
    SQLite is already in use for employee data — adding a table is free.
    In production you'd move to PostgreSQL alongside the main schema.

JAVA ANALOGY:
    This is a @Repository class backed by a SQLite table.
    store_feedback() = save()
    get_thumbs_down() = findByRatingOrderByTimestampDesc()
    add_correction() = updateById()
    get_golden_queries() = findByCorrectionIsNotNull()
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import os

from dotenv import load_dotenv

load_dotenv()

# ── Database path ─────────────────────────────────────────────────────────────
# We reuse the same company.db file — just adding a new table.
# This keeps all persistent data in one place for the prototype.
_DB_PATH = Path(
    os.getenv("SQLITE_DB_PATH", "data/db/company.db")
).resolve()

# ── Rating constants ──────────────────────────────────────────────────────────
THUMBS_UP   = "thumbs_up"
THUMBS_DOWN = "thumbs_down"


# ── Schema creation ───────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection with row_factory set so rows behave like dicts.

    row_factory = sqlite3.Row means instead of:
        row[0], row[1], row[2] ...
    you can write:
        row["question"], row["rating"], row["timestamp"]

    This is the SQLite equivalent of a ResultSet with named columns.
    """
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row  # access columns by name
    return conn


def create_feedback_table() -> None:
    """
    Create the feedback table if it doesn't already exist.

    Columns:
        id          — auto-increment primary key
        question    — the user's original question
        answer      — the agent's answer that was rated
        intent      — QUERY_SQL | QUERY_DOC | QUERY_BOTH | ERROR
        rating      — "thumbs_up" or "thumbs_down"
        correction  — human-written correct answer (NULL until reviewed)
        session_id  — optional session identifier for grouping conversations
        timestamp   — ISO 8601 UTC timestamp of when the feedback was given

    IF NOT EXISTS means this is safe to call on every startup — it only
    creates the table the first time. Same as SQLAlchemy's create_all().
    """
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                question    TEXT    NOT NULL,
                answer      TEXT    NOT NULL,
                intent      TEXT    NOT NULL,
                rating      TEXT    NOT NULL,
                correction  TEXT    DEFAULT NULL,
                session_id  TEXT    DEFAULT NULL,
                timestamp   TEXT    NOT NULL
            )
        """)
        conn.commit()


# ── Write operations ──────────────────────────────────────────────────────────

def store_feedback(
    question: str,
    answer: str,
    intent: str,
    rating: str,
    session_id: Optional[str] = None,
) -> int:
    """
    Record a user's rating for one answer.

    Parameters
    ----------
    question   : the user's question
    answer     : the agent's answer that was rated
    intent     : QUERY_SQL | QUERY_DOC | QUERY_BOTH | ERROR
    rating     : use THUMBS_UP or THUMBS_DOWN constants
    session_id : optional session identifier

    Returns
    -------
    int — the new row's id (useful for tests and for linking corrections)
    """
    if rating not in (THUMBS_UP, THUMBS_DOWN):
        raise ValueError(f"rating must be '{THUMBS_UP}' or '{THUMBS_DOWN}', got: {rating!r}")

    timestamp = datetime.now(timezone.utc).isoformat()

    with _get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO feedback (question, answer, intent, rating, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (question, answer, intent, rating, session_id, timestamp),
        )
        conn.commit()
        return cursor.lastrowid  # the auto-assigned id of the new row


def add_correction(feedback_id: int, correct_answer: str) -> bool:
    """
    Add a human-written correction to a thumbs-down row.

    Once a correction is added, this row becomes a "golden query" —
    a verified (question, correct_answer) pair that can be used for:
      - Regression testing before deployments
      - Few-shot examples in prompts to improve accuracy on similar questions

    Parameters
    ----------
    feedback_id    : the id of the feedback row to update
    correct_answer : the human-verified correct answer

    Returns
    -------
    bool — True if the row was found and updated, False if id not found
    """
    with _get_connection() as conn:
        cursor = conn.execute(
            "UPDATE feedback SET correction = ? WHERE id = ?",
            (correct_answer, feedback_id),
        )
        conn.commit()
        return cursor.rowcount > 0  # True if a row was actually updated


# ── Read operations ───────────────────────────────────────────────────────────

def get_thumbs_down(limit: int = 50) -> list[dict]:
    """
    Return the most recent thumbs-down entries, for human review.

    The admin panel in Streamlit will call this to show the reviewer
    a list of bad answers. The reviewer can then write a correction
    using add_correction().

    Returns
    -------
    list of dicts — each dict has: id, question, answer, intent,
                    correction, session_id, timestamp
    """
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, question, answer, intent, correction, session_id, timestamp
            FROM   feedback
            WHERE  rating = ?
            ORDER  BY timestamp DESC
            LIMIT  ?
            """,
            (THUMBS_DOWN, limit),
        ).fetchall()
    # sqlite3.Row objects behave like dicts but convert them explicitly
    # so callers get plain Python dicts (easier to test and serialise)
    return [dict(row) for row in rows]


def get_golden_queries() -> list[dict]:
    """
    Return all feedback rows that have a human correction (golden queries).

    These are verified (question, correct_answer) pairs where:
        rating     = thumbs_down  (the agent got it wrong)
        correction IS NOT NULL    (a human wrote the right answer)

    Use cases:
      1. Regression tests — run before every deployment
      2. Few-shot prompting — inject 2-3 examples into the prompt to
         show the LLM what a good answer looks like for this question type

    Returns
    -------
    list of dicts with: id, question, answer (original bad), correction
                        (the good answer), intent, timestamp
    """
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, question, answer, correction, intent, timestamp
            FROM   feedback
            WHERE  correction IS NOT NULL
            ORDER  BY timestamp DESC
            """,
        ).fetchall()
    return [dict(row) for row in rows]


def get_stats() -> dict:
    """
    Return a summary of feedback counts for the admin dashboard.

    Returns
    -------
    dict with:
        total        — total feedback events
        thumbs_up    — count of positive ratings
        thumbs_down  — count of negative ratings
        corrected    — count of thumbs-down with a correction added
        approval_pct — percentage of thumbs-up (0-100, rounded to 1dp)
    """
    with _get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        ups   = conn.execute(
            "SELECT COUNT(*) FROM feedback WHERE rating = ?", (THUMBS_UP,)
        ).fetchone()[0]
        downs = conn.execute(
            "SELECT COUNT(*) FROM feedback WHERE rating = ?", (THUMBS_DOWN,)
        ).fetchone()[0]
        corrected = conn.execute(
            "SELECT COUNT(*) FROM feedback WHERE correction IS NOT NULL"
        ).fetchone()[0]

    approval_pct = round((ups / total * 100), 1) if total > 0 else 0.0

    return {
        "total":        total,
        "thumbs_up":    ups,
        "thumbs_down":  downs,
        "corrected":    corrected,
        "approval_pct": approval_pct,
    }


# ── Initialise on import ──────────────────────────────────────────────────────
# Create the table when this module is first imported.
# Safe to call repeatedly — CREATE TABLE IF NOT EXISTS is idempotent.
create_feedback_table()
