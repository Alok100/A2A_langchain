# AI-Powered HR Decision Assistant — Architecture Diagrams

Visual reference for the system.

| What | Where |
|------|--------|
| **This file** | Mermaid + ASCII diagrams; view in GitHub, VS Code (Mermaid preview), or [mermaid.live](https://mermaid.live). |
| **PNG images** | Run `python make_architecture_diagram.py` from the **architecture/** folder. Generates: `architecture_spec.png`, `architecture.png`, `hr_decision_graph.png`, `policy_ingestion_graph.png`. |

---

## 1. System overview (components)

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────────────────────────────────┐
│   User      │────▶│  CLI / App  │────▶│              LangGraph Runtime                    │
└─────────────┘     └─────────────┘     │  validate → memory → classify → route → act       │
                                        └────────────┬─────────────────┬───────────────────┘
                                                     │                 │
                    ┌────────────────────────────────┼─────────────────┼────────────────────┐
                    │                                │                 │                    │
                    ▼                                ▼                 ▼                    ▼
             ┌────────────┐                  ┌────────────┐    ┌────────────┐       ┌────────────┐
             │    LLM     │                  │    MCP     │    │  Policies  │       │ LangSmith  │
             │ (classify, │                  │ (auth, DB,│    │ (RAG /     │       │ (tracing)  │
             │  RAG,      │                  │  search,   │    │  vector    │       │            │
             │  format)   │                  │  audit)    │    │  store)    │       │            │
             └────────────┘                  └─────┬──────┘    └────────────┘       └────────────┘
                                                    │
                                                    ▼
                                             ┌────────────┐
                                             │ PostgreSQL │
                                             │ + Vector DB│
                                             └────────────┘
```

**Mermaid version (copy to mermaid.live):**

```mermaid
flowchart LR
    subgraph User
        U[User]
    end
    subgraph App
        CLI[CLI / App]
    end
    subgraph Runtime["LangGraph Runtime"]
        direction TB
        V[validate_user]
        M[memory]
        C[classify_issue]
        R[route → act]
        V --> M --> C --> R
    end
    subgraph Services
        LLM[LLM]
        MCP[MCP]
        POL[Policies]
        LS[LangSmith]
        DB[(PostgreSQL + Vector DB)]
    end
    U --> CLI
    CLI --> Runtime
    Runtime --> LLM
    Runtime --> MCP
    Runtime --> POL
    Runtime --> LS
    MCP --> DB
```

---

## 2. Online decision graph (runtime, per request)

High-level flow: **validate → memory → classify → route** into three branches, then **guardrails → execute → explain**.

```mermaid
flowchart TB
    START([START])
    START --> VAL[validate_user<br/>MCP: auth + role]
    VAL --> LSM[load_session_memory<br/>short-term]
    LSM --> LTM[load_long_term_memory<br/>optional]
    LTM --> INP[user_input]
    INP --> CLS[classify_issue<br/>LLM]
    CLS --> ROUTE{route_by_intent}

    ROUTE -->|read| FETCH[fetch_simple_data<br/>MCP]
    ROUTE -->|policy Q&A| RAG[rag_policy_retrieve<br/>MCP]
    ROUTE -->|write/update| DRAFT[draft_action_plan<br/>LLM]

    FETCH --> FMT[format_response]

    RAG --> POL_AG[policy_reasoning_agent<br/>A2A]
    POL_AG --> FMT

    DRAFT --> DATA_AG[data_reasoning_agent<br/>A2A]
    DRAFT --> CRITIC[critic_compliance_agent<br/>A2A]
    DATA_AG --> GUARD[decision_guardrails]
    CRITIC --> GUARD
    GUARD -->|clarify| CLARIFY[ask_clarifying_question]
    GUARD -->|HITL| HITL[human_in_the_loop]
    GUARD -->|approve| EXEC[execute_update<br/>MCP]
    GUARD -->|deny| FMT
    CLARIFY --> CLS
    HITL --> AWAIT[await_approval]
    AWAIT -->|ok| EXEC
    AWAIT -->|reject| FMT
    EXEC --> AUDIT[persist_audit_log<br/>MCP]
    AUDIT --> FMT

    FMT --> UPDATE_MEM[update_short_term_memory]
    UPDATE_MEM --> END([END])
```

---

## 3. Offline policy ingestion (batch)

Run when PDFs change. Feeds the vector store used by **rag_policy_retrieve** at runtime.

```mermaid
flowchart TB
    A([ingest_docs_start])
    B[extract_text<br/>PDF → text]
    C[chunk_documents<br/>+ metadata]
    D[embed_chunks<br/>embedding model]
    E[upsert_vector_store<br/>DB]
    F[build_policy_index_manifest]
    G([ingest_docs_end])

    A --> B --> C --> D --> E --> F --> G
```

---

## 4. Branch summary (what runs when)

| Route        | When                         | Nodes in order |
|-------------|------------------------------|----------------|
| **Simple read** | "How many leaves?", "My laptop?" | fetch_simple_data → (optional policy_lookup) → format_response |
| **Policy Q&A**  | "What is bereavement leave?"     | rag_policy_retrieve → policy_reasoning_agent → format_response |
| **Write/update**| "Apply leave Friday"             | draft_action_plan → policy + data agents → critic → guardrails → (clarify / HITL / execute) → audit → format_response |

---

## 5. MCP tools (execution)

| Tool                | Purpose                          |
|---------------------|----------------------------------|
| auth / query_data   | Validate user, role, admin_rights |
| policy.semantic_search | RAG over policy embeddings     |
| db.read             | Read employees, attendance, timesheet, assets |
| db.validate         | Validate proposed action (no write) |
| db.execute          | Write after guardrails/approval  |
| approval.request    | HITL request to manager/HR      |
| audit.write         | Persist decision, why, policy_reference |

---

## 6. A2A agents (reasoning)

| Agent                  | Role |
|------------------------|------|
| Concierge / Orchestrator | User interaction, graph control |
| Policy Agent           | Interpret policy chunks → rules |
| Data Reasoning Agent   | Validate SQL/DB logic |
| Critic / Compliance   | Second-pass review |
| Sentiment (optional)   | Frustration → escalate |
| Prediction (optional)  | Leave/attendance risk, anomalies |

---

## 7. Explainability (every decision)

- **decision** — e.g. Leave Approved / Denied  
- **why** — human-readable bullets  
- **policy_reference** — e.g. Section 4.1 – Leave Rules  

Stored in state (`reasoning_output`) and in audit log.
