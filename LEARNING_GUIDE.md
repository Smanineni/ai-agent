# NexusAI — Complete Learning Guide

> This README is your personal reference document.
> Every file, every concept, every line, explained step by step.
> Come back to it whenever you feel lost.

---

> **About this guide:** Written for Srinivasulu Manineni (Srini), a Tech Lead with 15 years of Java/Spring/Kafka experience, now transitioning to Agentic AI Engineering. Java analogies are used throughout, and interview questions are woven into each section.

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

**NexusAI** is an enterprise knowledge and data query platform that answers natural language questions
across two types of data at the same time:

| Data Type | Example Question | How Answered |
|-----------|-----------------|--------------|
| **Structured** (SQL database) | "Who are the highest paid engineers?" | LLM writes SQL → runs against SQLite |
| **Unstructured** (documents) | "How many sick days do I get?" | Finds relevant text chunks → LLM reads and answers |
| **Both combined** | "Who manages the AI project, and what is their leave policy?" | Routes to both engines, combines answers |

**In plain English:** You type a question. The system figures out whether to
search the database, the documents, or both, then gives you a clear answer
in plain English.

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
nexus-ai/
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
can't import code from that folder. Think of it as a registration card that
tells Python the folder is a package.

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
Without it, `python` points to your system Python, which doesn't have
langchain, chromadb, and the rest installed. Once you activate, `python`
uses the project's own environment where all the packages live.

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
Unlike PostgreSQL or MySQL, there's no server to install or configure.
It's a good fit for learning and small projects.

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
you write a test once and run it whenever you want to confirm
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
**Impact:** None. These are harmless warnings and don't affect functionality.

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
| 5 | RAG Engine | ✅ Done | Retrieve chunks, stuff prompt, return answer + sources |
| 6 | Router | ✅ Done | Intent classifier: QUERY_SQL / QUERY_DOC / QUERY_BOTH |
| 7 | Memory | ✅ Done | Sliding window, last 3 turns, anaphora resolution support |
| 8 | Orchestrator | ✅ Done | Coordinates router + engines + memory end-to-end |
| 9 | Feedback | ✅ Done | Thumbs up/down, corrections, golden queries, stats |
| 10 | Streamlit UI | ✅ Done | Chat window, 👍👎 feedback, admin panel with golden queries |
| 11 | Docker | ✅ Done | Dockerfile, docker-compose.yml, .dockerignore |

---

*Last updated: 2026-07-01*
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

At a senior or tech lead level, interviewers don't just check if you can
code. They usually test four things:

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
> *autonomy* to decide which tools to use, in what order, and it can
> iterate based on what it finds along the way.
>
> **Java analogy you can use:** A chatbot is like a hardcoded `switch` statement.
> An agent is like a `Strategy` pattern where the strategy is chosen dynamically
> at runtime by the LLM itself.
>
> In this project, the agent can route to the SQL engine, the RAG engine,
> or both, based on what the user actually wants rather than a hardcoded rule.

---

**Q2. Why did you choose Python for this project instead of Java?**

> **Answer:**
> The AI/ML ecosystem is Python-native. LangChain, ChromaDB, HuggingFace
> Transformers, PyTorch. These are Python-first libraries with no mature Java
> equivalents. For prototyping and research, Python is the industry standard.
>
> That said, in production enterprise systems, you'd commonly see a Python
> AI service exposing REST/gRPC endpoints that a Java Spring Boot application
> calls. That combination lets you get the best of both ecosystems.

---

**Q3. Explain the architecture of NexusAI.**

> **Answer (walk through the diagram):**
> The system has 6 layers:
> 1. **UI** (Streamlit): the chat window in the browser
> 2. **Orchestrator**: the central coordinator, similar to an API Gateway
> 3. **Router**: classifies the question as SQL, document search, or both
> 4. **Engines**: SQL Engine for structured data, RAG Engine for documents
> 5. **Data layer**: SQLite for structured data, ChromaDB for vectors
> 6. **Memory**: stores the last N conversation turns for context
>
> **Java analogy:** This mirrors a microservices architecture.
> The orchestrator = API Gateway. Each engine = a microservice.
> The router = service discovery / routing logic.

---

#### STEP 2: Database Design

**Q4. Why SQLite for the database instead of PostgreSQL?**

> **Answer:**
> SQLite is a zero-configuration, single-file database, which makes it ideal for local
> development and prototyping. It ships with Python's standard library.
>
> The LangChain `SQLDatabase` abstraction means the NL-to-SQL engine works
> identically whether the backend is SQLite, PostgreSQL, or MySQL. You just
> change the connection string in `.env`. It's the same principle as
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
> An embedding converts text into a list of numbers (a vector) that captures
> semantic meaning. Here's what makes it powerful:
>
> - "sick leave" and "medical absence" → similar vectors → found together
> - "sick leave" and "quarterly earnings" → different vectors → not related
>
> Keyword search would miss "medical absence" if the user asked about "sick leave"
> because the words don't match. Vector search finds it because the *meaning* matches.
>
> **Java analogy:** Think of keyword search as `String.equals()`.
> Embedding similarity works like a semantic hash where similar concepts end up
> near each other in a high-dimensional space.

---

**Q8. What is RAG? Why use it instead of fine-tuning the model?**

> **Answer:**
> RAG = Retrieval Augmented Generation. Instead of baking knowledge into the
> model (fine-tuning), we *retrieve* relevant documents at query time and
> pass them as context to the LLM.
>
> | | RAG | Fine-tuning |
> |-|-----|------------|
> | **Cost** | Low (just storage and retrieval) | High (requires GPU training) |
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
> 1. **Allowlist tables:** `SQLDatabase(include_tables=[...])` so the LLM can only
>    reference the tables we explicitly listed. If it tries to query anything else,
>    LangChain raises an error before touching the database.
>
> 2. **Keyword blocklist:** `validate_sql()` checks the generated SQL for
>    `DELETE`, `UPDATE`, `DROP`, `ALTER`, `TRUNCATE` before execution.
>
> 3. **SELECT-only enforcement:** We verify the SQL starts with `SELECT` or `WITH`.
>
> **What we DON'T do:** We don't use parameterised queries for LLM-generated SQL
> because the LLM generates the entire SQL string. This is why the allowlist and
> blocklist are both essential. We validate the structure of the SQL itself.
>
> **Java equivalent:** This is similar to SQL injection prevention in JDBC.
> You'd use `PreparedStatement` for user input and also validate that user
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

#### STEP 5: RAG Engine

**Q12. Walk me through your RAG pipeline end-to-end.**

> **Answer:**
> ```
> User question
>     ↓
> Embed question → 384-dim vector (all-MiniLM-L6-v2)
>     ↓
> ChromaDB cosine similarity search → top-k chunks
>     ↓
> Stuff chunks into prompt as context
>     ↓
> GPT-4o generates answer grounded in those chunks
>     ↓
> Return: answer + source document names + chunk text used
> ```
>
> **Java analogy:** Think of it as a search-before-answer pattern.
> Before calling the LLM (your "business logic"), you first call a
> search service (ChromaDB) to load the relevant data, then pass that
> data into the service call. It's similar to how a Spring `@Service`
> might first call a `@Repository` to load an entity before processing it.

---

**Q13. What is "context stuffing" and what are its limits?**

> **Answer:**
> Context stuffing means we take retrieved chunks and literally paste them
> into the prompt so the LLM sees them as part of its input.
>
> ```
> "Use the following documents to answer the question.
>  Documents: [chunk1 text] [chunk2 text] [chunk3 text]
>  Question: How many sick days do I get?"
> ```
>
> **Limits:**
> - **Token window:** GPT-4o has 128k tokens. If you stuff too many chunks,
>   you hit the limit. We mitigate by controlling `k` (number of chunks).
> - **Lost-in-the-middle problem:** LLMs pay more attention to text at the
>   start and end of context. If the answer is in the middle of 20 chunks,
>   accuracy drops. Fix: reranker (Step 3 of our stack).
> - **Coherence:** Too many chunks from different documents can confuse the model.
>   Fix: use a reranker to select only the most relevant 2–3 chunks.
>
> **Map-Reduce** is another option where you summarise each chunk separately and
> then combine those summaries. It's slower but works well for very long documents.

---

**Q14. How do you measure RAG quality? What metrics do you use?**

> **Answer:**
> Three key metrics:
>
> | Metric | What it measures | How to compute |
> |--------|-----------------|----------------|
> | **Retrieval Recall** | Did we retrieve the right chunk? | Manually label 20 queries; check if the correct chunk is in top-k |
> | **Answer Faithfulness** | Is the answer supported by the retrieved text? | LLM-as-judge: ask GPT to score whether the answer contradicts the chunks |
> | **Answer Relevance** | Does the answer actually address the question? | Human or LLM evaluation on a test set |
>
> Tools: **RAGAS** (open-source RAG evaluation framework) automates all three.
>
> **Production monitoring:** Log every query + retrieved chunks + answer.
> Sample 5% for human review. Track thumbs-down rate from the feedback UI.
>
> **Java analogy:** Think of it like unit test coverage metrics.
> You're measuring how often your system returns the right answer,
> the same way you'd track line or branch coverage.

---

**Q15. What's the difference between a retriever and a reranker?**

> **Answer:**
> Two-stage pipeline:
>
> ```
> Stage 1 — Retriever (fast, approximate):
>   Embeds query → cosine similarity → returns top-20 candidates
>   Uses: bi-encoder (two separate embeddings compared)
>   Speed: milliseconds
>
> Stage 2 — Reranker (slow, precise):
>   Takes all 20 candidates + original query together
>   Uses: cross-encoder (reads query + document TOGETHER)
>   Outputs: relevance score for each → returns top-3
>   Speed: ~1 second per batch
> ```
>
> **Why two stages?** The retriever is fast but approximate.
> The reranker is more precise but slower, so you can't run it over the entire database.
> You retrieve broadly first, then rerank precisely. It's the same pattern as
> Elasticsearch combined with business-logic scoring in Java search systems.
>
> We use **BGE-Reranker** (BAAI/bge-reranker-base), a free local cross-encoder.

---

#### STEP 6: Router / Intent Detection

**Q16. Why does the router exist? Why not just send every question to both engines?**

> **Answer:**
> You could call both engines every time, but that would mean:
> - Two LLM calls instead of one (doubles cost and latency)
> - Two sets of results that need to be merged, which adds complexity
> - The SQL engine would try to query the database for document questions
>   and return nothing useful (or worse, hallucinate a query)
>
> The router adds a small upfront classification cost (one fast LLM call)
> to avoid two expensive downstream calls. It's the same principle as an
> API Gateway routing to microservices. You route once, then execute once.
>
> **Java analogy:** Think of it as a front-controller servlet or a Spring
> `HandlerMapping` that inspects the request and dispatches to the right
> handler. The router's job is dispatch, not execution.

---

**Q17. Why use an LLM for intent classification instead of keyword matching?**

> **Answer:**
> Keyword matching breaks on natural language variation:
>
> | Question | Keywords | Actual intent |
> |----------|----------|---------------|
> | "Tell me about Alice's projects" | "projects" → SQL | QUERY_SQL |
> | "What is the project leave policy?" | "project" → SQL? | QUERY_DOC |
> | "Who leads the AI project and what leave does she get?" | both | QUERY_BOTH |
>
> Keyword matching can't distinguish these. An LLM understands that
> "leave policy" is about HR documents and "who leads" is about the
> employee database, even in the same sentence.
>
> The trade-off is cost and latency. For production at scale, you could
> replace the LLM router with a fine-tuned text classifier (BERT-based)
> that runs locally in milliseconds, trained on labelled examples of each
> intent class.

---

**Q18. How do you make the LLM return a structured, machine-readable classification?**

> **Answer:**
> By default, an LLM returns free-form text. We need a controlled output
> like `QUERY_SQL`, `QUERY_DOC`, or `QUERY_BOTH`. Two approaches:
>
> **Approach 1: Constrained prompt + output parser** (what we use):
> The prompt explicitly says "Reply with ONLY one of these three words:
> QUERY_SQL, QUERY_DOC, QUERY_BOTH." The `StrOutputParser` extracts
> the text and we `.strip().upper()` it to normalise.
>
> **Approach 2: Structured output / function calling**:
> OpenAI supports `response_format={"type": "json_object"}` or
> tool/function calling, which forces the model to return a schema-valid
> JSON object. More robust but adds a dependency on the model's
> structured output feature.
>
> For a three-class classifier, Approach 1 is simple and reliable.
> For complex multi-field structured extraction, Approach 2 is better.
>
> **Java analogy:** Approach 1 is like parsing a plain text HTTP response.
> Approach 2 is like consuming a well-typed JSON REST API where the schema
> is enforced at the protocol level.

---

**Q19. How do you handle the case where the router is wrong?**

> **Answer:**
> The router will occasionally misclassify. For example, it might route
> "What project is Alice on?" to QUERY_DOC instead of QUERY_SQL.
>
> Mitigation strategies:
> 1. **Fallback to BOTH:** If confidence is low (you can ask the LLM to
>    return a confidence score), default to QUERY_BOTH. Slower but correct.
> 2. **Feedback loop:** When the user gives a thumbs down on an answer,
>    log the question + classification. These become training examples
>    for improving the router prompt or a fine-tuned classifier.
> 3. **User correction:** "I couldn't find that in the database. Did you
>    mean to ask about HR policies?" Give them a redirect.
> 4. **Confidence threshold:** Run both engines if the top classification
>    score is below 0.8. Only route exclusively when confident.
>
> In production, you'd track routing accuracy as a metric (correct
> classifications / total) and alert when it drops below a threshold.

---

#### STEP 7: Conversation Memory

**Q20. Why does a conversational AI need memory? Can't the user just repeat themselves?**

> **Answer:**
> Technically yes, but it makes the system unusable in practice. Real
> conversations are full of references like "their", "that project", "the same
> person" — pronouns and shorthand that only make sense in context.
>
> Example without memory:
> - User: "Who is the highest paid engineer?"
> - Agent: "David Park, $145,000."
> - User: "What leave does he get?"
> - Agent (no memory): ❌ "Who is 'he'? I don't have that information."
>
> Example with memory:
> - Agent (with memory): ✅ Resolves "he" → David Park → queries correctly.
>
> This is called **anaphora resolution** — resolving pronouns and references
> back to earlier entities in the conversation. It's what makes the agent
> feel like a conversation rather than a series of isolated searches.
>
> **Java analogy:** Memory is like an HTTP session (`HttpSession`). Without it,
> every request is stateless and the server has no idea who called before.
> With it, you carry state across multiple requests.

---

**Q21. What is ConversationBufferWindowMemory and why "window"?**

> **Answer:**
> LangChain's `ConversationBufferWindowMemory` stores the last `k` turns
> of conversation (a turn = one user message + one agent response).
>
> The "window" means we only keep the most recent `k` turns and discard older ones.
>
> Why not keep everything? Two reasons:
> 1. **Token cost.** Every past message gets included in the prompt for
>    the next LLM call. If you had 50 turns, that's thousands of tokens
>    added to every request — expensive and slow.
> 2. **Context window limit.** GPT-4o has 128k tokens. A long conversation
>    history can push you toward the limit, causing truncation or errors.
>
> Keeping the last 3-5 turns is a practical balance. Most follow-up
> questions refer to something said in the last 1-2 turns anyway.
>
> **Java analogy:** Think of it as a circular buffer or a fixed-size
> `LinkedList` with a max capacity. When it fills up, the oldest entry
> is dropped to make room for the newest.

---

**Q22. How does memory change the prompt sent to the LLM?**

> **Answer:**
> Without memory, the prompt is just:
> ```
> Question: What leave does he get?
> Answer:
> ```
>
> With memory, the prompt becomes:
> ```
> Previous conversation:
> Human: Who is the highest paid engineer?
> Assistant: David Park, $145,000, Engineering Manager.
>
> Current question: What leave does he get?
> Answer:
> ```
>
> The LLM now has the context it needs to resolve "he" to David Park.
> This is the entire mechanism — there's no magic, just carefully injecting
> history into the prompt before every call.
>
> In production systems with many users, each user gets their own memory
> instance, keyed by a session ID (same as how web sessions work).

---

#### STEP 8: Orchestrator

**Q23. What is the orchestrator's job? Why does it need to exist as a separate component?**

> **Answer:**
> The orchestrator is the central coordinator. It's the only component that
> knows about all the others. Its job is to receive a question and drive
> the full pipeline from start to finish:
>
> ```
> receive question
>     → enrich it with memory (inject conversation history)
>     → classify intent (router)
>     → call the right engine(s)
>     → store the result in memory
>     → return a structured response to the UI
> ```
>
> It needs to exist separately because none of the other components should
> know about each other. The SQL engine shouldn't know about memory. The
> router shouldn't know about ChromaDB. Each component does one thing.
> The orchestrator is the only place where they're wired together.
>
> This is the **Single Responsibility Principle** applied at the system level.
>
> **Java analogy:** The orchestrator is exactly an API Gateway or a
> Spring `@Service` that acts as a facade, coordinating calls to
> multiple downstream services and assembling the final response.
> Think of it as the entry point `@RestController` for the entire AI system.

---

**Q24. How does the orchestrator handle a QUERY_BOTH intent?**

> **Answer:**
> When the router returns `QUERY_BOTH`, the orchestrator needs results from
> two engines. There are two strategies:
>
> **Sequential (what we implement):**
> Call SQL engine first, then RAG engine, then combine both answers into
> one response with a synthesis prompt. Simple, easy to debug.
>
> **Parallel (production optimisation):**
> Call both engines concurrently using `asyncio.gather()`. Halves latency
> since you're waiting for both at the same time instead of one after the other.
> More complex — you need to handle partial failures (one engine succeeds,
> one fails) gracefully.
>
> For this project, sequential is the right starting point. You'd add
> async parallelism as a performance optimisation once the system is
> working correctly end-to-end.
>
> **Java analogy:** Sequential is like calling two `@Service` beans in order.
> Parallel is like using `CompletableFuture.allOf()` to fire both calls
> simultaneously and join when both complete.

---

**Q25. How does memory integrate with the orchestrator? What exactly changes in the prompt?**

> **Answer:**
> Before calling any engine, the orchestrator asks memory for the last k turns
> as formatted text. It then rewrites the user's question into a
> "context-enriched question" by prepending the history:
>
> ```
> Original question: "What is their leave policy?"
>
> Enriched question sent to the engine:
>     "Previous conversation:
>      Human: Who is the highest paid engineer?
>      Assistant: David Park, $145,000, Engineering Manager.
>
>      Current question: What is their leave policy?"
> ```
>
> If memory is empty (first question of the session), the enriched question
> is just the original question unchanged. No extra tokens, no overhead.
>
> After the engine returns an answer, the orchestrator stores the original
> question and the final answer back into memory for future turns.

---

#### STEP 9: Feedback Loop

**Q26. Why does an AI system need a feedback loop? Can't you just test it before launch?**

> **Answer:**
> Pre-launch testing only covers questions you thought to ask. In production,
> users ask things you never anticipated, and the system's quality drifts over
> time as documents change, language models update, and edge cases accumulate.
>
> A feedback loop gives you a continuous signal from real usage:
> - Which questions get thumbs down? Those are your failure modes.
> - Which queries consistently return wrong SQL? Add those to your test suite.
> - Which document topics are users asking about most? Those need better coverage.
>
> Without it, you're flying blind after launch. With it, you have a living
> dataset of real failures to fix and real successes to protect.
>
> **Java analogy:** This is exactly production monitoring and alerting.
> In Java systems you'd log exceptions, track response times, set up alerts
> in Splunk or Datadog. The feedback store is the AI equivalent — logging
> answer quality instead of error rates.

---

**Q27. What is a "golden query" and how does it relate to the feedback store?**

> **Answer:**
> A golden query is a verified (question, correct answer) pair that you trust
> completely. They come from two sources:
>
> 1. **Feedback corrections:** A user gives thumbs down and a human reviewer
>    writes the correct answer. That pair is now golden.
> 2. **Manual curation:** A domain expert writes question/answer pairs from
>    scratch during onboarding.
>
> Golden queries are used in three ways:
> - **Regression testing:** Run them before every deployment — if any answer
>   changes significantly, something broke.
> - **Few-shot examples:** Embed them into prompts: "Here are 2 correct examples
>   of how to answer questions like this..." This improves accuracy on similar
>   questions without any model retraining.
> - **Evaluation:** Measure the system's quality score (correct answers / total
>   golden queries) over time as a KPI.
>
> **Java analogy:** Golden queries are integration test fixtures. Just as you'd
> have a `@Test` that verifies a specific API response hasn't regressed, a
> golden query verifies a specific AI answer hasn't regressed.

---

**Q28. What data do you store per feedback event, and why each field?**

> **Answer:**
>
> | Field | Why it's stored |
> |-------|----------------|
> | `question` | Lets you find similar failing questions, build test cases |
> | `answer` | The exact response the user rated — needed for correction |
> | `intent` | Was the failure a SQL routing problem or a RAG retrieval problem? |
> | `rating` | `thumbs_up` / `thumbs_down` — the core signal |
> | `correction` | The human-written correct answer (nullable — filled in later) |
> | `timestamp` | Lets you track quality trends over time, detect regressions |
> | `session_id` | Groups a conversation together for context |
>
> You'd use this data to answer questions like:
> - "Our thumbs-down rate went from 5% to 15% this week — what changed?"
> - "Every question about maternity leave gets a thumbs down — is the document outdated?"
> - "Which intent class has the worst rating? SQL or RAG?"

---

#### STEP 10: Streamlit UI

**Q29. Why Streamlit instead of React or Angular for this project?**

> **Answer:**
> Streamlit is a Python-native web framework where the entire UI is
> written in Python. No HTML, no JavaScript, no separate frontend build.
>
> For an AI prototype, that tradeoff is correct:
> - The team building the AI is Python engineers, not frontend engineers
> - Iteration speed matters more than UI polish in a prototype phase
> - Streamlit's `st.session_state` handles per-user state (like our
>   ConversationMemory) in one line
>
> The downside is that Streamlit has limited UI customisation and doesn't
> scale well beyond ~100 concurrent users. For production, you'd replace
> the Streamlit UI with a React/Next.js frontend calling a FastAPI backend.
>
> **Java analogy:** Streamlit is like using Spring Boot's built-in Thymeleaf
> templates for internal tooling. Fast to build, good enough for demos,
> replaced by a proper frontend once the product proves its value.

---

**Q30. How does Streamlit's session state map to our ConversationMemory?**

> **Answer:**
> Streamlit re-runs the entire Python script from top to bottom every time
> the user clicks a button or sends a message. Variables created during one
> run are gone on the next run.
>
> `st.session_state` is a dictionary that persists across re-runs for the
> same browser session. We store one `ConversationMemory` object per user
> session in it:
>
> ```python
> if "memory" not in st.session_state:
>     st.session_state.memory = ConversationMemory(window_size=3)
> ```
>
> On every re-run, the memory object is retrieved from session state, not
> recreated. So the conversation history accumulates correctly.
>
> **Java analogy:** This is exactly `HttpSession.getAttribute("memory")`.
> The first request creates it; every subsequent request retrieves it.

---

#### STEP 11: Docker

**Q31. Why containerise a Python AI application? What problems does Docker solve?**

> **Answer:**
> Three core problems:
>
> 1. **"Works on my machine" problem.** Your laptop has Python 3.11, your colleague
>    has 3.9, the server has 3.10. Package versions differ. ChromaDB behaves
>    differently on each. Docker freezes the entire environment — Python version,
>    all packages, OS libraries — into a single image that runs identically anywhere.
>
> 2. **Dependency isolation.** The AI stack (PyTorch, sentence-transformers,
>    chromadb) conflicts with many other Python projects. Docker gives this app
>    its own isolated environment with no interference.
>
> 3. **Deployment simplicity.** On any server that has Docker installed,
>    `docker compose up` is the only command needed to start the entire system.
>    No manual setup, no pip installs, no environment variables to remember.
>
> **Java analogy:** Docker is to Python apps what a fat JAR (uber-jar) is to
> Spring Boot — you package everything needed to run the app into one artifact.
> Except Docker goes further: it packages the OS layer too, not just the JVM code.

---

**Q32. Explain the difference between a Dockerfile and docker-compose.yml.**

> **Answer:**
>
> | | `Dockerfile` | `docker-compose.yml` |
> |---|---|---|
> | **What it defines** | How to BUILD one container image | How to RUN one or more containers together |
> | **Analogy** | A recipe for baking a cake | Instructions for setting the whole table |
> | **Commands** | `FROM`, `COPY`, `RUN`, `CMD` | `services`, `ports`, `volumes`, `environment` |
> | **Used by** | `docker build` | `docker compose up` |
>
> **Dockerfile** answers: what goes inside the container?
> (Which Python version? Which packages? Which files? What command to run?)
>
> **docker-compose.yml** answers: how do containers connect to each other
> and to the host machine?
> (Which ports to expose? Which folders to mount? Which environment variables to pass?)
>
> **Java analogy:** Dockerfile is like a Maven `pom.xml` that builds an artifact.
> docker-compose.yml is like a Kubernetes deployment YAML that says how to run it.

---

**Q33. What is a Docker volume and why do we need one for this project?**

> **Answer:**
> By default, everything inside a Docker container is ephemeral. When you
> stop and remove a container, all data written inside it is lost.
>
> Our app writes data in two places:
> - `data/db/company.db` — the SQLite database (employees, projects, feedback)
> - `data/chroma/` — ChromaDB vector data (22 embedded document chunks)
>
> Without volumes, every `docker compose down` would wipe the database and all
> embeddings. Every restart would require re-seeding the database and re-embedding
> all documents.
>
> With volumes, those two folders are mounted from the host machine into the
> container. Data written there persists on the host disk, independent of the
> container lifecycle.
>
> **Java analogy:** Think of it like mounting an NFS or S3 bucket as a filesystem
> in a Spring Boot pod on Kubernetes. The pod is ephemeral; the data store is not.

---

**Q34. What base image would you choose for a Python AI app and why?**

> **Answer:**
> We use `python:3.11-slim` as the base image. Here's why:
>
> | Image | Size | Use case |
> |-------|------|----------|
> | `python:3.11` | ~900MB | Full Debian — includes compilers, tools. Only needed if building from source. |
> | `python:3.11-slim` | ~130MB | Minimal Debian — just enough to run Python. Our choice. |
> | `python:3.11-alpine` | ~50MB | Tiny, but many AI packages (PyTorch, numpy) don't have Alpine wheels and must compile from source — very slow build. |
>
> `slim` is the sweet spot: small image size for fast pulls and deploys,
> but compatible with all Python packages that have pre-built binary wheels
> (like PyTorch, sentence-transformers, chromadb).
>
> **Production consideration:** For production, you'd also add a non-root user
> inside the container. Running as root inside a container is a security risk
> — if the app is compromised, the attacker has root access to the container
> filesystem.

---

**Q35. How would you handle the .env file (secrets) in a Docker deployment?**

> **Answer:**
> Never bake secrets into the Docker image with `COPY .env .`. If you push
> that image to a registry, your API keys are publicly readable inside the image.
>
> Three secure approaches:
>
> **Development (what we use):**
> Mount `.env` as a file volume or pass it via `env_file` in docker-compose.yml.
> The file stays on the host — never copied into the image.
>
> **CI/CD pipelines:**
> Set environment variables directly in the pipeline (GitHub Actions secrets,
> GitLab CI variables). The container reads them from the environment at runtime.
>
> **Production:**
> Use a secrets manager — AWS Secrets Manager, HashiCorp Vault, or Kubernetes
> Secrets. The container fetches the secret at startup via an SDK call.
> No file ever touches disk.
>
> **Java analogy:** Same as externalising Spring Boot `application.properties`.
> You'd use AWS Parameter Store or Vault rather than bundling secrets in the JAR.

---

### 14.3 Scenario-Based Questions (Senior/TechLead Level)

These are the questions that separate senior candidates from mid-level.
One scenario per step — organised to match the build order.

---

#### STEP 1: Project Setup & Architecture

**Scenario 1 — Framework Choice**

> *"Your team wants to use LlamaIndex instead of LangChain. How do you evaluate this?"*

**Expected answer:**
- Both solve the same problem (LLM orchestration) with different design philosophy:
  - LangChain: general-purpose, huge ecosystem, more verbose, more control
  - LlamaIndex: specialised for RAG/document search, simpler for that use case, less flexible
- Evaluation criteria:
  1. What use cases dominate? (Document Q&A → LlamaIndex. Complex agents → LangChain)
  2. Team learning curve and existing knowledge
  3. Community support and maintenance (GitHub stars, open issues, release cadence)
  4. Integration with our existing stack (both work with ChromaDB, OpenAI, SQLite)
- **My recommendation:** LangChain for this project. We need both SQL agents and RAG, and
  LangChain's `SQLDatabase` + `create_sql_query_chain` are more mature than LlamaIndex's
  SQL tooling. Revisit if the use case shifts to document-only Q&A.

---

#### STEP 2: SQLite Database

**Scenario 2 — Schema Change in Production**

> *"Six months after launch, the HR team says: 'We need to add a leave_balance column
> to employees so the agent can answer how many days off each person has left.'
> How do you handle this without downtime?"*

**Expected answer:**
- **Never** run `DROP TABLE` or `ALTER TABLE` that removes columns in production. Additive changes only.
- Use a **schema migration tool** — for SQLAlchemy, that's `Alembic` (the Python equivalent of Flyway/Liquibase in Java):
  1. `alembic revision --autogenerate -m "add leave_balance to employees"`
  2. Review the generated migration script
  3. `alembic upgrade head` — applies the change to the live database
- The migration is **versioned** and **reversible** (`alembic downgrade -1`)
- **Re-seed or backfill:** Add a data migration step that sets `leave_balance = 20` for all existing employees as a default
- **LLM prompt impact:** The schema injected into the SQL prompt updates automatically — `SQLDatabase` reads the live schema on every run, so the LLM immediately knows about the new column
- **Java analogy:** This is exactly Flyway `V2__add_leave_balance.sql`. Same concept, different tool.

---

#### STEP 3: Vector Store

**Scenario 3 — Stale Documents**

> *"HR updates the leave policy PDF — annual leave goes from 20 days to 25 days.
> The agent is still answering '20 days' two weeks later. What went wrong and how do you fix it?"*

**Expected answer:**
- **Root cause:** ChromaDB is a persistent store. Old chunks from the previous version of the
  document are still in the collection. The new file was never re-ingested.
- **Immediate fix:**
  1. Delete the old chunks for that document by source metadata:
     `collection.delete(where={"source": "hr_leave_policy.txt"})`
  2. Re-ingest only that file with `ingest_documents(force=True, file="hr_leave_policy.txt")`
- **Process fix** (so this never happens again):
  1. Add document ingestion to the admin panel — HR uploads a file, it triggers re-embedding automatically
  2. Hash each document on ingest. On the next run, compare hashes. If a file changed, delete + re-embed.
  3. In production: store a `last_modified` timestamp per document alongside each chunk in ChromaDB metadata.
     On startup or on a nightly job, check if source files are newer than their stored timestamp.
- **Java analogy:** This is a cache invalidation problem. Your ChromaDB collection is a cache
  of the document content. When the source changes, the cache must be invalidated and rebuilt.

---

#### STEP 4: NL-to-SQL Engine

**Scenario 4 — Result Explosion**

> *"A user types: 'Show me everyone's salary'. The LLM generates correct SQL and it runs,
> but 10,000 employees' salaries come back. The UI freezes and the LLM token bill spikes. How do you fix this?"*

**Expected answer:**
- **Immediate fix:** Add a `LIMIT` guard in `validate_sql()`:
  ```python
  if "LIMIT" not in sql.upper():
      sql = sql.rstrip(";") + " LIMIT 100"
  ```
- **Prompt fix:** Add to the SQL generation prompt: "Always include LIMIT 100 unless the user
  explicitly asks for all records."
- **Security / compliance fix:** Add role-based column access. The LLM-generated SQL passes
  through a column allowlist before execution — employees can't query salary columns unless
  their role is HR_ADMIN.
- **Cost fix:** Cap the `max_tokens` in the answer synthesis call. A 10,000-row result stuffed
  into the answer prompt costs hundreds of tokens — add a row truncation step before passing
  results to the LLM.
- **Java analogy:** Same as adding a `setMaxResults(100)` on a JPA `TypedQuery`. Standard
  practice in any paginated API.

---

#### STEP 5: RAG Engine

**Scenario 5 — Hallucination**

> *"A user asks 'How many days of paternity leave do I get?' and the agent answers
> '8 weeks' but the HR document says '4 weeks'. How does this happen and how do you fix it?"*

**Expected answer:**
- **Root cause:** The LLM blended its training data with the retrieved context. GPT-4o was
  trained on internet text that mentions 8-week parental leave norms in some countries — it
  "remembered" that rather than strictly reading our chunk.
- **Fix 1 — Prompt instruction:** Add `"Answer ONLY from the documents provided. If the answer
  is not in the documents, say 'I could not find this in our HR policies.'"` This forces the
  model to stay grounded.
- **Fix 2 — Source citation:** Always return the chunk text alongside the answer so the user
  can verify. We already do this with `sources` in `rag_engine.py`.
- **Fix 3 — Increase k:** The correct chunk might be ranking 6th when k=5. Try k=7–10 with
  a reranker to keep the final context tight.
- **Fix 4 — Verification chain:** After generating the answer, run a second LLM call:
  *"Is this answer supported by the provided documents? Reply YES or NO."* If NO, return
  "I could not find a verified answer."
- **Fix 5 — Feedback loop:** The thumbs-down button surfaces exactly this failure. Flag the
  question for human review and add the corrected answer as a golden query.

---

#### STEP 6: Router

**Scenario 6 — Router Misclassification**

> *"In production you notice that every question containing the word 'project' is being
> routed to QUERY_SQL even when users are asking about 'project leave policies' (a document
> question). How do you diagnose and fix this?"*

**Expected answer:**
- **Diagnose:** Query the feedback store for all `thumbs_down` entries where `intent = QUERY_SQL`.
  Look for a pattern — are they all questions with "project" in them?
- **Root cause:** The router prompt probably says something like "SQL = questions about employees
  or projects". The word "project" in "project leave policy" triggers SQL even though the user
  wants a document.
- **Fix 1 — Improve the prompt:** Add more examples to the router prompt showing the distinction:
  ```
  "What project is Alice on?" → QUERY_SQL
  "What is the project leave allowance?" → QUERY_DOC
  "Who leads the AI project and what is the parental leave policy?" → QUERY_BOTH
  ```
  Few-shot examples are the most effective prompt improvement for classification tasks.
- **Fix 2 — Confidence + fallback:** Modify the router to also return a confidence score
  (`HIGH / LOW`). If confidence is LOW, default to `QUERY_BOTH` — slower but always correct.
- **Fix 3 — Fine-tuned classifier:** At scale, replace the LLM router with a BERT-based
  text classifier trained on your labelled feedback data. Runs in ~10ms locally vs ~500ms
  for an LLM call.
- **Java analogy:** This is exactly like improving a Spring `HandlerMapping` that's routing
  to the wrong controller. The router's condition logic needs refinement.

---

#### STEP 7: Conversation Memory

**Scenario 7 — Multi-User Session Isolation**

> *"You deploy the agent to 50 employees. You get a bug report: 'I asked about Alice's
> salary and the agent answered with something from a previous employee's conversation.'
> What went wrong?"*

**Expected answer:**
- **Root cause:** The `ConversationMemory` object is being shared across users instead of
  being isolated per session. In Streamlit this happens if memory is stored at module level
  (a global variable) instead of in `st.session_state`.
- **The fix:** Every user must get their own memory instance, keyed by a unique session ID.
  In Streamlit: `st.session_state["memory"]` is browser-session-scoped — each browser tab
  gets its own. This is already how we implemented it.
- **In an API context** (if we wrap this in FastAPI): the session ID comes from a JWT token
  or a cookie. Memory is stored in Redis keyed by `session_id`. Each request loads its own
  memory, runs, saves back.
- **Security implication:** This is not just a UX bug — it's a **data leakage vulnerability**.
  Employee A can see Employee B's conversation history. In a real enterprise system this would
  be a reportable security incident.
- **Java analogy:** This is the classic `static` field bug in a Spring singleton bean.
  Storing mutable per-request state in a `@Service` bean's field causes cross-user data leakage
  because the bean is shared. Use `ThreadLocal` or request-scoped beans instead.

---

#### STEP 8: Orchestrator

**Scenario 8 — Partial Engine Failure**

> *"Your QUERY_BOTH flow is running in production. The SQL engine times out (the database
> is under heavy load) but the RAG engine succeeds. What should the orchestrator do?"*

**Expected answer:**
- **Option A — Return partial result (best UX):** Return the RAG answer to the user with a
  note: *"I found this in our HR documents. I couldn't retrieve the employee data right now —
  please try again or rephrase your question."*
  This is better than returning nothing.
- **Option B — Retry with backoff:** Wrap the SQL engine call in `tenacity` retry logic:
  `@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))`
  Retry up to 3 times with exponential backoff before giving up.
- **Option C — Circuit breaker:** After 5 consecutive SQL timeouts, open the circuit for
  60 seconds. Route all QUERY_SQL and QUERY_BOTH requests to a graceful error message
  instead of hammering the database. Reset after 60 seconds (half-open probe).
- **Logging:** Always log which engine failed, the error message, and the latency. This is
  your signal to page the on-call engineer.
- **Java analogy:** Option B is Resilience4j `Retry`. Option C is Resilience4j `CircuitBreaker`.
  Exact same pattern — you've almost certainly used these in your Spring microservices work.

---

#### STEP 9: Feedback Loop

**Scenario 9 — Acting on Feedback Data**

> *"After one month in production, your feedback store shows: 40% thumbs-down rate on
> questions about 'parental leave'. The thumbs-down rate on all other topics is 8%.
> What is your action plan?"*

**Expected answer:**
- **Step 1 — Diagnose the retrieval:** Run the top 10 failing questions through the RAG
  engine manually. Print the actual chunks retrieved. Are they from `hr_leave_policy.txt`?
  Are they the right section?
- **Step 2 — Check the document:** Open `hr_leave_policy.txt`. Is the parental leave section
  present? Is it complete? Often the answer is that the section is too short, uses unusual
  terminology, or was added to the doc after the last ingestion.
- **Step 3 — Fix the document if needed:** If the content is wrong/missing, update the file
  and re-ingest: `collection.delete(where={"source": "hr_leave_policy.txt"})` then re-embed.
- **Step 4 — Fix the chunks:** If the parental leave answer spans two chunks (the policy text
  wraps around a chunk boundary), reduce `chunk_overlap` or increase `chunk_size` for that
  section. Or split the document into smaller single-topic files.
- **Step 5 — Add golden queries:** Write 5 verified question/answer pairs about parental leave
  and add them to the golden query store. Use as few-shot examples in the RAG prompt for this
  topic.
- **Step 6 — Track improvement:** After each fix, recheck the thumbs-down rate on that topic
  over the next week.
- **Java analogy:** This is a production incident post-mortem and remediation cycle. Same
  process as analysing Splunk error patterns, finding the root cause, fixing, and measuring.

---

#### STEP 10: Streamlit UI

**Scenario 10 — Concurrency and Scale**

> *"Your Streamlit app is working great for 5 internal users. Your manager says: 'Can we
> open this to the whole company — 500 users?' What do you say?"*

**Expected answer:**
- **Honest answer:** Streamlit is not designed for 500 concurrent users. Each Streamlit
  session runs a full Python process. At 500 users you'd need ~500 Python processes on the
  server — that's not practical.
- **Short-term mitigation:** Deploy Streamlit on a server with more RAM. Use Streamlit's
  `--server.maxUploadSize` and `--server.maxMessageSize` limits. This might stretch to 50–100
  users.
- **Proper solution — replatform the UI:**
  1. Extract the agent logic into a **FastAPI REST API**: `POST /query` → returns JSON answer
  2. Build a **React or Next.js frontend** that calls the API
  3. Deploy the API on Kubernetes (multiple replicas behind a load balancer)
  4. The Python AI logic is now stateless (memory stored in Redis by session ID) and horizontally scalable
- **Timeline pitch:** Keep Streamlit for the internal pilot. When usage justifies it, the
  FastAPI replatform is a 2-3 sprint effort. The Python agent code doesn't change — only
  the transport layer changes.
- **Java analogy:** This is exactly the journey from a Spring Boot monolith with a server-side
  Thymeleaf UI to a decoupled REST API + React SPA. Same architectural evolution.

---

#### STEP 11: Docker

**Scenario 11 — Container Crashes in Production**

> *"Your Docker container is crashing every few hours in production. The logs show
> `OOMKilled` (Out Of Memory). How do you diagnose and fix this?"*

**Expected answer:**
- **Root cause of OOMKilled:** The container exceeded its memory limit and the Linux kernel
  killed it. AI apps are memory-heavy: PyTorch loads model weights (~90 MB for MiniLM),
  ChromaDB caches vectors, and each concurrent user adds memory.
- **Diagnose:**
  - `docker stats hybrid-ai-agent` — watch live memory usage
  - `docker inspect hybrid-ai-agent` — check if a memory limit was set
  - Look at the timing: does it crash after N users or after a certain uptime? Memory leak vs. baseline too high.
- **Fix 1 — Set a memory limit that matches reality:** In `docker-compose.yml`:
  ```yaml
  deploy:
    resources:
      limits:
        memory: 4G   # Set based on observed peak usage + 20% buffer
  ```
- **Fix 2 — Lazy model loading:** Don't load the embedding model at import time.
  Load it on the first request and cache it. This reduces startup memory.
- **Fix 3 — Use CPU-only PyTorch:** The full CUDA PyTorch wheel loads NVIDIA libraries
  even when there's no GPU. Switch to `torch==2.3.1+cpu` — reduces memory footprint by ~500 MB.
- **Fix 4 — Restart policy + alerting:** The container restarts automatically (`restart: unless-stopped`
  in compose). Add a healthcheck alert so you know when it's restarting.
- **Java analogy:** This is exactly a JVM heap tuning problem. You'd set `-Xmx4g` and monitor
  with JVisualVM or Datadog. Same concept — set limits based on real measurement, not guesses.

---

### 14.4 Questions YOU Should Ask in Interviews

These signal senior-level thinking:

1. *"How is the model's output validated for correctness before it reaches the user?"*
2. *"What's the strategy for handling PII in queries? Are employee records masked?"*
3. *"How are LLM costs monitored and budgeted? Is there per-user or per-team quota management?"*
4. *"How do you evaluate whether the RAG retrieval quality is good enough? What metrics do you track?"*
5. *"Is the LLM fine-tuned on company data, or is it purely RAG-based? What's the data governance story?"*
6. *"How do you handle model version changes? If OpenAI releases GPT-5, how do you manage behaviour drift?"*

---

### 14.5 Keywords to Drop in Interviews (AI Vocabulary)

Make sure you know these terms cold. Interviewers listen for them:

| Term | What it means | Use in a sentence |
|------|--------------|-------------------|
| **RAG** | Retrieval Augmented Generation | "We use RAG to ground the LLM's answers in our HR documents" |
| **Embedding** | Text → vector of numbers | "We embed each document chunk using a sentence-transformer model" |
| **Vector similarity** | How close two embeddings are | "We use cosine similarity to find the top-k most relevant chunks" |
| **Chunking** | Splitting documents into pieces | "We chunk at 800 chars with 100-char overlap to preserve context" |
| **Grounding** | Basing answers on real data | "The agent is grounded in our database so it can't hallucinate employee names" |
| **Hallucination** | LLM making up facts | "We mitigate hallucination by always citing the source document" |
| **Temperature** | LLM creativity setting | "Temperature=0 for SQL generation ensures deterministic output" |
| **Prompt engineering** | Crafting effective LLM instructions | "We inject the schema into the prompt so the LLM knows the table structure" |
| **Chain** | Linked processing steps | "Our answer chain is: prompt → LLM → output parser" |
| **Agent** | LLM that decides which tools to call | "The orchestrator acts as an agent routing to SQL or RAG tools" |
| **Tool** | A function an agent can call | "SQL engine and RAG engine are tools registered with the orchestrator" |
| **LLM orchestration** | Coordinating multiple AI calls | "LangChain handles the orchestration of prompt building, LLM calls, and parsing" |
| **Fine-tuning** | Retraining a model on your data | "We chose RAG over fine-tuning because HR policies change quarterly" |
| **Context window** | Max tokens an LLM can process at once | "GPT-4o has a 128k token context window and we stay well under that with chunking" |
| **Semantic search** | Search by meaning, not keywords | "We use semantic search over the vector store to find policy answers" |
| **Reranker** | Re-orders retrieved chunks by relevance | "A cross-encoder reranker (BGE-Reranker) improves precision over the top-k results" |
| **LCEL** | LangChain Expression Language (the pipe syntax) | "LCEL lets us compose chains declaratively using the pipe operator" |

---

*Last updated: 2026-07-01*
*This document is updated at the end of each working session.*
