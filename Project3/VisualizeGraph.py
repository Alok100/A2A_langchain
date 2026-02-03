"""
Print ASCII visualization of the Project3 Help Service graph.
Run: python VisualizeGraph.py          → ASCII in terminal
     python VisualizeGraph.py --mermaid → Write Mermaid to flow_diagram.mmd (open in https://mermaid.live)

Flow tracing (what happened in the CLI) is available in LangSmith: https://smith.langchain.com
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def print_graph_structure():
    """Print ASCII visualization of the graph (includes login + admin_rights)."""
    print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│            PROJECT3 – HR HELP SERVICE (Login → Classify → Route → Act)        │
└─────────────────────────────────────────────────────────────────────────────┘

  CLI: Email + Password → admin_rights = True (HR) / False (Employee)

                                    START
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │     validate_user        │  1 MCP (DB lookup by email)
                        └────────────┬────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │  Valid?                 │
                   Yes   │                        │   No
                        ▼                         ▼
            ┌─────────────────────┐    ┌─────────────────────┐
            │   classify_issue    │    │   format_response    │ → END (error)
            │   (1 LLM)            │    │   (error message)   │
            └──────────┬──────────┘    └─────────────────────┘
                        │
                        ▼
            ┌─────────────────────┐
            │   route_issue       │  (logic: category + admin_rights)
            └──────────┬──────────┘
                        │
        ┌───────┬───────┼───────┬────────────┐
        │       │       │       │            │
        ▼       ▼       ▼       ▼            ▼
   ┌────────┐ ┌────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐
   │ fetch  │ │ handle │ │  handle    │ │  rag_policy │ │ format_      │
   │ simple │ │ update │ │  complex   │ │             │ │ response     │
   └───┬────┘ └───┬────┘ └─────┬──────┘ └──────┬─────┘ │ (denied)     │
       │          │            │               │       └───────┬───────┘
       │          │            │               │               │
       │     ┌────▼────┐       │               │               │
       │     │ verify  │       │               │               │
       │     │ update  │       │               │               │
       │     └────┬────┘       │               │               │
       │          │            │               │               │
       └──────────┴────────────┴───────────────┴───────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │   format_response        │  (build reply + usage stats)
                        └────────────┬────────────┘
                                      │
                                      ▼
                                    END

  ROUTES (from route_issue):
  ─────────────────────────
  • query_employee / query_attendance  → fetch_simple_data   (all users; "other" needs HR)
  • update_leave / update_attendance  → handle_update       (all users; "other" needs HR)
  • complex_report                    → handle_complex      (HR only) or format (denied)
  • query_policy                      → rag_policy         (all; 1 doc selected, then answer)
""")


def get_mermaid_flow():
    """Return Mermaid flowchart string for the Help Service (paste at mermaid.live for a nice diagram)."""
    return """flowchart TB
    subgraph entry[" "]
        START
    end
    START --> validate_user["validate_user<br/>(1 MCP)"]
    validate_user -->|Valid| classify["classify_issue<br/>(1 LLM)"]
    validate_user -->|Invalid| format_err["format_response<br/>(error)"]
    format_err --> END
    classify --> route["route_issue<br/>(logic)"]
    route -->|query_employee / query_attendance| fetch["fetch_simple_data<br/>(1 MCP)"]
    route -->|update_leave / update_attendance| update["handle_update<br/>(1 LLM, 2 MCP)"]
    route -->|complex_report + HR| complex["handle_complex<br/>(1 LLM, 2 MCP)"]
    route -->|complex_report + non-HR| format_deny["format_response<br/>(denied)"]
    route -->|query_policy| rag["rag_policy<br/>(2 LLM, 1 doc only)"]
    format_deny --> END
    fetch --> format["format_response"]
    update --> verify["verify_update<br/>(1 MCP)"]
    verify --> format
    complex --> format
    rag --> format
    format --> END
"""


def write_mermaid_file():
    """Write Mermaid diagram to flow_diagram.mmd in Project3. Open at https://mermaid.live"""
    path = os.path.join(SCRIPT_DIR, "flow_diagram.mmd")
    with open(path, "w", encoding="utf-8") as f:
        f.write(get_mermaid_flow())
    print(f"Mermaid diagram written to: {path}")
    print("Paste the file content (or open the file) at https://mermaid.live to view the flowchart.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--mermaid":
        write_mermaid_file()
    else:
        print_graph_structure()
