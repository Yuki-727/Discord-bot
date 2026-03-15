import discord
import asyncio
import re
from discord import app_commands
from ai_client import AIClient
from utils.memory import ChatMemory

# Initialize AI client and memory
ai_client = AIClient()
chat_memory = ChatMemory(limit=8)

# Context components (provided via setup_context)
_db = None
_identity = None
_memory = None
_relationship = None
_prompt_builder = None

def setup_context(db, identity, memory, relationship, prompt_builder):
    global _db, _identity, _memory, _relationship, _prompt_builder
    _db = db
    _identity = identity
    _memory = memory
    _relationship = relationship
    _prompt_builder = prompt_builder

async def get_ai_response(user_id, username, channel_id, message_text, bot_id):
    # 1. Perception Layer (Update relationship & memory)
    if _relationship:
        _relationship.update_relationship(user_id, message_text)
    if _memory:
        _memory.extract_memory(user_id, message_text)

    # 2. Context Layer (Prepare channel history & system prompt)
    system_instruction = "You are Yuki-bot."
    if _prompt_builder:
        system_instruction = _prompt_builder.build_system_prompt(user_id, username)

    bot_name = "Yuki"
    if _identity:
        bot_name = _identity.get_profile().get('name', 'Yuki').split()[0] # Just the first name for history labels

    # Use DB for full channel context instead of local ChatMemory
    history_str = "No recent history."
    if _db:
        # Get last 15 messages from this channel for context
        logs = _db.get_recent_logs(channel_id, limit=15)
        if logs:
            history_lines = []
            for logger_id, logger_name, content in logs:
                # Identify "self" (Yuki) by ID
                if str(logger_id) == str(bot_id):
                    display_tag = f"[{bot_name} (YOU)]"
                else:
                    display_tag = f"<@{logger_id}>"
                
                line = f"{display_tag}: {content}"
                # Avoid logging duplicate messages
                if len(history_lines) > 0 and history_lines[-1] == line:
                    continue
                history_lines.append(line)
            history_str = "\n".join(history_lines)

    # 3. Prompt Builder (Total rewrite integration)
    prompt_content = f"""SYSTEM
{system_instruction}

CHANNEL HISTORY (Look back for context!)
{history_str}

LATEST MESSAGE
<@{user_id}>: {message_text}

Respond following the <think> and <chat> format.
Note: You are [{bot_name} (YOU)] in the history. Respond naturally to the conversation!"""

    messages = [{"role": "user", "content": prompt_content}]
    
    # 4. LLM Thought Layer
    raw_response = await ai_client.generate_response(messages)
    
    # 5. Parse Layer (Extract chat portion)
    final_response = raw_response
    if "<chat>" in raw_response:
        match = re.search(r"<chat>(.*?)(</chat>|$)", raw_response, re.DOTALL | re.IGNORECASE)
        if match:
            final_response = match.group(1).strip()
    elif "<think>" in raw_response:
        parts = re.split(r"</think>", raw_response, flags=re.IGNORECASE)
        if len(parts) > 1:
            final_response = parts[1].strip()

    return final_response

def apply_persona_filter(text, user_id):
    # Order matters: replace specific contractions/phrases first
    replacements = [
        (r"\bI'm\b", "Yuki is"),
        (r"\bi'm\b", "Yuki is"),
        (r"\bI am\b", "Yuki is"),
        (r"\bi am\b", "Yuki is"),
        (r"\bi've\b", "Yuki has"),
        (r"\bI've\b", "Yuki has"),
        (r"\bi was\b", "Yuki was"),
        (r"\bI was\b", "Yuki was"),
        (r"\bmy\b", "Yuki's"),
        (r"\bmine\b", "Yuki's"),
        (r"\bI\b", "Yuki"),
        (r"\bme\b", "Yuki"),
        (r"\byou\b", f"<@{user_id}>"),
    ]
    
    filtered = text
    for pattern, repl in replacements:
        filtered = re.sub(pattern, repl, filtered, flags=re.IGNORECASE)
        
    # Final cleanup of common grammar slips
    fixes = [
        (r"\bYuki am\b", "Yuki is"),
        (r"\bYuki are\b", "Yuki is"),
        (r"\bYuki have\b", "Yuki has"),
        (r"\bYuki's are\b", "Yuki's is"),
        (r"\bYuki'm\b", "Yuki is"),
    ]
    
    for pattern, repl in fixes:
        filtered = re.sub(pattern, repl, filtered, flags=re.IGNORECASE)
        
    return filtered

# Lock for each user to prevent race conditions and handle rapid messages
user_locks = {}

async def handle_chat_command(ctx_or_interaction, message_text: str):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    
    if is_interaction:
        user = ctx_or_interaction.user
        channel = ctx_or_interaction.channel
        bot_user = ctx_or_interaction.client.user
    else:
        # ctx or message
        user = ctx_or_interaction.author
        channel = ctx_or_interaction.channel
        # In commands.Bot, ctx or message has access to bot via .bot or .client
        bot_user = getattr(ctx_or_interaction, "bot", getattr(ctx_or_interaction, "client", None)).user

    user_id = str(user.id)
    bot_id = str(bot_user.id)
    channel_id = str(channel.id)
    
    # 0. Queueing/Locking logic
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    
    async with user_locks[user_id]:
        if is_interaction:
            await ctx_or_interaction.response.defer()
            
        response = await get_ai_response(user_id, user.name, channel_id, message_text, bot_id)
        
        if response.startswith("Error:"):
            if is_interaction:
                await ctx_or_interaction.followup.send(response)
            else:
                await channel.send(response)
            return

        # Safety: replace literal "\n" characters with real ones
        response = response.replace("\\n", "\n")
        
        # Strip any lingering roleplay (*actions*) or prefixes (Yuki: )
        response = re.sub(r'\*.*?\*', '', response)
        response = re.sub(r'^Yuki:\s*', '', response, flags=re.IGNORECASE)
        
        # Apply Persona Filter (Post-processing)
        response = apply_persona_filter(response, user_id)
        
        # Log Yuki's final response to the database so she remembers it!
        if _db:
            bot_name = "Yuki"
            if _identity:
                bot_name = _identity.get_profile().get('name', 'Yuki').split()[0]
            _db.log_message(channel_id, bot_id, bot_name, response)

        # Split response by newlines for natural feel (both \n and \n\n)
        parts = re.split(r'\n+', response)
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part: continue
                
            if is_interaction:
                if i == 0: await ctx_or_interaction.followup.send(part)
                else: await channel.send(part)
            else:
                await channel.send(part, allowed_mentions=discord.AllowedMentions(users=True))
            
            if i < len(parts) - 1:
                # Human-like delay between messages
                await asyncio.sleep(0.5)
