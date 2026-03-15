import discord
from discord.ext import commands
import config
from commands.chat import handle_chat_command, setup_context
from utils.database import Database
from context.identity import IdentityModule
from context.memory import MemoryModule
from context.relationship import RelationshipModule
from context.prompt_builder import PromptBuilder

# Initialize Database and Modular Context
db = Database()
identity = IdentityModule()
memory = MemoryModule(db)
relationship = RelationshipModule(db)
prompt_builder = PromptBuilder(identity, memory, relationship)

# Pass new components to chat command handler
setup_context(db, identity, memory, relationship, prompt_builder)

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for !chat command

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Yuki-bot is online!")
    print(f"Logged in as: {bot.user.name} ({bot.user.id})")
    print("------", flush=True)
    try:
        # Sync slash commands
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Log message for passive context
    db.log_message(
        str(message.channel.id),
        str(message.author.id),
        message.author.name,
        message.content
    )

    # Passive invocation check: if mentioned, replied to, or name in message
    is_mentioned = bot.user in message.mentions
    is_replied = message.reference and message.reference.resolved and message.reference.resolved.author == bot.user
    is_named = any(name in message.content.lower() for name in ["yuki", "nyakeri"])
    
    if is_mentioned or is_replied or is_named:
        # Avoid double-triggering
        if not message.content.startswith("!chat"):
            await handle_chat_command(message, message.content)
            return

    # Allow commands to be processed
    await bot.process_commands(message)

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
