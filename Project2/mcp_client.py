import sys
import os
import json
from typing import Dict, Any

# Add path to Azure PostgreSQL MCP
azure_mcp_path = os.path.join(os.path.dirname(__file__), '..', 'azure-postgresql-mcp', 'src')
sys.path.insert(0, azure_mcp_path)

from azure_postgresql_mcp import AzurePostgreSQLMCP

# ============================================================================
# AZURE POSTGRESQL MCP CLIENT WRAPPER
# ============================================================================

class MCPClient:
    """Azure PostgreSQL MCP client wrapper"""
    
    def __init__(self):
        """Initialize Azure PostgreSQL MCP client"""
        self.azure_mcp = AzurePostgreSQLMCP()
        self.azure_mcp.init()  # Initialize with environment variables (PGHOST, PGUSER, PGPASSWORD, etc.)
        
        # Get database name from environment
        self.dbname = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB", "company_db")
    
    def _build_employee_query(self, filters: Dict[str, Any] = None) -> str:
        """Build SQL query for employees table"""
        sql = """
            SELECT employee_id as id, 
                   employee_name as name,
                   department,
                   CASE WHEN license_valid = 1 THEN 'PRO' ELSE 'EXPIRED' END as license,
                   date_of_joining::text as join_date,
                   leave_available as leave_days,
                   license_valid,
                   '' as email
            FROM employees
        """
        
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if key == "id":
                    where_clauses.append(f"employee_id = {value}")
                elif key == "email" or key == "name":
                    # Escape single quotes in value
                    escaped_value = str(value).replace("'", "''")
                    where_clauses.append(f"employee_name = '{escaped_value}'")
                else:
                    escaped_value = str(value).replace("'", "''")
                    where_clauses.append(f"{key} = '{escaped_value}'")
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        
        return sql
    
    def _build_attendance_query(self, filters: Dict[str, Any] = None) -> str:
        """Build SQL query for attendance table"""
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
        """Parse JSON result from Azure MCP query_data into list of dicts"""
        try:
            result = json.loads(result_json)
            columns_str = result.get("columns", "[]")
            rows_str = result.get("rows", "")
            
            # Parse columns
            import ast
            try:
                columns = ast.literal_eval(columns_str) if isinstance(columns_str, str) else columns_str
            except:
                # Fallback: try to extract column names from string
                columns = [col.strip() for col in columns_str.strip("[]").split(",")]
            
            # Parse rows - rows are comma-separated tuples
            results = []
            if rows_str:
                # Split by ),( to get individual rows
                rows = rows_str.split("),(")
                for i, row_str in enumerate(rows):
                    # Clean up row string
                    row_str = row_str.strip()
                    if i == 0:
                        row_str = row_str.lstrip("(")
                    if i == len(rows) - 1:
                        row_str = row_str.rstrip(")")
                    
                    # Parse tuple values
                    try:
                        row_values = ast.literal_eval(f"({row_str})")
                        row_dict = dict(zip(columns, row_values))
                        results.append(row_dict)
                    except:
                        continue
            
            return results
        except Exception as e:
            print(f"[ERROR] Failed to parse query result: {e}")
            print(f"Result JSON: {result_json}")
            return []
    
    def query(self, table: str, filters: Dict[str, Any] = None) -> list:
        """Read from database using Azure PostgreSQL MCP"""
        try:
            if table == "employees":
                sql = self._build_employee_query(filters)
            elif table == "attendance":
                sql = self._build_attendance_query(filters)
            else:
                return []
            
            # Execute query using Azure MCP
            result_json = self.azure_mcp.query_data(self.dbname, sql)
            
            if not result_json:
                return []
            
            # Parse result
            results = self._parse_query_result(result_json)
            
            # Add computed fields for employees
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
            import traceback
            traceback.print_exc()
            return []
    
    def update(self, table: str, record_id: int, updates: Dict[str, Any]) -> bool:
        """Update database record using Azure PostgreSQL MCP"""
        try:
            if table == "employees":
                # Map field names
                field_mapping = {
                    "leave_days": "leave_available",
                    "name": "employee_name",
                    "license": "license_valid"
                }
                
                set_clauses = []
                for key, value in updates.items():
                    db_field = field_mapping.get(key, key)
                    # Escape value
                    if isinstance(value, str):
                        escaped_value = value.replace("'", "''")
                        set_clauses.append(f"{db_field} = '{escaped_value}'")
                    else:
                        set_clauses.append(f"{db_field} = {value}")
                
                if set_clauses:
                    sql = f"UPDATE employees SET {', '.join(set_clauses)} WHERE employee_id = {record_id}"
                    self.azure_mcp.update_values(self.dbname, sql)
                    return True
            
            elif table == "attendance":
                set_clauses = []
                field_mapping = {
                    "check_in": "check_in_time",
                    "check_out": "check_out_time"
                }
                
                for key, value in updates.items():
                    db_field = field_mapping.get(key, key)
                    if isinstance(value, str):
                        escaped_value = value.replace("'", "''")
                        set_clauses.append(f"{db_field} = '{escaped_value}'")
                    else:
                        set_clauses.append(f"{db_field} = {value}")
                
                if set_clauses:
                    sql = f"UPDATE attendance SET {', '.join(set_clauses)} WHERE attendance_id = {record_id}"
                    self.azure_mcp.update_values(self.dbname, sql)
                    return True
            
            return False
        except Exception as e:
            print(f"[ERROR] Update failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def insert(self, table: str, record: Dict[str, Any]) -> bool:
        """Insert new record using Azure PostgreSQL MCP"""
        try:
            if table == "employees":
                sql = """
                    INSERT INTO employees (employee_id, employee_name, department, 
                                         license_valid, date_of_joining, leave_available)
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
            import traceback
            traceback.print_exc()
            return False