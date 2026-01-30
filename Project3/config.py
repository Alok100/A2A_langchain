"""Project3 config: load .env from repo root and set LangSmith project."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root (parent of Project3)
repo_root = Path(__file__).resolve().parent.parent
load_dotenv(repo_root / ".env")
load_dotenv()  # local .env if any

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "Project3-CLI")
os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
if os.getenv("LANGCHAIN_API_KEY"):
    pass  # already set from .env
