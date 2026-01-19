
import os
from dotenv import load_dotenv

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "A2A-Help-Service")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

print(f"🔍 LangSmith Tracing: {'✅ Enabled' if os.getenv('LANGCHAIN_TRACING_V2') == 'true' else '❌ Disabled'}")
print(f"📊 LangSmith Project: {os.getenv('LANGCHAIN_PROJECT', 'A2A-Help-Service')}")

