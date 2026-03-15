import discord
import asyncio
from discord import app_commands
from ai_client import AIClient
from utils.memory import ChatMemory

# Initialize AI client and memory
ai_client = AIClient()
chat_memory = ChatMemory(limit=8) # Changed limit to 8
_context_manager = None

def setup_context(cm):
    global _context_manager
    _context_manager = cm

async def get_ai_response(user_id, username, channel_id, message_text):
    # Get conversation history (last 8 messages)
    history = chat_memory.get_history(user_id)
    
    # Get dynamic system prompt from ContextManager
    system_instruction = "You are Yuki-bot."
    if _context_manager:
        system_instruction = _context_manager.get_system_prompt(user_id, username, channel_id, message_text)

    # Format CHAT HISTORY for the prompt
    history_lines = []
    for msg in history:
        role_label = username if msg["role"] == "user" else "bot"
        history_lines.append(f"{role_label}: {msg['content']}")
    
    history_str = "\n".join(history_lines) if history_lines else "No previous history."

    # Build the structured textual prompt as requested
    prompt_content = f"""SYSTEM
{system_instruction}

CHAT HISTORY
{history_str}

LATEST MESSAGE
{username}: {message_text}

Respond naturally."""

    # Send as a single user message for high instruction adherence to the structure
    messages = [{"role": "user", "content": prompt_content}]
    
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
    channel = ctx_or_interaction.channel if not is_interaction else ctx_or_interaction.channel
    channel_id = str(channel.id)
    
    # If interaction, defer response
    if is_interaction:
        await ctx_or_interaction.response.defer()
        
    response = await get_ai_response(str(user.id), user.name, channel_id, message)
    
    # Handle error responses
    if response.startswith("Error:"):
        if is_interaction:
            await ctx_or_interaction.followup.send(response)
        else:
            await ctx_or_interaction.channel.send(response)
        return

    # Split response by double newlines for natural feel
    parts = response.split("\n\n")
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
            
        if is_interaction:
            if i == 0:
                await ctx_or_interaction.followup.send(part)
            else:
                await ctx_or_interaction.channel.send(part)
        else:
            await ctx_or_interaction.channel.send(part)
        
        # Human-like delay between messages
        if i < len(parts) - 1:
            await asyncio.sleep(0.5)
