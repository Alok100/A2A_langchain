import sys
import os
sys.path.append(os.path.dirname(__file__))
from SettingUp_DB import get_connection
from typing import TypedDict, Literal, Optional, Dict, Any
# ============================================================================
# MCP CLIENT (Mock - Replace with your Azure PostgreSQL MCP)
# ============================================================================

class MCPClient:
    """Mock MCP client - replace with your actual Azure PostgreSQL MCP"""
    
    def __init__(self):
        # Mock data
        self.conn= None
    
    def _get_conn(self):
        if self.conn is None or self.conn.closed:
            self.conn = get_connection()
        return self.conn

    def query(self, table: str, filters: Dict[str, Any] = None) -> list:
        """Read from database"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            if table == "employees":
                # Build SELECT query
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
                
                # Add WHERE clause if filters provided
                if filters:
                    # Map common filter keys
                    where_clauses = []
                    params = []
                    
                    for key, value in filters.items():
                        if key == "id":
                            where_clauses.append("employee_id = %s")
                            params.append(value)
                        elif key == "email":
                            # Since email doesn't exist in DB, skip or handle differently
                            # For now, we'll try to match by name
                            where_clauses.append("employee_name = %s")
                            params.append(value)
                        elif key == "name":
                            where_clauses.append("employee_name = %s")
                            params.append(value)
                        else:
                            where_clauses.append(f"{key} = %s")
                            params.append(value)
                    
                    if where_clauses:
                        sql += " WHERE " + " AND ".join(where_clauses)
                    
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # Fetch results and convert to list of dicts
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    emp_dict = dict(zip(columns, row))
                    # Add computed fields for compatibility
                    emp_dict["verified"] = True
                    emp_dict["active"] = True
                    emp_dict["license_active"] = emp_dict["license_valid"] == 1
                    emp_dict["license_expired"] = emp_dict["license_valid"] == 0
                    # Generate email from name if not exists
                    if not emp_dict.get("email"):
                        emp_dict["email"] = emp_dict["name"].lower().replace(" ", ".") + "@company.com"
                    results.append(emp_dict)
                
                return results
            
            elif table == "attendance":
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
                    params = []
                    
                    for key, value in filters.items():
                        if key == "emp_id":
                            where_clauses.append("employee_id = %s")
                            params.append(value)
                        elif key == "date":
                            where_clauses.append("date = %s")
                            params.append(value)
                        else:
                            where_clauses.append(f"{key} = %s")
                            params.append(value)
                    
                    if where_clauses:
                        sql += " WHERE " + " AND ".join(where_clauses)
                    
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
            
            else:
                return []
                
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            return []
        finally:
            cursor.close()
    
    def update(self, table: str, record_id: int, updates: Dict[str, Any]) -> bool:
        """Update database record"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            if table == "employees":
                # Map field names
                field_mapping = {
                    "leave_days": "leave_available",
                    "name": "employee_name",
                    "license": "license_valid"
                }
                
                set_clauses = []
                params = []
                
                for key, value in updates.items():
                    db_field = field_mapping.get(key, key)
                    set_clauses.append(f"{db_field} = %s")
                    params.append(value)
                
                if set_clauses:
                    params.append(record_id)
                    sql = f"UPDATE employees SET {', '.join(set_clauses)} WHERE employee_id = %s"
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
            
            elif table == "attendance":
                set_clauses = []
                params = []
                
                field_mapping = {
                    "check_in": "check_in_time",
                    "check_out": "check_out_time"
                }
                
                for key, value in updates.items():
                    db_field = field_mapping.get(key, key)
                    set_clauses.append(f"{db_field} = %s")
                    params.append(value)
                
                if set_clauses:
                    params.append(record_id)
                    sql = f"UPDATE attendance SET {', '.join(set_clauses)} WHERE attendance_id = %s"
                    cursor.execute(sql, params)
                    conn.commit()
                    return True
            
            return False
        except Exception as e:
            print(f"[ERROR] Update failed: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    def insert(self, table: str, record: Dict[str, Any]) -> bool:
        """Insert new record"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            if table == "employees":
                # Map fields
                sql = """
                    INSERT INTO employees (employee_id, employee_name, department, 
                                         license_valid, date_of_joining, leave_available)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    record.get("id"),
                    record.get("name"),
                    record.get("department"),
                    1 if record.get("license_active", True) else 0,
                    record.get("join_date"),
                    record.get("leave_days", 0)
                )
                cursor.execute(sql, params)
                
            elif table == "attendance":
                sql = """
                    INSERT INTO attendance (employee_id, date, check_in_time, check_out_time)
                    VALUES (%s, %s, %s, %s)
                """
                params = (
                    record.get("emp_id"),
                    record.get("date"),
                    record.get("check_in"),
                    record.get("check_out")
                )
                cursor.execute(sql, params)
            else:
                return False
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"[ERROR] Insert failed: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
