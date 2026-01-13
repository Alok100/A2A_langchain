"""Interactive script to help set up PostgreSQL connection."""
import os
import psycopg2
from getpass import getpass

print("="*60)
print("PostgreSQL Setup Helper")
print("="*60)
print()

# Get connection details
host = input("PostgreSQL Host [localhost]: ").strip() or "localhost"
port = input("PostgreSQL Port [5432]: ").strip() or "5432"
user = input("PostgreSQL User [postgres]: ").strip() or "postgres"
password = getpass("PostgreSQL Password: ")

print("\nTesting connection...")

try:
    # Test connection to default postgres database
    conn = psycopg2.connect(
        host=host,
        port=port,
        database="postgres",
        user=user,
        password=password
    )
    print("✓ Connection successful!")
    conn.close()
    
    # Create .env file
    env_content = f"""# PostgreSQL Connection
POSTGRES_HOST={host}
POSTGRES_PORT={port}
POSTGRES_DB=employees_db
POSTGRES_USER={user}
POSTGRES_PASSWORD={password}

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✓ .env file created successfully!")
    print("\nNext step: Run 'python database_setup.py' to create the database and tables.")
    
except psycopg2.OperationalError as e:
    print(f"\n✗ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure PostgreSQL is running")
    print("2. Check your password is correct")
    print("3. Verify host and port are correct")
    print("\nTo start PostgreSQL service:")
    print("  Start-Service postgresql-x64-17")
    print("  (or postgresql-x64-16, depending on your version)")




