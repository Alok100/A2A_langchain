"""
Run full DB setup: creates employees + attendance tables, employee_code, trigger, seed data.
Uses .env for connection (PGHOST, PGUSER, PGPASSWORD, PGDATABASE).
Run from Project3: python setup_db.py

Passwords: James Garcia (HR) = 11111111; all others = 00000000
"""
import sys
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import config  # noqa: F401 - load .env
from mcp_client import MCPClient


def _split_sql(sql_content: str):
    """Split SQL into statements, respecting $$ ... $$ blocks. Keeps full statements."""
    statements = []
    in_dollar = False
    current = []
    for line in sql_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--") and not in_dollar:
            continue
        if "$$" in line:
            in_dollar = not in_dollar
        current.append(line)
        if not in_dollar and stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)
    return statements


def run_setup():
    dbname = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB", "employees_db")
    client = MCPClient()
    azure_mcp = client.azure_mcp

    sql_path = os.path.join(SCRIPT_DIR, "setup_db.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    statements = _split_sql(sql_content)
    print(f"Running full DB setup on database: {dbname}")
    print(f"Statements to run: {len(statements)}")
    for i, stmt in enumerate(statements, 1):
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            azure_mcp.update_values(dbname, stmt)
            print(f"  [{i}] OK")
        except Exception as e:
            err = str(e).strip()
            if "already exists" in err or "duplicate key" in err.lower():
                print(f"  [{i}] Skip (already exists): {err[:70]}...")
            else:
                print(f"  [{i}] Error: {e}")
                raise
    print("Setup finished. Run: python show_db.py")


if __name__ == "__main__":
    run_setup()
