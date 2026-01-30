"""
A2A Help Service – same as Project2, used by CLI.
"""
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langsmith import traceable

import config  # noqa: F401 - load env and LangSmith
from mcp_client import MCPClient

llm = ChatOllama(model="qwen2.5:latest", temperature=0, num_predict=150)
mcp_client = MCPClient()

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        from graph import build_graph
        _graph = build_graph()
    return _graph


def human_readeable_response(user_email: str, user_message: str, result: dict) -> str:
    prompt = f"""You are a helpful HR assistant. Transform the technical response into a natural, conversational answer.

USER QUESTION: "{user_message}"
CONTEXT: User: {user_email}, Category: {result.get('issue_category')}, Error: {result.get('error_message') is not None}
SYSTEM RESPONSE (use ONLY these exact values; do not replace with placeholders like [Department Name] or [Join Date]):
{result["final_response"]}

Rules: Use the exact values from SYSTEM RESPONSE. Do not invent or substitute placeholders. Keep all names, dates, emails, departments, and numbers exactly as shown. Give a short, friendly reply."""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def _collect_path_and_final_state(graph, initial_state):
    """Run graph via stream(updates + values); return (execution_path, final_state)."""
    path = []
    final_state = None
    for event in graph.stream(initial_state, stream_mode=["updates", "values"]):
        # With stream_mode list: event is (mode, chunk)
        if isinstance(event, tuple) and len(event) == 2:
            mode, chunk = event
            if mode == "updates":
                # chunk is {node_name: state_update}; with subgraphs can be (namespace, updates)
                if isinstance(chunk, dict):
                    for node_name in chunk:
                        path.append(node_name)
                elif isinstance(chunk, (list, tuple)) and len(chunk) == 2:
                    _, updates = chunk
                    if isinstance(updates, dict):
                        for node_name in updates:
                            path.append(node_name)
            elif mode == "values":
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    _, state = chunk
                    final_state = state
                else:
                    final_state = chunk
        else:
            if isinstance(event, dict):
                for node_name in event:
                    path.append(node_name)
    if final_state is None:
        final_state = graph.invoke(initial_state)
    return path, final_state


@traceable(name="A2A_Help_Service", tags=["help-desk", "langgraph", "project3"])
def run_help_service(user_email: str, user_message: str, admin_rights: bool = False, context_employee_name: str = None, context_employee_names: list = None, context_employee_infos: list = None):
    """Run help service; returns (response_str, execution_path, subject_employee_name, subject_employee_names, subject_employee_infos).
    context_employee_infos: list of {"id", "name"} when previous response had multiple employees (for disambiguation by ID).
    subject_employee_infos: pass as context_employee_infos next turn when multiple were shown."""
    graph = get_graph()
    initial_state = {
        "user_email": user_email,
        "user_message": user_message,
        "user_id": None,
        "user_data": None,
        "admin_rights": admin_rights,
        "issue_category": None,
        "query_target": None,
        "context_employee_name": context_employee_name or None,
        "context_employee_names": context_employee_names if context_employee_names else None,
        "context_employee_infos": context_employee_infos if context_employee_infos else None,
        "extracted_params": None,
        "db_result": None,
        "action_result": None,
        "error_message": None,
        "final_response": None,
        "llm_calls": 0,
        "mcp_calls": 0,
    }
    execution_path, result = _collect_path_and_final_state(graph, initial_state)
    result["final_response"] = human_readeable_response(user_email, user_message, result)
    subject = result.get("subject_employee_name")
    subject_list = result.get("subject_employee_names")
    subject_infos = result.get("subject_employee_infos")
    return result["final_response"], execution_path, subject, subject_list, subject_infos
