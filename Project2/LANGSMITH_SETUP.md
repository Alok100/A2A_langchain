# LangSmith Tracing Setup

## Overview
LangSmith tracing has been enabled in `HelpServiceState.py` to track all LLM calls, workflow execution, and performance metrics.

## Configuration

Add the following variables to your `.env` file in the `Project2` directory:

```env
# Enable LangSmith tracing (set to "true" to enable)
LANGCHAIN_TRACING_V2=true

# Your LangSmith API key (get it from https://smith.langchain.com/settings)
LANGCHAIN_API_KEY=your_langsmith_api_key_here

# Project name in LangSmith (will be created if it doesn't exist)
LANGCHAIN_PROJECT=A2A-Help-Service

# LangSmith endpoint (usually no need to change)
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

## Getting Your API Key

1. Go to [LangSmith](https://smith.langchain.com/)
2. Sign up or log in
3. Navigate to Settings → API Keys
4. Create a new API key
5. Copy the key and add it to your `.env` file

## What Gets Traced

With LangSmith tracing enabled, you'll see:

- **LLM Calls**: All prompts sent to Ollama and their responses
- **Workflow Execution**: Complete graph execution flow
- **Node Execution**: Individual node performance (validate_user, classify_issue, etc.)
- **Timing**: Duration of each step
- **Input/Output**: Full state transitions
- **Errors**: Any errors that occur during execution

## Viewing Traces

1. Run your help service as normal
2. Go to [LangSmith Projects](https://smith.langchain.com/)
3. Select the "A2A-Help-Service" project
4. View detailed traces of each execution

## Features Added

- ✅ Automatic trace collection for all LangGraph executions
- ✅ Tagged traces with "help-desk" and "langgraph"
- ✅ Named trace: "A2A_Help_Service"
- ✅ Environment variable loading from `.env`
- ✅ Startup confirmation messages

## Disabling Tracing

To disable tracing, set in your `.env`:
```env
LANGCHAIN_TRACING_V2=false
```

Or simply remove the environment variable.

