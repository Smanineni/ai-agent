"""
orchestrator.py — The Central Coordinator
==========================================
WHAT THIS FILE DOES:
    The orchestrator is the single entry point for every user question.
    It owns the full pipeline from question-in to answer-out:

        1. Enrich question with conversation history (memory)
        2. Classify intent (router) → QUERY_SQL | QUERY_DOC | QUERY_BOTH
        3. Call the appropriate engine(s)
        4. Combine results if both engines were called
        5. Store the exchange in memory for future turns
        6. Return a structured AgentResponse to the caller (UI or tests)

WHY THIS EXISTS AS A SEPARATE FILE:
    Each component (router, engines, memory) knows nothing about the others.
    The orchestrator is the ONLY place they are wired together.
    This keeps every other module independently testable and reusable.

    Single Responsibility Principle at the system level:
      - SQL engine    → converts NL to SQL and runs it. That's all.
      - RAG engine    → retrieves chunks and generates answers. That's all.
      - Router        → classifies intent. That's all.
      - Memory        → stores and retrieves turns. That's all.
      - Orchestrator  → coordinates all of the above. That's all.

JAVA ANALOGY:
    This is the API Gateway / Facade pattern. Think of it as the single
    @RestController endpoint that delegates to multiple @Service beans,
    assembles the result, and returns a unified response DTO.

    In Spring terms:
        @PostMapping("/ask")
        public AgentResponse ask(@RequestBody String question) {
            String enriched   = memory.enrich(question);
            Intent intent     = router.classify(enriched);
            AgentResponse res = dispatch(intent, enriched);
            memory.store(question, res.answer);
            return res;
        }

RETURN VALUE — AgentResponse (dataclass):
    {
        answer       str         the final answer shown to the user
        intent       str         QUERY_SQL | QUERY_DOC | QUERY_BOTH
        sql_used     str|None    the SQL query that was executed (if SQL engine ran)
        sources      list[str]   document filenames used (if RAG engine ran)
        error        str|None    set if something failed
        raw_sql_rows str|None    raw rows from SQL execution (for debugging)
    }
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Optional

from app.router.intent_router import classify_intent, QUERY_SQL, QUERY_DOC, QUERY_BOTH
from app.engines.sql_engine import run_sql_query
from app.engines.rag_engine import run_rag_query
from app.memory.conversation_memory import ConversationMemory


# ── Response type ─────────────────────────────────────────────────────────────
# This is the DTO (Data Transfer Object) returned by the orchestrator.
# The UI reads this to decide what to show.
# Java equivalent: a @ResponseBody POJO or a record class.

@dataclass
class AgentResponse:
    """
    The orchestrator's output for one question.

    Fields
    ------
    answer       : str        — the final answer to display to the user
    intent       : str        — which engine(s) were used
    sql_used     : str | None — the SQL query generated (SQL engine only)
    sources      : list[str]  — source document filenames (RAG engine only)
    error        : str | None — error message if the pipeline failed
    raw_sql_rows : str | None — raw DB result rows before LLM synthesis
    """
    answer: str
    intent: str
    sql_used: Optional[str] = None
    sources: list = field(default_factory=list)
    error: Optional[str] = None
    raw_sql_rows: Optional[str] = None


# ── Helper: enrich question with memory history ───────────────────────────────

def _enrich_question(question: str, memory: ConversationMemory) -> str:
    """
    Prepend conversation history to the question so the LLM has context.

    If memory is empty (first turn), returns the question unchanged.
    No extra tokens, no overhead on the first question.

    Example output when memory has 1 prior turn:
        'Previous conversation:
         Human: Who is the highest paid engineer?
         Assistant: David Park, $145,000.

         Current question: What department is he in?'
    """
    history = memory.get_history_as_text()
    if not history:
        return question

    return (
        f"Previous conversation:\n"
        f"{history}\n\n"
        f"Current question: {question}"
    )


# ── Helper: combine SQL + RAG answers for QUERY_BOTH ─────────────────────────

def _combine_answers(question: str, sql_result: dict, rag_result: dict) -> str:
    """
    Merge answers from both engines into one coherent response.

    We use a simple template approach: list what each engine found.
    A more sophisticated approach would be a third LLM call to synthesise
    a unified paragraph — we keep it simple here and leave that as an
    optional enhancement.
    """
    parts = []

    if sql_result.get("answer"):
        parts.append(f"From the employee database:\n{sql_result['answer']}")

    if rag_result.get("answer"):
        src_list = ", ".join(rag_result.get("sources", []))
        src_note = f" (source: {src_list})" if src_list else ""
        parts.append(f"From HR documents{src_note}:\n{rag_result['answer']}")

    if not parts:
        return "I could not find relevant information to answer your question."

    return "\n\n".join(parts)


# ── Main public function ──────────────────────────────────────────────────────

def ask(question: str, memory: ConversationMemory) -> AgentResponse:
    """
    Process a user question end-to-end and return a structured response.

    This is the single public entry point for the orchestrator.
    The UI calls this function for every message the user sends.

    Parameters
    ----------
    question : str
        The plain-English question from the user.
    memory : ConversationMemory
        The conversation memory for this session.
        The caller owns this object and passes it in.
        This keeps the orchestrator stateless — it doesn't create or store
        the memory object itself, it just uses whatever is passed to it.
        (Dependency Injection pattern — same as Spring @Autowired)

    Returns
    -------
    AgentResponse
        Structured result with answer, intent, sources, and debug fields.
    """
    try:
        # ── STEP 1: Enrich the question with conversation history ─────────────
        # If memory has prior turns, the enriched question includes them.
        # This is what allows the LLM to resolve "he", "that project", "their".
        enriched_question = _enrich_question(question, memory)

        # ── STEP 2: Classify intent ───────────────────────────────────────────
        # The router reads the enriched question (not the bare question) so it
        # can also see prior context when classifying.
        # On LLM failure, router safely returns QUERY_BOTH as a fallback.
        intent_result = classify_intent(enriched_question)
        intent = intent_result.intent

        # ── STEP 3: Dispatch to the right engine(s) ───────────────────────────
        sql_result = None
        rag_result = None

        if intent in (QUERY_SQL, QUERY_BOTH):
            # run_sql_query() returns a dict with: answer, sql, raw_rows, error
            sql_result = run_sql_query(enriched_question)

        if intent in (QUERY_DOC, QUERY_BOTH):
            # run_rag_query() returns a dict with: answer, sources, chunks_used, error
            rag_result = run_rag_query(enriched_question)

        # ── STEP 4: Build the final answer ────────────────────────────────────
        if intent == QUERY_SQL:
            final_answer = sql_result.get("answer") or sql_result.get("error") or "No answer."
            response = AgentResponse(
                answer=final_answer,
                intent=intent,
                sql_used=sql_result.get("sql"),
                raw_sql_rows=sql_result.get("raw_rows"),
                error=sql_result.get("error"),
            )

        elif intent == QUERY_DOC:
            final_answer = rag_result.get("answer") or rag_result.get("error") or "No answer."
            response = AgentResponse(
                answer=final_answer,
                intent=intent,
                sources=rag_result.get("sources", []),
                error=rag_result.get("error"),
            )

        else:  # QUERY_BOTH
            # Combine results from both engines
            final_answer = _combine_answers(enriched_question, sql_result or {}, rag_result or {})

            # Collect any errors from either engine
            errors = []
            if sql_result and sql_result.get("error"):
                errors.append(f"SQL: {sql_result['error']}")
            if rag_result and rag_result.get("error"):
                errors.append(f"RAG: {rag_result['error']}")

            response = AgentResponse(
                answer=final_answer,
                intent=intent,
                sql_used=sql_result.get("sql") if sql_result else None,
                sources=rag_result.get("sources", []) if rag_result else [],
                raw_sql_rows=sql_result.get("raw_rows") if sql_result else None,
                error="; ".join(errors) if errors else None,
            )

        # ── STEP 5: Store this exchange in memory ─────────────────────────────
        # We store the ORIGINAL question (not enriched) because the enriched
        # version already contains prior turns. Storing enriched would cause
        # duplication in the next turn's history.
        # We store the final answer (even if it contains an error message) so
        # the LLM has accurate context about what was said.
        memory.add_turn(
            question=question,
            answer=response.answer,
            intent=intent,
        )

        return response

    except Exception as exc:
        traceback.print_exc()
        error_msg = str(exc)

        # Even on hard failure, store the exchange in memory so the user
        # can see the conversation history. Store the error as the answer.
        try:
            memory.add_turn(
                question=question,
                answer=f"[Error: {error_msg}]",
                intent="ERROR",
            )
        except Exception:
            pass  # If memory itself fails, don't mask the original error

        return AgentResponse(
            answer="Something went wrong. Please try again.",
            intent="ERROR",
            error=error_msg,
        )
