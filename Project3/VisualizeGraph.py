"""
Print ASCII visualization of the Project3 Help Service graph.
Run: python VisualizeGraph.py
PNG is also saved when the graph is first built (e.g. on first CLI run).

To see the *actual* flow that was used in the last CLI run:
  python VisualizeGraph.py --path
  python VisualizeGraph.py --path-html   # writes path_diagram.html (open in browser)

The CLI auto-updates path_diagram.html after each message: Question -> Execution flow (accumulated).
"""
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_FLOW_FILE = os.path.join(SCRIPT_DIR, "last_flow.txt")
FLOW_HISTORY_FILE = os.path.join(SCRIPT_DIR, "flow_history.json")
PATH_HTML_FILE = os.path.join(SCRIPT_DIR, "path_diagram.html")


def get_last_execution_path():
    """Return list of node names from last CLI run, or [] if not available."""
    if not os.path.isfile(LAST_FLOW_FILE):
        return []
    with open(LAST_FLOW_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def get_flow_history():
    """Return list of {question, path} from flow_history.json (CLI session history)."""
    if not os.path.isfile(FLOW_HISTORY_FILE):
        return []
    try:
        with open(FLOW_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def print_path_diagram():
    """Print ASCII diagram of the actual path taken (from last_flow.txt)."""
    path = get_last_execution_path()
    if not path:
        print("No last flow found. Run the CLI, send a message, then run: python VisualizeGraph.py --path")
        return
    print("\n  [Flow] Last execution path (actual flow used):\n")
    for i, node in enumerate(path):
        print(f"      {node}")
        if i < len(path) - 1:
            print("        |")
    print()


def write_path_diagram_html(silent=False):
    """Write path_diagram.html: for each turn, show Question then Execution flow. Uses flow_history.json (CLI updates it)."""
    history = get_flow_history()
    if not history:
        path = get_last_execution_path()
        if not path:
            if not silent:
                print("No flow history. Run the CLI, send a message, then path_diagram.html will be created.")
            return
        history = [{"question": "(last run)", "path": path}]

    sections = []
    for idx, entry in enumerate(history, 1):
        q = entry.get("question", "")
        path = entry.get("path") or []
        flow_divs = []
        for i, node in enumerate(path):
            flow_divs.append(f'<div class="node">{node}</div>')
            if i < len(path) - 1:
                flow_divs.append('<div class="arrow">&#8595;</div>')
        flow_content = "\n      ".join(flow_divs)
        sections.append(f"""
  <section class="turn">
    <h2 class="turn-num">Turn {idx}</h2>
    <p class="question"><strong>Question:</strong> {_escape(q)}</p>
    <p class="flow-label"><strong>Execution flow:</strong></p>
    <div class="flow">
      {flow_content}
    </div>
  </section>""")

    body_sections = "\n".join(sections)
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Help Service – Questions and execution flow</title>
  <style>
    body {{ font-family: system-ui; padding: 2rem; background: #1a1a2e; color: #eee; max-width: 56rem; margin: 0 auto; }}
    h1 {{ color: #4fc3f7; }}
    .turn {{ margin-bottom: 2rem; padding: 1rem; border: 1px solid #333; border-radius: 8px; background: #16213e; }}
    .turn-num {{ color: #4fc3f7; margin-top: 0; font-size: 1.1rem; }}
    .question {{ margin: 0.5rem 0; color: #e0e0e0; }}
    .flow-label {{ margin: 0.75rem 0 0.25rem; color: #aaa; font-size: 0.9rem; }}
    .flow {{ display: flex; flex-direction: column; align-items: center; gap: 0; margin-top: 0.5rem; }}
    .node {{
      background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
      color: #0d47a1;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-weight: bold;
      margin: 2px 0;
      font-size: 0.9rem;
      box-shadow: 0 2px 6px rgba(79,195,247,0.4);
    }}
    .arrow {{ color: #4fc3f7; font-size: 1.2rem; margin: 2px 0; }}
    .note {{ margin-top: 1.5rem; color: #888; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <h1>Help Service – Questions and execution flow</h1>
  <p>For each question you asked, this shows the graph path that was <em>actually</em> used. Updated after each CLI message.</p>
{body_sections}
  <p class="note">Source: flow_history.json. New questions append to this page when you use the CLI.</p>
</body>
</html>
"""
    with open(PATH_HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    if not silent:
        print(f"Wrote {PATH_HTML_FILE} - open in a browser to see questions and flows.")


def write_empty_session_html(silent=True):
    """Write path_diagram.html for a fresh session (no turns yet). Used when CLI starts a new run."""
    body_placeholder = """
  <p class="note">No turns in this session yet. Ask a question in the CLI to see flows here.</p>"""
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Help Service – Questions and execution flow</title>
  <style>
    body {{ font-family: system-ui; padding: 2rem; background: #1a1a2e; color: #eee; max-width: 56rem; margin: 0 auto; }}
    h1 {{ color: #4fc3f7; }}
    .turn {{ margin-bottom: 2rem; padding: 1rem; border: 1px solid #333; border-radius: 8px; background: #16213e; }}
    .turn-num {{ color: #4fc3f7; margin-top: 0; font-size: 1.1rem; }}
    .question {{ margin: 0.5rem 0; color: #e0e0e0; }}
    .flow-label {{ margin: 0.75rem 0 0.25rem; color: #aaa; font-size: 0.9rem; }}
    .flow {{ display: flex; flex-direction: column; align-items: center; gap: 0; margin-top: 0.5rem; }}
    .node {{
      background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
      color: #0d47a1;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-weight: bold;
      margin: 2px 0;
      font-size: 0.9rem;
      box-shadow: 0 2px 6px rgba(79,195,247,0.4);
    }}
    .arrow {{ color: #4fc3f7; font-size: 1.2rem; margin: 2px 0; }}
    .note {{ margin-top: 1.5rem; color: #888; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <h1>Help Service – Questions and execution flow</h1>
  <p>For each question you asked, this shows the graph path that was <em>actually</em> used. Updated after each CLI message.</p>
{body_placeholder}
</body>
</html>
"""
    try:
        with open(PATH_HTML_FILE, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        pass


def _escape(s):
    """Escape HTML in question text."""
    if not s:
        return ""
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def print_graph_structure():
    """Print ASCII visualization of the graph (includes login + admin_rights)."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              PROJECT3 – HR HELP SERVICE GRAPH (with login & admin)           ║
╚══════════════════════════════════════════════════════════════════════════════╝

  CLI: Email + Password → authenticate() → admin_rights = True (HR) / False (Employee)

                            [START]
                               ↓
                      ┌────────────────┐
                      │ validate_user  │ ← 1 MCP (by user_email)
                      │   (0 LLM)      │   state has admin_rights from login
                      └────────┬───────┘
                               │
                        Valid? │
                    ┌──────────┴──────────┐
                   Yes                    No
                    │                      │
            ┌───────▼────────┐             │
            │ classify_issue │ ← 1 LLM     │
            │   (Agent 1)     │             │
            └───────┬────────┘             │
                    │                      │
            ┌───────▼────────┐             │
            │  route_issue  │ (logic)      │
            │ admin_rights  │             │
            │ checked here  │             │
            └───────┬────────┘             │
                    │                      │
         ┌──────────┼──────────┬───────────┤
         │          │          │           │
    Simple      Update    Complex          │
    (all)       (all)    (HR only)          │
         │          │          │           │
         │          │    ┌─────▼─────┐     │
         │          │    │ non-HR?   │     │
         │          │    │→ format   │     │
         │          │    │  (denied) │     │
         │          │    └─────┬─────┘     │
┌────────▼───┐ ┌───▼────────┐ ┌▼────────────┐
│fetch_simple│ │handle_update│ │handle_complex│
│  (0 LLM)   │ │(Agent 2)    │ │(Agent 2)     │
│  1 MCP     │ │1 LLM,2 MCP  │ │1 LLM, 2-3 MCP│
└────┬───────┘ └────┬────────┘ └───┬─────────┘
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

  • admin_rights = True  → HR: can do complex_report (analytics, list all, etc.)
  • admin_rights = False → Employee: complex_report → "Access denied. HR only."
  • All users: query_employee, query_attendance, update_leave, update_attendance (self)
╚══════════════════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--path":
        print_path_diagram()
    elif len(sys.argv) > 1 and sys.argv[1] == "--path-html":
        write_path_diagram_html()
    else:
        print_graph_structure()
