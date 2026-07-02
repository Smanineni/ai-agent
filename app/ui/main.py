import sys
import os
import uuid

# Add project root to sys.path so `import app.*` works when Streamlit
# launches this file directly (Streamlit adds app/ui/ to sys.path, not root).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

# set_page_config MUST be the very first Streamlit command.
# It is placed here — before the docstring and all other imports — because
# Streamlit's "magic" mode treats bare string literals as st.write() calls,
# which would count as a Streamlit command and cause set_page_config to fail.
st.set_page_config(
    page_title="Hybrid AI Agent",
    page_icon="🤖",
    layout="wide",
)

# ── Remaining imports (safe after set_page_config) ───────────────────────────
from app.orchestrator.orchestrator import ask, AgentResponse
from app.memory.conversation_memory import ConversationMemory
from app.feedback.feedback_store import (
    store_feedback,
    add_correction,
    get_thumbs_down,
    get_golden_queries,
    get_stats,
    THUMBS_UP,
    THUMBS_DOWN,
)

# ── Session state initialisation ──────────────────────────────────────────────
# st.session_state persists across re-runs for the same browser session.
# We initialise each key only once (on first load).

if "memory" not in st.session_state:
    # One ConversationMemory per user session — keeps the last 3 turns
    st.session_state.memory = ConversationMemory(window_size=3)

if "chat_history" not in st.session_state:
    # List of dicts: {"role": "user"|"agent", "content": str,
    #                 "response": AgentResponse|None, "feedback_id": int|None}
    st.session_state.chat_history = []

if "session_id" not in st.session_state:
    # Unique session ID so we can group feedback from one conversation
    st.session_state.session_id = str(uuid.uuid4())[:8]

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chat, tab_admin = st.tabs(["💬 Chat", "⚙️ Admin"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.title("🤖 Hybrid AI Agent")
    st.caption(
        "Ask questions about employees, projects, HR policies, or both. "
        "The agent figures out where to look."
    )

    # ── Render existing chat history ──────────────────────────────────────────
    for i, entry in enumerate(st.session_state.chat_history):

        if entry["role"] == "user":
            with st.chat_message("user"):
                st.markdown(entry["content"])

        else:  # agent turn
            with st.chat_message("assistant"):
                st.markdown(entry["content"])

                resp: AgentResponse = entry.get("response")
                if resp:
                    # Show metadata in an expander so the main answer stays clean
                    with st.expander("Details", expanded=False):
                        st.write(f"**Intent:** `{resp.intent}`")

                        if resp.sql_used:
                            st.code(resp.sql_used, language="sql")

                        if resp.sources:
                            st.write("**Sources:** " + ", ".join(resp.sources))

                        if resp.error:
                            st.warning(f"Note: {resp.error}")

                # Feedback buttons — only shown if no rating given yet
                feedback_id = entry.get("feedback_id")
                already_rated = entry.get("rated", False)

                if not already_rated and resp:
                    col_up, col_down, col_spacer = st.columns([1, 1, 8])

                    with col_up:
                        if st.button("👍", key=f"up_{i}"):
                            fid = store_feedback(
                                question=st.session_state.chat_history[i - 1]["content"],
                                answer=resp.answer,
                                intent=resp.intent,
                                rating=THUMBS_UP,
                                session_id=st.session_state.session_id,
                            )
                            st.session_state.chat_history[i]["feedback_id"] = fid
                            st.session_state.chat_history[i]["rated"] = True
                            st.rerun()

                    with col_down:
                        if st.button("👎", key=f"down_{i}"):
                            fid = store_feedback(
                                question=st.session_state.chat_history[i - 1]["content"],
                                answer=resp.answer,
                                intent=resp.intent,
                                rating=THUMBS_DOWN,
                                session_id=st.session_state.session_id,
                            )
                            st.session_state.chat_history[i]["feedback_id"] = fid
                            st.session_state.chat_history[i]["rated"] = True
                            st.rerun()

                elif already_rated:
                    st.caption("✓ Feedback recorded")

    # ── Chat input ────────────────────────────────────────────────────────────
    # st.chat_input renders a fixed input bar at the bottom of the page.
    # It returns the submitted text (or None if nothing submitted).
    if question := st.chat_input("Ask about employees, projects, or HR policies..."):

        # 1. Immediately show the user's message
        st.session_state.chat_history.append({
            "role": "user",
            "content": question,
            "response": None,
            "feedback_id": None,
            "rated": False,
        })

        # 2. Call the orchestrator — the heart of the whole system
        with st.spinner("Thinking..."):
            response = ask(question, st.session_state.memory)

        # 3. Store the agent's response
        st.session_state.chat_history.append({
            "role": "agent",
            "content": response.answer,
            "response": response,
            "feedback_id": None,
            "rated": False,
        })

        # 4. Re-run to render the new messages
        st.rerun()

    # ── Sidebar controls ──────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Session")
        st.caption(f"Session ID: `{st.session_state.session_id}`")
        st.caption(f"Memory: {st.session_state.memory.turn_count} / "
                   f"{st.session_state.memory.window_size} turns")

        if st.button("🗑️ Clear conversation"):
            st.session_state.chat_history = []
            st.session_state.memory.clear()
            st.rerun()

        st.divider()
        st.caption("**How it works:**")
        st.caption("1. Router classifies your question")
        st.caption("2. SQL engine queries the employee DB")
        st.caption("3. RAG engine searches HR documents")
        st.caption("4. Memory keeps the last 3 turns")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
with tab_admin:
    st.title("⚙️ Admin Panel")

    # ── Stats row ─────────────────────────────────────────────────────────────
    st.subheader("Feedback Stats")
    stats = get_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Ratings",  stats["total"])
    col2.metric("👍 Thumbs Up",   stats["thumbs_up"])
    col3.metric("👎 Thumbs Down", stats["thumbs_down"])
    col4.metric("Corrected",      stats["corrected"])
    col5.metric("Approval %",     f"{stats['approval_pct']}%")

    st.divider()

    # ── Thumbs-down review ────────────────────────────────────────────────────
    st.subheader("Thumbs-down Review")
    st.caption(
        "These are answers users rated negatively. "
        "Write a correction to turn them into golden queries."
    )

    downs = get_thumbs_down(limit=20)

    if not downs:
        st.info("No thumbs-down feedback yet.")
    else:
        for row in downs:
            with st.expander(
                f"[{row['intent']}] {row['question'][:80]}...",
                expanded=False
            ):
                st.write("**Question:**", row["question"])
                st.write("**Agent answer:**", row["answer"])
                st.write("**Intent:**", row["intent"])
                st.caption(f"Timestamp: {row['timestamp']}")

                if row["correction"]:
                    st.success(f"Correction already added: {row['correction']}")
                else:
                    correction_text = st.text_area(
                        "Write the correct answer:",
                        key=f"correction_{row['id']}",
                        height=80,
                    )
                    if st.button("Save correction", key=f"save_{row['id']}"):
                        if correction_text.strip():
                            success = add_correction(row["id"], correction_text.strip())
                            if success:
                                st.success("Correction saved as a golden query.")
                                st.rerun()
                        else:
                            st.warning("Please write a correction before saving.")

    st.divider()

    # ── Golden queries ────────────────────────────────────────────────────────
    st.subheader("Golden Queries")
    st.caption(
        "Verified question/answer pairs. "
        "Use these for regression testing and few-shot prompting."
    )

    golden = get_golden_queries()

    if not golden:
        st.info("No golden queries yet. Add corrections above to create them.")
    else:
        for g in golden:
            with st.expander(f"[{g['intent']}] {g['question'][:80]}..."):
                st.write("**Question:**", g["question"])
                st.write("**Original (wrong) answer:**", g["answer"])
                st.success(f"**Correct answer:** {g['correction']}")
                st.caption(f"Collected: {g['timestamp']}")
