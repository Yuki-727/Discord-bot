import discord
from discord import app_commands
from ai_client import AIClient
from utils.memory import ChatMemory

# Initialize AI client and memory
ai_client = AIClient()
chat_memory = ChatMemory(limit=10)

SYSTEM_PROMPT = "You are Yuki-bot, a friendly and helpful assistant on Discord."

async def get_ai_response(user_id, message_text):
    # Get conversation history
    history = chat_memory.get_history(user_id)
    
    # Prepare messages for API
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message_text})
    
    # Call AI API
    response = await ai_client.generate_response(messages)
    
    # Update memory if successful
    if not response.startswith("Error:"):
        chat_memory.add_message(user_id, "user", message_text)
        chat_memory.add_message(user_id, "assistant", response)
        
    return response

async def handle_chat_command(ctx_or_interaction, message: str):
    # Determine if it's a context (message) or interaction (slash command)
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    
    # If interaction, defer response because AI call might take time
    if is_interaction:
        await ctx_or_interaction.response.defer()
        
    response = await get_ai_response(str(user.id), message)
    
    # Send response
    if is_interaction:
        await ctx_or_interaction.followup.send(response)
    else:
        await ctx_or_interaction.channel.send(response)
