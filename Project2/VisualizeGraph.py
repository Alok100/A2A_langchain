
def print_graph_structure():
    """Print ASCII visualization of the graph"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    A2A HELP SERVICE GRAPH STRUCTURE                  ║
╚══════════════════════════════════════════════════════════════════════╝

                            [START]
                               ↓
                      ┌────────────────┐
                      │ validate_user  │ ← 1 MCP call
                      │   (0 LLM)      │
                      └────────┬───────┘
                               │
                        Valid? │
                    ┌──────────┴──────────┐
                   Yes                    No
                    │                      │
            ┌───────▼────────┐             │
            │ classify_issue │ ← 1 LLM    │
            │   (Agent 1)    │             │
            └───────┬────────┘             │
                    │                      │
            ┌───────▼────────┐             │
            │  route_issue   │ (logic)     │
            │   (0 LLM)      │             │
            └───────┬────────┘             │
                    │                      │
         ┌──────────┼──────────┐           │
         │          │          │           │
    Simple      Update     Complex         │
         │          │          │           │
┌────────▼───┐ ┌───▼────────┐ ┌───▼────────────┐
│fetch_simple│ │handle_update│ │handle_complex  │
│  (0 LLM)   │ │(Agent 2)    │ │(Agent 2)       │
│  1 MCP     │ │1 LLM,2 MCP  │ │1 LLM, 2-3 MCP  │
└────┬───────┘ └────┬────────┘ └───┬────────────┘
     │              │               │
     │         ┌────▼────────┐      │
     │         │verify_update│      │
     │         │  (0 LLM)    │      │
     │         │  1 MCP      │      │
     │         └────┬────────┘      │
     │              │               │
     └──────────────┼───────────────┘
                    │
            ┌───────▼────────┐
            │format_response │
            │   (0 LLM)      │
            └───────┬────────┘
                    │
                  [END]

╔══════════════════════════════════════════════════════════════════════╗
║ RESOURCE USAGE PER PATH:                                             ║
║ • Simple Query:  1 LLM call,  2 MCP calls                            ║
║ • Update:        2 LLM calls, 4 MCP calls                            ║
║ • Complex:       2 LLM calls, 3-4 MCP calls                          ║
╚══════════════════════════════════════════════════════════════════════╝
""")