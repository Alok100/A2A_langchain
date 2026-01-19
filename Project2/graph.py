
import json
from typing import TypedDict, Literal, Optional, Dict, Any
from datetime import date
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

from mcp_client import MCPClient
#from HelpServiceState import HelpServiceState


mcp_client = MCPClient()


llm = ChatOllama(
    model="qwen2.5:latest",
    temperature=0,
    num_predict=150  # Limit tokens
)


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
    