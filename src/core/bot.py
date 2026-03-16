import discord
from discord.ext import commands
import os
import asyncio
import logging
from .config import config

# Setup file logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        logger.info("Bot is initializing...")
        # Load Cogs automatically
        cogs_dir = os.path.join(os.getcwd(), "src", "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"src.cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    logger.info(f"Loaded extension: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load extension {cog_name}: {e}")
        
        # Sync global slash commands
        logger.info("Syncing slash commands...")
        await self.tree.sync()
        logger.info("Slash commands synced.")

    async def on_ready(self):
        logger.info(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"✅ Guilds: {len(self.guilds)}")
        logger.info("------")

bot = YukiBot()
