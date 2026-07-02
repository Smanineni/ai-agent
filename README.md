# NexusAI — Enterprise Knowledge & Data Query Platform

A production-grade agentic AI system that answers natural language questions over both structured (SQL) and unstructured (document) enterprise data. Built with LangChain, ChromaDB, SQLite, and Streamlit. Deployable via Docker.

---

## What It Does

Ask questions in plain English. The agent decides whether to query the database, search HR documents, or both — and returns a grounded, human-readable answer.

| Question | Source | Example Answer |
|---|---|---|
| "Who is the highest paid engineer?" | SQL (employees table) | "David Park, Engineering Manager — $145,000" |
| "How many sick days do I get?" | RAG (HR policy docs) | "10 days per year, per Section 2 of the Leave Policy" |
| "Who leads the AI project and what is their leave entitlement?" | Both | Combined SQL + document answer |

---

## Architecture

```
User question
      │
      ▼
┌──────────────┐
│ Streamlit UI │  Chat interface + admin panel
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Orchestrator │  Central coordinator
└──────┬───────┘
       │
  ┌────┴────────────┐
  ▼                 ▼
┌────────┐    ┌──────────────┐
│ Memory │    │    Router    │  Intent: QUERY_SQL | QUERY_DOC | QUERY_BOTH
└────────┘    └──────┬───────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   ┌────────────┐       ┌────────────┐
   │ SQL Engine │       │ RAG Engine │
   │ NL → SQL   │       │ Retrieve + │
   │ → Execute  │       │ Answer     │
   └─────┬──────┘       └─────┬──────┘
         ▼                     ▼
   ┌──────────┐       ┌──────────────┐
   │  SQLite  │       │   ChromaDB   │
   └──────────┘       └──────────────┘
```

**Key design decisions:**
- Router classifies intent before calling any engine — avoids double LLM calls
- Memory injects last 3 conversation turns into every prompt for anaphora resolution
- `_extract_sql()` cleans and validates LLM-generated SQL before execution
- Three-layer SQL security: table allowlist + keyword blocklist + SELECT-only enforcement
- Feedback loop stores thumbs-up/down ratings and golden queries for continuous improvement

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| LLM (paid) | OpenAI GPT-4o | SQL generation, RAG answer synthesis, routing |
| LLM (free) | Groq Llama 3.3-70B | Free-tier alternative — switch via `.env` |
| LLM (local) | Ollama Llama 3 | Fully offline — no API key needed |
| Embeddings | `all-MiniLM-L6-v2` | Local sentence-transformer, free, no API key |
| Orchestration | LangChain 0.2.6 | Chain building, SQL tools, prompt management |
| Vector DB | ChromaDB 0.5.3 | Stores and retrieves embedded document chunks |
| Structured DB | SQLite + SQLAlchemy | Employee/project data — swappable with PostgreSQL |
| UI | Streamlit 1.36.0 | Chat interface + admin panel |
| Reranker | BGE-Reranker | Cross-encoder reranking for RAG precision |
| Containerisation | Docker + Compose | Single-command deployment |

---

## Quick Start

### Option A — Docker (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/hybrid-ai-agent.git
cd hybrid-ai-agent

# 2. Copy the env template and fill in your keys
cp .env.example .env
# Edit .env: set LLM_PROVIDER and the corresponding API key

# 3. Start
docker compose up --build

# 4. Open
# http://localhost:8501
```

### Option B — Local (development)

```powershell
# Windows PowerShell
cd c:\hybrid-ai-agent

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Set up database
python -m app.database.seed

# Ingest documents into ChromaDB
python -m app.vectorstore.store

# Start the app
.\venv\Scripts\streamlit.exe run app/ui/main.py --server.headless true
```

---

## Configuration

Copy `.env.example` to `.env` and set the following:

```ini
# ── LLM Provider (choose one) ─────────────────────────────────────────────────
LLM_PROVIDER=groq           # openai | groq | ollama

# ── OpenAI (paid) ─────────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# ── Groq (free tier) ──────────────────────────────────────────────────────────
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# ── Ollama (local, no API key) ────────────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# ── Embeddings ────────────────────────────────────────────────────────────────
EMBEDDING_MODE=local                     # local | openai
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2

# ── Data ──────────────────────────────────────────────────────────────────────
SQLITE_DB_PATH=data/db/company.db
CHROMA_PERSIST_DIR=data/chroma
CHROMA_COLLECTION_NAME=hr_docs
```

**Getting a free Groq API key:** https://console.groq.com → Sign up → API Keys → Create key (no credit card required)

---

## Project Structure

```
hybrid-ai-agent/
├── app/
│   ├── database/          # SQLite schema, models, seed data
│   ├── vectorstore/       # ChromaDB ingestion and retrieval
│   ├── engines/
│   │   ├── llm.py         # LLM factory (OpenAI / Groq / Ollama)
│   │   ├── sql_engine.py  # NL → SQL → Answer pipeline
│   │   └── rag_engine.py  # Retrieve chunks → Answer pipeline
│   ├── router/            # Intent classification (QUERY_SQL/DOC/BOTH)
│   ├── memory/            # Sliding window conversation memory
│   ├── orchestrator/      # Coordinates all components
│   ├── feedback/          # Ratings, corrections, golden queries
│   └── ui/
│       └── main.py        # Streamlit chat UI + admin panel
├── data/
│   ├── db/                # SQLite database (volume-mounted in Docker)
│   ├── chroma/            # ChromaDB vectors  (volume-mounted in Docker)
│   └── documents/         # HR policy source documents (.txt)
├── tests/                 # Unit tests for all modules
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements.txt
├── .env.example
└── LEARNING_GUIDE.md      # Detailed step-by-step build guide + interview prep
```

---

## Sample Questions to Try

```
# SQL queries (hits the employee database)
"Who is the highest paid engineer?"
"List all employees in the Engineering department"
"Which projects have more than 3 team members?"
"Who reports to David Park?"

# Document queries (searches HR policy docs)
"How many sick days do I get per year?"
"What is the parental leave policy?"
"What expenses can I claim?"
"How do I raise a code of conduct complaint?"

# Combined queries (hits both)
"Who leads the AI Transformation project, and what leave are they entitled to?"
"Who is the most senior engineer and what is the annual leave carryover policy?"

# Follow-up questions (tests memory / anaphora resolution)
"Who is the highest paid engineer?"  →  then  →  "What projects is he on?"
```

---

## Running Tests

```powershell
# All tests
python -m pytest tests/ -v

# Individual modules
python -m tests.test_sql_engine
python -m tests.test_rag_engine
python -m tests.test_router
python -m tests.test_memory
python -m tests.test_orchestrator
python -m tests.test_feedback
```

---

## Docker Commands

```bash
# Start (first run builds the image)
docker compose up --build

# Start in background
docker compose up -d

# View live logs
docker compose logs -f app

# Stop
docker compose down

# Rebuild after code changes (pip cache is retained)
docker compose up --build

# Check memory usage
docker stats hybrid-ai-agent
```

---

## Data Persistence

The SQLite database and ChromaDB vectors are stored on the **host machine** and mounted into the container as volumes:

```yaml
volumes:
  - ./data/db:/app/data/db        # SQLite — survives docker compose down
  - ./data/chroma:/app/data/chroma # ChromaDB — survives docker compose down
```

Running `docker compose down` stops the container but **does not delete your data**. Only `docker compose down -v` removes named volumes.

---

## Security Notes

- `.env` is excluded from the Docker image via `.dockerignore` — API keys are never baked in
- LLM-generated SQL is validated through three layers before execution (allowlist → blocklist → SELECT-only)
- Each user session has isolated conversation memory — no cross-user data leakage
- For production: replace `env_file` with AWS Secrets Manager or HashiCorp Vault

---

## Built By

**Srinivasulu Manineni** — Tech Lead / Solution Architect transitioning to Agentic AI Engineering.  
15 years of Java / Spring / Kafka / Angular / NICE Actimize. Now building AI systems that sit on top of enterprise data.

- GitHub: [github.com/srinivasulu-mani](https://github.com/srinivasulu-manineni)
- LinkedIn: [linkedin.com/in/smanineni](https://linkedin.com/in/smanineni)

---

*Last updated: 2026-07-02*
