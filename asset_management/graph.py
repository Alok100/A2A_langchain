
import json
from typing import TypedDict, Literal, Optional, Dict, Any
from datetime import date
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
import streamlit as st
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


def intent(state: HelpServiceState) -> HelpServiceState:
    """
    Classify user intent using LLM
    Possible intents:
    - report_asset_issue: User wants to report a problem
    - update_asset: User wants to update asset info
    - check_asset_status: User wants to check their assets
    - assign_asset: User wants to request/assign an asset
    - remove_asset: User wants to return an asset
    """
    
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    
    user_message = state["user_message"]
    
    # Create prompt for intent classification
    prompt = f"""Classify the following user message into ONE of these intents:

    1. report_asset_issue - User is reporting a problem with an asset
    2. update_asset - User wants to update asset information
    3. check_asset_status - User wants to see their allocated assets or asset status
    4. assign_asset - User wants to request or assign an asset
    5. remove_asset - User wants to return/deallocate an asset

    User message: "{user_message}"

    Respond with ONLY the intent name (e.g., "check_asset_status"). No explanation.

    Intent:"""
    
    # Call LLM
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        intent_result = response.content.strip().lower()
        
        # Validate intent
        valid_intents = [
            "report_asset_issue",
            "update_asset", 
            "check_asset_status",
            "assign_asset",
            "remove_asset"
        ]
        
        if intent_result in valid_intents:
            state["issue_category"] = intent_result
        else:
            # Fallback: Try to match keywords
            intent_result = classify_by_keywords(user_message)
            state["issue_category"] = intent_result
            
    except Exception as e:
        state["error_message"] = f"Intent classification failed: {str(e)}"
        return state
    
    return state


def classify_by_keywords(message: str) -> str:
    """Fallback keyword-based classification"""
    message_lower = message.lower()
    
    # Check for keywords
    if any(word in message_lower for word in ["broken", "issue", "problem", "not working", "error", "bug"]):
        return "report_asset_issue"
    
    if any(word in message_lower for word in ["my assets", "show", "list", "what do i have", "check", "status"]):
        return "check_asset_status"
    
    if any(word in message_lower for word in ["need", "request", "assign", "get", "want"]):
        return "assign_asset"
    
    if any(word in message_lower for word in ["return", "give back", "remove", "deallocate"]):
        return "remove_asset"
    
    if any(word in message_lower for word in ["update", "change", "modify"]):
        return "update_asset"
    
    # Default to check status
    return "check_asset_status"

def validate_user_role(state: HelpServiceState) -> HelpServiceState:
    """
    validate user role if employee or HR or Manager checking the db 
    """
    st.session_state['user_role'] = mcp_client.get_user_role(state['user_id'])
    if st.session_state['user_role'] == 'employee':
        return state
    elif st.session_state['user_role'] == 'HR':
        return state
    elif st.session_state['user_role'] == 'Manager':
        return state
    else:
        return state


