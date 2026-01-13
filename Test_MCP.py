# test_mcp_server.py
"""Test script for Azure PostgreSQL MCP Server"""
import asyncio
import os
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# Set environment variables for your local PostgreSQL
# os.environ["PGHOST"] = "localhost"
# os.environ["PGUSER"] = "postgres"
# os.environ["PGPASSWORD"] = "alok@123"
# os.environ["PGDATABASE"] = "employees_db"

# Path to the MCP server script
server_script = "src/azure_postgresql_mcp.py"

async def test_mcp_server():
    """Test the MCP server by listing tools and calling one."""
    server_params = StdioServerParameters(
        command="python",
        args=[server_script],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("✓ MCP Server connected successfully!\n")
            
            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools ({len(tools_result.tools)}):")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            print("\n" + "="*60)
            
            # Test: Get databases
            print("\nTesting 'get_databases' tool...")
            try:
                result = await session.call_tool("get_databases", arguments={})
                if result.content:
                    print(f"Result: {result.content[0].text}")
                else:
                    print("No result returned")
            except Exception as e:
                print(f"Error: {e}")
            
            print("\n" + "="*60)
            
            # Test: Get schemas (if you have a database)
            print("\nTesting 'get_schemas' tool...")
            try:
                result = await session.call_tool("get_schemas", arguments={"database": "employees_db"})
                if result.content:
                    print(f"Result: {result.content[0].text[:500]}...")  # First 500 chars
                else:
                    print("No result returned")
            except Exception as e:
                print(f"Error: {e}")
            
            print("\n" + "="*60)
            
            # Test: Query data
            print("\nTesting 'query_data' tool...")
            try:
                result = await session.call_tool(
                    "query_data", 
                    arguments={
                        "dbname": "employees_db",
                        "s": "SELECT COUNT(*) FROM employees;"
                    }
                )
                if result.content:
                    print(f"Result: {result.content[0].text}")
                else:
                    print("No result returned")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())