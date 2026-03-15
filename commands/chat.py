import discord
from discord import app_commands
from ai_client import AIClient
from utils.memory import ChatMemory

# Initialize AI client and memory
ai_client = AIClient()
chat_memory = ChatMemory(limit=10)
_context_manager = None

def setup_context(cm):
    global _context_manager
    _context_manager = cm

async def get_ai_response(user_id, username, channel_id, message_text):
    # Get conversation history
    history = chat_memory.get_history(user_id)
    
    # Get dynamic system prompt from ContextManager
    system_prompt = "You are Yuki-bot."
    if _context_manager:
        system_prompt = _context_manager.get_system_prompt(user_id, username, channel_id)

    # Prepare messages for API
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message_text})
    
    # Call AI API
    response = await ai_client.generate_response(messages)
    
    # Update memory and analyze interaction if successful
    if not response.startswith("Error:"):
        chat_memory.add_message(user_id, "user", message_text)
        chat_memory.add_message(user_id, "assistant", response)
        
        if _context_manager:
            _context_manager.analyze_interaction(user_id, message_text, response)
        
    return response

async def handle_chat_command(ctx_or_interaction, message: str):
    # Determine if it's a context (message) or interaction (slash command)
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    channel_id = str(ctx_or_interaction.channel_id if is_interaction else ctx_or_interaction.channel.id)
    
    # If interaction, defer response
    if is_interaction:
        await ctx_or_interaction.response.defer()
        
    response = await get_ai_response(str(user.id), user.name, channel_id, message)
    
    # Send response
    if is_interaction:
        await ctx_or_interaction.followup.send(response)
    else:
        await ctx_or_interaction.channel.send(response)
