#!/usr/bin/env python3
"""
Database Test Script
Tests the moback_employees database with various queries
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'database': os.getenv('DB_NAME', 'moback_employees')
}


def get_connection():
    """Create database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        exit(1)


def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


def get_total_employees():
    """Get total count of employees"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return count


def get_employee_department(employee_name):
    """
    Get employee details including department by name
    
    Args:
        employee_name: Name or partial name of employee to search
        
    Returns:
        List of tuples with employee details
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.full_name, e.designation, d.name as department, e.email, e.status
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE e.full_name ILIKE %s
    """, (f'%{employee_name}%',))
    
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results


def get_employee_assets(employee_name):
    """
    Get assets allocated to an employee by name
    
    Args:
        employee_name: Name or partial name of employee to search
        
    Returns:
        List of tuples with asset details
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            e.full_name as employee_name,
            a.asset_tag,
            a.asset_type,
            a.brand,
            a.model,
            a.serial_number,
            a.status,
            al.allocated_at
        FROM employees e
        JOIN asset_allocations al ON e.id = al.employee_id
        JOIN assets a ON al.asset_id = a.id
        WHERE e.full_name ILIKE %s
        ORDER BY al.allocated_at DESC
    """, (f'%{employee_name}%',))
    
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results

def getall_managers():
    """Get all managers"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM employees WHERE role = 'manager'")
    results = cursor.fetchall()
    
    cursor.close()

def get_total_assets():
    """Get total count of assets and breakdown by status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM assets")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, COUNT(*) FROM assets GROUP BY status ORDER BY status")
    status_counts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return total_count, status_counts


def get_departments_summary(limit=10):
    """
    Get departments summary with employee count
    
    Args:
        limit: Maximum number of departments to return
        
    Returns:
        List of tuples with department name and employee count
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.name as department, COUNT(e.id) as employee_count
        FROM departments d
        LEFT JOIN employees e ON d.id = e.department_id
        GROUP BY d.name
        ORDER BY employee_count DESC
        LIMIT %s
    """, (limit,))
    
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results


def get_recent_allocations(limit=10):
    """
    Get recent asset allocations
    
    Args:
        limit: Maximum number of allocations to return
        
    Returns:
        List of tuples with allocation details
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            e.full_name as employee,
            a.asset_tag,
            a.asset_type,
            a.brand,
            al.allocated_at
        FROM asset_allocations al
        JOIN employees e ON al.employee_id = e.id
        JOIN assets a ON al.asset_id = a.id
        ORDER BY al.allocated_at DESC
        LIMIT %s
    """, (limit,))
    
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results


def get_employees_by_role():
    """Get count of employees grouped by role"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT role, COUNT(*) as count
        FROM employees
        GROUP BY role
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results


def get_available_assets(limit=10):
    """
    Get available assets (not allocated)
    
    Args:
        limit: Maximum number of assets to return
        
    Returns:
        List of tuples with asset details
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT asset_tag, asset_type, brand, model, status
        FROM assets
        WHERE status = 'available'
        ORDER BY asset_tag
        LIMIT %s
    """, (limit,))
    
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results


def search_employees_by_email(email_pattern, limit=10):
    """
    Search employees by email pattern
    
    Args:
        email_pattern: SQL LIKE pattern (e.g., 'a%', '%@moback.com')
        limit: Maximum number of employees to return
        
    Returns:
        List of tuples with employee details
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT full_name, email, designation, status
        FROM employees
        WHERE email LIKE %s
        ORDER BY full_name
        LIMIT %s
    """, (email_pattern, limit))
    
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results


def get_asset_issues(limit=10):
    """
    Get asset issues
    
    Args:
        limit: Maximum number of issues to return
        
    Returns:
        List of tuples with issue details
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            e.full_name as reported_by,
            a.asset_tag,
            ai.issue_description,
            ai.status,
            ai.reported_at
        FROM asset_issues ai
        JOIN employees e ON ai.employee_id = e.id
        JOIN assets a ON ai.asset_id = a.id
        ORDER BY ai.reported_at DESC
        LIMIT %s
    """, (limit,))
    
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results


def run_interactive_tests():
    """Run interactive tests with example data"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + " "*25 + "DATABASE TEST SUITE" + " "*34 + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    try:
        # Test database connection
        print("\n🔍 Testing database connection...")
        conn = get_connection()
        conn.close()
        print("✅ Database connection successful!")
        
        # Test 1: Total Employees
        print_header("TEST 1: Total Employees")
        count = get_total_employees()
        print(f"\n✅ Total Employees: {count}")
        
        # Test 2: Get Employee Department (Example: Abhinash)
        print_header("TEST 2: Employee Department - Example: 'Abhinash'")
        employee_name = "Abhinash"
        results = get_employee_department(employee_name)
        if results:
            headers = ['Name', 'Designation', 'Department', 'Email', 'Status']
            print(f"\n✅ Found {len(results)} employee(s) with name containing '{employee_name}':\n")
            print(tabulate(results, headers=headers, tablefmt='grid'))
        else:
            print(f"\n❌ No employee found with name containing '{employee_name}'")
        
        # Test 3: Get Employee Assets (Example: Kishore)
        print_header("TEST 3: Employee Assets - Example: 'Kishore'")
        employee_name = "Kishore"
        results = get_employee_assets(employee_name)
        if results:
            headers = ['Employee', 'Asset Tag', 'Type', 'Brand', 'Model', 'Serial Number', 'Status', 'Allocated At']
            print(f"\n✅ Found {len(results)} asset(s) allocated to '{employee_name}':\n")
            print(tabulate(results, headers=headers, tablefmt='grid'))
        else:
            print(f"\n❌ No assets found allocated to '{employee_name}'")
        
        # Test 4: Total Assets
        print_header("TEST 4: Total Assets")
        total_count, status_counts = get_total_assets()
        print(f"\n✅ Total Assets: {total_count}")
        print("\nAssets by Status:")
        print(tabulate(status_counts, headers=['Status', 'Count'], tablefmt='grid'))
        
        # Test 5: Departments Summary
        print_header("TEST 5: Departments Summary")
        results = get_departments_summary(limit=10)
        print("\n✅ Top 10 Departments by Employee Count:\n")
        print(tabulate(results, headers=['Department', 'Employee Count'], tablefmt='grid'))
        
        # Test 6: Recent Allocations
        print_header("TEST 6: Recent Asset Allocations")
        results = get_recent_allocations(limit=10)
        print("\n✅ 10 Most Recent Asset Allocations:\n")
        print(tabulate(results, headers=['Employee', 'Asset Tag', 'Type', 'Brand', 'Allocated At'], tablefmt='grid'))
        
        # Test 7: Employees by Role
        print_header("TEST 7: Employees by Role")
        results = get_employees_by_role()
        print("\n✅ Employees by Role:\n")
        print(tabulate(results, headers=['Role', 'Count'], tablefmt='grid'))
        
        # Test 8: Available Assets
        print_header("TEST 8: Available Assets (Not Allocated)")
        results = get_available_assets(limit=10)
        if results:
            print(f"\n✅ Found {len(results)} available assets (showing first 10):\n")
            print(tabulate(results, headers=['Asset Tag', 'Type', 'Brand', 'Model', 'Status'], tablefmt='grid'))
        else:
            print("\n✅ No available assets found (all are allocated)")
        
        # Test 9: Search Employees by Email
        print_header("TEST 9: Employees with Email Pattern - Example: 'a%'")
        email_pattern = 'a%'
        results = search_employees_by_email(email_pattern, limit=10)
        if results:
            print(f"\n✅ Employees with email starting with 'a' (first 10):\n")
            print(tabulate(results, headers=['Name', 'Email', 'Designation', 'Status'], tablefmt='grid'))
        else:
            print(f"\n❌ No employees found with email pattern '{email_pattern}'")
        
        # Test 10: Asset Issues
        print_header("TEST 10: Asset Issues")
        results = get_asset_issues(limit=10)
        if results:
            print(f"\n✅ Found {len(results)} asset issues (showing first 10):\n")
            print(tabulate(results, headers=['Reported By', 'Asset Tag', 'Issue', 'Status', 'Reported At'], tablefmt='grid'))
        else:
            print("\n✅ No asset issues found")
        
        # Final summary
        print("\n" + "█"*80)
        print("█" + " "*78 + "█")
        print("█" + " "*20 + "✅ ALL TESTS COMPLETED SUCCESSFULLY!" + " "*26 + "█")
        print("█" + " "*78 + "█")
        print("█"*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        exit(1)


def print_usage():
    """Print usage instructions"""
    print("""
Usage: python test_db.py [command] [arguments]

Commands:
    all                                    Run all tests with example data
    total-employees                        Get total employee count
    employee-dept <name>                   Get employee department by name
    employee-assets <name>                 Get assets allocated to employee
    total-assets                           Get total assets and breakdown
    departments [limit]                    Get departments summary
    recent-allocations [limit]             Get recent asset allocations
    employees-by-role                      Get employee count by role
    available-assets [limit]               Get available assets
    search-email <pattern> [limit]         Search employees by email pattern
    asset-issues [limit]                   Get asset issues

Examples:
    python test_db.py all
    python test_db.py employee-dept Abhinash
    python test_db.py employee-assets Kishore
    python test_db.py departments 20
    python test_db.py search-email "a%"
    """)


def main():
    """Main function to handle CLI arguments"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'all':
            run_interactive_tests()
        
        elif command == 'total-employees':
            count = get_total_employees()
            print(f"Total Employees: {count}")
        
        elif command == 'employee-dept':
            if len(sys.argv) < 3:
                print("❌ Error: Please provide employee name")
                print("Usage: python test_db.py employee-dept <name>")
                return
            
            name = sys.argv[2]
            results = get_employee_department(name)
            
            if results:
                headers = ['Name', 'Designation', 'Department', 'Email', 'Status']
                print(tabulate(results, headers=headers, tablefmt='grid'))
            else:
                print(f"No employee found with name containing '{name}'")
        
        elif command == 'employee-assets':
            if len(sys.argv) < 3:
                print("❌ Error: Please provide employee name")
                print("Usage: python test_db.py employee-assets <name>")
                return
            
            name = sys.argv[2]
            results = get_employee_assets(name)
            
            if results:
                headers = ['Employee', 'Asset Tag', 'Type', 'Brand', 'Model', 'Serial Number', 'Status', 'Allocated At']
                print(tabulate(results, headers=headers, tablefmt='grid'))
            else:
                print(f"No assets found allocated to '{name}'")
        
        elif command == 'total-assets':
            total_count, status_counts = get_total_assets()
            print(f"Total Assets: {total_count}\n")
            print("Assets by Status:")
            print(tabulate(status_counts, headers=['Status', 'Count'], tablefmt='grid'))
        
        elif command == 'departments':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            results = get_departments_summary(limit)
            print(f"Top {limit} Departments by Employee Count:\n")
            print(tabulate(results, headers=['Department', 'Employee Count'], tablefmt='grid'))
        
        elif command == 'recent-allocations':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            results = get_recent_allocations(limit)
            print(f"{limit} Most Recent Asset Allocations:\n")
            print(tabulate(results, headers=['Employee', 'Asset Tag', 'Type', 'Brand', 'Allocated At'], tablefmt='grid'))
        
        elif command == 'employees-by-role':
            results = get_employees_by_role()
            print("Employees by Role:\n")
            print(tabulate(results, headers=['Role', 'Count'], tablefmt='grid'))
        
        elif command == 'available-assets':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            results = get_available_assets(limit)
            
            if results:
                print(f"Available Assets (showing first {limit}):\n")
                print(tabulate(results, headers=['Asset Tag', 'Type', 'Brand', 'Model', 'Status'], tablefmt='grid'))
            else:
                print("No available assets found")
        
        elif command == 'search-email':
            if len(sys.argv) < 3:
                print("❌ Error: Please provide email pattern")
                print("Usage: python test_db.py search-email <pattern> [limit]")
                return
            
            pattern = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            results = search_employees_by_email(pattern, limit)
            
            if results:
                print(f"Employees with email pattern '{pattern}':\n")
                print(tabulate(results, headers=['Name', 'Email', 'Designation', 'Status'], tablefmt='grid'))
            else:
                print(f"No employees found with email pattern '{pattern}'")
        
        elif command == 'asset-issues':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            results = get_asset_issues(limit)
            
            if results:
                print(f"Asset Issues (showing first {limit}):\n")
                print(tabulate(results, headers=['Reported By', 'Asset Tag', 'Issue', 'Status', 'Reported At'], tablefmt='grid'))
            else:
                print("No asset issues found")
        
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()




# # Run all tests with examples
# python test_db.py all

# # Get total employees
# python test_db.py total-employees

# # Get employee department (any name)
# python test_db.py employee-dept Abhinash
# python test_db.py employee-dept Kishore

# # Get employee assets (any name)
# python test_db.py employee-assets Kishore
# python test_db.py employee-assets "Alok Kumar"

# # Get total assets
# python test_db.py total-assets

# # Get departments summary (custom limit)
# python test_db.py departments 20

# # Get recent allocations (custom limit)
# python test_db.py recent-allocations 15

# # Get employees by role
# python test_db.py employees-by-role

# # Get available assets (custom limit)
# python test_db.py available-assets 25

# # Search employees by email pattern
# python test_db.py search-email "a%"
# python test_db.py search-email "%kumar%"

# # Get asset issues (custom limit)
# python test_db.py asset-issues 20