"""
Continuous CLI chat: login with email + password → Employee or HR (admin_rights).
Then user input → Help Service (LLM + MCP) → response.
Type 'quit' or 'exit' to stop; 'logout' to sign out (clears flows etc.) and log in again.
"""
import sys
import os

# Ensure Project3 is on path and load config first
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import config  # noqa: F401 - load .env and LangSmith
from mcp_client import MCPClient
from HelpServiceState import run_help_service


def login():
    """Prompt for email and password; return (user_email, admin_rights) or (None, False)."""
    client = MCPClient()
    max_attempts = 3
    for attempt in range(max_attempts):
        email = input("Email: ").strip()
        if not email:
            print("Email cannot be empty.")
            continue
        password = input("Password: ").strip()
        if not password:
            print("Password cannot be empty.")
            continue
        user, admin_rights = client.authenticate(email, password)
        if user:
            return user.get("email") or user.get("name") or email, admin_rights
        print("Invalid email or password. Try again.")
    return None, False


def main():
    while True:
        # Fresh session: clear screen
        os.system("cls" if os.name == "nt" else "clear")

        print("=" * 60)
        print("  HR Help Service – CLI (Project3)")
        print("  Login with email + password.")
        print("  Commands: 'logout' = sign out & log in again | 'quit' or 'exit' = stop.")
        print("=" * 60)
        print()

        user_email, admin_rights = login()
        if user_email is None:
            print("Too many failed attempts. Exiting.")
            return
        role = "HR (admin)" if admin_rights else "Employee"
        print(f"Logged in as {user_email} [{role}]\n")

        last_subject_employee = None  # single employee from previous message (for "her", "his", etc.)
        last_subject_employee_names = None  # when previous response had multiple employees (e.g. multiple Sarahs)
        last_subject_employee_infos = None  # list of {"id", "name"} for disambiguation by employee ID
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                return
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q", "bye"):
                print("Goodbye.")
                return
            if user_input.lower() in ("logout", "log out", "signout", "sign out"):
                os.system("cls" if os.name == "nt" else "clear")
                print("Logged out. You can log in again.")
                print()
                break

            try:
                response, execution_path, subject_employee, subject_employee_names, subject_employee_infos = run_help_service(
                    user_email, user_input, admin_rights=admin_rights,
                    context_employee_name=last_subject_employee,
                    context_employee_names=last_subject_employee_names,
                    context_employee_infos=last_subject_employee_infos,
                )
                if subject_employee_infos:
                    last_subject_employee_infos = subject_employee_infos
                    last_subject_employee_names = [i.get("name") for i in subject_employee_infos if i.get("name")]
                    last_subject_employee = None
                elif subject_employee_names:
                    last_subject_employee_names = subject_employee_names
                    last_subject_employee_infos = None
                    last_subject_employee = None
                elif subject_employee:
                    last_subject_employee = subject_employee
                    last_subject_employee_names = None
                    last_subject_employee_infos = None
                print("\nAssistant:", response)
                if execution_path:
                    flow_str = " → ".join(execution_path)
                    print("\n[Flow used]", flow_str)
                print()
            except Exception as e:
                print(f"\nError: {e}\n")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
