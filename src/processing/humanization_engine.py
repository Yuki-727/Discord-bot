import random
import re
import json
from ..ai.client import ai_client

class HumanizationEngine:
    def __init__(self):
        self.deja_vu_cooldowns = {} # (user_id, message_hash) -> timestamp

    def apply_imperfections(self, text, behavior_analysis):
        """
        Applies typos, emotional prefixes, and shortening.
        """
        # 1. Emotional Prefix (7.5% chance)
        if random.random() < 0.075:
            prefixes = ["Hả? ", "Hmm... ", "Uầy, ", "Ơ... ", "Thật á? "]
            # Try to match context
            tone = behavior_analysis.get("reasoning", {}).get("tone", "").lower()
            if "surprised" in tone or "?" in text:
                text = "Hả? " + text
            elif "thinking" in tone or "factual" in tone:
                text = "Hmm... " + text
            else:
                text = random.choice(prefixes) + text

        # 2. Typos (5% chance if length > 10)
        if len(text) > 10 and random.random() < 0.05:
            text = self._add_typo(text)

        # 3. Shortening (3% chance)
        if random.random() < 0.03:
            text = text[:int(len(text) * 0.7)] + "..."

        return text

    def _add_typo(self, text):
        typo_type = random.choice(["repeat", "swap", "skip"])
        idx = random.randint(1, len(text) - 2)
        
        if typo_type == "repeat":
            return text[:idx] + text[idx] * 2 + text[idx+1:]
        elif typo_type == "swap":
            return text[:idx] + text[idx+1] + text[idx] + text[idx+2:]
        elif typo_type == "skip":
            return text[:idx] + text[idx+1:]
        return text

    # async def check_deja_vu(self, user_id, message_text, recent_context):
    #     """
    #     Checks if the user has asked this before (30% chance if >0.9 similarity).
    #     Cooldown: 20 minutes per user.
    #     """
    #     import time
    #     current_time = time.time()
    #     
    #     # Check Cooldown (20 mins = 1200 seconds)
    #     last_deja_vu = self.deja_vu_cooldowns.get(user_id, 0)
    #     if current_time - last_deja_vu < 1200:
    #         return None
    #
    #     if random.random() < 0.30:
    #         self.deja_vu_cooldowns[user_id] = current_time
    #         return "Ủa hình như cái này cậu hỏi rồi mà? "
    #         
    #     return None

humanization_engine = HumanizationEngine()
