import asyncio
import os
from context.identity import IdentityModule
from context.memory import MemoryModule
from context.relationship import RelationshipModule
from context.prompt_builder import PromptBuilder
from utils.database import Database

async def test_modular_system():
    db_name = "test_modular.db"
    if os.path.exists(db_name):
        os.remove(db_name)
        
    db = Database(db_name)
    identity = IdentityModule()
    memory = MemoryModule(db)
    relationship = RelationshipModule(db)
    builder = PromptBuilder(identity, memory, relationship)
    
    user_id = "user123"
    username = "Nyakaki"
    
    print("--- 1. Testing Perception (Affection Update) ---")
    relationship.update_relationship(user_id, "Yuki giỏi quá!")
    info = relationship.get_affection_info(user_id)
    print(f"Affection: {info['score']} ({info['level']})")
    assert info['score'] > 0
    
    print("--- 2. Testing Memory Extraction ---")
    memory.extract_memory(user_id, "Sinh nhật của tôi là ngày 27/7")
    facts = memory.get_user_facts(user_id)
    print(f"Facts: {facts}")
    assert "27/7" in facts
    
    print("--- 3. Testing Prompt Construction ---")
    prompt = builder.build_system_prompt(user_id, username)
    print("System Prompt Snippet:\n", prompt[:200], "...")
    assert "[THOUGHTS]" in prompt
    assert "[RESPONSE]" in prompt
    assert username in prompt
    
    print("✅ Modular system verification passed!")
    
    # if os.path.exists(db_name):
    #     os.remove(db_name)

if __name__ == "__main__":
    asyncio.run(test_modular_system())
