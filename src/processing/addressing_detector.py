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
        V3.5: Subject vs Topic Analysis with Conversation Locks.
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

        # Get or Update Thread Lock
        topic_vector = embedding_engine.embed_text(text)
        lock = lock_manager.get_active_lock(channel_id, user_id, topic_vector)
        if not lock:
            lock = lock_manager.create_lock(channel_id, user_id, topic_vector)
        
        lock.add_message(text, user_id)
        
        # --- Part 1: AW (Addressing Weight - 60%) ---
        has_name = self.bot_name in text_lower or any(n in text_lower for n in self.nicknames)
        
        # AI Analysis: Target vs Topic vs Continuity
        ai_role = "UNKNOWN"
        ai_conf = 0.0
        
        context_str = "\n".join([f"{m[1]}: {m[2]}" for m in recent_messages[-5:]])
        prompt = f"""Is Nia the intended RECIPIENT of this message?
CONTEXT:
{context_str}

LATEST MESSAGE from {username}: "{text}"

Roles:
- "TARGET": Speaking directly TO Nia.
- "TOPIC": Talking ABOUT Nia to someone else.
- "CONTINUITY": Following up on a conversation Nia is already in.
- "NONE": Not related to Nia.

Return JSON: {{"role": "TARGET"|"TOPIC"|"CONTINUITY"|"NONE", "confidence": float}}
"""
        try:
            raw = await ai_client.generate_response([{"role": "user", "content": prompt}])
            content = raw.strip()
            if "```json" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[-1].split("```")[0].strip()
            
            # Find the actual start and end
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start:end+1]
                
            data = json.loads(content)
            ai_role = data.get('role', 'NONE')
            ai_conf = data.get('confidence', 0.0)
        except Exception as e:
            ai_role = "ERROR"
            print(f"DEBUG: Addressing AI Error: {e}")

        aw = 0.0
        if ai_role == "TARGET": aw = ai_conf
        elif ai_role == "CONTINUITY": aw = ai_conf * 0.8
        elif ai_role == "TOPIC": aw = 0.1 # Very low, Nia is just a topic

        # --- Part 2: CS (Context Strength - 20%) ---
        # 1-1 Bonus logic
        is_1on1 = len(lock.participants) <= 2 # Nia + User
        
        ts = 0.0
        prev_text = recent_messages[-1][2] if recent_messages else ""
        if prev_text:
            prev_vector = embedding_engine.embed_text(prev_text)
            ts = embedding_engine.cosine_similarity(topic_vector, prev_vector)
        
        # AC: Addressing Carry
        ac = 1.0 if (ai_role == "CONTINUITY" or is_1on1) else ts
        # TP: Time Proximity (Assume Nia spoke last)
        tp = 1.0 if (recent_messages and recent_messages[-1][1].lower() == "nia") else 0.5
        
        cs = (ts * 0.4) + (ac * 0.3) + (tp * 0.3)

        # --- Part 3: KC & MM (20%) ---
        kc = 1.0; mm = 1.0

        # FINAL FORMULA
        final_confidence = (aw * 0.60) + (cs * 0.20) + (kc * 0.10) + (mm * 0.10)
        
        # Blocking Logic for Topic only
        blocked = (ai_role == "TOPIC" and ai_conf > 0.7)
        is_addressed = (not blocked) and (final_confidence >= 0.55)

        # Build detailed reason
        reason = (
            f"[Intent={ai_role}] [Is1on1={is_1on1}] [LockState={lock.state}] "
            f"[AW={aw:.2f}] [CS={cs:.2f}] [TS={ts:.2f}] [AC={ac:.2f}] [TP={tp:.2f}] [KC={kc:.2f}] [MM={mm:.2f}] "
            f"[BlockedBy={'TopicDetection' if blocked else 'None'}] [Confidence={final_confidence:.2f}]"
        )

        return {
            "is_addressed": is_addressed,
            "confidence": min(1.0, final_confidence),
            "reason": reason
        }

addressing_detector = AddressingDetector(bot_name="Nia", nicknames=["nia"])
