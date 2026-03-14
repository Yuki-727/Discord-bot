import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")
# Support both AI_API_BASE_URL and AI_BASE_URL
AI_API_BASE_URL = os.getenv("AI_API_BASE_URL") or os.getenv("AI_BASE_URL") or "https://api.openai.com/v1"
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

if not DISCORD_TOKEN:
    print("WARNING: DISCORD_TOKEN not found in environment variables.")
if not AI_API_KEY:
    print("WARNING: AI_API_KEY not found in environment variables.")

print(f"Config Loaded: Base URL={AI_API_BASE_URL}, Model={AI_MODEL}")
