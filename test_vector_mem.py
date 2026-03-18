import asyncio
from src.memory.semantic_memory import semantic_memory
from src.ai.embedding_engine import embedding_engine

async def test_vector_memory():
    print("Testing Vector Memory...")
    user_id = "test_user_123"
    username = "TestUser"
    
    # 1. Save some facts
    print("Saving facts...")
    semantic_memory.save_fact(user_id, "preferences", "User loves playing guitar and listening to rock music.", 5)
    semantic_memory.save_fact(user_id, "preferences", "User prefers spicy food but dislikes cilantro.", 4)
    semantic_memory.save_fact(user_id, "status", "User is currently learning Python for AI development.", 3)
    
    # 2. Query facts
    print("\nQuerying: 'What music does the user like?'")
    result1 = semantic_memory.query_facts(user_id, "What music does the user like?")
    print(f"Result 1:\n{result1}")
    
    print("\nQuerying: 'What food should I recommend?'")
    result2 = semantic_memory.query_facts(user_id, "What food should I recommend?")
    print(f"Result 2:\n{result2}")
    
    print("\nQuerying: 'What is the user learning?'")
    result3 = semantic_memory.query_facts(user_id, "What is the user learning?")
    print(f"Result 3:\n{result3}")

if __name__ == "__main__":
    asyncio.run(test_vector_memory())
