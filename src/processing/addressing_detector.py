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
        V3.5 Revision: Precise mathematical model for 1v1 vs Group.
        """
        from ..ai.embedding_engine import embedding_engine
        from ..core.conversation_lock import lock_manager
        import time

        text_lower = text.lower()
        channel_id = str(recent_context.get('channel_id', 'unknown'))
        user_id = str(recent_context.get('user_id', 'unknown'))
        recent_messages = recent_context.get('short_term', [])

        # --- Direct Command Bypass (Confidence = 1.0) ---
        is_tagged = str(bot_id) in text or f"<@{bot_id}>" in text
        is_prefix = text.startswith("!") or text.startswith("/")
        if is_tagged or is_prefix:
            return {
                "is_addressed": True,
                "confidence": 1.0,
                "reason": f"[Intent=Direct] [Target=Nia] [Confidence=1.0]"
            }

        topic_vector = embedding_engine.embed_text(text)
        lock = lock_manager.get_active_lock(channel_id, user_id, topic_vector)
        if not lock:
            lock = lock_manager.create_lock(channel_id, user_id, topic_vector)
        
        lock.add_message(text, user_id)
        is_1on1 = len(lock.participants) <= 2
        
        # --- Part 1: AI Role Analysis ---
        ai_role = "NONE"
        ai_conf = 0.0
        
        context_str = "\n".join([f"{m[1]}: {m[2]}" for m in recent_messages[-5:]])
        prompt = f"""Analyze if Nia is the RECIPIENT of this message.
CONTEXT:
{context_str}

LATEST MESSAGE from {username}: "{text}"

Roles:
- "TARGET": Speaking directly TO Nia.
- "TOPIC": Talking ABOUT Nia to someone else.
- "CONTINUITY": Following up on a conversation Nia is already in (no names mentioned).
- "NONE": Not related to Nia.

Return JSON: {{"role": "TARGET"|"TOPIC"|"CONTINUITY"|"NONE", "confidence": float}}
"""
        try:
            raw = await ai_client.generate_response([{"role": "user", "content": prompt}])
            content = raw.strip()
            if "```json" in content: content = content.split("```json")[-1].split("```")[0].strip()
            elif "```" in content: content = content.split("```")[-1].split("```")[0].strip()
            start, end = content.find("{"), content.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(content[start:end+1])
                ai_role, ai_conf = data.get('role', 'NONE'), data.get('confidence', 0.0)
        except: pass

        # AW (Addressing Weight)
        aw = 0.0
        if ai_role == "TARGET": aw = 1.0
        elif ai_role == "CONTINUITY": aw = 0.7 if is_1on1 else 0.3
        elif ai_role == "TOPIC": aw = 0.4 if is_1on1 else 0.1

        # --- Part 2: CS (Context Strength) ---
        ts = 0.2
        prev_text = recent_messages[-1][2] if recent_messages else ""
        if prev_text:
            prev_vector = embedding_engine.embed_text(prev_text)
            sim = embedding_engine.cosine_similarity(topic_vector, prev_vector)
            ts = 0.9 if sim > 0.75 else 0.2
        
        ac = 0.7 if (ai_role == "CONTINUITY" or (recent_messages and recent_messages[-1][1].lower() == "nia")) else 0.4
        
        # TP (Time Proximity - 60s decay)
        # Using current time vs lock's last message timestamp (or assume now if no messages)
        # For simplicity, we use the timestamp of the very last message in shorts
        tp = 0.0
        if recent_messages:
            # Note: Assuming database context includes timestamps. 
            # If not available, we use 1.0 as Nia spoke last OR 0.5 as fallback.
            # I will assume we can't get exact past timestamps now, but we'll try to use tp=1.0 for last 60s
            tp = 1.0 # Current implementation doesn't have absolute old timestamps yet
        
        cs = (0.6 * ts) + (0.3 * ac) + (0.1 * tp)

        # --- Part 3: MM (Mood Modifier) ---
        mm = 1.0

        # FINAL FORMULA
        if is_1on1:
            final_confidence = (aw * 0.60) + (cs * 0.30) + (mm * 0.10)
            threshold = 0.60
        else:
            final_confidence = (aw * 0.70) + (cs * 0.20) + (mm * 0.10)
            threshold = 0.55
        
        is_addressed = final_confidence >= threshold

        reason = (
            f"[Intent={ai_role}] [Is1on1={is_1on1}] [LockState={lock.state}] "
            f"[AW={aw:.2f}] [CS={cs:.2f}] [TS={ts:.2f}] [AC={ac:.2f}] [TP={tp:.2f}] [MM={mm:.2f}] "
            f"[Confidence={final_confidence:.2f}]"
        )

        return {
            "is_addressed": is_addressed,
            "confidence": min(1.0, final_confidence),
            "reason": reason
        }

addressing_detector = AddressingDetector(bot_name="Nia", nicknames=["nia"])
