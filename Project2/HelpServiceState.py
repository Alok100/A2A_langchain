"""
A2A Help Service System with LangGraph
Minimal LLM calls, optimized MCP usage, single-task nodes
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from langsmith import traceable

from mcp_client import MCPClient
load_dotenv()
from config import *

llm = ChatOllama(
    model="qwen2.5:latest",
    temperature=0,
    num_predict=150  # Limit tokens
)

mcp_client = MCPClient()

graph = None
def get_graph():
    global graph
    if graph is None:
        from graph import build_graph
        graph = build_graph()
    return graph

def human_readeable_response(user_email: str, user_message: str, result):

    # Enhanced prompt for better response formatting
    prompt = f"""You are a helpful HR assistant. Transform the technical response into a natural, conversational answer that directly addresses the user's question.

USER QUESTION: "{user_message}"

CONTEXT:
- User: {user_email}
- Issue Category: {result.get('issue_category', 'unknown')}
- User Data Available: {result.get('user_data') is not None}
- Error Occurred: {result.get('error_message') is not None}

SYSTEM RESPONSE:
{result["final_response"]}

INSTRUCTIONS:
1. Start by directly addressing what the user asked
2. If the user asked "why can't I login" or similar, explain the specific reason based on the data
3. If there's an error (license inactive, account issues), explain it clearly and what they should do
4. If showing data, present it in a friendly, conversational way
5. Keep technical details minimal unless relevant
6. End with actionable next steps if applicable
7. Use emojis sparingly for visual clarity
8. Be empathetic and professional

EXAMPLES:
- If user asks "why can't I login?" and license is inactive → "I see you're having trouble logging in. The issue is that your license has expired on [date]. Please contact HR at hr@company.com to renew your license."
- If user asks "what is my leave balance?" → "Hi [name]! You currently have [X] days of leave available. Your leave balance is looking good!"
- If everything is fine but user reports login issue → "I checked your account and everything looks good on our end. Your account is active, license is valid, and you joined on [date]. The issue might be technical. Try resetting your password or clearing your browser cache. If that doesn't work, contact IT support."

Generate a natural, helpful response:"""

    response = llm.invoke([HumanMessage(content=prompt)])

    return response.content

# ============================================================================
# MAIN EXECUTION
# ============================================================================

@traceable(name="A2A_Help_Service", tags=["help-desk", "langgraph"])
def run_help_service(user_email: str, user_message: str):
    """Main entry point"""
    graph = get_graph() 
    initial_state = {
        "user_email": user_email,
        "user_message": user_message,
        "user_id": None,
        "user_data": None,
        "issue_category": None,
        "extracted_params": None,
        "db_result": None,
        "action_result": None,
        "error_message": None,
        "final_response": None,
        "llm_calls": 0,
        "mcp_calls": 0
    }
    
    result = graph.invoke(initial_state)
    print("the response before human readable is ", result)
    result["final_response"] = human_readeable_response(user_email, user_message, result)
    
    return result["final_response"]




