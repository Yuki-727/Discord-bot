import discord
import asyncio
import re
from discord import app_commands
from ai_client import AIClient
from utils.memory import ChatMemory

# Initialize AI client and memory
ai_client = AIClient()
chat_memory = ChatMemory(limit=8)

# Context modules
_identity = None
_memory = None
_relationship = None
_prompt_builder = None

def setup_context(identity, memory, relationship, prompt_builder):
    global _identity, _memory, _relationship, _prompt_builder
    _identity = identity
    _memory = memory
    _relationship = relationship
    _prompt_builder = prompt_builder

async def get_ai_response(user_id, username, channel_id, message_text):
    # 1. Perception Layer (Update relationship & memory)
    if _relationship:
        _relationship.update_relationship(user_id, message_text)
    if _memory:
        _memory.extract_memory(user_id, message_text)

    # 2. Context Layer (Prepare history & system prompt)
    history = chat_memory.get_history(user_id)
    system_instruction = "You are Yuki-bot."
    if _prompt_builder:
        system_instruction = _prompt_builder.build_system_prompt(user_id, username)

    history_lines = []
    for msg in history:
        role_label = username if msg["role"] == "user" else "bot"
        history_lines.append(f"{role_label}: {msg['content']}")
    
    history_str = "\n".join(history_lines) if history_lines else "No previous history."

    # 3. Prompt Builder (Refined structured prompt)
    prompt_content = f"""SYSTEM
{system_instruction}

CHAT HISTORY
{history_str}

LATEST MESSAGE
{username}: {message_text}

Respond following the [THOUGHTS] and [RESPONSE] format."""

    messages = [{"role": "user", "content": prompt_content}]
    
    # 4. LLM Thought Layer
    raw_response = await ai_client.generate_response(messages)
    
    # 5. Parse Layer (Extract chat portion)
    final_response = raw_response
    if "<chat>" in raw_response:
        # Extract content between <chat> and </chat>
        match = re.search(r"<chat>(.*?)(</chat>|$)", raw_response, re.DOTALL | re.IGNORECASE)
        if match:
            final_response = match.group(1).strip()
    elif "<think>" in raw_response:
        # Fallback if AI forgot <chat> but has <think>
        parts = re.split(r"</think>", raw_response, flags=re.IGNORECASE)
        if len(parts) > 1:
            final_response = parts[1].strip()

    # Update memory if successful
    if not raw_response.startswith("Error:"):
        chat_memory.add_message(user_id, "user", message_text)
        chat_memory.add_message(user_id, "assistant", final_response)
        
    return final_response

async def handle_chat_command(ctx_or_interaction, message: str):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    channel = ctx_or_interaction.channel
    channel_id = str(channel.id)
    
    if is_interaction:
        await ctx_or_interaction.response.defer()
        
    response = await get_ai_response(str(user.id), user.name, channel_id, message)
    
    if response.startswith("Error:"):
        target = ctx_or_interaction.followup if is_interaction else ctx_or_interaction.channel
        await target.send(response)
        return

    # Split response by newlines for natural feel (both \n and \n\n)
    # Using a regex to split by one or more newlines
    parts = re.split(r'\n+', response)
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part: continue
            
        if is_interaction:
            if i == 0: await ctx_or_interaction.followup.send(part)
            else: await ctx_or_interaction.channel.send(part)
        else:
            await ctx_or_interaction.channel.send(part, allowed_mentions=discord.AllowedMentions(users=True))
        
        if i < len(parts) - 1:
            # Human-like delay between messages
            await asyncio.sleep(0.5)
