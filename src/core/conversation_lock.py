import time
import asyncio
from typing import Dict, List, Set

class ConversationLock:
    """
    Conversation Lock System (V3.5)
    Groups users and topics into managed conversation fragments.
    """
    def __init__(self, channel_id: str, topic_vector: List[float], participants: Set[str]):
        self.channel_id = channel_id
        self.topic_vector = topic_vector
        self.participants = participants # Set of User IDs
        self.messages = [] # List of {text, timestamp, owner_id}
        self.state = "ACTIVE" # ACTIVE, IDLE, DELETED
        self.last_activity = time.time()
        self.created_at = time.time()

    def add_message(self, text: str, user_id: str):
        self.messages.append({
            "text": text,
            "timestamp": time.time(),
            "owner_id": user_id
        })
        self.last_activity = time.time()
        self.participants.add(user_id)

    def is_idle(self, timeout=600): # 10 minutes
        return (time.time() - self.last_activity) > timeout

    def is_expired(self, expiry=86400): # 24 hours
        return (time.time() - self.last_activity) > expiry

class LockManager:
    def __init__(self):
        self.locks: Dict[str, List[ConversationLock]] = {} # channel_id -> [locks]
        self.queue = asyncio.Queue()

    def get_active_lock(self, channel_id: str, user_id: str, topic_vector: List[float]) -> ConversationLock:
        from ..ai.embedding_engine import embedding_engine
        
        if channel_id not in self.locks:
            self.locks[channel_id] = []
            
        # Try finding a lock with high similarity or where user is a participant
        best_lock = None
        highest_sim = 0.0
        
        for lock in self.locks[channel_id]:
            if lock.state != "ACTIVE": continue
            
            # Participant match
            if user_id in lock.participants:
                return lock
            
            # Topic similarity
            sim = embedding_engine.cosine_similarity(topic_vector, lock.topic_vector)
            if sim > 0.75 and sim > highest_sim:
                highest_sim = sim
                best_lock = lock
        
        return best_lock

    def create_lock(self, channel_id: str, user_id: str, topic_vector: List[float]) -> ConversationLock:
        new_lock = ConversationLock(channel_id, topic_vector, {user_id})
        if channel_id not in self.locks:
            self.locks[channel_id] = []
        self.locks[channel_id].append(new_lock)
        return new_lock

    async def process_cleanup(self):
        """Background task to handle 10m idle and 24h deletion."""
        while True:
            await asyncio.sleep(60) # Only check every minute
            now = time.time()
            for channel_id, channel_locks in list(self.locks.items()):
                for lock in list(channel_locks):
                    if lock.state == "ACTIVE" and lock.is_idle():
                        lock.state = "IDLE"
                        # TODO: Trigger summary and store in Daily Context
                    elif lock.is_expired():
                        lock.state = "DELETED"
                        channel_locks.remove(lock)

lock_manager = LockManager()
