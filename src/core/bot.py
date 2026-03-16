import discord
from discord.ext import commands
import os
import asyncio
from .config import config

class YukiBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        print("Bot is initializing...")
        # Load Cogs automatically
        cogs_dir = os.path.join(os.getcwd(), "src", "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                cog_name = f"src.cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    print(f"Loaded extension: {cog_name}")
                except Exception as e:
                    print(f"Failed to load extension {cog_name}: {e}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

bot = YukiBot()
