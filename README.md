# Yuki-bot

Yuki-bot is a Discord bot designed to chat with users using an AI API. It features both traditional prefix commands (`!chat`) and modern slash commands (`/chat`).

## Features
- **AI Chatting**: Uses OpenAI-style API (e.g., GPT-4o-mini) for intelligent responses.
- **Context Memory**: Remembers the last 10 messages per user for relevant conversations.
- **Error Handling**: gracefully handles API timeouts and errors.
- **Modern Interface**: Supports both `!chat` and `/chat`.

## Project Structure
```
Yuki-bot/
 ├ main.py           # Bot entry point and command registration
 ├ config.py         # Configuration management
 ├ ai_client.py      # AI API interaction logic
 ├ commands/         # Command implementations
 │   └ chat.py       # Core chat command handler
 ├ utils/            # Utility functions
 │   └ memory.py     # Conversation history management
 ├ requirements.txt  # Project dependencies
 ├ .env.example      # Template for environment variables
 └ README.md         # Documentation
```

## Setup Instructions

1. **Clone/Download** the repository.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   - Rename `.env.example` to `.env`.
   - Fill in your `DISCORD_TOKEN` (from [Discord Developer Portal](https://discord.com/developers/applications)) and `AI_API_KEY`.
4. **Run the Bot**:
   ```bash
   python main.py
   ```

## Hosting Instructions

### Option A: Railway (Recommended for 24/7)
1. **GitHub**: Push your code to a private GitHub repository.
2. **Connect**: Log in to [Railway](https://railway.app/) and create a "New Project" -> "Deploy from GitHub repo".
3. **Internal Procfile**: I've included a `Procfile` which tells Railway to run `python main.py` as a worker process.
4. **Environment Variables**:
   - Go to the **Variables** tab in your Railway project.
   - Add `DISCORD_TOKEN` and `AI_API_KEY`.
   - Optional: Add `AI_MODEL` and `AI_API_BASE_URL` if you want to override defaults.
5. **24/7 Availability**: Railway will automatically keep the bot running. If it crashes, Railway will restart it.

### Option B: Render
1. Create a new "Background Worker" service.
2. Connect your GitHub repository.
3. Set the build command: `pip install -r requirements.txt`.
4. Set the start command: `python main.py`.
5. Add your environment variables in the Render dashboard.

### Option C: Replit
1. Import your repository into Replit.
2. Replit will automatically install dependencies.
3. Add your secrets in the "Secrets" (padlock icon) tab.
4. Click "Run".

---
Built with ❤️ by Yuki-bot Team.
