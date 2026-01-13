"""Create PostgreSQL database with dummy employee data."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

# Connection parameters
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "employees_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to default postgres database to create our database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database="postgres",
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✓ Database '{DB_NAME}' created successfully")
        else:
            print(f"✓ Database '{DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        raise

def create_tables():
    """Create employees table."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # Drop table if exists (for clean setup)
    cursor.execute("DROP TABLE IF EXISTS employees CASCADE;")
    
    # Create employees table
    cursor.execute("""
        CREATE TABLE employees (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            department VARCHAR(50) NOT NULL,
            join_date DATE NOT NULL,
            salary DECIMAL(10, 2) NOT NULL,
            manager_id INTEGER REFERENCES employees(id)
        );
    """)
    
    conn.commit()
    print("✓ Employees table created")
    
    cursor.close()
    conn.close()

def insert_dummy_data():
    """Insert dummy employee data."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # Sample employee data
    employees = [
        ("John Smith", "john.smith@company.com", "Engineering", date(2022, 1, 15), 95000.00, None),
        ("Sarah Johnson", "sarah.j@company.com", "Engineering", date(2023, 3, 20), 85000.00, 1),
        ("Mike Davis", "mike.davis@company.com", "Engineering", date(2024, 1, 10), 80000.00, 1),
        ("Emily Brown", "emily.brown@company.com", "Sales", date(2021, 6, 1), 70000.00, None),
        ("David Wilson", "david.w@company.com", "Sales", date(2023, 8, 15), 65000.00, 4),
        ("Lisa Anderson", "lisa.a@company.com", "Sales", date(2024, 2, 5), 60000.00, 4),
        ("Robert Taylor", "robert.t@company.com", "Marketing", date(2022, 9, 10), 75000.00, None),
        ("Jennifer Martinez", "jennifer.m@company.com", "Marketing", date(2023, 11, 1), 70000.00, 7),
        ("James Garcia", "james.g@company.com", "HR", date(2020, 4, 1), 80000.00, None),
        ("Amanda Lee", "amanda.lee@company.com", "HR", date(2023, 5, 20), 72000.00, 9),
        ("Christopher White", "chris.w@company.com", "Finance", date(2021, 2, 14), 90000.00, None),
        ("Jessica Harris", "jessica.h@company.com", "Finance", date(2024, 3, 1), 78000.00, 11),
    ]
    
    cursor.executemany("""
        INSERT INTO employees (name, email, department, join_date, salary, manager_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, employees)
    
    conn.commit()
    print(f"✓ Inserted {len(employees)} employees")
    
    cursor.close()
    conn.close()

def main():
    """Main setup function."""
    print("Setting up PostgreSQL database...")
    print("-" * 50)
    
    try:
        create_database()
        create_tables()
        insert_dummy_data()
        print("-" * 50)
        print("✓ Database setup complete!")
        print(f"\nDatabase: {DB_NAME}")
        print(f"Host: {DB_HOST}:{DB_PORT}")
        print(f"User: {DB_USER}")
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        print("\nMake sure PostgreSQL is running and credentials are correct in .env file")

if __name__ == "__main__":
    main()
