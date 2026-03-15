from utils.database import Database
from utils.context_manager import ContextManager
import os

def test_context_flow():
    # Setup temporary DB
    db_name = "test_yuki.db"
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
        except:
            pass
        
    db = Database(db_name)
    cm = ContextManager(db)
    
    user_id = "12345"
    username = "TestUser"
    channel_id = "channel_99"
    
    print("--- Testing Passive Logging ---")
    db.log_message(channel_id, user_id, username, "Hello everyone!")
    db.log_message(channel_id, "67890", "OtherUser", "Hi TestUser, how are you?")
    
    print("--- Testing System Prompt Generation ---")
    prompt = cm.get_system_prompt(user_id, username, channel_id)
    print("Prompt generated successfully.")
    assert username in prompt
    assert "Affection score: 0" in prompt
    assert "Hi TestUser" in prompt
    
    print("--- Testing Affection System ---")
    cm.analyze_interaction(user_id, "Yuki thật dễ thương và giỏi quá!", "Cảm ơn bạn!")
    new_affection = db.get_affection(user_id)
    print(f"New Affection Level: {new_affection}")
    assert new_affection > 0
    
    print("--- Testing Memory Extraction ---")
    # Simulate a user saying something with "sinh nhật" and "là"
    # Note: cm.analyze_interaction has internal logic for this
    cm.analyze_interaction(user_id, "sinh nhật của mình là ngày 10/10 đó", "Ghi nhớ rồi!")
    memories = db.get_memories(user_id)
    print(f"Memories: {memories}")
    assert memories.get("sinh nhật") == "ngày 10/10 đó"
    
    print("✅ All internal tests passed!")

if __name__ == "__main__":
    test_context_flow()
