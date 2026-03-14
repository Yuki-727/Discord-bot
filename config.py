import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_API_BASE_URL = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables.")
if not AI_API_KEY:
    raise ValueError("AI_API_KEY not found in environment variables.")
