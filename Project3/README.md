# Project3 – CLI chat with same MCP as Project2

- **MCP**: Same Azure PostgreSQL MCP client as Project2 (lives in `mcp_client.py`).
- **Engine**: Same LangGraph help service (validate → classify → route → fetch/update/complex → format).
- **CLI**: Continuous chat: you type, the assistant replies using LLM + DB (MCP).
- **HR docs**: POC HR policy PDFs and timesheet (same idea as Project2, with more policies).

## HR policy docs (POC)

Generated under `poc_data/`:

- **PDFs** (`poc_data/hr_rules/`): Leave, Attendance, Code of Conduct, **Asset Distribution**, **Expense**, **Grievance**.
- **Timesheet** (`poc_data/employee_timesheet.xlsx`): Fake records for 10 employees (2 weeks).

To regenerate: `python generate_poc_data.py` (from Project3). Edit `poc_data/hr_rules_content.py` to change policy text.

## Setup

1. Use the same env as Project2 (PostgreSQL, Ollama, optional LangSmith).  
   `.env` is loaded from repo root (`A2A_langchain/.env`).

2. Install deps (from `Project3` or repo root):
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure `azure-postgresql-mcp` is at repo root (same as Project2):
   ```
   A2A_langchain/
   ├── azure-postgresql-mcp/
   ├── Project2/
   └── Project3/
   ```

## Run CLI

From `Project3`:

```bash
python cli_chat.py
```

- **Login**: Enter **email** then **password**. HR (James Garcia) password = `11111111`; others = `00000000`.
- **Role**: Employee → `admin_rights = False`; HR → `admin_rights = True`. Only HR can run complex reports/analytics.
- Then loop: type a message → get HR help reply. Type `quit` or `exit` to stop.

## Graph visualization

- **PNG**: When the graph is first built (e.g. first CLI run), it is saved as `Project3/help_service_graph.png`.
- **ASCII**: Run `python VisualizeGraph.py` to print the flow (login → validate → classify → route → …).

## Files

| File | Role |
|------|------|
| `mcp_client.py` | Same MCP wrapper as Project2 (PostgreSQL via Azure MCP). |
| `config.py` | Loads `.env` from repo root, sets LangSmith project to Project3-CLI. |
| `graph.py` | LangGraph workflow (validate, classify, fetch_simple_data, handle_update, verify_update, handle_complex, format_response). |
| `HelpServiceState.py` | `run_help_service(name, message)` used by CLI. |
| `cli_chat.py` | Continuous CLI: input → `run_help_service` → print response. |
| `generate_poc_data.py` | Generates HR policy PDFs and timesheet Excel from `poc_data/hr_rules_content.py`. |
| `poc_data/hr_rules_content.py` | Policy text (Leave, Attendance, Code of Conduct, Asset Distribution, Expense, Grievance). |
| `poc_data/hr_rules/*.pdf` | Generated HR policy PDFs (6 docs). |
| `poc_data/employee_timesheet.xlsx` | Generated fake timesheet. |
| `requirements.txt` | Same as Project2 + Azure MCP + reportlab + openpyxl. |
