"""MCP Server for PostgreSQL - exposes database tools."""
from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("PostgreSQL Server")

def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    try:
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "employees_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
        )
    except Exception as e:
        raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

@mcp.tool()
def query_database(query: str) -> str:
    """Execute a SQL SELECT query and return results as JSON.
    
    This tool allows you to run SELECT queries on the PostgreSQL database.
    Use this to retrieve data from tables.
    
    Args:
        query: The SQL SELECT query to execute
        
    Returns:
        JSON string with query results, or error message
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            # Convert to list of dicts for JSON serialization
            data = [dict(row) for row in results]
            return json.dumps(data, indent=2, default=str)
        else:
            conn.commit()
            return f"Query executed successfully. Rows affected: {cursor.rowcount}"
            
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def execute_query(query: str) -> str:
    """Execute a SQL query (INSERT, UPDATE, DELETE) and commit changes.
    
    Use this for modifying data in the database.
    
    Args:
        query: The SQL query to execute (INSERT, UPDATE, DELETE)
        
    Returns:
        Success message with rows affected, or error message
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        rows_affected = cursor.rowcount
        
        return f"Query executed successfully. Rows affected: {rows_affected}"
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return f"Error executing query: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def list_tables() -> str:
    """List all tables in the current database.
    
    Returns:
        JSON string with list of table names
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        return json.dumps(tables, indent=2)
        
    except Exception as e:
        return f"Error listing tables: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get the schema (columns and types) of a specific table.
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        JSON string with column information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = [dict(row) for row in cursor.fetchall()]
        return json.dumps(columns, indent=2, default=str)
        
    except Exception as e:
        return f"Error describing table: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run()
