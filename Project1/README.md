# LangChain Agent with MCP PostgreSQL - POC

A local proof-of-concept AI agent system using LangChain, MCP (Model Context Protocol), and PostgreSQL.

## Architecture

```
Terminal CLI → LangChain Agent → MCP Client → MCP Server → PostgreSQL
```

## Setup Instructions

### 1. Install PostgreSQL

Make sure PostgreSQL is installed and running on your local machine.

### 2. Create `.env` file

Create a `.env` file in the project root with:

```env
# PostgreSQL Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=employees_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here

# Ollama Configuration (if needed)
OLLAMA_BASE_URL=http://localhost:11434

# LangSmith Configuration (Optional - for tracing and monitoring)
# Get your API key from https://smith.langchain.com
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=mcp-postgres-agent
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3.5. (Optional) Set Up LangSmith

LangSmith provides tracing, monitoring, and debugging for your LLM applications.

1. Sign up for a free account at [https://smith.langchain.com](https://smith.langchain.com)
2. Get your API key from the settings page
3. Add the LangSmith configuration to your `.env` file (see step 2 above)

If you don't set up LangSmith, the agent will still work, but you won't have tracing and monitoring capabilities.

### 4. Set Up Database

Run the database setup script to create the database and insert dummy data:

```bash
python database_setup.py
```

This will:
- Create the `employees_db` database
- Create the `employees` table
- Insert 12 sample employee records

### 5. Make Sure Ollama is Running

Ensure you have Ollama installed and the `qwen2.5` model pulled:

```bash
ollama pull qwen2.5
```

### 6. Run the Agent

Start the terminal-based agent:

```bash
python agent.py
```

## Usage

Once the agent is running, you can ask questions like:

- "List all tables in the database"
- "Show me the schema of the employees table"
- "Show me all employees who joined after 2023"
- "What employees are in the Engineering department?"
- "Who are the managers and their direct reports?"

Type `exit` or `quit` to stop the agent.

## Files

- `agent.py` - Main LangChain agent with MCP integration and LangSmith tracing
- `mcp_postgres_server.py` - MCP server exposing PostgreSQL tools
- `database_setup.py` - Script to create database and dummy data
- `.env` - Environment variables (create this file)
- `requirements.txt` - Python dependencies

## LangSmith Integration

This project includes LangSmith integration for:
- **Tracing**: See every LLM call, tool usage, and agent step
- **Monitoring**: Track performance, latency, and costs
- **Debugging**: Visualize execution flows and identify issues

When LangSmith is configured (via `.env`), all agent runs are automatically traced. View your traces at [https://smith.langchain.com](https://smith.langchain.com).

The agent will show a message on startup indicating whether LangSmith tracing is enabled.

## How It Works

1. **MCP Server** (`mcp_postgres_server.py`): Runs as a separate process, exposes PostgreSQL tools via MCP protocol
2. **LangChain Agent** (`agent.py`): Connects to MCP server, converts MCP tools to LangChain tools, creates a ReAct agent
3. **Terminal Interface**: Simple CLI for user interaction

## Troubleshooting

- **PostgreSQL connection errors**: Check your `.env` file and make sure PostgreSQL is running
- **MCP server errors**: Make sure `mcp_postgres_server.py` can be executed
- **Ollama errors**: Ensure Ollama is running and `qwen2.5` model is available

