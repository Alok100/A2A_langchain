#!/usr/bin/env python3
"""
Moback Database Setup Script
Creates and populates PostgreSQL database with employees, departments, roles, and assets
"""

import os
import uuid
import random
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd

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

# Department list
DEPARTMENTS = [
    'Human Resources',
    'Manager',
    'Engineering/Development',
    'Product Management',
    'Design (UX/UI)',
    'Sales',
    'Operations (Ops)',
    'IT Operations',
    'Data Science/Analytics'
]

# Roles list
ROLES = [
    'Software Engineer',
    'DevOps Engineer',
    'QA Engineer',
    'Architect',
    'Product Manager',
    'Product Owner',
    'IT Operations',
    'Network Operations',
    'Site Reliability Engineering (SRE)',
    'Customer Support',
    'Data Scientist',
    'Data Analyst',
    'Machine Learning Engineer',
    'Security Analyst',
    'Incident Responder',
    'Security Architect'
]

# Employee roles enum
EMPLOYEE_ROLES = ['employee', 'manager', 'hr', 'admin']

# Asset status
ASSET_STATUS = ['available', 'assigned', 'maintenance']

# Issue status
ISSUE_STATUS = ['open', 'in_progress', 'resolved']


def generate_email(full_name):
    """
    Generate email from full name
    Format: firstname + first_letter_of_lastname@moback.com
    """
    # Clean the name
    name = full_name.strip()
    # Remove newlines and extra spaces
    name = re.sub(r'\s+', ' ', name)
    
    # Split name into parts
    parts = name.split()
    
    if len(parts) == 0:
        return "unknown@moback.com"
    elif len(parts) == 1:
        # Only first name
        email = parts[0].lower() + "@moback.com"
    else:
        # First name + first letter of last name
        first_name = parts[0].lower()
        last_initial = parts[-1][0].lower()
        email = f"{first_name}{last_initial}@moback.com"
    
    # Remove any special characters
    email = re.sub(r'[^a-z0-9@.]', '', email)
    
    return email


def get_connection(database=None):
    """Create database connection"""
    config = DB_CONFIG.copy()
    if database:
        config['database'] = database
    else:
        config.pop('database', None)
    
    return psycopg2.connect(**config)


def create_database():
    """Create database if it doesn't exist"""
    print("Creating database...")
    
    conn = get_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Terminate all connections to the database before dropping
    cursor.execute(f"""
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = '{DB_CONFIG['database']}' AND pid <> pg_backend_pid()
    """)
    
    # Drop database if exists
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
    
    # Create database
    cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
    
    cursor.close()
    conn.close()
    
    print(f"Database '{DB_CONFIG['database']}' created successfully!")


def create_tables():
    """Create all required tables"""
    print("Creating tables...")
    
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    # Drop tables if they exist (in correct order due to foreign keys)
    drop_tables = """
    DROP TABLE IF EXISTS asset_issues CASCADE;
    DROP TABLE IF EXISTS asset_allocations CASCADE;
    DROP TABLE IF EXISTS assets CASCADE;
    DROP TABLE IF EXISTS employees CASCADE;
    DROP TABLE IF EXISTS roles CASCADE;
    DROP TABLE IF EXISTS departments CASCADE;
    """
    cursor.execute(drop_tables)
    
    # Create departments table
    cursor.execute("""
        CREATE TABLE departments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create roles table
    cursor.execute("""
        CREATE TABLE roles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create employees table
    cursor.execute("""
        CREATE TABLE employees (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            employee_code VARCHAR(50) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK (role IN ('employee', 'manager', 'hr', 'admin')),
            department_id UUID REFERENCES departments(id),
            designation VARCHAR(255),
            manager_id UUID REFERENCES employees(id) NULL,
            status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'terminated')),
            join_date DATE DEFAULT CURRENT_DATE,
            exit_date DATE NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create assets table
    cursor.execute("""
        CREATE TABLE assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_tag VARCHAR(50) UNIQUE NOT NULL,
            asset_type VARCHAR(255),
            brand VARCHAR(255),
            model VARCHAR(255),
            serial_number VARCHAR(255),
            status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'assigned', 'maintenance')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create asset_allocations table
    cursor.execute("""
        CREATE TABLE asset_allocations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_id UUID REFERENCES assets(id) NOT NULL,
            employee_id UUID REFERENCES employees(id) NOT NULL,
            allocated_date DATE DEFAULT CURRENT_DATE,
            return_date DATE NULL,
            status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'returned')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create asset_issues table
    cursor.execute("""
        CREATE TABLE asset_issues (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_id UUID REFERENCES assets(id) NOT NULL,
            employee_id UUID REFERENCES employees(id) NOT NULL,
            issue_description TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP NULL
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Tables created successfully!")


def populate_departments():
    """Populate departments table"""
    print("Populating departments...")
    
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    for dept in DEPARTMENTS:
        cursor.execute(
            "INSERT INTO departments (name) VALUES (%s)",
            (dept,)
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Inserted {len(DEPARTMENTS)} departments!")


def populate_roles():
    """Populate roles table"""
    print("Populating roles...")
    
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    for role in ROLES:
        cursor.execute(
            "INSERT INTO roles (name) VALUES (%s)",
            (role,)
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Inserted {len(ROLES)} roles!")


def get_department_ids():
    """Get all department IDs"""
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM departments")
    dept_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return dept_ids


def get_role_names():
    """Get all role names"""
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM roles")
    role_names = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return role_names


def populate_employees():
    """Populate employees from Excel file"""
    print("Populating employees from Excel file...")
    
    # Read Excel file
    df = pd.read_excel('asset_management/assets/Moback IDC ASSETS  Inventory.xlsx')
    
    # Extract unique employees with their moBack numbers
    employee_data = df[['Who has it now', 'moBack Number']].dropna()
    
    # Remove duplicates based on moBack Number
    employee_data = employee_data.drop_duplicates(subset=['moBack Number'])
    
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    # Get department IDs and role names
    dept_ids = get_department_ids()
    role_names = get_role_names()
    
    employees_created = 0
    inserted_names = set()  # Track inserted names to skip duplicates
    used_emails = {}  # Track used emails: {base_email: count}
    
    for _, row in employee_data.iterrows():
        full_name = str(row['Who has it now']).strip()
        employee_code = str(row['moBack Number']).strip()
        
        # Skip if invalid data
        if not full_name or full_name == 'nan' or not employee_code or employee_code == 'nan':
            continue
        
        # Skip if this exact name was already inserted
        if full_name in inserted_names:
            print(f"Skipping duplicate name: {full_name}")
            continue
        
        # Generate base email
        base_email = generate_email(full_name)
        
        # Handle duplicate emails by adding number suffix
        if base_email in used_emails:
            # Email already used, add number suffix
            used_emails[base_email] += 1
            email_parts = base_email.split('@')
            email = f"{email_parts[0]}{used_emails[base_email]}@{email_parts[1]}"
        else:
            # First use of this email
            email = base_email
            used_emails[base_email] = 0
        
        # Randomly assign department and designation
        department_id = random.choice(dept_ids)
        designation = random.choice(role_names)
        
        # Determine role and password based on designation
        if 'Manager' in designation or 'manager' in full_name.lower():
            role = 'manager'
            password = '12345'
        elif 'HR' in designation or 'hr' in full_name.lower():
            role = 'hr'
            password = '12345'
        else:
            role = 'employee'
            password = '1234'
        
        # Random join date within last 3 years
        days_ago = random.randint(0, 1095)
        join_date = datetime.now() - timedelta(days=days_ago)
        
        try:
            cursor.execute("""
                INSERT INTO employees 
                (employee_code, full_name, email, password, role, department_id, designation, status, join_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (employee_code, full_name, email, password, role, department_id, designation, 'active', join_date.date()))
            
            employees_created += 1
            inserted_names.add(full_name)  # Track this name as inserted
        except Exception as e:
            print(f"Error inserting employee {full_name}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Inserted {employees_created} employees!")


def populate_assets():
    """Populate assets from Excel file"""
    print("Populating assets...")
    
    # Read Excel file
    df = pd.read_excel('asset_management/assets/Moback IDC ASSETS  Inventory.xlsx')
    
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    assets_created = 0
    inserted_asset_tags = set()  # Track inserted asset tags to skip duplicates
    
    for _, row in df.iterrows():
        asset_tag = str(row['moBack Number']).strip() if pd.notna(row['moBack Number']) else None
        asset_type = str(row['Item name ']).strip() if pd.notna(row['Item name ']) else 'Unknown'
        serial_number = str(row['Serial Number']).strip() if pd.notna(row['Serial Number']) else None
        
        # Skip if no asset tag
        if not asset_tag or asset_tag == 'nan':
            continue
        
        # Skip if this asset tag was already inserted
        if asset_tag in inserted_asset_tags:
            print(f"Skipping duplicate asset tag: {asset_tag}")
            continue
        
        # Extract brand and model from asset_type
        brand = 'Unknown'
        model = asset_type
        
        if 'Macbook' in asset_type or 'MacBook' in asset_type:
            brand = 'Apple'
        elif 'HP' in asset_type or 'Hp' in asset_type:
            brand = 'HP'
        elif 'Lenovo' in asset_type or 'lenovo' in asset_type:
            brand = 'Lenovo'
        elif 'Dell' in asset_type:
            brand = 'Dell'
        elif 'Xiaomi' in asset_type or 'Mi' in asset_type:
            brand = 'Xiaomi'
        elif 'Asus' in asset_type:
            brand = 'Asus'
        
        # Determine status
        status = 'assigned' if pd.notna(row['Who has it now']) else 'available'
        
        try:
            cursor.execute("""
                INSERT INTO assets 
                (asset_tag, asset_type, brand, model, serial_number, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (asset_tag, asset_type, brand, model, serial_number, status))
            
            assets_created += 1
            inserted_asset_tags.add(asset_tag)  # Track this asset tag as inserted
        except Exception as e:
            print(f"Error inserting asset {asset_tag}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Inserted {assets_created} assets!")


def populate_asset_allocations():
    """Populate asset allocations based on 'Who has it now' field"""
    print("Populating asset allocations...")
    
    # Read Excel file
    df = pd.read_excel('asset_management/assets/Moback IDC ASSETS  Inventory.xlsx')
    
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    allocations_created = 0
    
    for _, row in df.iterrows():
        asset_tag = str(row['moBack Number']).strip() if pd.notna(row['moBack Number']) else None
        employee_name = str(row['Who has it now']).strip() if pd.notna(row['Who has it now']) else None
        
        # Skip if no asset tag or employee
        if not asset_tag or asset_tag == 'nan' or not employee_name or employee_name == 'nan':
            continue
        
        try:
            # Get asset ID
            cursor.execute("SELECT id FROM assets WHERE asset_tag = %s", (asset_tag,))
            asset_result = cursor.fetchone()
            if not asset_result:
                continue
            asset_id = asset_result[0]
            
            # Get employee ID
            cursor.execute("SELECT id FROM employees WHERE full_name = %s", (employee_name,))
            employee_result = cursor.fetchone()
            if not employee_result:
                continue
            employee_id = employee_result[0]
            
            # Random allocation date within last year
            days_ago = random.randint(0, 365)
            allocated_date = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute("""
                INSERT INTO asset_allocations 
                (asset_id, employee_id, allocated_date, status)
                VALUES (%s, %s, %s, %s)
            """, (asset_id, employee_id, allocated_date.date(), 'active'))
            
            allocations_created += 1
        except Exception as e:
            print(f"Error creating allocation for asset {asset_tag}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Inserted {allocations_created} asset allocations!")


def populate_asset_issues():
    """Populate some sample asset issues"""
    print("Populating asset issues...")
    
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    # Get some allocated assets
    cursor.execute("""
        SELECT aa.asset_id, aa.employee_id
        FROM asset_allocations aa
        WHERE aa.status = 'active'
        LIMIT 20
    """)
    
    allocations = cursor.fetchall()
    
    issue_descriptions = [
        "Laptop screen flickering",
        "Battery draining quickly",
        "Keyboard keys not working properly",
        "Laptop overheating",
        "Charger not working",
        "Software installation issue",
        "Blue screen errors",
        "Slow performance",
        "WiFi connection issues",
        "Audio not working"
    ]
    
    issues_created = 0
    
    # Create issues for about 30% of allocations
    for asset_id, employee_id in allocations:
        if random.random() < 0.3:  # 30% chance of having an issue
            issue_desc = random.choice(issue_descriptions)
            status = random.choice(ISSUE_STATUS)
            
            days_ago = random.randint(1, 90)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            resolved_at = None
            if status == 'resolved':
                resolved_days = random.randint(1, days_ago)
                resolved_at = created_at + timedelta(days=resolved_days)
            
            try:
                cursor.execute("""
                    INSERT INTO asset_issues 
                    (asset_id, employee_id, issue_description, status, created_at, resolved_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (asset_id, employee_id, issue_desc, status, created_at, resolved_at))
                
                issues_created += 1
            except Exception as e:
                print(f"Error creating issue: {e}")
                conn.rollback()
                continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Inserted {issues_created} asset issues!")


def print_summary():
    """Print database summary"""
    print("\n" + "="*60)
    print("DATABASE SUMMARY")
    print("="*60)
    
    conn = get_connection(DB_CONFIG['database'])
    cursor = conn.cursor()
    
    # Count records in each table
    tables = ['departments', 'roles', 'employees', 'assets', 'asset_allocations', 'asset_issues']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table.capitalize()}: {count} records")
    
    print("="*60)
    
    # Show sample data
    print("\nSAMPLE EMPLOYEES:")
    cursor.execute("""
        SELECT e.employee_code, e.full_name, e.email, e.role, d.name as department, e.designation
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
    
    print("\nSAMPLE ASSETS:")
    cursor.execute("""
        SELECT asset_tag, brand, model, status
        FROM assets
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")
    
    cursor.close()
    conn.close()
    
    print("="*60 + "\n")


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("MOBACK DATABASE SETUP")
    print("="*60 + "\n")
    
    try:
        # Step 1: Create database
        create_database()
        
        # Step 2: Create tables
        create_tables()
        
        # Step 3: Populate departments
        populate_departments()
        
        # Step 4: Populate roles
        populate_roles()
        
        # Step 5: Populate employees
        populate_employees()
        
        # Step 6: Populate assets
        populate_assets()
        
        # Step 7: Populate asset allocations
        populate_asset_allocations()
        
        # Step 8: Populate asset issues
        populate_asset_issues()
        
        # Step 9: Print summary
        print_summary()
        
        print("✅ Database setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()