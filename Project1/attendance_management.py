"""
Attendance Management System - Database Setup and Management Script

This script creates and manages a SQLite database for an attendance management system.
It includes functions to create tables, insert dummy data, add employees, and mark attendance
with business rule validation (license validity check).

Database: company_db (SQLite)
Tables: employees, attendance
"""

import sqlite3
from datetime import date, time, datetime
from typing import Optional, Tuple


# Database configuration
DB_NAME = "company_db.db"


def get_connection():
    """Create and return a database connection."""
    return sqlite3.connect(DB_NAME)


def create_database_and_tables():
    """
    Create the database and tables if they don't exist.
    
    Creates:
    - employees table with employee information
    - attendance table with attendance records (with foreign key constraint)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id INTEGER PRIMARY KEY,
                employee_name TEXT NOT NULL,
                department TEXT,
                license_valid INTEGER NOT NULL CHECK(license_valid IN (0, 1)),
                date_of_joining DATE,
                leave_available INTEGER DEFAULT 0
            )
        """)
        
        # Create attendance table with foreign key constraint
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date DATE NOT NULL,
                check_in_time TIME,
                check_out_time TIME,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
                    ON DELETE CASCADE
            )
        """)
        
        # Enable foreign key constraints (SQLite requires explicit enabling)
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        print("[OK] Database and tables created successfully")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def insert_dummy_employees():
    """
    Insert dummy employee data if the employees table is empty.
    
    Returns:
        int: Number of employees inserted
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if table is empty
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"[INFO] Employees table already contains {count} records. Skipping insertion.")
            return count
        
        # Sample employee data
        employees_data = [
            (1, "John Smith", "Engineering", 1, date(2022, 1, 15), 20),
            (2, "Sarah Johnson", "Engineering", 1, date(2023, 3, 20), 18),
            (3, "Mike Davis", "Engineering", 0, date(2024, 1, 10), 15),  # License expired
            (4, "Emily Brown", "Sales", 1, date(2021, 6, 1), 22),
            (5, "David Wilson", "Sales", 1, date(2023, 8, 15), 18),
            (6, "Lisa Anderson", "Sales", 0, date(2024, 2, 5), 20),  # License expired
            (7, "Robert Taylor", "Marketing", 1, date(2022, 9, 10), 19),
            (8, "Jennifer Martinez", "Marketing", 1, date(2023, 11, 1), 17),
            (9, "James Garcia", "HR", 1, date(2020, 4, 1), 25),
            (10, "Amanda Lee", "HR", 0, date(2023, 5, 20), 20),  # License expired
        ]
        
        # Convert date objects to strings for SQLite
        employees = [
            (emp_id, name, dept, lic_valid, str(join_date), leave)
            for emp_id, name, dept, lic_valid, join_date, leave in employees_data
        ]
        
        cursor.executemany("""
            INSERT INTO employees 
            (employee_id, employee_name, department, license_valid, date_of_joining, leave_available)
            VALUES (?, ?, ?, ?, ?, ?)
        """, employees)
        
        conn.commit()
        print(f"[OK] Inserted {len(employees)} dummy employees")
        return len(employees)
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error inserting employees: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def insert_dummy_attendance():
    """
    Insert dummy attendance records if the attendance table is empty.
    Only inserts attendance for employees with valid licenses.
    
    Returns:
        int: Number of attendance records inserted
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Check if table is empty
        cursor.execute("SELECT COUNT(*) FROM attendance")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"[INFO] Attendance table already contains {count} records. Skipping insertion.")
            return count
        
        # Get employees with valid licenses
        cursor.execute("SELECT employee_id FROM employees WHERE license_valid = 1")
        valid_employees = cursor.fetchall()
        
        if not valid_employees:
            print("[WARNING] No employees with valid licenses found. Cannot insert attendance records.")
            return 0
        
        # Sample attendance data (only for employees with valid licenses)
        attendance_records = []
        today = date.today()
        
        # Create attendance records for the last 5 days for valid employees
        for i in range(5):
            check_date = date(today.year, today.month, today.day - i) if today.day > i else date(today.year, today.month - 1, 28 + today.day - i)
            
            for emp_id_tuple in valid_employees[:5]:  # First 5 valid employees
                emp_id = emp_id_tuple[0]
                check_in = time(9, 0 + (emp_id % 3))  # Vary check-in times
                check_out = time(17, 30 + (emp_id % 2))  # Vary check-out times
                attendance_records.append((
                    emp_id,
                    str(check_date),  # Convert date to string
                    str(check_in),    # Convert time to string
                    str(check_out)    # Convert time to string
                ))
        
        cursor.executemany("""
            INSERT INTO attendance (employee_id, date, check_in_time, check_out_time)
            VALUES (?, ?, ?, ?)
        """, attendance_records)
        
        conn.commit()
        print(f"[OK] Inserted {len(attendance_records)} dummy attendance records")
        return len(attendance_records)
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error inserting attendance: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def add_new_employee(
    employee_id: int,
    employee_name: str,
    department: Optional[str] = None,
    license_valid: bool = True,
    date_of_joining: Optional[date] = None,
    leave_available: int = 0
) -> bool:
    """
    Add a new employee to the database.
    
    Args:
        employee_id: Unique employee identifier
        employee_name: Name of the employee (required)
        department: Department name (optional)
        license_valid: Whether the employee's license is valid (default: True)
        date_of_joining: Date when employee joined (optional)
        leave_available: Number of leave days available (default: 0)
    
    Returns:
        bool: True if employee was added successfully, False otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if employee_id already exists
        cursor.execute("SELECT employee_id FROM employees WHERE employee_id = ?", (employee_id,))
        if cursor.fetchone():
            print(f"[ERROR] Employee with ID {employee_id} already exists")
            return False
        
        # Convert boolean to integer for SQLite
        license_valid_int = 1 if license_valid else 0
        
        # Convert date to string if it's a date object
        date_str = str(date_of_joining) if date_of_joining is not None and isinstance(date_of_joining, date) else date_of_joining
        
        cursor.execute("""
            INSERT INTO employees 
            (employee_id, employee_name, department, license_valid, date_of_joining, leave_available)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (employee_id, employee_name, department, license_valid_int, date_str, leave_available))
        
        conn.commit()
        print(f"[OK] Added new employee: {employee_name} (ID: {employee_id})")
        return True
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error adding employee: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def mark_attendance(
    employee_id: int,
    check_in: Optional[time] = None,
    check_out: Optional[time] = None,
    attendance_date: Optional[date] = None
) -> Tuple[bool, str]:
    """
    Mark attendance for an employee.
    
    Business Rule: Attendance can only be marked if license_valid = TRUE
    
    Args:
        employee_id: ID of the employee
        check_in: Check-in time (optional)
        check_out: Check-out time (optional)
        attendance_date: Date of attendance (defaults to today if not provided)
    
    Returns:
        Tuple[bool, str]: (success, message)
            - success: True if attendance was marked successfully
            - message: Descriptive message about the operation result
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Check if employee exists
        cursor.execute("""
            SELECT employee_id, employee_name, license_valid 
            FROM employees 
            WHERE employee_id = ?
        """, (employee_id,))
        
        employee = cursor.fetchone()
        
        if not employee:
            return False, f"Employee with ID {employee_id} does not exist"
        
        emp_id, emp_name, license_valid = employee
        
        # Business rule: Check license validity
        if license_valid != 1:
            message = (
                f"[REJECTED] Attendance rejected for {emp_name} (ID: {employee_id}): "
                f"License is invalid. Please renew license before marking attendance."
            )
            print(message)
            return False, message
        
        # Use today's date if not provided
        if attendance_date is None:
            attendance_date = date.today()
        
        # Convert date and time objects to strings for SQLite
        date_str = str(attendance_date) if isinstance(attendance_date, date) else attendance_date
        check_in_str = str(check_in) if check_in is not None and isinstance(check_in, time) else check_in
        check_out_str = str(check_out) if check_out is not None and isinstance(check_out, time) else check_out
        
        # Check if attendance record already exists for this date
        cursor.execute("""
            SELECT attendance_id FROM attendance 
            WHERE employee_id = ? AND date = ?
        """, (employee_id, date_str))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            attendance_id = existing[0]
            update_fields = []
            params = []
            
            if check_in is not None:
                update_fields.append("check_in_time = ?")
                params.append(check_in_str)
            
            if check_out is not None:
                update_fields.append("check_out_time = ?")
                params.append(check_out_str)
            
            if update_fields:
                params.append(attendance_id)
                cursor.execute(f"""
                    UPDATE attendance 
                    SET {', '.join(update_fields)}
                    WHERE attendance_id = ?
                """, params)
                conn.commit()
                message = f"[OK] Updated attendance for {emp_name} (ID: {employee_id}) on {attendance_date}"
                print(message)
                return True, message
            else:
                return False, "No attendance data provided to update"
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO attendance (employee_id, date, check_in_time, check_out_time)
                VALUES (?, ?, ?, ?)
            """, (employee_id, date_str, check_in_str, check_out_str))
            
            conn.commit()
            message = f"[OK] Marked attendance for {emp_name} (ID: {employee_id}) on {attendance_date}"
            print(message)
            return True, message
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        error_msg = f"[ERROR] Foreign key constraint violation: {str(e)}"
        print(error_msg)
        return False, error_msg
    except sqlite3.Error as e:
        conn.rollback()
        error_msg = f"[ERROR] Error marking attendance: {e}"
        print(error_msg)
        return False, error_msg
    finally:
        cursor.close()
        conn.close()


def display_employees():
    """Display all employees in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT employee_id, employee_name, department, 
                   CASE WHEN license_valid = 1 THEN 'Valid' ELSE 'Invalid' END as license_status,
                   date_of_joining, leave_available
            FROM employees
            ORDER BY employee_id
        """)
        
        employees = cursor.fetchall()
        
        if not employees:
            print("No employees found in the database.")
            return
        
        print("\n" + "=" * 80)
        print("EMPLOYEES")
        print("=" * 80)
        print(f"{'ID':<5} {'Name':<25} {'Department':<15} {'License':<10} {'Join Date':<12} {'Leave Days':<10}")
        print("-" * 80)
        
        for emp in employees:
            print(f"{emp[0]:<5} {emp[1]:<25} {emp[2] or 'N/A':<15} {emp[3]:<10} "
                  f"{str(emp[4]) if emp[4] else 'N/A':<12} {emp[5]:<10}")
        
        print("=" * 80)
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error displaying employees: {e}")
    finally:
        cursor.close()
        conn.close()


def display_attendance():
    """Display all attendance records."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.attendance_id, a.employee_id, e.employee_name, 
                   a.date, a.check_in_time, a.check_out_time
            FROM attendance a
            JOIN employees e ON a.employee_id = e.employee_id
            ORDER BY a.date DESC, a.employee_id
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("No attendance records found in the database.")
            return
        
        print("\n" + "=" * 90)
        print("ATTENDANCE RECORDS")
        print("=" * 90)
        print(f"{'ID':<5} {'Emp ID':<8} {'Employee Name':<25} {'Date':<12} {'Check In':<10} {'Check Out':<10}")
        print("-" * 90)
        
        for record in records:
            print(f"{record[0]:<5} {record[1]:<8} {record[2]:<25} {str(record[3]):<12} "
                  f"{str(record[4]) if record[4] else 'N/A':<10} {str(record[5]) if record[5] else 'N/A':<10}")
        
        print("=" * 90)
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error displaying attendance: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    """
    Main function to initialize the database and demonstrate functionality.
    """
    print("=" * 80)
    print("ATTENDANCE MANAGEMENT SYSTEM - DATABASE SETUP")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Create database and tables
        print("Step 1: Creating database and tables...")
        create_database_and_tables()
        print()
        
        # Step 2: Insert dummy employees
        print("Step 2: Inserting dummy employees...")
        insert_dummy_employees()
        print()
        
        # Step 3: Insert dummy attendance (only for valid licenses)
        print("Step 3: Inserting dummy attendance records...")
        insert_dummy_attendance()
        print()
        
        # Step 4: Display employees
        display_employees()
        print()
        
        # Step 5: Display attendance
        display_attendance()
        print()
        
        # Step 6: Demonstrate valid attendance entry
        print("Step 6: Demonstrating valid attendance entry...")
        print("-" * 80)
        mark_attendance(
            employee_id=1,
            check_in=time(9, 15),
            check_out=time(18, 0),
            attendance_date=date.today()
        )
        print()
        
        # Step 7: Demonstrate invalid attendance attempt (license expired)
        print("Step 7: Demonstrating invalid attendance attempt (license expired)...")
        print("-" * 80)
        mark_attendance(
            employee_id=3,  # Employee with expired license
            check_in=time(9, 0),
            check_out=time(17, 30),
            attendance_date=date.today()
        )
        print()
        
        # Step 8: Add a new employee
        print("Step 8: Adding a new employee...")
        print("-" * 80)
        add_new_employee(
            employee_id=11,
            employee_name="Test Employee",
            department="IT",
            license_valid=True,
            date_of_joining=date.today(),
            leave_available=20
        )
        print()
        
        # Step 9: Mark attendance for the new employee
        print("Step 9: Marking attendance for new employee...")
        print("-" * 80)
        mark_attendance(
            employee_id=11,
            check_in=time(9, 30),
            check_out=time(18, 15),
            attendance_date=date.today()
        )
        print()
        
        print("=" * 80)
        print("[SUCCESS] DATABASE SETUP AND DEMONSTRATION COMPLETE!")
        print("=" * 80)
        print(f"\nDatabase file: {DB_NAME}")
        print("You can now use the functions in this script to manage your attendance system.")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

