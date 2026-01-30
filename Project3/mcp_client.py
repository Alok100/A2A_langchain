import sys
import os
import json
from typing import Dict, Any

# Add path to Azure PostgreSQL MCP (parent of Project3 = A2A_langchain)
azure_mcp_path = os.path.join(os.path.dirname(__file__), '..', 'azure-postgresql-mcp', 'src')
sys.path.insert(0, azure_mcp_path)

from azure_postgresql_mcp import AzurePostgreSQLMCP

# ============================================================================
# AZURE POSTGRESQL MCP CLIENT WRAPPER (same as Project2)
# ============================================================================

class MCPClient:
    """Azure PostgreSQL MCP client wrapper"""
    
    def __init__(self):
        """Initialize Azure PostgreSQL MCP client"""
        self.azure_mcp = AzurePostgreSQLMCP()
        self.azure_mcp.init()
        self.dbname = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB", "company_db")
    
    def _build_employee_query(self, filters: Dict[str, Any] = None) -> str:
        # id = internal row number (1, 2, 3...); company_id = 6-digit company Employee ID (100001, 100002...)
        # company_id is computed from id; run migrations/add_employee_code.sql to add employee_code column for storage
        sql = """
            SELECT employee_id as id,
                   COALESCE(employee_code, LPAD((100000 + employee_id)::text, 6, '0'))::text as company_id,
                   employee_name as name,
                   department,
                   CASE WHEN license_valid = 1 THEN 'PRO' ELSE 'EXPIRED' END as license,
                   date_of_joining::text as join_date,
                   leave_available as leave_days,
                   license_valid,
                   COALESCE(email, '') as email
            FROM employees
        """
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if key == "id":
                    where_clauses.append(f"employee_id = {value}")
                elif key == "company_id" or key == "employee_code":
                    code = str(value).strip().replace("'", "''")
                    if code.isdigit():
                        where_clauses.append(f"COALESCE(employee_code, LPAD((100000 + employee_id)::text, 6, '0')) = LPAD('{code}', 6, '0')")
                    else:
                        where_clauses.append(f"employee_code = '{code}'")
                elif key == "email":
                    escaped_value = str(value).replace("'", "''")
                    where_clauses.append(f"(LOWER(COALESCE(email, '')) = LOWER('{escaped_value}') OR LOWER(employee_name) = LOWER('{escaped_value}'))")
                elif key == "name":
                    escaped_value = str(value).replace("'", "''")
                    where_clauses.append(f"LOWER(employee_name) = LOWER('{escaped_value}')")
                elif key == "name_contains":
                    escaped_value = str(value).replace("'", "''").replace("%", "\\%").replace("_", "\\_")
                    where_clauses.append(f"LOWER(employee_name) LIKE LOWER('%{escaped_value}%')")
                else:
                    escaped_value = str(value).replace("'", "''")
                    where_clauses.append(f"{key} = '{escaped_value}'")
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        return sql
    
    def _build_attendance_query(self, filters: Dict[str, Any] = None) -> str:
        sql = """
            SELECT attendance_id as id,
                   employee_id as emp_id,
                   (SELECT employee_name FROM employees WHERE employee_id = a.employee_id) as employee_name,
                   date::text as date,
                   check_in_time::text as check_in,
                   check_out_time::text as check_out
            FROM attendance a
        """
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if key == "emp_id":
                    where_clauses.append(f"employee_id = {value}")
                elif key == "date":
                    escaped_value = str(value).replace("'", "''")
                    where_clauses.append(f"date = '{escaped_value}'")
                else:
                    escaped_value = str(value).replace("'", "''")
                    where_clauses.append(f"{key} = '{escaped_value}'")
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        return sql
    
    def _parse_query_result(self, result_json: str) -> list:
        try:
            result = json.loads(result_json)
            columns_str = result.get("columns", "[]")
            rows_str = result.get("rows", "")
            import ast
            try:
                columns = ast.literal_eval(columns_str) if isinstance(columns_str, str) else columns_str
            except Exception:
                columns = [col.strip() for col in columns_str.strip("[]").split(",")]
            results = []
            if rows_str:
                rows = rows_str.split("),(")
                for i, row_str in enumerate(rows):
                    row_str = row_str.strip()
                    if i == 0:
                        row_str = row_str.lstrip("(")
                    if i == len(rows) - 1:
                        row_str = row_str.rstrip(")")
                    try:
                        row_values = ast.literal_eval(f"({row_str})")
                        row_dict = dict(zip(columns, row_values))
                        results.append(row_dict)
                    except Exception:
                        continue
            return results
        except Exception as e:
            print(f"[ERROR] Failed to parse query result: {e}")
            return []
    
    def query(self, table: str, filters: Dict[str, Any] = None) -> list:
        try:
            if table == "employees":
                sql = self._build_employee_query(filters)
            elif table == "attendance":
                sql = self._build_attendance_query(filters)
            else:
                return []
            result_json = self.azure_mcp.query_data(self.dbname, sql)
            if not result_json:
                return []
            results = self._parse_query_result(result_json)
            if table == "employees":
                for emp_dict in results:
                    emp_dict["verified"] = True
                    emp_dict["active"] = True
                    emp_dict["license_active"] = emp_dict.get("license_valid", 0) == 1
                    emp_dict["license_expired"] = emp_dict.get("license_valid", 0) == 0
                    if not emp_dict.get("email"):
                        name = emp_dict.get("name", "")
                        emp_dict["email"] = name.lower().replace(" ", ".") + "@company.com"
            return results
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            return []

    def authenticate(self, email: str, password: str):
        """
        Authenticate by email and password. Returns (user_dict, admin_rights).
        user_dict has id, name, email, department, etc. (no password).
        admin_rights True = HR (password 11111111), False = employee.
        Returns (None, False) if invalid.
        """
        try:
            escaped = str(email).strip().replace("'", "''")
            sql = f"""
                SELECT employee_id, employee_name, COALESCE(email,'') as email, department,
                       license_valid, date_of_joining::text as join_date, leave_available,
                       COALESCE(password,'') as password
                FROM employees
                WHERE LOWER(COALESCE(email,'')) = LOWER('{escaped}')
                   OR LOWER(employee_name) = LOWER('{escaped}')
            """
            result_json = self.azure_mcp.query_data(self.dbname, sql)
            if not result_json:
                return None, False
            rows = self._parse_query_result(result_json)
            if not rows:
                return None, False
            row = rows[0]
            # PostgreSQL may return lowercase column names
            def _r(k, default=None):
                return row.get(k) or row.get(k.lower() if k else k) or default
            stored_password = (str(_r("password") or "")).strip()
            if stored_password != password.strip():
                return None, False
            admin_rights = stored_password == "11111111"
            user = {
                "id": _r("employee_id") or _r("id"),
                "name": _r("employee_name") or _r("name"),
                "email": _r("email") or "",
                "department": _r("department"),
                "license_valid": _r("license_valid", 0),
                "join_date": _r("join_date"),
                "leave_days": _r("leave_available") or _r("leave_days", 0),
                "license": "PRO" if (_r("license_valid") or 0) == 1 else "EXPIRED",
                "verified": True,
                "active": True,
                "license_active": (_r("license_valid") or 0) == 1,
                "license_expired": (_r("license_valid") or 0) == 0,
            }
            if not user.get("email"):
                user["email"] = (user.get("name") or "").lower().replace(" ", ".") + "@gmail.com"
            return user, admin_rights
        except Exception as e:
            print(f"[ERROR] Auth failed: {e}")
            return None, False

    def update(self, table: str, record_id: int, updates: Dict[str, Any]) -> bool:
        try:
            if table == "employees":
                field_mapping = {"leave_days": "leave_available", "name": "employee_name", "license": "license_valid"}
                set_clauses = []
                for key, value in updates.items():
                    db_field = field_mapping.get(key, key)
                    if isinstance(value, str):
                        escaped = value.replace("'", "''")
                        set_clauses.append(f"{db_field} = '{escaped}'")
                    else:
                        set_clauses.append(f"{db_field} = {value}")
                if set_clauses:
                    sql = f"UPDATE employees SET {', '.join(set_clauses)} WHERE employee_id = {record_id}"
                    self.azure_mcp.update_values(self.dbname, sql)
                    return True
            elif table == "attendance":
                field_mapping = {"check_in": "check_in_time", "check_out": "check_out_time"}
                set_clauses = []
                for key, value in updates.items():
                    db_field = field_mapping.get(key, key)
                    if isinstance(value, str):
                        escaped = value.replace("'", "''")
                        set_clauses.append(f"{db_field} = '{escaped}'")
                    else:
                        set_clauses.append(f"{db_field} = {value}")
                if set_clauses:
                    sql = f"UPDATE attendance SET {', '.join(set_clauses)} WHERE attendance_id = {record_id}"
                    self.azure_mcp.update_values(self.dbname, sql)
                    return True
            return False
        except Exception as e:
            print(f"[ERROR] Update failed: {e}")
            return False
    
    def insert(self, table: str, record: Dict[str, Any]) -> bool:
        try:
            if table == "employees":
                sql = """
                    INSERT INTO employees (employee_id, employee_name, department, license_valid, date_of_joining, leave_available)
                    VALUES ({id}, '{name}', '{department}', {license}, '{join_date}', {leave_days})
                """.format(
                    id=record.get("id", "NULL"),
                    name=str(record.get("name", "")).replace("'", "''"),
                    department=str(record.get("department", "")).replace("'", "''"),
                    license=1 if record.get("license_active", True) else 0,
                    join_date=record.get("join_date", ""),
                    leave_days=record.get("leave_days", 0)
                )
                self.azure_mcp.update_values(self.dbname, sql)
                return True
            elif table == "attendance":
                sql = """
                    INSERT INTO attendance (employee_id, date, check_in_time, check_out_time)
                    VALUES ({emp_id}, '{date}', '{check_in}', '{check_out}')
                """.format(
                    emp_id=record.get("emp_id"),
                    date=str(record.get("date", "")).replace("'", "''"),
                    check_in=str(record.get("check_in", "")).replace("'", "''"),
                    check_out=str(record.get("check_out", "")).replace("'", "''")
                )
                self.azure_mcp.update_values(self.dbname, sql)
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Insert failed: {e}")
            return False
