import asyncio
import json
import re
from ..ai.client import ai_client

class AddressingDetector:
    def __init__(self, bot_name="Nia", nicknames=None):
        self.bot_name = bot_name.lower()
        self.nicknames = [n.lower() for n in nicknames] if nicknames else ["nia"]
        self.pronouns = ["cậu", "bạn", "mày", "you", "your", "you're", "u", "em", "anh", "chị"]

    async def check_addressing(self, text, username, recent_messages, bot_id):
        """
        Calculates confidence that the message is addressing the bot.
        Returns: { "is_addressed": bool, "confidence": float, "reason": str }
        """
        text_lower = text.lower()
        confidence = 0.0
        reason = "No obvious addressing."

        # 1. Base Checks (Tags & Names)
        is_tagged = str(bot_id) in text or f"<@!{bot_id}>" in text or f"<@{bot_id}>" in text
        has_name = self.bot_name in text_lower or any(n in text_lower for n in self.nicknames)
        is_vague = any(word in text_lower for word in ["mọi người", "everyone", "ai biết", "giúp với"])

        if is_tagged:
            confidence = 0.95
            reason = "Directly tagged."
        elif has_name:
            confidence = 0.55
            reason = "Name mentioned."
        elif is_vague:
            confidence = 0.40
            reason = "Vague call to everyone/anyone."

        # 2. Context Override (+0.2 if pronouns used and Nia was recently active)
        # Check if Nia was mentioned or spoke in the last 5 messages
        nia_active_recently = any(
            (self.bot_name in msg[2].lower() or msg[1].lower() == "nia" or msg[1].lower() == "yuki")
            for msg in recent_messages[-5:]
        )
        
        has_pronoun = any(re.search(rf"\b{p}\b", text_lower) for p in self.pronouns)
        
        if nia_active_recently and has_pronoun:
            confidence += 0.4 # Boooost
            reason += " (Follow-up Continuity detected)"

        confidence = min(1.0, confidence)

        # 3. AI Refinement (The "Thinking" Step)
        # Trigger AI if we have some confidence OR Nia was active recently (to catch short follow-ups)
        if confidence > 0.1 or nia_active_recently:
            context_str = "\n".join([f"{m[1]}: {m[2]}" for m in recent_messages[-5:]])
            prompt = f"""Is the latest message from {username} directed at Nia?
CONTEXT:
{context_str}

LATEST MESSAGE:
{username}: "{text}"

Guidelines:
- If Nia was the last person to speak, and {username} is using pronouns (you, cậu, bạn...), they are likely talking TO Nia.
- If they are just talking about Nia to someone else, is_addressing_bot = false.
- Focus on continuity. Is this a reply to what Nia just said?

Return JSON:
{{
  "is_addressing_bot": true/false,
  "confidence": 0-1,
  "reason": "short explanation"
}}
"""
            try:
                raw = await ai_client.generate_response([{"role": "user", "content": prompt}])
                data = json.loads(raw.strip().strip("```json").strip("```"))
                # Blend rule-based and AI-based
                final_conf = (confidence + data['confidence']) / 2
                return {
                    "is_addressed": final_conf >= 0.5 or (data['is_addressing_bot'] and data['confidence'] > 0.7),
                    "confidence": min(1.0, final_conf),
                    "reason": data['reason']
                }
            except:
                pass

        return {
            "is_addressed": confidence >= 0.6,
            "confidence": confidence,
            "reason": reason
        }

addressing_detector = AddressingDetector(bot_name="Nia", nicknames=["yuki"])
