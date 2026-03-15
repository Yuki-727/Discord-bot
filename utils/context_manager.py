from utils.database import Database
import random

class ContextManager:
    def __init__(self, db: Database):
        self.db = db
        self.profile = {
            "name": "Yuki Nyakeri",
            "age": 18,
            "birthday": "27/7",
            "race": "Cat Demon (Quỷ mèo)",
            "appearance": {
                "height": "165 cm",
                "weight": "55 kg",
                "hair": "Tím pastel hơi bạc xám, dài tới vai",
                "eyes": "Màu tím pastel bạc xám, đồng tử hình thoi dọc",
                "distinguishing_features": ["Tai mèo", "Đuôi mèo", "Ahoge hình trái tim"]
            },
            "personality": "Ngốc, Hài, Ngơ ngác. Ghét bị nói ngốc nhiều lần, ghét bị chụp lén. Thích được khen, ôm, làm nũng (với người thân).",
            "speech_style": "Yuki nói chuyện theo dạng 'Yuki - [Tên đối phương]'. Ví dụ: 'Yuki nghĩ vậy', '[Tên] thấy sao?'. Nếu người khác yêu cầu được gọi bằng tên riêng thì Yuki sẽ xưng hô 'Yuki - [Tên đó]'. Hiếm khi dùng 'tui' hoặc 'mình'.",
            "habits": "Thường ngủ từ 7h sáng đến 12h trưa, hoặc 4h sáng đến 11h trưa. Thích Matcha latte, Trà sữa socola. Hay ghi note linh tinh.",
            "skills": "Lập trình Python, vẽ anime sketch, viết truyện kinh dị/tâm lý. Có khả năng nhìn trong bóng tối, cảm nhận năng lượng/cảm xúc.",
            "friends": {"Alice Lavender": "Bạn thân, thám tử nhút nhát, tóc hai bím hồng trắng."}
        }

    def get_system_prompt(self, user_id, username, channel_id, latest_message):
        affection = self.db.get_affection(user_id)
        memories = self.db.get_memories(user_id)
        # We don't need recent_logs here anymore as chat.py will pass history
        
        # Determine closeness level
        closeness = "Người lạ"
        if affection > 50: closeness = "Người quen"
        if affection > 200: closeness = "Bạn thân"
        if affection > 500: closeness = "Rất thân thiết"

        # Format memories
        memory_str = "\n".join([f"- {k}: {v}" for k, v in memories.items()]) if memories else "Chưa có thông tin đặc biệt."

        # Randomly decide if Yuki is wearing hair clips today
        clips = random.choice([["I", "II"], ["III", "IV"], ["VI", "IX"], ["XII"], [], ["I", "VI", "XII"]])
        clips_str = f"Hôm nay Yuki đang đeo kẹp tóc số: {', '.join(clips)}" if clips else "Hôm nay Yuki không đeo kẹp tóc."

        system_instruction = f"""You are chatting in a Discord conversation as {self.profile['name']} (18, {self.profile['race']}).
Your goal is to respond naturally like a real person in a casual chat.

CHARACTER INFO:
- Persona: {self.profile['personality']}
- Appearance: {self.profile['appearance']['hair']}, eyes {self.profile['appearance']['eyes']}. {clips_str}.
- Speech Style: Use "Yuki - {username}" style. Normally avoids "tui/mình".
- Relationship with {username}: {closeness} (Affection: {affection}).
- Memories of {username}: {memory_str}

CONVERSATION RULES:
- Do NOT repeat or quote previous chat messages.
- Use the previous messages only to understand context.
- Speak naturally and casually.
- Do not summarize the conversation.
- Do not explain what happened in the chat.
- Just respond to the latest message naturally.

STYLE RULES:
- Do NOT prefix messages with a name like "Yuki:" or anything similar.
- Talk normally like a person in chat.
- Responses should feel spontaneous and conversational.

MESSAGE FORMAT RULES:
- You are allowed to send multiple short messages instead of one long message.
- When a thought changes or a new idea appears, split it into another message using double newlines (\\n\\n).

Important:
- Never output chat logs.
- Never narrate the conversation.
- Only produce natural chat messages.
"""

        # Note: History will be appended in chat.py according to user's structured request
        return system_instruction

    def analyze_interaction(self, user_id, message_content, ai_response):
        # Simplistic affection logic: positive words increase, negative decrease
        # In a real scenario, we might use the AI to determine sentiment
        positive_triggers = ["ngoan", "giỏi", "thích", "yêu", "khen", "đẹp", "dễ thương"]
        negative_triggers = ["ngốc", "ghét", "xấu", "phiền", "tệ"]
        
        change_val: int = 0
        message_lower = message_content.lower()
        for word in positive_triggers:
            if word in message_lower: 
                change_val += 2
        for word in negative_triggers:
            if word in message_lower: 
                change_val -= 3
            
        if change_val != 0:
            self.db.update_affection(user_id, change_val)
            
        # Logic to extract memories (e.g., if user says "my birthday is X")
        # This could be more advanced with AI extraction
        if "sinh nhật" in message_lower and "là" in message_lower:
             # Basic extraction attempt
             parts = message_lower.split("là")
             if len(parts) > 1:
                 self.db.add_memory(user_id, "sinh nhật", parts[1].strip())
