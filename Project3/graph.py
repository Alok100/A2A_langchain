import json
from typing import TypedDict, Literal, Optional, Dict, Any, List
from datetime import date
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

from mcp_client import MCPClient

# Policy documents for RAG (single-doc retrieval; only the selected doc is loaded)
try:
    from poc_data.hr_rules_content import POLICIES as HR_POLICIES
except Exception:
    HR_POLICIES = {}

mcp_client = MCPClient()

llm = ChatOllama(
    model="qwen2.5:latest",
    temperature=0,
    num_predict=150
)


class HelpServiceState(TypedDict):
    user_email: str
    user_id: Optional[int]
    user_data: Optional[Dict[str, Any]]
    admin_rights: bool
    user_message: str
    issue_category: Optional[Literal[
        "query_employee", "query_attendance", "update_leave", "update_attendance", "complex_report", "query_policy"
    ]]
    query_target: Optional[Literal["self", "other"]]  # self = logged-in user only, other = another employee
    context_employee_name: Optional[str]  # employee from previous message (for "her", "his", "that employee")
    context_employee_names: Optional[List[str]]  # when previous response had multiple employees (e.g. multiple Sarahs)
    context_employee_infos: Optional[List[Dict[str, Any]]]  # list of {"id", "name"} for disambiguation with IDs
    extracted_params: Optional[Dict[str, Any]]
    db_result: Optional[Any]
    action_result: Optional[str]
    error_message: Optional[str]
    final_response: Optional[str]
    llm_calls: int
    mcp_calls: int
    subject_employee_name: Optional[str]  # set after query/update of another employee, for next turn context
    subject_employee_names: Optional[List[str]]  # when multiple employees were shown (for disambiguation)
    subject_employee_infos: Optional[List[Dict[str, Any]]]  # list of {"id", "name"} for disambiguation by ID


def validate_user(state: HelpServiceState) -> HelpServiceState:
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    # Look up by email if user_email looks like email, else by name
    user_email = state.get("user_email") or ""
    filter_key = "email" if "@" in user_email else "name"
    users = mcp_client.query("employees", {filter_key: user_email})
    if not users:
        state["error_message"] = "User not found"
        return state
    user = users[0]
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
    state["user_id"] = user["id"]
    state["user_data"] = user
    return state


def classify_issue(state: HelpServiceState) -> HelpServiceState:
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    context_names = state.get("context_employee_names")
    if context_names and len(context_names) > 1:
        context_str = "Multiple: " + ", ".join(context_names)
    else:
        context_str = (state.get("context_employee_name") or "").strip() or "None"
    prompt = f"""Classify request and extract params. Output only JSON.
Request: {state['user_message']}
Logged-in user context: {state.get('user_email', '')}
Context (employee from previous message, if any): {context_str}

Categories:
- query_employee: Get employee info (own or another person)
- query_attendance: Get attendance *records* (show my/someone's actual clock-in/out, dates, history). NOT for "what does the policy say?" or "what is the default?"
- update_leave: Update leave days
- update_attendance: Add/update attendance
- complex_report: Analytics/aggregations
- query_policy: Questions about what the *policy or rules say* (defaults, guidelines, rules). Examples: "what is the default check-in?", "what does the attendance policy say?", "what are the leave rules?", "policy on expense?", "grievance process?". Use this when the user asks about policy/rules/defaults, not when they want to see their own or someone's actual data.

For query_employee and query_attendance, also set "target":
- "self": question is about the logged-in user (my join date, my attendance, etc.)
- "other": question is about another employee (e.g. "When did John join?", "Sarah's email"). When "other", include in params: employee_name and/or employee_email if mentioned.

For update_leave and update_attendance, also set "target":
- "self": update own leave/attendance (e.g. "set my leave to 10")
- "other": update another employee (e.g. "set Sarah's leave to 15", "mark attendance for John"). When "other", include in params: employee_name and/or employee_email, plus leave_days/date/check_in/check_out as needed.
IMPORTANT: If the user says "her", "his", "their", "that employee", "the same person", "that person", "them" and Context above is not "None", they mean that context employee. Set target to "other" and include employee_name in params. If Context is "Multiple: A, B, C" and the user did not specify which one, use employee_name: the first name or a short form (the system will ask which one).
When multiple employees match, the user can specify by full name or Employee ID (6-digit, e.g. 100001). Include employee_id or company_id (numeric) in params when mentioned (e.g. "employee 100001", "ID 100001").

Rule: "What is the default check-in?", "what does the policy say about X?", "what are the rules for Y?" → query_policy (answer from policy doc). "Show my attendance", "when did I check in last week?" → query_attendance (fetch records).

Output format:
{{"category": "...", "target": "self" or "other", "params": {{"key": "value"}}}}"""
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
        state["issue_category"] = result.get("category", "query_employee")
        state["query_target"] = result.get("target", "self")
        state["extracted_params"] = result.get("params") or {}
    except Exception:
        state["issue_category"] = "query_employee"
        state["query_target"] = "self"
        state["extracted_params"] = {}
    return state


def route_issue(state: HelpServiceState) -> str:
    if state.get("error_message"):
        return "format_response"
    category = state["issue_category"]
    # Employee can only view their own details; HR can view any employee
    if category in ["query_employee", "query_attendance"]:
        if not state.get("admin_rights") and state.get("query_target") == "other":
            state["error_message"] = (
                "You can only view your own details. To look up other employees, contact HR."
            )
            return "format_response"
        return "fetch_simple_data"
    # Employee can only update their own leave/attendance; HR can update any employee
    if category in ["update_leave", "update_attendance"]:
        if not state.get("admin_rights") and state.get("query_target") == "other":
            state["error_message"] = (
                "You can only update your own leave or attendance. Only HR can update other employees."
            )
            return "format_response"
        return "handle_update"
    # complex_report: HR only (admin_rights = True)
    if category == "complex_report" and not state.get("admin_rights"):
        state["error_message"] = "Access denied. Complex reports and analytics are for HR only."
        return "format_response"
    if category == "query_policy":
        return "rag_policy"
    return "handle_complex"


def _disambiguation_message(infos: list, names: list) -> str:
    """Build message asking user to specify by full name or company Employee ID (6-digit, e.g. 100001)."""
    if infos:
        parts = []
        for info in infos:
            if info.get("name"):
                eid = info.get("company_id") or info.get("id")
                parts.append(f"{info.get('name', '')} (Employee ID: {eid})")
        if parts:
            return "Multiple employees match. Which one do you mean? Please specify by full name or Employee ID (6-digit), e.g.: " + ", ".join(parts)
    return "Multiple employees match. Which one do you mean? Please specify the full name, e.g.: " + ", ".join(names)


def _resolve_employee_id(state: HelpServiceState) -> Optional[int]:
    """If HR is asking about another employee, resolve name/email/company_id to internal id; else return logged-in user id."""
    if not state.get("admin_rights"):
        return state.get("user_id")
    params = state.get("extracted_params") or {}
    target = state.get("query_target", "self")
    if target != "other":
        return state.get("user_id")
    name = params.get("employee_name") or params.get("name")
    email = params.get("employee_email") or params.get("email")
    if name:
        users = mcp_client.query("employees", {"name": name})
        if users:
            return users[0].get("id")
    if email:
        users = mcp_client.query("employees", {"email": email})
        if users:
            return users[0].get("id")
    raw_id = params.get("employee_id") or params.get("id") or params.get("company_id")
    if raw_id is not None:
        try:
            uid = int(raw_id)
            # 6-digit company Employee ID (100001, 100002...) vs internal id (1, 2, 3...)
            if uid >= 100000:
                users = mcp_client.query("employees", {"company_id": uid})
            else:
                users = mcp_client.query("employees", {"id": uid})
            if users:
                return users[0].get("id")
            return uid if uid < 100000 else None
        except (ValueError, TypeError):
            pass
    return state.get("user_id")


def _resolve_target_employee(state: HelpServiceState) -> tuple:
    """Return (emp_id, emp_data) for the employee being updated (self or other). emp_data is the full row for attendance insert name.
    When context has multiple and params don't specify full name or employee_id, returns (None, None) so caller will ask 'Which one?'"""
    target = state.get("query_target", "self")
    if target != "other" or not state.get("admin_rights"):
        return state.get("user_id"), state.get("user_data")
    params = state.get("extracted_params") or {}
    context_infos = state.get("context_employee_infos") or []
    context_names = state.get("context_employee_names") or []
    # When multiple match: accept employee_id or company_id (6-digit, e.g. 100001)
    if len(context_infos) > 1 or len(context_names) > 1:
        raw_id = params.get("employee_id") or params.get("id") or params.get("company_id")
        if raw_id is not None:
            try:
                uid = int(raw_id)
                for info in context_infos:
                    if info.get("id") == uid or info.get("company_id") == uid or str(info.get("company_id", "")) == str(uid):
                        if uid >= 100000:
                            users = mcp_client.query("employees", {"company_id": uid})
                        else:
                            users = mcp_client.query("employees", {"id": uid})
                        if users:
                            return users[0].get("id"), users[0]
                        return uid if uid < 100000 else None, None
            except (ValueError, TypeError):
                pass
        name = (params.get("employee_name") or params.get("name") or "").strip()
        if name:
            name_lower = name.lower()
            match = next((c for c in context_names if c and c.lower() == name_lower), None)
            if match:
                users = mcp_client.query("employees", {"name": match})
                if users:
                    return users[0].get("id"), users[0]
            else:
                return None, None
        return None, None
    name = (params.get("employee_name") or params.get("name") or "").strip()
    if name:
        users = mcp_client.query("employees", {"name": name})
        if users:
            return users[0].get("id"), users[0]
    email = params.get("employee_email") or params.get("email")
    if email:
        users = mcp_client.query("employees", {"email": email})
        if users:
            return users[0].get("id"), users[0]
    raw_id = params.get("employee_id") or params.get("id") or params.get("company_id")
    if raw_id is not None:
        try:
            uid = int(raw_id)
            if uid >= 100000:
                users = mcp_client.query("employees", {"company_id": uid})
            else:
                users = mcp_client.query("employees", {"id": uid})
            if users:
                return users[0].get("id"), users[0]
            return (uid, None) if uid < 100000 else (state.get("user_id"), state.get("user_data"))
        except (ValueError, TypeError):
            pass
    return state.get("user_id"), state.get("user_data")


def fetch_simple_data(state: HelpServiceState) -> HelpServiceState:
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    category = state["issue_category"]
    params = state.get("extracted_params") or {}
    context_names = state.get("context_employee_names") or []
    context_infos = state.get("context_employee_infos") or []
    # When previous response had multiple employees, require full name or employee ID to disambiguate
    if (len(context_names) > 1 or len(context_infos) > 1) and state.get("query_target") == "other":
        raw_id = params.get("employee_id") or params.get("id") or params.get("company_id")
        if raw_id is not None:
            try:
                uid = int(raw_id)
                match = any(
                    info.get("id") == uid or info.get("company_id") == uid or str(info.get("company_id", "")) == str(uid)
                    for info in context_infos
                )
                if match:
                    state["extracted_params"] = {**(state.get("extracted_params") or {}), "employee_id": uid}
                    if uid >= 100000:
                        state["extracted_params"]["company_id"] = uid
                    params = state["extracted_params"]
                else:
                    state["error_message"] = _disambiguation_message(context_infos, context_names)
                    return state
            except (ValueError, TypeError):
                state["error_message"] = _disambiguation_message(context_infos, context_names)
                return state
        else:
            name = (params.get("employee_name") or params.get("name") or "").strip()
            name_match = next((c for c in context_names if c and c.lower() == name.lower()), None) if name else None
            if not name_match:
                state["error_message"] = _disambiguation_message(context_infos, context_names)
                return state
            state["extracted_params"] = {**(state.get("extracted_params") or {}), "employee_name": name_match}
            params = state["extracted_params"]
    # HR query by first/partial name only: return all matching employees (e.g. all "Sarah")
    if (
        category == "query_employee"
        and state.get("admin_rights")
        and state.get("query_target") == "other"
    ):
        name = params.get("employee_name") or params.get("name")
        email = params.get("employee_email") or params.get("email")
        emp_id_param = params.get("employee_id") or params.get("id")
        if name and not email and emp_id_param is None:
            result = mcp_client.query("employees", {"name_contains": name})
            state["db_result"] = result
            return state
    emp_id = _resolve_employee_id(state)
    if emp_id is None:
        state["error_message"] = "Could not identify the employee to look up."
        return state
    if category == "query_employee":
        result = mcp_client.query("employees", {"id": emp_id})
    elif category == "query_attendance":
        filters = {"emp_id": emp_id}
        if "date" in params:
            filters["date"] = params["date"]
        result = mcp_client.query("attendance", filters)
    else:
        result = []
    state["db_result"] = result
    return state


def handle_update(state: HelpServiceState) -> HelpServiceState:
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    category = state["issue_category"]
    params = state["extracted_params"] or {}
    target_emp_id, target_emp_data = _resolve_target_employee(state)
    if target_emp_id is None:
        context_infos = state.get("context_employee_infos") or []
        context_names = state.get("context_employee_names") or []
        if len(context_infos) > 1 or len(context_names) > 1:
            state["error_message"] = _disambiguation_message(context_infos, context_names)
        else:
            state["error_message"] = "Could not identify the employee to update."
        return state
    if target_emp_id != state.get("user_id"):
        state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    state["update_target_id"] = target_emp_id
    if category == "update_attendance":
        if not state.get("admin_rights") and not (state.get("user_data") and state.get("user_data").get("license_active")):
            state["error_message"] = "Your license must be active to mark your own attendance."
            return state
    if category == "update_leave":
        prompt = f"""Validate leave update request. Output only JSON.
Category: {category}
Params: {json.dumps(params)}
Target employee: {json.dumps(target_emp_data or {{'id': target_emp_id}})}
Check: Leave days 0-30, required fields present.
Output: {{"valid": true/false, "reason": "..."}}"""
        response = llm.invoke([HumanMessage(content=prompt)])
        try:
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            validation = json.loads(content)
            if not validation.get("valid", True):
                state["error_message"] = validation.get("reason", "Validation failed")
                return state
        except Exception:
            leave_days = params.get("leave_days")
            if leave_days is not None:
                try:
                    if int(leave_days) < 0 or int(leave_days) > 30:
                        state["error_message"] = "Leave days must be 0-30"
                        return state
                except (ValueError, TypeError):
                    state["error_message"] = f"Invalid leave_days: {leave_days}"
                    return state
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    target_name = (target_emp_data or {}).get("name", "")
    if category == "update_leave":
        success = mcp_client.update("employees", target_emp_id, {"leave_days": params.get("leave_days")})
    elif category == "update_attendance":
        attendance_date = params.get("date")
        if not attendance_date or str(attendance_date).lower() in ["today", "now"]:
            attendance_date = str(date.today())
        success = mcp_client.insert("attendance", {
            "emp_id": target_emp_id,
            "employee_name": target_name,
            "date": attendance_date,
            "check_in": params.get("check_in", "09:00"),
            "check_out": params.get("check_out", "17:00")
        })
    else:
        success = False
    if success:
        state["action_result"] = "Update successful"
    else:
        state["error_message"] = f"Update failed: {category}"
    return state


def verify_update(state: HelpServiceState) -> HelpServiceState:
    if state.get("error_message"):
        return state
    state["mcp_calls"] = state.get("mcp_calls", 0) + 1
    emp_id = state.get("update_target_id") or state.get("user_id")
    state["db_result"] = mcp_client.query("employees", {"id": emp_id})
    return state


def rag_policy(state: HelpServiceState) -> HelpServiceState:
    """Answer policy/rules questions using only the one relevant document (no full corpus)."""
    if not HR_POLICIES:
        state["error_message"] = "Policy documents are not available."
        return state
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    policy_names = list(HR_POLICIES.keys())
    prompt_select = f"""The user is asking about HR policy or rules. Which single policy document is relevant?
Policy options (use exactly one of these keys): {json.dumps(policy_names)}

User request: {state['user_message']}

Output only JSON: {{"policy_key": "ExactKeyFromList"}}
If the question could apply to multiple policies, pick the single most relevant one."""
    response_select = llm.invoke([HumanMessage(content=prompt_select)])
    try:
        content = response_select.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
        policy_key = result.get("policy_key") or ""
    except Exception:
        policy_key = policy_names[0] if policy_names else ""
    if policy_key not in HR_POLICIES:
        policy_key = policy_names[0] if policy_names else ""
    doc_text = HR_POLICIES[policy_key]
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    prompt_answer = f"""Answer the user's question using ONLY the following policy document. Do not use other knowledge.
If the document does not contain the answer, say so briefly.

Policy document ({policy_key}):
---
{doc_text}
---

User question: {state['user_message']}

Give a concise, accurate answer based only on the document above."""
    response_answer = llm.invoke([HumanMessage(content=prompt_answer)])
    answer = (response_answer.content or "").strip()
    state["db_result"] = {"message": answer, "source_policy": policy_key}
    return state


def handle_complex(state: HelpServiceState) -> HelpServiceState:
    state["llm_calls"] = state.get("llm_calls", 0) + 1
    state["mcp_calls"] = state.get("mcp_calls", 0) + 2
    employees = mcp_client.query("employees")
    attendance = mcp_client.query("attendance")
    prompt = f"""Analyze and answer. Output only JSON.
Request: {state['user_message']}
Employees: {json.dumps(employees[:5])}...
Attendance: {json.dumps(attendance[:5])}...
Output: {{"answer": "concise answer", "data": []}}"""
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        state["db_result"] = json.loads(response.content.strip())
    except Exception:
        state["db_result"] = {"answer": response.content}
    return state


def format_response(state: HelpServiceState) -> HelpServiceState:
    if state.get("error_message"):
        error_msg = f"❌ Error: {state['error_message']}"
        if state.get("user_data"):
            u = state["user_data"]
            error_msg += f"\n\n👤 User: {u.get('name')}, Dept: {u.get('department')}, License: {'✅' if u.get('license_active') else '❌'}, Leave: {u.get('leave_days')}"
        state["final_response"] = error_msg
    elif state.get("action_result"):
        state["final_response"] = f"✅ {state['action_result']}"
        if state.get("db_result"):
            state["final_response"] += f"\n\n{json.dumps(state['db_result'], indent=2)}"
    elif state.get("db_result"):
        if isinstance(state["db_result"], dict) and "message" in state["db_result"]:
            state["final_response"] = state["db_result"]["message"]
        elif isinstance(state["db_result"], list) and state["db_result"] and "name" in state["db_result"][0]:
            parts = []
            for i, emp in enumerate(state["db_result"], 1):
                no_ = emp.get("id", "")
                company_id = emp.get("company_id", "") or str(100000 + (no_ if no_ else 0))[:6]
                parts.append(
                    f"👤 {emp.get('name', '')} | No.: {no_} | Employee ID: {company_id}\n"
                    f"  Department: {emp.get('department', '')}\n"
                    f"  Email: {emp.get('email', '')}\n"
                    f"  License: {emp.get('license', '')} | Join: {emp.get('join_date', '')} | Leave: {emp.get('leave_days', '')} days"
                )
                if i < len(state["db_result"]):
                    parts.append("")
            state["final_response"] = "\n".join(parts)
        else:
            state["final_response"] = f"📊 Result:\n{json.dumps(state['db_result'], indent=2)}"
    else:
        state["final_response"] = "✅ Request processed"
    state["final_response"] += f"\n\n📈 Usage: {state.get('llm_calls', 0)} LLM calls, {state.get('mcp_calls', 0)} DB calls"
    # Set subject for next turn: single name or list with IDs (for disambiguation by name or company Employee ID)
    if state.get("query_target") == "other" and state.get("db_result") and isinstance(state["db_result"], list) and state["db_result"] and "name" in state["db_result"][0]:
        names = [e["name"] for e in state["db_result"] if e.get("name")]
        infos = [{"id": e.get("id"), "company_id": e.get("company_id"), "name": e.get("name", "")} for e in state["db_result"] if e.get("name")]
        if len(names) > 1:
            state["subject_employee_names"] = names
            state["subject_employee_infos"] = infos
            state["subject_employee_name"] = None
        else:
            state["subject_employee_name"] = names[0] if names else None
            state["subject_employee_names"] = None
            state["subject_employee_infos"] = None
    elif state.get("query_target") == "other":
        params = state.get("extracted_params") or {}
        state["subject_employee_name"] = params.get("employee_name") or params.get("name")
        state["subject_employee_names"] = None
        state["subject_employee_infos"] = None
    elif state.get("action_result") and state.get("db_result") and isinstance(state["db_result"], list) and state["db_result"] and "name" in state["db_result"][0]:
        state["subject_employee_name"] = state["db_result"][0]["name"]
        state["subject_employee_names"] = None
        state["subject_employee_infos"] = None
    return state


def build_graph():
    workflow = StateGraph(HelpServiceState)
    workflow.add_node("validate_user", validate_user)
    workflow.add_node("classify_issue", classify_issue)
    workflow.add_node("fetch_simple_data", fetch_simple_data)
    workflow.add_node("handle_update", handle_update)
    workflow.add_node("verify_update", verify_update)
    workflow.add_node("rag_policy", rag_policy)
    workflow.add_node("handle_complex", handle_complex)
    workflow.add_node("format_response", format_response)
    workflow.set_entry_point("validate_user")
    workflow.add_conditional_edges(
        "validate_user",
        lambda s: "classify_issue" if not s.get("error_message") else "format_response",
        {"classify_issue": "classify_issue", "format_response": "format_response"}
    )
    workflow.add_conditional_edges(
        "classify_issue", route_issue,
        {"fetch_simple_data": "fetch_simple_data", "handle_update": "handle_update",
         "handle_complex": "handle_complex", "rag_policy": "rag_policy", "format_response": "format_response"}
    )
    workflow.add_edge("fetch_simple_data", "format_response")
    workflow.add_edge("handle_update", "verify_update")
    workflow.add_edge("verify_update", "format_response")
    workflow.add_edge("rag_policy", "format_response")
    workflow.add_edge("handle_complex", "format_response")
    workflow.add_edge("format_response", END)
    graph = workflow.compile()

    # Save graph visualization: try mermaid.ink API first, then Pyppeteer (works offline)
    import os
    out_path = os.path.join(os.path.dirname(__file__), "help_service_graph.png")
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        print(f"Graph saved as {out_path}")
    except Exception as e:
        err = str(e)
        if "mermaid.ink" in err or "Failed to reach" in err:
            try:
                from langchain_core.runnables.graph import MermaidDrawMethod
                png_bytes = graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.PYPPETEER)
                with open(out_path, "wb") as f:
                    f.write(png_bytes)
                print(f"Graph saved as {out_path} (local Pyppeteer)")
            except Exception as e2:
                print(f"Graph PNG skipped: {e2}")
        else:
            try:
                from langchain_core.runnables.graph import MermaidDrawMethod
                png_bytes = graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.PYPPETEER)
                with open(out_path, "wb") as f:
                    f.write(png_bytes)
                print(f"Graph saved as {out_path} (local Pyppeteer)")
            except Exception as e2:
                print(f"Could not save graph image: {e}")
    return graph
