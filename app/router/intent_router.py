"""
intent_router.py — Query Intent Classifier
============================================
WHAT THIS FILE DOES:
    Reads a user's plain-English question and classifies it into one of
    three categories so the orchestrator knows which engine(s) to call:

        QUERY_SQL   — question is about employees, projects, salaries, dates
                      (data that lives in the SQLite database)

        QUERY_DOC   — question is about HR policies, benefits, code of conduct
                      (data that lives in the ChromaDB document store)

        QUERY_BOTH  — question spans both sources
                      e.g. "Who manages the AI project and what leave do they get?"

WHY A ROUTER?
    Without it, you'd call both engines for every question — doubling cost,
    doubling latency, and getting irrelevant results from the wrong engine.
    The router adds one small upfront LLM call to avoid two expensive ones.

HOW CLASSIFICATION WORKS:
    We give GPT-4o a carefully engineered prompt that describes what each
    category means, provides examples, and instructs the model to reply with
    ONLY the category name. We then parse and validate that output.

    This is called "zero-shot classification" — no training examples in the
    prompt, just a clear description of each class.

JAVA ANALOGY:
    This is a Spring HandlerMapping or a front-controller servlet.
    It inspects the incoming request and returns the name of the handler
    (engine) that should process it. The router itself does no execution.

RETURN VALUE:
    IntentResult — a simple dataclass with:
        intent    (str)  — one of: QUERY_SQL | QUERY_DOC | QUERY_BOTH
        reasoning (str)  — the LLM's explanation for its choice (useful for debugging)
        error     (str|None) — set if classification failed
"""

from __future__ import annotations

# ── Standard library ────────────────────────────────────────────────────────
import traceback
from dataclasses import dataclass
from typing import Optional

# ── LangChain ────────────────────────────────────────────────────────────────
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ── Our modules ──────────────────────────────────────────────────────────────
from app.engines.llm import get_llm


# ── Intent constants ─────────────────────────────────────────────────────────
# Using string constants (not Python Enum) keeps things simple and readable.
# If this grows, an Enum would be cleaner — but for 3 values, constants are fine.

QUERY_SQL  = "QUERY_SQL"   # Question answered from the SQLite database
QUERY_DOC  = "QUERY_DOC"   # Question answered from HR document store
QUERY_BOTH = "QUERY_BOTH"  # Question needs both engines

# All valid intents — used for validation
_VALID_INTENTS = {QUERY_SQL, QUERY_DOC, QUERY_BOTH}

# Fallback when we can't classify — safer to try both engines than to pick wrong
_DEFAULT_INTENT = QUERY_BOTH


# ── Return type ──────────────────────────────────────────────────────────────
# dataclass is Python's version of a simple "value object" or DTO.
# Like a Java record (Java 16+) or a simple POJO with no business logic.
# @dataclass auto-generates __init__, __repr__, __eq__ for us.

@dataclass
class IntentResult:
    """
    The router's output. Tells the orchestrator what to do with the question.

    Fields
    ------
    intent    : str        — QUERY_SQL | QUERY_DOC | QUERY_BOTH
    reasoning : str        — why the LLM chose this intent (for logging/debug)
    error     : str | None — set if the router itself failed; orchestrator
                             should fall back to QUERY_BOTH in this case
    """
    intent: str
    reasoning: str
    error: Optional[str] = None


# ── The classification prompt ─────────────────────────────────────────────────
#
# PROMPT ENGINEERING NOTES (important for interviews):
#
# 1. We describe WHAT each intent means, not just what to return.
#    This grounds the LLM in our specific domain.
#
# 2. We give concrete examples of each category.
#    Even though this is "zero-shot", examples in the description
#    (not in few-shot format) still help the model calibrate.
#
# 3. We explicitly say "reply with ONLY the intent name on the first line".
#    Without this instruction, the LLM might say "I think this is QUERY_SQL
#    because..." — which breaks our simple output parser.
#
# 4. We ask for reasoning on the second line.
#    This serves two purposes:
#      a) Makes the model "think before answering" — improves accuracy
#         (this is called chain-of-thought, even in compact form)
#      b) Gives us a log trail to debug misclassifications

_ROUTER_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are a query router for a company's AI assistant.
Your job is to classify the user's question into exactly one of three categories.

CATEGORY DEFINITIONS:

QUERY_SQL
  The question asks about structured data: employees, projects, salaries,
  departments, roles, hire dates, project budgets, project status, team
  assignments, or any question that can be answered by querying a database.
  Examples:
    - "Who are the highest paid engineers?"
    - "Which projects are currently active?"
    - "How many employees work in the HR department?"
    - "What is Alice's role and salary?"

QUERY_DOC
  The question asks about HR policies, company rules, employee benefits,
  code of conduct, leave policies, health insurance, 401k, or any topic
  covered in HR documents.
  Examples:
    - "How many sick days do I get per year?"
    - "What is the maternity leave policy?"
    - "What does the code of conduct say about conflicts of interest?"
    - "Is home office equipment covered in benefits?"

QUERY_BOTH
  The question requires information from BOTH the database AND the HR documents
  to give a complete answer.
  Examples:
    - "Who manages the AI project and what is their leave entitlement?"
    - "List all engineers and explain what benefits they receive."
    - "How many days off does Alice get based on her hire date and the leave policy?"

INSTRUCTIONS:
  Reply in exactly this format — two lines, nothing else:
  Line 1: One of: QUERY_SQL, QUERY_DOC, or QUERY_BOTH
  Line 2: One sentence explaining why.

User question: {question}""",
)


# ── Internal: parse the raw LLM output ───────────────────────────────────────

def _parse_router_output(raw: str) -> tuple[str, str]:
    """
    Parse the LLM's two-line response into (intent, reasoning).

    Expected format:
        QUERY_SQL
        This question asks about employee salary data from the database.

    Handles messy output gracefully:
        - strips whitespace
        - uppercases the first line
        - falls back to QUERY_BOTH if the intent is not recognised
    """
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]

    if not lines:
        return _DEFAULT_INTENT, "LLM returned empty output"

    # First non-empty line should be the intent
    raw_intent = lines[0].upper()

    # Sometimes the LLM wraps the intent in a sentence like "The intent is QUERY_SQL"
    # so we search for a valid intent anywhere in the first line
    intent = _DEFAULT_INTENT
    for valid in _VALID_INTENTS:
        if valid in raw_intent:
            intent = valid
            break

    # Second line is the reasoning (join remaining lines if multi-line)
    reasoning = " ".join(lines[1:]) if len(lines) > 1 else "No reasoning provided."

    return intent, reasoning


# ── Main public function ──────────────────────────────────────────────────────

def classify_intent(question: str) -> IntentResult:
    """
    Classify the user's question into QUERY_SQL, QUERY_DOC, or QUERY_BOTH.

    Parameters
    ----------
    question : str
        The plain-English question from the user.

    Returns
    -------
    IntentResult
        .intent    — one of QUERY_SQL | QUERY_DOC | QUERY_BOTH
        .reasoning — the LLM's explanation
        .error     — set if the LLM call itself failed
    """
    try:
        # temperature=0 for classification — we want deterministic, consistent output.
        # This is the same reasoning as using temperature=0 for SQL generation.
        llm = get_llm(temperature=0)

        # Build and run the chain: prompt → LLM → plain text output
        chain = _ROUTER_PROMPT | llm | StrOutputParser()
        raw_output = chain.invoke({"question": question})

        intent, reasoning = _parse_router_output(raw_output)

        return IntentResult(intent=intent, reasoning=reasoning)

    except Exception as exc:
        traceback.print_exc()
        # On failure, default to QUERY_BOTH so the orchestrator tries both
        # engines. Safer than picking the wrong one.
        return IntentResult(
            intent=_DEFAULT_INTENT,
            reasoning="Router failed — defaulting to QUERY_BOTH as a safe fallback.",
            error=str(exc),
        )
