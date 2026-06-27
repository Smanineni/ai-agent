# Hybrid AI Agent — Complete Learning Guide

> This README is your personal reference document.
> Every file, every concept, every line — explained step by step.
> Revisit this whenever you feel lost.

---

> **About this guide:** Written for Srinivasulu Manineni (Srini) — 15 years Java/Spring/Kafka
> Tech Lead transitioning to Agentic AI Engineering. Every concept is explained with Java
> analogies where possible. Interview questions are embedded throughout each section.

---

## Table of Contents

1. [What Are We Building?](#1-what-are-we-building)
2. [System Architecture](#2-system-architecture)
3. [Project Folder Structure](#3-project-folder-structure)
4. [How to Start the Project (Every Time)](#4-how-to-start-the-project-every-time)
5. [Step 1 — Project Setup](#5-step-1--project-setup)
6. [Step 2 — SQLite Database](#6-step-2--sqlite-database)
7. [Step 3 — Vector Store (ChromaDB)](#7-step-3--vector-store-chromadb)
8. [Step 4 — NL-to-SQL Engine](#8-step-4--nl-to-sql-engine)
9. [How to Run Tests](#9-how-to-run-tests)
10. [Known Issues & Fixes](#10-known-issues--fixes)
11. [Learning Resources](#11-learning-resources)

---

## 1. What Are We Building?

A **Hybrid AI Agent** — a system that can answer natural language questions
over TWO types of data simultaneously:

| Data Type | Example Question | How Answered |
|-----------|-----------------|--------------|
| **Structured** (SQL database) | "Who are the highest paid engineers?" | LLM writes SQL → runs against SQLite |
| **Unstructured** (documents) | "How many sick days do I get?" | Finds relevant text chunks → LLM reads and answers |
| **Both combined** | "Who manages the AI project, and what is their leave policy?" | Routes to both engines, combines answers |

**In plain English:** You type a question. The system figures out whether to
search the database, search documents, or both — and gives you a plain
English answer.

---

## 2. System Architecture

```
You type a question
        │
        ▼
┌───────────────────┐
│   Streamlit UI    │  ← Step 10: The chat window you see in the browser
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   Orchestrator    │  ← Step 8: The "brain" — coordinates all other parts
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Memory │ │ Router │  ← Steps 7 & 6
│        │ │        │
│ Keeps  │ │ Decides│
│ last 5 │ │ SQL vs │
│ turns  │ │ RAG vs │
└────────┘ │ Both   │
           └───┬────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌────────────┐   ┌────────────┐
│ SQL Engine │   │ RAG Engine │  ← Steps 4 & 5
│            │   │            │
│ Question   │   │ Question   │
│ → SQL      │   │ → Retrieve │
│ → Execute  │   │ → Answer   │
└─────┬──────┘   └─────┬──────┘
      │                │
      ▼                ▼
┌──────────┐    ┌──────────────┐
│  SQLite  │    │   ChromaDB   │  ← Steps 2 & 3
│ Database │    │ Vector Store │
└──────────┘    └──────────────┘
```

**Reading this diagram:**
- Each box is a Python module (a .py file)
- The arrows show data flow (where information moves)
- We build from the bottom up: database first, then engines, then router, then UI

---

## 3. Project Folder Structure

```
hybrid-ai-agent/
│
├── app/                        ← All application code lives here
│   ├── __init__.py             ← Marks 'app' as a Python package
│   │
│   ├── database/               ← Step 2: SQLite database layer
│   │   ├── __init__.py
│   │   ├── connection.py       ← Database engine + session factory
│   │   ├── models.py           ← Table definitions (Employee, Project)
│   │   └── seed.py             ← Creates tables + inserts fake data
│   │
│   ├── vectorstore/            ← Step 3: ChromaDB vector store layer
│   │   ├── __init__.py
│   │   ├── embedder.py         ← Embedding model (local or OpenAI)
│   │   └── store.py            ← ChromaDB: ingest docs, retrieve chunks
│   │
│   ├── engines/                ← Steps 4 & 5: The query engines
│   │   ├── __init__.py
│   │   ├── llm.py              ← GPT-4o chat model factory
│   │   ├── sql_engine.py       ← NL → SQL → Answer pipeline
│   │   └── rag_engine.py       ← (Step 5: coming soon)
│   │
│   ├── router/                 ← Step 6: Intent detection
│   │   └── __init__.py
│   │
│   ├── memory/                 ← Step 7: Conversation memory
│   │   └── __init__.py
│   │
│   ├── orchestrator/           ← Step 8: Ties everything together
│   │   └── __init__.py
│   │
│   ├── feedback/               ← Step 9: Thumbs up/down feedback
│   │   └── __init__.py
│   │
│   └── ui/                     ← Step 10: Streamlit chat interface
│       └── __init__.py
│
├── data/
│   ├── db/
│   │   └── company.db          ← The SQLite database file (auto-created)
│   ├── documents/              ← HR policy text files
│   │   ├── hr_leave_policy.txt
│   │   ├── hr_code_of_conduct.txt
│   │   └── hr_benefits_guide.txt
│   └── chroma/                 ← ChromaDB vector data (auto-created)
│
├── config/                     ← (Reserved for future config files)
│
├── tests/                      ← Test files — verify each module works
│   └── test_sql_engine.py
│
├── venv/                       ← Virtual environment (DO NOT edit manually)
├── requirements.txt            ← Package list
├── .env                        ← Your real secrets (NOT committed to Git)
├── .env.example                ← Safe template showing what keys are needed
├── .gitignore                  ← Tells Git what files to ignore
└── README.md                   ← This file
```

**Key Rule to Remember:**
Every folder inside `app/` has an `__init__.py` file. Without it, Python
cannot import code from that folder. It's like a "registration card" that
says "this folder is a Python package."

---

## 4. How to Start the Project (Every Time)

Every time you open VS Code and want to work on this project:

```powershell
# Step 1: Open a terminal in VS Code (Ctrl + `)
# Step 2: Navigate to the project folder
cd c:\hybrid-ai-agent

# Step 3: Activate the virtual environment
.\venv\Scripts\activate

# You will see (venv) appear at the start of your prompt:
# (venv) PS C:\hybrid-ai-agent>
# This means you're now using the project's isolated Python environment
```

**Why activate the venv?**
Without activating, `python` points to your system Python which doesn't have
langchain, chromadb, etc. installed. With activation, `python` points to the
project's private Python that has all packages.

---

## 5. Step 1 — Project Setup

### What was created and why

#### `requirements.txt`

```
# This file lists every Python package the project needs.
# Think of it as a shopping list for pip.

openai==1.35.3        # For calling GPT-4o and the embeddings API
langchain==0.2.6      # The main AI orchestration framework
chromadb==0.5.3       # The vector database (stores document embeddings)
sqlalchemy==2.0.31    # The SQL toolkit (Python ↔ database bridge)
streamlit==1.36.0     # The web UI framework
python-dotenv==1.0.1  # Reads our .env file into Python
...
```

**How to install:** `pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org`
(The `--trusted-host` flags are needed because of the corporate SSL proxy)

**Why pin exact versions (==)?**
`langchain==0.2.6` means "exactly version 0.2.6".
If we wrote `langchain>=0.2.6`, pip might install 0.3.0 which has different
behaviour and could break our code. Pinning ensures the code always behaves
the same way.

---

#### `.env` and `.env.example`

```bash
# .env — your REAL file, never committed to Git
OPENAI_API_KEY=sk-proj-abc123...    # Real key — treat like a password

# .env.example — safe template, committed to Git
OPENAI_API_KEY=sk-...               # Placeholder — shows what key is needed
```

**Why two files?**
- If you commit `.env`, your API key is publicly visible on GitHub
- A bad actor could steal it and run up thousands of dollars in charges
- `.env.example` shows teammates what variables are needed without exposing values

**How Python reads .env:**
```python
from dotenv import load_dotenv
import os

load_dotenv()                         # Reads .env file into memory
api_key = os.getenv("OPENAI_API_KEY") # Gets the value by name
```

---

#### `__init__.py` files

These are mostly empty files. Their only job is to mark a folder as a
Python "package" so you can import from it.

**Without `__init__.py`:**
```python
from app.database.connection import engine  # ❌ ImportError
```

**With `__init__.py` in app/ and app/database/:**
```python
from app.database.connection import engine  # ✅ Works
```

---

#### `.gitignore`

```
.env            # Contains your real API key — never commit this
venv/           # 400MB of packages — teammates regenerate from requirements.txt
__pycache__/    # Python bytecode — auto-generated, not source code
data/db/*.db    # Database files — runtime data, not code
data/chroma/    # Vector database files — regenerated from documents
```

---

## 6. Step 2 — SQLite Database

### What is SQLite?

SQLite is a database that lives in a single file (`company.db`).
Unlike PostgreSQL or MySQL, it needs no server to run.
Perfect for learning and small projects.

```
company.db file contains:
├── employees table    (10 rows)
├── projects table     (5 rows)
└── employee_projects  (11 rows — who works on which project)
```

### File: `app/database/connection.py`

```python
# LINE BY LINE EXPLANATION

import os
from pathlib import Path
# os — for reading environment variables (like SQLITE_DB_PATH from .env)
# pathlib.Path — modern way to work with file paths in Python

from dotenv import load_dotenv
# load_dotenv() reads the .env file and puts everything into os.environ

from sqlalchemy import create_engine
# create_engine() creates the connection to the database
# It's like creating a "phone line" to call the database

from sqlalchemy.orm import sessionmaker, DeclarativeBase
# sessionmaker — factory for creating Session objects
# DeclarativeBase — parent class that all our table definitions inherit from

load_dotenv()
# Reads .env file NOW, so all os.getenv() calls below can find the values

_DB_PATH = Path(
    os.getenv("SQLITE_DB_PATH", "data/db/company.db")
).resolve()
# os.getenv("SQLITE_DB_PATH", "data/db/company.db"):
#   Try to read SQLITE_DB_PATH from .env
#   If it's not there, use "data/db/company.db" as the default
# Path(...).resolve():
#   Converts "data/db/company.db" → "C:\hybrid-ai-agent\data\db\company.db"
#   Always use absolute paths — avoids confusion about which folder we're in

_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
# _DB_PATH.parent = the folder containing the .db file = "data/db/"
# .mkdir(parents=True, exist_ok=True):
#   parents=True  → create "data/" AND "data/db/" if they don't exist
#   exist_ok=True → don't crash if the folder already exists

engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
# create_engine():
#   "sqlite:///C:\hybrid-ai-agent\data\db\company.db"
#   This is the "connection string" — tells SQLAlchemy WHERE the database is
#   and WHAT type it is (sqlite, postgresql, mysql, etc.)
#
# check_same_thread=False:
#   SQLite normally complains if two threads use the same connection.
#   Streamlit uses multiple threads, so we need to allow it.
#
# echo=False:
#   If True, prints every SQL query SQLAlchemy runs (helpful for debugging).
#   We set False to keep the terminal clean.

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
# sessionmaker creates a "Session factory" — a blueprint for creating Sessions.
# A Session is a temporary workspace for database operations.
#
# autocommit=False:
#   Changes are NOT saved to the database until you call session.commit()
#   This lets you make multiple changes and save them all at once (atomically)
#   OR roll them all back if something goes wrong.
#
# autoflush=False:
#   Don't automatically send changes to the DB before every query.
#   We control exactly when things are saved.

class Base(DeclarativeBase):
    pass
# All our table classes (Employee, Project, etc.) will inherit from Base.
# SQLAlchemy uses Base to track all table definitions.
# When we call Base.metadata.create_all(engine), it creates ALL tables
# that inherit from Base — in one shot.

def get_session():
    session = SessionLocal()  # Opens a new session (connection to DB)
    try:
        yield session         # Hands the session to the caller
        session.commit()      # If no error occurred, SAVE all changes
    except Exception:
        session.rollback()    # If something went wrong, UNDO all changes
        raise                 # Re-raise so the caller knows what happened
    finally:
        session.close()       # ALWAYS close the session (release resources)
# get_session() is a generator function (notice 'yield' instead of 'return')
# 'yield' pauses the function and hands control to the caller.
# When the caller is done, execution resumes at the line after yield.
#
# Usage:
#   with get_session() as session:
#       employees = session.query(Employee).all()
#   # session is automatically closed here
```

---

### File: `app/database/models.py`

```python
# LINE BY LINE EXPLANATION

from sqlalchemy import String, Integer, Float, Date, ForeignKey, Text
# These are column type definitions:
#   String(100) → text, max 100 characters (VARCHAR in SQL)
#   Integer     → whole numbers (1, 2, 3...)
#   Float       → decimal numbers (115000.50)
#   Date        → a calendar date (2024-01-15)
#   Text        → unlimited length text (for descriptions)
#   ForeignKey  → a reference to another table's column

from sqlalchemy.orm import Mapped, mapped_column, relationship
# Mapped[int] → tells Python (and type checkers) this attribute is an int
# mapped_column() → defines a database column with its properties
# relationship() → creates a Python-level link between two tables
#                  (NOT a real database column — just Python convenience)

class Employee(Base):
    __tablename__ = "employees"   # The actual SQL table name
    #
    # Each attribute below = one column in the employees table
    #
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # primary_key=True  → this column uniquely identifies each row
    # autoincrement=True → SQLite assigns 1, 2, 3... automatically
    # You never need to set id yourself — the database does it.
    #
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # nullable=False → this column CANNOT be empty (required field)
    # Mapped[str] → Python type hint, tells you this will be a string
    #
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    # Mapped[float] → will be a decimal number in Python
    #
    manager_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Optional[str] → this can be None (NULL in the database)
    # nullable=True → the database allows this column to be empty
    # Used for top-level managers who have no manager above them.
    #
    assignments: Mapped[List["EmployeeProject"]] = relationship(...)
    # This is NOT a column. It's a Python-only "shortcut".
    # After loading an Employee, you can do:
    #   alice.assignments  → returns a list of her project assignments
    # Without this, you'd have to write a separate query every time.
```

---

### File: `app/database/seed.py`

```python
# LINE BY LINE EXPLANATION (key parts)

from loguru import logger
# loguru is a better version of Python's built-in 'logging' module.
# Instead of print("Creating tables..."), we write:
#   logger.info("Creating tables...")     → shows timestamps
#   logger.success("Done!")              → green coloured output
#   logger.error("Something failed")     → red coloured output
# This makes it much easier to see what's happening and when.

Base.metadata.create_all(bind=engine)
# Base.metadata — a registry of ALL classes that inherit from Base
# .create_all(engine) — generates CREATE TABLE SQL for each class
#                       and runs them against the database.
# This is idempotent — running it twice doesn't cause an error.
# If a table already exists, SQLAlchemy skips it.

emp = Employee(**data)
# **data "unpacks" the dictionary as keyword arguments.
# This is equivalent to:
#   emp = Employee(name="Alice", email="alice@...", department="Engineering", ...)
# Python's **kwargs syntax lets you pass a dict as named arguments.

session.add(emp)
# Stages the Employee object for insertion.
# Nothing is written to the database yet — it's queued in memory.

session.flush()
# Sends the queued INSERT statements to the database.
# BUT does NOT commit (finalize) them yet.
# Why flush before commit? Because flush assigns auto-increment IDs.
# We need emp.id to be set BEFORE we create EmployeeProject rows
# that reference employees.id.

session.commit()
# Finalizes all changes — makes them permanent in the database.
# Before commit: changes exist in memory only (can be rolled back)
# After commit: changes are permanently saved to company.db

session.rollback()
# Undoes ALL changes since the last commit.
# Called when something goes wrong, to leave the database in a clean state.
```

**How to run seed.py:**
```powershell
# From the project root with venv activated:
python -m app.database.seed

# The -m flag means "run as a module" — it adds the project root to Python's
# path, so 'from app.database.connection import engine' works correctly.
# If you ran 'python app/database/seed.py' directly, Python wouldn't know
# where to find the 'app' package and would give an ImportError.
```

---

## 7. Step 3 — Vector Store (ChromaDB)

### What is a Vector / Embedding?

Every word or sentence can be converted to a list of numbers by an
"embedding model". These numbers encode the *meaning* of the text.

```
"sick leave"           → [0.12, -0.45, 0.78, ...]   (384 numbers)
"annual leave policy"  → [0.11, -0.44, 0.80, ...]   ← similar numbers!
"quarterly earnings"   → [-0.82, 0.23, -0.15, ...] ← very different numbers
```

Similar meaning → similar numbers → close together in "vector space".
This is how the AI finds relevant documents WITHOUT keyword matching.

### What is Chunking?

A 5,000-word HR policy document is too long to embed as one piece.
We split it into overlapping 800-character chunks:

```
Full document:
"LEAVE POLICY ... 1. ANNUAL LEAVE ... 2. SICK LEAVE ... 3. MATERNITY..."

After chunking (chunk_size=800, overlap=100):
Chunk 1: "LEAVE POLICY ... 1. ANNUAL LEAVE ... All employees are entitled to 20 days..."
Chunk 2: "...20 days of paid annual leave. Carryover Policy: max 5 days..."  ← overlaps
Chunk 3: "...5 days. 2. SICK LEAVE ... All employees are entitled to 10 days..."
```

The 100-character overlap ensures we never split a sentence in two pieces
and lose the context.

### File: `app/vectorstore/embedder.py`

```python
# The key design decision here is the "factory pattern":

def get_embedding_model():
    mode = os.getenv("EMBEDDING_MODE", "local").lower()
    if mode == "local":
        return _get_local_embedding_model()   # Free, offline
    else:
        return _get_openai_embedding_model()  # Paid, higher quality

# WHY a factory function instead of just writing:
#   from langchain_community.embeddings import HuggingFaceEmbeddings
#   model = HuggingFaceEmbeddings(...)
# everywhere?
#
# Because if you later want to switch from local to OpenAI, you'd have
# to find and change EVERY file that uses embeddings. With the factory,
# you change ONE function and everything else stays the same.
# This is called "Dependency Inversion" — a key software design principle.
```

**EMBEDDING_MODE in .env:**
```
EMBEDDING_MODE=local    # Uses all-MiniLM-L6-v2 (free, already downloaded)
EMBEDDING_MODE=openai   # Uses text-embedding-3-small (costs ~$0.001 per run)
```

### File: `app/vectorstore/store.py`

```python
# KEY FUNCTION: ingest_documents()
# This is the pipeline that converts your text files into searchable vectors.

documents = load_documents(docs_dir)
# Reads each .txt file from data/documents/
# Creates a LangChain Document object for each:
#   Document(
#     page_content = "LEAVE POLICY\n\n1. ANNUAL LEAVE...",  ← the text
#     metadata = {"source": "hr_leave_policy.txt"}          ← where it came from
#   )
# The metadata is important — it tells us WHICH document a chunk came from.

chunks = chunk_documents(documents)
# Splits each Document into smaller pieces using RecursiveCharacterTextSplitter.
# "Recursive" means it tries different split points in order:
#   1. Try to split at paragraph breaks (\n\n) first
#   2. If still too long, split at line breaks (\n)
#   3. If still too long, split at sentence ends (". ")
#   4. If still too long, split at spaces ( )
#   5. Last resort: split at any character
# This keeps chunks at natural language boundaries.

vectorstore.add_documents(chunks)
# For each chunk:
#   1. Calls the embedding model: text → [0.12, -0.45, 0.78, ...]
#   2. Stores the vector + original text + metadata in ChromaDB
#   3. Saves everything to disk in data/chroma/
# After this, ChromaDB can find relevant chunks for any query.

# KEY FUNCTION: retrieve(query, k=5)
results = vectorstore.similarity_search(query, k=k)
# query → converted to a vector using the same embedding model
# Compares query vector to ALL stored chunk vectors
# Returns the k=5 most similar chunks
# "Similar" = closest in vector space = closest in meaning
```

**How to run ingestion:**
```powershell
python -m app.vectorstore.store
# Only needs to run ONCE (or when you add new documents).
# On second run, it detects existing chunks and skips re-embedding.
# Use force=True to re-embed everything:
#   python -c "from app.vectorstore.store import ingest_documents; ingest_documents(force=True)"
```

---

## 8. Step 4 — NL-to-SQL Engine

### How the Pipeline Works

```
User: "Who are the highest paid engineers?"
  │
  ▼  Step 1: Show LLM our schema
  "Table employees: id, name, department, role, salary, hire_date..."
  "Sample rows: Alice Sharma | Engineering | 115000..."
  │
  ▼  Step 2: LLM generates SQL
  SELECT name, salary
  FROM employees
  WHERE department = 'Engineering'
  ORDER BY salary DESC
  │
  ▼  Step 3: Safety check
  Does it contain DELETE/UPDATE/DROP? → No → proceed
  Does it start with SELECT? → Yes → proceed
  │
  ▼  Step 4: Execute SQL against SQLite
  [("David Park", 145000), ("Alice Sharma", 115000), ...]
  │
  ▼  Step 5: LLM reads results, writes human answer
  "The highest paid engineer is David Park (Engineering Manager)
   with a salary of $145,000, followed by Alice Sharma at $115,000."
```

### File: `app/engines/llm.py`

```python
def get_llm(temperature: float = 0) -> ChatOpenAI:
    # temperature controls how "creative" the LLM is:
    #   temperature=0   → always picks the most probable next word
    #                     → deterministic, consistent, correct
    #                     → best for: SQL generation (we want exact SQL)
    #   temperature=0.3 → slightly varied
    #                     → best for: answer synthesis (sounds more natural)
    #   temperature=0.7 → creative, varied responses
    #                     → best for: brainstorming, creative writing
    #   temperature=1.0 → very random, unpredictable
    #                     → rarely useful in production

    return ChatOpenAI(
        model=model_name,        # "gpt-4o" (from .env)
        temperature=temperature,
        max_tokens=1024,         # Safety cap — LLM can't return more than
                                 # 1024 tokens (~750 words) per call.
                                 # Prevents runaway API costs.
        ...
    )
```

### File: `app/engines/sql_engine.py`

```python
# KEY CONCEPT: LangChain "pipe" syntax
answer_chain = _ANSWER_PROMPT | get_llm(temperature=0.3) | StrOutputParser()

# The | symbol (pipe) connects steps into a chain.
# Data flows left to right:
#   _ANSWER_PROMPT    → fills in {question}, {sql}, {results} placeholders
#                        → produces a complete prompt string
#   get_llm(...)      → sends prompt to GPT-4o
#                        → returns an AIMessage object
#   StrOutputParser() → extracts just the text from the AIMessage
#                        → returns a plain Python string

answer = answer_chain.invoke({
    "question": question,
    "sql": clean_sql,
    "results": raw_rows,
})
# .invoke() runs the entire chain with the given inputs.
# It's equivalent to:
#   prompt = _ANSWER_PROMPT.format(question=..., sql=..., results=...)
#   message = get_llm().invoke(prompt)
#   answer = StrOutputParser().parse(message)
# But the chain syntax is cleaner and more composable.
```

---

## 9. How to Run Tests

### What is a test file?

A test file verifies that your code works correctly.
Instead of manually checking output every time you make a change,
you write a test once — and run it whenever you want to confirm
nothing is broken.

### File: `tests/test_sql_engine.py` — Line by Line

```python
"""Quick test script for the SQL engine — run with: python -m tests.test_sql_engine"""

from app.engines.sql_engine import get_sql_database, validate_sql
# Import the two functions we want to test from sql_engine.py.
# We're testing without the LLM so this works even without API credits.

db = get_sql_database()
# Creates a LangChain SQLDatabase connection to our SQLite file.
# This also reads the schema (table names, columns, sample rows).

print("=== MANUAL SQL EXECUTION ===")

queries = [
    ("Highest paid engineers",
     "SELECT name, salary FROM employees WHERE department='Engineering' ORDER BY salary DESC"),
    ...
]
# A list of (label, sql) tuples.
# Each tuple = one test case.
# We manually wrote the SQL that the LLM *should* generate.
# This lets us verify the database works before adding the LLM.

for label, sql in queries:
    print(f"\nQ: {label}")       # Print the test name
    print(f"SQL: {sql}")         # Print the SQL being tested
    print(f"Result: {db.run(sql)}") # Execute SQL and print the raw result
# db.run(sql) sends the SQL to SQLite and returns results as a string.
# e.g. "[('David Park', 145000.0), ('Alice Sharma', 115000.0)]"

print("\n\n=== SAFETY VALIDATOR ===")

bad = ["DELETE FROM employees", "DROP TABLE projects", "UPDATE employees SET salary=0"]
for q in bad:
    try:
        validate_sql(q)             # This SHOULD raise an error
        print(f"  MISSED: {q}")     # If it didn't, our validator has a bug
    except ValueError:
        print(f"  BLOCKED correctly: {q}")  # This is what we want to see
# The try/except pattern:
#   try:     → attempt to run validate_sql(q)
#   except ValueError:  → if validate_sql() raises a ValueError, catch it here
# If validate_sql() DOESN'T raise an error for a dangerous query,
# it means our security check failed, and we print "MISSED".

print("\nAll tests passed!")
```

### How to run ALL tests:

```powershell
# Run a specific test file:
python -m tests.test_sql_engine

# Why -m and not just python tests/test_sql_engine.py ?
# The -m flag adds the current directory (c:\hybrid-ai-agent) to Python's path.
# This lets Python find 'from app.engines.sql_engine import ...' correctly.
# Without -m, Python looks for 'app' relative to the tests/ folder — and fails.

# In the future, we'll use pytest to run all tests at once:
python -m pytest tests/ -v
# -v means "verbose" — shows each test name and pass/fail status
```

---

## 10. Known Issues & Fixes

### Issue 1: SSL Certificate Error on pip install
**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`
**Cause:** Corporate network proxy intercepts HTTPS and uses a company SSL certificate that Python doesn't trust.
**Fix:**
```powershell
pip install package-name --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### Issue 2: OpenAI API Quota Exceeded (429)
**Error:** `RateLimitError: insufficient_quota`
**Cause:** The OpenAI API key has no billing credits attached.
**Fix:** Add credits at https://platform.openai.com/billing
**Workaround for embeddings:** Set `EMBEDDING_MODE=local` in `.env` to use the free local model.

### Issue 3: `ModuleNotFoundError: No module named 'app'`
**Error:** Happens when running `python app/database/seed.py` directly.
**Cause:** Python doesn't know about the project root, so it can't find `app/`.
**Fix:** Always use `-m` flag: `python -m app.database.seed`

### Issue 4: ChromaDB telemetry warnings
**Warning:** `Failed to send telemetry event`
**Cause:** ChromaDB tries to send usage statistics to its servers, which the corporate proxy blocks.
**Impact:** None — these are harmless warnings. Functionality is not affected.

---

## 11. Learning Resources

### Python Fundamentals (if you need to brush up)
| Topic | Resource | Why It Matters |
|-------|----------|----------------|
| Python basics | https://docs.python.org/3/tutorial/ | Foundation for everything |
| Classes & OOP | https://realpython.com/python3-object-oriented-programming/ | SQLAlchemy models use classes |
| Decorators & generators | https://realpython.com/introduction-to-python-generators/ | `get_session()` uses `yield` |
| f-strings & formatting | https://realpython.com/python-f-strings/ | Used throughout the code |
| Type hints | https://realpython.com/python-type-checking/ | `Mapped[str]`, `Optional[str]` etc. |

### SQLAlchemy (Database Layer)
| Topic | Resource |
|-------|----------|
| Official docs | https://docs.sqlalchemy.org/en/20/ |
| ORM tutorial | https://docs.sqlalchemy.org/en/20/orm/quickstart.html |
| Models & relationships | https://realpython.com/python-sqlalchemy/ |

### LangChain (AI Orchestration)
| Topic | Resource |
|-------|----------|
| Official docs | https://python.langchain.com/docs/introduction/ |
| Conceptual guide | https://python.langchain.com/docs/concepts/ |
| LCEL (pipe syntax) | https://python.langchain.com/docs/concepts/lcel/ |
| SQL chain tutorial | https://python.langchain.com/docs/tutorials/sql_qa/ |
| RAG tutorial | https://python.langchain.com/docs/tutorials/rag/ |

### ChromaDB (Vector Database)
| Topic | Resource |
|-------|----------|
| Official docs | https://docs.trychroma.com/ |
| Getting started | https://docs.trychroma.com/getting-started |
| Usage guide | https://docs.trychroma.com/usage-guide |

### Embeddings & Vector Search (the core AI concept)
| Topic | Resource |
|-------|----------|
| What are embeddings? | https://platform.openai.com/docs/guides/embeddings |
| Visual explanation | https://vickiboykis.com/what_are_embeddings/ (beginner-friendly) |
| Sentence Transformers | https://sbert.net/ |

### OpenAI API
| Topic | Resource |
|-------|----------|
| Official docs | https://platform.openai.com/docs/overview |
| Chat completions | https://platform.openai.com/docs/guides/text-generation |
| Managing billing | https://platform.openai.com/billing |

### SQLite
| Topic | Resource |
|-------|----------|
| SQLite overview | https://www.sqlite.org/about.html |
| SQL basics | https://www.w3schools.com/sql/ |
| SQLite browser (GUI tool to inspect your .db file) | https://sqlitebrowser.org/ |

### python-dotenv (Environment Variables)
| Topic | Resource |
|-------|----------|
| Official docs | https://pypi.org/project/python-dotenv/ |
| Why use .env files | https://12factor.net/config |

### Streamlit (UI — Step 10)
| Topic | Resource |
|-------|----------|
| Getting started | https://docs.streamlit.io/get-started |
| API reference | https://docs.streamlit.io/library/api-reference |

---

## 12. Progress Tracker

| Step | Module | Status | What it does |
|------|--------|--------|-------------|
| 1 | Project Setup | ✅ Done | venv, packages, config files |
| 2 | SQLite Database | ✅ Done | 3 tables, 10 employees, 5 projects |
| 3 | Vector Store | ✅ Done | 22 chunks from 3 HR docs in ChromaDB |
| 4 | NL-to-SQL Engine | ✅ Done | Schema + SQL execution + safety validator |
| 5 | RAG Engine | 🔜 Next | Connect vector store to LLM for doc Q&A |
| 6 | Router | ⏳ Pending | Classify question: SQL vs RAG vs Both |
| 7 | Memory | ⏳ Pending | Remember last 5 turns of conversation |
| 8 | Orchestrator | ⏳ Pending | Tie router + engines + memory together |
| 9 | Feedback | ⏳ Pending | Thumbs up/down, log corrections |
| 10 | Streamlit UI | ⏳ Pending | Chat window + admin panel |
| 11 | Docker | ⏳ Pending | Package everything into containers |

---

*Last updated: 2026-06-26*
*This document is updated at the end of each working session.*

---

## 13. Your Java → AI Bridge (Concept Mapping)

Srini, your 15 years of Java/Spring experience maps directly to AI concepts.
Here's the translation table you'll use in every interview:

| Java / Spring Concept | AI / LangChain Equivalent | How They're Similar |
|----------------------|--------------------------|---------------------|
| `@Service` class | LangChain `Chain` | A reusable unit of business logic |
| `@RestController` endpoint | Agent Tool | Exposes a capability the AI can call |
| Spring `ApplicationContext` | LangChain `Runnable` graph | Wires components together |
| Kafka topic / message | LangChain `Message` | Structured data passed between components |
| Spring `@Transactional` | `session.commit()` / `rollback()` | Atomic all-or-nothing operations |
| JPA `@Entity` | SQLAlchemy `Base` model | Maps a class to a database table |
| JPA `@Repository` | `get_session()` + queries | Data access layer pattern |
| `application.properties` | `.env` file | Externalised configuration |
| Maven `pom.xml` | `requirements.txt` | Dependency management |
| Spring Bean singleton | `get_llm()` factory | Single configured instance, reused |
| Microservices | Agent Tools | Small, single-purpose components |
| API Gateway | Orchestrator | Routes requests to correct service |
| Circuit Breaker (Hystrix) | `tenacity` retry decorator | Resilience for external API calls |
| Event-driven (Kafka) | LangChain Streaming | Async, token-by-token response delivery |

---

## 14. Interview Preparation — Agentic AI Engineer (Senior/Lead)

### 14.1 What Interviewers Actually Test at Senior Level

At a Senior / Tech Lead level, interviewers don't just check if you can
code — they test FOUR things:

```
1. DEPTH     — Can you explain WHY, not just WHAT?
               "Why did you use RAG instead of fine-tuning?"

2. TRADE-OFF — Can you compare approaches and justify choices?
               "Why ChromaDB over Pinecone? Why LangChain over LlamaIndex?"

3. PRODUCTION — Can you think beyond the happy path?
               "What happens when the LLM generates invalid SQL?"
               "How do you handle API rate limits at scale?"

4. LEADERSHIP — Can you guide a team?
               "How would you evaluate whether an AI answer is trustworthy?"
               "How would you convince stakeholders to use RAG vs fine-tuning?"
```

---

### 14.2 Core Interview Questions — By Step

#### STEP 1: Project Setup & Architecture

**Q1. What is an Agentic AI system? How is it different from a simple chatbot?**

> **Answer (say this in an interview):**
> A chatbot follows a fixed conversation script. An Agentic AI system has
> *autonomy* — it can decide which tools to use, in what order, and can
> iterate based on intermediate results.
>
> **Java analogy you can use:** A chatbot is like a hardcoded `switch` statement.
> An agent is like a `Strategy` pattern where the strategy is chosen dynamically
> at runtime by the LLM itself.
>
> In this project, the agent can route to the SQL engine, the RAG engine,
> or both — based on understanding the user's intent, not a hardcoded rule.

---

**Q2. Why did you choose Python for this project instead of Java?**

> **Answer:**
> The AI/ML ecosystem is Python-native. LangChain, ChromaDB, HuggingFace
> Transformers, PyTorch — these are Python-first with no Java equivalents of
> the same maturity. For prototyping and research, Python is the industry standard.
>
> That said, in production enterprise systems, you'd commonly see a Python
> AI service exposing REST/gRPC endpoints that a Java Spring Boot application
> calls — combining the strengths of both ecosystems.

---

**Q3. Explain the architecture of your hybrid AI agent.**

> **Answer (walk through the diagram):**
> The system has 6 layers:
> 1. **UI** (Streamlit) — user-facing chat interface
> 2. **Orchestrator** — the central coordinator, like an API Gateway
> 3. **Router** — classifies intent: SQL query, document query, or both
> 4. **Engines** — SQL Engine (structured data) + RAG Engine (unstructured)
> 5. **Data layer** — SQLite (structured) + ChromaDB (vector)
> 6. **Memory** — keeps last N conversation turns for context
>
> **Java analogy:** This mirrors a microservices architecture.
> The orchestrator = API Gateway. Each engine = a microservice.
> The router = service discovery / routing logic.

---

#### STEP 2: Database Design

**Q4. Why SQLite for the database instead of PostgreSQL?**

> **Answer:**
> SQLite is a zero-configuration, single-file database — perfect for local
> development and prototyping. It ships with Python's standard library.
>
> The LangChain `SQLDatabase` abstraction means the NL-to-SQL engine works
> identically whether the backend is SQLite, PostgreSQL, or MySQL — we just
> change the connection string in `.env`. This is the same principle as
> Spring's `DataSource` abstraction.
>
> For production, I'd switch to PostgreSQL for concurrent users, transactions,
> and enterprise-grade reliability.

---

**Q5. How does SQLAlchemy compare to JPA/Hibernate?**

> **Answer:**
>
> | Concept | Hibernate/JPA | SQLAlchemy |
> |---------|--------------|-----------|
> | Entity mapping | `@Entity` class | Class inheriting `Base` |
> | Column definition | `@Column` annotation | `mapped_column(...)` |
> | Relationships | `@OneToMany`, `@ManyToMany` | `relationship(...)` |
> | Session/Transaction | `EntityManager` | `Session` |
> | Schema creation | `hbm2ddl.auto=create` | `Base.metadata.create_all()` |
> | JPQL / Criteria API | `session.createQuery(...)` | `session.query(Model).filter(...)` |
>
> Both follow the same ORM concept: map Python/Java objects ↔ database tables,
> manage connections via a session/entity manager, and support transactions.

---

**Q6. Explain the many-to-many relationship in your schema.**

> **Answer:**
> An employee can work on many projects. A project can have many employees.
> In SQL, you can't store a list inside a column, so we use a **junction table**
> `employee_projects` that stores (employee_id, project_id) pairs.
>
> Each row = one assignment. The primary key is composite: (employee_id + project_id)
> together, which prevents the same employee being assigned to the same project twice.
>
> **Java equivalent:** This is a `@ManyToMany` with `@JoinTable` in JPA.

---

#### STEP 3: Vector Store & Embeddings

**Q7. What is a vector embedding and why is it better than keyword search?**

> **Answer:**
> An embedding converts text into a list of numbers (a vector) that encodes
> semantic meaning. The key insight is:
>
> - "sick leave" and "medical absence" → similar vectors → found together
> - "sick leave" and "quarterly earnings" → different vectors → not related
>
> Keyword search would miss "medical absence" if the user asked about "sick leave"
> because the words don't match. Vector search finds it because the *meaning* matches.
>
> **Java analogy:** Think of keyword search as `String.equals()`.
> Embedding similarity is like a semantic hash — similar concepts hash to nearby
> values in a high-dimensional space.

---

**Q8. What is RAG? Why use it instead of fine-tuning the model?**

> **Answer:**
> RAG = Retrieval Augmented Generation. Instead of baking knowledge into the
> model (fine-tuning), we *retrieve* relevant documents at query time and
> pass them as context to the LLM.
>
> | | RAG | Fine-tuning |
> |-|-----|------------|
> | **Cost** | Low — just storage + retrieval | High — GPU training |
> | **Updates** | Add a file, re-embed, done | Retrain the model |
> | **Transparency** | You can see which chunk was used | Opaque |
> | **Accuracy** | High for factual, doc-grounded answers | High for style/behaviour |
>
> For enterprise HR documents that change quarterly, RAG is the clear choice.
> Fine-tuning is better when you need to change the model's *behaviour*, not
> its *knowledge*.

---

**Q9. How do you choose chunk size?**

> **Answer:**
> It's a trade-off:
>
> - **Too small (e.g. 200 chars):** Each chunk lacks context. The answer to
>   "what is the sick leave policy?" might be split across 3 chunks and
>   none alone contains the full answer.
>
> - **Too large (e.g. 3000 chars):** Retrieval is imprecise. You return too
>   much text and the LLM has to wade through noise. Also hits token limits.
>
> Our choice of 800 chars with 100-char overlap is a common starting point
> for HR/policy documents. In production, you'd experiment with different
> sizes and measure retrieval precision (did we get the right chunk?).
>
> **Advanced consideration:** Different document types need different strategies.
> Code files → split by function. PDFs → split by page. HTML → split by section.

---

#### STEP 4: NL-to-SQL Engine

**Q10. How do you prevent SQL injection in an LLM-generated query?**

> **Answer:**
> This is a critical security concern. We use three layers:
>
> 1. **Allowlist tables:** `SQLDatabase(include_tables=[...])` — the LLM can only
>    reference the tables we explicitly listed. If it tries to query any other
>    table, LangChain raises an error before touching the database.
>
> 2. **Keyword blocklist:** `validate_sql()` checks the generated SQL for
>    `DELETE`, `UPDATE`, `DROP`, `ALTER`, `TRUNCATE` before execution.
>
> 3. **SELECT-only enforcement:** We verify the SQL starts with `SELECT` or `WITH`.
>
> **What we DON'T do:** We don't use parameterised queries for LLM-generated SQL
> because the LLM generates the entire SQL string. This is why the allowlist and
> blocklist are essential — we validate the structure of the SQL itself.
>
> **Java equivalent:** This is similar to SQL injection prevention in JDBC —
> you'd use `PreparedStatement` for user input, and also validate that user
> input can't override your query structure.

---

**Q11. What is LangChain's "chain" and how does it compare to Spring's pipeline patterns?**

> **Answer:**
> A LangChain chain is a sequence of processing steps connected by the `|` pipe operator:
>
> ```python
> chain = prompt | llm | output_parser
> result = chain.invoke({"question": "..."})
> ```
>
> **Java analogy:** This is identical to Java 8 Stream pipelines:
> ```java
> result = Stream.of(question)
>     .map(prompt::format)       // ← prompt
>     .map(llm::call)            // ← llm
>     .map(parser::parse)        // ← output_parser
>     .findFirst();
> ```
>
> Or Spring Integration's message pipeline / Spring Batch step chaining.
> The LangChain Expression Language (LCEL) is just a fluent API for composing
> these processing steps.

---

### 14.3 Scenario-Based Questions (Senior/TechLead Level)

These are the questions that separate senior candidates from mid-level:

---

**Scenario 1: Production Failure**

> *"Your NL-to-SQL engine is in production. A user types: 'Show me everyone's salary'.
> The LLM generates correct SQL and it runs — but 10,000 employees' salaries are
> returned in the UI. How do you fix this?"*

**Expected answer:**
- Add a `LIMIT` clause to every generated query (e.g. max 100 rows)
- In `validate_sql()`, check if the query has a LIMIT and add one if not
- Add role-based access control — the user's role determines which columns they can see
- Consider column-level masking: HR sees full salary, others see a salary band
- Log all queries with user identity for audit compliance (GDPR/SOX requirement)

---

**Scenario 2: RAG Hallucination**

> *"A user asks 'How many days of paternity leave do I get?' and the AI answers
> '8 weeks' — but the HR document says '4 weeks'. How does this happen and how do you fix it?"*

**Expected answer:**
- This is a **hallucination** — the LLM made up a number not in the retrieved chunks
- Root cause: wrong chunk was retrieved, OR the LLM blended its training data with the retrieved text
- Fix 1: Always cite the source chunk in the answer (`"According to hr_leave_policy.txt..."`
- Fix 2: Increase `k` (retrieve more chunks) — the right chunk might rank 6th when k=5
- Fix 3: Add a reranker (BGE-Reranker, Step 3 of our stack) — reranks top-k for precision
- Fix 4: Add a verification step — after generating the answer, ask the LLM "Is this answer supported by the provided text? Yes/No"
- Fix 5: Collect user feedback (thumbs down), flag for human review

---

**Scenario 3: Architecture Design**

> *"Your hybrid agent is getting 1000 queries/minute in production. How do you scale it?"*

**Expected answer:**
- **LLM calls** are the bottleneck — they're slow (1-3 seconds each) and expensive
  - Use async/concurrent calls: `asyncio` + `aiohttp`
  - Cache common queries: if "show me sick leave policy" is asked 100x/day, cache the answer
  - Use a faster/cheaper model for simple queries (GPT-4o-mini) and reserve GPT-4o for complex ones
- **Vector search** (ChromaDB) is fast — but at 1000 req/min consider:
  - Move to a managed vector DB (Pinecone, Weaviate) with horizontal scaling
  - Keep embeddings warm in memory
- **SQL queries** are fast — SQLite won't handle concurrent writes but reads scale fine
  - For write-heavy production: switch to PostgreSQL with connection pooling (HikariCP equivalent: SQLAlchemy `pool_size`)
- **Application layer**: wrap the Python agent in FastAPI, containerize with Docker, deploy on Kubernetes
  - This is exactly your Java microservices experience applied to Python

---

**Scenario 4: Team Leadership**

> *"Your team wants to use LlamaIndex instead of LangChain. How do you evaluate this?"*

**Expected answer:**
- Both solve the same problem (LLM orchestration) with different design philosophy:
  - LangChain: general-purpose, huge ecosystem, more verbose, more control
  - LlamaIndex: specialised for RAG/document search, simpler for that use case, less flexible
- Evaluation criteria:
  1. What use cases dominate? (Document Q&A → LlamaIndex. Complex agents → LangChain)
  2. Team learning curve and existing knowledge
  3. Community support and maintenance activity (GitHub stars, issues, PRs)
  4. Integration with our existing stack (both integrate with ChromaDB, OpenAI)
- My recommendation: for this project, LangChain is the right choice because we have both SQL and RAG — LangChain's SQL tools are more mature than LlamaIndex's.

---

### 14.4 Questions YOU Should Ask in Interviews

These signal senior-level thinking:

1. *"How is the model's output validated for correctness before it reaches the user?"*
2. *"What's the strategy for handling PII (personal data) in queries — are employee records masked?"*
3. *"How are LLM costs monitored and budgeted? Is there per-user or per-team quota management?"*
4. *"How do you evaluate whether the RAG retrieval quality is good enough? What metrics do you track?"*
5. *"Is the LLM fine-tuned on company data, or is it purely RAG-based? What's the data governance story?"*
6. *"How do you handle model version changes — if OpenAI releases GPT-5 and behaviour changes?"*

---

### 14.5 Keywords to Drop in Interviews (AI Vocabulary)

Know these terms confidently — interviewers listen for them:

| Term | What it means | Use in a sentence |
|------|--------------|-------------------|
| **RAG** | Retrieval Augmented Generation | "We use RAG to ground the LLM's answers in our HR documents" |
| **Embedding** | Text → vector of numbers | "We embed each document chunk using a sentence-transformer model" |
| **Vector similarity** | How close two embeddings are | "We use cosine similarity to find the top-k most relevant chunks" |
| **Chunking** | Splitting documents into pieces | "We chunk at 800 chars with 100-char overlap to preserve context" |
| **Grounding** | Basing answers on real data | "The agent is grounded in our database — it can't hallucinate employee names" |
| **Hallucination** | LLM making up facts | "We mitigate hallucination by always citing the source document" |
| **Temperature** | LLM creativity setting | "Temperature=0 for SQL generation ensures deterministic output" |
| **Prompt engineering** | Crafting effective LLM instructions | "We inject the schema into the prompt so the LLM knows the table structure" |
| **Chain** | Linked processing steps | "Our answer chain is: prompt → LLM → output parser" |
| **Agent** | LLM that decides which tools to call | "The orchestrator acts as an agent routing to SQL or RAG tools" |
| **Tool** | A function an agent can call | "SQL engine and RAG engine are tools registered with the orchestrator" |
| **LLM orchestration** | Coordinating multiple AI calls | "LangChain handles the orchestration of prompt building, LLM calls, and parsing" |
| **Fine-tuning** | Retraining a model on your data | "We chose RAG over fine-tuning because HR policies change quarterly" |
| **Context window** | Max tokens an LLM can process at once | "GPT-4o has a 128k token context window — we stay well under with chunking" |
| **Semantic search** | Search by meaning, not keywords | "We use semantic search over the vector store to find policy answers" |
| **Reranker** | Re-orders retrieved chunks by relevance | "A cross-encoder reranker (BGE-Reranker) improves precision over the top-k results" |
| **LCEL** | LangChain Expression Language (the pipe syntax) | "LCEL lets us compose chains declaratively using the pipe operator" |

---

*Last updated: 2026-06-26*
*This document is updated at the end of each working session.*
