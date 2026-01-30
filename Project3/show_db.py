"""
Show what's in the DB: employees and (optionally) attendance.
Uses same MCP as the CLI. Run: python show_db.py
"""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import config  # noqa: F401 - load .env
from mcp_client import MCPClient


def main():
    print("Connecting to DB via MCP...")
    client = MCPClient()
    print(f"Database: {client.dbname}\n")

    # Employees
    employees = client.query("employees", None)
    if not employees:
        print("No employees in DB. Run Project2/SettingUp_DB.py to create and seed the DB.")
        return
    print("=" * 105)
    print("EMPLOYEES (use exact name, email, or Employee ID in CLI)")
    print("=" * 105)
    print(f"{'No.':<5} {'Employee ID':<12} {'Name':<22} {'Email':<28} {'Dept':<10} {'License':<8} {'Join':<12} {'Leave':<5}")
    print("-" * 105)
    for e in employees:
        email = e.get('email') or (e.get('name', '').lower().replace(' ', '.') + '@gmail.com')
        no_ = e.get('id', '')
        company_id = e.get('company_id', '') or str(100000 + (no_ if no_ else 0))[:6]
        print(f"{no_:<5} {company_id:<12} {e.get('name', ''):<22} {email:<28} {(e.get('department') or 'N/A'):<10} "
              f"{e.get('license', ''):<8} {(e.get('join_date') or 'N/A'):<12} {e.get('leave_days', 0):<5}")
    print("=" * 95)
    print("Passwords: HR (James Garcia) = 11111111; all others = 00000000. (Not shown in CLI.)")
    print("Tip: In CLI, enter name exactly as above or use email.\n")

    # Attendance (last 10)
    attendance = client.query("attendance", None)
    if attendance:
        print("ATTENDANCE (last 15 records)")
        print("-" * 75)
        for a in attendance[:15]:
            print(f"  Emp {a.get('emp_id')} | {a.get('date')} | {a.get('check_in')} - {a.get('check_out')} | {a.get('employee_name')}")
        print()
    else:
        print("No attendance records yet.\n")


if __name__ == "__main__":
    main()
