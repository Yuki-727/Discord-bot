from ..core.database import db
from .semantic_memory import semantic_memory

class MemoryManager:
    def __init__(self):
        pass

    def get_context(self, user_id, channel_id, query_text=None):
        # Retrieve 3-tier memory
        short_term = db.get_recent_logs(channel_id, limit=10)
        
        # Use Vector Search if query_text is provided
        semantic = "No matching memories found."
        if query_text:
            semantic = semantic_memory.query_facts(user_id, query_text)
        
        return {
            "short_term": short_term,
            "long_term": [],
            "semantic": semantic
        }

    def update_memory(self, channel_id, user_id, username, message, response):
        # Save user message
        db.log_message(channel_id, user_id, username, message)
        # Save bot response
        db.log_message(channel_id, "bot_id_placeholder", "AI Assistant", response)

memory_manager = MemoryManager()
