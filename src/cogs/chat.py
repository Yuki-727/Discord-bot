import discord
from discord.ext import commands
from ..core.pipeline import pipeline

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Receive & 2. Filter
        if message.author.bot:
            return
        
        # Check if mentioned or name in message (Passive Chat)
        is_mentioned = self.bot.user in message.mentions
        is_named = "yuki" in message.content.lower()
        is_replied = message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user
        
        if is_mentioned or is_named or is_replied:
            if not message.content.startswith("!"):
                async with message.channel.typing():
                    response = await pipeline.run(
                        channel_id=str(message.channel.id),
                        user_id=str(message.author.id),
                        username=message.author.name,
                        message_text=message.content,
                        bot_id=str(self.bot.user.id)
                    )
                    await message.reply(response)

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
            await ctx.reply(response)

    @discord.app_commands.command(name="chat", description="Chat with Yuki!")
    async def chat_slash(self, interaction: discord.Interaction, text: str):
        # 3-second timeout protection
        await interaction.response.defer()
        
        response = await pipeline.run(
            channel_id=str(interaction.channel_id),
            user_id=str(interaction.user.id),
            username=interaction.user.name,
            message_text=text,
            bot_id=str(self.bot.user.id)
        )
        
        await interaction.followup.send(response)

async def setup(bot):
    await bot.add_cog(ChatCog(bot))
