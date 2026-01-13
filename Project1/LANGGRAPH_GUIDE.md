# LangGraph Visualization Guide

## What is LangGraph?

LangGraph is the underlying framework that powers the agent created by `create_agent()`. It's a state machine that manages the agent's execution flow, similar to how ADK web shows the agent's trace.

## How to See Everything (Like ADK Web)

### 1. **Run the Agent**

```bash
python agent.py
```

### 2. **See the Graph Structure**

When the agent starts, it automatically shows:
- All nodes in the graph
- All edges (connections between nodes)
- Graph type and metadata

You can also type `graph` at any time to see the structure again.

### 3. **Watch Execution Flow**

When you ask a question, you'll see:

```
🔄 LangGraph Execution Flow (Like ADK Web):
============================================================

📍 Step 1: Node 'agent'
   🔧 Tool Calls:
      → list_tables
        Args: {}

📍 Step 2: Node 'tools'
   📥 Tool Result from 'list_tables':
      ['employees']

📍 Step 3: Node 'agent'
   🔧 Tool Calls:
      → query_database
        Args: {'query': 'SELECT * FROM employees WHERE join_date > ...'}

📍 Step 4: Node 'tools'
   📥 Tool Result from 'query_database':
      [{'id': 1, 'name': 'Alice Smith', ...}]

📍 Step 5: Node 'agent'
   💬 AI: Based on the database query, here are the employees...
```

### 4. **Understanding the Flow**

The LangGraph agent follows this pattern:

1. **Agent Node** - The LLM decides what to do
   - May call tools
   - May generate a final answer

2. **Tools Node** - Executes tool calls
   - Calls MCP server
   - Returns results

3. **Loop** - Continues until agent decides to finish

### 5. **Stream Modes**

The agent uses `stream_mode="updates"` which shows:
- Each node execution
- Tool calls being made
- Tool results being returned
- AI responses

### 6. **Compare to ADK Web**

| ADK Web | Our LangGraph Implementation |
|---------|----------------------------|
| Shows agent trace | ✅ Shows step-by-step execution |
| Shows tool calls | ✅ Shows tool calls with args |
| Shows tool results | ✅ Shows tool results |
| Shows state changes | ✅ Shows node updates |
| Visual graph | ✅ Shows graph structure (text) |

## Key Differences from ADK

1. **ADK Web**: Visual UI with interactive trace
2. **Our Implementation**: Terminal-based, step-by-step output

Both show the same information, just in different formats!

## Advanced: Accessing Graph Internals

The `agent` object is a `CompiledStateGraph`. You can:

```python
# See all nodes
print(agent.nodes.keys())

# See the graph structure
graph = agent.get_graph()
print(graph.nodes)
print(graph.edges)
```

## Testing the Visualization

Try these queries to see different execution patterns:

1. **Simple query**: "List all tables"
   - Should show: `list_tables` tool call

2. **Complex query**: "Show me employees who joined after 2023"
   - Should show: Multiple steps (list_tables → describe_table → query_database → final answer)

3. **Type `graph`**: See the graph structure anytime

## Troubleshooting

If you don't see the execution flow:
- Make sure you're using `agent.stream()` (not `agent.invoke()`)
- Check that `stream_mode="updates"` is set
- Verify the agent is a LangGraph (it should be from `create_agent()`)


