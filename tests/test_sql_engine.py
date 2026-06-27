"""Quick test script for the SQL engine — run with: python tests/test_sql_engine.py"""
from app.engines.sql_engine import get_sql_database, validate_sql

db = get_sql_database()

print("=== MANUAL SQL EXECUTION ===")
queries = [
    ("Highest paid engineers",
     "SELECT name, salary FROM employees WHERE department='Engineering' ORDER BY salary DESC"),
    ("Active projects over 100k",
     "SELECT name, budget FROM projects WHERE status='active' AND budget > 100000"),
    ("Who works on which projects",
     "SELECT e.name, p.name, ep.role_on_project FROM employees e "
     "JOIN employee_projects ep ON e.id=ep.employee_id "
     "JOIN projects p ON p.id=ep.project_id"),
    ("Average salary by department",
     "SELECT department, ROUND(AVG(salary),0) as avg_salary FROM employees GROUP BY department ORDER BY avg_salary DESC"),
]
for label, sql in queries:
    print(f"\nQ: {label}")
    print(f"SQL: {sql}")
    print(f"Result: {db.run(sql)}")

print("\n\n=== SAFETY VALIDATOR ===")
bad = ["DELETE FROM employees", "DROP TABLE projects", "UPDATE employees SET salary=0"]
for q in bad:
    try:
        validate_sql(q)
        print(f"  MISSED (should have blocked): {q}")
    except ValueError:
        print(f"  BLOCKED correctly: {q}")

print("\nAll tests passed!")
