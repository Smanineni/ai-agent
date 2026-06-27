"""
seed.py — Create Tables and Populate with Seed Data
=====================================================
WHAT THIS FILE DOES:
    1. Creates all database tables (if they don't exist yet)
    2. Checks if data already exists (so running it twice doesn't duplicate)
    3. Inserts realistic fake employees, projects, and assignments

HOW TO RUN THIS FILE:
    From the project root, with venv activated:
        python -m app.database.seed

WHY SEED DATA MATTERS:
    Our AI agent needs data to query. Without it, every SQL query
    returns empty results and the LLM has nothing to reason about.
    Good seed data should cover multiple departments, salary ranges,
    project statuses, and date ranges so our NL-to-SQL queries are
    interesting and varied.
"""

from datetime import date

from loguru import logger   # Better logging than print() — shows timestamps

# Import the engine and Base from connection.py
from app.database.connection import engine, Base, get_session

# Import all three model classes — Base needs to "see" them before
# calling create_all(), otherwise it won't know which tables to create.
from app.database.models import Employee, Project, EmployeeProject


# ═══════════════════════════════════════════════════════════════════
# STEP 1: Create all tables
# ═══════════════════════════════════════════════════════════════════
def create_tables() -> None:
    """
    Creates all tables defined in models.py inside the SQLite database.

    Base.metadata.create_all(engine) does the following:
      - Looks at every class that inherits from Base (Employee, Project, etc.)
      - Generates the SQL CREATE TABLE statements
      - Runs them against the database
      - Skips tables that already exist (safe to call multiple times)
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.success("Tables created (or already exist).")


# ═══════════════════════════════════════════════════════════════════
# STEP 2: Define seed data
# ═══════════════════════════════════════════════════════════════════

# Each dictionary here represents ONE row in the employees table.
# The keys match the column names defined in models.py.
EMPLOYEES = [
    # ── Engineering Department ──────────────────────────────────────
    {
        "name": "Alice Sharma",
        "email": "alice.sharma@company.com",
        "department": "Engineering",
        "role": "Senior Software Engineer",
        "salary": 115000.0,
        "hire_date": date(2021, 3, 15),
        "manager_name": "David Park",
        "location": "New York",
    },
    {
        "name": "Marcus Williams",
        "email": "marcus.williams@company.com",
        "department": "Engineering",
        "role": "Software Engineer",
        "salary": 92000.0,
        "hire_date": date(2022, 8, 1),
        "manager_name": "David Park",
        "location": "New York",
    },
    {
        "name": "Priya Nair",
        "email": "priya.nair@company.com",
        "department": "Engineering",
        "role": "DevOps Engineer",
        "salary": 105000.0,
        "hire_date": date(2020, 5, 20),
        "manager_name": "David Park",
        "location": "Austin",
    },
    {
        "name": "David Park",
        "email": "david.park@company.com",
        "department": "Engineering",
        "role": "Engineering Manager",
        "salary": 145000.0,
        "hire_date": date(2018, 1, 10),
        "manager_name": None,         # David is a top-level manager
        "location": "New York",
    },
    # ── Human Resources Department ──────────────────────────────────
    {
        "name": "Sandra Torres",
        "email": "sandra.torres@company.com",
        "department": "HR",
        "role": "HR Manager",
        "salary": 88000.0,
        "hire_date": date(2019, 7, 1),
        "manager_name": None,
        "location": "Chicago",
    },
    {
        "name": "James Okafor",
        "email": "james.okafor@company.com",
        "department": "HR",
        "role": "HR Specialist",
        "salary": 62000.0,
        "hire_date": date(2023, 2, 14),
        "manager_name": "Sandra Torres",
        "location": "Chicago",
    },
    # ── Sales Department ─────────────────────────────────────────────
    {
        "name": "Rachel Kim",
        "email": "rachel.kim@company.com",
        "department": "Sales",
        "role": "Sales Director",
        "salary": 130000.0,
        "hire_date": date(2017, 9, 5),
        "manager_name": None,
        "location": "San Francisco",
    },
    {
        "name": "Tom Nguyen",
        "email": "tom.nguyen@company.com",
        "department": "Sales",
        "role": "Account Executive",
        "salary": 75000.0,
        "hire_date": date(2022, 11, 1),
        "manager_name": "Rachel Kim",
        "location": "San Francisco",
    },
    # ── Finance Department ───────────────────────────────────────────
    {
        "name": "Elena Petrov",
        "email": "elena.petrov@company.com",
        "department": "Finance",
        "role": "Finance Manager",
        "salary": 120000.0,
        "hire_date": date(2016, 4, 18),
        "manager_name": None,
        "location": "New York",
    },
    {
        "name": "Chris Andersen",
        "email": "chris.andersen@company.com",
        "department": "Finance",
        "role": "Financial Analyst",
        "salary": 83000.0,
        "hire_date": date(2021, 10, 25),
        "manager_name": "Elena Petrov",
        "location": "New York",
    },
]

PROJECTS = [
    {
        "name": "AI-Powered Customer Support",
        "department": "Engineering",
        "description": "Build an AI chatbot to handle tier-1 customer support tickets automatically.",
        "status": "active",
        "budget": 250000.0,
        "start_date": date(2024, 1, 15),
        "end_date": date(2024, 12, 31),
    },
    {
        "name": "Employee Onboarding Redesign",
        "department": "HR",
        "description": "Redesign the employee onboarding process to reduce time-to-productivity.",
        "status": "completed",
        "budget": 45000.0,
        "start_date": date(2023, 6, 1),
        "end_date": date(2023, 11, 30),
    },
    {
        "name": "Q4 Enterprise Sales Push",
        "department": "Sales",
        "description": "Targeted campaign to close enterprise deals before Q4 deadline.",
        "status": "active",
        "budget": 180000.0,
        "start_date": date(2024, 10, 1),
        "end_date": date(2024, 12, 31),
    },
    {
        "name": "Cloud Infrastructure Migration",
        "department": "Engineering",
        "description": "Migrate all on-premise services to AWS cloud infrastructure.",
        "status": "on_hold",
        "budget": 500000.0,
        "start_date": date(2024, 3, 1),
        "end_date": date(2025, 3, 1),
    },
    {
        "name": "Annual Budget Forecast 2025",
        "department": "Finance",
        "description": "Prepare department-level budget forecasts and variance analysis for 2025.",
        "status": "planning",
        "budget": 20000.0,
        "start_date": date(2024, 11, 1),
        "end_date": date(2025, 1, 31),
    },
]

# Each dict = one row in employee_projects.
# We use names here for readability — they'll be resolved to IDs at insert time.
ASSIGNMENTS = [
    # AI Customer Support project
    {"employee": "Alice Sharma",   "project": "AI-Powered Customer Support",  "role": "Tech Lead",        "hours": 32.0},
    {"employee": "Marcus Williams","project": "AI-Powered Customer Support",  "role": "Developer",        "hours": 40.0},
    {"employee": "Priya Nair",     "project": "AI-Powered Customer Support",  "role": "DevOps",           "hours": 20.0},
    # Onboarding project
    {"employee": "Sandra Torres",  "project": "Employee Onboarding Redesign", "role": "Project Owner",    "hours": 25.0},
    {"employee": "James Okafor",   "project": "Employee Onboarding Redesign", "role": "Coordinator",      "hours": 38.0},
    # Sales Push
    {"employee": "Rachel Kim",     "project": "Q4 Enterprise Sales Push",     "role": "Director",         "hours": 20.0},
    {"employee": "Tom Nguyen",     "project": "Q4 Enterprise Sales Push",     "role": "AE",               "hours": 40.0},
    # Cloud Migration
    {"employee": "Priya Nair",     "project": "Cloud Infrastructure Migration","role": "Lead DevOps",     "hours": 40.0},
    {"employee": "David Park",     "project": "Cloud Infrastructure Migration","role": "Sponsor",         "hours": 8.0},
    # Budget Forecast
    {"employee": "Elena Petrov",   "project": "Annual Budget Forecast 2025",  "role": "Owner",            "hours": 30.0},
    {"employee": "Chris Andersen", "project": "Annual Budget Forecast 2025",  "role": "Analyst",          "hours": 40.0},
]


# ═══════════════════════════════════════════════════════════════════
# STEP 3: Insert seed data
# ═══════════════════════════════════════════════════════════════════
def seed_employees(session) -> dict:
    """
    Inserts all employees into the DB and returns a name→object mapping.
    Returns a dict like: {"Alice Sharma": <Employee object>, ...}
    """
    # Check if data already exists — avoid duplicates on re-runs
    if session.query(Employee).count() > 0:
        logger.info("Employees already seeded — skipping.")
        # Still return the existing mapping so seed_assignments() can use it
        return {emp.name: emp for emp in session.query(Employee).all()}

    logger.info("Seeding employees...")
    name_to_obj = {}

    for data in EMPLOYEES:
        # Create an Employee Python object from the dict
        emp = Employee(**data)
        # `session.add(emp)` stages the insert — nothing is written to DB yet
        session.add(emp)
        name_to_obj[emp.name] = emp

    # `session.flush()` sends the SQL INSERT statements to the DB
    # but does NOT commit. This assigns auto-increment IDs to each employee
    # so we can reference them in employee_projects below.
    session.flush()
    logger.success(f"Inserted {len(EMPLOYEES)} employees.")
    return name_to_obj


def seed_projects(session) -> dict:
    """
    Inserts all projects and returns a name→object mapping.
    """
    if session.query(Project).count() > 0:
        logger.info("Projects already seeded — skipping.")
        return {proj.name: proj for proj in session.query(Project).all()}

    logger.info("Seeding projects...")
    name_to_obj = {}

    for data in PROJECTS:
        proj = Project(**data)
        session.add(proj)
        name_to_obj[proj.name] = proj

    session.flush()
    logger.success(f"Inserted {len(PROJECTS)} projects.")
    return name_to_obj


def seed_assignments(session, employees: dict, projects: dict) -> None:
    """
    Inserts employee-project assignments using the name→object mappings.
    """
    if session.query(EmployeeProject).count() > 0:
        logger.info("Assignments already seeded — skipping.")
        return

    logger.info("Seeding project assignments...")

    for data in ASSIGNMENTS:
        # Look up the actual Employee and Project objects by name
        emp = employees[data["employee"]]
        proj = projects[data["project"]]

        assignment = EmployeeProject(
            employee_id=emp.id,
            project_id=proj.id,
            role_on_project=data["role"],
            hours_allocated=data["hours"],
        )
        session.add(assignment)

    session.flush()
    logger.success(f"Inserted {len(ASSIGNMENTS)} assignments.")


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
def run_seed() -> None:
    """
    Orchestrates the full seed process:
    1. Create tables
    2. Open a session
    3. Insert employees, projects, assignments
    4. Commit everything in one transaction
    """
    create_tables()

    # get_session() is a generator — we use next() to get the session object.
    # In a web app we'd use it as `with get_session() as s:` but here
    # we drive it manually so we can pass the session across all seed functions.
    session_gen = get_session()
    session = next(session_gen)   # Opens the session

    try:
        employees = seed_employees(session)
        projects = seed_projects(session)
        seed_assignments(session, employees, projects)
        session.commit()
        logger.success("Database seeded successfully!")
        logger.info(f"Database file: data/db/company.db")
    except Exception as e:
        session.rollback()
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        session.close()


# ── Allow running as a script: python -m app.database.seed ────────
if __name__ == "__main__":
    run_seed()
