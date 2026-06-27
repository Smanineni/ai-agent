"""
models.py — Database Table Definitions (Schema)
================================================
WHAT THIS FILE DOES:
    Defines the structure of every table in our database using
    SQLAlchemy's ORM (Object Relational Mapper).

HOW IT WORKS:
    Each Python class below = one database table.
    Each class attribute decorated with `mapped_column` = one column.
    SQLAlchemy reads these classes and creates the real SQL tables.

    Python class Employee  →  SQL table "employees"
    Python class Project   →  SQL table "projects"
    Python class EmployeeProject → SQL table "employee_projects"

TABLES WE'RE BUILDING:
    ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
    │  employees   │────<│ employee_projects │>────│   projects   │
    └──────────────┘     └──────────────────┘     └──────────────┘
    Many-to-many relationship via junction table
"""

from datetime import date
from typing import Optional, List

from sqlalchemy import String, Integer, Float, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Base from our connection module — all models must inherit from it
from app.database.connection import Base


# ═══════════════════════════════════════════════════════════════════
# TABLE 1: employees
# ═══════════════════════════════════════════════════════════════════
class Employee(Base):
    """
    Represents one row in the 'employees' table.

    COLUMN TYPES explained:
        String(100) = text up to 100 characters
        Float       = decimal number (for salary)
        Date        = a calendar date (no time)
        Optional    = the column can be NULL (empty)
    """

    # __tablename__ tells SQLAlchemy what to name the actual SQL table
    __tablename__ = "employees"

    # ── Primary Key ────────────────────────────────────────────────
    # Every table needs a primary key — a unique ID for each row.
    # primary_key=True means this column uniquely identifies each row.
    # autoincrement=True means SQLite assigns 1, 2, 3... automatically.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Required columns (NOT NULL) ────────────────────────────────
    # Mapped[str] without Optional means this field cannot be empty.
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)

    # ── Optional columns (can be NULL) ─────────────────────────────
    # Optional[str] means this column can hold NULL in the database.
    manager_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationship (not a real column!) ──────────────────────────
    # This tells SQLAlchemy: "an Employee can have many EmployeeProject links."
    # back_populates="employee" connects this to the same attribute in
    # the EmployeeProject class, creating a two-way link.
    # This is NOT a database column — it only exists in Python memory.
    assignments: Mapped[List["EmployeeProject"]] = relationship(
        "EmployeeProject",
        back_populates="employee",
    )

    def __repr__(self) -> str:
        # __repr__ controls what you see when you print an Employee object
        return f"<Employee(id={self.id}, name='{self.name}', dept='{self.department}')>"


# ═══════════════════════════════════════════════════════════════════
# TABLE 2: projects
# ═══════════════════════════════════════════════════════════════════
class Project(Base):
    """
    Represents one row in the 'projects' table.

    STATUS values (controlled vocabulary):
        'active'    — project is currently running
        'completed' — project is finished
        'on_hold'   — project is paused
        'planning'  — project not started yet
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)

    # Text type is used for longer descriptions (no length limit, unlike String)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="planning",   # Default value if not specified
    )
    budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationship: a Project can have many EmployeeProject assignments
    assignments: Mapped[List["EmployeeProject"]] = relationship(
        "EmployeeProject",
        back_populates="project",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


# ═══════════════════════════════════════════════════════════════════
# TABLE 3: employee_projects  (junction / association table)
# ═══════════════════════════════════════════════════════════════════
class EmployeeProject(Base):
    """
    Junction table linking employees to projects (many-to-many).

    WHY DO WE NEED THIS TABLE?
        An employee can work on MANY projects.
        A project can have MANY employees.
        SQL cannot store "arrays" of values in one column.
        So we create a separate table where each row is one assignment:

        employee_id=1, project_id=3  →  Alice works on Project Alpha
        employee_id=1, project_id=5  →  Alice ALSO works on Project Beta
        employee_id=2, project_id=3  →  Bob ALSO works on Project Alpha

    COMPOSITE PRIMARY KEY:
        Instead of a single 'id' column, we use the combination of
        (employee_id + project_id) as the primary key. This guarantees
        the same employee can't be assigned to the same project twice.
    """

    __tablename__ = "employee_projects"

    # ── Composite Primary Key ───────────────────────────────────────
    # ForeignKey("employees.id") means: this column MUST match an id
    # that already exists in the employees table. If you try to insert
    # an employee_id that doesn't exist — SQLite will reject it.
    # This is called a "referential integrity constraint."
    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id"),
        primary_key=True,   # Part 1 of composite primary key
    )
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        primary_key=True,   # Part 2 of composite primary key
    )

    # ── Extra columns on the junction table ────────────────────────
    # Junction tables can carry extra data about the relationship itself.
    role_on_project: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hours_allocated: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Back-references ─────────────────────────────────────────────
    # These connect back to the Employee and Project classes above.
    # With these, you can do: assignment.employee.name  (no extra query!)
    employee: Mapped["Employee"] = relationship("Employee", back_populates="assignments")
    project: Mapped["Project"] = relationship("Project", back_populates="assignments")

    def __repr__(self) -> str:
        return (
            f"<EmployeeProject("
            f"employee_id={self.employee_id}, "
            f"project_id={self.project_id}, "
            f"role='{self.role_on_project}')>"
        )
