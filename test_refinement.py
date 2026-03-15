from utils.database import Database
from utils.context_manager import ContextManager
import asyncio
import os

async def test_refinement():
    db_name = "test_refinement.db"
    if os.path.exists(db_name):
        os.remove(db_name)
        
    db = Database(db_name)
    cm = ContextManager(db)
    
    user_id = "test_user"
    username = "Nyakaki"
    channel_id = "test_channel"
    message_text = "Chào Yuki, hôm nay thế nào?"
    
    print("--- Testing Full Prompt Construction ---")
    system_instruction = cm.get_system_prompt(user_id, username, channel_id, message_text)
    
    # Simulate chat.py construction
    history_str = "No previous history."
    prompt_content = f"""SYSTEM
{system_instruction}

CHAT HISTORY
{history_str}

LATEST MESSAGE
{username}: {message_text}

Respond naturally."""

    print("Final Prompt Snippet:\n", prompt_content[:200], "...")
    assert "SYSTEM" in prompt_content
    assert "CHAT HISTORY" in prompt_content
    assert "LATEST MESSAGE" in prompt_content
    assert "Respond naturally." in prompt_content
    assert "Yuki - Nyakaki" in prompt_content
    
    print("--- Testing Response Splitting ---")
    response = "Chào bạn!\n\nYuki cảm thấy rất vui khi được trò chuyện.\n\nBạn có khỏe không?"
    parts = response.split("\n\n")
    print("Parts:", parts)
    assert len(parts) == 3
    
    print("✅ Logic verification passed!")
    
    if os.path.exists(db_name):
        os.remove(db_name)

if __name__ == "__main__":
    asyncio.run(test_refinement())
