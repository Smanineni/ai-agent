"""
conversation_memory.py — Sliding Window Conversation Memory
=============================================================
WHAT THIS FILE DOES:
    Keeps a rolling window of the last k conversation turns so the
    orchestrator can inject recent history into every LLM prompt.

    A "turn" is one exchange: one user question + one agent answer.
    We store turns as a list and trim the oldest when we exceed k.

WHY MEMORY MATTERS:
    Without memory, every question is stateless. The agent can't resolve
    pronouns like "their", "that project", "him" — it has no context.

    With memory, before sending the user's next question to the LLM,
    we prepend the last k turns. The LLM sees the full conversation
    context and can resolve references correctly.

    This is called anaphora resolution — understanding that "he" in
    "what leave does he get?" refers to "David Park" from the previous turn.

HOW THE WINDOW WORKS:
    k = 3 (default). Memory stores turns in a list:

    After turn 1: [t1]
    After turn 2: [t1, t2]
    After turn 3: [t1, t2, t3]
    After turn 4: [t2, t3, t4]  ← t1 dropped (oldest evicted)
    After turn 5: [t3, t4, t5]  ← t2 dropped

    The oldest turn is always evicted first (FIFO — first in, first out).

JAVA ANALOGY:
    This is an HttpSession wrapper with a fixed-size LinkedList as storage.
    Each session (user) gets its own ConversationMemory instance.
    The orchestrator creates one per user session and passes it around.

DESIGN DECISION — Why not use LangChain's built-in memory?
    LangChain has ConversationBufferWindowMemory. We build our own because:
    1. Easier to understand exactly what goes into the prompt (no magic)
    2. Easier to test (pure Python, no LangChain dependency in this module)
    3. Easier to extend (e.g. add per-engine memory, persist to DB later)
    LangChain memory is shown as an interview answer; our implementation
    gives us more control and transparency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from collections import deque


# ── Data types ───────────────────────────────────────────────────────────────

@dataclass
class Turn:
    """
    One conversation exchange: a user question and the agent's answer.

    Both fields are required. If the agent failed, pass error text as the
    answer so the history still makes sense to the LLM.

    Fields
    ------
    question : str   — the user's original plain-English question
    answer   : str   — the agent's response (or an error message)
    intent   : str | None — the router's classification for this turn
                            (QUERY_SQL / QUERY_DOC / QUERY_BOTH).
                            Stored for debugging; not included in the prompt.
    """
    question: str
    answer: str
    intent: Optional[str] = None


@dataclass
class ConversationMemory:
    """
    Sliding-window conversation memory.

    Stores the last `window_size` turns and provides methods to:
      - add a new turn
      - get history as formatted text (for injecting into prompts)
      - get history as a list of message dicts (for LangChain chat models)
      - clear the memory (start fresh)

    Parameters
    ----------
    window_size : int
        Maximum number of turns to retain. Defaults to 3.
        (3 turns = 6 messages: 3 questions + 3 answers)
    """
    window_size: int = 3

    # deque with maxlen is a Python built-in circular buffer.
    # When you append to a full deque, the oldest item is automatically dropped.
    # This is exactly the "sliding window" behaviour we want.
    # field(default_factory=...) is required because dataclass can't use
    # a mutable default value directly — same issue as Java's "don't initialise
    # a List in a field declaration".
    _turns: deque = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        # Recreate the deque with the correct maxlen now that window_size is set.
        # __post_init__ runs after __init__ (the dataclass-generated constructor).
        # Java equivalent: a @PostConstruct method in a Spring bean.
        self._turns = deque(maxlen=self.window_size)

    # ── Write ────────────────────────────────────────────────────────────────

    def add_turn(self, question: str, answer: str, intent: Optional[str] = None) -> None:
        """
        Add a completed exchange to memory.

        Call this AFTER the agent has produced its answer, not before.
        If the window is full, the oldest turn is automatically dropped.

        Parameters
        ----------
        question : str         — the user's question
        answer   : str         — the agent's answer (or error message)
        intent   : str | None  — optional router classification
        """
        self._turns.append(Turn(question=question, answer=answer, intent=intent))

    def clear(self) -> None:
        """
        Erase all stored turns. Call this to start a new conversation session.
        """
        self._turns.clear()

    # ── Read ─────────────────────────────────────────────────────────────────

    def get_messages(self) -> list[dict]:
        """
        Return history as a list of {"role": ..., "content": ...} dicts.

        This format matches the OpenAI chat messages API and LangChain's
        message format, so it can be passed directly to ChatOpenAI.

        Example output:
            [
                {"role": "human",     "content": "Who is the highest paid engineer?"},
                {"role": "assistant", "content": "David Park, $145,000."},
                {"role": "human",     "content": "What department is he in?"},
                {"role": "assistant", "content": "Engineering."},
            ]
        """
        messages = []
        for turn in self._turns:
            messages.append({"role": "human",     "content": turn.question})
            messages.append({"role": "assistant", "content": turn.answer})
        return messages

    def get_history_as_text(self) -> str:
        """
        Return history as a formatted multi-line string for prompt injection.

        This is what gets inserted into the LLM prompt before the current
        question. Format:

            Human: Who is the highest paid engineer?
            Assistant: David Park, $145,000, Engineering Manager.

            Human: What department is he in?
            Assistant: Engineering.

        Returns an empty string if there are no stored turns yet.
        (First question of a conversation has no history to inject.)
        """
        if not self._turns:
            return ""

        lines = []
        for turn in self._turns:
            lines.append(f"Human: {turn.question}")
            lines.append(f"Assistant: {turn.answer}")
        return "\n".join(lines)

    def get_turns(self) -> list[Turn]:
        """
        Return the raw list of Turn objects (useful for inspection/testing).
        """
        return list(self._turns)

    # ── Introspection ────────────────────────────────────────────────────────

    @property
    def turn_count(self) -> int:
        """How many turns are currently stored."""
        return len(self._turns)

    @property
    def is_empty(self) -> bool:
        """True if no turns have been added yet."""
        return len(self._turns) == 0

    def __repr__(self) -> str:
        return (
            f"ConversationMemory("
            f"window_size={self.window_size}, "
            f"turns={self.turn_count})"
        )
