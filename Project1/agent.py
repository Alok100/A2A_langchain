"""LangChain agent with MCP tools for PostgreSQL."""
import asyncio
import json
from typing import List, Any, Dict
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.tools import Tool, StructuredTool, BaseTool
from langchain_core.messages import HumanMessage
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
import os
from dotenv import load_dotenv

load_dotenv()

# LangSmith Configuration
# LangSmith will automatically trace if LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY are set
# You can also configure it programmatically here if needed
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "mcp-postgres-agent")

if LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
    print(f"✓ LangSmith tracing enabled (Project: {LANGCHAIN_PROJECT})")
    print(f"  View traces at: https://smith.langchain.com")
elif LANGCHAIN_TRACING_V2:
    print("⚠ LangSmith tracing requested but LANGCHAIN_API_KEY not set. Tracing disabled.")

# Setup Ollama LLM
llm = ChatOllama(model="qwen2.5", temperature=0)

# Global MCP session manager
_server_params = StdioServerParameters(
    command="python",
    args=["mcp_postgres_server.py"],
)

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Call an MCP tool and return the result."""
    try:
        async with stdio_client(_server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                if result.content:
                    return result.content[0].text if result.content else "No result"
                return "No result"
    except Exception as e:
        return f"Error calling tool: {str(e)}"

def get_mcp_tools() -> List[BaseTool]:
    """Get MCP tools and convert them to LangChain tools."""
    tools = []
    
    # Define the tools we know exist from our MCP server
    # We'll create wrappers for each
    
    def query_db_wrapper(query: str) -> str:
        """Wrapper for query_database tool."""
        return asyncio.run(call_mcp_tool("query_database", {"query": query}))
    
    def list_tables_wrapper() -> str:
        """Wrapper for list_tables tool - takes no arguments."""
        return asyncio.run(call_mcp_tool("list_tables", {}))
    
    def describe_table_wrapper(table_name: str) -> str:
        """Wrapper for describe_table tool."""
        return asyncio.run(call_mcp_tool("describe_table", {"table_name": table_name}))
    
    # Create LangChain tools
    tools.append(Tool(
        name="query_database",
        description="Execute a SQL SELECT query on the PostgreSQL database. Use this to retrieve data from tables. Input should be a valid SQL SELECT query.",
        func=query_db_wrapper
    ))
    
    # Use StructuredTool for list_tables since it takes no arguments
    tools.append(StructuredTool.from_function(
        func=list_tables_wrapper,
        name="list_tables",
        description="List all tables in the PostgreSQL database. This tool takes no arguments.",
    ))
    
    tools.append(Tool(
        name="describe_table",
        description="Get the schema (columns, types) of a specific table. Input should be the table name as a string.",
        func=describe_table_wrapper
    ))
    
    return tools

def create_agent_with_mcp_tools():
    """Create LangChain agent with MCP tools."""
    # Get MCP tools
    tools = get_mcp_tools()
    
    # System prompt
    system_prompt = """You are a helpful AI assistant with access to a PostgreSQL database containing employee information.
You can query the database to answer questions about employees and company data.

Available tools:
- query_database: Execute SELECT queries to retrieve data. Input should be a SQL query string.
- list_tables: List all tables in the database. No input needed.
- describe_table: Get the schema of a table. Input should be the table name.

When users ask questions:
1. First, use list_tables to see what tables are available
2. Use describe_table to understand the table structure if needed
3. Use query_database to retrieve the relevant data
4. Provide clear, natural language answers based on the data

Always explain what you're doing step by step."""
    
    # Create agent using LangChain 1.2.0 API
    # This returns a LangGraph CompiledStateGraph
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        debug=False,  # Disable debug to reduce verbose output
    )
    
    return agent

def visualize_graph(agent):
    """Print the LangGraph structure (like ADK web shows)."""
    print("\n" + "="*60)
    print("📊 LangGraph Structure:")
    print("="*60)
    
    # The agent is a CompiledStateGraph
    if hasattr(agent, "nodes"):
        print(f"\n🔷 Nodes in the graph:")
        for node_name in agent.nodes.keys():
            print(f"   - {node_name}")
    
    if hasattr(agent, "edges"):
        print(f"\n🔗 Edges in the graph:")
        for edge in agent.edges:
            print(f"   - {edge}")
    
    # Get graph info
    if hasattr(agent, "get_graph"):
        try:
            graph = agent.get_graph()
            print(f"\n📈 Graph Type: {type(graph).__name__}")
            if hasattr(graph, "nodes"):
                print(f"   Total Nodes: {len(graph.nodes)}")
        except:
            pass
    
    print("="*60 + "\n")

# Terminal interaction loop
def main():
    """Main terminal interaction loop."""
    print("\n" + "="*60)
    print("🤖 LangChain Agent with MCP PostgreSQL Tools")
    print("="*60)
    if LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY:
        print(f"📊 LangSmith: Enabled (Project: {LANGCHAIN_PROJECT})")
    print("\nConnecting to MCP server and loading tools...")
    
    try:
        agent = create_agent_with_mcp_tools()
        print("✓ Agent ready!")
        
        # Show graph structure
        visualize_graph(agent)
        
        print("Type 'exit' or 'quit' to stop.")
        print("Type 'graph' to see the graph structure again.\n")
    except Exception as e:
        print(f"✗ Error initializing agent: {e}")
        print("\nMake sure:")
        print("1. PostgreSQL is running")
        print("2. Database is set up (run: python database_setup.py)")
        print("3. MCP server can be started (python mcp_postgres_server.py)")
        import traceback
        traceback.print_exc()
        return
    
    while True:
        try:
            query = input("\n👤 User: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ["exit", "quit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == "graph":
                visualize_graph(agent)
                continue
            
            print("\n" + "="*60)
            print("🔄 LangGraph Execution Flow:")
            print("="*60)
            
            # Use streaming to see step-by-step execution
            step_count = 0
            final_answer = None
            
            # Stream with "updates" mode to see each node execution
            for chunk in agent.stream(
                {"messages": [HumanMessage(content=query)]},
                stream_mode="updates",  # Show node updates step-by-step
            ):
                # Skip non-dict chunks (these are debug output or other stream modes)
                if not isinstance(chunk, dict):
                    continue
                
                step_count += 1
                
                # Process each node's update
                for node_name, node_data in chunk.items():
                    # Skip __start__ node
                    if node_name == "__start__":
                        continue
                    
                    print(f"\n📍 Step {step_count}: Node '{node_name}'")
                    
                    if isinstance(node_data, dict) and "messages" in node_data:
                        for msg in node_data["messages"]:
                            # Check for tool calls (AIMessage with tool_calls)
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                print(f"   🔧 Tool Calls:")
                                for tool_call in msg.tool_calls:
                                    tool_name = tool_call.get("name", "unknown")
                                    tool_args = tool_call.get("args", {})
                                    print(f"      → {tool_name}")
                                    if tool_args:
                                        # Clean up args display
                                        args_str = str(tool_args)
                                        # Remove __arg1 wrapper if present
                                        if "__arg1" in args_str:
                                            clean_args = tool_args.get("__arg1", "")
                                            if isinstance(clean_args, str) and len(clean_args) > 80:
                                                print(f"        Query: {clean_args[:80]}...")
                                            else:
                                                print(f"        Args: {clean_args}")
                                        elif len(args_str) > 100:
                                            print(f"        Args: {args_str[:100]}...")
                                        else:
                                            print(f"        Args: {args_str}")
                            
                            # Check for tool results (ToolMessage)
                            elif hasattr(msg, "name") and msg.name and hasattr(msg, "content"):
                                print(f"   📥 Tool Result from '{msg.name}':")
                                content = str(msg.content)
                                # Try to parse JSON for better display
                                try:
                                    import json
                                    parsed = json.loads(content)
                                    if isinstance(parsed, list) and len(parsed) > 0:
                                        if len(parsed) <= 3:
                                            print(f"      {json.dumps(parsed, indent=6)}")
                                        else:
                                            print(f"      [{len(parsed)} items] {json.dumps(parsed[:2], indent=6)}...")
                                    else:
                                        print(f"      {content[:200]}...")
                                except:
                                    if len(content) > 200:
                                        print(f"      {content[:200]}...")
                                    else:
                                        print(f"      {content}")
                            
                            # Check for AI responses (AIMessage without tool_calls)
                            elif hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_calls"):
                                content = str(msg.content)
                                # Store final answer
                                if not final_answer or len(content) > len(final_answer):
                                    final_answer = content
                                if len(content) > 150:
                                    print(f"   💬 AI: {content[:150]}...")
                                else:
                                    print(f"   💬 AI: {content}")
            
            print("\n" + "="*60)
            print("✅ Final Answer:")
            print("="*60)
            
            # Display final answer
            if final_answer:
                print(f"\n{final_answer}\n")
            else:
                # Fallback: get final state
                final_state = agent.invoke({"messages": [HumanMessage(content=query)]})
                if isinstance(final_state, dict) and "messages" in final_state:
                    messages = final_state["messages"]
                    for msg in reversed(messages):
                        if hasattr(msg, "content") and msg.content and not (hasattr(msg, "name") and msg.name):
                            print(f"\n{msg.content}\n")
                            break
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    main()
