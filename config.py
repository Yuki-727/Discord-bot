import os
from dotenv import load_dotenv

load_dotenv()

# AI API Configuration
AI_API_KEY = os.getenv("AI_API_KEY")
AI_API_BASE_URL = os.getenv("AI_API_BASE_URL") or os.getenv("AI_BASE_URL") or "https://api.openai.com/v1"
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

# Load other settings
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
