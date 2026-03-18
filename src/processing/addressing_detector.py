import asyncio
import json
import re
from ..ai.client import ai_client

class AddressingDetector:
    def __init__(self, bot_name="Nia", nicknames=None):
        self.bot_name = bot_name.lower()
        self.nicknames = [n.lower() for n in nicknames] if nicknames else ["nia"]
        self.pronouns = ["cậu", "bạn", "mày", "you", "em", "anh", "chị"]

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
            confidence += 0.2
            reason += " (Context Override: Pronoun + Recent Activity)"

        # 3. AI Refinement (The "Thinking" Step)
        if confidence > 0.3:
            context_str = "\n".join([f"{m[1]}: {m[2]}" for m in recent_messages[-5:]])
            prompt = f"""Is the User ({username}) addressing the AI (Nia) in this message?
CONTEXT:
{context_str}

LATEST MESSAGE:
{username}: "{text}"

Analyze:
- Is Nia the second person (being talk TO)?
- Or is Nia the third person (being talked ABOUT)?

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
                    "is_addressed": final_conf >= 0.6 and data['is_addressing_bot'],
                    "confidence": final_conf,
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
