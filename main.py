import asyncio
from src.core.bot import bot
from src.core.config import config

VERSION = "1.0.2 - Modular Reconstruction Fix"

async def main():
    print(f"🚀 Starting YukiBot {VERSION}")
    async with bot:
        await bot.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
