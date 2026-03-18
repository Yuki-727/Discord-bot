import discord
from discord.ext import commands
from ..core.pipeline import pipeline

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Receive & Skip Bots
        if message.author.bot:
            return
        
        from ..core.database import db
        from ..core.cooldown import cooldown_manager
        
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        is_monitored = db.is_channel_monitored(channel_id)
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        # Determine if we should process this message
        # We process if: it's a DM, it starts with prefix, or channel is monitored.
        is_command = message.content.startswith(self.bot.command_prefix)
        
        if is_dm or is_command or is_monitored:
            # Check Cooldown for passive reads (not commands and not DMs)
            on_cooldown = cooldown_manager.is_on_cooldown(user_id)
            
            # Run Pipeline
            # Note: We pass everything. Pipeline's AddressingDetector will decide if we reply.
            response = await pipeline.run(
                channel_id=channel_id,
                user_id=user_id,
                username=message.author.name,
                message_text=message.content,
                bot_id=str(self.bot.user.id)
            )
            
            # Decide whether to send the reply to Discord
            if response and response != "[Overheard]":
                # Only reply if not on cooldown or it's a direct command/DM
                if not on_cooldown or is_command or is_dm:
                    async with message.channel.typing():
                        await message.reply(response)
                        # Set/Reset cooldown after any successful response
                        cooldown_manager.set_cooldown(user_id)

    @commands.command(name="chat")
    async def chat_command(self, ctx, *, text: str):
        async with ctx.typing():
            response = await pipeline.run(
                channel_id=str(ctx.channel.id),
                user_id=str(ctx.author.id),
                username=ctx.author.name,
                message_text=text,
                bot_id=str(self.bot.user.id)
            )
            if response:
                from ..core.cooldown import cooldown_manager
                cooldown_manager.set_cooldown(str(ctx.author.id))
                await ctx.reply(response)

    @discord.app_commands.command(name="chat", description="Chat with Nia!")
    async def chat_slash(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        response = await pipeline.run(
            channel_id=str(interaction.channel_id),
            user_id=str(interaction.user.id),
            username=interaction.user.name,
            message_text=text,
            bot_id=str(self.bot.user.id)
        )
        if response:
            from ..core.cooldown import cooldown_manager
            cooldown_manager.set_cooldown(str(interaction.user.id))
            await interaction.followup.send(response)
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

async def setup(bot):
    await bot.add_cog(ChatCog(bot))
