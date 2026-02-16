
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from langsmith import traceable
from mcp_client import MCPClient
load_dotenv()
from config import *

llm = ChatOllama(
    model="qwen2.5:latest",
    temperature=0,
    num_predict=150  # Limit tokens
)

mcp_client = MCPClient()

graph = None
def get_graph():
    global graph
    if graph is None:
        from graph import build_graph
        graph = build_graph()
    return graph