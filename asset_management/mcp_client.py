import sys
import os
import json
from typing import Dict, Any

# Add path to Azure PostgreSQL MCP
azure_mcp_path = os.path.join(os.path.dirname(__file__), '..', 'azure-postgresql-mcp', 'src')
sys.path.insert(0, azure_mcp_path)

# import azure_postgresql_mcp
# AzurePostgreSQLMCP = azure_postgresql_mcp.AzurePostgreSQLMCP


# Add path to Azure PostgreSQL MCP
azure_mcp_path = os.path.join(os.path.dirname(__file__), '..', 'azure-postgresql-mcp', 'src')
sys.path.insert(0, azure_mcp_path)

#from azure_postgresql_mcp import AzurePostgreSQLMCP
from azure_postgresql_mcp.azure_postgresql_mcp import AzurePostgreSQLMCP
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
        self.dbname = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB", "moback_employees") 

    # ---------------------------------------------------
    # Core Query Executor
    # ---------------------------------------------------
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        try:
            result = self.azure_mcp.execute(
                database=self.dbname,
                query=query,
                params=params
            )

            if fetch:
                return result  # Already JSON-like from MCP

            return {"status": "success"}

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    # ---------------------------------------------------
    # EMPLOYEE METHODS
    # ---------------------------------------------------
    def get_employee_by_email(self, email: str):
        query = "Select * from employees where email= %s"
        return self.execute_query(query, (email,),fetch=True)
    
    def get_employee_by_id(self, employee_id: str):
        query ="Select *from employees where employee_id= %s"
        return self.execute_query(query, (employee_id,),fetch=True)
    
    def list_employees(self):
        query = "Select * from employees"
        return self.execute_query(query, fetch=True)
    
    # ---------------------------------------------------
    # ASSET METHODS
    # ---------------------------------------------------
    def list_available_assets(self):
        query = "Select * from assets where status= 'available'"
        return self.execute_query(query, fetch=True)    

    def get_asset_by_tag(self, asset_tag: str):
        query = "Select * from assets where asset_tag= %s"
        return self.execute_query(query, (asset_tag,),fetch=True)

    def get_asset_by__model(self, model: str):
        query = "Select * from assets where model= %s"
        return self.execute_query(query, (model,),fetch=True)
    
    def get_asset_by_brand(self, brand: str):
        query = "Select * from assets where brand= %s"
        return self.execute_query(query, (brand,),fetch=True)
    
    def get_asset_by_serial_number(self, serial_number: str):
        query = "Select * from assets where serial_number= %s"
        return self.execute_query(query, (serial_number,),fetch=True)
    
    # ---------------------------------------------------
    # ALLOCATION METHODS
    # --
    def assign_asset(self, asset_id: str, employee_id: str):
        query1 = """
        INSERT INTO asset_allocations (asset_id, employee_id)
        VALUES (%s, %s)
        """

        query2 = """
        UPDATE assets SET status = 'assigned'
        WHERE id = %s
        """

        self.execute_query(query1, (asset_id, employee_id))
        self.execute_query(query2, (asset_id,))

        return {"status": "asset_assigned"}

    # ---------------------------------------------------
    # ISSUE METHODS
    # ---------------------------------------------------

    def create_issue(self, asset_id: str, employee_id: str, description: str):
        query = """
        INSERT INTO asset_issues (asset_id, employee_id, issue_description)
        VALUES (%s, %s, %s)
        """
        return self.execute_query(query, (asset_id, employee_id, description))

    def get_open_issues(self):
        query = "SELECT * FROM asset_issues WHERE status = 'open'"
        return self.execute_query(query, fetch=True)


    def get_all_allocated_assets_to_employee_id(self, employee_id: str):
        query = "SELECT * FROM asset_allocations WHERE employee_id = %s"
        return self.execute_query(query, (employee_id,),fetch=True)

    def get_all_allocated_assets_to_employee_email(self, email: str):
        query = "SELECT * FROM asset_allocations WHERE employee_id = (SELECT id FROM employees WHERE email = %s)"
        return self.execute_query(query, (email,),fetch=True)

    # ---------------------------------------------------
    # RETURN METHODS
    # ---------------------------------------------------

    def return_asset(self, asset_id: str):
        query = "UPDATE assets SET status = 'available' WHERE id = %s"
        return self.execute_query(query, (asset_id,))

    def get_user_role(self, user_id: str):
        query = "SELECT role FROM employees WHERE id = %s"
        return self.execute_query(query, (user_id,),fetch=True)
        