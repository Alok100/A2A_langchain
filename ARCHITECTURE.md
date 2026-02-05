# AI-Powered HR Decision Assistant — Architecture Specification

This document is the **buildable architecture** derived from *AI-Powered HR Decision Assistant* (LangGraph + MCP + A2A). Use it as the blueprint before implementing.

---

## 1. System Overview

| Concept | Description |
|--------|-------------|
| **What it is** | Policy-aware, explainable AI decision engine for HR (attendance, leave, timesheet, assets). Not a chatbot — reasons over policy, validates before DB updates, escalates when needed. |
| **A2A** | Reasoning (agents collaborate). |
| **MCP** | Execution (DB, auth, semantic search, approval, audit). |

**Core principles:** Natural language in → intent + policy + data reasoning → guardrails → optional HITL → MCP updates → explainable response out.

---

## 2. Two Graphs (High Level)

| Graph | When it runs | Purpose |
|-------|----------------|--------|
| **Online Decision Graph** | Per user request (runtime) | Validate user → load memory → classify → route → reason (policy + data) → guardrails → HITL if needed → execute → explain. |
| **Offline Policy Ingestion Graph** | Batch / on doc change | PDFs → extract text → chunk → embed → store in vector DB (long-doc memory for RAG). |

---

## 3. Online Decision Graph — Node Map

### 3.1 Flow (Conceptual Order)

```
START
  → validate_user          (MCP: auth + role; set admin_rights)
  → load_session_memory    (short-term: recent turns, subject employee, etc.)
  → load_long_term_memory  (optional: user profile, preferences, patterns — MCP/DB)
  → user_input             (natural language query enters state)
  → classify_issue         (LLM: intent → domain, operation, sensitivity, needs_policy)
  → route_by_intent        (conditional: read / policy_only / write)
```

**Branch 1 — Simple read (e.g. "How many leaves left?", "Which laptop for me?")**
```
  → fetch_simple_data      (MCP: query employees, attendance, timesheet, assets)
  → [optional] policy_lookup_if_needed (RAG if answer must cite policy)
  → format_response
```

**Branch 2 — Policy Q&A only (e.g. "What is bereavement leave policy?")**
```
  → rag_policy_retrieve    (MCP semantic search over policy embeddings)
  → policy_reasoning_agent (A2A: interpret clauses → rules/constraints)
  → format_response
```

**Branch 3 — Write / update (leave apply, attendance correction, timesheet submit, asset request)**
```
  → draft_action_plan           (LLM: proposed_action — type, target_table, fields, reason)
  → [parallel] policy_reasoning_agent + data_reasoning_agent
  → critic_compliance_agent     (A2A: second-pass review)
  → decision_guardrails        (LangGraph conditional)
       ├─ NEED_CLARIFICATION → ask_clarifying_question → (loop back to classify or draft)
       ├─ NEED_HITL_APPROVAL  → human_in_the_loop → await_approval → execute_update (if approved)
       ├─ APPROVE_AUTOMATIC   → execute_update
       └─ DENY                 → format_response (denial + reason)
  → execute_update             (MCP: DB write only after guardrails/approval)
  → persist_audit_log          (MCP: decision, why, policy_reference, before/after)
  → format_response
```

**Optional (can run in parallel after classify or before format):**
- **sentiment_agent** (A2A): frustration → escalate / human-friendly mode
- **prediction_agent** (A2A): leave exhaustion, attendance risk, anomalies

**Final**
```
  → format_response   (must include: decision, why, policy_reference — explainability contract)
  → update_short_term_memory  (save turn + state for next request)
  → END
```

### 3.2 Node Summary Table

| Node | Type | Purpose |
|------|------|--------|
| `validate_user` | MCP | Auth + role (employee / HR / CEO); set admin_rights. |
| `load_session_memory` | Memory | Load short-term: recent turns, subject employee, pending clarification. |
| `load_long_term_memory` | MCP/DB | Load user profile, preferences, patterns (optional). |
| `classify_issue` | LLM | Intent: domain (attendance \| leave \| timesheet \| asset \| policy_only \| other), operation (read \| write \| mixed), sensitivity, needs_policy. |
| `route_by_intent` | Logic | Conditional edge to Branch 1 / 2 / 3. |
| `fetch_simple_data` | MCP | Read employees, attendance, timesheet, assets. |
| `rag_policy_retrieve` | MCP | Semantic search over policy chunks (vector DB). |
| `policy_reasoning_agent` | A2A | Interpret retrieved policy → rules/constraints. |
| `draft_action_plan` | LLM | Proposed action (type, table, fields, reason). |
| `data_reasoning_agent` | A2A | Validate SQL/constraints before execution. |
| `critic_compliance_agent` | A2A | Review decision and compliance. |
| `decision_guardrails` | Logic | Route: clarify / HITL / approve / deny. |
| `ask_clarifying_question` | LLM | 1–2 targeted questions; then re-route. |
| `human_in_the_loop` | MCP | Create approval request for manager/HR. |
| `await_approval_event` | MCP/polling | Wait for approval; then execute or deny. |
| `execute_update` | MCP | DB update (leave, attendance, timesheet, asset). |
| `persist_audit_log` | MCP | Store reasoning_output (decision, why, policy_reference). |
| `format_response` | LLM | Build explainable response (decision, why, policy_reference). |
| `update_short_term_memory` | Memory | Persist turn + state after response. |

---

## 4. Offline Policy Ingestion Graph

| Step | Node / Step | Purpose |
|------|----------------|--------|
| 1 | `ingest_docs_start` | Input: PDFs (leave, attendance, timesheet, asset, code of conduct, etc.). |
| 2 | `extract_text` | PDF → raw text. |
| 3 | `chunk_documents` | Split into chunks; metadata: doc_title, section, page. |
| 4 | `embed_chunks` | Embedding model (e.g. text-embedding-ada-002 or local) → vectors. |
| 5 | `upsert_vector_store` | Store in DB/vector store: doc_title, chunk_id, content, embedding, metadata. |
| 6 | `build_policy_index_manifest` | Doc versions + last updated (for freshness). |
| 7 | `ingest_docs_end` | Done. |

**Storage schema (conceptual):** One row per chunk: `doc_title`, `chunk` (or `content`), `embedding` (vector). No separate table per conversation.

---

## 5. State (LangGraph State)

Suggested fields for the **Online** graph (extend as needed):

| Field | Type | Purpose |
|-------|------|--------|
| `user_id`, `user_email`, `admin_rights` | — | From validate_user. |
| `user_message` | str | Current natural language input. |
| `short_term_memory` | dict/list | Loaded/updated session context. |
| `long_term_memory` | dict | User profile, preferences, patterns (optional). |
| `intent` | object | domain, operation, sensitivity, needs_policy. |
| `extracted_params` | dict | Entities, dates, amounts. |
| `proposed_action` | object | From draft_action_plan. |
| `policy_chunks` | list | Retrieved from RAG. |
| `policy_interpretation` | str/object | From policy_reasoning_agent. |
| `data_validation_result` | object | From data_reasoning_agent. |
| `critic_result` | object | From critic_compliance_agent. |
| `guardrail_decision` | enum | NEED_CLARIFICATION \| NEED_HITL_APPROVAL \| APPROVE_AUTOMATIC \| DENY. |
| `reasoning_output` | object | **Mandatory for explainability:** decision, why, policy_reference. |
| `db_result`, `error_message` | — | For format_response. |
| `final_response` | str | User-facing explainable answer. |

---

## 6. MCP Tools (Execution)

| Tool | Purpose |
|------|--------|
| `auth.get_user_role` (or query_data for auth) | Validate user, return role / admin_rights. |
| `policy.semantic_search` | Query vector DB with user question; return relevant chunks. |
| `db.read` | Read employees, attendance, timesheet, assets (query_data). |
| `db.validate` | Validate proposed action (constraints, SQL safety) without writing. |
| `db.execute` | Perform update/insert after guardrails/approval (update_values, etc.). |
| `approval.request` | Create HITL approval request for manager/HR. |
| `audit.write` | Persist reasoning_output (decision, why, policy_reference, before/after). |

---

## 7. A2A Agents (Reasoning)

| Agent | Responsibility |
|-------|----------------|
| **Concierge / Orchestrator** | User interaction, graph control, final response shape. |
| **Policy Agent** | RAG interpretation: map policy chunks to rules/constraints. |
| **Data Reasoning Agent** | SQL/DB validation logic for attendance, timesheet, asset. |
| **Critic / Compliance Agent** | Second-pass review, compliance check. |
| **Sentiment Agent** (optional) | Detect frustration; trigger escalation or tone change. |
| **Prediction Agent** (optional) | Leave exhaustion, attendance risk, anomalies (Phase 1: rules/rolling stats; Phase 2: models). |

---

## 8. Data Models (High-Level)

**Attendance** (existing): employee, date, check_in, check_out, etc.

**Timesheet:** employee_id, date, project/task, hours_logged, work_type (office/remote/on-call), status (draft/submitted/approved).

**Asset:** asset_type (laptop/phone/headset), brand, model, serial_number, assigned_to, assigned_date, condition, status.

**Policy chunks (vector store):** doc_title, chunk/content, embedding, metadata (section, page).

**Short-term memory:** session_id, user_id, last N messages + state (e.g. subject_employee, pending_clarification).

**Long-term memory:** user_id, preferences, behavioral summary (e.g. preferred leave types, patterns).

---

## 9. Guardrails (LangGraph Conditional Edges)

Implement in `decision_guardrails` (or equivalent router node):

- Leave duration > 3 days → e.g. NEED_HITL_APPROVAL or NEED_CLARIFICATION.
- Conflict with critical timelines → NEED_CLARIFICATION or DENY.
- Unclear or low confidence → NEED_CLARIFICATION.
- Sensitive operation (e.g. bulk update, role change) → NEED_HITL_APPROVAL.
- Otherwise → APPROVE_AUTOMATIC or DENY with reason.

---

## 10. Explainability Contract

Every response that involves a decision must expose (in state and to the user):

- **decision** (e.g. Leave Approved, Request Denied).
- **why** (human-readable bullets).
- **policy_reference** (e.g. Section 4.1 – Leave Rules).

Store the same in `reasoning_output` and in `audit.write` for traceability.

---

## 11. Implementation Order (Suggested)

1. **Phase 1 — Foundation**
   - Online graph: validate_user → classify_issue → route_by_intent.
   - Branches: fetch_simple_data (read), rag_policy (policy Q&A), draft_action_plan → execute_update (write) with basic guardrails.
   - State: user, intent, proposed_action, reasoning_output, final_response.
   - MCP: auth, db.read, db.execute, policy.semantic_search (once vector store exists).
   - Offline graph: PDF → chunk → embed → upsert_vector_store.

2. **Phase 2 — Memory & explainability**
   - Short-term memory: load after validate_user; update after format_response.
   - Long-term memory (optional): load after validate_user; table per user.
   - reasoning_output and format_response always set decision, why, policy_reference.
   - persist_audit_log after execute_update.

3. **Phase 3 — Guardrails & HITL**
   - decision_guardrails node with conditional edges.
   - ask_clarifying_question and loop back.
   - human_in_the_loop + await_approval_event; execute only on approval.

4. **Phase 4 — A2A & optional agents**
   - policy_reasoning_agent, data_reasoning_agent, critic_compliance_agent.
   - sentiment_agent, prediction_agent (simple rules first).

5. **Phase 5 — Domains**
   - Timesheet model + nodes; asset model + nodes; cross-checks (e.g. timesheet × attendance × asset).

---

## 12. Diagram References

- **Online flow:** See `make_architecture_diagram.py` → `hr_decision_graph.png` (align node names with this spec).
- **Offline flow:** Same script → `policy_ingestion_graph.png`.
- **High-level:** `architecture.png` (User → CLI → LangGraph → LLM + MCP + Policies + LangSmith).

Use this document as the single source of truth when implementing the AI-Powered HR Decision Assistant.
