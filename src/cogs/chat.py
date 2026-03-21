import asyncio
import random
import re
import os
import httpx
import discord
from discord.ext import commands
from ..core.pipeline import pipeline

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.msg_buffers = {} # (channel_id, user_id) -> [messages]
        self.buffer_tasks = {} # (channel_id, user_id) -> asyncio.Task

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if user.bot: return
        from ..processing.mcp import mcp
        mcp.update_typing(str(channel.id), str(user.id))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        from ..core.database import db
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        
        # We only buffer for monitored channels, DMs, or direct Tag/Command
        is_monitored = db.is_channel_monitored(channel_id)
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_tag = self.bot.user.mentioned_in(message)
        is_command = message.content.startswith(self.bot.command_prefix)

        if not (is_monitored or is_dm or is_command or is_tag):
            return

        # Buffering logic
        key = (channel_id, user_id)
        if key not in self.msg_buffers:
            self.msg_buffers[key] = []
        
        self.msg_buffers[key].append(message.content)

        # Reset/Start timer
        if key in self.buffer_tasks:
            self.buffer_tasks[key].cancel()
        
        self.buffer_tasks[key] = asyncio.create_task(self._process_buffer_task(message, key))

    async def _process_buffer_task(self, original_message, key):
        from ..processing.mcp import mcp
        channel_id, user_id = key
        
        try:
            # Wait for user to stop typing and for message completion
            wait_count = 0
            while wait_count < 10: # Max 10s additional wait
                await asyncio.sleep(1.0)
                
                # Check typing status
                if mcp.is_user_typing(channel_id, user_id):
                    wait_count += 1
                    continue
                
                # Check AI completeness
                combined_text = "\n".join(self.msg_buffers.get(key, []))
                if not combined_text: break
                
                status = await mcp.check_completeness(combined_text, original_message.author.name)
                if status == "STOP":
                    break
                else:
                    wait_count += 1

            messages = self.msg_buffers.pop(key, [])
            if not messages: return
            
            combined_text = "\n".join(messages)
            await self._process_merged_message(original_message, combined_text)
        except asyncio.CancelledError:
            pass
        finally:
            self.buffer_tasks.pop(key, None)

    async def _process_merged_message(self, message, combined_text):
        from ..core.cooldown import cooldown_manager
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_command = combined_text.startswith(self.bot.command_prefix)

        on_cooldown = cooldown_manager.is_on_cooldown(user_id)
        
        response = await pipeline.run(
            channel_id=channel_id,
            user_id=user_id,
            username=message.author.name,
            message_text=combined_text,
            bot_id=str(self.bot.user.id)
        )

        if response and response != "[Overheard]":
            if not on_cooldown or is_command or is_dm:
                await self._send_split_response(message.channel, message, response)
                cooldown_manager.set_cooldown(user_id)

    async def _send_split_response(self, channel, original_message, response):
        # Split by sentences or newlines
        parts = re.split(r'(?<=[.!?])\s+|\n+', response)
        parts = [p.strip() for p in parts if p.strip()]

        for i, part in enumerate(parts):
            async with channel.typing():
                # Delay = (chars * 0.022) + random(-1, 1)
                # 45 chars per sec -> 1/45 = 0.022
                delay = (len(part) * 0.022) + random.uniform(-1, 1)
                # Min delay 1s for first part, 0.5s for subsequent
                min_wait = 1.0 if i == 0 else 0.5
                await asyncio.sleep(max(min_wait, delay))
                
                if i == 0:
                    await original_message.reply(part)
                else:
                    await channel.send(part)

    @commands.command(name="chat")
    async def chat_command(self, ctx, *, text: str):
        response = await pipeline.run(
            channel_id=str(ctx.channel.id),
            user_id=str(ctx.author.id),
            username=ctx.author.name,
            message_text=text,
            bot_id=str(self.bot.user.id),
            forced_confidence=1.0 # NEW
        )
        if response:
            from ..core.cooldown import cooldown_manager
            cooldown_manager.set_cooldown(str(ctx.author.id))
            await self._send_split_response(ctx.channel, ctx.message, response)

    @discord.app_commands.command(name="chat", description="Chat with Nia!")
    async def chat_slash(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        response = await pipeline.run(
            channel_id=str(interaction.channel_id),
            user_id=str(interaction.user.id),
            username=interaction.user.name,
            message_text=text,
            bot_id=str(self.bot.user.id),
            forced_confidence=1.0 # NEW
        )
        if response:
            from ..core.cooldown import cooldown_manager
            cooldown_manager.set_cooldown(str(interaction.user.id))
            # For slash commands, we send the first part as followup then the rest
            parts = re.split(r'(?<=[.!?])\s+|\n+', response)
            parts = [p.strip() for p in parts if p.strip()]
            for i, part in enumerate(parts):
                if i == 0:
                    await interaction.followup.send(part)
                else:
                    await interaction.channel.send(part)
        else:
            await interaction.followup.send("*(Nia overhears this but stays silent)*", ephemeral=True)

    @discord.app_commands.command(name="read", description="Enable passive reading in this channel.")
    async def read_slash(self, interaction: discord.Interaction):
        from ..core.database import db
        db.add_monitored_channel(str(interaction.channel_id))
        await interaction.response.send_message("I can read the messages here now! (Passive reading enabled)", ephemeral=True)

    @commands.command(name="read")
    @commands.has_permissions(administrator=True)
    async def read_prefix(self, ctx):
        from ..core.database import db
        db.add_monitored_channel(str(ctx.channel.id))
        await ctx.send("I can read the messages here now! (Passive reading enabled)")

    @commands.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_prefix(self, ctx):
        from ..core.database import db
        db.clear_history(str(ctx.channel.id))
        await ctx.send("Memory cleared for this channel! (Character state reset globally)")

    @discord.app_commands.command(name="reset", description="Reset Nia's memory for this channel.")
    async def reset_slash(self, interaction: discord.Interaction):
        from ..core.database import db
        db.clear_history(str(interaction.channel_id))
        await interaction.response.send_message("Memory cleared for this channel!", ephemeral=True)

    @commands.command(name="listmodels")
    @commands.has_permissions(administrator=True)
    async def list_models(self, ctx):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    embed_models = [m['name'] for m in models if "embedContent" in m.get("supportedGenerationMethods", [])]
                    await ctx.send(f"Available Embedding Models: {', '.join(embed_models) or 'None'}")
                else:
                    await ctx.send(f"Error {response.status_code}: {response.text[:200]}")
        except Exception as e:
            await ctx.send(f"Exception: {str(e)}")

async def setup(bot):
    await bot.add_cog(ChatCog(bot))
