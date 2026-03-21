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
        self.WAIT_THRESHOLD = 5.0 # Seconds to wait after typing stops

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
        # Short strings or common continuation indicators
        text_lower = text.strip().lower()
        if len(text_lower) < 4 or text_lower.endswith("...") or text_lower.endswith(",") or text_lower.endswith("và"):
            return "CONTINUE"

        prompt = f"""Analyze this message from {username}. Is it a complete thought, or does it look like they will send more fragments?
MESSAGE: "{text}"

Return only "STOP" if it is complete and Nia should reply, or "CONTINUE" if it is incomplete/vague and Nia should wait.
Status:"""
        try:
            raw = await ai_client.generate_response([{"role": "user", "content": prompt}])
            result = raw.strip().upper()
            if "STOP" in result: return "STOP"
            return "CONTINUE"
        except:
            return "STOP" # Fallback to reply if AI fails

mcp = MessageContinuationPredictor()
