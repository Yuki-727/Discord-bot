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
        
        # Filtering logic for commands
        is_command = message.content.startswith(self.bot.command_prefix)
        is_chat_command = message.content.startswith(f"{self.bot.command_prefix}chat ")
        
        # If it's a command but NOT !chat, we ignore it entirely (don't even passive read it)
        if is_command and not is_chat_command:
            return

        is_monitored = db.is_channel_monitored(channel_id)
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_tag = self.bot.user.mentioned_in(message)

        if not (is_monitored or is_dm or is_tag or is_chat_command):
            return

        # Buffering logic
        content = message.content
        if is_chat_command:
            content = content[len(self.bot.command_prefix) + 5:].strip() # Strip "!chat "

        key = (channel_id, user_id)
        if key not in self.msg_buffers:
            self.msg_buffers[key] = []
        
        self.msg_buffers[key].append(content)
        print(f"DEBUG [Queue]: Added message from {message.author.name} to buffer. Count: {len(self.msg_buffers[key])}")

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
            while wait_count < 30: # Max 30s wait to prevent infinite loops
                await asyncio.sleep(1.0)
                
                # If user is still actively typing, reset wait_count or just don't count it as a "check"
                if mcp.is_user_typing(channel_id, user_id):
                    # We stay in the loop but don't count this as a "try" for completeness
                    continue
                
                # Check AI completeness
                combined_text = "\n".join(self.msg_buffers.get(key, []))
                if not combined_text: break
                
                status = await mcp.check_completeness(combined_text, original_message.author.name)
                if status == "STOP":
                    print(f"DEBUG [Queue]: MCP returned STOP for {original_message.author.name}. Merging buffer.")
                    break
                else:
                    wait_count += 1

            messages = self.msg_buffers.pop(key, [])
            if not messages: return
            
            combined_text = "\n".join(messages)
            print(f"DEBUG [Queue]: Processed merged message ({len(messages)} chunks) from {original_message.author.name}")
            await self._process_merged_message(original_message, combined_text)
        except asyncio.CancelledError:
            pass
        finally:
            self.buffer_tasks.pop(key, None)

    @discord.app_commands.command(name="show_queue", description="Hiển thị hàng chờ tin nhắn hiện tại (Buffering)")
    async def show_queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not self.msg_buffers:
            return await interaction.followup.send("Hàng chờ tin nhắn hiện đang trống.")
        
        embed = discord.Embed(title="Message Buffers", color=discord.Color.orange())
        for (cid, uid), msgs in self.msg_buffers.items():
            user = self.bot.get_user(int(uid))
            name = user.name if user else uid
            embed.add_field(
                name=f"User: {name} (Channel: {cid})",
                value=f"**Count**: {len(msgs)}\n**Content**: {' | '.join(msgs)[:100]}...",
                inline=False
            )
        await interaction.followup.send(embed=embed)

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

    @discord.app_commands.command(name="read", description="Bật/Tắt chế độ Passive Read (Nia sẽ lắng nghe và tự động rep)")
    async def read_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from ..core.database import db
        channel_id = str(interaction.channel_id)
        
        if db.is_channel_monitored(channel_id):
            db.remove_monitored_channel(channel_id)
            await interaction.followup.send(f"⏹️ Đã tắt chế độ **Passive Read** tại kênh này.")
        else:
            db.add_monitored_channel(channel_id)
            await interaction.followup.send(f"📡 Đã bật chế độ **Passive Read**. Nia sẽ bắt đầu lắng nghe và trả lời tự động!")

    @commands.command(name="read")
    async def read_prefix(self, ctx):
        from ..core.database import db
        channel_id = str(ctx.channel.id)
        
        if db.is_channel_monitored(channel_id):
            db.remove_monitored_channel(channel_id)
            await ctx.send(f"⏹️ Đã tắt chế độ **Passive Read**.")
        else:
            db.add_monitored_channel(channel_id)
            await ctx.send(f"📡 Đã bật chế độ **Passive Read**.")

    @discord.app_commands.command(name="show_locks", description="Hiển thị các Conversation Locks hiện tại")
    async def show_locks(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from ..core.conversation_lock import lock_manager
        channel_id = str(interaction.channel_id)
        locks = lock_manager.locks.get(channel_id, [])
        
        if not locks:
            return await interaction.followup.send("Không có Conversation Lock nào đang hoạt động.")
        
        embed = discord.Embed(title="Conversation Locks", color=discord.Color.blue())
        for i, l in enumerate(locks):
            parts = ", ".join([f"<@{pid}>" for pid in l.participants])
            last_msg = l.messages[-1]['text'][:50] + "..." if l.messages else "None"
            embed.add_field(
                name=f"Lock #{i+1} [{l.state}]",
                value=f"**Participants**: {parts}\n**Last Msg**: {last_msg}",
                inline=False
            )
        await interaction.followup.send(embed=embed)

    @discord.app_commands.command(name="show_memory", description="Hiển thị các Fact gần nhất trong bộ nhớ dài hạn")
    async def show_memory(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from ..memory.semantic_memory import semantic_memory
        user_id = str(interaction.user.id)
        
        # Use existing query_facts with a generic thought
        facts_str = semantic_memory.query_facts(user_id, "What do you know about me?")
        
        if "No matching memories found" in facts_str:
            return await interaction.followup.send(f"Chưa có dữ liệu Semantic Memory cho <@{user_id}>.")
        
        embed = discord.Embed(title=f"Semantic Memory for {interaction.user.name}", color=discord.Color.green(), description=facts_str)
        await interaction.followup.send(embed=embed)

    @commands.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_prefix(self, ctx):
        from ..core.database import db
        from ..core.conversation_lock import lock_manager
        channel_id = str(ctx.channel.id)
        db.clear_history(channel_id)
        if channel_id in lock_manager.locks:
            lock_manager.locks.pop(channel_id)
        await ctx.send("🧹 Memory and Locks cleared for this channel!")

    @discord.app_commands.command(name="reset", description="Xóa sạch ký ức và các khóa hội thoại tại kênh này")
    async def reset_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from ..core.database import db
        from ..core.conversation_lock import lock_manager
        from ..memory.semantic_memory import semantic_memory
        
        channel_id = str(interaction.channel_id)
        user_id = str(interaction.user.id)
        
        db.clear_history(channel_id)
        semantic_memory.delete_user_memory(user_id)
        
        if channel_id in lock_manager.locks:
            lock_manager.locks.pop(channel_id)
            
        await interaction.followup.send("🧹 Đã dọn dẹp sạch KÝ ỨC (Ngắn hạn & Dài hạn) và các Lock tại kênh này!")

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_commands(self, ctx):
        """Force sync slash commands with Discord."""
        await ctx.send("⏳ Đang đồng bộ Slash Commands...")
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Đã đồng bộ {len(synced)} lệnh!")
        except Exception as e:
            await ctx.send(f"❌ Lỗi đồng bộ: {e}")

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
