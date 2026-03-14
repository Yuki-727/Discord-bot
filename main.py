import discord
from discord.ext import commands
import config
from commands.chat import handle_chat_command

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for !chat command

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"YUKI-BOT VERSION 2.1 STARTING", flush=True)
    print(f"Logged in as {bot.user.name} ({bot.user.id})", flush=True)
    print("------", flush=True)
    try:
        # Sync slash commands
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.command(name="chat")
async def chat_prefix(ctx, *, message: str):
    """Chat with Yuki-bot using !chat <message>"""
    await handle_chat_command(ctx, message)

@bot.tree.command(name="chat", description="Chat with Yuki-bot")
async def chat_slash(interaction: discord.Interaction, message: str):
    """Chat with Yuki-bot using slash command /chat"""
    await handle_chat_command(interaction, message)

if __name__ == "__main__":
    if config.DISCORD_TOKEN:
        bot.run(config.DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN is not set. Please check your .env file.")
