import asyncio
import json
import re
from ..ai.client import ai_client

class AddressingDetector:
    def __init__(self, bot_name="Nia", nicknames=None):
        self.bot_name = bot_name.lower()
        self.nicknames = [n.lower() for n in nicknames] if nicknames else ["nia"]
        self.pronouns = ["cậu", "bạn", "mày", "you", "your", "you're", "u", "em", "anh", "chị"]

    async def check_addressing(self, text, username, recent_context, bot_id):
        """
        Calculates confidence using the new weighted formula (Phase 16).
        recent_context: { short_term: [...], summary: {...}, semantic: "..." }
        """
        from ..ai.embedding_engine import embedding_engine
        import time

        text_lower = text.lower()
        recent_messages = recent_context.get('short_term', [])
        
        # --- Part 1: AW (Addressing Weight - 50%) ---
        # Rule-based detection
        rule_conf = 0.0
        is_tagged = str(bot_id) in text or f"<@!{bot_id}>" in text or f"<@{bot_id}>" in text
        has_name = self.bot_name in text_lower or any(n in text_lower for n in self.nicknames)
        
        # Check last 3 for "carry"
        nia_active_recently = any(
            (self.bot_name in msg[2].lower() or msg[1].lower() == "nia")
            for msg in recent_messages[-3:]
        )

        has_pronoun = any(re.search(rf"\b{p}\b", text_lower) for p in self.pronouns)
        
        if is_tagged: 
            rule_conf = 0.95
        elif has_name: 
            rule_conf = 0.55
        elif has_pronoun and nia_active_recently:
            rule_conf = 0.45 # Moderate confidence if following up with a pronoun

        ai_conf = 0.0
        is_addressing_bot_ai = False
        # Trigger AI if some rules met or Nia active
        if rule_conf > 0.1 or nia_active_recently:
            context_str = "\n".join([f"{m[1]}: {m[2]}" for m in recent_messages[-5:]])
            prompt = f"""Is the latest message from {username} directed at Nia?
CONTEXT:
{context_str}

LATEST MESSAGE:
{username}: "{text}"

Guidelines:
- Directed at Nia? is_addressing_bot = true.
- Talking about Nia to someone else? is_addressing_bot = false.
Return JSON: {{"is_addressing_bot": bool, "confidence": float}}
"""
            try:
                raw = await ai_client.generate_response([{"role": "user", "content": prompt}])
                data = json.loads(raw.strip().strip("```json").strip("```"))
                ai_conf = data.get('confidence', 0.0)
                is_addressing_bot_ai = data.get('is_addressing_bot', False)
            except: pass

        aw = (rule_conf + ai_conf) / 2 if ai_conf > 0 else rule_conf

        # --- Part 2: CS (Context Strength - 15%) ---
        # CS = (0.55 * TS) + (0.25 * TP) + (0.2 * AC)
        
        # TS: Topic Similarity
        ts = 0.0
        curr_vector = embedding_engine.embed_text(text)
        prev_text = recent_messages[-1][2] if recent_messages else ""
        if not prev_text and recent_context.get('summary'):
            prev_text = recent_context['summary'].get('content', "")
        
        if prev_text:
            prev_vector = embedding_engine.embed_text(prev_text)
            ts = embedding_engine.cosine_similarity(curr_vector, prev_vector)
        
        # TP: Time Proximity (Decay over 60 seconds)
        tp = 0.0
        # For simplicity, we assume messages are incoming fast. 
        # In a real scenario, we'd check timestamps from DB. 
        # Since we don't have absolute wall-clock easily, we'll assume 1.0 if Nia spoke last.
        if recent_messages and recent_messages[-1][1].lower() == "nia":
            tp = 1.0
            
        # AC: Addressing Carry
        ac = 1.0 if nia_active_recently else 0.0
        
        cs = (0.55 * ts) + (0.25 * tp) + (0.2 * ac)

        # --- Part 3: KC & MM (20%) ---
        kc = 1.0 # Knowledge Confidence
        mm = 1.0 # Mood Modifier

        # --- Final Formula (Stricter weights - Phase 16.5) ---
        # aw (60%) + cs (20%) + kc (10%) + mm (10%)
        final_confidence = (aw * 0.60) + (cs * 0.20) + (kc * 0.10) + (mm * 0.10)
        
        # Decide
        # Strict: must have some AW or very high CS
        is_addressed = (aw > 0.4 and is_addressing_bot_ai) or (final_confidence >= 0.6)

        return {
            "is_addressed": is_addressed,
            "confidence": min(1.0, final_confidence),
            "reason": f"AW={aw:.2f}, CS={cs:.2f} (TS={ts:.2f})"
        }

addressing_detector = AddressingDetector(bot_name="Nia", nicknames=["yuki"])
