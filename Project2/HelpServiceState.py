"""
A2A Help Service System with LangGraph
Minimal LLM calls, optimized MCP usage, single-task nodes
"""

import json
from typing import TypedDict, Literal, Optional, Dict, Any
from datetime import datetime, date
from webbrowser import get
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# ============================================================================
# LANGSMITH TRACING SETUP
# ============================================================================
import os
from dotenv import load_dotenv
from langsmith import traceable

# Load environment variables from .env file
load_dotenv()

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "A2A-Help-Service")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

print(f"🔍 LangSmith Tracing: {'✅ Enabled' if os.getenv('LANGCHAIN_TRACING_V2') == 'true' else '❌ Disabled'}")
print(f"📊 LangSmith Project: {os.getenv('LANGCHAIN_PROJECT', 'A2A-Help-Service')}")



import sys
import os
sys.path.append(os.path.dirname(__file__))
from SettingUp_DB import get_connection


# ============================================================================
# STATE DEFINITION
# ============================================================================

class HelpServiceState(TypedDict):
    """Global state shared across all nodes"""
    user_email: str
    user_id: Optional[int]
    user_data: Optional[Dict[str, Any]]
    
    user_message: str
    issue_category: Optional[Literal[
        "query_employee", 
        "query_attendance", 
        "update_leave", 
        "update_attendance",
        "complex_report"
    ]]
    extracted_params: Optional[Dict[str, Any]]
    
    db_result: Optional[Any]
    action_result: Optional[str]
    error_message: Optional[str]
    
    final_response: Optional[str]
    llm_calls: int
    mcp_calls: int





# ============================================================================
# LLM SETUP
# ============================================================================

llm = ChatOllama(
    model="qwen2.5:latest",
    temperature=0,
    num_predict=150  # Limit tokens
)
from mcp_client import MCPClient
mcp_client = MCPClient()


# ============================================================================
# NODE 1: VALIDATE USER
# ============================================================================

def validate_user(state: HelpServiceState) -> HelpServiceState:
    """
    Single task: Validate user access
    No LLM call, 1 MCP call
    """
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    
    # Single MCP query to get user
    users = mcp_client.query("employees", {"name": state["user_email"]})
    
    if not users:
        state["error_message"] = "User not found"
        return state
    
    user = users[0]
    
    # All validation checks
    if not user.get("verified"):
        state["error_message"] = "Email not verified"
        return state
    
    if not user.get("active"):
        state["error_message"] = "Account inactive"
        return state
    
    if not user.get("license_active"):
        state["error_message"] = "License inactive"
        return state
    
    if user.get("license_expired"):
        state["error_message"] = "License expired"
        return state
    
    # Valid user
    state["user_id"] = user["id"]
    state["user_data"] = user
    return state


# ============================================================================
# NODE 2: CLASSIFY ISSUE (AGENT 1)
# ============================================================================

def classify_issue(state: HelpServiceState) -> HelpServiceState:
    """
    Single task: Classify user request
    1 LLM call, 0 MCP calls
    """
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    
    prompt = f"""Classify request and extract params. Output only JSON.
Request: {state['user_message']}

Categories:
- query_employee: Get employee info
- query_attendance: Get attendance records
- update_leave: Update leave days
- update_attendance: Add/update attendance
- complex_report: Analytics/aggregations

Output format:
{{"category": "...", "params": {{"key": "value"}}}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        result = json.loads(response.content.strip())
        state["issue_category"] = result["category"]
        state["extracted_params"] = result["params"]
    except:
        state["issue_category"] = "query_employee"
        state["extracted_params"] = {}
    
    return state


# ============================================================================
# NODE 3: ROUTE ISSUE
# ============================================================================

def route_issue(state: HelpServiceState) -> str:
    """
    Single task: Route to appropriate handler
    No LLM, no MCP
    """
    if state.get("error_message"):
        return "format_response"
    
    category = state["issue_category"]
    
    if category in ["query_employee", "query_attendance"]:
        return "fetch_simple_data"
    elif category in ["update_leave", "update_attendance"]:
        return "handle_update"
    else:
        return "handle_complex"


# ============================================================================
# NODE 4: FETCH SIMPLE DATA
# ============================================================================

def fetch_simple_data(state: HelpServiceState) -> HelpServiceState:
    """
    Single task: Fetch data for simple queries
    0 LLM calls, 1 MCP call
    """
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    
    category = state["issue_category"]
    params = state["extracted_params"]
    
    if category == "query_employee":
        result = mcp_client.query("employees", {"id": state["user_id"]})
    elif category == "query_attendance":
        filters = {"emp_id": state["user_id"]}
        if "date" in params:
            filters["date"] = params["date"]
        result = mcp_client.query("attendance", filters)
    else:
        result = []
    
    state["db_result"] = result
    return state


# ============================================================================
# NODE 5: HANDLE UPDATE (AGENT 2)
# ============================================================================

def handle_update(state: HelpServiceState) -> HelpServiceState:
    """
    Single task: Handle update requests
    1 LLM call for validation, 2 MCP calls (read + write)
    """
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    
    category = state["issue_category"]
    params = state["extracted_params"]
    
    # LLM validates business rules
    prompt = f"""Validate update request. Output only JSON.
Category: {category}
Params: {json.dumps(params)}
User: {json.dumps(state['user_data'])}

Check:
- Leave days: 0-30 range
- Attendance: valid date format, future dates not allowed
- Required fields present

Output: {{"valid": true/false, "reason": "..."}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        validation = json.loads(response.content.strip())
        if not validation["valid"]:
            state["error_message"] = validation["reason"]
            return state
    except:
        state["error_message"] = "Validation failed"
        return state
    
    # Perform update
    state["mcp_calls"] += 1
    
    if category == "update_leave":
        success = mcp_client.update(
            "employees",
            state["user_id"],
            {"leave_days": params.get("leave_days")}
        )
    elif category == "update_attendance":
        success = mcp_client.insert("attendance", {
            "emp_id": state["user_id"],
            "employee_name": state["user_data"]["name"],
            "date": params.get("date", str(date.today())),
            "check_in": params.get("check_in", "09:00"),
            "check_out": params.get("check_out", "17:00")
        })
    else:
        success = False
    
    if success:
        state["action_result"] = "Update successful"
    else:
        state["error_message"] = "Update failed"
    
    return state


# ============================================================================
# NODE 6: VERIFY UPDATE
# ============================================================================

def verify_update(state: HelpServiceState) -> HelpServiceState:
    """
    Single task: Verify update was applied
    0 LLM calls, 1 MCP call
    """
    if state.get("error_message"):
        return state
    
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    
    # Read back to verify
    result = mcp_client.query("employees", {"id": state["user_id"]})
    state["db_result"] = result
    
    return state


# ============================================================================
# NODE 7: HANDLE COMPLEX (AGENT 2)
# ============================================================================

def handle_complex(state: HelpServiceState) -> HelpServiceState:
    """
    Single task: Handle complex analytics
    1 LLM call, 2-3 MCP calls
    """
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    state["mcp_calls"] = state.get("mcp_calls", 0) + 2
    
    # Fetch relevant data
    employees = mcp_client.query("employees")
    attendance = mcp_client.query("attendance")
    
    # LLM generates analysis
    prompt = f"""Analyze and answer. Output only JSON.
Request: {state['user_message']}
Employees: {json.dumps(employees[:5])}...
Attendance: {json.dumps(attendance[:5])}...

Output: {{"answer": "concise answer", "data": []}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        result = json.loads(response.content.strip())
        state["db_result"] = result
    except:
        state["db_result"] = {"answer": response.content}
    
    return state


# ============================================================================
# NODE 8: FORMAT RESPONSE
# ============================================================================
def format_response(state: HelpServiceState) -> HelpServiceState:
    """
    Single task: Format final response
    0 LLM calls, 0 MCP calls
    """
    if state.get("error_message"):
        error_msg = f"❌ Error: {state['error_message']}"
        
        # Add user details if available
        if state.get("user_data"):
            user = state["user_data"]
            error_msg += f"\n\n👤 User Details:"
            error_msg += f"\n  - Name: {user.get('name', 'N/A')}"
            error_msg += f"\n  - Department: {user.get('department', 'N/A')}"
            error_msg += f"\n  - Date of Joining: {user.get('join_date', 'N/A')}"
            error_msg += f"\n  - License Status: {'✅ Active' if user.get('license_active') else '❌ Inactive'}"
            error_msg += f"\n  - Leave Days: {user.get('leave_days', 0)}"
        
        state["final_response"] = error_msg
        
    elif state.get("action_result"):
        state["final_response"] = f"✅ {state['action_result']}"
        if state.get("db_result"):
            state["final_response"] += f"\n\nUpdated data: {json.dumps(state['db_result'], indent=2)}"
            
    elif state.get("db_result"):
        # ✅ Check if it's a formatted message already
        if isinstance(state['db_result'], dict) and 'message' in state['db_result']:
            state["final_response"] = state['db_result']['message']
        # ✅ Format employee data nicely instead of raw JSON
        elif isinstance(state['db_result'], list) and len(state['db_result']) > 0:
            if 'name' in state['db_result'][0]:  # Employee data
                emp = state['db_result'][0]
                state["final_response"] = f"👤 Employee Information:\n\n"
                state["final_response"] += f"  • Name: {emp.get('name')}\n"
                state["final_response"] += f"  • Department: {emp.get('department')}\n"
                state["final_response"] += f"  • Email: {emp.get('email')}\n"
                state["final_response"] += f"  • License: {emp.get('license')} ({'✅ Active' if emp.get('license_active') else '❌ Inactive'})\n"
                state["final_response"] += f"  • Date of Joining: {emp.get('join_date')}\n"
                state["final_response"] += f"  • Leave Available: {emp.get('leave_days')} days\n"
            else:
                # Fallback to JSON for other data
                state["final_response"] = f"📊 Result:\n{json.dumps(state['db_result'], indent=2)}"
        else:
            state["final_response"] = f"📊 Result:\n{json.dumps(state['db_result'], indent=2)}"
    else:
        state["final_response"] = "✅ Request processed"
    
    # Add usage stats
    state["final_response"] += f"\n\n📈 Usage: {state.get('llm_calls', 0)} LLM calls, {state.get('mcp_calls', 0)} DB calls"
    
    return state
# ============================================================================
# BUILD GRAPH
# ============================================================================

def build_graph():
    """Build the LangGraph workflow"""
    workflow = StateGraph(HelpServiceState)
    
    # Add nodes
    workflow.add_node("validate_user", validate_user)
    workflow.add_node("classify_issue", classify_issue)
    workflow.add_node("fetch_simple_data", fetch_simple_data)
    workflow.add_node("handle_update", handle_update)
    workflow.add_node("verify_update", verify_update)
    workflow.add_node("handle_complex", handle_complex)
    workflow.add_node("format_response", format_response)
    
    # Set entry point
    workflow.set_entry_point("validate_user")
    
    # Add edges
    workflow.add_conditional_edges(
        "validate_user",
        lambda s: "classify_issue" if not s.get("error_message") else "format_response",
        {
            "classify_issue": "classify_issue",
            "format_response": "format_response"
        }
    )
    
    workflow.add_conditional_edges(
        "classify_issue",
        route_issue,
        {
            "fetch_simple_data": "fetch_simple_data",
            "handle_update": "handle_update",
            "handle_complex": "handle_complex",
            "format_response": "format_response"
        }
    )
    
    workflow.add_edge("fetch_simple_data", "format_response")
    workflow.add_edge("handle_update", "verify_update")
    workflow.add_edge("verify_update", "format_response")
    workflow.add_edge("handle_complex", "format_response")
    workflow.add_edge("format_response", END)

    graph = workflow.compile()

       # ✅ Save the graph visualization as PNG
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        
        # Save to file
        with open("help_service_graph.png", "wb") as f:
            f.write(png_bytes)
        print("✅ Graph saved as 'help_service_graph.png'")
    except Exception as e:
        print(f"⚠️ Could not save graph image: {e}")
    
    return graph
    
    
# ============================================================================
# MAIN EXECUTION
# ============================================================================

@traceable(name="A2A_Help_Service", tags=["help-desk", "langgraph"])
def run_help_service(user_email: str, user_message: str):
    """Main entry point"""
    graph = build_graph()
    
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
    result["final_response"] = response.content
    
    return result["final_response"]




# ============================================================================
# TEST EXAMPLES
# ============================================================================

if __name__ == "__main__":
    #print_graph_structure()
    
    # print("\n" + "="*70)
    # print("TEST 1: Simple Query")
    # print("="*70)
    # response = run_help_service("Amanda Lee", "Show my employee info")
    # print(response)
    
    # print("\n" + "="*70)
    # print("TEST 2: Update Request")
    # print("="*70)
    # response = run_help_service("Sarah Johnson", "I am not able to login");
    # print("the response is ",response)
    
    # print("\n" + "="*70)
    # print("TEST 3: Invalid User")
    # print("="*70)
    # response = run_help_service("James Garcia", "I am not able to apply for leaves for 2 days")
    # print(response)
    
    print("\n" + "="*70)
    print("TEST 4: Complex Query")
    print("="*70)
    response = run_help_service("David Wilson", "I want to change my department from Sales to Marketing?")
    print(response)