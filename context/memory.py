from utils.database import Database

class MemoryModule:
    def __init__(self, db: Database):
        self.db = db

    def get_user_facts(self, user_id):
        memories = self.db.get_memories(user_id)
        if not memories:
            return "Chưa có thông tin đặc biệt."
        return "\n".join([f"- {k}: {v}" for k, v in memories.items()])

    def extract_memory(self, user_id, message_content):
        message_lower = message_content.lower()
        if "sinh nhật" in message_lower and "là" in message_lower:
            parts = message_lower.split("là")
            if len(parts) > 1:
                self.db.add_memory(user_id, "sinh nhật", parts[1].strip())
                return True
        return False
        
    def get_recent_context(self, channel_id, limit=8):
        # Optional: could be used for extra passive context if needed
        return self.db.get_recent_logs(channel_id, limit=limit)
