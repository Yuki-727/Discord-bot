import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "yuki_v3.db")
    
    # Model settings
    AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
    MAX_TOKENS = 1024
    TEMPERATURE = 0.7

config = Config()
