"""
connection.py — Database Connection Setup
==========================================
WHAT THIS FILE DOES:
    Creates and manages the connection to our SQLite database.
    Every other module imports `engine` and `get_session` from here.

KEY CONCEPTS:
    - Engine    : The "connection string" — knows WHERE the database is
                  and HOW to talk to it. Created once at startup.
    - Session   : A temporary workspace for one unit of work (a query
                  or a batch of inserts). Think of it like opening a
                  spreadsheet, making changes, then saving and closing.
    - SessionLocal: A factory (blueprint) for creating new Sessions.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ── Load environment variables from .env ─────────────────────────────────────
# load_dotenv() reads the .env file and puts all KEY=VALUE pairs into
# os.environ so we can access them with os.getenv().
load_dotenv()

# ── Resolve the database file path ────────────────────────────────────────────
# os.getenv("SQLITE_DB_PATH") reads from .env, e.g. "data/db/company.db"
# If .env doesn't exist yet, we fall back to the default path.
# Path(...).resolve() converts a relative path → absolute path.
# This is important because Python scripts can be run from different
# working directories, and we always want to find the same .db file.
_DB_PATH = Path(
    os.getenv("SQLITE_DB_PATH", "data/db/company.db")
).resolve()

# ── Ensure the parent directory exists ────────────────────────────────────────
# SQLite will create the .db file automatically, but it will NOT create
# the parent folders. We must do that ourselves.
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Create the SQLAlchemy Engine ──────────────────────────────────────────────
# The engine is the core interface to the database.
# "sqlite:///" is the connection string prefix for SQLite.
# check_same_thread=False is needed for SQLite when used in web apps
# (like Streamlit) where multiple threads may access the DB.
engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,   # Set echo=True if you want to see every SQL query printed
)

# ── Create the Session Factory ────────────────────────────────────────────────
# SessionLocal is NOT a session itself — it's a blueprint for creating sessions.
# autocommit=False : Changes are NOT saved until you explicitly call session.commit()
# autoflush=False  : Changes are NOT sent to DB until you call session.flush() or commit()
# This gives us full control over when data is written.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Base Class for all Models ─────────────────────────────────────────────────
# All our table classes (in models.py) will inherit from this Base.
# SQLAlchemy uses Base to track every table definition so it can
# create/drop them in the right order.
class Base(DeclarativeBase):
    """
    Parent class for all ORM models (table definitions).
    Any class that inherits from Base will be treated as a database table.
    """
    pass


# ── Helper: get_session() ─────────────────────────────────────────────────────
# This is a Python "generator function" (notice the `yield` keyword).
# It's used as a context manager — it opens a session, hands it over,
# and guarantees the session is closed afterwards even if an error occurs.
#
# Usage example:
#   with get_session() as session:
#       results = session.query(Employee).all()
#   # session is automatically closed here, even if an error happened
def get_session():
    """
    Yields a database session and ensures it is closed after use.
    Use this with a 'with' statement for safe session management.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()   # Save all changes if everything went fine
    except Exception:
        session.rollback() # Undo all changes if something went wrong
        raise              # Re-raise the exception so caller knows about it
    finally:
        session.close()    # Always close the session (release the connection)
