import json
import time
from ..ai.client import ai_client

class MessageContinuationPredictor:
    """
    MCP (Message Continuation Predictor)
    Determines if Nia should wait for more messages or reply now.
    """
    def __init__(self):
        self.typing_cache = {} # channel_id -> {user_id: timestamp}
        self.WAIT_THRESHOLD = 12.0 # Discord typing heartbeat is ~10s, so 12s is safer

    def update_typing(self, channel_id, user_id):
        """Update the last seen typing timestamp for a user."""
        if channel_id not in self.typing_cache:
            self.typing_cache[channel_id] = {}
        self.typing_cache[channel_id][user_id] = time.time()

    def is_user_typing(self, channel_id, user_id):
        """Check if a user is still considered 'typing' based on the threshold."""
        if channel_id not in self.typing_cache or user_id not in self.typing_cache[channel_id]:
            return False
        
        last_typing = self.typing_cache[channel_id][user_id]
        return (time.time() - last_typing) < self.WAIT_THRESHOLD

    async def check_completeness(self, text, username):
        """
        Uses AI to predict if a message fragment is complete or likely to be continued.
        Returns: "STOP" (Complete) or "CONTINUE" (Wait)
        """
        # Hard check for fragments
        text_lower = text.strip().lower()
        # Common Vietnamese continuation particles
        particles = [
            "thì", "là", "mà", "nhưng", "nếu", "và", "hoặc", "rồi", 
            "còn", "nên", "cho", "vì", "với", "hơn", "như", "nào"
        ]
        
        is_fragment = (
            len(text_lower) < 4 or 
            text_lower.endswith("...") or 
            text_lower.endswith(",") or 
            any(text_lower.endswith(f" {p}") or text_lower == p for p in particles)
        )
        
        if is_fragment:
            return "CONTINUE"

        prompt = f"""Analyze if Nia should reply NOW to {username}. 
MESSAGE: "{text}"

Is this a complete thought/question? 
- If the user is likely to send more fragments, details, or if the message is open-ended (like "hey", "I think", "tính ra thì"), return "CONTINUE".
- ONLY if the message is a full sentence and seems like a natural stopping point, return "STOP".

Return only: "STOP" or "CONTINUE".
"""
        try:
            raw = await ai_client.generate_response([{"role": "user", "content": prompt}])
            result = raw.strip().upper()
            if "STOP" in result: return "STOP"
            return "CONTINUE"
        except:
            return "STOP" # Fallback to reply if AI fails

mcp = MessageContinuationPredictor()
