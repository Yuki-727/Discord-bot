import asyncio
import os
import sys
import json

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Ensure we have the ENV variables for Groq/Voyage
from dotenv import load_dotenv
load_dotenv()

from src.memory.memory_manager import memory_manager
from src.core.database import db

async def test_summarization():
    channel_id = "test_channel_summarize"
    user_id = "test_user"
    username = "TestUser"

    print("--- 1. Cleaning old test data ---")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_logs WHERE channel_id = ?", (channel_id,))
        cursor.execute("DELETE FROM summary_memory WHERE channel_id = ?", (channel_id,))
        conn.commit()

    print("--- 2. Injecting 16 messages ---")
    # Total 32 rows (User + Bot)
    for i in range(16):
        db.log_message(channel_id, user_id, username, f"Message {i}: I am talking about topic X version {i}")
        db.log_message(channel_id, "bot", "Yuki", f"Response {i}: Interesting point about {i}")

    # Check count
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE channel_id = ?", (channel_id,))
        count = cursor.fetchone()[0]
        print(f"Current log count: {count} (Expected 32)")

    print("--- 3. Running Summarization ---")
    # Trigger summarization
    await memory_manager.summarize_history(channel_id)

    print("--- 4. Verifying Results ---")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        # Verify summary exists
        cursor.execute("SELECT topic, content, key_points FROM summary_memory WHERE channel_id = ?", (channel_id,))
        summary = cursor.fetchone()
        if summary:
            print(f"Summary Found!\nTopic: {summary[0]}\nContent: {summary[1]}\nKey Points: {summary[2]}")
        else:
            print("FAILED: No summary found in summary_memory")

        # Verify logs were deleted (Should have deleted 10)
        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE channel_id = ?", (channel_id,))
        new_count = cursor.fetchone()[0]
        print(f"New log count: {new_count} (Should be 32 - 10 = 22)")

if __name__ == "__main__":
    asyncio.run(test_summarization())
